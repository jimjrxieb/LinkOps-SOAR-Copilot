// Whis Frontend - Core JavaScript functionality
class WhisInterface {
    constructor() {
        this.socket = null;
        this.currentConversationId = null;
        this.isConnected = false;
        this.messageQueue = [];
        this.conversationHistory = [];
    }
    
    // Initialize the interface
    static init() {
        if (!window.whisInterface) {
            window.whisInterface = new WhisInterface();
        }
        return window.whisInterface.initialize();
    }
    
    initialize() {
        console.log('🤖 Initializing Whis Interface...');
        
        this.setupSocketConnection();
        this.setupEventListeners();
        this.loadStoredConversations();
        this.checkSystemStatus();
        
        return this;
    }
    
    // Socket.IO connection management
    setupSocketConnection() {
        if (typeof io === 'undefined') {
            console.error('Socket.IO not loaded');
            return;
        }
        
        this.socket = io();
        
        this.socket.on('connect', () => {
            console.log('✅ Connected to Whis backend');
            this.isConnected = true;
            this.updateConnectionStatus(true);
            this.processMessageQueue();
        });
        
        this.socket.on('disconnect', () => {
            console.log('❌ Disconnected from Whis backend');
            this.isConnected = false;
            this.updateConnectionStatus(false);
        });
        
        this.socket.on('status', (data) => {
            console.log('📡 Status update:', data);
            this.showToast(data.message, 'info');
        });
        
        this.socket.on('whis_thinking', (data) => {
            this.showWhisThinking(data.conversation_id);
        });
        
        this.socket.on('whis_response', (data) => {
            this.handleWhisResponse(data);
        });
        
        this.socket.on('new_alert', (alert) => {
            this.handleNewAlert(alert);
        });
        
        this.socket.on('approval_update', (data) => {
            this.handleApprovalUpdate(data);
        });
    }
    
