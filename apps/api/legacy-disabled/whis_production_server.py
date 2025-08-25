#!/usr/bin/env python3
"""
🚀 WHIS Production Server
========================
Production-ready server using the new intent router architecture

[TAG: PRODUCTION] - Clean architecture with intent routing
[TAG: RAG-INTEGRATED] - FAISS vector search integration  
[TAG: SECURITY-FIRST] - Dangerous action blocking and injection detection
"""

import json
import os
import sys
from datetime import datetime
from typing import Dict, Any, List
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import uvicorn
import yaml
from pathlib import Path

# Add paths for imports
sys.path.append('apps/api')
sys.path.append('soar-platform')

# Import our new architecture
try:
    from engines.intent_router import IntentRouter, IntentType
    INTENT_ROUTER_AVAILABLE = True
except ImportError as e:
    print(f"Intent router not available: {e}")
    INTENT_ROUTER_AVAILABLE = False

try:
    from engines.rag_retriever import get_rag_retriever
    RAG_AVAILABLE = True
except ImportError as e:
    print(f"RAG retriever not available: {e}")
    RAG_AVAILABLE = False

try:
    from knowledge_gaps.data_lake import log_knowledge_gap
    from knowledge_gaps.schemas import AbstainReason
    KNOWLEDGE_GAPS_AVAILABLE = True
except ImportError as e:
    print(f"Knowledge gaps not available: {e}")
    KNOWLEDGE_GAPS_AVAILABLE = False

class ChatRequest(BaseModel):
    message: str

class TrainingQueueItem(BaseModel):
    question: str
    context: str
    timestamp: str
    confidence_score: float
    question_hash: str

class WHISProductionServer:
    """
    Production WHIS server with intent routing and RAG integration
    
    [TAG: PRODUCTION] - Uses new architecture components
    """
    
    def __init__(self):
        self.app = FastAPI(title="WHIS SOAR Copilot - Production")
        
        # Load configuration
        self.config = self._load_config()
        self.confidence_threshold = self.config.get('response_constraints', {}).get('confidence_threshold', 0.6)
        
        # Initialize intent router
        self.intent_router = IntentRouter() if INTENT_ROUTER_AVAILABLE else None
        
        # Initialize RAG retriever
        self.rag_retriever = get_rag_retriever() if RAG_AVAILABLE else None
        
        # Load response templates
        self.templates = self._load_templates()
        
        # Training queue file
        self.training_queue_file = "training_queue.jsonl"
        
        self._setup_routes()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load WHIS configuration"""
        config_path = Path("configs/model.whis.yaml")
        if config_path.exists():
            with open(config_path) as f:
                return yaml.safe_load(f)
        return {}
    
    def _load_templates(self) -> Dict[str, str]:
        """Load response templates"""
        templates = {}
        template_dir = Path("apps/api/engines/templates")
        
        if template_dir.exists():
            for template_file in template_dir.glob("*.txt"):
                template_name = template_file.stem
                with open(template_file) as f:
                    templates[template_name] = f.read().strip()
        
        return templates
    
    def _setup_routes(self):
        """Setup FastAPI routes"""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def dashboard():
            return f"""
