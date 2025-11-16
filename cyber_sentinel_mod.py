"""
cyber_sentinel_mod.py

Modular Cyber Sentinel IDS engine that integrates:
 - 5-class CICIDS2017 Keras model (.h5)
 - StandardScaler and LabelEncoder (.pkl)
 - PortScanDetector for behavioral detection
 - Heuristic detectors for DoS / Brute Force / Service scans

Drop this file into your project root and ensure `models/` contains:
 - CICIDS2017_5class_model.h5
 - scaler.pkl
 - label_encoder.pkl

Usage:
    from cyber_sentinel_mod import CyberSentinelMod
    ids = CyberSentinelMod(model_path='models/CICIDS2017_5class_model.h5')
    result = ids.analyze_packet(packet_dict)

"""

import os
import logging
from typing import Dict, Optional, Any
from datetime import datetime

import numpy as np
import joblib

# Try to import tensorflow/keras robustly
try:
    import tensorflow as tf
    from tensorflow.keras.models import load_model
except Exception:
    # If TF not available, keep graceful fallback
    tf = None
    load_model = None

# Import port scan detector (assumes port_scan_detector.py present)
try:
    from port_scan_detector import PortScanDetector
except Exception:
    PortScanDetector = None

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class CyberSentinelMod:
    """Central IDS engine that combines ML + Behavioral detection."""

    def __init__(self,
                 model_path: str = "models/CICIDS2017_5class_model.h5",
                 scaler_path: str = "models/scaler.pkl",
                 encoder_path: str = "models/label_encoder.pkl",
                 port_scan_window: int = 60):
        self.model_path = model_path
        self.scaler_path = scaler_path
        self.encoder_path = encoder_path

        self.model = None
        self.scaler = None
        self.encoder = None

        self.port_scan_detector = PortScanDetector(window_size=port_scan_window) if PortScanDetector else None

        # load artifacts if available
        self._load_artifacts()

    def _load_artifacts(self):
        # Helper to resolve paths (try relative, then absolute)
        def resolve_path(path):
            if os.path.isabs(path):
                return path
            # Try relative to current directory
            if os.path.exists(path):
                return path
            # Try relative to script directory
            script_dir = os.path.dirname(os.path.abspath(__file__))
            abs_path = os.path.join(script_dir, path)
            if os.path.exists(abs_path):
                return abs_path
            return path
        
        model_path = resolve_path(self.model_path)
        scaler_path = resolve_path(self.scaler_path)
        encoder_path = resolve_path(self.encoder_path)
        
        # Load Keras model
        try:
            if load_model is None:
                logger.warning("TensorFlow/Keras not available; ML model disabled")
                self.model = None
            elif not os.path.exists(model_path):
                logger.warning(f"Model file not found at {model_path} (tried: {self.model_path}); ML disabled")
                logger.info(f"Current working directory: {os.getcwd()}")
                logger.info(f"Script directory: {os.path.dirname(os.path.abspath(__file__))}")
                self.model = None
            else:
                try:
                    self.model = load_model(model_path, compile=False)
                    logger.info(f"✅ Loaded Keras model from {model_path}")
                    # Log model summary if available
                    try:
                        logger.info(f"Model input shape: {self.model.input_shape}, output shape: {self.model.output_shape}")
                    except:
                        pass
                except Exception as load_error:
                    logger.error(f"Failed to load Keras model: {load_error}")
                    logger.exception("Model loading traceback:")
                    self.model = None
        except Exception as e:
            logger.error(f"Unexpected error during model loading: {e}")
            logger.exception("Unexpected error traceback:")
            self.model = None

        # Load scaler
        try:
            if os.path.exists(scaler_path):
                self.scaler = joblib.load(scaler_path)
                logger.info(f"✅ Loaded scaler from {scaler_path}")
            else:
                logger.warning(f"Scaler file not found at {scaler_path} (tried: {self.scaler_path}); scaling disabled")
        except Exception as e:
            logger.error(f"Failed to load scaler: {e}")
            self.scaler = None

        # Load label encoder
        try:
            if os.path.exists(encoder_path):
                self.encoder = joblib.load(encoder_path)
                logger.info(f"✅ Loaded label encoder from {encoder_path}")
            else:
                logger.warning(f"Label encoder file not found at {encoder_path} (tried: {self.encoder_path}); will return numeric classes")
        except Exception as e:
            logger.error(f"Failed to load label encoder: {e}")
            self.encoder = None

    # ---------------------- Feature extraction ----------------------
    def preprocess_packet(self, packet: Dict[str, Any]) -> np.ndarray:
        """Convert incoming packet dict into feature vector compatible with CICIDS2017 model.
        
        Maps common network packet fields to CICIDS2017 features. The model expects
        approximately 79 features. This function extracts available features and fills
        missing ones with default values.
        """
        # If scaler exists, infer expected feature length from scaler.mean_
        if self.scaler is not None and hasattr(self.scaler, 'mean_'):
            n_features = len(self.scaler.mean_)
        else:
            # default to 79 features (standard CICIDS2017)
            n_features = 79

        fv = np.zeros(n_features, dtype=np.float32)

        # Helper functions for feature extraction
        def safe_float(value, default=0.0):
            try:
                return float(value) if value is not None else default
            except (ValueError, TypeError):
                return default

        def safe_int(value, default=0):
            try:
                return int(value) if value is not None else default
            except (ValueError, TypeError):
                return default

        # Extract basic packet information
        protocol = str(packet.get('protocol', 'tcp')).lower()
        src_port = safe_int(packet.get('src_port', 0))
        dst_port = safe_int(packet.get('dst_port', 0))
        duration = safe_float(packet.get('duration', 0.0))
        packet_size = safe_float(packet.get('packet_size', 0.0))
        flags = safe_int(packet.get('flags', 0))
        
        # Extract IP addresses for flow-based features
        srcip = packet.get('srcip', '0.0.0.0')
        dstip = packet.get('dstip', '0.0.0.0')
        
        # Map protocol to numeric (common CICIDS2017 encoding)
        protocol_map = {'tcp': 0, 'udp': 1, 'icmp': 2}
        protocol_num = protocol_map.get(protocol, 0)
        
        # Extract additional features if available
        service = packet.get('service', '-')
        state = packet.get('state', 'REQ')
        
        # Build feature vector (mapping to common CICIDS2017 feature order)
        # Note: This is a generic mapping. Adjust indices based on your specific model.
        feature_idx = 0
        
        # Basic flow features (typically first 10-15 features)
        if feature_idx < n_features:
            fv[feature_idx] = duration  # Flow Duration
            feature_idx += 1
        
        if feature_idx < n_features:
            fv[feature_idx] = protocol_num  # Protocol
            feature_idx += 1
        
        if feature_idx < n_features:
            fv[feature_idx] = safe_float(packet.get('service', 0), 0.0)  # Service (encoded)
            feature_idx += 1
        
        if feature_idx < n_features:
            fv[feature_idx] = safe_float(packet.get('state', 0), 0.0)  # State (encoded)
            feature_idx += 1
        
        # Packet counts
        if feature_idx < n_features:
            fv[feature_idx] = safe_float(packet.get('spkts', 1.0), 1.0)  # Source packets
            feature_idx += 1
        
        if feature_idx < n_features:
            fv[feature_idx] = safe_float(packet.get('dpkts', 1.0), 1.0)  # Destination packets
            feature_idx += 1
        
        # Byte counts
        if feature_idx < n_features:
            fv[feature_idx] = safe_float(packet.get('sbytes', packet_size), packet_size)  # Source bytes
            feature_idx += 1
        
        if feature_idx < n_features:
            fv[feature_idx] = safe_float(packet.get('dbytes', packet_size), packet_size)  # Destination bytes
            feature_idx += 1
        
        # Rate and timing features
        if feature_idx < n_features:
            fv[feature_idx] = safe_float(packet.get('rate', 0.0), 0.0)  # Flow rate
            feature_idx += 1
        
        if feature_idx < n_features:
            fv[feature_idx] = safe_float(packet.get('sttl', 64.0), 64.0)  # Source TTL
            feature_idx += 1
        
        if feature_idx < n_features:
            fv[feature_idx] = safe_float(packet.get('dttl', 64.0), 64.0)  # Destination TTL
            feature_idx += 1
        
        # Load features
        if feature_idx < n_features:
            fv[feature_idx] = safe_float(packet.get('sload', 0.0), 0.0)  # Source load
            feature_idx += 1
        
        if feature_idx < n_features:
            fv[feature_idx] = safe_float(packet.get('dload', 0.0), 0.0)  # Destination load
            feature_idx += 1
        
        # Loss features
        if feature_idx < n_features:
            fv[feature_idx] = safe_float(packet.get('sloss', 0.0), 0.0)  # Source loss
            feature_idx += 1
        
        if feature_idx < n_features:
            fv[feature_idx] = safe_float(packet.get('dloss', 0.0), 0.0)  # Destination loss
            feature_idx += 1
        
        # Inter-packet timing
        if feature_idx < n_features:
            fv[feature_idx] = safe_float(packet.get('sinpkt', 0.0), 0.0)  # Source inter-packet time
            feature_idx += 1
        
        if feature_idx < n_features:
            fv[feature_idx] = safe_float(packet.get('dinpkt', 0.0), 0.0)  # Destination inter-packet time
            feature_idx += 1
        
        # Jitter
        if feature_idx < n_features:
            fv[feature_idx] = safe_float(packet.get('sjit', 0.0), 0.0)  # Source jitter
            feature_idx += 1
        
        if feature_idx < n_features:
            fv[feature_idx] = safe_float(packet.get('djit', 0.0), 0.0)  # Destination jitter
            feature_idx += 1
        
        # Window size
        if feature_idx < n_features:
            fv[feature_idx] = safe_float(packet.get('swin', 0.0), 0.0)  # Source window size
            feature_idx += 1
        
        if feature_idx < n_features:
            fv[feature_idx] = safe_float(packet.get('dwin', 0.0), 0.0)  # Destination window size
            feature_idx += 1
        
        # TCP features
        if feature_idx < n_features:
            fv[feature_idx] = safe_float(packet.get('stcpb', 0.0), 0.0)  # Source TCP base sequence number
            feature_idx += 1
        
        if feature_idx < n_features:
            fv[feature_idx] = safe_float(packet.get('dtcpb', 0.0), 0.0)  # Destination TCP base sequence number
            feature_idx += 1
        
        # TCP RTT
        if feature_idx < n_features:
            fv[feature_idx] = safe_float(packet.get('tcprtt', 0.0), 0.0)  # TCP RTT
            feature_idx += 1
        
        if feature_idx < n_features:
            fv[feature_idx] = safe_float(packet.get('synack', 0.0), 0.0)  # SYN-ACK time
            feature_idx += 1
        
        if feature_idx < n_features:
            fv[feature_idx] = safe_float(packet.get('ackdat', 0.0), 0.0)  # ACK data time
            feature_idx += 1
        
        # Mean features
        if feature_idx < n_features:
            fv[feature_idx] = safe_float(packet.get('smean', 0.0), 0.0)  # Source mean
            feature_idx += 1
        
        if feature_idx < n_features:
            fv[feature_idx] = safe_float(packet.get('dmean', 0.0), 0.0)  # Destination mean
            feature_idx += 1
        
        # Connection features
        if feature_idx < n_features:
            fv[feature_idx] = safe_float(packet.get('trans_depth', 0.0), 0.0)  # Transaction depth
            feature_idx += 1
        
        if feature_idx < n_features:
            fv[feature_idx] = safe_float(packet.get('response_body_len', 0.0), 0.0)  # Response body length
            feature_idx += 1
        
        # Connection state features (ct_*)
        if feature_idx < n_features:
            fv[feature_idx] = safe_float(packet.get('ct_srv_src', 0.0), 0.0)  # Count of connections to same service from source
            feature_idx += 1
        
        if feature_idx < n_features:
            fv[feature_idx] = safe_float(packet.get('ct_state_ttl', 0.0), 0.0)  # Count of connections with same state and TTL
            feature_idx += 1
        
        if feature_idx < n_features:
            fv[feature_idx] = safe_float(packet.get('ct_dst_ltm', 0.0), 0.0)  # Count of connections to same destination
            feature_idx += 1
        
        if feature_idx < n_features:
            fv[feature_idx] = safe_float(packet.get('ct_src_dport_ltm', 0.0), 0.0)  # Count of connections from source to destination port
            feature_idx += 1
        
        if feature_idx < n_features:
            fv[feature_idx] = safe_float(packet.get('ct_dst_sport_ltm', 0.0), 0.0)  # Count of connections to destination from source port
            feature_idx += 1
        
        if feature_idx < n_features:
            fv[feature_idx] = safe_float(packet.get('ct_dst_src_ltm', 0.0), 0.0)  # Count of connections to same destination and source
            feature_idx += 1
        
        # FTP and HTTP features
        if feature_idx < n_features:
            fv[feature_idx] = safe_float(packet.get('is_ftp_login', 0.0), 0.0)  # Is FTP login
            feature_idx += 1
        
        if feature_idx < n_features:
            fv[feature_idx] = safe_float(packet.get('ct_ftp_cmd', 0.0), 0.0)  # Count of FTP commands
            feature_idx += 1
        
        if feature_idx < n_features:
            fv[feature_idx] = safe_float(packet.get('ct_flw_http_mthd', 0.0), 0.0)  # Count of HTTP methods in flow
            feature_idx += 1
        
        if feature_idx < n_features:
            fv[feature_idx] = safe_float(packet.get('ct_src_ltm', 0.0), 0.0)  # Count of connections from source
            feature_idx += 1
        
        if feature_idx < n_features:
            fv[feature_idx] = safe_float(packet.get('ct_srv_dst', 0.0), 0.0)  # Count of connections to same service to destination
            feature_idx += 1
        
        if feature_idx < n_features:
            fv[feature_idx] = safe_float(packet.get('is_sm_ips_ports', 0.0), 0.0)  # Is same IP and port
            feature_idx += 1
        
        # Fill remaining features with zeros or derived values
        while feature_idx < n_features:
            # Use port numbers, flags, or other available data
            if feature_idx < n_features and feature_idx % 2 == 0:
                fv[feature_idx] = float(src_port % 65536) / 65536.0  # Normalized source port
            elif feature_idx < n_features:
                fv[feature_idx] = float(dst_port % 65536) / 65536.0  # Normalized destination port
            feature_idx += 1

        # If scaler present, use it to transform
        if self.scaler is not None:
            try:
                fv = self.scaler.transform(fv.reshape(1, -1))[0]
            except Exception as e:
                logger.warning(f"Scaler transform failed: {e}; proceeding without scaling")

        return fv

    # ---------------------- ML Prediction ----------------------
    def predict_ml(self, packet: Dict[str, Any]) -> Dict[str, Any]:
        """Return multi-class prediction and confidence.

        Returns:
            {
                'ml_available': bool,
                'pred_class_idx': int,
                'pred_class': str (if encoder available),
                'confidence': float,
                'raw_probs': list
            }
        """
        if self.model is None:
            return {'ml_available': False, 'error': 'Model not loaded'}

        try:
            fv = self.preprocess_packet(packet).astype(np.float32)
            inp = fv.reshape(1, -1)
            probs = self.model.predict(inp, verbose=0)

            # handle different output shapes
            if probs.ndim == 2 and probs.shape[1] > 1:
                probs = probs[0]
                idx = int(np.argmax(probs))
                conf = float(probs[idx])
            else:
                # binary single-probability output
                probs = probs.flatten()
                if len(probs) == 1:
                    conf = float(probs[0])
                    idx = 1 if conf >= 0.5 else 0
                else:
                    idx = int(np.argmax(probs))
                    conf = float(probs[idx])

            pred_class = None
            if self.encoder is not None:
                try:
                    pred_class = str(self.encoder.inverse_transform([idx])[0])
                except Exception:
                    pred_class = str(idx)

            return {
                'ml_available': True,
                'pred_class_idx': idx,
                'pred_class': pred_class,
                'confidence': conf,
                'raw_probs': probs.tolist() if hasattr(probs, 'tolist') else [float(probs)]
            }
        except Exception as e:
            logger.error(f"ML prediction failed: {e}")
            return {'ml_available': False, 'error': str(e)}

    # ---------------------- Behavioral detection ----------------------
    def detect_port_scan(self, packet: Dict[str, Any]) -> Dict[str, Any]:
        if self.port_scan_detector is None:
            return {'port_scan_available': False}
        try:
            return self.port_scan_detector.detect_port_scan(packet)
        except Exception as e:
            logger.error(f"Port scan detection error: {e}")
            return {'port_scan_available': False, 'error': str(e)}

    # ---------------------- Heuristics for DoS / Brute Force ----------------------
    def heuristic_classify(self, packet: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Simple heuristics to detect DoS / brute-force / service scans using port_scan_detector state."""
        if self.port_scan_detector is None:
            return None

        srcip = packet.get('srcip')
        if not srcip:
            return None

        ip_state = self.port_scan_detector.ip_tracking.get(srcip)
        if not ip_state:
            return None

        total_conns = len(ip_state['timestamps'])
        unique_ports = len(ip_state['ports'])
        # compute connection_rate over stored window
        time_window = (ip_state['timestamps'][-1] - ip_state['timestamps'][0]).total_seconds() if total_conns > 1 else 1
        conn_rate = total_conns / max(time_window, 1)

        # DoS heuristic
        if conn_rate > 50:  # very high rate
            return {'heuristic': 'DOS_ATTACK', 'confidence': min(0.99, conn_rate/100), 'severity': 'CRITICAL'}

        # Brute force heuristic: many attempts to same small set of ports
        if total_conns > 20 and unique_ports < 5:
            return {'heuristic': 'BRUTE_FORCE', 'confidence': min(0.95, total_conns/100), 'severity': 'HIGH'}

        # Service scan: many well-known ports touched
        well_known_hits = sum(1 for p in ip_state['ports'] if p <= 1023)
        if well_known_hits > 10:
            return {'heuristic': 'SERVICE_SCAN', 'confidence': 0.8, 'severity': 'HIGH'}

        return None

    # ---------------------- Unified analysis ----------------------
    def analyze_packet(self, packet: Dict[str, Any], prefer_behavior: bool = True) -> Dict[str, Any]:
        """Run full analysis pipeline and return structured result."""
        ts = packet.get('timestamp') or datetime.utcnow().isoformat()
        packet['timestamp'] = ts

        ml_res = self.predict_ml(packet)
        scan_res = self.detect_port_scan(packet)
        heuristic_res = self.heuristic_classify(packet)

        # Combine logic: if port_scan detects something, give it priority
        final = {
            'timestamp': ts,
            'source_ip': packet.get('srcip', 'unknown'),
            'destination_ip': packet.get('dstip', 'unknown'),
            'protocol': packet.get('protocol', 'unknown'),
            'ml_result': ml_res,
            'port_scan_result': scan_res,
            'heuristic_result': heuristic_res,
            'threat_detected': False,
            'attack_type': 'BENIGN',  # Use attack_type for consistency with app.py
            'attack_label': 'BENIGN',
            'confidence': 0.0,
            'severity': 'NONE',
            'recommendation': None,
            'model_used': None
        }

        # Priority rules - ML MODEL FIRST (CICIDS2017_5class_model.h5 is PRIMARY)
        # 1) ML Model (CICIDS2017_5class_model.h5) - PRIMARY DETECTION METHOD
        if ml_res.get('ml_available'):
            # If encoder present, use class name; else numeric
            pred = ml_res.get('pred_class') or str(ml_res.get('pred_class_idx'))
            conf = float(ml_res.get('confidence', 0.0) or 0.0)
            final['attack_label'] = pred
            final['confidence'] = conf
            
            # Get actual model name from file path (e.g., "CICIDS2017_5class_model")
            model_name = 'CICIDS2017_5class_model'
            if self.model_path:
                # Extract model name from path (e.g., "models/CICIDS2017_5class_model.h5" -> "CICIDS2017_5class_model")
                import os
                base_name = os.path.basename(self.model_path)
                if base_name.endswith('.h5'):
                    model_name = base_name[:-3]  # Remove .h5 extension
                else:
                    model_name = base_name
            
            final['model_used'] = model_name
            
            # Check if it's a threat (not BENIGN/Normal)
            is_benign = False
            if pred:
                pred_upper = str(pred).upper()
                is_benign = pred_upper in ['BENIGN', 'NORMAL', '0', 'NONE']
            
            if not is_benign and conf >= 0.3:  # Lower threshold for ML detection
                final['threat_detected'] = True
                final['attack_type'] = pred
                final['attack_label'] = pred
                final['severity'] = self._get_severity_from_attack_type(pred)
                final['recommendation'] = f'{model_name} detected {pred}. Investigate and apply IDS policy based on attack type.'
                return final
            else:
                # ML says BENIGN, but check other detectors as backup
                final['threat_detected'] = False
                final['attack_type'] = 'BENIGN'
                final['attack_label'] = 'BENIGN'
                final['status'] = 'Normal'
                final['severity'] = 'NONE'
                # Don't return here - continue to check other detectors as backup

        # 2) Port Scan Detector (backup/secondary detection - only if ML didn't detect threat)
        if scan_res.get('threat_detected'):
            final['threat_detected'] = True
            attack_type = scan_res.get('attack_type', 'PORT_SCAN')
            final['attack_type'] = attack_type
            final['attack_label'] = attack_type
            final['confidence'] = float(scan_res.get('confidence', 0.0) or 0.0)
            final['severity'] = scan_res.get('severity', 'MEDIUM')
            final['recommendation'] = scan_res.get('recommended_action')
            final['model_used'] = 'PortScanDetector (backup)'
            return final

        # 3) Heuristic (backup/secondary detection - only if ML didn't detect threat)
        if heuristic_res and heuristic_res.get('confidence', 0) > 0.5:
            final['threat_detected'] = True
            attack_type = heuristic_res.get('heuristic', 'UNKNOWN')
            final['attack_type'] = attack_type
            final['attack_label'] = attack_type
            final['confidence'] = float(heuristic_res.get('confidence', 0.0))
            final['severity'] = heuristic_res.get('severity', 'MEDIUM')
            final['recommendation'] = f"Heuristic detected {attack_type}"
            final['model_used'] = 'Heuristic (backup)'
            return final
        
        # If we get here, ML model said BENIGN and no other detector found threats
        if ml_res.get('ml_available'):
            return final

        # Default: benign
        final['attack_type'] = 'BENIGN'
        final['status'] = 'Normal'
        final['severity'] = 'NONE'
        return final
    
    def _get_severity_from_attack_type(self, attack_type: str) -> str:
        """Map attack type to severity level"""
        if not attack_type:
            return 'LOW'
        
        attack_upper = str(attack_type).upper()
        severity_map = {
            'BENIGN': 'NONE',
            'NORMAL': 'NONE',
            'DOS': 'HIGH',
            'DDOS': 'HIGH',
            'PORTSCAN': 'MEDIUM',
            'PORT_SCAN': 'MEDIUM',
            'BOT': 'HIGH',
            'INFILTRATION': 'CRITICAL',
            'WEBATTACK': 'HIGH',
            'WEB_ATTACK': 'HIGH',
            'FTP-PATATOR': 'MEDIUM',
            'SSH-PATATOR': 'MEDIUM',
            'BRUTEFORCE': 'HIGH',
            'BRUTE_FORCE': 'HIGH',
            'HEARTBLEED': 'CRITICAL',
            'EXPLOITS': 'HIGH',
            'BACKDOOR': 'CRITICAL',
            'SHELLCODE': 'CRITICAL',
            'WORMS': 'CRITICAL',
            'ANALYSIS': 'MEDIUM',
            'FUZZERS': 'MEDIUM',
            'RECONNAISSANCE': 'MEDIUM',
            'GENERIC': 'MEDIUM'
        }
        return severity_map.get(attack_upper, 'MEDIUM')

    def get_statistics(self, srcip: Optional[str] = None) -> Dict[str, Any]:
        if self.port_scan_detector:
            return self.port_scan_detector.get_statistics(srcip)
        return {'error': 'Port scan detector not available'}


# CLI quick test
if __name__ == '__main__':
    ids = CyberSentinelMod()
    sample = {
        'srcip': '192.168.1.100',
        'dstip': '10.0.1.10',
        'src_port': 54321,
        'dst_port': 22,
        'protocol': 'tcp',
        'packet_size': 120,
        'duration': 0.5,
        'flags': 2,
        'timestamp': datetime.utcnow().isoformat()
    }
    out = ids.analyze_packet(sample)
    import json
    print(json.dumps(out, indent=2))
