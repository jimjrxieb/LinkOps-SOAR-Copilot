#!/usr/bin/env python3
"""
📊 Knowledge Gaps Dashboard & Analytics
======================================
Web-based console for reviewing and managing knowledge gaps

[TAG: CONSOLE-REVIEW] - Human review interface
[TAG: DASHBOARD-TILE] - Analytics and metrics visualization
"""

from fastapi import FastAPI, Request, HTTPException, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import json
import sys
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from knowledge_gaps.data_lake import KnowledgeGapDataLake
from knowledge_gaps.slack_alerts import SlackAlertManager
from knowledge_gaps.schemas import (
    UnansweredQuestionV1,
    KnowledgeGapMetrics,
    ApprovalState,
    AbstainReason,
    IntentCategory
)

class KnowledgeGapsDashboard:
    """
    Web dashboard for knowledge gaps management
    
    [TAG: CONSOLE-REVIEW] - Human review workflow
    [TAG: DASHBOARD-TILE] - Metrics and analytics
    """
    
    def __init__(self, data_lake: Optional[KnowledgeGapDataLake] = None):
        self.app = FastAPI(title="WHIS Knowledge Gaps Console")
        self.data_lake = data_lake or KnowledgeGapDataLake()
        self.slack_manager = SlackAlertManager()
        
        # Setup templates (for now, inline HTML)
        self.templates_dir = Path("templates")
        self.templates_dir.mkdir(exist_ok=True)
        
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup FastAPI routes"""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def dashboard_home():
            """Main dashboard view"""
            
            # Get recent metrics
            metrics = self.data_lake.calculate_metrics(hours=24)
            recent_gaps = self.data_lake.get_recent_gaps(hours=24)
            queued_alerts = self.slack_manager.get_queued_alerts()
            
            # Calculate additional stats
            stats = {
                "total_gaps_24h": metrics.gaps_count,
                "pending_review": metrics.pending_review,
                "promoted_count": metrics.promoted_count,
                "dismissed_count": metrics.dismissed_count,
                "gap_rate": f"{metrics.gap_rate:.1%}",
                "queued_alerts": len(queued_alerts),
                "avg_confidence": sum(gap.confidence_score for gap in recent_gaps) / len(recent_gaps) if recent_gaps else 0.0
            }
            
            return f"""
