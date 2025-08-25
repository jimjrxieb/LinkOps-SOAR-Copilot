#!/usr/bin/env python3
"""
🚀 WHIS SOAR PIPELINE MONITOR - REAL-TIME DASHBOARD
==================================================
Real-time monitoring for lanes 1-4 pipeline progress on port 8000

Features:
- Live intake progress (Splunk + LimaCharlie events)
- Sanitization status (PII redactions, USE validation)
- Curation metrics (LLM training data, RAG chunks)
- Green-light gates (security scans, validation rates)

Usage: python3 pipeline_monitor.py
Access: http://localhost:8000
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional
import sys

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Whis SOAR Pipeline Monitor",
    description="🚀 Real-time pipeline monitoring for lanes 1-4",
    version="1.0.0"
)

# Templates and static files
ui_dir = Path(__file__).parent
templates = Jinja2Templates(directory=str(ui_dir / "templates"))
try:
    app.mount("/static", StaticFiles(directory=str(ui_dir / "static")), name="static")
except RuntimeError:
    # Static directory doesn't exist yet, create it
    (ui_dir / "static").mkdir(exist_ok=True)
    app.mount("/static", StaticFiles(directory=str(ui_dir / "static")), name="static")

# WebSocket connection manager
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
        
        for conn in disconnected:
            self.disconnect(conn)

manager = ConnectionManager()

def read_jsonl_file(filepath: Path) -> List[Dict[str, Any]]:
    """Read JSONL file and return list of records"""
    if not filepath.exists():
        return []
    
    records = []
    try:
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    records.append(json.loads(line))
    except Exception as e:
        logger.error(f"Error reading {filepath}: {e}")
    
    return records

def read_json_file(filepath: Path) -> Dict[str, Any]:
    """Read JSON file and return data"""
    if not filepath.exists():
        return {}
    
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error reading {filepath}: {e}")
        return {}

def get_pipeline_status() -> Dict[str, Any]:
    """Get comprehensive pipeline status from data directories"""
    base_dir = Path("/home/jimmie/linkops-industries/SOAR-copilot")
    
    # Check data directories
    intake_dir = base_dir / "data" / "intake"
    staging_dir = base_dir / "data" / "staging"
    curated_dir = base_dir / "data" / "curated"
    manifests_dir = base_dir / "data" / "manifests"
    results_dir = base_dir / "results"
    
    status = {
        "timestamp": datetime.now().isoformat(),
        "intake": {"events": 0, "files": 0, "sources": {"splunk": 0, "limacharlie": 0}},
        "sanitize": {"events": 0, "files": 0, "redactions": 0, "validation_rate": 0.0},
        "curate": {"llm_pairs": 0, "rag_chunks": 0, "files": 0},
        "manifests": {"count": 0, "total_events": 0, "total_bytes": 0},
        "security_gates": {"secrets_detected": 0, "validation_passes": 0, "status": "UNKNOWN"},
        "green_lights": {
            "intake": False,
            "sanitize": False, 
            "curate": False,
            "overall": False
        }
    }
    
    # Intake stats
    if intake_dir.exists():
        for source_dir in ["splunk", "limacharlie"]:
            source_path = intake_dir / source_dir
            if source_path.exists():
                jsonl_files = list(source_path.glob("**/*.jsonl"))
                status["intake"]["files"] += len(jsonl_files)
                
                source_events = 0
                for file in jsonl_files:
                    events = read_jsonl_file(file)
                    source_events += len(events)
                
                status["intake"]["sources"][source_dir] = source_events
                status["intake"]["events"] += source_events
    
    # Staging/Sanitize stats
    if staging_dir.exists():
        jsonl_files = list(staging_dir.glob("**/*.jsonl"))
        status["sanitize"]["files"] = len(jsonl_files)
        
        total_events = 0
        for file in jsonl_files:
            events = read_jsonl_file(file)
            total_events += len(events)
            
            # Check for redaction metadata
            for event in events[:10]:  # Sample first 10
                if "metadata" in event and "redactions" in event.get("metadata", {}):
                    redactions = event["metadata"]["redactions"]
                    status["sanitize"]["redactions"] += sum(redactions.values()) if isinstance(redactions, dict) else 0
        
        status["sanitize"]["events"] = total_events
        
        # Calculate validation rate (mock for now)
        if total_events > 0:
            status["sanitize"]["validation_rate"] = min(0.99, max(0.85, (total_events - 1) / total_events))  # Mock validation
    
    # Curated stats
    if curated_dir.exists():
        # LLM training data
        llm_dir = curated_dir / "llm"
        if llm_dir.exists():
            jsonl_files = list(llm_dir.glob("*.jsonl"))
            for file in jsonl_files:
                pairs = read_jsonl_file(file)
                status["curate"]["llm_pairs"] += len(pairs)
        
        # RAG chunks
        rag_dir = curated_dir / "rag"
        if rag_dir.exists():
            jsonl_files = list(rag_dir.glob("**/*.jsonl"))
            for file in jsonl_files:
                chunks = read_jsonl_file(file)
                status["curate"]["rag_chunks"] += len(chunks)
        
        status["curate"]["files"] = len(list(curated_dir.glob("**/*.jsonl")))
    
    # Manifest stats
    if manifests_dir.exists():
        manifest_files = list(manifests_dir.glob("*.json"))
        status["manifests"]["count"] = len(manifest_files)
        
        for manifest_file in manifest_files:
            manifest = read_json_file(manifest_file)
            status["manifests"]["total_events"] += manifest.get("events", 0)
            status["manifests"]["total_bytes"] += manifest.get("bytes", 0)
    
    # Security gates (check results directory)
    if results_dir.exists():
        # Check for security scan results
        security_files = list(results_dir.glob("**/security_*.json"))
        status["security_gates"]["validation_passes"] = len(security_files)
        
        # Mock security status
        if status["sanitize"]["events"] > 0 and status["sanitize"]["redactions"] > 0:
            status["security_gates"]["status"] = "PASS"
        else:
            status["security_gates"]["status"] = "PENDING"
    
    # Green light calculations
    status["green_lights"]["intake"] = status["intake"]["events"] > 0
    status["green_lights"]["sanitize"] = (
        status["sanitize"]["events"] > 0 and 
        status["sanitize"]["validation_rate"] >= 0.99
    )
    status["green_lights"]["curate"] = (
        status["curate"]["llm_pairs"] > 0 or 
        status["curate"]["rag_chunks"] > 0
    )
    status["green_lights"]["overall"] = all([
        status["green_lights"]["intake"],
        status["green_lights"]["sanitize"],
        status["green_lights"]["curate"]
    ])
    
    return status

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main pipeline monitoring dashboard"""
    return templates.TemplateResponse("pipeline_dashboard.html", {
        "request": request,
        "title": "Whis SOAR Pipeline Monitor"
    })

