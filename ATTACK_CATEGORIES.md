# Attack Categories Management System

Cyber Sentinel ML provides a comprehensive attack categorization and automatic detection system. You can configure which attack types the system should automatically detect based on your security requirements.

## 🎯 Features

### **Attack Categories Available**

1. **Port Scan Detection**
   - TCP SYN Scan
   - TCP NULL Scan  
   - TCP XMAS Scan
   - TCP FIN Scan
   - UDP Port Scan
   - Vertical Port Scan
   - Horizontal Port Scan

2. **Denial of Service (DoS) Attacks**
   - SYN Flood Attack
   - UDP Flood Attack
   - ICMP Flood Attack
   - HTTP Flood Attack

3. **Brute Force Attacks**
   - SSH Brute Force
   - FTP Brute Force
   - RDP Brute Force
   - Web Application Brute Force

4. **Malware Detection**
   - Command & Control Communication
   - Botnet Activity
   - Ransomware Activity

5. **Reconnaissance**
   - DNS Enumeration
   - Network Discovery
   - OS Fingerprinting

## 🚀 Quick Start

### **Option 1: Web Interface (Recommended)**

1. Start the system:
   ```bash
   python start_system.py
   ```

2. Open your browser to:
   ```
   http://localhost:5000/attack_categories
   ```

3. Use the interface to:
   - View all available attack types
   - Enable/disable specific attacks
   - See severity levels and auto-responses
   - Use quick action buttons

### **Option 2: Command Line Configuration**

```bash
# Show all available categories
python configure_attacks.py show

# Enable all critical severity attacks
python configure_attacks.py critical

# Enable all port scan detection
python configure_attacks.py portscan

# Enable specific attacks
python configure_attacks.py enable SYN_SCAN NULL_SCAN XMAS_SCAN

# Enable all attacks
python configure_attacks.py all

# Disable all attacks
python configure_attacks.py none

# Save current configuration
python configure_attacks.py save

# Load saved configuration
python configure_attacks.py load

# Check current status
python configure_attacks.py status
```

## 🛡️ Severity Levels

- **CRITICAL** (🔴): Immediate threats requiring instant response
- **HIGH** (🟠): Serious threats needing quick attention  
- **MEDIUM** (🟡): Moderate threats for monitoring
- **LOW** (🟢): Minor threats for logging

## ⚡ Automatic Responses

Each attack type has a predefined response:

- **block_ip_immediately**: Instant IP blocking
- **block_ip_temporarily**: Temporary IP blocking
- **block_ip_after_threshold**: Block after multiple attempts
- **rate_limit_requests**: Rate limit HTTP requests
- **quarantine_system**: Isolate infected system
- **monitor_and_alert**: Monitor and notify only
- **block_domain_and_ip**: Block both domain and IP

## 📊 Detection Rules

Each attack type uses specific detection rules:

### **Example: SYN Scan Detection**
```json
{
  "tcp_flags": ["SYN"],
  "connection_rate": "> 10/second",
  "unique_ports": "> 5",
  "confidence_threshold": 0.8
}
```

### **Example: SSH Brute Force**
```json
{
  "dst_port": 22,
  "protocol": "TCP",
  "connection_rate": "> 5/second",
  "failed_attempts": "> 10",
  "confidence_threshold": 0.85
}
```

## 🔧 Configuration Methods

### **1. Web Interface**
- User-friendly visual interface
- Real-time status updates
- Bulk operations available
- Detailed attack information

### **2. REST API**
```bash
# Get all categories
curl http://localhost:5000/api/attack_categories

# Enable specific attacks
curl -X POST http://localhost:5000/api/attack_categories/enable \
  -H "Content-Type: application/json" \
  -d '{"attack_ids": ["SYN_SCAN", "NULL_SCAN"]}'

# Disable attacks
curl -X POST http://localhost:5000/api/attack_categories/disable \
  -H "Content-Type: application/json" \
  -d '{"attack_ids": ["SYN_SCAN"]}'
```

