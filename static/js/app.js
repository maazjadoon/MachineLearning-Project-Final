// Global variables
let socket = null;
let isConnected = false;

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    // Add page load animation
    document.body.style.opacity = '0';
    setTimeout(() => {
        document.body.style.transition = 'opacity 0.5s ease-in';
        document.body.style.opacity = '1';
    }, 100);
    
    initializeSocket();
    loadDashboardStats();
    setInterval(loadDashboardStats, 5000); // Update stats every 5 seconds
    
    // Only load threat detections if we're on a page that has the threatDetections container
    if (document.getElementById('threatDetections')) {
        loadThreatDetections();
        setInterval(loadThreatDetections, 3000); // Poll every 3 seconds
    }
    
    // Show welcome toast
    setTimeout(() => {
        showToast('Welcome to Cyber Sentinel! System initialized.', 'success', 3000);
    }, 1000);
});

// Socket.IO initialization
function initializeSocket() {
    socket = io();
    
    socket.on('connect', function() {
        console.log('Connected to server');
        isConnected = true;
        updateConnectionStatus(true);
        addActivity('Connected to Cyber Sentinel', 'info');
    });
    
    socket.on('disconnect', function() {
        console.log('Disconnected from server');
        isConnected = false;
        updateConnectionStatus(false);
        addActivity('Disconnected from server', 'info');
    });
    
    socket.on('status', function(data) {
        console.log('Status:', data);
        addActivity(data.message, 'info');
    });
    
    socket.on('threat_update', function(data) {
        console.log('Threat update:', data);
        handleThreatUpdate(data);
    });
    
    socket.on('new_detection', function(detection) {
        console.log('New detection via SocketIO:', detection);
        // Track this detection ID to avoid duplicates
        const detectionId = `${detection.timestamp}_${detection.source_ip}_${detection.destination_ip}_${detection.attack_type}`;
        if (!knownDetectionIds.has(detectionId)) {
            knownDetectionIds.add(detectionId);
            // Add detection to UI in real-time
            addThreatDetectionToUI(detection);
            // Update count
            updateDetectionCount();
            // Show notification
            showToast(`🚨 New threat detected: ${detection.attack_type}`, 'warning', 5000);
        }
    });
    
    socket.on('stats_update', function(data) {
        console.log('Stats update via SocketIO:', data);
        // Update dashboard statistics in real-time
        updateDashboardStatsRealTime(data);
    });
    
    socket.on('sample_traffic', function(data) {
        console.log('Sample traffic:', data);
        handleSampleTraffic(data);
    });
    
    socket.on('error', function(data) {
        console.error('Socket error:', data);
        addActivity(`Error: ${data.message}`, 'threat');
    });
}

// Update connection status indicator
function updateConnectionStatus(connected) {
    const statusIndicator = document.getElementById('statusIndicator');
    const statusText = document.getElementById('statusText');
    const statusDot = statusIndicator.querySelector('.status-dot');
    
    if (connected) {
        statusDot.classList.add('connected');
        statusText.textContent = 'Connected';
        statusIndicator.style.background = 'rgba(0, 255, 136, 0.1)';
    } else {
        statusDot.classList.remove('connected');
        statusText.textContent = 'Disconnected';
        statusIndicator.style.background = 'rgba(255, 68, 68, 0.1)';
    }
}

// Smooth number counter animation
function animateNumber(element, targetValue, duration = 1000) {
    if (!element) return;
    
    const startValue = parseInt(element.textContent.replace(/,/g, '')) || 0;
    const target = parseInt(targetValue) || 0;
    
    if (startValue === target) {
        element.textContent = target.toLocaleString();
        return;
    }
    
    const steps = Math.abs(target - startValue);
    if (steps === 0) return;
    
    const increment = target > startValue ? 1 : -1;
    const stepDuration = Math.max(10, duration / steps);
    
    let currentValue = startValue;
    const timer = setInterval(() => {
        currentValue += increment;
        if ((increment > 0 && currentValue >= target) || 
            (increment < 0 && currentValue <= target)) {
            currentValue = target;
            clearInterval(timer);
        }
        element.textContent = currentValue.toLocaleString();
        element.classList.add('counter', 'animate');
        setTimeout(() => element.classList.remove('animate'), 500);
    }, stepDuration);
}

