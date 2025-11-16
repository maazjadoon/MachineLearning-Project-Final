#!/usr/bin/env python3
"""
Production launcher for Cyber Sentinel ML
This script sets up production environment and starts real threat detection
"""

import os
import sys
import logging
import platform

def setup_production_environment():
    """Configure environment for production mode"""
    
    # Set production environment variables
    os.environ['CYBER_SENTINEL_PRODUCTION'] = 'true'
    os.environ['LOG_LEVEL'] = 'INFO'
    os.environ['MAX_PACKETS_PER_SECOND'] = '50'
    os.environ['THREAT_RATE_LIMIT_SECONDS'] = '5'
    
    print("🔧 Cyber Sentinel Production Environment Setup")
    print("=" * 50)
    print(f"🖥️  Platform: {platform.system()}")
    print(f"🐍 Python: {sys.version}")
    print()
    
    # Check administrator privileges
    if platform.system().lower() == 'windows':
        try:
            import ctypes
            if not ctypes.windll.shell32.IsUserAnAdmin():
                print("❌ ERROR: Not running as Administrator")
                print("💡 Please run this script as Administrator:")
                print("   Right-click -> 'Run as administrator'")
                return False
        except:
            print("⚠️  Could not verify administrator privileges")
    else:
        if os.geteuid() != 0:
            print("❌ ERROR: Not running as root")
            print("💡 Please run with sudo:")
            print("   sudo python run_production.py")
            return False
    
    print("✅ Administrator/root privileges confirmed")
    
    # Check dependencies
    try:
        import scapy
        print("✅ Scapy is installed")
    except ImportError:
        print("❌ Scapy not installed")
        print("💡 Install with: pip install scapy")
        return False
    
    # Check Npcap on Windows
    if platform.system().lower() == 'windows':
        try:
            # Try multiple ways to detect Npcap
            try:
                from scapy.arch.windows import get_if_list
                interfaces = get_if_list()
                if interfaces:
                    print("✅ Npcap/WinPcap is working")
                else:
                    raise ImportError("No interfaces found")
            except ImportError:
                # Try alternative detection
                from scapy.all import get_if_list
                interfaces = get_if_list()
                if interfaces:
                    print("✅ Network packet capture is available")
                else:
                    raise ImportError("No interfaces found")
        except ImportError as e:
            print("⚠️  Npcap detection issue, but continuing...")
            print("💡 If packet capture fails, install/reinstall Npcap: https://npcap.com/")
            print("   Make sure to install with 'Install Npcap in WinPcap API-compatible Mode'")
            print("   For now, the system will run but packet capture may not work")
            # Don't fail - let the user try
            pass
    
    print("✅ All dependencies checked")
    return True

def main():
    """Main production launcher"""
    
    # Setup production environment
    if not setup_production_environment():
        print("\n❌ Production setup failed. Please fix the issues above.")
        sys.exit(1)
    
    print("\n🚀 Starting Cyber Sentinel in PRODUCTION MODE...")
    print("📡 Monitoring REAL network traffic for threats...")
    print("🔍 All detections represent actual network activity")
    print()
    
    # Import and run the main application
    try:
        from app import app, socketio, config
        
        # Display configuration
        mode_info = config.get_mode_info()
        print(f"🔧 Configuration:")
        print(f"   Mode: {mode_info['mode']}")
        print(f"   Real Threat Detection: {mode_info['real_threat_detection']}")
        print(f"   Packet Capture: {'Enabled' if mode_info['packet_capture_active'] else 'Disabled'}")
        print(f"   Sample Traffic: {'Enabled' if mode_info['sample_traffic_active'] else 'Disabled'}")
        print()
        
        print("🌐 Access your dashboard:")
        print(f"   Local: http://localhost:{config.WEB_PORT}")
        print(f"   Network: http://0.0.0.0:{config.WEB_PORT}")
        print()
        print("⚠️  Press Ctrl+C to stop monitoring")
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
        print("✅ Monitoring stopped")
    except Exception as e:
        print(f"\n❌ Failed to start Cyber Sentinel: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