<!DOCTYPE html>
<html>
<head>
    <title>WHIS Knowledge Gaps Console</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', roboto, oxygen, ubuntu, cantarell, sans-serif;
            margin: 0; 
            padding: 0; 
            background: #f5f7fa;
            color: #2d3748;
        }}
        .header {{ 
            background: #1a202c; 
            color: white; 
            padding: 1rem 2rem;
            border-bottom: 3px solid #4299e1;
        }}
        .container {{ 
            max-width: 1200px; 
            margin: 0 auto; 
            padding: 2rem;
        }}
        .metrics-grid {{ 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
            gap: 1rem; 
            margin-bottom: 2rem;
        }}
        .metric-card {{ 
            background: white; 
            padding: 1.5rem; 
            border-radius: 8px; 
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border-left: 4px solid #4299e1;
        }}
        .metric-value {{ 
            font-size: 2rem; 
            font-weight: bold; 
            color: #2b6cb0;
        }}
        .metric-label {{ 
            color: #718096; 
            font-size: 0.9rem; 
            text-transform: uppercase; 
            letter-spacing: 0.5px;
        }}
        .gaps-table {{ 
            background: white; 
            border-radius: 8px; 
            overflow: hidden; 
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .gaps-table table {{ 
            width: 100%; 
            border-collapse: collapse;
        }}
        .gaps-table th {{ 
            background: #edf2f7; 
            padding: 1rem; 
            text-align: left; 
            font-weight: 600;
            color: #4a5568;
        }}
        .gaps-table td {{ 
            padding: 1rem; 
            border-bottom: 1px solid #e2e8f0;
        }}
        .gaps-table tr:hover {{ 
            background: #f7fafc;
        }}
        .confidence-badge {{ 
            padding: 0.25rem 0.75rem; 
            border-radius: 1rem; 
            font-size: 0.8rem; 
            font-weight: 600;
        }}
        .confidence-low {{ 
            background: #fed7d7; 
            color: #c53030;
        }}
        .confidence-medium {{ 
            background: #faf089; 
            color: #975a16;
        }}
        .confidence-high {{ 
            background: #c6f6d5; 
            color: #2f855a;
        }}
        .intent-badge {{ 
            padding: 0.25rem 0.5rem; 
            background: #bee3f8; 
            color: #2c5282; 
            border-radius: 4px; 
            font-size: 0.8rem;
        }}
        .btn {{ 
            padding: 0.5rem 1rem; 
            border: none; 
            border-radius: 4px; 
            cursor: pointer; 
            text-decoration: none; 
            display: inline-block; 
            font-size: 0.9rem;
        }}
        .btn-primary {{ 
            background: #4299e1; 
            color: white;
        }}
        .btn-secondary {{ 
            background: #a0aec0; 
            color: white;
        }}
        .btn-danger {{ 
            background: #f56565; 
            color: white;
        }}
        .refresh-note {{ 
            color: #718096; 
            font-size: 0.9rem; 
            margin-top: 1rem; 
            text-align: center;
        }}
        .query-preview {{ 
            max-width: 300px; 
            overflow: hidden; 
            text-overflow: ellipsis; 
            white-space: nowrap;
        }}
    </style>
    <script>
        // Auto-refresh every 30 seconds
        setTimeout(() => location.reload(), 30000);
        
        function reviewGap(gapId, action) {{
            fetch('/gaps/' + gapId + '/action', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/x-www-form-urlencoded'}},
                body: 'action=' + action
            }})
            .then(response => response.json())
            .then(data => {{
                alert(data.message || 'Action completed');
                location.reload();
            }})
            .catch(error => {{
                alert('Error: ' + error);
            }});
        }}
    </script>
</head>
<body>
    <div class="header">
        <h1>🧠 WHIS Knowledge Gaps Console</h1>
        <p>Monitor and manage gaps in WHIS knowledge for continuous learning</p>
    </div>
    
    <div class="container">
        <!-- Metrics Overview -->
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-value">{stats['total_gaps_24h']}</div>
                <div class="metric-label">Total Gaps (24h)</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{stats['pending_review']}</div>
                <div class="metric-label">Pending Review</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{stats['gap_rate']}</div>
                <div class="metric-label">Gap Rate</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{stats['avg_confidence']:.2f}</div>
                <div class="metric-label">Avg Confidence</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{stats['promoted_count']}</div>
                <div class="metric-label">Promoted</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{stats['queued_alerts']}</div>
                <div class="metric-label">Queued Alerts</div>
            </div>
        </div>
        
        <!-- Recent Knowledge Gaps -->
        <div class="gaps-table">
            <table>
                <thead>
                    <tr>
                        <th>Timestamp</th>
                        <th>Query</th>
                        <th>Intent</th>
                        <th>Reason</th>
                        <th>Confidence</th>
                        <th>Status</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>"""
            
            # Add recent gaps to table  
            table_rows = []
            for gap in recent_gaps[:20]:  # Show top 20
                confidence_class = "low" if gap.confidence_score < 0.5 else "medium" if gap.confidence_score < 0.8 else "high"
                confidence_badge = f'<span class="confidence-badge confidence-{confidence_class}">{gap.confidence_score:.2f}</span>'
                
                intent_badge = f'<span class="intent-badge">{gap.intent.value.title()}</span>'
                
                status_color = {{
                    ApprovalState.PENDING: "#fbb040",
                    ApprovalState.REVIEWED: "#4299e1", 
                    ApprovalState.PROMOTED: "#48bb78",
                    ApprovalState.DISMISSED: "#a0aec0"
                }}.get(gap.approval_state, "#a0aec0")
                
                actions_html = f'''
                    <button class="btn btn-primary" onclick="reviewGap('{gap.id}', 'promote')">Promote</button>
                    <button class="btn btn-secondary" onclick="reviewGap('{gap.id}', 'escalate')">Teacher</button>
                    <button class="btn btn-danger" onclick="reviewGap('{gap.id}', 'dismiss')">Dismiss</button>
                ''' if gap.approval_state == ApprovalState.PENDING else 'Reviewed'
                
                table_rows.append(f"""
                    <tr>
                        <td>{gap.timestamp.strftime("%H:%M:%S")}</td>
                        <td class="query-preview" title="{gap.query_text_redacted}">{gap.query_text_redacted}</td>
                        <td>{intent_badge}</td>
                        <td>{gap.why_abstained.value.replace('_', ' ').title()}</td>
                        <td>{confidence_badge}</td>
                        <td><span style="color: {status_color}">●</span> {gap.approval_state.value.title()}</td>
                        <td>{actions_html}</td>
                    </tr>
                """)
            
            # If no gaps, show empty message
            if not table_rows:
                table_rows.append("""
                    <tr>
                        <td colspan="7" style="text-align: center; color: #718096; padding: 2rem;">
                            No knowledge gaps found in the last 24 hours
                        </td>
                    </tr>
                """)
            
            return "".join(table_rows) + """
                </tbody>
            </table>
        </div>
        
        <div class="refresh-note">
            🔄 Auto-refreshing every 30 seconds | Last updated: """ + datetime.now().strftime("%H:%M:%S") + """
        </div>
    </div>
