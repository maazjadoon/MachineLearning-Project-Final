// History page specific functionality
let currentPage = 1;
const perPage = 20;
let currentFilter = 'all';
let totalPages = 1;
let allHistoryData = [];

// Initialize history page
document.addEventListener('DOMContentLoaded', function() {
    console.log('History page initialized');
    loadHistory();
    setupEventListeners();
});

// Setup event listeners
function setupEventListeners() {
    // Filter change
    document.getElementById('statusFilter').addEventListener('change', function() {
        currentFilter = this.value;
        currentPage = 1;
        loadHistory();
    });
    
    // Refresh button
    document.getElementById('refreshBtn')?.addEventListener('click', loadHistory);
}

// Load history data
async function loadHistory() {
    showLoading(true);
    
    try {
        const response = await fetch(`/api/history?page=${currentPage}&per_page=${perPage}&filter=${currentFilter}`);
        const data = await response.json();
        
        allHistoryData = data.history || [];
        totalPages = data.total_pages || 1;
        
        updateHistoryStats(data);
        renderHistoryTable();
        renderPagination();
        
    } catch (error) {
        console.error('Error loading history:', error);
        showError('Failed to load history data');
    } finally {
        showLoading(false);
    }
}

// Update history statistics
function updateHistoryStats(data) {
    const totalEvents = data.total_detections || 0;
    
    // Calculate threats and normal events
    let threatEvents = 0;
    let normalEvents = 0;
    let falsePositives = 0;
    
    allHistoryData.forEach(item => {
        if (item.result.threat_detected) {
            threatEvents++;
            // Simple heuristic for false positives (low confidence threats)
            if (item.result.confidence < 0.6) {
                falsePositives++;
            }
        } else {
            normalEvents++;
        }
    });
    
    // Update stat elements
    document.getElementById('totalEvents').textContent = totalEvents.toLocaleString();
    document.getElementById('threatEvents').textContent = threatEvents.toLocaleString();
    document.getElementById('normalEvents').textContent = normalEvents.toLocaleString();
    document.getElementById('falsePositives').textContent = falsePositives.toLocaleString();
}

// Render history table
function renderHistoryTable() {
    const tableBody = document.getElementById('historyTableBody');
    const noDataElement = document.getElementById('noData');
    
    // Clear existing rows
    tableBody.innerHTML = '';
    
    if (allHistoryData.length === 0) {
        tableBody.style.display = 'none';
        noDataElement.style.display = 'block';
        return;
    }
    
    tableBody.style.display = 'table-row-group';
    noDataElement.style.display = 'none';
    
    // Add rows for each history item
    allHistoryData.forEach(item => {
        const row = createHistoryRow(item);
        tableBody.appendChild(row);
    });
}

// Create a history table row
function createHistoryRow(historyItem) {
    const row = document.createElement('tr');
    const result = historyItem.result;
    
    // Determine status and styling
    const isThreat = result.threat_detected;
    const statusClass = isThreat ? 'status-threat' : 'status-normal';
    const statusText = isThreat ? 'THREAT' : 'NORMAL';
    
    // Format confidence as percentage bar
    const confidencePercent = Math.round((result.confidence || 0) * 100);
    const confidenceBar = `
        <div class="confidence-bar">
            <div class="confidence-fill" style="width: ${confidencePercent}%"></div>
        </div>
        <small>${confidencePercent}%</small>
    `;
    
    // Format severity with appropriate class
    const severity = result.severity || 'UNKNOWN';
    const severityClass = `severity-${severity.toLowerCase()}`;
    
    row.innerHTML = `
        <td>${formatTimestamp(historyItem.timestamp)}</td>
        <td>
            <i class="fas fa-desktop"></i>
            ${historyItem.source_ip}
        </td>
        <td>
            <i class="fas fa-server"></i>
            ${historyItem.destination_ip}
        </td>
        <td>
            <span class="traffic-protocol">${historyItem.protocol?.toUpperCase() || 'N/A'}</span>
        </td>
        <td>
            <span class="status-badge ${statusClass}">${statusText}</span>
        </td>
        <td>${result.attack_type || 'Normal'}</td>
        <td>${confidenceBar}</td>
        <td>
            <span class="threat-severity ${severityClass}">${severity}</span>
        </td>
        <td>
            <button class="btn btn-secondary btn-sm" onclick="viewThreatDetails('${historyItem.timestamp}')">
                <i class="fas fa-search"></i>
            </button>
            <button class="btn btn-primary btn-sm" onclick="exportThreatData('${historyItem.timestamp}')">
                <i class="fas fa-download"></i>
            </button>
        </td>
    `;
    
    // Store the full data for details view
    row.dataset.historyData = JSON.stringify(historyItem);
    
    return row;
}

