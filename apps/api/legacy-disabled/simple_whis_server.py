#!/usr/bin/env python3
"""
Simple WHIS Server for Demo
"""
import json
import os
import sys
from datetime import datetime
from typing import Dict, Any, List
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn
import hashlib

# Add soar-platform to path for imports
sys.path.append('soar-platform')

# Import knowledge gaps pipeline
try:
    from knowledge_gaps.data_lake import log_knowledge_gap
    from knowledge_gaps.schemas import AbstainReason, IntentCategory
    KNOWLEDGE_GAPS_AVAILABLE = True
except ImportError as e:
    print(f"Knowledge gaps pipeline not available: {e}")
    KNOWLEDGE_GAPS_AVAILABLE = False

# Mock data for demo
MOCK_INCIDENTS = [
    {
        "id": "INC-001",
        "title": "Suspicious PowerShell Activity Detected",
        "severity": "HIGH",
        "status": "INVESTIGATING",
        "timestamp": "2025-01-24T16:30:00Z",
        "indicators": ["powershell.exe", "base64 encoded commands"]
    },
    {
        "id": "INC-002", 
        "title": "Potential Lateral Movement",
        "severity": "CRITICAL",
        "status": "CONTAINED",
        "timestamp": "2025-01-24T15:45:00Z",
        "indicators": ["psexec.exe", "192.168.1.100"]
    }
]

class ChatRequest(BaseModel):
    message: str
    use_rag: bool = True
    max_tokens: int = 500

class TrainingQueueItem(BaseModel):
    question: str
    context: str
    timestamp: str
    confidence_score: float
    question_hash: str
    user_session: str = "anonymous"

