import numpy as np
import pandas as pd
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PortScanDetector:
    """
    Advanced port scan detection with pattern recognition
    Detects: TCP SYN, TCP Connect, UDP, XMAS, FIN, NULL scans
    """
    
    def __init__(self, window_size: int = 60, threshold_ports: int = 10, 
                 threshold_connections: int = 20):
        """
        Args:
            window_size: Time window in seconds to track scanning activity
            threshold_ports: Number of unique ports accessed to trigger alert
            threshold_connections: Number of connections to trigger alert
        """
        self.window_size = window_size
        self.threshold_ports = threshold_ports
        self.threshold_connections = threshold_connections
        
        # Track connection attempts per source IP
        self.ip_tracking = defaultdict(lambda: {
            'ports': set(),
            'timestamps': deque(),
            'connection_attempts': deque(),
            'flags': deque(),
            'protocols': deque()
        })
        
        # Port scan signatures
        self.scan_signatures = {
            'SYN_SCAN': {
                'description': 'TCP SYN Stealth Scan',
                'flags': ['S', 'SYN'],
                'severity': 'HIGH'
            },
            'CONNECT_SCAN': {
                'description': 'TCP Connect Scan',
                'flags': ['SA', 'SYN-ACK'],
                'severity': 'MEDIUM'
            },
            'XMAS_SCAN': {
                'description': 'XMAS Tree Scan',
                'flags': ['FPU', 'FIN-PSH-URG'],
                'severity': 'HIGH'
            },
            'FIN_SCAN': {
                'description': 'FIN Stealth Scan',
                'flags': ['F', 'FIN'],
                'severity': 'HIGH'
            },
            'NULL_SCAN': {
                'description': 'NULL Scan',
                'flags': ['NULL', '0'],
                'severity': 'HIGH'
            },
            'UDP_SCAN': {
                'description': 'UDP Port Scan',
                'protocol': 'UDP',
                'severity': 'MEDIUM'
            },
            'VERTICAL_SCAN': {
                'description': 'Vertical Port Scan (many ports, one target)',
                'pattern': 'sequential_ports',
                'severity': 'HIGH'
            },
            'HORIZONTAL_SCAN': {
                'description': 'Horizontal Scan (one port, many targets)',
                'pattern': 'multiple_hosts',
                'severity': 'CRITICAL'
            }
        }
        
        logger.info("🔍 Port Scan Detector initialized")
    
    def extract_port_scan_features(self, packet: Dict) -> Dict:
        """
        Extract features specific to port scanning detection
        
        Args:
            packet: Dictionary containing packet information
                - srcip: Source IP address
                - dstip: Destination IP address
                - src_port: Source port
                - dst_port: Destination port
                - protocol: Protocol (tcp/udp/icmp)
                - flags: TCP flags
                - timestamp: Packet timestamp
                - packet_size: Size of packet
                - duration: Connection duration
        
        Returns:
            Dictionary of extracted features
        """
        features = {
            # Basic packet info
            'srcip': packet.get('srcip', '0.0.0.0'),
            'dstip': packet.get('dstip', '0.0.0.0'),
            'src_port': packet.get('src_port', 0),
            'dst_port': packet.get('dst_port', 0),
            'protocol': packet.get('protocol', 'tcp').lower(),
            'flags': self._parse_tcp_flags(packet.get('flags', 0)),
            'timestamp': packet.get('timestamp', datetime.now()),
            'packet_size': packet.get('packet_size', 0),
            'duration': packet.get('duration', 0),
            
            # Port scan specific features
            'is_syn_only': False,
            'is_stealth_scan': False,
            'is_sequential_port': False,
            'connection_rate': 0.0,
            'unique_ports_accessed': 0,
            'port_range_span': 0,
            'is_well_known_port': False,
            'response_size': packet.get('packet_size', 0),
            'has_payload': packet.get('packet_size', 0) > 64,
            'is_fragmented': packet.get('is_fragmented', False)
        }
        
        # Ensure timestamp is datetime object
        if isinstance(features['timestamp'], str):
            try:
                # Handle ISO format timestamps
                ts_str = features['timestamp'].replace('Z', '+00:00')
                if hasattr(datetime, 'fromisoformat'):
                    features['timestamp'] = datetime.fromisoformat(ts_str)
                else:
                    # Fallback for Python < 3.7
                    from dateutil import parser
                    features['timestamp'] = parser.parse(ts_str)
            except Exception:
                try:
                    # Try parsing with strptime
                    features['timestamp'] = datetime.strptime(features['timestamp'], '%Y-%m-%dT%H:%M:%S')
                except Exception:
                    features['timestamp'] = datetime.now()
        
        # Check if accessing well-known ports (0-1023)
        features['is_well_known_port'] = features['dst_port'] <= 1023
        
        # Check for SYN-only packets (stealth scan indicator)
        if features['protocol'] == 'tcp':
            flags = features['flags']
            features['is_syn_only'] = flags == 'S' or flags == 'SYN'
            features['is_stealth_scan'] = flags in ['F', 'FIN', 'NULL', 'FPU', 'XMAS']
        
        return features
    
    def detect_port_scan(self, packet: Dict) -> Dict:
        """
        Analyze packet and detect if it's part of a port scanning attack
        
        Returns:
            Detection result with threat level and details
        """
        features = self.extract_port_scan_features(packet)
        srcip = features['srcip']
        dst_port = features['dst_port']
        timestamp = features['timestamp']
        
        # Update tracking for this IP
        ip_data = self.ip_tracking[srcip]
        ip_data['ports'].add(dst_port)
        ip_data['timestamps'].append(timestamp)
        ip_data['flags'].append(features['flags'])
        ip_data['protocols'].append(features['protocol'])
        
        # Clean old entries outside time window
        self._clean_old_entries(srcip, timestamp)
        
        # Calculate behavioral metrics
        time_window_seconds = (ip_data['timestamps'][-1] - ip_data['timestamps'][0]).total_seconds() if len(ip_data['timestamps']) > 1 else 1
        unique_ports = len(ip_data['ports'])
        connection_rate = len(ip_data['timestamps']) / max(time_window_seconds, 1)
        
        # Detect port scan patterns
        scan_detected = False
        scan_type = None
        confidence = 0.0
        severity = 'LOW'
        details = []
        
        # Pattern 1: High number of unique ports accessed
        if unique_ports >= self.threshold_ports:
            scan_detected = True
            scan_type = 'VERTICAL_SCAN'
            confidence = min(0.95, 0.5 + (unique_ports / self.threshold_ports) * 0.45)
            severity = 'HIGH'
            details.append(f"Accessed {unique_ports} unique ports in {time_window_seconds:.1f}s")
        
        # Pattern 2: High connection rate
        if connection_rate > 5.0:  # More than 5 connections per second
            scan_detected = True
            if not scan_type:
                scan_type = 'RAPID_SCAN'
            confidence = max(confidence, min(0.98, 0.6 + (connection_rate / 10) * 0.38))
            severity = 'HIGH'
            details.append(f"High connection rate: {connection_rate:.2f} conn/s")
        
        # Pattern 3: Sequential port scanning
        if self._detect_sequential_ports(list(ip_data['ports'])):
            scan_detected = True
            scan_type = 'SEQUENTIAL_SCAN'
            confidence = max(confidence, 0.92)
            severity = 'HIGH'
            details.append("Sequential port scanning pattern detected")
        
        # Pattern 4: SYN scan (stealth scan)
        syn_only_count = sum(1 for f in ip_data['flags'] if f in ['S', 'SYN'])
        if syn_only_count > 5 and len(ip_data['flags']) > 0 and syn_only_count / len(ip_data['flags']) > 0.7:
            scan_detected = True
            scan_type = 'SYN_SCAN'
            confidence = max(confidence, 0.96)
            severity = 'HIGH'
            details.append(f"SYN stealth scan: {syn_only_count} SYN-only packets")
        
        # Pattern 5: Stealth scan techniques (FIN, NULL, XMAS)
        stealth_flags = ['F', 'FIN', 'NULL', 'FPU', 'XMAS']
        stealth_count = sum(1 for f in ip_data['flags'] if f in stealth_flags)
        if stealth_count > 3:
            scan_detected = True
            scan_type = self._identify_stealth_scan_type(list(ip_data['flags']))
            confidence = max(confidence, 0.98)
            severity = 'CRITICAL'
            details.append(f"Advanced stealth scan detected: {scan_type}")
        
        # Pattern 6: UDP scan
        udp_count = sum(1 for p in ip_data['protocols'] if p == 'udp')
        if udp_count > 10 and unique_ports > 8:
            scan_detected = True
            scan_type = 'UDP_SCAN'
            confidence = max(confidence, 0.89)
            severity = 'MEDIUM'
            details.append(f"UDP port scan: {udp_count} UDP probes")
        
        # Pattern 7: Well-known port scanning
        well_known_scans = sum(1 for p in ip_data['ports'] if p <= 1023)
        if well_known_scans > 15:
            severity = 'CRITICAL'  # Upgrade severity
            details.append(f"Targeting {well_known_scans} well-known service ports")
        
        # Build detection result - ensure all values are JSON serializable
        result = {
            'threat_detected': bool(scan_detected),
            'attack_type': scan_type if scan_detected else 'Normal',
            'confidence': float(confidence),
            'severity': severity if scan_detected else 'NONE',
            'source_ip': str(srcip),
            'destination_ip': str(features['dstip']),
            'unique_ports_accessed': int(unique_ports),
            'connection_rate': float(connection_rate),
            'time_window': float(time_window_seconds),
            'scan_signature': self.scan_signatures.get(scan_type, {}).get('description', 'Unknown'),
            'details': [str(d) for d in details],
            'recommended_action': str(self._get_mitigation_action(scan_type, severity)) if scan_detected else None,
            'timestamp': timestamp.isoformat() if hasattr(timestamp, 'isoformat') else str(timestamp),
            'behavioral_metrics': {
                'total_connections': int(len(ip_data['timestamps'])),
                'unique_ports': int(unique_ports),
                'connection_rate': float(round(connection_rate, 2)),
                'dominant_protocol': str(max(set(ip_data['protocols']), key=list(ip_data['protocols']).count)) if ip_data['protocols'] else 'unknown',
                'flag_distribution': {str(k): int(v) for k, v in dict(pd.Series(list(ip_data['flags'])).value_counts()).items()} if ip_data['flags'] else {}
            }
        }
        
        if scan_detected:
            logger.warning(f"🚨 PORT SCAN DETECTED: {scan_type} from {srcip} | Confidence: {confidence:.2%} | Severity: {severity}")
        
        return result
    
    def _parse_tcp_flags(self, flags) -> str:
        """Parse TCP flags from integer to string representation"""
        if isinstance(flags, str):
            return flags
        
        flag_map = {
            1: 'FIN',
            2: 'SYN',
            4: 'RST',
            8: 'PSH',
            16: 'ACK',
            32: 'URG'
        }
        
        if flags == 0:
            return 'NULL'
        
        flag_str = []
        for bit, name in flag_map.items():
            if flags & bit:
                flag_str.append(name)
        
        result = '-'.join(flag_str) if flag_str else 'NULL'
        
        # Special patterns
        if 'FIN' in result and 'PSH' in result and 'URG' in result:
            return 'XMAS'
        if result == 'SYN':
            return 'S'
        if result == 'FIN':
            return 'F'
        
        return result
    
    def _detect_sequential_ports(self, ports: List[int]) -> bool:
        """Detect if ports are being scanned sequentially"""
        if len(ports) < 5:
            return False
        
        sorted_ports = sorted(ports)
        sequential_count = 0
        
        for i in range(len(sorted_ports) - 1):
            if sorted_ports[i+1] - sorted_ports[i] <= 2:  # Allow small gaps
                sequential_count += 1
        
        return sequential_count / len(sorted_ports) > 0.6
    
    def _identify_stealth_scan_type(self, flags: List[str]) -> str:
        """Identify specific type of stealth scan"""
        flag_counts = pd.Series(flags).value_counts()
        
        if 'F' in flag_counts or 'FIN' in flag_counts:
            return 'FIN_SCAN'
        if 'NULL' in flag_counts:
            return 'NULL_SCAN'
        if any('XMAS' in f or 'FPU' in f for f in flags):
            return 'XMAS_SCAN'
        
        return 'STEALTH_SCAN'
    
    def _clean_old_entries(self, srcip: str, current_time: datetime):
        """Remove tracking entries outside the time window"""
        ip_data = self.ip_tracking[srcip]
        cutoff_time = current_time - timedelta(seconds=self.window_size)
        
        # Remove old timestamps and associated data
        while ip_data['timestamps'] and ip_data['timestamps'][0] < cutoff_time:
            ip_data['timestamps'].popleft()
            if ip_data['flags']:
                ip_data['flags'].popleft()
            if ip_data['protocols']:
                ip_data['protocols'].popleft()
    
    def _get_mitigation_action(self, scan_type: str, severity: str) -> str:
        """Get recommended mitigation action based on scan type"""
        actions = {
            'SYN_SCAN': 'Block source IP immediately. Enable SYN cookies. Review firewall rules.',
            'VERTICAL_SCAN': 'Block source IP. Enable port knocking. Implement rate limiting.',
            'HORIZONTAL_SCAN': 'CRITICAL: Network-wide attack. Block source network. Alert SOC team.',
            'STEALTH_SCAN': 'Advanced attacker detected. Block IP. Enable IPS. Forensic analysis required.',
            'UDP_SCAN': 'Block UDP traffic from source. Enable stateful firewall inspection.',
            'FIN_SCAN': 'Stealth attack detected. Block source IP. Review all recent connections.',
            'NULL_SCAN': 'Advanced reconnaissance. Block IP. Enable deep packet inspection.',
            'XMAS_SCAN': 'Sophisticated attack. Immediate IP block. Increase monitoring.',
            'SEQUENTIAL_SCAN': 'Systematic reconnaissance. Block IP. Review access logs.',
            'RAPID_SCAN': 'Automated scanning tool detected. Block IP range. Implement CAPTCHA.'
        }
        
        return actions.get(scan_type, 'Block source IP and investigate further.')
    
    def get_statistics(self, srcip: Optional[str] = None) -> Dict:
        """Get scanning statistics for an IP or all IPs"""
        if srcip:
            if srcip not in self.ip_tracking:
                return {'error': 'IP not found in tracking'}
            
            ip_data = self.ip_tracking[srcip]
            return {
                'ip': str(srcip),
                'unique_ports': int(len(ip_data['ports'])),
                'total_connections': int(len(ip_data['timestamps'])),
                'active_window': float((ip_data['timestamps'][-1] - ip_data['timestamps'][0]).total_seconds()) if len(ip_data['timestamps']) > 1 else 0.0,
                'ports_accessed': [int(p) for p in sorted(list(ip_data['ports']))[:20]]  # First 20 ports
            }
        
        # Return global statistics
        return {
            'total_tracked_ips': int(len(self.ip_tracking)),
            'active_scanners': int(sum(1 for ip_data in self.ip_tracking.values() if len(ip_data['ports']) >= self.threshold_ports)),
            'total_unique_ports_scanned': int(sum(len(ip_data['ports']) for ip_data in self.ip_tracking.values()))
        }


if __name__ == "__main__":
    # Quick test
    detector = PortScanDetector()
    print("✅ Port Scan Detector module loaded successfully!")
    print("🔍 Ready to detect: SYN, FIN, NULL, XMAS, UDP scans and more")