// Load dashboard statistics
async function loadDashboardStats() {
    try {
        const response = await fetch('/api/stats');
        const stats = await response.json();
        
        // Update stats cards with smooth animations
        const totalEl = document.getElementById('totalDetections');
        const threatsEl = document.getElementById('threatsDetected');
        const normalEl = document.getElementById('normalTraffic');
        
        animateNumber(totalEl, stats.total_detections || 0);
        animateNumber(threatsEl, stats.threats_detected || 0);
        animateNumber(normalEl, stats.normal_traffic || 0);
        
        // Update AI models status if available
        if (stats.ai_models) {
            const aiModelsEl = document.getElementById('aiModels');
            if (aiModelsEl) {
                animateNumber(aiModelsEl, stats.ai_models.models_loaded || 0);
            }
        }
        
        // Update system status
        const socketStatus = document.getElementById('socketStatus');
        const modelStatus = document.getElementById('modelStatus');
        
        if (stats.system_status === 'operational') {
            socketStatus.textContent = 'Connected';
            socketStatus.className = 'status-active';
            modelStatus.textContent = 'Active';
            modelStatus.className = 'status-active';
        } else {
            socketStatus.textContent = 'Disconnected';
            socketStatus.className = 'status-inactive';
            modelStatus.textContent = 'Inactive';
            modelStatus.className = 'status-inactive';
        }
        
        // Update recent activity
        updateRecentActivity(stats.recent_activity);
        
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

// Update dashboard statistics in real-time
function updateDashboardStatsRealTime(data) {
    try {
        // Increment threat count
        const threatsEl = document.getElementById('threatsDetected');
        if (threatsEl) {
            const currentCount = parseInt(threatsEl.textContent.replace(/,/g, '')) || 0;
            animateNumber(threatsEl, currentCount + 1);
        }
        
        // Increment total detections
        const totalEl = document.getElementById('totalDetections');
        if (totalEl) {
            const currentTotal = parseInt(totalEl.textContent.replace(/,/g, '')) || 0;
            animateNumber(totalEl, currentTotal + 1);
        }
        
        // Update AI models status (show as active since we just processed a threat)
        const aiModelsEl = document.getElementById('aiModels');
        if (aiModelsEl) {
            animateNumber(aiModelsEl, 1); // Show 1 active model
        }
        
        // Add to recent activity
        if (data.new_threat) {
            const message = `Threat detected: ${data.new_threat.attack_type} from ${data.new_threat.source_ip}`;
            addActivity(message, 'threat');
        }
        
        // Flash the stats cards to show update
        [threatsEl, totalEl, aiModelsEl].forEach(el => {
            if (el) {
                el.style.boxShadow = '0 0 20px rgba(255, 68, 68, 0.5)';
                setTimeout(() => {
                    el.style.boxShadow = '';
                }, 1000);
            }
        });
        
    } catch (error) {
        console.error('Error updating real-time stats:', error);
    }
}

// Update recent activity feed
function updateRecentActivity(activities) {
    const activityFeed = document.getElementById('activityFeed');
    
    // Clear existing activities (keep the first info message if no activities)
    if (activities.length > 0) {
        activityFeed.innerHTML = '';
    }
    
    // Add new activities (show latest 5)
    activities.slice(-5).reverse().forEach(activity => {
        addActivityFromHistory(activity);
    });
}

// Add activity from history
function addActivityFromHistory(activity) {
    const result = activity.result;
    let message = '';
    let type = 'info';
    
    if (result.error) {
        message = `Error: ${result.error}`;
        type = 'threat';
    } else if (result.threat_detected) {
        message = `Threat detected: ${result.attack_type} from ${activity.source_ip}`;
        type = 'threat';
    } else {
        message = `Normal traffic from ${activity.source_ip} to ${activity.destination_ip}`;
        type = 'normal';
    }
    
    addActivity(message, type);
}

// Add activity message
function addActivity(message, type = 'info') {
    const activityFeed = document.getElementById('activityFeed');
    
    // Remove the initial placeholder if it exists
    const placeholder = activityFeed.querySelector('.empty-state');
    if (placeholder) {
        placeholder.remove();
    }
    
    const activityItem = document.createElement('div');
    activityItem.className = `activity-item ${type}`;
    activityItem.style.opacity = '0';
    activityItem.style.transform = 'translateX(-20px)';
    
    const icon = type === 'threat' ? 'exclamation-triangle' : 
                 type === 'normal' ? 'check-circle' : 'info-circle';
    
    activityItem.innerHTML = `
        <i class="fas fa-${icon}"></i>
        <span>${message}</span>
        <span style="margin-left: auto; font-size: 0.8rem; color: #888;">${new Date().toLocaleTimeString()}</span>
    `;
    
    activityFeed.appendChild(activityItem);
    
    // Trigger animation
    setTimeout(() => {
        activityItem.style.opacity = '1';
        activityItem.style.transform = 'translateX(0)';
        activityItem.style.transition = 'all 0.4s ease-out';
    }, 10);
    
    // Smooth scroll
    setTimeout(() => {
        activityFeed.scrollTo({
            top: activityFeed.scrollHeight,
            behavior: 'smooth'
        });
    }, 100);
    
    // Keep only last 10 items
    const items = activityFeed.querySelectorAll('.activity-item');
    if (items.length > 10) {
        items[0].style.opacity = '0';
        setTimeout(() => items[0].remove(), 400);
    }
}

// Toast notification system (global function)
window.showToast = function(message, type = 'info', duration = 5000) {
    // Remove existing toasts
    const existingToasts = document.querySelectorAll('.toast');
    existingToasts.forEach(toast => {
        toast.classList.add('hide');
        setTimeout(() => toast.remove(), 300);
    });
    
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    const icons = {
        success: 'check-circle',
        error: 'exclamation-circle',
        warning: 'exclamation-triangle',
        info: 'info-circle'
    };
    
    toast.innerHTML = `
        <i class="fas fa-${icons[type] || 'info-circle'} toast-icon"></i>
        <div class="toast-content">${message}</div>
        <button class="toast-close" onclick="this.parentElement.classList.add('hide'); setTimeout(() => this.parentElement.remove(), 300)">&times;</button>
    `;
    
    document.body.appendChild(toast);
    
    // Auto remove after duration
    setTimeout(() => {
        toast.classList.add('hide');
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

// Test threat detection
async function testDetection() {
    try {
        showToast('Running test detection...', 'info', 2000);
        
        const testData = {
            srcip: '192.168.1.100',
            dstip: '10.0.1.50',
            src_port: 54321,
            dst_port: 80,
            protocol: 'tcp',
            packet_size: 1500,
            duration: 5.5,
            flags: 24
        };
        
        const response = await fetch('/api/detect', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(testData)
        });
        
        const result = await response.json();
        
        if (result.error) {
            showToast(`Error: ${result.error}`, 'error');
            if (result.suggestion) {
                setTimeout(() => showToast(result.suggestion, 'info', 7000), 2000);
            }
        } else {
            const message = `Test detection: ${result.threat_detected ? 'THREAT' : 'NORMAL'} - ${result.attack_type || 'Normal'}`;
            const toastType = result.threat_detected ? 'warning' : 'success';
            showToast(message, toastType);
            
            // Show warning if using fallback model
            if (result.warning) {
                setTimeout(() => showToast(result.warning, 'warning', 8000), 2000);
            }
            
            addActivity(message, result.threat_detected ? 'threat' : 'normal');
        }
        
    } catch (error) {
        console.error('Error testing detection:', error);
        showToast('Error testing detection. Please try again.', 'error');
    }
}

// Show system info modal
function showSystemInfo() {
    const modal = document.getElementById('systemModal');
    modal.style.display = 'flex';
    modal.classList.add('show');
    document.getElementById('lastUpdate').textContent = new Date().toLocaleString();
}

// Close modal
function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    modal.classList.remove('show');
    setTimeout(() => {
        modal.style.display = 'none';
    }, 300);
}

// Handle threat update from WebSocket
function handleThreatUpdate(data) {
    // This will be implemented in detection.js
    if (typeof handleThreatUpdateDetection === 'function') {
        handleThreatUpdateDetection(data);
    }
}

// Handle sample traffic from WebSocket
function handleSampleTraffic(data) {
    // This will be implemented in detection.js
    if (typeof handleSampleTrafficDetection === 'function') {
        handleSampleTrafficDetection(data);
    }
}

// Close modals when clicking outside
window.onclick = function(event) {
    const modals = document.getElementsByClassName('modal');
    for (let modal of modals) {
        if (event.target == modal) {
            modal.style.display = 'none';
        }
    }
}

// Utility function to format timestamp
function formatTimestamp(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleString();
}

// Utility function to format confidence
function formatConfidence(confidence) {
    return (confidence * 100).toFixed(1) + '%';
}

// Threat Detections Management
let knownDetectionIds = new Set(); // Track displayed detections to avoid duplicates

// Load threat detections from server
async function loadThreatDetections() {
    try {
        const response = await fetch('/detections');
        const data = await response.json();
        
        if (data.detections && Array.isArray(data.detections)) {
            // Update detection count
            updateDetectionCount(data.detections.length);
            
            // Add new detections (only ones we haven't seen)
            data.detections.forEach(detection => {
                const detectionId = `${detection.timestamp}_${detection.source_ip}_${detection.destination_ip}_${detection.attack_type}`;
                if (!knownDetectionIds.has(detectionId)) {
                    knownDetectionIds.add(detectionId);
                    addThreatDetectionToUI(detection);
                }
            });
        }
    } catch (error) {
        console.error('Error loading threat detections:', error);
    }
}

// Add threat detection to UI
function addThreatDetectionToUI(detection) {
    const container = document.getElementById('threatDetections');
    
    // Remove empty state if present
    const emptyState = container.querySelector('.empty-state');
    if (emptyState) {
        emptyState.remove();
    }
    
    // Create detection item
    const item = document.createElement('div');
    item.className = 'threat-detection-item';
    item.style.opacity = '0';
    item.style.transform = 'translateX(-20px)';
    
    const severity = (detection.severity || 'UNKNOWN').toLowerCase();
    const confidence = typeof detection.confidence === 'number' 
        ? (detection.confidence * 100).toFixed(2) + '%' 
        : detection.confidence || '0%';
    
    const timestamp = new Date(detection.timestamp).toLocaleString();
    
    item.innerHTML = `
        <div class="threat-detection-header">
            <div class="threat-attack-type">
                <i class="fas fa-exclamation-triangle"></i>
                ${detection.attack_type || 'Unknown Attack'}
            </div>
            <div class="threat-confidence">${confidence}</div>
        </div>
        <div class="threat-details-row">
            <div class="threat-detail">
                <span class="threat-detail-label">Source IP</span>
                <span class="threat-detail-value">${detection.source_ip || 'unknown'}</span>
            </div>
            <div class="threat-detail">
                <span class="threat-detail-label">Destination IP</span>
                <span class="threat-detail-value">${detection.destination_ip || 'unknown'}</span>
            </div>
            <div class="threat-detail">
                <span class="threat-detail-label">Severity</span>
                <span class="threat-severity ${severity}">${detection.severity || 'UNKNOWN'}</span>
            </div>
            <div class="threat-detail">
                <span class="threat-detail-label">Protocol</span>
                <span class="threat-detail-value">${(detection.protocol || 'unknown').toUpperCase()}</span>
            </div>
        </div>
        ${detection.src_port || detection.dst_port ? `
        <div class="threat-details-row">
            <div class="threat-detail">
                <span class="threat-detail-label">Source Port</span>
                <span class="threat-detail-value">${detection.src_port || 'N/A'}</span>
            </div>
            <div class="threat-detail">
                <span class="threat-detail-label">Destination Port</span>
                <span class="threat-detail-value">${detection.dst_port || 'N/A'}</span>
            </div>
            <div class="threat-detail">
                <span class="threat-detail-label">Model Used</span>
                <span class="threat-detail-value">${detection.model_used || 'Unknown'}</span>
            </div>
        </div>
        ` : ''}
        ${detection.recommended_action ? `
        <div style="margin-top: 12px; padding: 10px; background: rgba(0, 0, 0, 0.2); border-radius: 8px;">
            <strong style="color: #00d4ff;">Recommended Action:</strong> ${detection.recommended_action}
        </div>
        ` : ''}
        <div class="threat-timestamp">
            <i class="fas fa-clock"></i>
            ${timestamp}
        </div>
    `;
    
    // Insert at the top (newest first)
    container.insertBefore(item, container.firstChild);
    
    // Animate in
    setTimeout(() => {
        item.style.transition = 'all 0.4s ease-out';
        item.style.opacity = '1';
        item.style.transform = 'translateX(0)';
    }, 10);
    
    // Keep only last 50 detections in DOM
    const items = container.querySelectorAll('.threat-detection-item');
    if (items.length > 50) {
        const oldestItem = items[items.length - 1];
        oldestItem.style.opacity = '0';
        setTimeout(() => oldestItem.remove(), 400);
    }
    
    // Scroll to top to show new detection
    container.scrollTop = 0;
}

// Update detection count badge
function updateDetectionCount(count) {
    const countElement = document.getElementById('detectionCount');
    if (countElement) {
        if (count !== undefined) {
            countElement.textContent = `${count} threat${count !== 1 ? 's' : ''}`;
        } else {
            // Count from DOM if count not provided
            const container = document.getElementById('threatDetections');
            const items = container.querySelectorAll('.threat-detection-item');
            countElement.textContent = `${items.length} threat${items.length !== 1 ? 's' : ''}`;
        }
    }
}

// Clear all detections
function clearDetections() {
    if (confirm('Are you sure you want to clear all threat detections?')) {
        const container = document.getElementById('threatDetections');
        const items = container.querySelectorAll('.threat-detection-item');
        
        // Animate out
        items.forEach((item, index) => {
            setTimeout(() => {
                item.style.opacity = '0';
                item.style.transform = 'translateX(-20px)';
                setTimeout(() => item.remove(), 400);
            }, index * 50);
        });
        
        // Show empty state
        setTimeout(() => {
            if (container.children.length === 0) {
                container.innerHTML = `
                    <div class="empty-state">
                        <i class="fas fa-shield-check"></i>
                        <p>No threats detected. System is monitoring...</p>
                    </div>
                `;
            }
            knownDetectionIds.clear();
            updateDetectionCount(0);
        }, items.length * 50 + 500);
    }
}

// Make clearDetections available globally
window.clearDetections = clearDetections;