class WhisServer:
    def __init__(self):
        self.app = FastAPI(
            title="WHIS SOAR Copilot",
            description="AI-Powered Security Operations",
            version="1.0.0"
        )
        self.training_queue_file = "training_queue.jsonl"
        self.confidence_threshold = 0.6  # Fallback if confidence < 60%
        self.setup_routes()
    
    def setup_routes(self):
        
        @self.app.get("/", response_class=HTMLResponse)
        async def dashboard():
            return """
<!DOCTYPE html>
<html>
<head>
    <title>🤖 WHIS SOAR Copilot</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
        .header { text-align: center; margin-bottom: 30px; }
        .chat-container { max-width: 800px; margin: 0 auto; background: white; border-radius: 12px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .chat-messages { height: 400px; overflow-y: auto; border: 1px solid #ddd; border-radius: 8px; padding: 15px; margin-bottom: 15px; background: #fafafa; }
        .message { margin-bottom: 15px; }
        .user { color: #007bff; font-weight: bold; }
        .whis { color: #28a745; font-weight: bold; }
        .input-container { display: flex; gap: 10px; }
        input { flex: 1; padding: 12px; border: 1px solid #ddd; border-radius: 6px; }
        button { padding: 12px 20px; background: #007bff; color: white; border: none; border-radius: 6px; cursor: pointer; }
        button:hover { background: #0056b3; }
        .chip { padding: 8px 12px; background: #f8f9fa; color: #495057; border: 1px solid #dee2e6; border-radius: 20px; font-size: 12px; cursor: pointer; }
        .chip:hover { background: #e9ecef; }
        .status { display: flex; gap: 20px; margin-bottom: 20px; }
        .status-item { text-align: center; padding: 10px; background: #e9ecef; border-radius: 6px; flex: 1; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🤖 WHIS SOAR Copilot</h1>
        <p>AI-Powered Security Orchestration, Automation & Response</p>
    </div>
    
    <div class="status">
        <div class="status-item">
            <strong>🟢 AI Engine</strong><br>
            <span>Ready</span>
        </div>
        <div class="status-item">
            <strong>🧠 RAG System</strong><br>
            <span>Active</span>
        </div>
        <div class="status-item">
            <strong>🔍 Active Hunts</strong><br>
            <span>3</span>
        </div>
        <div class="status-item">
            <strong>🚨 Open Incidents</strong><br>
            <span>2</span>
        </div>
        <div class="status-item">
            <strong>📝 Training Queue</strong><br>
            <span id="training-queue-count">0</span>
        </div>
    </div>
    
    <div class="chat-container">
        <div class="chat-messages" id="messages">
            <div class="message">
                <span class="whis">🤖 WHIS:</span> Hello! I'm your AI security copilot. What would you like to investigate?
            </div>
        </div>
        
        <div class="input-container">
            <input type="text" id="messageInput" placeholder="What would you like to investigate?" onkeypress="if(event.key==='Enter') sendMessage()">
            <button onclick="sendMessage()">Send</button>
        </div>
        
        <!-- Capability chips moved to UI -->
        <div style="margin-top: 10px; display: flex; gap: 8px; flex-wrap: wrap;">
            <button class="chip" onclick="sendQuickMessage('Show me current incidents')">🚨 Current Incidents</button>
            <button class="chip" onclick="sendQuickMessage('Start threat hunt for credential theft')">🎯 Hunt Credentials</button>
            <button class="chip" onclick="sendQuickMessage('Analyze suspicious network activity')">🔍 Network Analysis</button>
            <button class="chip" onclick="sendQuickMessage('Execute ransomware playbook')">📚 Ransomware Response</button>
            <button class="chip" onclick="sendQuickMessage('Show system status')">📊 System Status</button>
        </div>
    </div>

    <script>
        // Update training queue count
        async function updateTrainingQueue() {
            try {
                const response = await fetch('/training-queue');
                const data = await response.json();
                document.getElementById('training-queue-count').textContent = data.count;
            } catch (error) {
                console.error('Failed to update training queue:', error);
            }
        }
        
        function sendQuickMessage(message) {
            document.getElementById('messageInput').value = message;
            sendMessage();
        }
        
        async function sendMessage() {
            const input = document.getElementById('messageInput');
            const messages = document.getElementById('messages');
            const message = input.value.trim();
            
            if (!message) return;
            
            // Add user message
            messages.innerHTML += `<div class="message"><span class="user">👤 You:</span> ${message}</div>`;
            input.value = '';
            
            // Show thinking
            messages.innerHTML += `<div class="message" id="thinking"><span class="whis">🤖 WHIS:</span> <em>Analyzing...</em></div>`;
            messages.scrollTop = messages.scrollHeight;
            
            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message, use_rag: true })
                });
                
                const data = await response.json();
                
                // Remove thinking message
                document.getElementById('thinking').remove();
                
                // Add WHIS response with confidence indicator
                let confidenceIcon = '';
                if (data.confidence_score < 0.6) {
                    confidenceIcon = ' 🤔';
                } else if (data.confidence_score > 0.8) {
                    confidenceIcon = ' ✅';
                }
                
                messages.innerHTML += `<div class="message"><span class="whis">🤖 WHIS${confidenceIcon}:</span> ${data.response}</div>`;
                
                // Update training queue if item was added
                if (data.training_queued) {
                    updateTrainingQueue();
                }
                
            } catch (error) {
                document.getElementById('thinking').remove();
                messages.innerHTML += `<div class="message"><span class="whis">🤖 WHIS:</span> <em>Error connecting to AI engine. Please try again.</em></div>`;
            }
            
            messages.scrollTop = messages.scrollHeight;
        }
        
        // Update training queue on page load
        updateTrainingQueue();
        
        // Refresh training queue periodically
        setInterval(updateTrainingQueue, 30000);  // Every 30 seconds
    </script>
</body>
</html>
            """
        
        @self.app.get("/health")
        async def health():
            return {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "api": True,
                "rag": True,
                "retriever": True,
                "vectorstore": True,
                "ai_confidence": 0.89
            }
        
        @self.app.post("/chat")
        async def chat(request: ChatRequest):
            # Micro-intent detection for short inputs
            message = request.message.lower().strip()
            word_count = len(message.split())
            
            # Greeting/acknowledgment brevity rules
            if word_count <= 3 and any(greeting in message for greeting in ['hello', 'hi', 'hey', 'thanks', 'thank you', 'ok', 'okay']):
                if any(greeting in message for greeting in ['hello', 'hi', 'hey']):
                    return {
                        "response": "Hello! What security matter can I help you investigate?",
                        "confidence_score": 0.95,
                        "sources_used": [],
                        "timestamp": datetime.utcnow().isoformat()
                    }
                elif any(thanks in message for thanks in ['thanks', 'thank you']):
                    return {
                        "response": "You're welcome! Anything else I can analyze?",
                        "confidence_score": 0.95,
                        "sources_used": [],
                        "timestamp": datetime.utcnow().isoformat()
                    }
                elif message in ['ok', 'okay']:
                    return {
                        "response": "Ready for your next security question.",
                        "confidence_score": 0.95,
                        "sources_used": [],
                        "timestamp": datetime.utcnow().isoformat()
                    }
            
            # Content-based responses for substantial queries
            
            if "incident" in message or "alert" in message:
                response = f"""Based on our current incident database, I can see 2 active incidents:

**INC-001**: Suspicious PowerShell Activity (HIGH severity)
- Detected base64 encoded commands
- Status: Under investigation
- Recommended: Review process execution logs

**INC-002**: Potential Lateral Movement (CRITICAL severity) 
- PsExec activity detected from 192.168.1.100
- Status: Contained
- Recommended: Check for additional compromised hosts

Would you like me to dive deeper into any of these incidents?"""

            elif "threat" in message or "hunt" in message:
                response = """I'm ready to initiate threat hunting! Here are some hunting opportunities I've identified:

🎯 **Active Hunt Suggestions:**
1. **Credential Harvesting**: Unusual LSASS access patterns
2. **Command & Control**: Suspicious DNS queries to newly registered domains  
3. **Data Exfiltration**: Large file transfers during off-hours

Which threat vector would you like me to investigate? I can query our SIEM and EDR systems for relevant telemetry."""

            elif "playbook" in message or "response" in message:
                response = """I have several incident response playbooks ready:

📚 **Available Playbooks:**
- **Ransomware Response**: Immediate containment and recovery
- **Phishing Investigation**: Email analysis and user impact assessment
- **Insider Threat**: Behavioral analysis and data access review
- **APT Investigation**: Advanced persistent threat hunting

Would you like me to execute one of these playbooks? I can run them in dry-run mode first for your review."""

            elif "analyze" in message or "investigate" in message:
                response = """I'm analyzing the security landscape. Here's what I found:

🔍 **Current Analysis:**
- **Risk Score**: 7.2/10 (Elevated)
- **Top Threats**: PowerShell abuse, lateral movement attempts
- **IOCs Detected**: 15 unique indicators in last 24h
- **MITRE Techniques**: T1059 (Command Line), T1021 (Remote Services)

**Recommendations:**
1. Implement additional PowerShell logging
2. Review privileged account activity  
3. Validate network segmentation controls

Would you like me to create detailed hunting queries for any of these findings?"""

            elif "status" in message or "dashboard" in message:
                response = """📊 **WHIS System Status:**

**AI Engine**: 🟢 Operational (89% confidence)
**RAG System**: 🟢 Active (1,247 documents indexed)
**SIEM Integration**: 🟢 Connected (Splunk)
**EDR Integration**: 🟢 Connected (LimaCharlie)
**Threat Intelligence**: 🟢 Updated 2 hours ago

**Current Workload:**
- 3 active threat hunts
- 2 open incidents
- 15 IOCs under analysis
- 847 events processed (last hour)

All systems nominal. Ready for security operations!"""

            else:
                # Check if this is a complex query that might need fallback
                confidence_score = self._calculate_confidence(message)
                
                if confidence_score < self.confidence_threshold:
                    # Add to training queue and provide fallback
                    await self._add_to_training_queue(request.message, confidence_score)
                    
                    if any(keyword in message for keyword in ['splunk', 'limacharlie', 'playbook', 'mitre', 'attack']):
                        response = """I don't have enough confidence in my answer for this security-specific question. I've queued it for Jimmie's next training session to improve my knowledge.
                        
For immediate help, try asking about current incidents, system status, or general security concepts I'm more confident about."""
                    else:
                        response = """I'm not confident enough to provide a reliable answer to that question. I've sent it to Jimmie for the next training session.
                        
In the meantime, I can help with incident analysis, threat hunting guidance, or system status checks."""
                    
                    confidence_score = 0.3  # Low confidence for fallback
                else:
                    # Focused response for questions we're confident about
                    response = """I'd be happy to help with that security question. Could you be more specific about what you'd like me to investigate or analyze?"""
                    confidence_score = 0.8  # High confidence for general responses

            # Ensure confidence_score is always defined
            final_confidence = locals().get('confidence_score', 0.89)
            training_queued = final_confidence < self.confidence_threshold
            
            return {
                "response": response,
                "confidence_score": final_confidence,
                "sources_used": ["incident_db", "threat_intel", "playbook_library"] if final_confidence >= self.confidence_threshold else [],
                "timestamp": datetime.utcnow().isoformat(),
                "training_queued": training_queued
            }
        
        @self.app.get("/incidents")
        async def get_incidents():
            return {"incidents": MOCK_INCIDENTS}
        
        @self.app.get("/metrics")
        async def metrics():
            training_queue_size = self._get_training_queue_size()
            return {
                "inference_latency_ms_p95": 245,
                "rag_chunks_upserted_total": 1247,
                "eval_ragas_score": 0.89,
                "ws_connected_clients": 1,
                "active_hunts": 3,
                "open_incidents": 2,
                "training_queue_size": training_queue_size,
                "confidence_threshold": self.confidence_threshold
            }
        
        @self.app.get("/training-queue")
        async def get_training_queue():
            """Get queued training items for review"""
            try:
                if not os.path.exists(self.training_queue_file):
                    return {"queue": [], "count": 0}
                
                queue_items = []
                with open(self.training_queue_file, 'r') as f:
                    for line in f:
                        if line.strip():
                            queue_items.append(json.loads(line))
                
                return {
                    "queue": queue_items,
                    "count": len(queue_items),
                    "last_updated": datetime.utcnow().isoformat()
                }
            except Exception as e:
                return {"error": str(e), "queue": [], "count": 0}
        
        @self.app.post("/training-queue/clear")
        async def clear_training_queue():
            """Clear the training queue (after training session)"""
            try:
                if os.path.exists(self.training_queue_file):
                    # Archive instead of delete
                    archive_name = f"training_queue_archived_{int(datetime.utcnow().timestamp())}.jsonl"
                    os.rename(self.training_queue_file, archive_name)
                    return {"status": "cleared", "archived_to": archive_name}
                else:
                    return {"status": "already_empty"}
            except Exception as e:
                return {"error": str(e)}

    def _calculate_confidence(self, message: str) -> float:
        """Calculate confidence score for response capability"""
        message_lower = message.lower()
        
        # High confidence topics
        high_confidence_topics = [
            'incident', 'alert', 'status', 'dashboard', 'threat', 'hunt', 'analyze'
        ]
        
        # Low confidence topics (need integration)
        low_confidence_topics = [
            'splunk', 'limacharlie', 'playbook', 'execute', 'run', 'deploy', 
            'mitre', 'att&ck', 'technique', 'tactic', 'cite', 'source'
        ]
        
        # Very low confidence topics (need development)
        very_low_confidence_topics = [
            'playwright', 'browser', 'sandbox', 'slack', 'approval', 'rbac',
            'rollback', 'rag', 'retrieval', 'vector', 'embedding'
        ]
        
        # Check for specific technical terms that need real integration
        if any(term in message_lower for term in very_low_confidence_topics):
            return 0.2
        
        if any(term in message_lower for term in low_confidence_topics):
            return 0.4
        
        if any(term in message_lower for term in high_confidence_topics):
            return 0.8
        
        # Default confidence for general questions
        return 0.7
    
    async def _add_to_training_queue(self, question: str, confidence: float):
        """Add question to training queue using structured knowledge gaps pipeline"""
        try:
            # Use structured knowledge gaps pipeline if available
            if KNOWLEDGE_GAPS_AVAILABLE:
                # Classify abstain reason
                if confidence < 0.3:
                    reason = AbstainReason.LOW_CONFIDENCE
                elif "splunk" in question.lower() or "limacharlie" in question.lower():
                    reason = AbstainReason.TOOL_FAILURE
                elif "mitre" in question.lower() or "attack" in question.lower():
                    reason = AbstainReason.GLOSSARY_MISS
                else:
                    reason = AbstainReason.NO_RAG_HITS
                
                # Log to structured data lake with Slack notifications
                context = {
                    "tenant": "default",
                    "channel": "chat",
                    "user_id": "anonymous",
                    "session_id": None,
                    "environment": "demo",
                    "model_version": "1.0.0"
                }
                
                await log_knowledge_gap(
                    query=question,
                    confidence=confidence,
                    reason=reason,
                    context=context,
                    notify_slack=True  # Enable Slack notifications
                )
                print(f"Knowledge gap logged: {question[:50]}... (confidence: {confidence:.2f})")
                
            # Fallback to simple file-based queue
            else:
                # Create hash to avoid duplicates
                question_hash = hashlib.md5(question.lower().encode()).hexdigest()[:8]
                
                # Check if already queued
                if os.path.exists(self.training_queue_file):
                    with open(self.training_queue_file, 'r') as f:
                        for line in f:
                            if line.strip():
                                item = json.loads(line)
                                if item.get('question_hash') == question_hash:
                                    return  # Already queued
                
                # Add to queue
                queue_item = TrainingQueueItem(
                    question=question,
                    context="chat_fallback",
                    timestamp=datetime.utcnow().isoformat(),
                    confidence_score=confidence,
                    question_hash=question_hash
                )
                
                with open(self.training_queue_file, 'a') as f:
                    f.write(json.dumps(queue_item.model_dump()) + '\n')
                    
        except Exception as e:
            print(f"Error adding to training queue: {e}")
    
    def _get_training_queue_size(self) -> int:
        """Get current training queue size"""
        try:
            if not os.path.exists(self.training_queue_file):
                return 0
            
            count = 0
            with open(self.training_queue_file, 'r') as f:
                for line in f:
                    if line.strip():
                        count += 1
            return count
        except:
            return 0

def main():
    server = WhisServer()
    
    print("🚀 Starting WHIS SOAR Copilot...")
    print("🌐 Dashboard: http://localhost:8000")
    print("📚 API Docs: http://localhost:8000/docs")
    print("📝 Training Queue: http://localhost:8000/training-queue")
    print("💬 Chat with WHIS at the dashboard!")
    
    uvicorn.run(
        server.app,
        host="0.0.0.0", 
        port=8000,
        log_level="info"
    )

if __name__ == "__main__":
    main()