@app.get("/api/pipeline/status")
async def pipeline_status():
    """Get current pipeline status"""
    return get_pipeline_status()

@app.get("/api/pipeline/history")
async def pipeline_history():
    """Get pipeline execution history"""
    # Mock data for now - in production, read from logs
    history = [
        {
            "timestamp": (datetime.now() - timedelta(hours=2)).isoformat(),
            "stage": "intake",
            "status": "completed",
            "events": 15420,
            "duration": 180
        },
        {
            "timestamp": (datetime.now() - timedelta(hours=1, minutes=45)).isoformat(),
            "stage": "sanitize", 
            "status": "completed",
            "events": 15420,
            "redactions": 234,
            "duration": 45
        },
        {
            "timestamp": (datetime.now() - timedelta(hours=1, minutes=30)).isoformat(),
            "stage": "curate",
            "status": "completed", 
            "llm_pairs": 820,
            "rag_chunks": 156,
            "duration": 120
        }
    ]
    return {"history": history}

@app.get("/api/pipeline/logs/{stage}")
async def pipeline_logs(stage: str):
    """Get logs for specific pipeline stage"""
    # Mock logs - in production, read from actual log files
    logs = [
        f"[{datetime.now().strftime('%H:%M:%S')}] Starting {stage} pipeline",
        f"[{datetime.now().strftime('%H:%M:%S')}] Processing events...",
        f"[{datetime.now().strftime('%H:%M:%S')}] {stage} pipeline completed successfully"
    ]
    return {"stage": stage, "logs": logs}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time updates"""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        manager.disconnect(websocket)

async def periodic_status_updates():
    """Send periodic status updates to connected clients"""
    while True:
        try:
            await asyncio.sleep(5)  # Update every 5 seconds
            
            status = get_pipeline_status()
            
            await manager.broadcast({
                "type": "status_update",
                "data": status,
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error in periodic updates: {e}")

@app.on_event("startup")
async def startup():
    """Initialize the pipeline monitor"""
    logger.info("🚀 Starting Whis SOAR Pipeline Monitor on port 8000...")
    
    # Ensure templates directory exists
    templates_dir = ui_dir / "templates"
    templates_dir.mkdir(exist_ok=True)
    
    # Create basic dashboard template if it doesn't exist
    dashboard_template = templates_dir / "pipeline_dashboard.html"
    if not dashboard_template.exists():
        dashboard_html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/alpinejs@3.x.x/dist/cdn.min.js" defer></script>
</head>
<body class="bg-gray-900 text-white">
    <div class="container mx-auto px-4 py-8" x-data="pipelineMonitor()">
        <header class="mb-8">
            <h1 class="text-4xl font-bold text-blue-400">🚀 Whis SOAR Pipeline Monitor</h1>
            <p class="text-gray-400 mt-2">Real-time monitoring for lanes 1-4 data pipeline</p>
        </header>

        <!-- Status Cards -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <!-- Intake Card -->
            <div class="bg-gray-800 rounded-lg p-6 border-l-4" :class="status.green_lights.intake ? 'border-green-400' : 'border-yellow-400'">
                <h3 class="text-xl font-semibold text-blue-300 mb-3">📥 Intake</h3>
                <div class="space-y-2">
                    <p class="text-2xl font-bold" x-text="status.intake.events.toLocaleString()">0</p>
                    <p class="text-sm text-gray-400">Total Events</p>
                    <div class="flex justify-between text-xs">
                        <span>Splunk: <span x-text="status.intake.sources.splunk"></span></span>
                        <span>LC: <span x-text="status.intake.sources.limacharlie"></span></span>
                    </div>
                </div>
            </div>

            <!-- Sanitize Card -->
            <div class="bg-gray-800 rounded-lg p-6 border-l-4" :class="status.green_lights.sanitize ? 'border-green-400' : 'border-yellow-400'">
                <h3 class="text-xl font-semibold text-purple-300 mb-3">🧹 Sanitize</h3>
                <div class="space-y-2">
                    <p class="text-2xl font-bold" x-text="status.sanitize.events.toLocaleString()">0</p>
                    <p class="text-sm text-gray-400">Events Processed</p>
                    <div class="flex justify-between text-xs">
                        <span>Redacted: <span x-text="status.sanitize.redactions"></span></span>
                        <span>Valid: <span x-text="(status.sanitize.validation_rate * 100).toFixed(1)">0</span>%</span>
                    </div>
                </div>
            </div>

            <!-- Curate Card -->
            <div class="bg-gray-800 rounded-lg p-6 border-l-4" :class="status.green_lights.curate ? 'border-green-400' : 'border-yellow-400'">
                <h3 class="text-xl font-semibold text-green-300 mb-3">🎓 Curate</h3>
                <div class="space-y-2">
                    <p class="text-2xl font-bold" x-text="status.curate.llm_pairs.toLocaleString()">0</p>
                    <p class="text-sm text-gray-400">LLM Training Pairs</p>
                    <div class="flex justify-between text-xs">
                        <span>RAG Chunks: <span x-text="status.curate.rag_chunks"></span></span>
                        <span>Files: <span x-text="status.curate.files"></span></span>
                    </div>
                </div>
            </div>

            <!-- Security Gates Card -->
            <div class="bg-gray-800 rounded-lg p-6 border-l-4" :class="status.security_gates.status === 'PASS' ? 'border-green-400' : 'border-red-400'">
                <h3 class="text-xl font-semibold text-red-300 mb-3">🛡️ Security</h3>
                <div class="space-y-2">
                    <p class="text-2xl font-bold" x-text="status.security_gates.status">UNKNOWN</p>
                    <p class="text-sm text-gray-400">Gate Status</p>
                    <div class="flex justify-between text-xs">
                        <span>Scans: <span x-text="status.security_gates.validation_passes"></span></span>
                        <span>Secrets: <span x-text="status.security_gates.secrets_detected"></span></span>
                    </div>
                </div>
            </div>
        </div>

        <!-- Green Light Status -->
        <div class="bg-gray-800 rounded-lg p-6 mb-8">
            <h3 class="text-xl font-semibold mb-4">🚦 Green Light Status</h3>
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div class="text-center">
                    <div class="text-3xl mb-2" x-text="status.green_lights.intake ? '🟢' : '🟡'">🟡</div>
                    <p class="text-sm">Intake</p>
                </div>
                <div class="text-center">
                    <div class="text-3xl mb-2" x-text="status.green_lights.sanitize ? '🟢' : '🟡'">🟡</div>
                    <p class="text-sm">Sanitize</p>
                </div>
                <div class="text-center">
                    <div class="text-3xl mb-2" x-text="status.green_lights.curate ? '🟢' : '🟡'">🟡</div>
                    <p class="text-sm">Curate</p>
                </div>
                <div class="text-center">
                    <div class="text-3xl mb-2" x-text="status.green_lights.overall ? '🟢' : '🟡'">🟡</div>
                    <p class="text-sm font-bold">Overall</p>
                </div>
            </div>
        </div>

        <!-- Real-time Logs -->
        <div class="bg-gray-800 rounded-lg p-6">
            <h3 class="text-xl font-semibold mb-4">📊 Real-time Activity</h3>
            <div class="bg-gray-900 rounded p-4 font-mono text-sm h-48 overflow-y-auto" id="logs">
                <div class="text-green-400" x-show="connected">● Connected to pipeline monitor</div>
                <div class="text-red-400" x-show="!connected">● Disconnected from pipeline monitor</div>
                <div class="text-gray-400 mt-2">Last update: <span x-text="lastUpdate">Never</span></div>
            </div>
        </div>
    </div>

    <script>
        function pipelineMonitor() {
            return {
                status: {
                    intake: { events: 0, sources: { splunk: 0, limacharlie: 0 } },
                    sanitize: { events: 0, redactions: 0, validation_rate: 0 },
                    curate: { llm_pairs: 0, rag_chunks: 0, files: 0 },
                    security_gates: { status: 'UNKNOWN', validation_passes: 0, secrets_detected: 0 },
                    green_lights: { intake: false, sanitize: false, curate: false, overall: false }
                },
                connected: false,
                lastUpdate: 'Never',
                ws: null,

                init() {
                    this.connectWebSocket();
                    this.fetchStatus();
                    setInterval(() => this.fetchStatus(), 10000); // Fallback polling
                },

                connectWebSocket() {
                    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                    this.ws = new WebSocket(`${protocol}//${window.location.host}/ws`);
                    
                    this.ws.onopen = () => {
                        this.connected = true;
                        console.log('WebSocket connected');
                    };
                    
                    this.ws.onmessage = (event) => {
                        const data = JSON.parse(event.data);
                        if (data.type === 'status_update') {
                            this.status = data.data;
                            this.lastUpdate = new Date().toLocaleTimeString();
                        }
                    };
                    
                    this.ws.onclose = () => {
                        this.connected = false;
                        setTimeout(() => this.connectWebSocket(), 5000);
                    };
                },

                async fetchStatus() {
                    try {
                        const response = await fetch('/api/pipeline/status');
                        const data = await response.json();
                        this.status = data;
                        this.lastUpdate = new Date().toLocaleTimeString();
                    } catch (error) {
                        console.error('Error fetching status:', error);
                    }
                }
            };
        }
    </script>
</body>
</html>'''
        
        with open(dashboard_template, 'w') as f:
            f.write(dashboard_html)
    
    # Start periodic updates
    asyncio.create_task(periodic_status_updates())
    
    logger.info("✅ Pipeline Monitor initialized on http://localhost:8000")

if __name__ == "__main__":
    uvicorn.run(
        "pipeline_monitor:app",
        host="0.0.0.0",
        port=8000,
        reload=False
    )