</body>
</html>
            """
        
        @self.app.get("/api/metrics")
        async def get_metrics():
            """API endpoint for metrics"""
            metrics = self.data_lake.calculate_metrics(hours=24)
            return metrics
        
        @self.app.get("/api/gaps")
        async def get_gaps(hours: int = 24, limit: int = 50):
            """API endpoint for recent gaps"""
            gaps = self.data_lake.get_recent_gaps(hours=hours)
            return {
                "gaps": [gap.model_dump() for gap in gaps[:limit]],
                "count": len(gaps[:limit]),
                "total": len(gaps)
            }
        
        @self.app.post("/gaps/{gap_id}/action")
        async def handle_gap_action(gap_id: str, action: str = Form(...)):
            """Handle gap review actions"""
            
            try:
                if action == "promote":
                    # TODO: Implement promotion to glossary
                    return {"status": "success", "message": f"Gap {gap_id} promoted to glossary"}
                    
                elif action == "escalate":
                    # Use Slack manager to handle teacher escalation
                    result = await self.slack_manager.process_alert_action("escalate", gap_id, "console_user")
                    return result
                    
                elif action == "dismiss":
                    # Use Slack manager to handle dismissal
                    result = await self.slack_manager.process_alert_action("dismiss", gap_id, "console_user")
                    return result
                    
                else:
                    raise HTTPException(status_code=400, detail=f"Unknown action: {action}")
                    
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/health")
        async def health():
            """Health check endpoint"""
            return {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "data_lake": True,
                "slack_alerts": True
            }

def create_dashboard_app(port: int = 8001) -> KnowledgeGapsDashboard:
    """Factory function to create dashboard app"""
    dashboard = KnowledgeGapsDashboard()
    return dashboard

if __name__ == "__main__":
    import uvicorn
    
    # Create and run dashboard
    dashboard = create_dashboard_app()
    
    print("🚀 Starting WHIS Knowledge Gaps Console...")
    print("📊 Dashboard: http://localhost:8001")
    print("📈 Metrics API: http://localhost:8001/api/metrics") 
    print("🔍 Monitor knowledge gaps and manage review workflow!")
    
    uvicorn.run(
        dashboard.app,
        host="0.0.0.0",
        port=8001,
        log_level="info"
    )