// Render pagination controls
function renderPagination() {
    const pagination = document.getElementById('pagination');
    
    if (totalPages <= 1) {
        pagination.innerHTML = '';
        return;
    }
    
    let paginationHTML = '';
    
    // Previous button
    paginationHTML += `
        <button class="btn btn-secondary" onclick="goToPage(${currentPage - 1})" ${currentPage === 1 ? 'disabled' : ''}>
            <i class="fas fa-chevron-left"></i> Previous
        </button>
    `;
    
    // Page numbers
    const startPage = Math.max(1, currentPage - 2);
    const endPage = Math.min(totalPages, currentPage + 2);
    
    for (let i = startPage; i <= endPage; i++) {
        if (i === currentPage) {
            paginationHTML += `<button class="btn btn-primary" disabled>${i}</button>`;
        } else {
            paginationHTML += `<button class="btn btn-secondary" onclick="goToPage(${i})">${i}</button>`;
        }
    }
    
    // Next button
    paginationHTML += `
        <button class="btn btn-secondary" onclick="goToPage(${currentPage + 1})" ${currentPage === totalPages ? 'disabled' : ''}>
            Next <i class="fas fa-chevron-right"></i>
        </button>
    `;
    
    // Page info
    paginationHTML += `
        <span class="pagination-info">
            Page ${currentPage} of ${totalPages}
        </span>
    `;
    
    pagination.innerHTML = paginationHTML;
}

// Navigate to specific page
function goToPage(page) {
    if (page < 1 || page > totalPages) return;
    
    currentPage = page;
    loadHistory();
    
    // Scroll to top of table
    document.getElementById('historyTable').scrollIntoView({ behavior: 'smooth' });
}

