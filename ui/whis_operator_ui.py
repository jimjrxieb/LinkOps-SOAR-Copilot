#!/usr/bin/env python3
"""
🖥️ Whis SOAR-Copilot Operator UI
Minimal web interface for incident monitoring and approval workflows
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path
import sys

# Add API path for imports
sys.path.append('/home/jimmie/linkops-industries/SOAR-copilot/apps/api')
sys.path.append('/home/jimmie/linkops-industries/SOAR-copilot/pipelines')

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn

from attack_chain_analyzer import attack_chain_analyzer
from training_pipeline import training_pipeline

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Whis SOAR-Copilot Operator UI",
    description="🖥️ Minimal operator interface for incident monitoring",
    version="1.0.0"
)

# Templates and static files
ui_dir = Path(__file__).parent
templates = Jinja2Templates(directory=str(ui_dir / "templates"))
app.mount("/static", StaticFiles(directory=str(ui_dir / "static")), name="static")

# WebSocket connections for real-time updates
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def broadcast(self, message: dict):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                disconnected.append(connection)
        
        # Clean up disconnected connections
        for conn in disconnected:
            self.disconnect(conn)

manager = ConnectionManager()

# In-memory storage for demo (in production, use proper database)
incidents = []
approvals_pending = []
whis_responses = []

# ============================================================================
# WEB ROUTES
# ============================================================================

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main operator dashboard"""
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "title": "Whis SOAR-Copilot Operator Dashboard"
    })

@app.get("/incidents", response_class=HTMLResponse)
async def incidents_page(request: Request):
    """Incident monitoring page"""
    return templates.TemplateResponse("incidents.html", {
        "request": request,
        "title": "Incident Monitoring"
    })

@app.get("/approvals", response_class=HTMLResponse)
async def approvals_page(request: Request):
    """Approval workflow page"""
    return templates.TemplateResponse("approvals.html", {
        "request": request,
        "title": "Approval Workflows"
    })

@app.get("/training", response_class=HTMLResponse)
async def training_page(request: Request):
    """Training monitoring page"""
    return templates.TemplateResponse("training.html", {
        "request": request,
        "title": "Red vs Blue Training"
    })

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/api/dashboard/stats")
async def dashboard_stats():
    """Get dashboard statistics"""
    # Get attack chain stats
    chain_stats = attack_chain_analyzer.get_chain_statistics()
    
    # Get training stats
    training_stats = training_pipeline.get_training_statistics()
    
    # Calculate some real-time metrics
    active_incidents = len([i for i in incidents if i.get("status") == "active"])
    pending_approvals = len(approvals_pending)
    
    return {
        "incidents": {
            "total": len(incidents),
            "active": active_incidents,
            "closed": len(incidents) - active_incidents
        },
        "approvals": {
            "pending": pending_approvals,
            "processed_today": len([a for a in approvals_pending if a.get("created_at", "").startswith(datetime.now().strftime("%Y-%m-%d"))])
        },
        "attack_chains": chain_stats,
        "training": training_stats,
        "system_status": {
            "whis_api": "operational",
            "red_blue_lab": "active",
            "quality_gates": "passing"
        }
    }

@app.get("/api/incidents/recent")
async def recent_incidents():
    """Get recent incidents"""
    # In production, this would query from database with pagination
    recent = sorted(incidents, key=lambda x: x.get("timestamp", ""), reverse=True)[:20]
    return {"incidents": recent}

@app.post("/api/incidents/create")
async def create_incident(incident_data: dict):
    """Create new incident (from webhook)"""
    incident = {
        "id": f"inc_{int(datetime.now().timestamp())}",
        "title": incident_data.get("title", "Security Incident"),
        "severity": incident_data.get("severity", "medium"),
        "status": "active",
        "host": incident_data.get("host", "unknown"),
        "user": incident_data.get("user", "unknown"),
        "event_type": incident_data.get("event_type", "unknown"),
        "timestamp": datetime.now().isoformat(),
        "whis_analysis": incident_data.get("whis_analysis"),
        "raw_data": incident_data
    }
    
    incidents.append(incident)
    
    # Broadcast to connected clients
    await manager.broadcast({
        "type": "new_incident",
        "data": incident
    })
    
    logger.info(f"🚨 New incident created: {incident['id']}")
    return {"status": "created", "incident_id": incident["id"]}

@app.get("/api/approvals/pending")
async def pending_approvals():
    """Get pending approvals"""
    return {"approvals": approvals_pending}

