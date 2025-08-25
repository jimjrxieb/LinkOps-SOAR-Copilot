#!/usr/bin/env python3
"""
📊 WHIS SOAR Observability - Metrics Collection
==============================================

Production-ready metrics collection for SOAR system monitoring.

Tracks:
- Incident processing metrics (volume, latency, success rate)
- Decision graph execution (path taken, confidence scores)
- Runbook execution (success/failure, time to complete)
- Safety gate triggers (which gates, how often)
- Tool execution metrics (by tool type, success rate)
- Autonomy level effectiveness (L0-L3 performance)

Integration:
- Prometheus exposition format
- Custom dashboards via /metrics endpoint
- Real-time alerts for anomalies
"""

import time
import threading
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
import json
import structlog

logger = structlog.get_logger(__name__)

@dataclass
class MetricPoint:
    """Individual metric data point"""
    name: str
    value: float
    timestamp: datetime = field(default_factory=datetime.now)
    labels: Dict[str, str] = field(default_factory=dict)
    
@dataclass
class IncidentMetrics:
    """Incident processing metrics"""
    total_incidents: int = 0
    incidents_by_severity: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    incidents_by_runbook: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    incidents_by_classification: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    avg_processing_time_ms: float = 0.0
    processing_times: deque = field(default_factory=lambda: deque(maxlen=1000))
    confidence_scores: deque = field(default_factory=lambda: deque(maxlen=1000))

@dataclass  
class ActionMetrics:
    """Action execution metrics"""
    total_actions: int = 0
    actions_by_tool: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    actions_by_autonomy_level: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    success_rate_by_tool: Dict[str, float] = field(default_factory=lambda: defaultdict(float))
    avg_execution_time_ms: float = 0.0
    safety_gate_blocks: Dict[str, int] = field(default_factory=lambda: defaultdict(int))

@dataclass
class SystemMetrics:
    """System health metrics"""
    uptime_seconds: float = 0.0
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    rag_query_count: int = 0
    rag_avg_response_time_ms: float = 0.0
    llm_request_count: int = 0
    llm_avg_response_time_ms: float = 0.0