// View threat details in modal
function viewThreatDetails(timestamp) {
    const historyItem = allHistoryData.find(item => item.timestamp === timestamp);
    
    if (!historyItem) {
        alert('Threat details not found');
        return;
    }
    
    const threatDetails = document.getElementById('threatDetails');
    const result = historyItem.result;
    
    let detailsHTML = `
        <div class="threat-detail-section">
            <h3>Basic Information</h3>
            <div class="detail-grid">
                <div class="detail-item">
                    <label>Timestamp:</label>
                    <span>${formatTimestamp(historyItem.timestamp)}</span>
                </div>
                <div class="detail-item">
                    <label>Source IP:</label>
                    <span>${historyItem.source_ip}</span>
                </div>
                <div class="detail-item">
                    <label>Destination IP:</label>
                    <span>${historyItem.destination_ip}</span>
                </div>
                <div class="detail-item">
                    <label>Protocol:</label>
                    <span>${historyItem.protocol || 'N/A'}</span>
                </div>
            </div>
        </div>
        
        <div class="threat-detail-section">
            <h3>Threat Analysis</h3>
            <div class="detail-grid">
                <div class="detail-item">
                    <label>Threat Detected:</label>
                    <span class="${result.threat_detected ? 'status-threat' : 'status-normal'}">
                        ${result.threat_detected ? 'YES' : 'NO'}
                    </span>
                </div>
                <div class="detail-item">
                    <label>Attack Type:</label>
                    <span>${result.attack_type || 'Normal'}</span>
                </div>
                <div class="detail-item">
                    <label>Confidence:</label>
                    <span>${formatConfidence(result.confidence)}</span>
                </div>
                <div class="detail-item">
                    <label>Severity:</label>
                    <span class="threat-severity severity-${(result.severity || 'LOW').toLowerCase()}">
                        ${result.severity || 'LOW'}
                    </span>
                </div>
            </div>
        </div>
    `;
    
    // Add recommended action if available
    if (result.recommended_action) {
        detailsHTML += `
            <div class="threat-detail-section">
                <h3>Recommended Action</h3>
                <div class="action-recommendation">
                    <i class="fas fa-shield-alt"></i>
                    <span>${result.recommended_action}</span>
                </div>
            </div>
        `;
    }
    
    // Add TRM reasoning path if available
    if (result.refinement_path && result.refinement_path.length > 0) {
        detailsHTML += `
            <div class="threat-detail-section">
                <h3><i class="fas fa-brain"></i> TRM Reasoning Process</h3>
                <div class="reasoning-path">
        `;
        
        result.refinement_path.forEach(step => {
            detailsHTML += `
                <div class="reasoning-step">
                    <div class="step-header">
                        <span class="step-number">Step ${step.step}</span>
                        <span class="step-confidence">${formatConfidence(step.confidence)}</span>
                    </div>
                    <div class="step-prediction">
                        <strong>Prediction:</strong> ${step.predicted_attack}
                    </div>
                </div>
            `;
        });
        
        // Add final decision
        detailsHTML += `
                <div class="reasoning-step final">
                    <div class="step-header">
                        <span class="step-number">🎯 Final Decision</span>
                        <span class="step-confidence">${formatConfidence(result.confidence)}</span>
                    </div>
                    <div class="step-prediction">
                        <strong>Attack Type:</strong> ${result.attack_type}<br>
                        <strong>Model Used:</strong> ${result.model_used}
                    </div>
                </div>
            </div>
        </div>
        `;
    }
    
    // Add raw data section for advanced users
    detailsHTML += `
        <div class="threat-detail-section">
            <h3>Raw Data</h3>
            <div class="raw-data">
                <pre><code>${JSON.stringify(historyItem, null, 2)}</code></pre>
            </div>
        </div>
    `;
    
    threatDetails.innerHTML = detailsHTML;
    document.getElementById('threatModal').style.display = 'block';
}

