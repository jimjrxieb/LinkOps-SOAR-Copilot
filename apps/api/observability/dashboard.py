#!/usr/bin/env python3
"""
📊 WHIS SOAR Observability Dashboard
===================================

Production observability dashboard for SOAR system monitoring.

Provides real-time visibility into:
- Incident processing pipeline
- Decision graph execution paths
- Action success rates and timing
- Safety gate effectiveness
- System health and performance
- Autonomy level effectiveness

Integration points:
- Grafana dashboard provisioning
- Prometheus metrics scraping
- ELK/Loki log aggregation
- Alert manager integration
"""

import json
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

from fastapi import APIRouter, Request, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse
import structlog

from .metrics import soar_metrics, get_all_metrics
from .logging import get_performance_logger, correlation_context

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/observability", tags=["Observability"])

@dataclass
class AlertRule:
    """Alert rule definition"""
    name: str
    condition: str
    threshold: float
    severity: str
    message: str
    enabled: bool = True

# Default alert rules
DEFAULT_ALERT_RULES = [
    AlertRule(
        name="high_incident_processing_time",
        condition="avg_processing_time_ms > threshold",
        threshold=2000.0,  # 2 seconds
        severity="warning",
        message="Incident processing time exceeding 2 seconds"
    ),
    AlertRule(
        name="low_action_success_rate",
        condition="success_rate < threshold",
        threshold=0.95,  # 95%
        severity="critical",
        message="Action success rate below 95%"
    ),
    AlertRule(
        name="high_safety_gate_blocks",
        condition="safety_gate_blocks_per_hour > threshold",
        threshold=50.0,
        severity="warning", 
        message="High number of safety gate blocks - review automation rules"
    ),
    AlertRule(
        name="system_memory_high",
        condition="memory_usage_mb > threshold",
        threshold=1024.0,  # 1GB
        severity="warning",
        message="System memory usage exceeding 1GB"
    ),
    AlertRule(
        name="decision_confidence_low",
        condition="avg_confidence < threshold",
        threshold=0.80,  # 80%
        severity="warning",
        message="Decision confidence below 80% - review classification rules"
    )
]