class SOARMetricsCollector:
    """SOAR metrics collection and aggregation"""
    
    def __init__(self):
        self.incident_metrics = IncidentMetrics()
        self.action_metrics = ActionMetrics()
        self.system_metrics = SystemMetrics()
        
        self._lock = threading.RLock()
        self._start_time = datetime.now()
        self._custom_metrics: Dict[str, List[MetricPoint]] = defaultdict(list)
        
        # Start background collection
        self._collection_thread = threading.Thread(target=self._collect_system_metrics, daemon=True)
        self._collection_thread.start()
        
        logger.info("📊 SOAR metrics collector initialized")
    
    def record_incident_processed(self, 
                                incident_data: Dict[str, Any], 
                                runbook_id: str,
                                classification: str,
                                confidence: float,
                                processing_time_ms: float):
        """Record incident processing metrics"""
        
        with self._lock:
            # Basic counters
            self.incident_metrics.total_incidents += 1
            
            # Breakdown by attributes
            severity = incident_data.get('severity', 'unknown')
            self.incident_metrics.incidents_by_severity[severity] += 1
            self.incident_metrics.incidents_by_runbook[runbook_id] += 1
            self.incident_metrics.incidents_by_classification[classification] += 1
            
            # Time series data
            self.incident_metrics.processing_times.append(processing_time_ms)
            self.incident_metrics.confidence_scores.append(confidence)
            
            # Update averages
            if self.incident_metrics.processing_times:
                self.incident_metrics.avg_processing_time_ms = sum(self.incident_metrics.processing_times) / len(self.incident_metrics.processing_times)
        
        logger.info(
            "📋 Incident processed",
            runbook=runbook_id,
            classification=classification,
            confidence=confidence,
            processing_time_ms=processing_time_ms,
            total_incidents=self.incident_metrics.total_incidents
        )
    
    def record_action_executed(self,
                             action_type: str,
                             tool_name: str, 
                             autonomy_level: str,
                             success: bool,
                             execution_time_ms: float,
                             safety_gates_triggered: List[str] = None):
        """Record action execution metrics"""
        
        with self._lock:
            # Basic counters
            self.action_metrics.total_actions += 1
            self.action_metrics.actions_by_tool[tool_name] += 1
            self.action_metrics.actions_by_autonomy_level[autonomy_level] += 1
            
            # Safety gate blocks
            if safety_gates_triggered:
                for gate in safety_gates_triggered:
                    self.action_metrics.safety_gate_blocks[gate] += 1
            
            # Success rates (exponential moving average)
            current_rate = self.action_metrics.success_rate_by_tool[tool_name]
            if current_rate == 0:
                self.action_metrics.success_rate_by_tool[tool_name] = 1.0 if success else 0.0
            else:
                # EMA with alpha=0.1
                new_value = 1.0 if success else 0.0
                self.action_metrics.success_rate_by_tool[tool_name] = (0.1 * new_value) + (0.9 * current_rate)
        
        logger.info(
            "⚡ Action executed",
            action_type=action_type,
            tool=tool_name,
            autonomy_level=autonomy_level,
            success=success,
            execution_time_ms=execution_time_ms,
            safety_gates=safety_gates_triggered,
            total_actions=self.action_metrics.total_actions
        )
    
    def record_safety_gate_triggered(self, gate_name: str, runbook_id: str, reason: str):
        """Record safety gate activation"""
        
        with self._lock:
            self.action_metrics.safety_gate_blocks[gate_name] += 1
        
        logger.warning(
            "🛡️ Safety gate triggered",
            gate=gate_name,
            runbook=runbook_id,
            reason=reason,
            total_blocks=self.action_metrics.safety_gate_blocks[gate_name]
        )
    
    def record_custom_metric(self, name: str, value: float, labels: Dict[str, str] = None):
        """Record custom metric"""
        
        metric = MetricPoint(
            name=name,
            value=value,
            labels=labels or {}
        )
        
        with self._lock:
            self._custom_metrics[name].append(metric)
            # Keep only last 1000 points
            if len(self._custom_metrics[name]) > 1000:
                self._custom_metrics[name] = self._custom_metrics[name][-1000:]
    
    def get_incident_stats(self) -> Dict[str, Any]:
        """Get incident processing statistics"""
        
        with self._lock:
            stats = {
                "total_incidents": self.incident_metrics.total_incidents,
                "avg_processing_time_ms": round(self.incident_metrics.avg_processing_time_ms, 2),
                "incidents_by_severity": dict(self.incident_metrics.incidents_by_severity),
                "incidents_by_runbook": dict(self.incident_metrics.incidents_by_runbook),
                "incidents_by_classification": dict(self.incident_metrics.incidents_by_classification),
                "avg_confidence": round(sum(self.incident_metrics.confidence_scores) / len(self.incident_metrics.confidence_scores), 3) if self.incident_metrics.confidence_scores else 0.0,
                "processing_time_p95": self._calculate_percentile(list(self.incident_metrics.processing_times), 95),
                "processing_time_p99": self._calculate_percentile(list(self.incident_metrics.processing_times), 99)
            }
        
        return stats
    
    def get_action_stats(self) -> Dict[str, Any]:
        """Get action execution statistics"""
        
        with self._lock:
            stats = {
                "total_actions": self.action_metrics.total_actions,
                "actions_by_tool": dict(self.action_metrics.actions_by_tool),
                "actions_by_autonomy_level": dict(self.action_metrics.actions_by_autonomy_level),
                "success_rate_by_tool": {k: round(v, 3) for k, v in self.action_metrics.success_rate_by_tool.items()},
                "safety_gate_blocks": dict(self.action_metrics.safety_gate_blocks),
                "avg_execution_time_ms": round(self.action_metrics.avg_execution_time_ms, 2)
            }
        
        return stats
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get system health statistics"""
        
        uptime = (datetime.now() - self._start_time).total_seconds()
        
        with self._lock:
            stats = {
                "uptime_seconds": round(uptime, 1),
                "uptime_hours": round(uptime / 3600, 1),
                "memory_usage_mb": round(self.system_metrics.memory_usage_mb, 1),
                "cpu_usage_percent": round(self.system_metrics.cpu_usage_percent, 1),
                "rag_queries_total": self.system_metrics.rag_query_count,
                "rag_avg_response_time_ms": round(self.system_metrics.rag_avg_response_time_ms, 2),
                "llm_requests_total": self.system_metrics.llm_request_count, 
                "llm_avg_response_time_ms": round(self.system_metrics.llm_avg_response_time_ms, 2)
            }
        
        return stats
    
    def get_prometheus_metrics(self) -> str:
        """Export metrics in Prometheus format"""
        
        metrics = []
        
        # Incident metrics
        incident_stats = self.get_incident_stats()
        metrics.append(f'soar_incidents_total {incident_stats["total_incidents"]}')
        metrics.append(f'soar_incidents_avg_processing_time_ms {incident_stats["avg_processing_time_ms"]}')
        metrics.append(f'soar_incidents_avg_confidence {incident_stats["avg_confidence"]}')
        
        for severity, count in incident_stats["incidents_by_severity"].items():
            metrics.append(f'soar_incidents_by_severity{{severity="{severity}"}} {count}')
        
        for runbook, count in incident_stats["incidents_by_runbook"].items():
            metrics.append(f'soar_incidents_by_runbook{{runbook="{runbook}"}} {count}')
        
        # Action metrics
        action_stats = self.get_action_stats()
        metrics.append(f'soar_actions_total {action_stats["total_actions"]}')
        
        for tool, count in action_stats["actions_by_tool"].items():
            metrics.append(f'soar_actions_by_tool{{tool="{tool}"}} {count}')
            
        for tool, rate in action_stats["success_rate_by_tool"].items():
            metrics.append(f'soar_actions_success_rate{{tool="{tool}"}} {rate}')
        
        for gate, blocks in action_stats["safety_gate_blocks"].items():
            metrics.append(f'soar_safety_gate_blocks{{gate="{gate}"}} {blocks}')
        
        # System metrics
        system_stats = self.get_system_stats()
        metrics.append(f'soar_uptime_seconds {system_stats["uptime_seconds"]}')
        metrics.append(f'soar_memory_usage_mb {system_stats["memory_usage_mb"]}')
        metrics.append(f'soar_cpu_usage_percent {system_stats["cpu_usage_percent"]}')
        metrics.append(f'soar_rag_queries_total {system_stats["rag_queries_total"]}')
        metrics.append(f'soar_llm_requests_total {system_stats["llm_requests_total"]}')
        
        # Custom metrics
        with self._lock:
            for name, points in self._custom_metrics.items():
                if points:
                    latest = points[-1]
                    label_str = ",".join(f'{k}="{v}"' for k, v in latest.labels.items())
                    label_part = f'{{{label_str}}}' if label_str else ''
                    metrics.append(f'{name}{label_part} {latest.value}')
        
        return "\n".join(metrics) + "\n"
    
    def _collect_system_metrics(self):
        """Background thread to collect system metrics"""
        
        try:
            import psutil
            has_psutil = True
        except ImportError:
            has_psutil = False
            logger.warning("psutil not available, system metrics will be limited")
        
        while True:
            try:
                if has_psutil:
                    process = psutil.Process()
                    with self._lock:
                        self.system_metrics.memory_usage_mb = process.memory_info().rss / 1024 / 1024
                        self.system_metrics.cpu_usage_percent = process.cpu_percent()
                
                time.sleep(30)  # Update every 30 seconds
                
            except Exception as e:
                logger.error("Error collecting system metrics", error=str(e))
                time.sleep(60)  # Wait longer on error
    
    def _calculate_percentile(self, values: List[float], percentile: int) -> float:
        """Calculate percentile of values"""
        
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile / 100)
        if index >= len(sorted_values):
            index = len(sorted_values) - 1
        
        return round(sorted_values[index], 2)

# Global metrics collector instance
soar_metrics = SOARMetricsCollector()

# Convenience functions for common operations
def record_incident_processed(incident_data: Dict[str, Any], runbook_id: str, 
                            classification: str, confidence: float, processing_time_ms: float):
    """Record incident processing (convenience function)"""
    soar_metrics.record_incident_processed(incident_data, runbook_id, classification, confidence, processing_time_ms)

def record_action_executed(action_type: str, tool_name: str, autonomy_level: str,
                         success: bool, execution_time_ms: float, safety_gates_triggered: List[str] = None):
    """Record action execution (convenience function)"""
    soar_metrics.record_action_executed(action_type, tool_name, autonomy_level, success, execution_time_ms, safety_gates_triggered)

def record_safety_gate_triggered(gate_name: str, runbook_id: str, reason: str):
    """Record safety gate activation (convenience function)"""
    soar_metrics.record_safety_gate_triggered(gate_name, runbook_id, reason)

def get_all_metrics() -> Dict[str, Any]:
    """Get all SOAR metrics"""
    return {
        "timestamp": datetime.now().isoformat(),
        "incidents": soar_metrics.get_incident_stats(),
        "actions": soar_metrics.get_action_stats(), 
        "system": soar_metrics.get_system_stats()
    }