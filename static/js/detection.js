// Detection page specific functionality
let isMonitoring = false;
let trafficCount = 0;
let threatCount = 0;
let detectionPollingInterval = null;
let lastDetectionCount = 0;

// Initialize detection page
document.addEventListener('DOMContentLoaded', function() {
    console.log('Detection page initialized');
    
    // Start polling for detections immediately
    startDetectionPolling();
    
    // Set up WebSocket listeners for real-time updates
    if (typeof socket !== 'undefined' && socket) {
        socket.on('new_detection', function(detection) {
            console.log('New detection via WebSocket:', detection);
            // Add to live threats display immediately
            addNewDetectionToLiveThreats(detection);
        });
        
        socket.on('stats_update', function(data) {
            console.log('Stats update on detection page:', data);
            // Update any stats displays on detection page
            updateDetectionPageStats(data);
        });
    }
    
    // Auto-start monitoring if we're on the detection page
    // (packet capture may already be running)
    setTimeout(() => {
        if (!isMonitoring) {
            startMonitoring();
        }
    }, 1000);
});

// Start polling for detections
function startDetectionPolling() {
    console.log('Starting detection polling...');
    
    // Initial fetch
    fetchDetections();
    
    // Poll every 10 seconds (reduced frequency to prevent overload)
    detectionPollingInterval = setInterval(fetchDetections, 10000);
}

// Stop polling for detections
function stopDetectionPolling() {
    if (detectionPollingInterval) {
        clearInterval(detectionPollingInterval);
        detectionPollingInterval = null;
        console.log('Detection polling stopped');
    }
}

// Fetch detections from /detections endpoint
function fetchDetections() {
    fetch('/detections')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            updateLiveThreats(data.detections || []);
            updateThreatsStats(data.total || 0, data.timestamp);
        })
        .catch(error => {
            console.error('Error fetching detections:', error);
            // Don't show error to user for polling failures
        });
}

// Start monitoring
function startMonitoring() {
    isMonitoring = true;
    const startBtn = document.getElementById('startMonitoring');
    const stopBtn = document.getElementById('stopMonitoring');
    if (startBtn) startBtn.disabled = true;
    if (stopBtn) stopBtn.disabled = false;
    
    addTrafficMessage('Monitoring started - listening for network traffic...', 'info');
    addThreatMessage('Threat detection activated. Analyzing incoming traffic...', 'info');
}

// Stop monitoring
function stopMonitoring() {
    isMonitoring = false;
    document.getElementById('startMonitoring').disabled = false;
    document.getElementById('stopMonitoring').disabled = true;
    
    addTrafficMessage('Monitoring stopped.', 'info');
    addThreatMessage('Threat detection paused.', 'info');
}

