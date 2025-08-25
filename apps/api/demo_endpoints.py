#!/usr/bin/env python3
"""
Demo endpoints to make the UI dashboard fully functional
"""

from fastapi import APIRouter
from typing import Dict, Any
import random
import time

router = APIRouter()

@router.post("/chat")
async def chat_endpoint(request: Dict[str, Any]) -> Dict[str, Any]:
    """Demo chat endpoint for UI testing"""
    
    message = request.get("message", "").lower()
    
    # Simulate SOAR responses
    if "threat" in message or "suspicious" in message:
        response = """🔍 **Threat Analysis Complete**

Based on your query, I've identified potential security concerns. Here's my analysis:

• **Risk Level**: Medium to High
• **Recommended Action**: Initiate investigation workflow
• **Suggested Runbook**: RB-101 (Threat Investigation)

**Next Steps:**
1. Gather additional context from SIEM
2. Check threat intelligence feeds
3. Validate against known attack patterns

Would you like me to create an incident for this threat?"""
        
    elif "incident" in message or "response" in message:
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
        
    elif "hunt" in message or "apt" in message:
        response = """🎯 **Threat Hunt Initiated**

Hunting for APT indicators across your environment:

• **Hunt ID**: TH-2024-001
• **Scope**: All endpoints and network traffic
• **Duration**: ~2 hours
• **Indicators**: 147 IOCs loaded

**Current Status:**
- Endpoints scanned: 45/200
- Suspicious activities found: 3
- Confidence level: 87%

I'll notify you when the hunt completes with detailed findings."""
        
    elif "security" in message or "best practices" in message:
        response = """🛡️ **Security Guidance**

Here are my recommendations for improving your security posture:

**Top Priorities:**
1. **Endpoint Security**: Deploy EDR on all workstations
2. **Access Control**: Implement zero-trust network access
3. **Monitoring**: Enhance SIEM rule coverage
4. **Training**: Conduct phishing awareness training

**Quick Wins:**
• Enable MFA on all admin accounts
• Update security policies quarterly  
• Regular vulnerability assessments
• Incident response tabletop exercises

Need specific guidance on any of these areas?"""
        
    elif "risk" in message or "assess" in message:
        response = """📊 **Risk Assessment Summary**

Current security posture analysis:

**Overall Risk Score**: 7.2/10 (Good)

**Strengths:**
✅ Strong endpoint protection
✅ Regular security updates
✅ Incident response procedures

**Areas for Improvement:**
⚠️ Network segmentation
⚠️ Privileged access management
⚠️ Security awareness training

**Recommendations:**
1. Implement network microsegmentation
2. Deploy privileged access management
3. Enhanced security training program

Would you like a detailed remediation plan?"""
        
    else:
        response = f"""👋 **Hello!** 

I'm WHIS, your AI-powered SOAR copilot. I can help you with:

🎯 **Threat Analysis** - Analyze suspicious activities and indicators
🚨 **Incident Response** - Create response plans and coordinate actions  
🔍 **Threat Hunting** - Proactively hunt for threats in your environment
🛡️ **Security Guidance** - Best practices and recommendations
📊 **Risk Assessment** - Evaluate and improve security posture

Just ask me about any security concerns or try saying:
• "Analyze this suspicious PowerShell activity"
• "Create incident response plan for ransomware"
• "Hunt for APT29 indicators"
• "What are endpoint security best practices?"

What would you like to explore today?"""

    # Simulate processing time
    processing_time = random.randint(500, 1500)
    
    return {
        "response": response,
        "confidence_score": random.uniform(0.85, 0.98),
        "response_time_ms": processing_time,
        "request_id": f"req_{int(time.time())}",
        "sources": random.randint(3, 8),
        "threat_indicators": [],
        "recommendations": []
    }

@router.post("/threat-hunt")
async def threat_hunt_endpoint(request: Dict[str, Any]) -> Dict[str, Any]:
    """Demo threat hunt endpoint"""
    
    hunt_types = [
        "Lateral Movement Detection",
        "Credential Harvesting Hunt", 
        "Persistence Mechanism Search",
        "Data Exfiltration Analysis",
        "Command & Control Detection"
    ]
    
    return {
        "hunt_id": f"TH-{random.randint(1000, 9999)}",
        "status": "initiated",
        "hunt_type": random.choice(hunt_types),
        "indicators_analyzed": random.randint(50, 200),
        "threats_found": [
            {"type": "suspicious_process", "confidence": 0.87},
            {"type": "network_anomaly", "confidence": 0.92}
        ],
        "confidence_score": random.uniform(0.85, 0.95),
        "estimated_completion": "2024-08-24T16:30:00Z"
    }

@router.post("/incident") 
async def create_incident_endpoint(request: Dict[str, Any]) -> Dict[str, Any]:
    """Demo incident creation endpoint"""
    
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

@router.get("/metrics")
async def metrics_endpoint() -> Dict[str, Any]:
    """Demo metrics endpoint"""
    
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