class AlertManager:
    """Manages alerting rules and notifications"""
    
    def __init__(self):
        self.rules = {rule.name: rule for rule in DEFAULT_ALERT_RULES}
        self.active_alerts: Dict[str, datetime] = {}
        self.alert_history: List[Dict[str, Any]] = []
        
    def evaluate_alerts(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Evaluate all alert rules against current metrics"""
        
        alerts = []
        current_time = datetime.now()
        
        for rule_name, rule in self.rules.items():
            if not rule.enabled:
                continue
                
            try:
                triggered = self._evaluate_rule(rule, metrics)
                
                if triggered:
                    if rule_name not in self.active_alerts:
                        # New alert
                        alert = {
                            "rule_name": rule_name,
                            "severity": rule.severity,
                            "message": rule.message,
                            "triggered_at": current_time.isoformat(),
                            "metrics_snapshot": metrics
                        }
                        
                        alerts.append(alert)
                        self.active_alerts[rule_name] = current_time
                        self.alert_history.append(alert)
                        
                        logger.warning(
                            "Alert triggered",
                            rule=rule_name,
                            severity=rule.severity,
                            message=rule.message
                        )
                else:
                    # Alert resolved
                    if rule_name in self.active_alerts:
                        logger.info("Alert resolved", rule=rule_name)
                        del self.active_alerts[rule_name]
                        
            except Exception as e:
                logger.error("Error evaluating alert rule", rule=rule_name, error=str(e))
        
        return alerts
    
    def _evaluate_rule(self, rule: AlertRule, metrics: Dict[str, Any]) -> bool:
        """Evaluate a single alert rule"""
        
        # Extract relevant metrics based on rule condition
        if "avg_processing_time_ms" in rule.condition:
            value = metrics.get("incidents", {}).get("avg_processing_time_ms", 0)
            return value > rule.threshold
            
        elif "success_rate" in rule.condition:
            action_stats = metrics.get("actions", {}).get("success_rate_by_tool", {})
            if action_stats:
                avg_success_rate = sum(action_stats.values()) / len(action_stats)
                return avg_success_rate < rule.threshold
            return False
            
        elif "safety_gate_blocks_per_hour" in rule.condition:
            # Calculate blocks per hour based on total blocks and uptime
            total_blocks = sum(metrics.get("actions", {}).get("safety_gate_blocks", {}).values())
            uptime_hours = metrics.get("system", {}).get("uptime_hours", 1)
            blocks_per_hour = total_blocks / max(uptime_hours, 0.1)  # Avoid division by zero
            return blocks_per_hour > rule.threshold
            
        elif "memory_usage_mb" in rule.condition:
            value = metrics.get("system", {}).get("memory_usage_mb", 0)
            return value > rule.threshold
            
        elif "avg_confidence" in rule.condition:
            value = metrics.get("incidents", {}).get("avg_confidence", 1.0)
            return value < rule.threshold
        
        return False

# Global alert manager
alert_manager = AlertManager()

@router.get("/metrics", response_model=Dict[str, Any])
async def get_metrics(request: Request):
    """Get all SOAR metrics for monitoring"""
    
    with correlation_context():
        perf_logger = get_performance_logger()
        start_time = time.time()
        
        try:
            metrics = get_all_metrics()
            
            # Evaluate alerts
            alerts = alert_manager.evaluate_alerts(metrics)
            if alerts:
                metrics["active_alerts"] = alerts
            
            processing_time = (time.time() - start_time) * 1000
            perf_logger.info(
                "Metrics request served",
                processing_time_ms=round(processing_time, 2),
                metrics_count=len(metrics)
            )
            
            return metrics
            
        except Exception as e:
            logger.error("Failed to retrieve metrics", error=str(e))
            raise HTTPException(status_code=500, detail=f"Metrics retrieval failed: {str(e)}")

@router.get("/metrics/prometheus", response_class=JSONResponse)
async def get_prometheus_metrics():
    """Get metrics in Prometheus exposition format"""
    
    try:
        metrics_text = soar_metrics.get_prometheus_metrics()
        
        return JSONResponse(
            content={"metrics": metrics_text},
            headers={"Content-Type": "text/plain; charset=utf-8"}
        )
        
    except Exception as e:
        logger.error("Failed to export Prometheus metrics", error=str(e))
        raise HTTPException(status_code=500, detail=f"Prometheus export failed: {str(e)}")

@router.get("/health/detailed", response_model=Dict[str, Any])
async def get_detailed_health():
    """Detailed health check with component status"""
    
    try:
        metrics = get_all_metrics()
        system_stats = metrics["system"]
        
        # Health scoring
        health_score = 100
        issues = []
        
        # Check processing time
        if metrics["incidents"].get("avg_processing_time_ms", 0) > 2000:
            health_score -= 20
            issues.append("High incident processing time")
        
        # Check action success rates
        action_stats = metrics["actions"].get("success_rate_by_tool", {})
        if action_stats:
            avg_success = sum(action_stats.values()) / len(action_stats)
            if avg_success < 0.95:
                health_score -= 30
                issues.append("Low action success rate")
        
        # Check memory usage
        if system_stats.get("memory_usage_mb", 0) > 1024:
            health_score -= 10
            issues.append("High memory usage")
        
        # Check confidence levels
        if metrics["incidents"].get("avg_confidence", 1.0) < 0.80:
            health_score -= 15
            issues.append("Low decision confidence")
        
        health_status = "healthy"
        if health_score < 70:
            health_status = "unhealthy"
        elif health_score < 85:
            health_status = "degraded"
        
        return {
            "status": health_status,
            "health_score": health_score,
            "issues": issues,
            "uptime_hours": system_stats.get("uptime_hours", 0),
            "total_incidents_processed": metrics["incidents"].get("total_incidents", 0),
            "total_actions_executed": metrics["actions"].get("total_actions", 0),
            "active_alerts": len(alert_manager.active_alerts),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return {
            "status": "unhealthy",
            "health_score": 0,
            "issues": [f"Health check error: {str(e)}"],
            "timestamp": datetime.now().isoformat()
        }

@router.get("/dashboard", response_class=HTMLResponse)
async def get_observability_dashboard():
    """Serve observability dashboard HTML"""
    
    dashboard_html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>WHIS SOAR - Observability Dashboard</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
            .header { background: #2c3e50; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
            .metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
            .metric-card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .metric-title { font-size: 18px; font-weight: bold; margin-bottom: 10px; color: #2c3e50; }
            .metric-value { font-size: 24px; font-weight: bold; margin-bottom: 5px; }
            .metric-description { color: #7f8c8d; font-size: 14px; }
            .chart-container { position: relative; height: 200px; margin-top: 10px; }
            .status-healthy { color: #27ae60; }
            .status-warning { color: #f39c12; }
            .status-critical { color: #e74c3c; }
            .refresh-btn { background: #3498db; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🤖 WHIS SOAR Observability Dashboard</h1>
            <p>Real-time monitoring and metrics for SOAR automation system</p>
            <button class="refresh-btn" onclick="refreshMetrics()">🔄 Refresh Data</button>
        </div>
        
        <div class="metrics-grid" id="metricsContainer">
            <div class="metric-card">
                <div class="metric-title">Loading...</div>
                <div class="metric-value">⏳</div>
                <div class="metric-description">Fetching SOAR metrics...</div>
            </div>
        </div>
        
        <script>
            async function refreshMetrics() {
                try {
                    const response = await fetch('/observability/metrics');
                    const data = await response.json();
                    renderMetrics(data);
                } catch (error) {
                    console.error('Failed to fetch metrics:', error);
                    document.getElementById('metricsContainer').innerHTML = 
                        '<div class="metric-card"><div class="metric-title">Error</div><div class="metric-value status-critical">❌</div><div class="metric-description">Failed to load metrics</div></div>';
                }
            }
            
            function renderMetrics(data) {
                const container = document.getElementById('metricsContainer');
                const incidents = data.incidents || {};
                const actions = data.actions || {};
                const system = data.system || {};
                
                container.innerHTML = `
                    <div class="metric-card">
                        <div class="metric-title">📊 Total Incidents</div>
                        <div class="metric-value">${incidents.total_incidents || 0}</div>
                        <div class="metric-description">Security incidents processed</div>
                    </div>
                    
                    <div class="metric-card">
                        <div class="metric-title">⚡ Total Actions</div>
                        <div class="metric-value">${actions.total_actions || 0}</div>
                        <div class="metric-description">Automated actions executed</div>
                    </div>
                    
                    <div class="metric-card">
                        <div class="metric-title">⏱️ Avg Processing Time</div>
                        <div class="metric-value ${incidents.avg_processing_time_ms > 2000 ? 'status-warning' : 'status-healthy'}">${incidents.avg_processing_time_ms || 0}ms</div>
                        <div class="metric-description">Incident classification speed</div>
                    </div>
                    
                    <div class="metric-card">
                        <div class="metric-title">🎯 Decision Confidence</div>
                        <div class="metric-value ${incidents.avg_confidence < 0.8 ? 'status-warning' : 'status-healthy'}">${Math.round((incidents.avg_confidence || 0) * 100)}%</div>
                        <div class="metric-description">Classification accuracy</div>
                    </div>
                    
                    <div class="metric-card">
                        <div class="metric-title">🔧 System Uptime</div>
                        <div class="metric-value status-healthy">${system.uptime_hours || 0}h</div>
                        <div class="metric-description">System availability</div>
                    </div>
                    
                    <div class="metric-card">
                        <div class="metric-title">💾 Memory Usage</div>
                        <div class="metric-value ${system.memory_usage_mb > 1024 ? 'status-warning' : 'status-healthy'}">${system.memory_usage_mb || 0}MB</div>
                        <div class="metric-description">System resource usage</div>
                    </div>
                    
                    <div class="metric-card">
                        <div class="metric-title">🛡️ Safety Gate Blocks</div>
                        <div class="metric-value">${Object.values(actions.safety_gate_blocks || {}).reduce((a, b) => a + b, 0)}</div>
                        <div class="metric-description">Actions blocked by safety gates</div>
                    </div>
                    
                    <div class="metric-card">
                        <div class="metric-title">📋 Active Runbooks</div>
                        <div class="metric-value">${Object.keys(incidents.incidents_by_runbook || {}).length}</div>
                        <div class="metric-description">Runbooks in use</div>
                    </div>
                `;
                
                // Show alerts if any
                if (data.active_alerts && data.active_alerts.length > 0) {
                    container.innerHTML += `
                        <div class="metric-card">
                            <div class="metric-title">🚨 Active Alerts</div>
                            <div class="metric-value status-critical">${data.active_alerts.length}</div>
                            <div class="metric-description">Issues requiring attention</div>
                        </div>
                    `;
                }
            }
            
            // Auto-refresh every 30 seconds
            setInterval(refreshMetrics, 30000);
            
            // Initial load
            refreshMetrics();
        </script>
    </body>
    </html>
    """
    
    return HTMLResponse(content=dashboard_html)

@router.get("/alerts", response_model=Dict[str, Any])
async def get_alerts():
    """Get current alert status"""
    
    return {
        "active_alerts": [
            {
                "rule_name": rule_name,
                "triggered_at": triggered_time.isoformat(),
                "severity": alert_manager.rules[rule_name].severity,
                "message": alert_manager.rules[rule_name].message
            }
            for rule_name, triggered_time in alert_manager.active_alerts.items()
        ],
        "alert_history": alert_manager.alert_history[-50:],  # Last 50 alerts
        "total_active": len(alert_manager.active_alerts)
    }

@router.post("/alerts/rules/{rule_name}/enable")
async def enable_alert_rule(rule_name: str):
    """Enable an alert rule"""
    
    if rule_name not in alert_manager.rules:
        raise HTTPException(status_code=404, detail="Alert rule not found")
    
    alert_manager.rules[rule_name].enabled = True
    
    logger.info("Alert rule enabled", rule=rule_name)
    
    return {"message": f"Alert rule {rule_name} enabled"}

@router.post("/alerts/rules/{rule_name}/disable") 
async def disable_alert_rule(rule_name: str):
    """Disable an alert rule"""
    
    if rule_name not in alert_manager.rules:
        raise HTTPException(status_code=404, detail="Alert rule not found")
    
    alert_manager.rules[rule_name].enabled = False
    
    # Clear active alert if any
    if rule_name in alert_manager.active_alerts:
        del alert_manager.active_alerts[rule_name]
    
    logger.info("Alert rule disabled", rule=rule_name)
    
    return {"message": f"Alert rule {rule_name} disabled"}

@router.get("/traces/{correlation_id}")
async def get_trace(correlation_id: str):
    """Get distributed trace for a correlation ID"""
    
    # This would integrate with a tracing system like Jaeger
    # For now, return a placeholder
    
    return {
        "correlation_id": correlation_id,
        "message": "Distributed tracing not yet implemented",
        "suggestion": "Integrate with Jaeger or Zipkin for request tracing"
    }