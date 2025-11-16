#!/usr/bin/env python3
"""
Attack Categories and Automatic Detection System
Defines attack types, their signatures, and automatic detection rules
"""

from enum import Enum
from typing import Dict, List, Any, Optional
import re
import ipaddress

class AttackCategory(Enum):
    """Enumeration of attack categories"""
    PORT_SCAN = "Port Scan"
    DOS_ATTACK = "Denial of Service"
    BRUTE_FORCE = "Brute Force"
    MALWARE = "Malware Communication"
    DATA_EXFILTRATION = "Data Exfiltration"
    COMMAND_INJECTION = "Command Injection"
    SQL_INJECTION = "SQL Injection"
    CROSS_SITE_SCRIPTING = "Cross-Site Scripting"
    MAN_IN_MIDDLE = "Man-in-the-Middle"
    RECONNAISSANCE = "Reconnaissance"
    UNKNOWN = "Unknown Attack"

class AttackSubcategory:
    """Detailed attack subcategories with detection rules"""
    
    CATEGORIES = {
        AttackCategory.PORT_SCAN: {
            "SYN_SCAN": {
                "name": "TCP SYN Scan",
                "description": "Stealth port scan using SYN packets",
                "detection_rules": {
                    "tcp_flags": ["SYN"],
                    "connection_rate": "> 10/second",
                    "unique_ports": "> 5",
                    "confidence_threshold": 0.8
                },
                "severity": "HIGH",
                "auto_response": "block_ip_temporarily"
            },
            "NULL_SCAN": {
                "name": "TCP NULL Scan",
                "description": "Port scan with no TCP flags set",
                "detection_rules": {
                    "tcp_flags": ["NULL"],
                    "connection_rate": "> 5/second",
                    "confidence_threshold": 0.9
                },
                "severity": "HIGH",
                "auto_response": "block_ip_immediately"
            },
            "XMAS_SCAN": {
                "name": "TCP XMAS Scan",
                "description": "Port scan with FIN, PSH, URG flags",
                "detection_rules": {
                    "tcp_flags": ["FIN", "PSH", "URG"],
                    "connection_rate": "> 5/second",
                    "confidence_threshold": 0.85
                },
                "severity": "HIGH",
                "auto_response": "block_ip_temporarily"
            },
            "FIN_SCAN": {
                "name": "TCP FIN Scan",
                "description": "Stealth port scan using FIN packets",
                "detection_rules": {
                    "tcp_flags": ["FIN"],
                    "connection_rate": "> 5/second",
                    "confidence_threshold": 0.8
                },
                "severity": "HIGH",
                "auto_response": "block_ip_temporarily"
            },
            "UDP_SCAN": {
                "name": "UDP Port Scan",
                "description": "Scanning UDP ports for open services",
                "detection_rules": {
                    "protocol": "UDP",
                    "connection_rate": "> 10/second",
                    "unique_ports": "> 10",
                    "confidence_threshold": 0.7
                },
                "severity": "MEDIUM",
                "auto_response": "monitor_and_alert"
            },
            "VERTICAL_SCAN": {
                "name": "Vertical Port Scan",
                "description": "Scanning multiple ports on single target",
                "detection_rules": {
                    "unique_ports": "> 20",
                    "single_target": True,
                    "time_window": "< 60 seconds",
                    "confidence_threshold": 0.75
                },
                "severity": "HIGH",
                "auto_response": "block_ip_temporarily"
            },
            "HORIZONTAL_SCAN": {
                "name": "Horizontal Port Scan",
                "description": "Scanning single port across multiple targets",
                "detection_rules": {
                    "single_port": True,
                    "unique_targets": "> 10",
                    "time_window": "< 60 seconds",
                    "confidence_threshold": 0.8
                },
                "severity": "CRITICAL",
                "auto_response": "block_ip_immediately"
            }
        },
        
        AttackCategory.DOS_ATTACK: {
            "SYN_FLOOD": {
                "name": "SYN Flood Attack",
                "description": "Overwhelming target with SYN packets",
                "detection_rules": {
                    "tcp_flags": ["SYN"],
                    "connection_rate": "> 100/second",
                    "no_ack_response": True,
                    "confidence_threshold": 0.9
                },
                "severity": "CRITICAL",
                "auto_response": "block_ip_immediately"
            },
            "UDP_FLOOD": {
                "name": "UDP Flood Attack",
                "description": "Overwhelming target with UDP packets",
                "detection_rules": {
                    "protocol": "UDP",
                    "packet_rate": "> 1000/second",
                    "confidence_threshold": 0.85
                },
                "severity": "CRITICAL",
                "auto_response": "block_ip_immediately"
            },
            "ICMP_FLOOD": {
                "name": "ICMP Flood Attack",
                "description": "Ping flood or ICMP packet storm",
                "detection_rules": {
                    "protocol": "ICMP",
                    "packet_rate": "> 100/second",
                    "confidence_threshold": 0.8
                },
                "severity": "HIGH",
                "auto_response": "block_ip_temporarily"
            },
            "HTTP_FLOOD": {
                "name": "HTTP Flood Attack",
                "description": "Overwhelming web server with HTTP requests",
                "detection_rules": {
                    "protocol": "TCP",
                    "dst_port": [80, 443, 8080],
                    "request_rate": "> 50/second",
                    "confidence_threshold": 0.8
                },
                "severity": "HIGH",
                "auto_response": "rate_limit_requests"
            }
        },
        
        AttackCategory.BRUTE_FORCE: {
            "SSH_BRUTE_FORCE": {
                "name": "SSH Brute Force",
                "description": "Attempting to guess SSH credentials",
                "detection_rules": {
                    "dst_port": 22,
                    "protocol": "TCP",
                    "connection_rate": "> 5/second",
                    "failed_attempts": "> 10",
                    "confidence_threshold": 0.85
                },
                "severity": "HIGH",
                "auto_response": "block_ip_after_threshold"
            },
            "FTP_BRUTE_FORCE": {
                "name": "FTP Brute Force",
                "description": "Attempting to guess FTP credentials",
                "detection_rules": {
                    "dst_port": 21,
                    "protocol": "TCP",
                    "connection_rate": "> 10/second",
                    "failed_attempts": "> 15",
                    "confidence_threshold": 0.8
                },
                "severity": "HIGH",
                "auto_response": "block_ip_after_threshold"
            },
            "RDP_BRUTE_FORCE": {
                "name": "RDP Brute Force",
                "description": "Attempting to guess RDP credentials",
                "detection_rules": {
                    "dst_port": 3389,
                    "protocol": "TCP",
                    "connection_rate": "> 3/second",
                    "failed_attempts": "> 5",
                    "confidence_threshold": 0.9
                },
                "severity": "CRITICAL",
                "auto_response": "block_ip_immediately"
            },
            "WEB_BRUTE_FORCE": {
                "name": "Web Application Brute Force",
                "description": "Attempting to guess web credentials",
                "detection_rules": {
                    "dst_port": [80, 443, 8080],
                    "protocol": "TCP",
                    "http_methods": ["POST"],
                    "login_attempts": "> 20",
                    "confidence_threshold": 0.75
                },
                "severity": "MEDIUM",
                "auto_response": "rate_limit_and_alert"
            }
        },
        
        AttackCategory.MALWARE: {
            "C2_COMMUNICATION": {
                "name": "Command & Control Communication",
                "description": "Malware communicating with C2 server",
                "detection_rules": {
                    "suspicious_domains": True,
                    "periodic_connections": True,
                    "encrypted_traffic": True,
                    "confidence_threshold": 0.8
                },
                "severity": "CRITICAL",
                "auto_response": "block_domain_and_ip"
            },
            "BOTNET_ACTIVITY": {
                "name": "Botnet Activity",
                "description": "Infected system participating in botnet",
                "detection_rules": {
                    "multiple_outbound_connections": True,
                    "similar_patterns": True,
                    "high_connection_rate": True,
                    "confidence_threshold": 0.85
                },
                "severity": "CRITICAL",
                "auto_response": "quarantine_system"
            },
            "RANSOMWARE": {
                "name": "Ransomware Activity",
                "description": "Ransomware encrypting files and communicating",
                "detection_rules": {
                    "file_encryption_patterns": True,
                    "ransom_notes": True,
                    "payment_requests": True,
                    "confidence_threshold": 0.95
                },
                "severity": "CRITICAL",
                "auto_response": "isolate_system_immediately"
            }
        },
        
        AttackCategory.RECONNAISSANCE: {
            "DNS_ENUMERATION": {
                "name": "DNS Enumeration",
                "description": "Gathering information through DNS queries",
                "detection_rules": {
                    "dns_queries": "> 100/second",
                    "subdomain_bruteforce": True,
                    "zone_transfers": True,
                    "confidence_threshold": 0.7
                },
                "severity": "MEDIUM",
                "auto_response": "monitor_and_log"
            },
            "NETWORK_DISCOVERY": {
                "name": "Network Discovery",
                "description": "Scanning network to discover hosts and services",
                "detection_rules": {
                    "arp_scanning": True,
                    "ping_sweeps": True,
                    "service_fingerprinting": True,
                    "confidence_threshold": 0.6
                },
                "severity": "LOW",
                "auto_response": "monitor_and_log"
            },
            "OS_FINGERPRINTING": {
                "name": "OS Fingerprinting",
                "description": "Attempting to identify operating systems",
                "detection_rules": {
                    "ttl_analysis": True,
                    "window_size_analysis": True,
                    "tcp_options_analysis": True,
                    "confidence_threshold": 0.65
                },
                "severity": "LOW",
                "auto_response": "monitor_and_log"
            }
        }
    }
    
    @classmethod
    def get_all_categories(cls) -> List[Dict[str, Any]]:
        """Get all attack categories with their subcategories"""
        categories = []
        for category, subcategories in cls.CATEGORIES.items():
            category_info = {
                "category": category.value,
                "subcategories": []
            }
            for subcat_key, subcat_info in subcategories.items():
                category_info["subcategories"].append({
                    "id": subcat_key,
                    "name": subcat_info["name"],
                    "description": subcat_info["description"],
                    "severity": subcat_info["severity"],
                    "auto_response": subcat_info["auto_response"]
                })
            categories.append(category_info)
        return categories
    
    @classmethod
    def get_subcategory_info(cls, subcategory_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific subcategory"""
        for category, subcategories in cls.CATEGORIES.items():
            if subcategory_id in subcategories:
                info = subcategories[subcategory_id].copy()
                info["category"] = category.value
                info["id"] = subcategory_id
                return info
        return None
    
    @classmethod
    def get_detection_rules(cls, subcategory_id: str) -> Optional[Dict[str, Any]]:
        """Get detection rules for a specific attack type"""
        for category, subcategories in cls.CATEGORIES.items():
            if subcategory_id in subcategories:
                return subcategories[subcategory_id]["detection_rules"]
        return None

class AutomaticDetector:
    """Automatic attack detection based on selected categories"""
    
    def __init__(self):
        self.enabled_attacks = set()
        self.detection_rules = {}
        self.response_actions = {}
    
    def enable_attack_detection(self, subcategory_ids: List[str]):
        """Enable automatic detection for specific attack types"""
        for subcat_id in subcategory_ids:
            rules = AttackSubcategory.get_detection_rules(subcat_id)
            info = AttackSubcategory.get_subcategory_info(subcat_id)
            
            if rules and info:
                self.enabled_attacks.add(subcat_id)
                self.detection_rules[subcat_id] = rules
                self.response_actions[subcat_id] = info["auto_response"]
    
    def disable_attack_detection(self, subcategory_ids: List[str]):
        """Disable detection for specific attack types"""
        for subcat_id in subcategory_ids:
            self.enabled_attacks.discard(subcat_id)
            self.detection_rules.pop(subcat_id, None)
            self.response_actions.pop(subcat_id, None)
    
    def analyze_packet(self, packet_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze packet for enabled attack types"""
        detections = []
        
        for attack_type in self.enabled_attacks:
            if attack_type in self.detection_rules:
                detection = self._check_attack_rules(packet_data, attack_type)
                if detection:
                    detections.append(detection)
        
        return detections
    
    def _check_attack_rules(self, packet_data: Dict[str, Any], attack_type: str) -> Optional[Dict[str, Any]]:
        """Check if packet matches attack detection rules"""
        rules = self.detection_rules[attack_type]
        info = AttackSubcategory.get_subcategory_info(attack_type)
        
        if not info:
            return None
        
        confidence = 0.0
        matched_rules = []
        
        # Check TCP flags
        if "tcp_flags" in rules:
            packet_flags = packet_data.get("flags", 0)
            required_flags = rules["tcp_flags"]
            
            if self._check_tcp_flags(packet_flags, required_flags):
                confidence += 0.3
                matched_rules.append("tcp_flags")
        
        # Check connection rate
        if "connection_rate" in rules:
            rate_rule = rules["connection_rate"]
            if self._check_connection_rate(packet_data, rate_rule):
                confidence += 0.25
                matched_rules.append("connection_rate")
        
        # Check protocol
        if "protocol" in rules:
            if packet_data.get("protocol", "").upper() == rules["protocol"].upper():
                confidence += 0.2
                matched_rules.append("protocol")
        
        # Check destination ports
        if "dst_port" in rules:
            dst_port = packet_data.get("dst_port", 0)
            allowed_ports = rules["dst_port"]
            if isinstance(allowed_ports, list):
                if dst_port in allowed_ports:
                    confidence += 0.15
                    matched_rules.append("dst_port")
            elif dst_port == allowed_ports:
                confidence += 0.15
                matched_rules.append("dst_port")
        
        # Check unique ports
        if "unique_ports" in rules:
            # This would need to be tracked over time
            # For now, we'll add a small confidence boost
            confidence += 0.1
            matched_rules.append("unique_ports_pattern")
        
        # Check confidence threshold
        threshold = rules.get("confidence_threshold", 0.7)
        
        if confidence >= threshold:
            return {
                "attack_type": attack_type,
                "attack_name": info["name"],
                "category": info["category"],
                "confidence": confidence,
                "severity": info["severity"],
                "matched_rules": matched_rules,
                "auto_response": self.response_actions.get(attack_type),
                "description": info["description"]
            }
        
        return None
    
    def _check_tcp_flags(self, packet_flags: int, required_flags: List[str]) -> bool:
        """Check if TCP flags match the required pattern"""
        flag_map = {
            "SYN": 0x02,
            "ACK": 0x10,
            "FIN": 0x01,
            "RST": 0x04,
            "PSH": 0x08,
            "URG": 0x20,
            "ECE": 0x40,
            "CWR": 0x80,
            "NULL": 0x00
        }
        
        if len(required_flags) == 1:
            required_flag = required_flags[0]
            if required_flag in flag_map:
                return packet_flags == flag_map[required_flag]
        
        # For multiple flags, check if all are present
        for flag in required_flags:
            if flag in flag_map:
                if not (packet_flags & flag_map[flag]):
                    return False
        
        return True
    
    def _check_connection_rate(self, packet_data: Dict[str, Any], rate_rule: str) -> bool:
        """Check connection rate - simplified version"""
        # This would need to be implemented with actual rate tracking
        # For now, return True if the rule suggests high rate
        return ">" in rate_rule or "high" in rate_rule.lower()
    
    def get_enabled_attacks(self) -> List[Dict[str, Any]]:
        """Get list of currently enabled attack detections"""
        enabled = []
        for attack_type in self.enabled_attacks:
            info = AttackSubcategory.get_subcategory_info(attack_type)
            if info:
                enabled.append({
                    "id": attack_type,
                    "name": info["name"],
                    "category": info["category"],
                    "severity": info["severity"],
                    "auto_response": info["auto_response"]
                })
        return enabled

# Global detector instance
auto_detector = AutomaticDetector()
