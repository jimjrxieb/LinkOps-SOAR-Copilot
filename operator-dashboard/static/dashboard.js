// Whis SOAR-Copilot Dashboard JavaScript

class WhisDashboard {
    constructor() {
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.init();
    }

    init() {
        this.connectWebSocket();
        this.loadInitialData();
        this.setupEventHandlers();
        
        // Refresh data every 30 seconds as fallback
        setInterval(() => this.loadDashboardStats(), 30000);
    }

    connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;
        
        try {
            this.ws = new WebSocket(wsUrl);
            
            this.ws.onopen = () => {
                console.log('🔗 WebSocket connected');
                this.reconnectAttempts = 0;
                this.updateConnectionStatus(true);
            };
            
            this.ws.onmessage = (event) => {
                const message = JSON.parse(event.data);
                this.handleWebSocketMessage(message);
            };
            
            this.ws.onclose = () => {
                console.log('❌ WebSocket disconnected');
                this.updateConnectionStatus(false);
                this.attemptReconnect();
            };
            
            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.updateConnectionStatus(false);
            };
            
        } catch (error) {
            console.error('Failed to connect WebSocket:', error);
            this.updateConnectionStatus(false);
        }
    }

    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
            
            console.log(`🔄 Reconnecting in ${delay/1000}s... (attempt ${this.reconnectAttempts})`);
            
            setTimeout(() => {
                this.connectWebSocket();
            }, delay);
        }
    }

    handleWebSocketMessage(message) {
        console.log('📨 WebSocket message:', message.type);
        
        switch (message.type) {
            case 'stats_update':
                this.updateDashboardStats(message.data);
                break;
            case 'new_incident':
                this.addNewIncident(message.data);
                this.showNotification('🚨 New Incident', message.data.title, 'warning');
                break;
            case 'approval_decision':
                this.updateApproval(message.data);
                break;
            case 'training_update':
                this.updateTrainingStatus(message.data);
                this.showNotification('🔄 Training Update', 'New training data generated', 'info');
                break;
            case 'retraining_started':
                this.showNotification('🚀 Retraining Started', 'Model retraining in progress', 'info');
                break;
        }
    }

    updateConnectionStatus(connected) {
        const statusDot = document.querySelector('.status-dot');
        const statusText = document.querySelector('.nav-status span:last-child');
        
        if (connected) {
            statusDot.className = 'status-dot online';
            statusText.textContent = 'Live';
        } else {
            statusDot.className = 'status-dot offline';
            statusText.textContent = 'Offline';
        }
    }

    async loadInitialData() {
        await Promise.all([
            this.loadDashboardStats(),
            this.loadRecentIncidents(),
            this.loadPendingApprovals(),
            this.loadTrainingStatus()
        ]);
    }

    async loadDashboardStats() {
        try {
            const response = await fetch('/api/dashboard/stats');
            const data = await response.json();
            this.updateDashboardStats(data);
        } catch (error) {
            console.error('Failed to load dashboard stats:', error);
        }
    }

    updateDashboardStats(data) {
        // Update metric cards
        this.updateElement('active-incidents', data.incidents?.active || 0);
        this.updateElement('pending-approvals', data.approvals?.pending || 0);
        this.updateElement('training-examples', data.training?.total_examples || 0);
        
        // Update attack chain stats
        this.updateChainStats(data.attack_chains);
    }

    updateChainStats(chainStats) {
        const container = document.getElementById('chain-stats');
        if (!container || !chainStats) return;

        if (chainStats.message) {
            container.innerHTML = `<div class="loading">${chainStats.message}</div>`;
            return;
        }

        container.innerHTML = `
            <div class="chain-stat">
                <span class="chain-stat-value">${chainStats.total_chains || 0}</span>
                <span class="chain-stat-label">Attack Chains</span>
            </div>
            <div class="chain-stat">
                <span class="chain-stat-value">${chainStats.total_events || 0}</span>
                <span class="chain-stat-label">Total Events</span>
            </div>
            <div class="chain-stat">
                <span class="chain-stat-value">${chainStats.high_value_chains || 0}</span>
                <span class="chain-stat-label">High Value Chains</span>
            </div>
            <div class="chain-stat">
                <span class="chain-stat-value">${(chainStats.average_training_value || 0).toFixed(2)}</span>
                <span class="chain-stat-label">Avg Training Value</span>
            </div>
        `;
    }

    async loadRecentIncidents() {
        try {
            const response = await fetch('/api/incidents/recent');
            const data = await response.json();
            this.updateRecentIncidents(data.incidents);
        } catch (error) {
            console.error('Failed to load recent incidents:', error);
        }
    }

    updateRecentIncidents(incidents) {
        const container = document.getElementById('recent-incidents');
        if (!container) return;

        if (!incidents || incidents.length === 0) {
            container.innerHTML = '<div class="loading">No recent incidents</div>';
            return;
        }

        container.innerHTML = incidents.slice(0, 5).map(incident => `
            <div class="incident-item">
                <div class="incident-details">
                    <div class="incident-title">${incident.title}</div>
                    <div class="incident-meta">
                        <span>🖥️ ${incident.host}</span>
                        <span>👤 ${incident.user}</span>
                        <span>⏰ ${this.formatTime(incident.timestamp)}</span>
                    </div>
                </div>
                <div class="severity-badge severity-${incident.severity}">
                    ${incident.severity}
                </div>
            </div>
        `).join('');
    }

    async loadPendingApprovals() {
        try {
            const response = await fetch('/api/approvals/pending');
            const data = await response.json();
            this.updatePendingApprovals(data.approvals);
        } catch (error) {
            console.error('Failed to load pending approvals:', error);
        }
    }

    updatePendingApprovals(approvals) {
        const container = document.getElementById('pending-approvals-list');
        if (!container) return;

        if (!approvals || approvals.length === 0) {
            container.innerHTML = '<div class="loading">No pending approvals</div>';
            return;
        }

        container.innerHTML = approvals.slice(0, 5).map(approval => `
            <div class="approval-item">
                <div class="approval-details">
                    <div class="approval-title">${approval.title}</div>
                    <div class="approval-meta">
                        <span>📝 ${approval.description}</span>
                        <span>⏰ ${this.formatTime(approval.created_at)}</span>
                    </div>
                </div>
                <div class="severity-badge severity-${approval.severity}">
                    ${approval.status}
                </div>
            </div>
        `).join('');
    }

    async loadTrainingStatus() {
        try {
            const response = await fetch('/api/training/status');
            const data = await response.json();
            this.updateTrainingStatusDisplay(data);
        } catch (error) {
            console.error('Failed to load training status:', error);
        }
    }

    updateTrainingStatusDisplay(data) {
        this.updateElement('chains-ready', data.attack_chains_ready || 0);
        this.updateElement('model-version', data.model_version || 'unknown');
        this.updateElement('quality-score', data.quality_score || 0);
    }

    addNewIncident(incident) {
        // Add to recent incidents list
        const container = document.getElementById('recent-incidents');
        if (!container) return;

        const incidentHtml = `
            <div class="incident-item" style="animation: slideIn 0.3s ease-out;">
                <div class="incident-details">
                    <div class="incident-title">${incident.title}</div>
                    <div class="incident-meta">
                        <span>🖥️ ${incident.host}</span>
                        <span>👤 ${incident.user}</span>
                        <span>⏰ ${this.formatTime(incident.timestamp)}</span>
                    </div>
                </div>
                <div class="severity-badge severity-${incident.severity}">
                    ${incident.severity}
                </div>
            </div>
        `;

        container.insertAdjacentHTML('afterbegin', incidentHtml);

        // Keep only the most recent 5 incidents
        const items = container.querySelectorAll('.incident-item');
        if (items.length > 5) {
            items[items.length - 1].remove();
        }

        // Update counter
        const activeIncidents = document.getElementById('active-incidents');
        if (activeIncidents) {
            const current = parseInt(activeIncidents.textContent) || 0;
            activeIncidents.textContent = current + 1;
        }
    }

    updateElement(id, value) {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
        }
    }

    formatTime(timestamp) {
        try {
            const date = new Date(timestamp);
            const now = new Date();
            const diff = now - date;

            if (diff < 60000) { // Less than 1 minute
                return 'Just now';
            } else if (diff < 3600000) { // Less than 1 hour
                return `${Math.floor(diff / 60000)}m ago`;
            } else if (diff < 86400000) { // Less than 1 day
                return `${Math.floor(diff / 3600000)}h ago`;
            } else {
                return date.toLocaleDateString();
            }
        } catch (error) {
            return 'Unknown';
        }
    }

    showNotification(title, message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <div class="notification-title">${title}</div>
                <div class="notification-message">${message}</div>
            </div>
            <button class="notification-close" onclick="this.parentElement.remove()">×</button>
        `;

        // Add to page
        document.body.appendChild(notification);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 5000);
    }

    setupEventHandlers() {
        // Add any additional event handlers here
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden && (!this.ws || this.ws.readyState !== WebSocket.OPEN)) {
                this.connectWebSocket();
            }
        });
    }
}

// Global functions for button actions
window.generateTrainingData = async function() {
    try {
        const response = await fetch('/api/training/generate', { method: 'POST' });
        const result = await response.json();
        
        if (result.error) {
            dashboard.showNotification('❌ Error', result.error, 'error');
        } else {
            dashboard.showNotification('✅ Success', `Generated ${result.training_examples_generated} training examples`, 'success');
        }
    } catch (error) {
        dashboard.showNotification('❌ Error', 'Failed to generate training data', 'error');
    }
};

window.triggerRetraining = async function() {
    try {
        const response = await fetch('/api/training/retrain', { method: 'POST' });
        const result = await response.json();
        
        if (result.error) {
            dashboard.showNotification('❌ Error', result.error, 'error');
        } else {
            dashboard.showNotification('🚀 Retraining Started', 'Model retraining prepared - check logs', 'success');
        }
    } catch (error) {
        dashboard.showNotification('❌ Error', 'Failed to trigger retraining', 'error');
    }
};

// Initialize dashboard when page loads
let dashboard;
document.addEventListener('DOMContentLoaded', () => {
    dashboard = new WhisDashboard();
});

// Add notification styles
const notificationStyles = `
<style>
.notification {
    position: fixed;
    top: 20px;
    right: 20px;
    background: var(--surface-color);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    padding: 1rem;
    display: flex;
    align-items: flex-start;
    gap: 1rem;
    max-width: 400px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
    z-index: 1000;
    animation: slideInRight 0.3s ease-out;
}

.notification-success { border-left: 4px solid var(--success-color); }
.notification-error { border-left: 4px solid var(--danger-color); }
.notification-warning { border-left: 4px solid var(--warning-color); }
.notification-info { border-left: 4px solid var(--primary-color); }

.notification-content {
    flex: 1;
}

.notification-title {
    font-weight: 600;
    margin-bottom: 0.25rem;
    color: var(--text-primary);
}

.notification-message {
    font-size: 0.9rem;
    color: var(--text-secondary);
}

.notification-close {
    background: none;
    border: none;
    color: var(--text-secondary);
    cursor: pointer;
    font-size: 1.2rem;
    padding: 0;
    width: 20px;
    height: 20px;
}

@keyframes slideInRight {
    from { transform: translateX(100%); opacity: 0; }
    to { transform: translateX(0); opacity: 1; }
}
</style>
`;

document.head.insertAdjacentHTML('beforeend', notificationStyles);