### **3. Command Line Script**
```bash
python configure_attacks.py critical
```

## 📈 Monitoring and Statistics

The system provides real-time statistics:
- Total categories available
- Number of enabled attacks
- Critical attacks enabled
- Coverage percentage

## 🔄 Integration with Detection

Once attack categories are enabled:

1. **Automatic Detection**: System automatically analyzes incoming packets
2. **Rule Matching**: Applies detection rules based on enabled attacks
3. **Confidence Scoring**: Calculates confidence for each detection
4. **Priority Handling**: Prioritizes automatic rules over ML predictions
5. **Response Actions**: Executes predefined responses

## 📝 Example Use Cases

### **High Security Environment**
```bash
# Enable all critical and high severity attacks
python configure_attacks.py critical
python configure_attacks.py enable SSH_BRUTE_FORCE RDP_BRUTE_FORCE SYN_FLOOD
```

### **Web Server Protection**
```bash
# Enable web-specific attacks
python configure_attacks.py enable HTTP_FLOOD WEB_BRUTE_FORCE SQL_INJECTION
```

### **Network Monitoring**
```bash
# Enable reconnaissance and scanning detection
python configure_attacks.py portscan
python configure_attacks.py enable DNS_ENUMERATION NETWORK_DISCOVERY
```

## 🛠️ Configuration Persistence

Save and load configurations:

```bash
# Save current setup
python configure_attacks.py save

# Creates attack_config.json with:
{
  "enabled_attacks": ["SYN_SCAN", "NULL_SCAN", ...],
  "timestamp": "2024-01-01T12:00:00"
}

# Load saved setup
python configure_attacks.py load
```

## 🔍 Real-time Detection Flow

1. **Packet Received** → Network packet captured
2. **Rule Analysis** → Automatic rules check enabled attacks
3. **ML Processing** → Machine learning models analyze
4. **Priority Logic** → Automatic rules take priority if high confidence
5. **Response Execution** → Auto-response actions triggered
6. **Logging & Alerting** → Events logged and notifications sent

## 📋 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/attack_categories` | GET | Get all categories and status |
| `/api/attack_categories/enable` | POST | Enable specific attacks |
| `/api/attack_categories/disable` | POST | Disable specific attacks |
| `/api/attack_categories/{id}` | GET | Get attack details |

## 🎛️ Advanced Configuration

### **Custom Detection Rules**
You can modify detection rules in `attack_categories.py`:

```python
"SYN_SCAN": {
    "name": "TCP SYN Scan",
    "detection_rules": {
        "tcp_flags": ["SYN"],
        "connection_rate": "> 10/second",  # Adjust threshold
        "confidence_threshold": 0.8       # Adjust confidence
    }
}
```

### **Custom Response Actions**
Add new response types in the configuration and implement them in your system.

## 🔒 Security Considerations

- **Enable Only Needed Attacks**: Reduce false positives
- **Monitor Critical Attacks**: Prioritize critical severity
- **Regular Updates**: Keep detection rules current
- **Log All Actions**: Maintain audit trail
- **Test Configurations**: Validate in test environment

## 🚨 Troubleshooting

### **Common Issues**

1. **Attack Not Detected**
   - Check if attack type is enabled
   - Verify detection rules match traffic
   - Check confidence thresholds

2. **Too Many False Positives**
   - Increase confidence thresholds
   - Disable overly sensitive rules
   - Adjust rate limits

3. **Configuration Not Saving**
   - Check file permissions
   - Verify disk space
   - Check JSON syntax

### **Debug Mode**
Enable debug logging:
```bash
export LOG_LEVEL=DEBUG
python start_system.py
```

## 📞 Support

For issues with attack categories:
1. Check system logs
2. Verify configuration syntax
3. Test with known attack patterns
4. Review detection rules

---

**Next Steps:**
1. Start the system: `python start_system.py`
2. Open web interface: http://localhost:5000/attack_categories
3. Configure your attack detection preferences
4. Monitor real-time detections