<!DOCTYPE html>
<html>
<head>
    <title>🤖 WHIS SOAR Copilot - Production</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', roboto, sans-serif;
            margin: 0; 
            padding: 20px; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        .container {{ 
            max-width: 800px; 
            margin: 0 auto; 
            background: white; 
            border-radius: 12px; 
            padding: 2rem;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }}
        .header {{ 
            text-align: center; 
            margin-bottom: 2rem;
        }}
        .header h1 {{
            color: #2d3748;
            margin: 0;
        }}
        .status-bar {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
            padding: 1rem;
            background: #f8f9fa;
            border-radius: 8px;
        }}
        .status-item {{
            text-align: center;
        }}
        .status-label {{
            font-size: 0.8rem;
            color: #6c757d;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .status-value {{
            font-size: 1.2rem;
            font-weight: bold;
            color: #2d3748;
        }}
        .status-good {{ color: #28a745; }}
        .status-warning {{ color: #ffc107; }}
        .status-error {{ color: #dc3545; }}
        #messages {{ 
            height: 400px; 
            border: 2px solid #e9ecef; 
            border-radius: 8px; 
            padding: 1rem; 
            overflow-y: auto; 
            background: #f8f9fa;
            margin-bottom: 1rem;
        }}
        #chatForm {{ 
            display: flex; 
            gap: 10px;
        }}
        #message {{ 
            flex: 1; 
            padding: 12px; 
            border: 2px solid #dee2e6; 
            border-radius: 6px; 
            font-size: 16px;
        }}
        #send {{ 
            padding: 12px 24px; 
            background: #007bff; 
            color: white; 
            border: none; 
            border-radius: 6px; 
            cursor: pointer; 
            font-size: 16px;
            font-weight: 600;
        }}
        #send:hover {{ background: #0056b3; }}
        #send:disabled {{ background: #6c757d; cursor: not-allowed; }}
        .message {{ 
            margin-bottom: 15px; 
            line-height: 1.4;
        }}
        .user {{ 
            color: #007bff; 
            font-weight: 600;
        }}
        .whis {{ 
            color: #28a745; 
            font-weight: 600;
        }}
        .confidence-indicator {{
            font-size: 0.9rem;
            margin-left: 5px;
        }}
        #thinking {{ 
            color: #6c757d; 
            font-style: italic;
        }}
        .debug-panel {{
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 4px;
            padding: 0.5rem;
            margin-top: 0.5rem;
            font-size: 0.8rem;
            font-family: monospace;
            color: #6c757d;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 WHIS SOAR Copilot</h1>
            <p>Production Server with Intent Routing & RAG Integration</p>
        </div>
        
        <div class="status-bar" data-testid="system-status">
            <div class="status-item">
                <div class="status-label">Intent Router</div>
                <div class="status-value status-{'good' if INTENT_ROUTER_AVAILABLE else 'error'}">
                    {'✅ Active' if INTENT_ROUTER_AVAILABLE else '❌ Offline'}
                </div>
            </div>
            <div class="status-item">
                <div class="status-label">Knowledge Gaps</div>
                <div class="status-value status-{'good' if KNOWLEDGE_GAPS_AVAILABLE else 'warning'}">
                    {'✅ Active' if KNOWLEDGE_GAPS_AVAILABLE else '⚠️ Limited'}
                </div>
            </div>
            <div class="status-item">
                <div class="status-label">RAG System</div>
                <div class="status-value status-{'good' if RAG_AVAILABLE and self.rag_retriever and self.rag_retriever.is_available() else 'error'}">
                    {'✅ Active' if RAG_AVAILABLE and self.rag_retriever and self.rag_retriever.is_available() else '❌ Offline'}
                </div>
            </div>
            <div class="status-item">
                <div class="status-label">Training Queue</div>
                <div class="status-value" id="trainingQueueSize" data-testid="training-queue-size">0</div>
            </div>
        </div>
        
        <div id="messages" data-testid="chat-messages-container">
            <div class="message">
                <span class="whis">🤖 WHIS:</span> Hello! I'm your AI security copilot using production-grade intent routing. What would you like to investigate?
            </div>
        </div>
        
        <form id="chatForm">
            <input type="text" id="message" data-testid="chat-message-input" placeholder="Ask me about security incidents, threats, or investigations..." required>
            <button type="submit" id="send" data-testid="chat-send-button">Send</button>
        </form>
    </div>
    
    <script>
        document.getElementById('chatForm').addEventListener('submit', async (e) => {{
            e.preventDefault();
            await sendMessage();
        }});
        
        async function sendMessage() {{
            const messageInput = document.getElementById('message');
            const sendButton = document.getElementById('send');
            const messages = document.getElementById('messages');
            
            const message = messageInput.value.trim();
            if (!message) return;
            
            // Show user message
            messages.innerHTML += `<div class="message"><span class="user">👤 You:</span> ${{message}}</div>`;
            
            // Show thinking indicator
            const thinkingDiv = document.createElement('div');
            thinkingDiv.id = 'thinking';
            thinkingDiv.className = 'message';
            thinkingDiv.innerHTML = '<span id="thinking" data-testid="chat-thinking-indicator">🤔 WHIS is thinking...</span>';
            messages.appendChild(thinkingDiv);
            
            // Clear input and disable send
            messageInput.value = '';
            sendButton.disabled = true;
            messages.scrollTop = messages.scrollHeight;
            
            try {{
                const response = await fetch('/chat', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{message: message}})
                }});
                
                const data = await response.json();
                
                // Remove thinking indicator
                document.getElementById('thinking').remove();
                
                // Add WHIS response with confidence and debug info
                let confidenceIcon = '';
                let confidenceClass = '';
                if (data.confidence_score >= 0.8) {{
                    confidenceIcon = ' ✅';
                    confidenceClass = 'status-good';
                }} else if (data.confidence_score >= 0.6) {{
                    confidenceIcon = ' 🟡';
                    confidenceClass = 'status-warning';
                }} else {{
                    confidenceIcon = ' 🤔';
                    confidenceClass = 'status-error';
                }}
                
                let responseHtml = `<div class="message">
                    <span class="whis" data-testid="whis-message">🤖 WHIS${{confidenceIcon}}:</span> ${{data.response}}
                `;
                
                // Add debug panel if available
                if (data.debug_info) {{
                    responseHtml += `<div class="debug-panel">
                        <strong>Debug Info:</strong><br>
                        Intent: ${{data.debug_info.intent || 'unknown'}}<br>
                        Confidence: ${{data.confidence_score?.toFixed(2) || 'N/A'}}<br>
                        Matched Patterns: ${{data.debug_info.matched_patterns?.join(', ') || 'none'}}<br>
                        Template: ${{data.debug_info.template || 'default'}}
                        ${{data.debug_info.security_flags?.length ? `<br>🚨 Security Flags: ${{data.debug_info.security_flags.join(', ')}}` : ''}}
                    </div>`;
                }}
                
                responseHtml += '</div>';
                messages.innerHTML += responseHtml;
                
                // Update training queue if item was added
                if (data.training_queued) {{
                    updateTrainingQueue();
                }}
                
            }} catch (error) {{
                document.getElementById('thinking').remove();
                messages.innerHTML += `<div class="message"><span class="whis">🤖 WHIS:</span> <em>Error connecting to AI engine. Please try again.</em></div>`;
            }}
            
            sendButton.disabled = false;
            messages.scrollTop = messages.scrollHeight;
        }}
        
        async function updateTrainingQueue() {{
            try {{
                const response = await fetch('/training-queue');
                const data = await response.json();
                document.getElementById('trainingQueueSize').textContent = data.count;
            }} catch (error) {{
                console.error('Failed to update training queue:', error);
            }}
        }}
        
        // Update training queue on page load and periodically
        updateTrainingQueue();
        setInterval(updateTrainingQueue, 30000);
    </script>