// Export threat data as JSON
function exportThreatData(timestamp) {
    const historyItem = allHistoryData.find(item => item.timestamp === timestamp);
    
    if (!historyItem) {
        alert('Threat data not found');
        return;
    }
    
    const dataStr = JSON.stringify(historyItem, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `threat-${timestamp.replace(/[:.]/g, '-')}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    
    // Show success message
    showNotification('Threat data exported successfully', 'success');
}

// Export all history
async function exportHistory() {
    try {
        // Get all history data (you might want to implement a separate endpoint for this)
        const response = await fetch('/api/history?page=1&per_page=1000');
        const data = await response.json();
        
        const exportData = {
            export_timestamp: new Date().toISOString(),
            total_detections: data.total_detections,
            history: data.history
        };
        
        const dataStr = JSON.stringify(exportData, null, 2);
        const dataBlob = new Blob([dataStr], { type: 'application/json' });
        
        const url = URL.createObjectURL(dataBlob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `cyber-sentinel-history-${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
        
        showNotification('History exported successfully', 'success');
        
    } catch (error) {
        console.error('Error exporting history:', error);
        showNotification('Failed to export history', 'error');
    }
}

// Show loading indicator
function showLoading(show) {
    const loadingIndicator = document.getElementById('loadingIndicator');
    const historyTableBody = document.getElementById('historyTableBody');
    const noData = document.getElementById('noData');
    
    if (show) {
        loadingIndicator.style.display = 'flex';
        historyTableBody.style.display = 'none';
        noData.style.display = 'none';
    } else {
        loadingIndicator.style.display = 'none';
    }
}

// Show error message
function showError(message) {
    const historyTableBody = document.getElementById('historyTableBody');
    const noData = document.getElementById('noData');
    
    historyTableBody.style.display = 'none';
    noData.style.display = 'block';
    noData.innerHTML = `
        <i class="fas fa-exclamation-triangle"></i>
        <p>${message}</p>
        <button class="btn btn-primary" onclick="loadHistory()">
            <i class="fas fa-redo"></i> Try Again
        </button>
    `;
}

// Show notification
function showNotification(message, type = 'info') {
    // Remove existing notification
    const existingNotification = document.querySelector('.notification');
    if (existingNotification) {
        existingNotification.remove();
    }
    
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <span>${message}</span>
        <button onclick="this.parentElement.remove()">&times;</button>
    `;
    
    // Add styles if not already added
    if (!document.querySelector('#notification-styles')) {
        const styles = document.createElement('style');
        styles.id = 'notification-styles';
        styles.textContent = `
            .notification {
                position: fixed;
                top: 20px;
                right: 20px;
                padding: 15px 20px;
                border-radius: 8px;
                color: white;
                z-index: 10000;
                display: flex;
                align-items: center;
                gap: 10px;
                max-width: 400px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                animation: slideIn 0.3s ease;
            }
            .notification-success { background: linear-gradient(135deg, #00b894, #00a085); }
            .notification-error { background: linear-gradient(135deg, #ff7675, #e84393); }
            .notification-info { background: linear-gradient(135deg, #74b9ff, #0984e3); }
            .notification button {
                background: none;
                border: none;
                color: white;
                font-size: 18px;
                cursor: pointer;
                padding: 0;
                width: 20px;
                height: 20px;
            }
            @keyframes slideIn {
                from { transform: translateX(100%); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
        `;
        document.head.appendChild(styles);
    }
    
    document.body.appendChild(notification);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (notification.parentElement) {
            notification.remove();
        }
    }, 5000);
}

// Utility function to format timestamp for display
function formatTimestamp(timestamp) {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    
    if (diffMins < 1) {
        return 'Just now';
    } else if (diffMins < 60) {
        return `${diffMins}m ago`;
    } else if (diffHours < 24) {
        return `${diffHours}h ago`;
    } else if (diffDays < 7) {
        return `${diffDays}d ago`;
    } else {
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }
}

// Close modal function for history page
function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

// Add CSS for history page specific styles
const historyStyles = `
    .btn-sm {
        padding: 6px 12px;
        font-size: 0.8rem;
    }
    
    .threat-detail-section {
        margin-bottom: 25px;
        padding-bottom: 20px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .threat-detail-section:last-child {
        border-bottom: none;
    }
    
    .threat-detail-section h3 {
        margin-bottom: 15px;
        color: #00d4ff;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    .detail-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 15px;
    }
    
    .detail-item {
        display: flex;
        justify-content: space-between;
        padding: 10px;
        background: rgba(255, 255, 255, 0.05);
        border-radius: 6px;
    }
    
    .detail-item label {
        font-weight: bold;
        color: #cccccc;
    }
    
    .action-recommendation {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 15px;
        background: rgba(0, 212, 255, 0.1);
        border-radius: 8px;
        border-left: 4px solid #00d4ff;
    }
    
    .action-recommendation i {
        color: #00d4ff;
        font-size: 1.2rem;
    }
    
    .reasoning-path {
        display: flex;
        flex-direction: column;
        gap: 10px;
    }
    
    .reasoning-step {
        background: rgba(255, 255, 255, 0.05);
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #00d4ff;
    }
    
    .reasoning-step.final {
        background: rgba(0, 212, 255, 0.1);
        border-left-color: #00ff88;
    }
    
    .step-header {
        display: flex;
        justify-content: space-between;
        margin-bottom: 8px;
    }
    
    .step-number {
        font-weight: bold;
        color: #00d4ff;
    }
    
    .step-confidence {
        color: #cccccc;
        font-size: 0.9rem;
    }
    
    .step-prediction {
        font-size: 0.9rem;
        color: #cccccc;
    }
    
    .raw-data {
        background: rgba(0, 0, 0, 0.3);
        border-radius: 6px;
        padding: 15px;
        max-height: 300px;
        overflow: auto;
    }
    
    .raw-data pre {
        margin: 0;
        font-size: 0.8rem;
        color: #cccccc;
    }
    
    @media (max-width: 768px) {
        .detail-grid {
            grid-template-columns: 1fr;
        }
        
        .detail-item {
            flex-direction: column;
            gap: 5px;
        }
    }
`;

// Inject styles into the page
if (!document.querySelector('#history-styles')) {
    const styleElement = document.createElement('style');
    styleElement.id = 'history-styles';
    styleElement.textContent = historyStyles;
    document.head.appendChild(styleElement);
}