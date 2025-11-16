"""
Test script to check if Scapy is working
"""
import sys

print("=" * 60)
print("Testing Scapy Installation")
print("=" * 60)

# Test 1: Check if Scapy is installed
try:
    import scapy
    print("[OK] Scapy is installed")
    try:
        print(f"   Version: {scapy.__version__}")
    except:
        print("   Version: Unknown")
except ImportError as e:
    print("[ERROR] Scapy is NOT installed")
    print(f"   Error: {e}")
    print("\nTo install Scapy:")
    print("   pip install scapy")
    print("\nOn Windows, also install Npcap:")
    print("   Download from: https://npcap.com/")
    sys.exit(1)

# Test 2: Check if we can import required modules
print("\n" + "=" * 60)
print("Testing Scapy Imports")
print("=" * 60)

modules_to_test = [
    ('scapy.all', 'sniff'),
    ('scapy.all', 'IP'),
    ('scapy.all', 'TCP'),
    ('scapy.all', 'UDP'),
    ('scapy.all', 'ICMP'),
    ('scapy.all', 'get_if_list'),
]

all_ok = True
for module, item in modules_to_test:
    try:
        if module == 'scapy.all':
            from scapy.all import sniff, IP, TCP, UDP, ICMP, get_if_list
            print(f"[OK] Successfully imported {item} from {module}")
        else:
            exec(f"from {module} import {item}")
            print(f"[OK] Successfully imported {item} from {module}")
    except Exception as e:
        print(f"[ERROR] Failed to import {item} from {module}: {e}")
        all_ok = False

# Test 3: Check network interfaces
print("\n" + "=" * 60)
print("Testing Network Interface Detection")
print("=" * 60)

try:
    from scapy.all import get_if_list
    interfaces = get_if_list()
    if interfaces:
        print(f"[OK] Found {len(interfaces)} network interface(s):")
        for i, iface in enumerate(interfaces[:5], 1):  # Show first 5
            print(f"   {i}. {iface}")
        if len(interfaces) > 5:
            print(f"   ... and {len(interfaces) - 5} more")
    else:
        print("[WARNING] No network interfaces found")
except Exception as e:
    print(f"[ERROR] Error getting network interfaces: {e}")

# Test 4: Check permissions (packet capture requires admin)
print("\n" + "=" * 60)
print("Testing Permissions")
print("=" * 60)

import os
import platform

if platform.system() == 'Windows':
    try:
        import ctypes
        is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
        if is_admin:
            print("[OK] Running with administrator privileges")
        else:
            print("[WARNING] NOT running with administrator privileges")
            print("   Packet capture requires admin rights on Windows")
    except:
        print("[WARNING] Could not check admin status")
else:
    # Linux/Mac
    if os.geteuid() == 0:
        print("[OK] Running as root")
    else:
        print("[WARNING] NOT running as root")
        print("   Packet capture may require sudo/root privileges")

print("\n" + "=" * 60)
if all_ok:
    print("[OK] All tests passed! Scapy is ready to use.")
else:
    print("[ERROR] Some tests failed. Please check the errors above.")
print("=" * 60)

