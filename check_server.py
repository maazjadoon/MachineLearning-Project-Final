#!/usr/bin/env python3
"""
Check if model server is running and accessible
"""

import socket
import json
import sys

def check_model_server(host='localhost', port=9999):
    """Check if model server is running"""
    try:
        # Try to connect to the server
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((host, port))
        
        # Send a test request
        test_data = {
            'srcip': '192.168.1.1',
            'dstip': '192.168.1.2',
            'src_port': 12345,
            'dst_port': 80,
            'protocol': 'tcp',
            'packet_size': 100,
            'duration': 0.1,
            'timestamp': '2024-01-01T00:00:00'
        }
        
        json_data = json.dumps(test_data)
        sock.send(json_data.encode('utf-8'))
        
        # Get response
        response = sock.recv(8192).decode('utf-8')
        result = json.loads(response)
        
        sock.close()
        
        print("✅ Model Server is running and responding")
        print(f"📊 Test result: {result.get('attack_type', 'No threat')}")
        print(f"🎯 Confidence: {result.get('confidence', 0):.2%}")
        print(f"⚠️  Threat detected: {result.get('threat_detected', False)}")
        
        return True
        
    except ConnectionRefusedError:
        print("❌ Model Server is not running or not accepting connections")
        print("💡 Start the model server with: python model_server.py")
        return False
        
    except socket.timeout:
        print("❌ Model Server timeout - server may be busy")
        return False
        
    except Exception as e:
        print(f"❌ Error connecting to Model Server: {e}")
        return False

def main():
    """Main check function"""
    print("🔍 Checking Cyber Sentinel Model Server")
    print("=" * 45)
    
    if check_model_server():
        print("\n🎉 Model Server is ready!")
        print("🌐 You can now start the web application:")
        print("   python run_fallback.py")
        print("   or")
        print("   python start_system.py")
    else:
        print("\n❌ Model Server is not ready")
        print("🚀 Please start it first:")
        print("   python model_server.py")
        sys.exit(1)

if __name__ == '__main__':
    main()
