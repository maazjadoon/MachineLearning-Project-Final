"""
packet_capture.py - Real-time network packet capture and analysis using Scapy

This module captures live network packets and forwards them to the detection system
for real-time threat analysis.
"""

import socket
import json
import threading
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from collections import defaultdict, deque
from datetime import timedelta

logger = logging.getLogger(__name__)

# Try to import Scapy
try:
    from scapy.all import sniff, IP, TCP, UDP, ICMP, ARP, Raw, get_if_list
    # IPPROTO constants are not needed for basic packet capture
    # They're only used for protocol matching which we do via string comparison
    SCAPY_AVAILABLE = True
except ImportError as e:
    SCAPY_AVAILABLE = False
    logger.warning(f"Scapy not available: {e}")
    logger.warning("Install with: pip install scapy")
    # Create dummy classes for type hints
    IP = TCP = UDP = ICMP = None

class PacketCapture:
    """Capture network packets and forward to detection system"""
    
    def __init__(self, model_server_host='localhost', model_server_port=9999, 
                 interface=None, filter_str=None, max_packets_per_second=100,
                 socketio=None, threat_callback=None):
        """
        Args:
            model_server_host: Host where model server is running
            model_server_port: Port where model server is listening
            interface: Network interface to capture from (None = all interfaces)
            filter_str: BPF filter string (e.g., "tcp port 80")
            max_packets_per_second: Rate limit to prevent overload
            socketio: Flask-SocketIO instance for real-time updates (optional)
            threat_callback: Callback function to call when threat is detected (optional)
        """
        self.model_server_host = model_server_host
        self.model_server_port = model_server_port
        self.interface = interface
        self.filter_str = filter_str
        self.max_packets_per_second = max_packets_per_second
        self.socketio = socketio  # Flask-SocketIO instance for WebSocket updates
        self.threat_callback = threat_callback  # Callback for threat detections
        self.running = False
        self.capture_thread = None
        self._interface_map = {}  # Will store mapping of readable names to actual interface names
        
        # Flow tracking for connection duration and statistics
        self.flow_tracking = defaultdict(lambda: {
            'start_time': None,
            'packet_count': 0,
            'bytes': 0,
            'flags': []
        })
        
        # Rate limiting
        self.packet_timestamps = deque(maxlen=max_packets_per_second)
        
        # Statistics
        self.stats = {
            'total_packets': 0,
            'packets_analyzed': 0,
            'threats_detected': 0,
            'start_time': None
        }
    
    def _get_windows_interface_friendly_names(self):
        """Get Windows interface friendly names mapped to GUIDs"""
        friendly_names = {}
        try:
            import platform
            if platform.system() != 'Windows':
                return friendly_names
            
            try:
                # Try using netifaces if available
                import netifaces
                for iface in netifaces.interfaces():
                    try:
                        addrs = netifaces.ifaddresses(iface)
                        if netifaces.AF_LINK in addrs:
                            # Get friendly name from registry or use GUID
                            friendly_name = iface
                            # Try to get actual friendly name
                            try:
                                import winreg
                                key_path = r"SYSTEM\CurrentControlSet\Control\Network\{4d36e972-e325-11ce-bfc1-08002be10318}"
                                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
                                    for i in range(winreg.QueryInfoKey(key)[0]):
                                        try:
                                            subkey_name = winreg.EnumKey(key, i)
                                            subkey_path = f"{key_path}\\{subkey_name}\\Connection"
                                            try:
                                                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, subkey_path) as conn_key:
                                                    guid = winreg.QueryValueEx(conn_key, "PnpInstanceID")[0]
                                                    if guid == iface or guid.replace('{', '').replace('}', '') == iface.replace('{', '').replace('}', ''):
                                                        friendly_name = winreg.QueryValueEx(conn_key, "Name")[0]
                                                        friendly_names[iface] = friendly_name
                                                        break
                                            except:
                                                continue
                                        except:
                                            continue
                            except Exception:
                                pass
                    except:
                        continue
            except ImportError:
                # netifaces not available, try alternative method
                try:
                    import subprocess
                    result = subprocess.run(['netsh', 'interface', 'show', 'interface'], 
                                          capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        lines = result.stdout.strip().split('\n')
                        for line in lines[2:]:  # Skip header lines
                            parts = line.split()
                            if len(parts) >= 4:
                                state = parts[0]
                                name = ' '.join(parts[3:])
                                # We'll need to match this to GUIDs later
                                friendly_names[name] = name
                except Exception:
                    pass
        except Exception as e:
            logger.debug(f"Could not get Windows friendly names: {e}")
        
        return friendly_names
    
    def _get_available_interfaces(self):
        """Get list of available network interfaces, prioritizing Wi-Fi"""
        if not SCAPY_AVAILABLE:
            return []
        try:
            from scapy.arch import get_if_list
            import platform
            raw_interfaces = get_if_list()
            
            # For Windows, try to get friendly names and prioritize Wi-Fi
            friendly_names = {}
            if platform.system() == 'Windows':
                friendly_names = self._get_windows_interface_friendly_names()
            
            # Filter and prioritize interfaces
            filtered_interfaces = []
            wifi_interface = None
            other_interfaces = []
            
            for iface in raw_interfaces:
                # Skip loopback for production monitoring
                if 'Loopback' in iface or 'loopback' in iface.lower():
                    continue
                # Skip empty or invalid interfaces
                if not iface or len(iface.strip()) < 3:
                    continue
                
                # Check if this is Wi-Fi
                is_wifi = False
                iface_lower = iface.lower()
                # Check friendly name if available
                if iface in friendly_names:
                    friendly_name = friendly_names[iface].lower()
                    if 'wi-fi' in friendly_name or 'wifi' in friendly_name or 'wireless' in friendly_name:
                        is_wifi = True
                # Also check GUID/name directly
                if 'wi-fi' in iface_lower or 'wifi' in iface_lower or 'wireless' in iface_lower:
                    is_wifi = True
                
                if is_wifi:
                    wifi_interface = iface
                else:
                    other_interfaces.append(iface)
            
            # Prioritize Wi-Fi, then add others
            if wifi_interface:
                filtered_interfaces.append(wifi_interface)
            filtered_interfaces.extend(other_interfaces)
            
            # If no interfaces found, return all (except loopback)
            if not filtered_interfaces:
                for iface in raw_interfaces:
                    if 'Loopback' not in iface and iface and len(iface.strip()) >= 3:
                        filtered_interfaces.append(iface)
            
            return filtered_interfaces
        except Exception as e:
            logger.error(f"Error getting interfaces: {e}")
            return []
    
    def _rate_limit(self) -> bool:
        """Check if we should process this packet (rate limiting)"""
        now = datetime.now()
        
        # Remove timestamps older than 1 second
        while self.packet_timestamps and (now - self.packet_timestamps[0]).total_seconds() > 1.0:
            self.packet_timestamps.popleft()
        
        # Check if we're at the rate limit
        if len(self.packet_timestamps) >= self.max_packets_per_second:
            return False
        
        self.packet_timestamps.append(now)
        return True
    
    def _packet_to_dict(self, packet) -> Optional[Dict[str, Any]]:
        """Convert Scapy packet to dictionary format expected by detection system"""
        try:
            packet_dict = {
                'timestamp': datetime.now().isoformat(),
                'packet_size': len(packet),
            }
            
            # Extract IP layer
            if IP in packet:
                ip_layer = packet[IP]
                packet_dict['srcip'] = ip_layer.src
                packet_dict['dstip'] = ip_layer.dst
                packet_dict['protocol'] = 'unknown'
                
                # Track flow for duration calculation
                flow_key = (ip_layer.src, ip_layer.dst, ip_layer.proto)
                
                # Extract TCP layer
                if TCP in packet:
                    tcp_layer = packet[TCP]
                    packet_dict['src_port'] = tcp_layer.sport
                    packet_dict['dst_port'] = tcp_layer.dport
                    packet_dict['flags'] = self._tcp_flags_to_int(tcp_layer.flags)
                    packet_dict['protocol'] = 'tcp'
                    
                    # Update flow tracking
                    flow_key = (ip_layer.src, ip_layer.dst, tcp_layer.sport, tcp_layer.dport, 'tcp')
                    if flow_key not in self.flow_tracking:
                        self.flow_tracking[flow_key]['start_time'] = datetime.now()
                    self.flow_tracking[flow_key]['packet_count'] += 1
                    self.flow_tracking[flow_key]['bytes'] += len(packet)
                    self.flow_tracking[flow_key]['flags'].append(tcp_layer.flags)
                    
                    # Calculate duration
                    flow_start = self.flow_tracking[flow_key]['start_time']
                    if flow_start:
                        duration = (datetime.now() - flow_start).total_seconds()
                        packet_dict['duration'] = duration
                    else:
                        packet_dict['duration'] = 0.0
                    
                # Extract UDP layer
                elif UDP in packet:
                    udp_layer = packet[UDP]
                    packet_dict['src_port'] = udp_layer.sport
                    packet_dict['dst_port'] = udp_layer.dport
                    packet_dict['protocol'] = 'udp'
                    packet_dict['flags'] = 0
                    
                    # Update flow tracking
                    flow_key = (ip_layer.src, ip_layer.dst, udp_layer.sport, udp_layer.dport, 'udp')
                    if flow_key not in self.flow_tracking:
                        self.flow_tracking[flow_key]['start_time'] = datetime.now()
                    self.flow_tracking[flow_key]['packet_count'] += 1
                    self.flow_tracking[flow_key]['bytes'] += len(packet)
                    
                    packet_dict['duration'] = 0.0  # UDP is connectionless
                    
                # Extract ICMP layer
                elif ICMP in packet:
                    icmp_layer = packet[ICMP]
                    packet_dict['protocol'] = 'icmp'
                    packet_dict['src_port'] = 0
                    packet_dict['dst_port'] = 0
                    packet_dict['flags'] = 0
                    packet_dict['duration'] = 0.0
                
                # Add flow-based features
                flow_key_base = (ip_layer.src, ip_layer.dst)
                packet_dict['spkts'] = self.flow_tracking.get(flow_key_base, {}).get('packet_count', 1)
                packet_dict['sbytes'] = self.flow_tracking.get(flow_key_base, {}).get('bytes', len(packet))
                packet_dict['dpkts'] = 1  # Simplified
                packet_dict['dbytes'] = len(packet)
                
                # Add rate (packets per second estimate)
                if flow_key_base in self.flow_tracking:
                    flow = self.flow_tracking[flow_key_base]
                    if flow['start_time']:
                        elapsed = (datetime.now() - flow['start_time']).total_seconds()
                        if elapsed > 0:
                            packet_dict['rate'] = flow['packet_count'] / elapsed
                        else:
                            packet_dict['rate'] = flow['packet_count']
                    else:
                        packet_dict['rate'] = 0.0
                else:
                    packet_dict['rate'] = 0.0
                
                # Clean old flows (older than 5 minutes)
                self._clean_old_flows()
                
                return packet_dict
                
        except Exception as e:
            logger.error(f"Error converting packet: {e}")
            return None
        
        return None
    
    def _tcp_flags_to_int(self, flags) -> int:
        """Convert Scapy TCP flags to integer representation"""
        flag_map = {
            'F': 1,   # FIN
            'S': 2,   # SYN
            'R': 4,   # RST
            'P': 8,   # PSH
            'A': 16,  # ACK
            'U': 32,  # URG
        }
        
        flags_str = str(flags)
        result = 0
        for flag_char, flag_value in flag_map.items():
            if flag_char in flags_str:
                result |= flag_value
        return result
    
    def _clean_old_flows(self):
        """Remove flow entries older than 5 minutes"""
        cutoff_time = datetime.now() - timedelta(minutes=5)
        keys_to_remove = []
        
        for key, flow_data in self.flow_tracking.items():
            if flow_data['start_time'] and flow_data['start_time'] < cutoff_time:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.flow_tracking[key]
    
    def _send_to_model_server(self, packet_dict: Dict[str, Any]) -> bool:
        """Send packet to model server for analysis"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            sock.connect((self.model_server_host, self.model_server_port))
            
            json_data = json.dumps(packet_dict, default=str)
            sock.send(json_data.encode('utf-8'))
            
            response = sock.recv(8192).decode('utf-8')
            result = json.loads(response)
            
            # Update statistics
            self.stats['packets_analyzed'] += 1
            if result.get('threat_detected'):
                self.stats['threats_detected'] += 1
                logger.warning(
                    f"🚨 THREAT DETECTED: {result.get('attack_type', 'Unknown')} "
                    f"from {packet_dict.get('srcip')} to {packet_dict.get('dstip')} "
                    f"| Confidence: {result.get('confidence', 0):.2%} | "
                    f"Severity: {result.get('severity', 'UNKNOWN')}"
                )
                
                # Call threat callback if provided (for adding to app.py's threat_detections list)
                if self.threat_callback:
                    try:
                        logger.info(f"🔔 Calling threat callback to store detection in Flask app")
                        detection = self.threat_callback(packet_dict, result)
                        if detection:
                            logger.info(f"✅ Threat detection stored successfully: {detection.get('attack_type')}")
                        else:
                            logger.debug("⚠️ Threat callback returned None (may be rate-limited)")
                    except Exception as e:
                        logger.error(f"❌ Error in threat callback: {e}")
                        import traceback
                        logger.error(traceback.format_exc())
                else:
                    logger.warning("⚠️ No threat_callback provided - detections will NOT be stored in Flask app!")
                
                # Emit threat update via WebSocket if available
                if self.socketio:
                    try:
                        self.socketio.emit('threat_update', {
                            'timestamp': packet_dict.get('timestamp', datetime.now().isoformat()),
                            'data': packet_dict,
                            'result': result
                        })
                        
                        # Also emit new_detection event for real-time dashboard updates
                        detection = {
                            'timestamp': packet_dict.get('timestamp', datetime.now().isoformat()),
                            'attack_type': result.get('attack_type', 'Unknown'),
                            'source_ip': packet_dict.get('srcip', 'unknown'),
                            'destination_ip': packet_dict.get('dstip', 'unknown'),
                            'confidence': result.get('confidence', 0.0),
                            'severity': result.get('severity', 'UNKNOWN'),
                            'protocol': packet_dict.get('protocol', 'unknown'),
                            'src_port': packet_dict.get('src_port', 0),
                            'dst_port': packet_dict.get('dst_port', 0),
                            'model_used': result.get('model_used', result.get('detection_method', 'Unknown')),
                            'recommended_action': result.get('recommended_action', 'Investigate further')
                        }
                        self.socketio.emit('new_detection', detection)
                    except Exception as e:
                        logger.debug(f"Error emitting threat update: {e}")
            
            # Emit regular traffic updates (throttled - every 10th packet or if threat detected)
            if self.socketio and (self.stats['packets_analyzed'] % 10 == 0 or result.get('threat_detected')):
                try:
                    self.socketio.emit('sample_traffic', packet_dict)
                except Exception as e:
                    logger.debug(f"Error emitting traffic update: {e}")
            
            sock.close()
            return True
        except socket.timeout:
            logger.debug("Model server timeout")
            return False
        except ConnectionRefusedError:
            logger.warning("Model server not available")
            return False
        except Exception as e:
            logger.error(f"Error sending to model server: {e}")
            return False
    
    def _process_packet(self, packet):
        """Process captured packet from real network traffic"""
        if not self.running:
            return
        
        self.stats['total_packets'] += 1
        
        # Rate limiting
        if not self._rate_limit():
            return  # Skip this packet if rate limit exceeded
        
        # Convert real Scapy packet to dictionary
        packet_dict = self._packet_to_dict(packet)
        if packet_dict:
            # Verify we have real packet data (not dummy)
            if not packet_dict.get('srcip') or packet_dict.get('srcip') == 'unknown':
                logger.debug("Skipping packet with invalid source IP")
                return
            
            # Log that we're processing real packet data
            logger.debug(f"📦 Processing real packet: {packet_dict.get('srcip')} -> {packet_dict.get('dstip')} ({packet_dict.get('protocol')})")
            
            # Send REAL packet data to model server for analysis
            self._send_to_model_server(packet_dict)
    
    def _test_interface(self):
        """Test if an interface is accessible for packet capture
        
        Returns:
            tuple: (success: bool, use_fallback: bool)
            - If success is True and use_fallback is False: interface works directly
            - If success is True and use_fallback is True: interface doesn't work, but fallback (iface=None) works
            - If success is False: interface doesn't work and fallback also doesn't work
        """
        try:
            from scapy.all import sniff
            import platform
            
            logger.info(f"🧪 Testing interface {self.interface}...")
            
            # On Windows, try friendly name first if it's a GUID
            iface_to_use = self.interface
            if platform.system() == 'Windows' and self.interface and self.interface.startswith('{'):
                # Try using "Wi-Fi" directly first (Scapy might accept it)
                try:
                    test_result = sniff(
                        iface="Wi-Fi",
                        timeout=1,
                        count=0,
                        store=False
                    )
                    logger.info(f"✅ Can use 'Wi-Fi' directly as interface name")
                    # Store the friendly name for later use
                    self._wifi_name = "Wi-Fi"
                    return (True, False)
                except Exception:
                    pass  # Continue with GUID
            
            # Try the interface as-is (GUID or name)
            test_result = sniff(
                iface=iface_to_use,
                timeout=2,
                count=1,
                store=False
            )
            
            logger.info(f"✅ Interface {self.interface} is accessible")
            return (True, False)  # Success, no fallback needed
            
        except PermissionError:
            logger.error(f"❌ Permission denied on interface {self.interface}")
            logger.error("💡 Run as Administrator to capture packets")
            return (False, False)
        except (OSError, ValueError) as e:
            # On Windows, error 123 means "The filename, directory name, or volume label syntax is incorrect"
            # This often happens with GUID-based interface names
            error_str = str(e)
            if platform.system() == 'Windows' and ('123' in error_str or 'syntax is incorrect' in error_str.lower()):
                logger.debug(f"⚠️ Interface {self.interface} may need different format (Windows GUID issue)")
                # Try using None to capture on all interfaces as fallback
                try:
                    test_result = sniff(
                        iface=None,
                        timeout=1,
                        count=0,
                        store=False
                    )
                    logger.info(f"✅ Can capture on all interfaces (fallback mode)")
                    return (True, True)  # Success, but need fallback
                except Exception as fallback_error:
                    logger.debug(f"Fallback test also failed: {fallback_error}")
                    return (False, False)
            logger.error(f"❌ Interface {self.interface} not accessible: {e}")
            return (False, False)
        except Exception as e:
            logger.error(f"❌ Interface {self.interface} test failed: {e}")
            return (False, False)
    
    def start_capture(self) -> bool:
        """Start capturing packets"""
        if not SCAPY_AVAILABLE:
            logger.error("Scapy not available. Cannot capture packets.")
            logger.error("Install with: pip install scapy")
            logger.error("On Windows, also install Npcap: https://npcap.com/")
            return False
        
        if self.running:
            logger.warning("Capture already running")
            return False
        
        self.running = True
        self.stats['start_time'] = datetime.now()
        
        def capture_loop():
            try:
                interface_info = self.interface if self.interface else "ALL interfaces"
                filter_info = f" (filter: {self.filter_str})" if self.filter_str else ""
                logger.info(f"🔍 Starting packet capture on {interface_info}{filter_info}")
                logger.info(f"📊 Max packets/second: {self.max_packets_per_second}")
                logger.info(f"🔗 Model server: {self.model_server_host}:{self.model_server_port}")
                
                # Use the interface as-is. On Windows, if GUID doesn't work,
                # the caller should have already tested and fallen back to None
                # Also try "Wi-Fi" if interface is a GUID
                iface_to_use = self.interface
                import platform
                if platform.system() == 'Windows' and self.interface and self.interface.startswith('{'):
                    # If we have a GUID but "Wi-Fi" was set during testing, use it
                    if hasattr(self, '_wifi_name') and self._wifi_name:
                        iface_to_use = self._wifi_name
                        logger.info(f"Using friendly name '{iface_to_use}' instead of GUID")
                
                sniff(
                    iface=iface_to_use,
                    filter=self.filter_str,
                    prn=self._process_packet,
                    stop_filter=lambda x: not self.running,
                    store=False  # Don't store packets in memory (important for performance)
                )
            except PermissionError:
                logger.error("❌ Permission denied. Packet capture requires administrator/root privileges.")
                logger.error("Please run with administrator/root access.")
                self.running = False
            except Exception as e:
                logger.error(f"Packet capture error: {e}")
                logger.exception("Capture error traceback:")
                self.running = False
        
        self.capture_thread = threading.Thread(target=capture_loop, daemon=True)
        self.capture_thread.start()
        return True
    
    def stop_capture(self):
        """Stop capturing packets"""
        if self.running:
            self.running = False
            logger.info("🛑 Stopping packet capture...")
            # Wait a bit for the thread to finish
            if self.capture_thread:
                self.capture_thread.join(timeout=2)
            logger.info("✅ Packet capture stopped")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get capture statistics"""
        uptime = None
        if self.stats['start_time']:
            uptime = (datetime.now() - self.stats['start_time']).total_seconds()
        
        return {
            'running': self.running,
            'total_packets': self.stats['total_packets'],
            'packets_analyzed': self.stats['packets_analyzed'],
            'threats_detected': self.stats['threats_detected'],
            'uptime_seconds': uptime,
            'active_flows': len(self.flow_tracking),
            'packets_per_second': (
                self.stats['total_packets'] / uptime if uptime and uptime > 0 else 0
            )
        }


if __name__ == '__main__':
    import time
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Example usage
    print("Available interfaces:", PacketCapture()._get_available_interfaces())
    
    capture = PacketCapture(
        model_server_host='localhost',
        model_server_port=9999,
        interface=None,  # All interfaces
        filter_str="tcp or udp",  # Only TCP/UDP packets (exclude ICMP for less noise)
        max_packets_per_second=100
    )
    
    if capture.start_capture():
        try:
            print("Packet capture started. Press Ctrl+C to stop...")
            while True:
                time.sleep(5)
                stats = capture.get_statistics()
                print(f"Stats: {stats}")
        except KeyboardInterrupt:
            print("\nStopping capture...")
            capture.stop_capture()
    else:
        print("Failed to start packet capture")