// Test port scan
function testPortScan() {
    if (!isMonitoring) {
        alert('Please start monitoring first');
        return;
    }
    
    addTrafficMessage('🔍 Simulating port scan attack...', 'info');
    addThreatMessage('🔍 Port scan simulation initiated...', 'info');
    
    // Make POST request to test endpoint
    fetch('/api/test_port_scan', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({})
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(result => {
        console.log('Port scan test result:', result);
        
        if (result.success) {
            addTrafficMessage(`✅ Port scan simulation completed: ${result.packets_sent} packets sent`, 'info');
            
            if (result.threats_detected > 0) {
                addThreatMessage(`🚨 PORT SCAN DETECTED! ${result.threats_detected}/${result.packets_sent} packets identified as threats`, 'threat');
                
                // Show final detection result
                if (result.final_result && result.final_result.threat_detected) {
                    const fr = result.final_result;
                    addThreatMessage(
                        `Attack Type: ${fr.attack_type} | Confidence: ${(fr.confidence * 100).toFixed(1)}% | Severity: ${fr.severity}`,
                        'threat'
                    );
                    
                    if (fr.scan_details && fr.scan_details.length > 0) {
                        fr.scan_details.forEach(detail => {
                            addThreatMessage(`  • ${detail}`, 'info');
                        });
                    }
                }
            } else {
                addThreatMessage(`ℹ️ No port scan pattern detected yet (checked ${result.packets_sent} packets)`, 'info');
            }
        } else {
            addTrafficMessage(`❌ Port scan test failed: ${result.error || result.message}`, 'error');
            addThreatMessage(`❌ ${result.error || result.message}`, 'error');
        }
    })
    .catch(error => {
        console.error('Port scan test error:', error);
        addTrafficMessage(`❌ Port scan test failed: ${error.message}`, 'error');
        addThreatMessage(`❌ Port scan test failed: ${error.message}`, 'error');
    });
}

// Test general threat detection
function testThreat() {
    if (!isMonitoring) {
        alert('Please start monitoring first');
        return;
    }
    
    // Generate a test threat
    const testThreatData = {
        srcip: '192.168.1.666', // Suspicious IP
        dstip: '10.0.1.100',
        src_port: 6666, // Suspicious port
        dst_port: 22, // SSH port
        protocol: 'tcp',
        packet_size: 1500, // Large packets
        duration: 8.5, // Long duration
        flags: 2 // SYN flood
    };
    
    // Send via WebSocket
    if (socket) {
        socket.emit('realtime_detection', testThreatData);
        addTrafficMessage('🧪 Test threat packet sent via WebSocket', 'info');
    }
}

// Handle sample traffic from WebSocket
function handleSampleTrafficDetection(data) {
    if (!isMonitoring) {
        // Auto-start monitoring if packet capture is active
        if (data && data.srcip) {
            startMonitoring();
        }
    }
    
    trafficCount++;
    addTrafficItem(data);
}

// Handle threat update from WebSocket
function handleThreatUpdateDetection(data) {
    // Auto-start monitoring if threat detected
    if (!isMonitoring && data && data.result && data.result.threat_detected) {
        startMonitoring();
    }
    
    if (!isMonitoring) return;
    
    const result = data.result;
    
    if (result && result.error) {
        addThreatMessage(`Error: ${result.error}`, 'error');
        return;
    }
    
    if (result && result.threat_detected) {
        threatCount++;
        addThreatItem(data);
        
        // Show reasoning panel for threats
        if (result.refinement_path) {
            showReasoningPanel(result);
        }
        
        // Show port scan details if available
        if (result.details && result.details.length > 0) {
            result.details.forEach(detail => {
                addThreatMessage(`  📊 ${detail}`, 'info');
            });
        }
        
        // Show scan details if available (alternative field name)
        if (result.scan_details && result.scan_details.length > 0) {
            result.scan_details.forEach(detail => {
                addThreatMessage(`  📊 ${detail}`, 'info');
            });
        }
    } else {
        // Optionally log normal traffic
        // addThreatMessage(`Normal traffic from ${data.data.srcip} to ${data.data.dstip}`, 'normal');
    }
}

// Add traffic item to feed
function addTrafficItem(trafficData) {
    const trafficFeed = document.getElementById('trafficFeed');
    
    // Remove empty state if present
    const emptyState = trafficFeed.querySelector('.empty-state');
    if (emptyState) {
        emptyState.remove();
    }
    
    const trafficItem = document.createElement('div');
    trafficItem.className = 'traffic-item';
    
    // Check for suspicious patterns
    const isSuspicious = trafficData.packet_size > 1000 || trafficData.duration > 5;
    if (isSuspicious) {
        trafficItem.classList.add('suspicious');
    }
    
    trafficItem.innerHTML = `
        <div class="traffic-header">
            <span class="traffic-ip">${trafficData.srcip} → ${trafficData.dstip}</span>
            <span class="traffic-protocol">${trafficData.protocol.toUpperCase()}</span>
        </div>
        <div class="traffic-details">
            <div>Ports: ${trafficData.src_port} → ${trafficData.dst_port}</div>
            <div>Size: ${trafficData.packet_size} bytes</div>
            <div>Duration: ${trafficData.duration.toFixed(2)}s</div>
            <div>Flags: 0x${trafficData.flags.toString(16)}</div>
        </div>
    `;
    
    trafficFeed.appendChild(trafficItem);
    trafficFeed.scrollTop = trafficFeed.scrollHeight;
    
    // Keep only last 50 items
    const items = trafficFeed.querySelectorAll('.traffic-item');
    if (items.length > 50) {
        items[0].remove();
    }
}

// Add threat item to analysis
function addThreatItem(threatData) {
    const threatAnalysis = document.getElementById('threatAnalysis');
    const result = threatData.result;
    
    // Remove empty state if present
    const emptyState = threatAnalysis.querySelector('.empty-state');
    if (emptyState) {
        emptyState.remove();
    }
    
    const threatItem = document.createElement('div');
    threatItem.className = `threat-item ${result.threat_detected ? '' : 'normal'}`;
    
    const severityClass = `severity-${(result.severity || 'low').toLowerCase()}`;
    const detectionMethod = result.model_used || result.detection_method || 'ML Model';
    
    let detailsHTML = '';
    if (result.details && result.details.length > 0) {
        detailsHTML = '<div class="threat-scan-details">' + 
            result.details.map(d => `<div>• ${d}</div>`).join('') +
            '</div>';
    } else if (result.scan_details && result.scan_details.length > 0) {
        detailsHTML = '<div class="threat-scan-details">' + 
            result.scan_details.map(d => `<div>• ${d}</div>`).join('') +
            '</div>';
    }
    
    threatItem.innerHTML = `
        <div class="threat-header">
            <span class="threat-type">${result.attack_type}</span>
            <span class="threat-confidence">${formatConfidence(result.confidence)}</span>
        </div>
        <div class="threat-details">
            <span class="threat-severity ${severityClass}">${result.severity || 'UNKNOWN'}</span>
            <span>From: ${threatData.data.srcip} → ${threatData.data.dstip}</span>
            <span class="detection-badge">${detectionMethod}</span>
        </div>
        ${detailsHTML}
        <div class="threat-recommendation">
            <strong>Action:</strong> ${result.recommended_action || 'Investigate further'}
        </div>
        <div class="threat-actions">
            <button class="btn btn-secondary" onclick="viewThreatDetails(this)">
                <i class="fas fa-search"></i> Details
            </button>
            <button class="btn btn-primary" onclick="takeAction('${result.attack_type}')">
                <i class="fas fa-shield-alt"></i> Mitigate
            </button>
        </div>
    `;
    
    // Store the full data for details view
    threatItem.dataset.threatData = JSON.stringify(threatData);
    
    threatAnalysis.appendChild(threatItem);
    threatAnalysis.scrollTop = threatAnalysis.scrollHeight;
    
    // Keep only last 20 items
    const items = threatAnalysis.querySelectorAll('.threat-item');
    if (items.length > 20) {
        items[0].remove();
    }
}

// Add message to traffic feed
function addTrafficMessage(message, type = 'info') {
    const trafficFeed = document.getElementById('trafficFeed');
    
    const messageItem = document.createElement('div');
    messageItem.className = `traffic-item ${type === 'info' ? '' : 'suspicious'}`;
    messageItem.innerHTML = `
        <div class="traffic-header">
            <span><i class="fas fa-${type === 'info' ? 'info-circle' : 'exclamation-triangle'}"></i> ${message}</span>
        </div>
    `;
    
    trafficFeed.appendChild(messageItem);
    trafficFeed.scrollTop = trafficFeed.scrollHeight;
}

// Add message to threat analysis
function addThreatMessage(message, type = 'info') {
    const threatAnalysis = document.getElementById('threatAnalysis');
    
    // Remove empty state if present
    const emptyState = threatAnalysis.querySelector('.empty-state');
    if (emptyState) {
        emptyState.remove();
    }
    
    const messageItem = document.createElement('div');
    messageItem.className = `threat-item ${type === 'normal' ? 'normal' : type === 'threat' ? '' : 'normal'}`;
    
    const iconClass = type === 'info' ? 'info-circle' : 
                     type === 'normal' ? 'check-circle' : 
                     type === 'error' ? 'times-circle' :
                     'exclamation-triangle';
    
    messageItem.innerHTML = `
        <div class="threat-header">
            <span><i class="fas fa-${iconClass}"></i> ${message}</span>
        </div>
    `;
    
    threatAnalysis.appendChild(messageItem);
    threatAnalysis.scrollTop = threatAnalysis.scrollHeight;
}

// Show TRM reasoning panel
function showReasoningPanel(threatResult) {
    const reasoningPanel = document.getElementById('reasoningPanel');
    const reasoningContent = document.getElementById('reasoningContent');
    
    reasoningPanel.style.display = 'block';
    reasoningContent.innerHTML = '';
    
    if (!threatResult.refinement_path) {
        reasoningContent.innerHTML = '<p>No reasoning data available.</p>';
        return;
    }
    
    threatResult.refinement_path.forEach(step => {
        const stepElement = document.createElement('div');
        stepElement.className = 'reasoning-step';
        
        stepElement.innerHTML = `
            <div class="step-header">
                <span class="step-number">Step ${step.step}</span>
                <span class="step-confidence">${formatConfidence(step.confidence)}</span>
            </div>
            <div class="step-prediction">
                <strong>Prediction:</strong> ${step.predicted_attack}
            </div>
        `;
        
        reasoningContent.appendChild(stepElement);
    });
    
    // Add final decision
    const finalStep = document.createElement('div');
    finalStep.className = 'reasoning-step';
    finalStep.style.background = 'rgba(0, 212, 255, 0.1)';
    finalStep.style.borderLeftColor = '#00ff88';
    
    finalStep.innerHTML = `
        <div class="step-header">
            <span class="step-number">🎯 Final Decision</span>
            <span class="step-confidence">${formatConfidence(threatResult.confidence)}</span>
        </div>
        <div class="step-prediction">
            <strong>Attack Type:</strong> ${threatResult.attack_type}<br>
            <strong>Severity:</strong> ${threatResult.severity}<br>
            <strong>Model:</strong> ${threatResult.model_used || threatResult.detection_method || 'Unknown'}
        </div>
    `;
    
    reasoningContent.appendChild(finalStep);
}

// View threat details
function viewThreatDetails(button) {
    const threatItem = button.closest('.threat-item');
    const threatData = JSON.parse(threatItem.dataset.threatData);
    
    // For now, just log the data
    console.log('Threat details:', threatData);
    
    const result = threatData.result;
    let detailsMessage = `Threat Details:\n\nAttack: ${result.attack_type}\nSeverity: ${result.severity}\nConfidence: ${formatConfidence(result.confidence)}\nMethod: ${result.detection_method || 'Unknown'}`;
    
    if (result.scan_details) {
        detailsMessage += '\n\nDetails:\n' + result.scan_details.join('\n');
    }
    
    if (result.behavioral_metrics) {
        detailsMessage += '\n\nBehavioral Metrics:\n' + JSON.stringify(result.behavioral_metrics, null, 2);
    }
    
    alert(detailsMessage);
}

// Take mitigation action
function takeAction(attackType) {
    const actions = {
        'DoS': 'Blocking source IP and enabling rate limiting...',
        'Backdoor': 'Isolating system and initiating forensic analysis...',
        'Exploits': 'Patching vulnerable services and blocking exploit patterns...',
        'Reconnaissance': 'Blocking scanning IPs and implementing honeypot...',
        'SYN_SCAN': 'Blocking source IP and enabling SYN cookies...',
        'UDP_SCAN': 'Blocking UDP traffic and enabling stateful inspection...',
        'VERTICAL_SCAN': 'Blocking IP and enabling port knocking...',
        'SEQUENTIAL_SCAN': 'Blocking IP and reviewing access logs...',
        'Generic': 'Executing general threat mitigation procedures...'
    };
    
    const action = actions[attackType] || 'Executing standard mitigation procedures...';
    
    addThreatMessage(`🛡️ Mitigation: ${action}`, 'info');
    
    // Simulate action completion
    setTimeout(() => {
        addThreatMessage(`✅ Mitigation completed for ${attackType}`, 'normal');
    }, 2000);
}

// Helper function to format confidence
function formatConfidence(confidence) {
    if (typeof confidence === 'number') {
        return (confidence * 100).toFixed(1) + '%';
    }
    return confidence || '0%';
}

// Update live threats display
function updateLiveThreats(detections) {
    const container = document.getElementById('liveThreatsContainer');
    
    // Clear existing content
    container.innerHTML = '';
    
    if (!detections || detections.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-shield-alt"></i>
                <p>No threats detected yet. System is monitoring...</p>
            </div>
        `;
        return;
    }
    
    // Display threats (limit to last 20)
    const recentThreats = detections.slice(0, 20);
    
    recentThreats.forEach(threat => {
        const threatElement = document.createElement('div');
        threatElement.className = 'live-threat-item';
        
        const severityClass = `severity-${(threat.severity || 'unknown').toLowerCase()}`;
        const timeAgo = getTimeAgo(threat.timestamp);
        
        threatElement.innerHTML = `
            <div class="threat-header">
                <span class="threat-type">${threat.attack_type}</span>
                <span class="threat-time">${timeAgo}</span>
            </div>
            <div class="threat-details">
                <div class="threat-ips">
                    <i class="fas fa-arrow-right"></i>
                    <span>${threat.source_ip} → ${threat.destination_ip}</span>
                </div>
                <div class="threat-metrics">
                    <span class="confidence">Confidence: ${formatConfidence(threat.confidence)}</span>
                    <span class="severity ${severityClass}">${threat.severity}</span>
                </div>
            </div>
        `;
        
        container.appendChild(threatElement);
    });
}

// Update threats statistics
function updateThreatsStats(total, timestamp) {
    const threatsCount = document.getElementById('threatsCount');
    const lastUpdate = document.getElementById('lastUpdate');
    
    if (threatsCount) {
        threatsCount.textContent = `${total} Threats`;
        
        // Add visual indicator for new threats
        if (total > lastDetectionCount) {
            threatsCount.classList.add('new-threats');
            setTimeout(() => threatsCount.classList.remove('new-threats'), 2000);
        }
        lastDetectionCount = total;
    }
    
    if (lastUpdate && timestamp) {
        const updateTime = new Date(timestamp);
        lastUpdate.textContent = `Last update: ${updateTime.toLocaleTimeString()}`;
    }
}

// Get time ago string
function getTimeAgo(timestamp) {
    const now = new Date();
    const time = new Date(timestamp);
    const diffMs = now - time;
    const diffSecs = Math.floor(diffMs / 1000);
    const diffMins = Math.floor(diffSecs / 60);
    const diffHours = Math.floor(diffMins / 60);
    
    if (diffSecs < 60) return `${diffSecs}s ago`;
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return time.toLocaleDateString();
}

// Add new detection to live threats display (real-time)
function addNewDetectionToLiveThreats(detection) {
    const container = document.getElementById('liveThreatsContainer');
    
    // Remove empty state if present
    const emptyState = container.querySelector('.empty-state');
    if (emptyState) {
        emptyState.remove();
    }
    
    // Create new threat element
    const threatElement = document.createElement('div');
    threatElement.className = 'live-threat-item';
    
    const severityClass = `severity-${(detection.severity || 'unknown').toLowerCase()}`;
    const timeAgo = 'Just now';
    
    threatElement.innerHTML = `
        <div class="threat-header">
            <span class="threat-type">${detection.attack_type}</span>
            <span class="threat-time">${timeAgo}</span>
        </div>
        <div class="threat-details">
            <div class="threat-ips">
                <i class="fas fa-arrow-right"></i>
                <span>${detection.source_ip} → ${detection.destination_ip}</span>
            </div>
            <div class="threat-metrics">
                <span class="confidence">Confidence: ${formatConfidence(detection.confidence)}</span>
                <span class="severity ${severityClass}">${detection.severity}</span>
            </div>
        </div>
    `;
    
    // Add to top of container (newest first)
    container.insertBefore(threatElement, container.firstChild);
    
    // Keep only last 20 items
    const items = container.querySelectorAll('.live-threat-item');
    if (items.length > 20) {
        items[items.length - 1].remove();
    }
    
    // Update statistics
    const currentCount = items.length;
    updateThreatsStats(currentCount, new Date().toISOString());
}

// Update detection page statistics in real-time
function updateDetectionPageStats(data) {
    try {
        // Update threat count badge if it exists
        const threatCountBadge = document.getElementById('liveThreatsCount');
        if (threatCountBadge) {
            const currentCount = parseInt(threatCountBadge.textContent) || 0;
            threatCountBadge.textContent = currentCount + 1;
            
            // Flash the badge
            threatCountBadge.style.background = 'rgba(255, 68, 68, 0.9)';
            setTimeout(() => {
                threatCountBadge.style.background = '';
            }, 1000);
        }
        
        // Update any other stats displays on the page
        const statsElements = document.querySelectorAll('.stats-value');
        statsElements.forEach(el => {
            if (el.dataset.stat === 'threats') {
                const currentValue = parseInt(el.textContent.replace(/,/g, '')) || 0;
                el.textContent = (currentValue + 1).toLocaleString();
            }
        });
        
        // Show notification on detection page
        if (data.new_threat && typeof showToast === 'function') {
            showToast(`🚨 ${data.new_threat.attack_type} detected from ${data.new_threat.source_ip}`, 'warning', 3000);
        }
        
    } catch (error) {
        console.error('Error updating detection page stats:', error);
    }
}