from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import socket
import json
import threading
import time
from datetime import datetime
import logging
import random
import os

# Import configuration
from config import get_config, Config

# Import attack categories
from attack_categories import AttackSubcategory, AttackCategory, auto_detector

# Get current configuration
config = get_config()

# Try to import packet capture
try:
    from packet_capture import PacketCapture
    PACKET_CAPTURE_AVAILABLE = True
except ImportError:
    PACKET_CAPTURE_AVAILABLE = False
    PacketCapture = None

# Configure logging based on mode
logging.basicConfig(level=getattr(logging, config.LOG_LEVEL))
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'cyber_sentinel_secret_2024')
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

class SocketClient:
    def __init__(self, host='localhost', port=9999):
        self.host = host
        self.port = port
        self.socket = None
        self.connect()
    
    def connect(self):
        """Connect to the model server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(5)  # 5 second timeout
            self.socket.connect((self.host, self.port))
            logger.info("✅ Connected to model server")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect to model server: {e}")
            self.socket = None
            return False
    
    def send_network_data(self, network_data):
        """Send network data to model server and get response"""
        if not self.socket:
            if not self.connect():
                return {"error": "Cannot connect to model server"}
        
        try:
            # Send data
            json_data = json.dumps(network_data)
            self.socket.send(json_data.encode('utf-8'))
            
            # Receive response
            response = self.socket.recv(8192).decode('utf-8')  # Increased buffer size
            return json.loads(response)
            
        except socket.timeout:
            logger.error("Socket timeout")
            self.socket = None
            return {"error": "Model server timeout"}
        except Exception as e:
            logger.error(f"Error communicating with model server: {e}")
            self.socket = None
            return {"error": str(e)}

# Global socket client
socket_client = SocketClient(
    host=config.MODEL_SERVER_HOST, 
    port=config.MODEL_SERVER_PORT
)

# Store detection history
detection_history = []

# Store threat detections separately for live display
threat_detections = []
threat_detections_lock = threading.Lock()

# Global packet capture instance (will be set in main)
packet_capture = None

@app.route('/')
def index():
    """Main dashboard"""
    return render_template('index.html')

@app.route('/detection')
def detection():
    """Real-time detection page"""
    return render_template('detection.html')

@app.route('/history')
def history():
    """Detection history page"""
    return render_template('history.html')

@app.route('/attack_categories')
def attack_categories():
    """Attack categories management page"""
    return render_template('attack_categories.html')

@app.route('/api/attack_categories', methods=['GET'])
def api_attack_categories():
    """Get all available attack categories and subcategories"""
    try:
        categories = AttackSubcategory.get_all_categories()
        enabled_attacks = auto_detector.get_enabled_attacks()
        
        return jsonify({
            'success': True,
            'categories': categories,
            'enabled_attacks': enabled_attacks,
            'total_categories': len(categories),
            'total_enabled': len(enabled_attacks)
        })
    except Exception as e:
        logger.error(f"Error getting attack categories: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/attack_categories/enable', methods=['POST'])
def api_enable_attack_detection():
    """Enable automatic detection for specific attack types"""
    try:
        data = request.json
        attack_ids = data.get('attack_ids', [])
        
        if not attack_ids:
            return jsonify({"error": "No attack IDs provided"}), 400
        
        # Validate attack IDs
        valid_attacks = []
        invalid_attacks = []
        
        for attack_id in attack_ids:
            info = AttackSubcategory.get_subcategory_info(attack_id)
            if info:
                valid_attacks.append(attack_id)
            else:
                invalid_attacks.append(attack_id)
        
        if invalid_attacks:
            return jsonify({
                "error": f"Invalid attack IDs: {invalid_attacks}"
            }), 400
        
        # Enable detection
        auto_detector.enable_attack_detection(valid_attacks)
        
        logger.info(f"✅ Enabled detection for {len(valid_attacks)} attack types: {valid_attacks}")
        
        return jsonify({
            'success': True,
            'message': f'Enabled detection for {len(valid_attacks)} attack types',
            'enabled_attacks': valid_attacks,
            'current_enabled': auto_detector.get_enabled_attacks()
        })
        
    except Exception as e:
        logger.error(f"Error enabling attack detection: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/attack_categories/disable', methods=['POST'])
def api_disable_attack_detection():
    """Disable detection for specific attack types"""
    try:
        data = request.json
        attack_ids = data.get('attack_ids', [])
        
        if not attack_ids:
            return jsonify({"error": "No attack IDs provided"}), 400
        
        # Disable detection
        auto_detector.disable_attack_detection(attack_ids)
        
        logger.info(f"🚫 Disabled detection for {len(attack_ids)} attack types: {attack_ids}")
        
        return jsonify({
            'success': True,
            'message': f'Disabled detection for {len(attack_ids)} attack types',
            'disabled_attacks': attack_ids,
            'current_enabled': auto_detector.get_enabled_attacks()
        })
        
    except Exception as e:
        logger.error(f"Error disabling attack detection: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/attack_categories/<attack_id>', methods=['GET'])
def api_attack_category_info(attack_id):
    """Get detailed information about a specific attack category"""
    try:
        info = AttackSubcategory.get_subcategory_info(attack_id)
        rules = AttackSubcategory.get_detection_rules(attack_id)
        
        if not info:
            return jsonify({"error": "Attack category not found"}), 404
        
        return jsonify({
            'success': True,
            'attack_info': info,
            'detection_rules': rules,
            'is_enabled': attack_id in auto_detector.enabled_attacks
        })
        
    except Exception as e:
        logger.error(f"Error getting attack category info: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/detect', methods=['POST'])
def api_detect():
    """API endpoint for threat detection (can be used for manual testing with JSON payload)"""
    try:
        network_data = request.json
        
        if not network_data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        # Add timestamp
        network_data['timestamp'] = datetime.now().isoformat()
        
        # Log that this is a manual API call (not from packet capture)
        logger.info(f"📥 API /detect called with data: {network_data.get('srcip')} -> {network_data.get('dstip')}")
        
        # Run automatic detection for enabled attack types
        auto_detections = auto_detector.analyze_packet(network_data)
        
        # Send to model server via socket
        result = socket_client.send_network_data(network_data)
        
        # If automatic detection found threats, prioritize them
        if auto_detections:
            # Use the highest confidence automatic detection
            best_detection = max(auto_detections, key=lambda x: x['confidence'])
            result.update({
                'threat_detected': True,
                'attack_type': best_detection['attack_name'],
                'attack_category': best_detection['category'],
                'confidence': best_detection['confidence'],
                'severity': best_detection['severity'],
                'detection_method': 'automatic_rules',
                'auto_response': best_detection['auto_response'],
                'matched_rules': best_detection['matched_rules'],
                'description': best_detection['description']
            })
            
            logger.warning(
                f"🚨 AUTOMATIC DETECTION: {best_detection['attack_name']} "
                f"from {network_data.get('srcip')} to {network_data.get('dstip')} "
                f"| Confidence: {best_detection['confidence']:.2%} | "
                f"Severity: {best_detection['severity']} | "
                f"Category: {best_detection['category']}"
            )
        
        # IMPORTANT: Add to threat detections list if threat detected
        # This ensures the detection is stored and visible in the Flask UI
        threat_detection = add_threat_detection(network_data, result)
        
        if threat_detection:
            logger.info(f"✅ Detection stored in threat_detections list (total: {len(threat_detections)})")
        else:
            if result.get('threat_detected'):
                logger.warning("⚠️ Threat detected but NOT stored (may be rate-limited or error)")
        
        # Emit new_detection event for real-time updates
        if threat_detection:
            socketio.emit('new_detection', threat_detection)
            logger.info("📡 Emitted new_detection event via SocketIO")
        
        # Store in history
        if 'error' not in result:
            detection_history.append({
                'timestamp': network_data['timestamp'],
                'source_ip': network_data.get('srcip', 'unknown'),
                'destination_ip': network_data.get('dstip', 'unknown'),
                'protocol': network_data.get('protocol', 'unknown'),
                'result': result
            })
            
            # Keep only last 1000 entries
            if len(detection_history) > 1000:
                detection_history.pop(0)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"API error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/stats')
def api_stats():
    """Get system statistics"""
    threats_detected = sum(1 for d in detection_history if d['result'].get('threat_detected', False))
    
    # Get packet capture stats if available
    capture_stats = {}
    if PACKET_CAPTURE_AVAILABLE:
        try:
            # Access the global packet_capture instance
            global packet_capture
            if packet_capture:
                capture_stats = packet_capture.get_statistics()
        except Exception as e:
            logger.debug(f"Error getting capture stats: {e}")
    
    # Count threat detections from global list
    with threat_detections_lock:
        live_threats_count = len(threat_detections)
        
        # Count by severity
        critical_threats = sum(1 for t in threat_detections if t.get('severity', '').upper() == 'CRITICAL')
        high_threats = sum(1 for t in threat_detections if t.get('severity', '').upper() == 'HIGH')
        medium_threats = sum(1 for t in threat_detections if t.get('severity', '').upper() == 'MEDIUM')
        low_threats = sum(1 for t in threat_detections if t.get('severity', '').upper() == 'LOW')
        
        # Count by attack type
        attack_types = {}
        for t in threat_detections:
            attack_type = t.get('attack_type', 'Unknown')
            attack_types[attack_type] = attack_types.get(attack_type, 0) + 1
    
    # AI Model status
    model_status = {
        'connected': socket_client.socket is not None,
        'model_server_running': socket_client.socket is not None,
        'models_loaded': 1 if socket_client.socket else 0,
        'total_models': 1,  # CyberSentinel model
        'model_names': ['CyberSentinel CICIDS2017'] if socket_client.socket else []
    }
    
    stats = {
        'total_detections': len(detection_history),
        'threats_detected': threats_detected,
        'normal_traffic': len(detection_history) - threats_detected,
        'system_status': 'operational' if socket_client.socket else 'disconnected',
        'recent_activity': detection_history[-10:] if detection_history else [],
        'live_threats': {
            'total': live_threats_count,
            'critical': critical_threats,
            'high': high_threats,
            'medium': medium_threats,
            'low': low_threats,
            'by_type': attack_types
        },
        'ai_models': model_status,
        'packet_capture': {
            'available': PACKET_CAPTURE_AVAILABLE,
            'running': capture_stats.get('running', False),
            'total_packets': capture_stats.get('total_packets', 0),
            'packets_analyzed': capture_stats.get('packets_analyzed', 0),
            'threats_detected': capture_stats.get('threats_detected', 0),
            'packets_per_second': capture_stats.get('packets_per_second', 0)
        },
        'rate_limiting': {
            'enabled': True,
            'limit_seconds': THREAT_RATE_LIMIT_SECONDS,
            'active_limits': len(threat_rate_limiter)
        }
    }
    return jsonify(stats)

@app.route('/api/history')
def api_history():
    """Get detection history"""
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    
    history_page = detection_history[::-1][start_idx:end_idx]  # Reverse for newest first
    
    return jsonify({
        'history': history_page,
        'total_pages': (len(detection_history) + per_page - 1) // per_page,
        'current_page': page,
        'total_detections': len(detection_history)
    })

@app.route('/detections')
def get_detections():
    """Get all threat detections as JSON"""
    with threat_detections_lock:
        # Return detections in reverse order (newest first)
        detections = threat_detections[::-1]
    
    return jsonify({
        'detections': detections,
        'total': len(detections),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/feedback', methods=['POST'])
def api_feedback():
    """Submit labeled sample for online learning"""
    try:
        payload = request.json
        if not payload:
            return jsonify({"error": "No JSON payload"}), 400
        if 'label' not in payload:
            return jsonify({"error": "Missing 'label' field"}), 400

        payload['timestamp'] = datetime.now().isoformat()
        result = socket_client.send_network_data(payload)

        # record feedback in history if accepted
        if 'error' not in result:
            detection_history.append({
                'timestamp': payload['timestamp'],
                'source_ip': payload.get('srcip', 'unknown'),
                'destination_ip': payload.get('dstip', 'unknown'),
                'protocol': payload.get('protocol', 'unknown'),
                'result': result,
                'feedback': True
            })
            if len(detection_history) > 1000:
                detection_history.pop(0)

        return jsonify(result)
    except Exception as e:
        logger.error(f"Feedback API error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/test_port_scan', methods=['POST'])
def api_test_port_scan():
    """TEST/SIMULATION ONLY: Simulate a port scan attack for demonstration purposes"""
    try:
        logger.warning("🧪 TEST MODE: Starting port scan simulation (NOT REAL THREAT)")
        
        # SIMULATED port scanning activity - these are fake IPs for testing
        attacker_ip = "TEST.192.168.1.100"  # Clearly marked as test IP
        target_ip = "TEST.10.0.0.50"        # Clearly marked as test IP
        
        results = []
        threats_detected = 0
        
        # Simulate scanning 20 ports rapidly
        for port in range(20, 40):
            scan_packet = {
                'srcip': attacker_ip,
                'dstip': target_ip,
                'src_port': 54321,
                'dst_port': port,
                'protocol': 'tcp',
                'flags': 2,  # SYN flag only (stealth scan)
                'packet_size': 60,
                'duration': 0.01,
                'timestamp': datetime.now().isoformat()
            }
            
            # Send to model server
            result = socket_client.send_network_data(scan_packet)
            results.append(result)
            
            # Check if threat detected
            if result.get('threat_detected'):
                threats_detected += 1
            
            # Store in history
            if 'error' not in result:
                detection_history.append({
                    'timestamp': scan_packet['timestamp'],
                    'source_ip': attacker_ip,
                    'destination_ip': target_ip,
                    'protocol': 'tcp',
                    'result': result
                })
            
            # Add to threat detections if threat detected
            threat_detection = add_threat_detection(scan_packet, result)
            
            # Emit via WebSocket for real-time display (FIXED - removed broadcast)
            socketio.emit('threat_update', {
                'timestamp': scan_packet['timestamp'],
                'data': scan_packet,
                'result': result
            })
            
            # Also emit new_detection event for real-time updates
            if threat_detection:
                socketio.emit('new_detection', threat_detection)
            
            # Small delay to simulate realistic scanning
            time.sleep(0.1)
        
        final_result = results[-1] if results else {"error": "No results"}
        
        logger.info(f"🧪 TEST COMPLETED: {len(results)} SIMULATED packets sent, {threats_detected} threats detected")
        
        return jsonify({
            'success': True,
            'message': 'SIMULATION COMPLETED - This was a test, not a real attack',
            'packets_sent': len(results),
            'threats_detected': threats_detected,
            'final_result': final_result,
            'all_results': results[-5:],  # Last 5 results
            'test_mode': True  # Clearly indicate this was a test
        })
        
    except Exception as e:
        logger.error(f"Port scan test error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Port scan test failed'
        }), 500

@app.route('/api/port_scan_stats')
def api_port_scan_stats():
    """Get port scan detection statistics"""
    try:
        # Request stats from model server via socket
        stats_request = {
            'command': 'get_port_scan_stats'
        }
        
        result = socket_client.send_network_data(stats_request)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error getting port scan stats: {e}")
        return jsonify({"error": str(e)}), 500

# Rate limiting for threat detections (configurable)
threat_rate_limiter = {}
THREAT_RATE_LIMIT_SECONDS = config.THREAT_RATE_LIMIT_SECONDS

@app.route('/api/rate_limit', methods=['GET', 'POST'])
def api_rate_limit():
    """Get or set rate limiting configuration"""
    global THREAT_RATE_LIMIT_SECONDS
    
    if request.method == 'POST':
        try:
            data = request.json
            new_limit = int(data.get('seconds', THREAT_RATE_LIMIT_SECONDS))
            if 1 <= new_limit <= 60:  # Allow 1-60 seconds
                THREAT_RATE_LIMIT_SECONDS = new_limit
                # Clear existing rate limiter to apply new settings
                threat_rate_limiter.clear()
                return jsonify({
                    'success': True,
                    'message': f'Rate limit updated to {new_limit} seconds',
                    'rate_limit_seconds': THREAT_RATE_LIMIT_SECONDS
                })
            else:
                return jsonify({'error': 'Rate limit must be between 1 and 60 seconds'}), 400
        except Exception as e:
            return jsonify({'error': str(e)}), 400
    
    return jsonify({
        'rate_limit_seconds': THREAT_RATE_LIMIT_SECONDS,
        'active_rate_limits': len(threat_rate_limiter)
    })

def add_threat_detection(packet_data, result):
    """Add a threat detection to the global threat_detections list (thread-safe) with rate limiting
    
    This function is called by:
    1. Packet capture when real threats are detected from network traffic
    2. API /detect endpoint when manual detections are made
    3. WebSocket realtime_detection handler
    
    All detections are stored in the global threat_detections list which is
    accessible via the /detections endpoint for the Flask UI.
    """
    if not result:
        logger.warning("add_threat_detection called with None result")
        return None
        
    if result.get('threat_detected'):
        # Create rate limiting key
        rate_key = f"{result.get('attack_type', 'Unknown')}_{packet_data.get('srcip', 'unknown')}"
        current_time = time.time()
        
        # Check rate limiting
        if rate_key in threat_rate_limiter:
            if current_time - threat_rate_limiter[rate_key] < THREAT_RATE_LIMIT_SECONDS:
                # Skip this detection due to rate limiting
                logger.debug(f"⏭️ Detection rate-limited: {rate_key}")
                return None
        
        # Update rate limiter
        threat_rate_limiter[rate_key] = current_time
        
        # Clean old entries from rate limiter (keep it from growing indefinitely)
        keys_to_remove = [k for k, v in threat_rate_limiter.items() if current_time - v > THREAT_RATE_LIMIT_SECONDS * 2]
        for k in keys_to_remove:
            del threat_rate_limiter[k]
        
        detection = {
            'timestamp': packet_data.get('timestamp', datetime.now().isoformat()),
            'attack_type': result.get('attack_type', 'Unknown'),
            'source_ip': packet_data.get('srcip', 'unknown'),
            'destination_ip': packet_data.get('dstip', 'unknown'),
            'confidence': result.get('confidence', 0.0),
            'severity': result.get('severity', 'UNKNOWN'),
            'protocol': packet_data.get('protocol', 'unknown'),
            'src_port': packet_data.get('src_port', 0),
            'dst_port': packet_data.get('dst_port', 0),
            'model_used': result.get('model_used', result.get('detection_method', 'Unknown')),
            'recommended_action': result.get('recommended_action', 'Investigate further')
        }
        
        # CRITICAL: Store detection in global list (this is what the Flask UI reads from)
        with threat_detections_lock:
            threat_detections.append(detection)
            total_count = len(threat_detections)
            # Keep only last 500 detections (reduced from 1000)
            if len(threat_detections) > 500:
                threat_detections.pop(0)
        
        logger.info(f"💾 Detection stored in threat_detections list (total stored: {total_count})")
        
        # Also log to terminal (preserve existing behavior)
        logger.warning(
            f"🚨 THREAT DETECTED: {detection['attack_type']} "
            f"from {detection['source_ip']} to {detection['destination_ip']} | "
            f"Confidence: {detection['confidence']:.2%} | "
            f"Severity: {detection['severity']}"
        )
        
        # Emit stats update via WebSocket for real-time dashboard updates
        try:
            socketio.emit('stats_update', {
                'total_threats': len(threat_detections),
                'new_threat': detection,
                'timestamp': detection['timestamp']
            })
        except Exception as e:
            logger.debug(f"Error emitting stats update: {e}")
        
        return detection
    else:
        logger.debug(f"No threat detected in result: {result.get('attack_type', 'Normal traffic')}")
    return None

@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection"""
    logger.info('Client connected via WebSocket')
    emit('status', {'message': 'Connected to Cyber Sentinel', 'status': 'connected'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection"""
    logger.info('Client disconnected')

@socketio.on('realtime_detection')
def handle_realtime_detection(data):
    """Handle real-time detection via WebSocket"""
    try:
        # Send to model server
        result = socket_client.send_network_data(data)
        
        # Add timestamp if not present
        if 'timestamp' not in data:
            data['timestamp'] = datetime.now().isoformat()
        
        # Add to threat detections if threat detected
        threat_detection = add_threat_detection(data, result)
        
        # Emit to all connected clients (FIXED - removed broadcast)
        emit('threat_update', {
            'timestamp': data.get('timestamp', datetime.now().isoformat()),
            'data': data,
            'result': result
        })
        
        # Also emit new_detection event for real-time updates
        if threat_detection:
            socketio.emit('new_detection', threat_detection)
        
        # Store in history
        if 'error' not in result:
            detection_history.append({
                'timestamp': data.get('timestamp', datetime.now().isoformat()),
                'source_ip': data.get('srcip', 'unknown'),
                'destination_ip': data.get('dstip', 'unknown'),
                'protocol': data.get('protocol', 'unknown'),
                'result': result
            })
            
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        emit('error', {'message': str(e)})

@socketio.on('label_feedback')
def handle_label_feedback(data):
    """Receive labeled sample via WebSocket and forward to model server"""
    try:
        data['timestamp'] = datetime.now().isoformat()
        result = socket_client.send_network_data(data)

        # acknowledge back to sender
        emit('feedback_ack', {'result': result})

        # store in history if accepted
        if 'error' not in result:
            detection_history.append({
                'timestamp': data['timestamp'],
                'source_ip': data.get('srcip', 'unknown'),
                'destination_ip': data.get('dstip', 'unknown'),
                'protocol': data.get('protocol', 'unknown'),
                'result': result,
                'feedback': True
            })
            if len(detection_history) > 1000:
                detection_history.pop(0)

    except Exception as e:
        logger.error(f"WebSocket feedback error: {e}")
        emit('error', {'message': str(e)})

def generate_sample_traffic():
    """Generate sample network traffic for demonstration (CONFIGURABLE)"""
    # Check if sample traffic is enabled in configuration
    if not config.SAMPLE_TRAFFIC_ENABLED:
        return  # Disabled in production mode
    
    protocols = ['tcp', 'udp', 'icmp']
    attack_types = ['normal', 'dos', 'exploit', 'reconnaissance']
    
    while True:
        time.sleep(3)  # Generate every 3 seconds
        
        # Create realistic sample data
        sample_data = {
            'srcip': f"192.168.1.{random.randint(1, 255)}",
            'dstip': f"10.0.0.{random.randint(1, 255)}",
            'src_port': random.randint(1024, 65535),
            'dst_port': random.choice([80, 443, 22, 53, 3389]),
            'protocol': random.choice(protocols),
            'packet_size': random.randint(64, 1500),
            'duration': random.uniform(0.1, 10.0),
            'flags': random.randint(1, 255)
        }
        
        # Occasionally generate attack-like patterns (30% chance)
        if random.random() < 0.3:
            sample_data['packet_size'] = random.randint(1000, 1500)
            sample_data['duration'] = random.uniform(5.0, 10.0)
            sample_data['flags'] = random.choice([2, 4, 8])  # Suspicious flags
        
        # Send via WebSocket
        socketio.emit('sample_traffic', sample_data)

if __name__ == '__main__':
    # Display current mode information
    mode_info = config.get_mode_info()
    logger.info("🔧 Cyber Sentinel Configuration:")
    logger.info(f"   Mode: {mode_info['mode']}")
    logger.info(f"   Real Threat Detection: {mode_info['real_threat_detection']}")
    logger.info(f"   Packet Capture: {'Enabled' if mode_info['packet_capture_active'] else 'Disabled'}")
    logger.info(f"   Sample Traffic: {'Enabled' if mode_info['sample_traffic_active'] else 'Disabled'}")
    logger.info(f"   Debug Mode: {mode_info['debug_mode']}")
    
    # Start sample traffic generator if enabled
    if config.SAMPLE_TRAFFIC_ENABLED:
        logger.info("🧪 Starting sample traffic generator (TEST MODE)")
        traffic_thread = threading.Thread(target=generate_sample_traffic, daemon=True)
        traffic_thread.start()
    else:
        logger.info("🚫 Sample traffic disabled (PRODUCTION MODE)")
    
    # Start real-time packet capture if available and enabled
    if config.PACKET_CAPTURE_ENABLED and PACKET_CAPTURE_AVAILABLE:
        try:
            # Get available network interfaces for real monitoring
            packet_capture_instance = PacketCapture()
            available_interfaces = packet_capture_instance._get_available_interfaces()
            
            if available_interfaces:
                logger.info(f"🌐 Available network interfaces: {available_interfaces}")
                
                # Use first available interface for real monitoring
                monitor_interface = None
                interface_found = False
                
                if available_interfaces:
                    # Prioritize Wi-Fi interface (should be first if found)
                    monitor_interface = available_interfaces[0]
                    # Check if first interface is Wi-Fi
                    iface_lower = monitor_interface.lower()
                    is_wifi = 'wi-fi' in iface_lower or 'wifi' in iface_lower or 'wireless' in iface_lower
                    if is_wifi:
                        logger.info(f"📶 Selected Wi-Fi interface for monitoring: {monitor_interface}")
                    else:
                        logger.info(f"🎯 Selected interface for monitoring: {monitor_interface}")
                        # Try to find Wi-Fi in the list
                        for iface in available_interfaces:
                            iface_lower = iface.lower()
                            if 'wi-fi' in iface_lower or 'wifi' in iface_lower or 'wireless' in iface_lower:
                                monitor_interface = iface
                                logger.info(f"📶 Found and selected Wi-Fi interface: {monitor_interface}")
                                break
                    
                    # Try to start packet capture and test if it works
                    test_capture = PacketCapture(
                        model_server_host=config.MODEL_SERVER_HOST,
                        model_server_port=config.MODEL_SERVER_PORT,
                        interface=monitor_interface,
                        filter_str="tcp or udp",
                        max_packets_per_second=1,  # Very low rate for testing
                        socketio=None,
                        threat_callback=None
                    )
                    
                    # Quick test to see if interface works
                    logger.info(f"🧪 Testing interface {monitor_interface}...")
                    test_success, needs_fallback = test_capture._test_interface()
                    if not test_success:
                        logger.warning(f"⚠️ Interface {monitor_interface} failed test, trying next...")
                        # Try next interface
                        for i, iface in enumerate(available_interfaces[1:], 1):
                            logger.info(f"🧪 Testing interface {iface}...")
                            test_capture.interface = iface
                            test_success, needs_fallback = test_capture._test_interface()
                            if test_success:
                                monitor_interface = iface if not needs_fallback else None
                                logger.info(f"✅ Interface {iface} works!" if not needs_fallback else f"✅ Interface {iface} needs fallback, using all interfaces")
                                interface_found = True
                                break
                        else:
                            logger.error("❌ No working interfaces found")
                            packet_capture = None
                            interface_found = False
                    else:
                        # If test succeeded but needs fallback, set interface to None
                        if needs_fallback:
                            logger.info(f"⚠️ Interface {monitor_interface} needs fallback, will use all interfaces")
                            monitor_interface = None
                        # Check if test_capture found a Wi-Fi friendly name
                        elif hasattr(test_capture, '_wifi_name') and test_capture._wifi_name:
                            monitor_interface = test_capture._wifi_name
                            logger.info(f"📶 Using Wi-Fi friendly name: {monitor_interface}")
                        interface_found = True
                else:
                    logger.error("❌ No network interfaces available")
                    packet_capture = None
                    interface_found = False
                
                # Only proceed if we found a working interface (monitor_interface can be None for fallback)
                if interface_found:
                    packet_capture = PacketCapture(
                        model_server_host=config.MODEL_SERVER_HOST,
                        model_server_port=config.MODEL_SERVER_PORT,
                        interface=monitor_interface,  # Use specific interface for real monitoring
                        filter_str="tcp or udp",  # Focus on TCP/UDP for threat detection
                        max_packets_per_second=config.MAX_PACKETS_PER_SECOND,  # Use config value
                        socketio=socketio,  # Pass SocketIO instance for real-time updates
                        threat_callback=add_threat_detection  # Callback to add threats to global list
                    )
                    if packet_capture.start_capture():
                        logger.info("✅ Real-time packet capture started on production interface")
                        logger.info("📡 Monitoring REAL network traffic for threats...")
                        logger.info("🔍 All detections now represent actual network activity")
                    else:
                        logger.warning("⚠️ Failed to start packet capture (may need admin privileges)")
                        logger.warning("💡 Run as Administrator on Windows for real network monitoring")
                        packet_capture = None
                else:
                    logger.warning("⚠️ No working network interfaces found")
                    logger.info("💡 Trying fallback: capture on all interfaces (iface=None)")
                    # Try fallback: capture on all interfaces
                    try:
                        packet_capture = PacketCapture(
                            model_server_host=config.MODEL_SERVER_HOST,
                            model_server_port=config.MODEL_SERVER_PORT,
                            interface=None,  # Use None to capture on all interfaces
                            filter_str="tcp or udp",
                            max_packets_per_second=config.MAX_PACKETS_PER_SECOND,
                            socketio=socketio,
                            threat_callback=add_threat_detection
                        )
                        if packet_capture.start_capture():
                            logger.info("✅ Packet capture started on all interfaces (fallback mode)")
                            logger.info("📡 Monitoring network traffic for threats...")
                        else:
                            logger.warning("⚠️ Fallback capture also failed")
                            packet_capture = None
                    except Exception as e:
                        logger.error(f"❌ Fallback capture failed: {e}")
                        packet_capture = None
                
        except Exception as e:
            logger.error(f"❌ Error starting packet capture: {e}")
            logger.error("💡 For real network monitoring:")
            logger.error("   1. Run as Administrator/root")
            logger.error("   2. Install Npcap on Windows: https://npcap.com/")
            logger.error("   3. Install Scapy: pip install scapy")
            packet_capture = None
    else:
        if not config.PACKET_CAPTURE_ENABLED:
            logger.info("🚫 Packet capture disabled in configuration")
        elif not PACKET_CAPTURE_AVAILABLE:
            logger.warning("⚠️ Packet capture not available. Install Scapy: pip install scapy")
            logger.warning("On Windows, also install Npcap: https://npcap.com/")
    
    logger.info("🚀 Starting Cyber Sentinel Web Application...")
    logger.info(f"📊 Dashboard: http://{config.WEB_HOST}:{config.WEB_PORT}")
    logger.info(f"🔍 Real-time Detection: http://{config.WEB_HOST}:{config.WEB_PORT}/detection")
    logger.info(f"📈 History: http://{config.WEB_HOST}:{config.WEB_PORT}/history")
    
    try:
        socketio.run(app, host=config.WEB_HOST, port=config.WEB_PORT, debug=config.DEBUG_MODE, allow_unsafe_werkzeug=True)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        if packet_capture:
            packet_capture.stop_capture()