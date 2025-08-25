#!/usr/bin/env python3
"""
Simple SOAR API for UI demonstration
Just provides the basic endpoints the UI needs
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any
import random
import time

app = FastAPI(title="WHIS SOAR API", description="Simple SOAR API for UI demo")

# Enable CORS for UI connection
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    """Health check endpoint that UI expects"""
    return {
        "status": "healthy",
        "timestamp": "2025-08-24T16:00:00Z",
        "data_lake": True,
        "slack_alerts": True,
        "dependencies": {
            "soar_status": {
                "autonomy_level": "L0",
                "active_incidents": random.randint(0, 3),
                "active_hunts": random.randint(1, 4),
                "ai_confidence": 0.95,
                "autonomous_actions_today": random.randint(10, 50),
                "threat_level": "medium",
                "ai_engine_status": "active",
                "uptime_seconds": 3600
            }
        }
    }

@app.post("/chat")
async def chat(request: Dict[str, Any]):
    """Chat endpoint for AI conversations"""
    
    message = request.get("message", "").lower()
    
    # Simulate different responses based on message content
    if "threat" in message or "suspicious" in message:
        response = """🔍 **Threat Analysis Complete**

Based on your query, I've identified potential security concerns:

• **Risk Level**: Medium to High  
• **Recommended Action**: Initiate investigation workflow
• **Suggested Runbook**: RB-101 (Threat Investigation)

**Next Steps:**
1. Gather additional context from SIEM
2. Check threat intelligence feeds  
3. Validate against known attack patterns

Would you like me to create an incident for this threat?"""
        
    elif "incident" in message:
        response = """🚨 **Incident Response Plan Generated**

I've created a comprehensive response plan:

• **Priority**: High
• **Estimated Time**: 30-45 minutes
• **Required Resources**: SOC analyst, Network admin

**Response Steps:**
1. Contain the threat (isolate affected systems)
2. Investigate root cause
3. Eradicate threat vectors
4. Recover systems to normal operation
5. Document lessons learned

Ready to execute this plan?"""
        
    elif "hunt" in message:
        response = """🎯 **Threat Hunt Initiated**

Hunting for threats across your environment:

• **Hunt ID**: TH-2024-001
• **Scope**: All endpoints and network traffic
• **Duration**: ~2 hours
• **Indicators**: 147 IOCs loaded

**Current Status:**
- Endpoints scanned: 45/200
- Suspicious activities found: 3
- Confidence level: 87%

I'll notify you when the hunt completes!"""
        
    else:
        response = """👋 **Hello!** I'm WHIS, your AI SOAR copilot.

I can help you with:
🎯 **Threat Analysis** - Analyze suspicious activities
🚨 **Incident Response** - Create response plans  
🔍 **Threat Hunting** - Hunt for threats
🛡️ **Security Guidance** - Best practices
📊 **Risk Assessment** - Security posture

Try asking: "Analyze this suspicious PowerShell activity" or "Create incident response plan for ransomware"

What can I help you secure today?"""

    return {
        "response": response,
        "confidence_score": random.uniform(0.85, 0.98),
        "response_time_ms": random.randint(500, 1500),
        "request_id": f"req_{int(time.time())}",
        "sources": random.randint(3, 8),
        "threat_indicators": [],
        "recommendations": []
    }

@app.post("/threat-hunt")
async def threat_hunt(request: Dict[str, Any]):
    """Threat hunt endpoint"""
    return {
        "hunt_id": f"TH-{random.randint(1000, 9999)}",
        "status": "initiated",
        "hunt_type": "Lateral Movement Detection",
        "indicators_analyzed": random.randint(50, 200),
        "threats_found": [
            {"type": "suspicious_process", "confidence": 0.87},
            {"type": "network_anomaly", "confidence": 0.92}
        ],
        "confidence_score": random.uniform(0.85, 0.95),
        "estimated_completion": "2024-08-24T16:30:00Z"
    }

@app.post("/incident")
async def create_incident(request: Dict[str, Any]):
    """Create incident endpoint"""
    return {
        "incident_id": f"INC-{random.randint(10000, 99999)}",
        "estimated_resolution_time": "45 minutes",
        "assigned_analyst": "SOC-Analyst-01",
        "immediate_actions": [
            "Isolate affected system",
            "Collect forensic evidence", 
            "Notify incident commander",
            "Update threat intelligence"
        ]
    }

@app.get("/metrics")
async def metrics():
    """Metrics endpoint"""
    return {
        "requests_total": random.randint(1000, 5000),
        "requests_last_hour": random.randint(50, 200),
        "average_response_time_ms": random.randint(800, 1500),
        "ai_engine_uptime_seconds": random.randint(86400, 604800),
        "autonomous_actions_today": random.randint(10, 50),
        "rag_queries_total": random.randint(500, 2000),
        "threat_hunts_active": random.randint(1, 5),
        "incidents_open": random.randint(2, 8)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)