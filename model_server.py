"""
model_server.py

Socket-based model server that wraps CyberSentinelMod and exposes a simple JSON TCP API.

Protocol (JSON over TCP): client sends a JSON object per request and server replies with JSON.

Supported requests:
 - analyze packet: {"srcip":..., "dstip":..., ...}
 - command: {"command": "get_port_scan_stats", "srcip": "1.2.3.4"}
 - labeled sample: include key "label": e.g. {..packet.., "label": "DoS"}

Drop this file into your project root and run it separately from Flask app. It will
load models from the `models/` directory by default.
"""

import socket
import threading
import json
import logging
import time
from datetime import datetime
from typing import Tuple
import numpy as np

from cyber_sentinel_mod import CyberSentinelMod

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DEFAULT_HOST = '0.0.0.0'
DEFAULT_PORT = 9999

class ModelServer:
    def __init__(self, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT,
                 model_path: str = 'models/CICIDS2017_5class_model.h5',
                 scaler_path: str = 'models/scaler.pkl',
                 encoder_path: str = 'models/label_encoder.pkl',
                 retrain_interval: int = 300, retrain_batch: int = 50):
        self.host = host
        self.port = port
        self.ids_engine = CyberSentinelMod(model_path=model_path,
                                           scaler_path=scaler_path,
                                           encoder_path=encoder_path)
        self._stop = False

        # online learning buffer
        self.update_buffer = []
        self.update_lock = threading.Lock()
        self.retrain_interval = retrain_interval
        self.retrain_batch = retrain_batch

        # start retrainer thread
        self.retrainer_thread = threading.Thread(target=self._background_retrainer, daemon=True)
        self.retrainer_thread.start()

    def start(self):
        logger.info(f"🚀 Starting Model Server on {self.host}:{self.port}")
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((self.host, self.port))
        server.listen(8)

        try:
            while not self._stop:
                client_sock, addr = server.accept()
                logger.info(f"🔗 Connection from {addr}")
                t = threading.Thread(target=self._handle_client, args=(client_sock, addr), daemon=True)
                t.start()
        except KeyboardInterrupt:
            logger.info("Shutting down server...")
        finally:
            self._stop = True
            server.close()

    def _handle_client(self, sock: socket.socket, addr: Tuple[str,int]):
        with sock:
            data_chunks = []
            sock.settimeout(10)
            while True:
                try:
                    data = sock.recv(64 * 1024)
                    if not data:
                        break
                    data_chunks.append(data)
                    # try to decode full JSON
                    try:
                        text = b''.join(data_chunks).decode('utf-8')
                        payload = json.loads(text)
                    except json.JSONDecodeError:
                        # wait for more data - but limit buffer size
                        if len(data_chunks) > 10:  # Prevent memory issues
                            logger.warning(f"JSON decode failed, buffer too large from {addr}")
                            break
                        continue

                    logger.info(f"📨 Received request from {addr}")
                    # process request
                    response = self._process_request(payload)
                    resp_text = json.dumps(response, default=self._json_serializer)
                    sock.sendall(resp_text.encode('utf-8'))

                    # reset buffer for next request
                    data_chunks = []
                except socket.timeout:
                    logger.warning(f"Socket timeout from {addr}")
                    break
                except ConnectionResetError:
                    logger.warning(f"Connection reset by {addr}")
                    break
                except Exception as e:
                    logger.error(f"Error handling client {addr}: {e}")
                    try:
                        error_response = {'error': str(e)}
                        sock.sendall(json.dumps(error_response, default=self._json_serializer).encode('utf-8'))
                    except Exception:
                        pass
                    break

    def _json_serializer(self, obj):
        """Custom JSON serializer for numpy types and other non-serializable objects"""
        if isinstance(obj, (np.integer, np.int64, np.int32, np.int16, np.int8)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64, np.float32, np.float16)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, (np.bool_, bool)):
            return bool(obj)
        elif isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Type {type(obj)} not serializable")
    
    def _process_request(self, payload: dict) -> dict:
        # Commands
        if isinstance(payload, dict) and payload.get('command'):
            cmd = payload.get('command')
            if cmd == 'get_port_scan_stats':
                srcip = payload.get('srcip')
                return self.ids_engine.get_statistics(srcip)
            elif cmd == 'ping':
                return {'status': 'ok', 'timestamp': datetime.utcnow().isoformat()}
            else:
                return {'error': f'Unknown command: {cmd}'}

        # Labeled sample submission for online learning
        if 'label' in payload:
            # queue update (we store (features, label) for later)
            with self.update_lock:
                self.update_buffer.append(payload)
            return {'status': 'queued'}

        # Otherwise treat as packet to analyze
        try:
            result = self.ids_engine.analyze_packet(payload)
            return result
        except Exception as e:
            logger.error(f"Processing error: {e}")
            return {'error': str(e)}

    def _background_retrainer(self):
        """Periodically consumes update_buffer and performs batch retrain if supported."""
        while not self._stop:
            time.sleep(self.retrain_interval)
            batch = []
            with self.update_lock:
                while self.update_buffer and len(batch) < self.retrain_batch:
                    batch.append(self.update_buffer.pop(0))
            if not batch:
                continue

            logger.info(f"🔁 Applying incremental update with {len(batch)} samples")
            # For now, we only log — implementing online retraining depends on underlying model support
            try:
                # Convert batch into X/y if needed and call partial_fit on ensemble
                # Placeholder: write batch to 'models/online_updates.jsonl' for offline retrain
                import os
                os.makedirs('models/updates', exist_ok=True)
                path = f"models/updates/update_{int(time.time())}.jsonl"
                with open(path, 'w') as f:
                    for item in batch:
                        f.write(json.dumps(item) + '\n')
                logger.info(f"Wrote {len(batch)} labeled samples to {path} for offline retraining")
            except Exception as e:
                logger.error(f"Failed to persist update batch: {e}")

if __name__ == '__main__':
    server = ModelServer()
    server.start()