@app.post("/api/approvals/{approval_id}/approve")
async def approve_action(approval_id: str, decision_data: dict):
    """Approve or reject a pending action"""
    approval = None
    for a in approvals_pending:
        if a["id"] == approval_id:
            approval = a
            break
    
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    
    approval["status"] = "approved" if decision_data.get("approved") else "rejected"
    approval["decision_by"] = decision_data.get("operator", "unknown")
    approval["decision_at"] = datetime.now().isoformat()
    approval["comments"] = decision_data.get("comments", "")
    
    # Broadcast decision
    await manager.broadcast({
        "type": "approval_decision",
        "data": approval
    })
    
    logger.info(f"✅ Approval {approval_id} {approval['status']} by {approval['decision_by']}")
    return {"status": approval["status"]}

@app.get("/api/training/status")
async def training_status():
    """Get training pipeline status"""
    try:
        # Get attack chain analysis status
        chains = attack_chain_analyzer.get_completed_chains(min_training_value=0.4)
        
        # Get training pipeline status
        stats = training_pipeline.get_training_statistics()
        
        return {
            "attack_chains_ready": len(chains),
            "training_examples_generated": stats.get("total_examples", 0),
            "last_training_run": "2024-01-15T10:30:00Z",  # Mock data
            "model_version": "whis-mega-v1.0",
            "quality_score": 0.85
        }
    except Exception as e:
        logger.error(f"Error getting training status: {e}")
        return {"error": str(e)}

@app.post("/api/training/generate")
async def generate_training_data():
    """Generate training data from attack chains"""
    try:
        result = await training_pipeline.process_attack_chains()
        
        # Broadcast update
        await manager.broadcast({
            "type": "training_update",
            "data": result
        })
        
        return result
    except Exception as e:
        logger.error(f"Error generating training data: {e}")
        return {"error": str(e)}

@app.post("/api/training/retrain")
async def trigger_retraining():
    """Trigger model retraining"""
    try:
        result = await training_pipeline.trigger_retraining()
        
        # Broadcast update
        await manager.broadcast({
            "type": "retraining_started",
            "data": result
        })
        
        return result
    except Exception as e:
        logger.error(f"Error triggering retraining: {e}")
        return {"error": str(e)}

# ============================================================================
# WEBSOCKET ENDPOINT
# ============================================================================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and listen for client messages
            data = await websocket.receive_json()
            
            # Handle client messages if needed
            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# ============================================================================
# BACKGROUND TASKS
# ============================================================================

async def periodic_updates():
    """Send periodic updates to connected clients"""
    while True:
        try:
            await asyncio.sleep(30)  # Update every 30 seconds
            
            # Get current stats
            stats = await dashboard_stats()
            
            # Broadcast to all connected clients
            await manager.broadcast({
                "type": "stats_update",
                "data": stats,
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error in periodic updates: {e}")

# ============================================================================
# STARTUP
# ============================================================================

@app.on_event("startup")
async def startup():
    """Initialize the operator UI"""
    logger.info("🖥️ Starting Whis Operator UI...")
    
    # Create some demo data
    demo_incidents = [
        {
            "id": "inc_001",
            "title": "Suspicious PowerShell Activity",
            "severity": "high",
            "status": "active",
            "host": "VULN-WIN-01",
            "user": "labadmin",
            "event_type": "Process Execution",
            "timestamp": (datetime.now() - timedelta(minutes=15)).isoformat(),
            "whis_analysis": {
                "triage_steps": ["Investigate PowerShell execution", "Check process tree"],
                "containment": ["Isolate host", "Block process"],
                "confidence": 0.85
            }
        },
        {
            "id": "inc_002", 
            "title": "Lateral Movement Detected",
            "severity": "critical",
            "status": "active",
            "host": "VULN-WIN-01",
            "user": "administrator",
            "event_type": "Network Connection",
            "timestamp": (datetime.now() - timedelta(minutes=5)).isoformat(),
            "whis_analysis": {
                "triage_steps": ["Review authentication logs", "Check lateral movement"],
                "containment": ["Network isolation", "Reset credentials"],
                "confidence": 0.92
            }
        }
    ]
    
    incidents.extend(demo_incidents)
    
    # Create some demo approvals
    demo_approvals = [
        {
            "id": "app_001",
            "title": "System Isolation Request",
            "description": "Isolate VULN-WIN-01 from network due to lateral movement",
            "severity": "critical",
            "requested_by": "whis_ai",
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "actions": ["Network isolation", "Process termination"]
        }
    ]
    
    approvals_pending.extend(demo_approvals)
    
    # Start periodic updates
    asyncio.create_task(periodic_updates())
    
    logger.info("✅ Whis Operator UI initialized")

if __name__ == "__main__":
    uvicorn.run(
        "whis_operator_ui:app",
        host="0.0.0.0",
        port=8080,
        reload=False
    )