    // Event listeners for UI interactions
    setupEventListeners() {
        // Chat form submission
        const chatForm = document.getElementById('chat-form');
        if (chatForm) {
            chatForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.sendChatMessage();
            });
        }
        
        // Chat input enter key
        const chatInput = document.getElementById('chat-input');
        if (chatInput) {
            chatInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendChatMessage();
                }
            });
            
            // Auto-resize textarea
            chatInput.addEventListener('input', () => {
                this.autoResizeTextarea(chatInput);
            });
        }
        
        // Approval action buttons
        document.addEventListener('click', (e) => {
            if (e.target.matches('.approve-btn')) {
                const approvalId = e.target.dataset.approvalId;
                this.handleApprovalAction(approvalId, 'approve');
            } else if (e.target.matches('.reject-btn')) {
                const approvalId = e.target.dataset.approvalId;
                this.handleApprovalAction(approvalId, 'reject');
            } else if (e.target.matches('.view-details-btn')) {
                const approvalId = e.target.dataset.approvalId;
                this.showApprovalDetails(approvalId);
            }
        });
        
        // Log search and filtering
        const logSearchInput = document.getElementById('log-search');
        if (logSearchInput) {
            logSearchInput.addEventListener('input', () => {
                this.filterLogs(logSearchInput.value);
            });
        }
        
        // SIEM source toggles
        const siemToggles = document.querySelectorAll('.siem-toggle');
        siemToggles.forEach(toggle => {
            toggle.addEventListener('change', () => {
                this.toggleSiemSource(toggle.dataset.source, toggle.checked);
            });
        });
        
        // Global keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            // Ctrl+K or Cmd+K to focus chat input
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                const chatInput = document.getElementById('chat-input');
                if (chatInput) {
                    chatInput.focus();
                }
            }
            
            // Escape to close modals
            if (e.key === 'Escape') {
                this.closeModals();
            }
        });
    }
    
    // Chat functionality
    sendChatMessage() {
        const chatInput = document.getElementById('chat-input');
        const message = chatInput.value.trim();
        
        if (!message) return;
        
        // Clear input
        chatInput.value = '';
        this.autoResizeTextarea(chatInput);
        
        // Add user message to chat
        this.addMessageToChat('user', message);
        
        // Send to backend
        if (this.isConnected) {
            this.socket.emit('chat_message', { message: message });
        } else {
            this.messageQueue.push(message);
            this.showToast('Message queued - connecting to Whis...', 'warning');
        }
    }
    
    addMessageToChat(sender, content, metadata = {}) {
        const chatMessages = document.getElementById('chat-messages');
        if (!chatMessages) return;
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender} fade-in`;
        
        const timestamp = new Date().toLocaleTimeString();
        const avatar = sender === 'user' ? '👤' : '🤖';
        const avatarColor = sender === 'user' ? 'bg-info' : 'bg-success';
        
        messageDiv.innerHTML = `
            <div class="message-avatar ${avatarColor}">
                ${avatar}
            </div>
            <div class="message-content">
                <div class="message-text">${this.formatMessageContent(content, metadata)}</div>
                <div class="message-timestamp">${timestamp}</div>
                ${metadata.artifacts ? this.renderArtifacts(metadata.artifacts) : ''}
                ${metadata.actions ? this.renderActionButtons(metadata.actions) : ''}
            </div>
        `;
        
        chatMessages.appendChild(messageDiv);
        this.scrollToBottom(chatMessages);
        
        // Store in conversation history
        this.conversationHistory.push({
            sender,
            content,
            timestamp: new Date(),
            metadata
        });
        
        this.saveConversationHistory();
    }
    
    formatMessageContent(content, metadata) {
        if (typeof content === 'string') {
            // Convert URLs to links
            content = content.replace(
                /(https?:\/\/[^\s]+)/g, 
                '<a href="$1" target="_blank" rel="noopener noreferrer">$1</a>'
            );
            
            // Convert newlines to <br>
            content = content.replace(/\n/g, '<br>');
        } else if (typeof content === 'object') {
            // Handle structured responses from Whis
            if (content.explanation) {
                return `<div class="whis-explanation">${content.explanation}</div>`;
            } else if (content.error) {
                return `<div class="alert alert-danger">${content.error}</div>`;
            }
        }
        
        return content;
    }
    
    renderArtifacts(artifacts) {
        if (!Array.isArray(artifacts)) return '';
        
        let html = '<div class="message-artifacts mt-2">';
        artifacts.forEach(artifact => {
            html += `
                <div class="artifact-item">
                    <i class="fas fa-file-code"></i>
                    <span>${artifact.name}</span>
                    <button class="btn btn-sm btn-outline-primary ms-2" 
                            onclick="window.whisInterface.downloadArtifact('${artifact.id}')">
                        Download
                    </button>
                </div>
            `;
        });
        html += '</div>';
        return html;
    }
    
    renderActionButtons(actions) {
        if (!Array.isArray(actions)) return '';
        
        let html = '<div class="message-actions mt-2">';
        actions.forEach(action => {
            html += `
                <button class="btn btn-sm btn-outline-warning me-2" 
                        onclick="window.whisInterface.requestApproval('${action.id}')">
                    ${action.label}
                </button>
            `;
        });
        html += '</div>';
        return html;
    }
    
    showWhisThinking(conversationId) {
        const chatMessages = document.getElementById('chat-messages');
        if (!chatMessages) return;
        
        // Remove any existing thinking indicator
        const existingThinking = chatMessages.querySelector('.whis-thinking-message');
        if (existingThinking) {
            existingThinking.remove();
        }
        
        const thinkingDiv = document.createElement('div');
        thinkingDiv.className = 'message whis whis-thinking-message fade-in';
        thinkingDiv.innerHTML = `
            <div class="message-avatar bg-success">🤖</div>
            <div class="message-content">
                <div class="whis-thinking">
                    <div class="loading-spinner"></div>
                    Whis is analyzing...
                </div>
            </div>
        `;
        
        chatMessages.appendChild(thinkingDiv);
        this.scrollToBottom(chatMessages);
    }
    
    handleWhisResponse(data) {
        // Remove thinking indicator
        const thinkingMessage = document.querySelector('.whis-thinking-message');
        if (thinkingMessage) {
            thinkingMessage.remove();
        }
        
        // Add Whis response
        this.addMessageToChat('whis', data.response, {
            conversationId: data.conversation_id,
            artifacts: data.response.artifacts,
            actions: data.response.how
        });
        
        this.currentConversationId = data.conversation_id;
    }
    
    // Approval system
    handleApprovalAction(approvalId, action) {
        const confirmation = action === 'approve' 
            ? 'Are you sure you want to approve this action?' 
            : 'Are you sure you want to reject this action?';
            
        if (!confirm(confirmation)) return;
        
        fetch('/api/approve_action', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                approval_id: approvalId,
                action: action
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                this.showToast(`Action ${action}d successfully`, 'success');
                this.updateApprovalStatus(approvalId, action + 'd');
            } else {
                this.showToast('Failed to process approval', 'error');
            }
        })
        .catch(error => {
            console.error('Approval error:', error);
            this.showToast('Network error occurred', 'error');
        });
    }
    
    updateApprovalStatus(approvalId, status) {
        const approvalCard = document.querySelector(`[data-approval-id="${approvalId}"]`);
        if (approvalCard) {
            const statusBadge = approvalCard.querySelector('.approval-status');
            if (statusBadge) {
                statusBadge.textContent = status;
                statusBadge.className = `badge ${this.getStatusBadgeClass(status)}`;
            }
            
            // Disable action buttons
            const actionButtons = approvalCard.querySelectorAll('.approve-btn, .reject-btn');
            actionButtons.forEach(btn => {
                btn.disabled = true;
                btn.classList.add('disabled');
            });
        }
    }
    
    getStatusBadgeClass(status) {
        switch (status) {
            case 'approved': return 'bg-success';
            case 'rejected': return 'bg-danger';
            case 'pending': return 'bg-warning';
            default: return 'bg-secondary';
        }
    }
    
    showApprovalDetails(approvalId) {
        // Implementation for showing detailed approval information
        const modal = document.getElementById('approval-details-modal');
        if (modal) {
            // Load approval details and show modal
            this.loadApprovalDetails(approvalId).then(details => {
                this.populateApprovalModal(details);
                const bsModal = new bootstrap.Modal(modal);
                bsModal.show();
            });
        }
    }
    
    async loadApprovalDetails(approvalId) {
        try {
            const response = await fetch(`/api/approval/${approvalId}`);
            return await response.json();
        } catch (error) {
            console.error('Failed to load approval details:', error);
            return null;
        }
    }
    
    // SIEM log management
    loadSiemLogs(source = 'all', query = '', timeRange = '24h') {
        const endpoint = source === 'limacharlie' 
            ? '/api/limacharlie/detections'
            : source === 'splunk'
            ? '/api/splunk/search'
            : '/api/logs';
            
        const params = new URLSearchParams({
            query: query,
            time_range: timeRange,
            limit: 100
        });
        
        fetch(`${endpoint}?${params}`)
            .then(response => response.json())
            .then(data => {
                this.displaySiemLogs(data, source);
            })
            .catch(error => {
                console.error('Failed to load SIEM logs:', error);
                this.showToast('Failed to load SIEM logs', 'error');
            });
    }
    
    displaySiemLogs(logs, source) {
        const logContainer = document.getElementById('siem-logs');
        if (!logContainer) return;
        
        logContainer.innerHTML = '';
        
        if (!logs || (Array.isArray(logs) && logs.length === 0)) {
            logContainer.innerHTML = '<div class="text-center text-muted p-4">No logs found</div>';
            return;
        }
        
        const logEntries = Array.isArray(logs) ? logs : logs.events || logs.results || [logs];
        
        logEntries.forEach(log => {
            const logDiv = document.createElement('div');
            logDiv.className = `log-entry ${log.severity || 'info'} p-3`;
            logDiv.innerHTML = this.formatLogEntry(log, source);
            logContainer.appendChild(logDiv);
        });
    }
    
    formatLogEntry(log, source) {
        const timestamp = new Date(log.timestamp || log._time || Date.now()).toLocaleString();
        const severity = log.severity || log.urgency || 'info';
        const message = log.message || log.description || log._raw || 'No message available';
        
        return `
            <div class="d-flex justify-content-between align-items-start">
                <div class="flex-grow-1">
                    <div class="d-flex align-items-center mb-2">
                        <span class="log-source">${source}</span>
                        <span class="log-timestamp ms-2">${timestamp}</span>
                        <span class="badge bg-${this.getSeverityColor(severity)} ms-auto">${severity}</span>
                    </div>
                    <div class="log-message">${message}</div>
                    ${log.details ? `<div class="log-details">${JSON.stringify(log.details, null, 2)}</div>` : ''}
                </div>
                <div class="log-actions">
                    <button class="btn btn-sm btn-outline-primary" onclick="window.whisInterface.analyzeLogWithWhis('${log.id || Math.random()}')">
                        <i class="fas fa-robot"></i> Analyze
                    </button>
                </div>
            </div>
        `;
    }
    
    getSeverityColor(severity) {
        switch (severity?.toLowerCase()) {
            case 'high': case 'critical': return 'danger';
            case 'medium': case 'warning': return 'warning';
            case 'low': return 'info';
            default: return 'secondary';
        }
    }
    
    filterLogs(searchTerm) {
        const logEntries = document.querySelectorAll('.log-entry');
        
        logEntries.forEach(entry => {
            const text = entry.textContent.toLowerCase();
            const matches = text.includes(searchTerm.toLowerCase());
            entry.style.display = matches ? 'block' : 'none';
        });
    }
    
    toggleSiemSource(source, enabled) {
        if (enabled) {
            this.loadSiemLogs(source);
        } else {
            // Hide logs from this source
            const sourceElements = document.querySelectorAll(`.log-source:contains("${source}")`);
            sourceElements.forEach(el => {
                el.closest('.log-entry').style.display = 'none';
            });
        }
    }
    
    analyzeLogWithWhis(logId) {
        const logEntry = document.querySelector(`[data-log-id="${logId}"]`);
        if (logEntry) {
            const logData = this.extractLogData(logEntry);
            const message = `Analyze this log entry: ${JSON.stringify(logData)}`;
            
            // Switch to chat tab and send message
            const chatTab = document.querySelector('a[href="/chat"]');
            if (chatTab) {
                chatTab.click();
                
                setTimeout(() => {
                    const chatInput = document.getElementById('chat-input');
                    if (chatInput) {
                        chatInput.value = message;
                        this.sendChatMessage();
                    }
                }, 500);
            }
        }
    }
    
    // Utility functions
    autoResizeTextarea(textarea) {
        textarea.style.height = 'auto';
        textarea.style.height = textarea.scrollHeight + 'px';
    }
    
    scrollToBottom(container) {
        container.scrollTop = container.scrollHeight;
    }
    
    updateConnectionStatus(connected) {
        const statusIndicators = document.querySelectorAll('.connection-status');
        statusIndicators.forEach(indicator => {
            indicator.className = `connection-status ${connected ? 'status-online' : 'status-offline'}`;
            indicator.textContent = connected ? 'Connected' : 'Disconnected';
        });
    }
    
    processMessageQueue() {
        while (this.messageQueue.length > 0) {
            const message = this.messageQueue.shift();
            this.socket.emit('chat_message', { message: message });
        }
    }
    
    saveConversationHistory() {
        try {
            localStorage.setItem('whis_conversation_history', JSON.stringify(this.conversationHistory));
        } catch (error) {
            console.warn('Failed to save conversation history:', error);
        }
    }
    
    loadStoredConversations() {
        try {
            const stored = localStorage.getItem('whis_conversation_history');
            if (stored) {
                this.conversationHistory = JSON.parse(stored);
                this.restoreConversationUI();
            }
        } catch (error) {
            console.warn('Failed to load conversation history:', error);
        }
    }
    
    restoreConversationUI() {
        const chatMessages = document.getElementById('chat-messages');
        if (!chatMessages || this.conversationHistory.length === 0) return;
        
        // Show only recent messages (last 20)
        const recentMessages = this.conversationHistory.slice(-20);
        
        recentMessages.forEach(msg => {
            this.addMessageToChat(msg.sender, msg.content, msg.metadata || {});
        });
    }
    
    closeModals() {
        const modals = document.querySelectorAll('.modal.show');
        modals.forEach(modal => {
            const bsModal = bootstrap.Modal.getInstance(modal);
            if (bsModal) {
                bsModal.hide();
            }
        });
    }
    
    checkSystemStatus() {
        fetch('/api/status')
            .then(response => response.json())
            .then(status => {
                console.log('System status:', status);
                this.updateSystemStatus(status);
            })
            .catch(error => {
                console.warn('Status check failed:', error);
            });
    }
    
    updateSystemStatus(status) {
        // Update various status indicators in the UI
        const statusElements = document.querySelectorAll('.system-status');
        statusElements.forEach(element => {
            element.dataset.status = status.overall || 'unknown';
        });
    }
    
    // Public API methods
    static showToast(message, type = 'info', duration = 3000) {
        const toast = document.getElementById('status-toast');
        const toastBody = document.getElementById('status-message');
        
        if (!toast || !toastBody) {
            console.log(`Toast: ${message}`);
            return;
        }
        
        // Update content and styling
        toastBody.textContent = message;
        toast.className = `toast align-items-center text-white border-0 ${this.getToastClass(type)}`;
        
        // Show toast
        const bsToast = new bootstrap.Toast(toast, { delay: duration });
        bsToast.show();
    }
    
    static getToastClass(type) {
        switch (type) {
            case 'success': return 'bg-success';
            case 'error': case 'danger': return 'bg-danger';
            case 'warning': return 'bg-warning';
            case 'info': return 'bg-info';
            default: return 'bg-primary';
        }
    }
    
    // Artifact management
    downloadArtifact(artifactId) {
        window.open(`/api/artifact/${artifactId}/download`, '_blank');
    }
    
    requestApproval(actionId) {
        this.showToast('Approval request sent', 'info');
        // Navigate to approvals page or show modal
        window.location.href = '/approvals';
    }
    
    // Alert handling
    handleNewAlert(alert) {
        this.showToast(`New ${alert.severity} alert: ${alert.message}`, alert.severity);
        
        // Update dashboard counters if on dashboard
        if (window.location.pathname === '/') {
            this.updateDashboardMetrics();
        }
    }
    
    handleApprovalUpdate(data) {
        this.updateApprovalStatus(data.approval_id, data.status);
        this.showToast(`Approval ${data.status}`, 'success');
    }
    
    updateDashboardMetrics() {
        // Refresh dashboard metrics
        if (typeof updateMetrics === 'function') {
            updateMetrics();
        }
    }
}

// Make WhisInterface globally available
window.WhisInterface = WhisInterface;

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', WhisInterface.init);
} else {
    WhisInterface.init();
}