</body>
</html>
            """
        
        @self.app.post("/chat")
        async def chat(request: ChatRequest):
            """
            Main chat endpoint using production intent routing
            
            [TAG: INTENT-ROUTER] - Uses new classification system
            """
            
            message = request.message.strip()
            
            # Use intent router if available
            if self.intent_router:
                classification = self.intent_router.classify(message)
                
                # Get response based on intent (with RAG integration)
                response, sources_used = await self._generate_intent_response(classification, message)
                confidence_score = classification.confidence
                training_queued = False
                
                # Check if needs knowledge gaps escalation
                if self.intent_router.should_escalate_to_knowledge_gaps(classification):
                    training_queued = True
                    if KNOWLEDGE_GAPS_AVAILABLE:
                        await self._log_knowledge_gap(message, confidence_score, classification)
                    else:
                        await self._add_to_simple_training_queue(message, confidence_score)
                
                return {
                    "response": response,
                    "confidence_score": confidence_score,
                    "sources_used": sources_used,
                    "timestamp": datetime.utcnow().isoformat(),
                    "training_queued": training_queued,
                    "intent_classified": classification.intent.value,
                    "debug_info": {
                        "intent": classification.intent.value,
                        "matched_patterns": classification.matched_patterns,
                        "security_flags": classification.security_flags,
                        "template": classification.suggested_template,
                        "escalation_required": classification.escalation_required,
                        "rag_sources": len(sources_used)
                    }
                }
            
            # Fallback if intent router not available
            else:
                return {
                    "response": "I'm currently running in limited mode. The intent routing system is not available.",
                    "confidence_score": 0.5,
                    "sources_used": [],
                    "timestamp": datetime.utcnow().isoformat(),
                    "training_queued": False
                }
        
        @self.app.get("/health")
        async def health():
            """Health check with architecture status"""
            rag_status = {}
            if self.rag_retriever:
                rag_status = self.rag_retriever.get_health_status()
            
            return {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "architecture": "production",
                "components": {
                    "intent_router": INTENT_ROUTER_AVAILABLE,
                    "knowledge_gaps": KNOWLEDGE_GAPS_AVAILABLE,
                    "rag_system": RAG_AVAILABLE and self.rag_retriever.is_available() if self.rag_retriever else False,
                    "templates_loaded": len(self.templates),
                    "confidence_threshold": self.confidence_threshold
                },
                "rag_status": rag_status
            }
        
        @self.app.get("/training-queue")
        async def get_training_queue():
            """Get training queue items"""
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
                return {"queue": [], "count": 0, "error": str(e)}
    
    async def _generate_intent_response(self, classification, message: str) -> tuple[str, list[str]]:
        """Generate response based on intent classification with RAG integration"""
        
        intent = classification.intent
        template_name = classification.suggested_template.replace('.txt', '')
        sources_used = []
        
        # Get template or fallback
        template = self.templates.get(template_name, self.templates.get('generic_unclear', 
            "I'd like to help with that. Could you provide more specific details?"))
        
        # PRIORITY: Try RAG first for any knowledge/definition questions regardless of intent
        if self.rag_retriever and self.rag_retriever.is_available():
            message_lower = message.lower()
            
            # Configuration questions (what siem are we using, etc.)
            if any(phrase in message_lower for phrase in ['are we using', 'are you using', 'configured', 'our siem', 'our edr', 'what siem', 'what edr']):
                answer, citations = self.rag_retriever.get_config_answer(message)
                if answer and citations:
                    return answer, citations
            
            # Definition and knowledge questions (prioritize over intent-specific templates)
            elif any(phrase in message_lower for phrase in ['what is', 'define', 'definition', 'what are', 'explain', 'describe', 'how does', 'what does']):
                answer, citations = self.rag_retriever.get_answer_with_citations(message)
                if answer and citations:
                    return answer, citations
        
        # Handle specific intents with context-aware responses
        if intent == IntentType.GREETING:
            return "Hello! What security matter can I help you investigate?", []
            
        elif intent == IntentType.BROAD_SCAN:
            return "I can help analyze active incidents or recent threat hunting results. Which would you like me to investigate?", []
            
        elif intent == IntentType.DANGEROUS_ACTION_REFUSAL:
            action = self._extract_dangerous_action(message)
            response = template.format(
                action=action,
                workflow="proper approval workflow"
            )
            return response, []
            
        elif intent == IntentType.PROMPT_INJECTION_REFUSAL:
            return "I'm WHIS, your security operations analyst. How can I help you with legitimate security operations today?", []
            
        elif intent == IntentType.INCIDENT_ANALYSIS:
            return "I can analyze that incident. Which specific aspect would you like me to investigate - the timeline, affected systems, or indicators of compromise?", []
            
        elif intent == IntentType.THREAT_HUNTING:
            return "I can help with that threat hunt. Which hunting approach should I focus on - behavioral analysis, IOC matching, or anomaly detection?", []
            
        elif intent == IntentType.TOOL_INTEGRATION:
            # Try RAG first for tool/definition questions
            if self.rag_retriever and self.rag_retriever.is_available():
                message_lower = message.lower()
                
                # Configuration questions (what siem are we using, etc.)
                if any(phrase in message_lower for phrase in ['are we using', 'are you using', 'configured', 'our siem', 'our edr']):
                    answer, citations = self.rag_retriever.get_config_answer(message)
                    if answer and citations:
                        return answer, citations
                
                # Definition questions (what is X, define X)
                elif any(phrase in message_lower for phrase in ['what is', 'define', 'definition', 'what are']):
                    answer, citations = self.rag_retriever.get_answer_with_citations(message)
                    if answer and citations:
                        return answer, citations
            
            # Fallback to knowledge gap
            return "I don't have enough confidence in my answer for this tool-specific question. I've queued it for Jimmie's next training session to improve my integration knowledge.", []
            
        else:
            # Generic unclear - try RAG for definition-style questions
            if self.rag_retriever and self.rag_retriever.is_available():
                message_lower = message.lower()
                
                if any(phrase in message_lower for phrase in ['what is', 'define', 'definition', 'explain']):
                    answer, citations = self.rag_retriever.get_answer_with_citations(message)
                    if answer and citations:
                        return answer, citations
            
            # Fallback to generic unclear
            return "I'd like to help with that security question. Could you be more specific about what you'd like me to investigate or analyze?", []
    
    def _extract_dangerous_action(self, message: str) -> str:
        """Extract the dangerous action from the message"""
        dangerous_words = ['isolate', 'shutdown', 'delete', 'remove', 'disable']
        for word in dangerous_words:
            if word in message.lower():
                return f"that {word} operation"
        return "that action"
    
    async def _log_knowledge_gap(self, query: str, confidence: float, classification):
        """Log to structured knowledge gaps system"""
        if not KNOWLEDGE_GAPS_AVAILABLE:
            return
            
        # Map classification to abstain reason
        reason_mapping = {
            IntentType.TOOL_INTEGRATION: AbstainReason.TOOL_FAILURE,
            IntentType.GENERIC_UNCLEAR: AbstainReason.NO_RAG_HITS
        }
        
        reason = reason_mapping.get(classification.intent, AbstainReason.LOW_CONFIDENCE)
        
        context = {
            "tenant": "default",
            "channel": "chat",
            "user_id": "anonymous", 
            "environment": "production",
            "model_version": "1.0.0",
            "intent_classified": classification.intent.value,
            "matched_patterns": classification.matched_patterns
        }
        
        await log_knowledge_gap(
            query=query,
            confidence=confidence,
            reason=reason,
            context=context,
            notify_slack=True
        )
    
    async def _add_to_simple_training_queue(self, question: str, confidence: float):
        """Fallback training queue if knowledge gaps not available"""
        try:
            import hashlib
            question_hash = hashlib.md5(question.lower().encode()).hexdigest()[:8]
            
            queue_item = TrainingQueueItem(
                question=question,
                context="production_fallback",
                timestamp=datetime.utcnow().isoformat(),
                confidence_score=confidence,
                question_hash=question_hash
            )
            
            with open(self.training_queue_file, 'a') as f:
                f.write(json.dumps(queue_item.model_dump()) + '\n')
                
        except Exception as e:
            print(f"Error adding to training queue: {e}")

def create_production_server():
    """Factory function"""
    return WHISProductionServer()

if __name__ == "__main__":
    server = create_production_server()
    
    print("🚀 Starting WHIS SOAR Copilot - Production Server...")
    print("🎯 Intent Router:", "✅ Active" if INTENT_ROUTER_AVAILABLE else "❌ Offline")
    print("🧠 Knowledge Gaps:", "✅ Active" if KNOWLEDGE_GAPS_AVAILABLE else "⚠️ Limited")
    print("📊 Templates Loaded:", len(server.templates))
    print("🌐 Dashboard: http://localhost:8000")
    print("📈 Health Check: http://localhost:8000/health")
    print("💬 Chat with WHIS using production-grade intent classification!")
    
    uvicorn.run(
        server.app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )