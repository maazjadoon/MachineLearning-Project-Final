#!/usr/bin/env python3
"""
Test script to check network interface availability and permissions
Run this to diagnose packet capture issues
"""

import logging
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_scapy_installation():
    """Test if Scapy is properly installed"""
    try:
        from scapy.all import sniff, get_if_list
        logger.info("✅ Scapy is installed and working")
        return True
    except ImportError as e:
        logger.error(f"❌ Scapy not installed: {e}")
        logger.error("Install with: pip install scapy")
        return False
    except Exception as e:
        logger.error(f"❌ Scapy installation issue: {e}")
        return False

def test_interface_list():
    """Test getting network interfaces"""
    try:
        from scapy.all import get_if_list
        interfaces = get_if_list()
        logger.info(f"📡 Found {len(interfaces)} network interfaces:")
        
        for i, iface in enumerate(interfaces):
            logger.info(f"   {i+1}. {iface}")
        
        return interfaces
    except Exception as e:
        logger.error(f"❌ Error getting interfaces: {e}")
        return []

def test_packet_capture(interface_name=None):
    """Test packet capture on a specific interface"""
    try:
        from scapy.all import sniff, IP
        import time
        
        if interface_name is None:
            # Get first non-loopback interface
            interfaces = test_interface_list()
            for iface in interfaces:
                if not iface.startswith('lo') and not iface.startswith('Loopback'):
                    interface_name = iface
                    break
            
            if interface_name is None and interfaces:
                interface_name = interfaces[0]
        
        if interface_name is None:
            logger.error("❌ No suitable interface found for testing")
            return False
        
        logger.info(f"🧪 Testing packet capture on: {interface_name}")
        logger.info("⏱️  Capturing for 10 seconds...")
        
        packet_count = 0
        def packet_handler(packet):
            nonlocal packet_count
            packet_count += 1
            if IP in packet:
                logger.info(f"   📦 Packet {packet_count}: {packet[IP].src} -> {packet[IP].dst}")
        
        # Capture packets for 10 seconds
        sniff(
            iface=interface_name,
            prn=packet_handler,
            timeout=10,
            store=False
        )
        
        logger.info(f"✅ Successfully captured {packet_count} packets")
        return True
        
    except PermissionError:
        logger.error("❌ Permission denied - run as Administrator (Windows) or root (Linux/Mac)")
        return False
    except OSError as e:
        logger.error(f"❌ Network interface error: {e}")
        logger.error("   This might indicate:")
        logger.error("   - Interface is disabled")
        logger.error("   - Npcap/winpcap not properly installed")
        logger.error("   - Network driver issues")
        return False
    except Exception as e:
        logger.error(f"❌ Packet capture failed: {e}")
        return False

def test_npcap_installation():
    """Test Npcap installation on Windows"""
    try:
        import platform
        if platform.system().lower() != 'windows':
            logger.info("ℹ️  Not running on Windows - Npcap check skipped")
            return True
        
        # Try to import Npcap-specific modules
        from scapy.arch.windows import get_if_list
        logger.info("✅ Npcap/WinPcap appears to be working")
        return True
        
    except ImportError as e:
        logger.error(f"❌ Npcap issue detected: {e}")
        logger.error("   Download and install Npcap: https://npcap.com/")
        logger.error("   Make sure to install with 'Install Npcap in WinPcap API-compatible Mode'")
        return False
    except Exception as e:
        logger.error(f"❌ Npcap installation issue: {e}")
        return False

def main():
    """Main test function"""
    logger.info("🔧 Cyber Sentinel Network Interface Test")
    logger.info("=" * 50)
    
    # Test 1: Scapy installation
    if not test_scapy_installation():
        sys.exit(1)
    
    # Test 2: Npcap installation (Windows)
    test_npcap_installation()
    
    # Test 3: Interface listing
    interfaces = test_interface_list()
    if not interfaces:
        logger.error("❌ No network interfaces found")
        sys.exit(1)
    
    # Test 4: Packet capture
    logger.info("\n🧪 Starting packet capture test...")
    if test_packet_capture():
        logger.info("🎉 All tests passed! Packet capture should work.")
    else:
        logger.error("❌ Packet capture test failed.")
        logger.info("\n💡 Troubleshooting tips:")
        logger.info("   1. Run this script as Administrator (Windows) or root (Linux/Mac)")
        logger.info("   2. Install/reinstall Npcap: https://npcap.com/")
        logger.info("   3. Disable VPN software temporarily")
        logger.info("   4. Check if network adapters are enabled")
        logger.info("   5. Try restarting your network services")
        sys.exit(1)

if __name__ == '__main__':
    main()
