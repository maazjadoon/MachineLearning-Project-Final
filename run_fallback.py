#!/usr/bin/env python3
"""
Fallback launcher for Cyber Sentinel ML
This script runs the system in API-only mode when packet capture is not available
"""

import os
import sys
import logging
import platform

def setup_fallback_environment():
    """Configure environment for fallback mode"""
    
    # Set environment variables for fallback mode
    os.environ['CYBER_SENTINEL_PRODUCTION'] = 'true'
    os.environ['LOG_LEVEL'] = 'INFO'
    os.environ['PACKET_CAPTURE_ENABLED'] = 'false'  # Disable packet capture
    os.environ['MAX_PACKETS_PER_SECOND'] = '0'
    
    print("🔧 Cyber Sentinel Fallback Mode Setup")
    print("=" * 50)
    print(f"🖥️  Platform: {platform.system()}")
    print(f"🐍 Python: {sys.version}")
    print()
    print("📋 Mode Configuration:")
    print("   ✅ Real Threat Detection: API Only")
    print("   ❌ Packet Capture: Disabled (Npcap issue)")
    print("   ✅ Web Dashboard: Available")
    print("   ✅ Manual API Testing: Available")
    print()
    print("💡 How to use this mode:")
    print("   1. Use the web dashboard to manually submit network data")
    print("   2. Use the /api/detect endpoint for threat analysis")
    print("   3. Use /api/test_port_scan for testing (simulated)")
    print("   4. Install Npcap later to enable real packet capture")
    print()
    
    # Check basic dependencies
    try:
        import scapy
        print("✅ Scapy is installed")
    except ImportError:
        print("❌ Scapy not installed")
        print("💡 Install with: pip install scapy")
        return False
    
    print("✅ Fallback mode ready")
    return True

def main():
    """Main fallback launcher"""
    
    # Setup fallback environment
    if not setup_fallback_environment():
        print("\n❌ Fallback setup failed. Please fix the issues above.")
        sys.exit(1)
    
    print("🚀 Starting Cyber Sentinel in FALLBACK MODE...")
    print("📡 API-based threat detection active...")
    print("🌐 Web dashboard available for manual testing...")
    print()
    
    # Import and run the main application
    try:
        from app import app, socketio, config
        
        # Display configuration
        mode_info = config.get_mode_info()
        print(f"🔧 Configuration:")
        print(f"   Mode: {mode_info['mode']} (FALLBACK)")
        print(f"   Real Threat Detection: {mode_info['real_threat_detection']}")
        print(f"   Packet Capture: {'Enabled' if mode_info['packet_capture_active'] else 'Disabled'}")
        print(f"   Sample Traffic: {'Enabled' if mode_info['sample_traffic_active'] else 'Disabled'}")
        print()
        
        print("🌐 Access your dashboard:")
        print(f"   Local: http://localhost:{config.WEB_PORT}")
        print(f"   Network: http://0.0.0.0:{config.WEB_PORT}")
        print()
        print("📝 Available features:")
        print("   ✅ Manual threat detection via /api/detect")
        print("   ✅ Test simulations via /api/test_port_scan")
        print("   ✅ Real-time dashboard")
        print("   ✅ Detection history")
        print("   ❌ Real packet capture (requires Npcap)")
        print()
        print("💡 To enable real packet capture:")
        print("   1. Download Npcap: https://npcap.com/")
        print("   2. Install with 'WinPcap API-compatible Mode'")
        print("   3. Run: python run_production.py")
        print()
        print("⚠️  Press Ctrl+C to stop the server")
        print("=" * 50)
        
        # Start the application
        socketio.run(
            app, 
            host=config.WEB_HOST, 
            port=config.WEB_PORT, 
            debug=config.DEBUG_MODE,
            allow_unsafe_werkzeug=True
        )
        
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down Cyber Sentinel...")
        print("✅ Server stopped")
    except Exception as e:
        print(f"\n❌ Failed to start Cyber Sentinel: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
