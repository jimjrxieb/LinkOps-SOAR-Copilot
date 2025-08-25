#!/usr/bin/env python3
"""
🔍 WHIS Telemetry & Observability
================================
Comprehensive monitoring for ML pipelines with OpenTelemetry integration.
"""

import os
import time
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from contextlib import contextmanager
from functools import wraps
from pathlib import Path

import psutil
import torch
from dataclasses import dataclass
from opentelemetry import trace, metrics
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter


@dataclass
class ModelMetrics:
    """Model performance metrics"""
    inference_time: float
    tokens_generated: int
    memory_used: float
    gpu_utilization: float
    batch_size: int
    temperature: float


@dataclass
class RAGMetrics:
    """RAG pipeline metrics"""
    retrieval_time: float
    embedding_time: float
    rerank_time: float
    documents_retrieved: int
    similarity_scores: List[float]
    context_length: int


class WhisTelemetry:
    """Centralized telemetry for WHIS SOAR-Copilot"""
    
    def __init__(self, service_name: str = "whis-soar-copilot"):
        self.service_name = service_name
        self.start_time = time.time()
        
        # Initialize OpenTelemetry
        self._setup_tracing()
        self._setup_metrics()
        
        # Get tracers and meters
        self.tracer = trace.get_tracer(__name__)
        self.meter = metrics.get_meter(__name__)
        
        # Create metrics
        self._create_metrics()
        
        # Session tracking
        self.session_stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_tokens_generated": 0,
            "total_inference_time": 0.0,
            "rag_queries": 0,
            "cache_hits": 0,
            "cache_misses": 0
        }
        
        logging.info(f"🔍 Telemetry initialized for {service_name}")
    
    def _setup_tracing(self):
        """Initialize distributed tracing"""
        trace.set_tracer_provider(TracerProvider())
        
        # OTLP exporter for Jaeger/etc
        if os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"):
            otlp_exporter = OTLPSpanExporter(
                endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"),
                insecure=True
            )
            span_processor = BatchSpanProcessor(otlp_exporter)
            trace.get_tracer_provider().add_span_processor(span_processor)
    
    def _setup_metrics(self):
        """Initialize metrics collection"""
        # Prometheus metrics reader
        prometheus_reader = PrometheusMetricReader()
        metrics.set_meter_provider(MeterProvider(metric_readers=[prometheus_reader]))
    
    def _create_metrics(self):
        """Create application metrics"""
        # Request metrics
        self.request_counter = self.meter.create_counter(
            "whis_requests_total",
            description="Total number of requests"
        )
        
        self.request_duration = self.meter.create_histogram(
            "whis_request_duration_seconds",
            description="Request duration in seconds"
        )
        
        # Model metrics
        self.inference_duration = self.meter.create_histogram(
            "whis_inference_duration_seconds",
            description="Model inference duration"
        )
        
        self.tokens_generated = self.meter.create_counter(
            "whis_tokens_generated_total",
            description="Total tokens generated"
        )
        
        self.model_memory = self.meter.create_gauge(
            "whis_model_memory_bytes",
            description="Model memory usage"
        )
        
        # RAG metrics
        self.rag_retrieval_duration = self.meter.create_histogram(
            "whis_rag_retrieval_duration_seconds",
            description="RAG retrieval time"
        )
        
        self.rag_documents_retrieved = self.meter.create_histogram(
            "whis_rag_documents_retrieved",
            description="Number of documents retrieved"
        )
        
        # System metrics
        self.system_memory = self.meter.create_gauge(
            "whis_system_memory_percent",
            description="System memory usage percentage"
        )
        
        self.gpu_memory = self.meter.create_gauge(
            "whis_gpu_memory_percent",
            description="GPU memory usage percentage"
        )
    
    @contextmanager
    def trace_operation(self, operation_name: str, attributes: Optional[Dict] = None):
        """Context manager for tracing operations"""
        with self.tracer.start_as_current_span(operation_name) as span:
            if attributes:
                for key, value in attributes.items():
                    span.set_attribute(key, str(value))
            
            start_time = time.time()
            try:
                yield span
            finally:
                duration = time.time() - start_time
                span.set_attribute("duration_seconds", duration)
    
    def track_model_inference(self, metrics: ModelMetrics):
        """Track model inference metrics"""
        self.inference_duration.record(
            metrics.inference_time,
            {"model": "whis", "batch_size": str(metrics.batch_size)}
        )
        
        self.tokens_generated.add(
            metrics.tokens_generated,
            {"model": "whis", "temperature": str(metrics.temperature)}
        )
        
        self.model_memory.set(metrics.memory_used, {"device": "gpu"})
        
        # Update session stats
        self.session_stats["total_tokens_generated"] += metrics.tokens_generated
        self.session_stats["total_inference_time"] += metrics.inference_time
    
    def track_rag_query(self, metrics: RAGMetrics):
        """Track RAG pipeline metrics"""
        self.rag_retrieval_duration.record(
            metrics.retrieval_time,
            {"documents": str(metrics.documents_retrieved)}
        )
        
        self.rag_documents_retrieved.record(
            metrics.documents_retrieved,
            {"context_length": str(metrics.context_length)}
        )
        
        # Update session stats
        self.session_stats["rag_queries"] += 1
    
    def track_request(self, success: bool, duration: float, request_type: str = "chat"):
        """Track API request"""
        status = "success" if success else "error"
        
        self.request_counter.add(1, {"status": status, "type": request_type})
        self.request_duration.record(duration, {"status": status, "type": request_type})
        
        # Update session stats
        self.session_stats["total_requests"] += 1
        if success:
            self.session_stats["successful_requests"] += 1
        else:
            self.session_stats["failed_requests"] += 1
    
    def track_cache_hit(self, hit: bool):
        """Track cache performance"""
        if hit:
            self.session_stats["cache_hits"] += 1
        else:
            self.session_stats["cache_misses"] += 1
    
    def collect_system_metrics(self):
        """Collect system resource metrics"""
        # CPU and memory
        memory_percent = psutil.virtual_memory().percent
        self.system_memory.set(memory_percent)
        
        # GPU metrics if available
        if torch.cuda.is_available():
            for i in range(torch.cuda.device_count()):
                memory_allocated = torch.cuda.memory_allocated(i)
                memory_reserved = torch.cuda.memory_reserved(i)
                memory_total = torch.cuda.get_device_properties(i).total_memory
                
                gpu_percent = (memory_allocated / memory_total) * 100
                self.gpu_memory.set(gpu_percent, {"device": f"gpu_{i}"})
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get current system health status"""
        uptime = time.time() - self.start_time
        
        # Calculate rates
        success_rate = 0.0
        if self.session_stats["total_requests"] > 0:
            success_rate = self.session_stats["successful_requests"] / self.session_stats["total_requests"]
        
        cache_hit_rate = 0.0
        total_cache_ops = self.session_stats["cache_hits"] + self.session_stats["cache_misses"]
        if total_cache_ops > 0:
            cache_hit_rate = self.session_stats["cache_hits"] / total_cache_ops
        
        avg_inference_time = 0.0
        if self.session_stats["successful_requests"] > 0:
            avg_inference_time = self.session_stats["total_inference_time"] / self.session_stats["successful_requests"]
        
        return {
            "service": self.service_name,
            "uptime_seconds": uptime,
            "status": "healthy" if success_rate > 0.9 else "degraded",
            "performance": {
                "success_rate": success_rate,
                "avg_inference_time": avg_inference_time,
                "cache_hit_rate": cache_hit_rate,
                "total_requests": self.session_stats["total_requests"],
                "tokens_per_second": self.session_stats["total_tokens_generated"] / max(uptime, 1)
            },
            "resources": {
                "memory_percent": psutil.virtual_memory().percent,
                "gpu_available": torch.cuda.is_available(),
                "gpu_count": torch.cuda.device_count() if torch.cuda.is_available() else 0
            }
        }
    
    def export_session_report(self, output_path: Optional[str] = None) -> Dict[str, Any]:
        """Export comprehensive session report"""
        report = {
            "service": self.service_name,
            "session_start": datetime.fromtimestamp(self.start_time).isoformat(),
            "session_end": datetime.now().isoformat(),
            "duration_seconds": time.time() - self.start_time,
            "statistics": self.session_stats.copy(),
            "health": self.get_health_status(),
            "system_info": {
                "python_version": os.sys.version,
                "torch_version": torch.__version__,
                "cuda_available": torch.cuda.is_available(),
                "cuda_version": torch.version.cuda if torch.cuda.is_available() else None
            }
        }
        
        if output_path:
            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2)
            logging.info(f"📊 Session report exported to {output_path}")
        
        return report


def trace_inference(telemetry: WhisTelemetry):
    """Decorator for tracing model inference"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with telemetry.trace_operation("model_inference"):
                start_time = time.time()
                result = func(*args, **kwargs)
                inference_time = time.time() - start_time
                
                # Extract metrics from result if available
                if isinstance(result, dict) and "metrics" in result:
                    telemetry.track_model_inference(result["metrics"])
                
                return result
        return wrapper
    return decorator


def trace_rag_query(telemetry: WhisTelemetry):
    """Decorator for tracing RAG queries"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with telemetry.trace_operation("rag_query"):
                start_time = time.time()
                result = func(*args, **kwargs)
                query_time = time.time() - start_time
                
                # Extract RAG metrics if available
                if isinstance(result, dict) and "metrics" in result:
                    telemetry.track_rag_query(result["metrics"])
                
                return result
        return wrapper
    return decorator


# Global telemetry instance
_global_telemetry: Optional[WhisTelemetry] = None


def get_telemetry() -> WhisTelemetry:
    """Get global telemetry instance"""
    global _global_telemetry
    if _global_telemetry is None:
        _global_telemetry = WhisTelemetry()
    return _global_telemetry


def initialize_telemetry(service_name: str = "whis-soar-copilot") -> WhisTelemetry:
    """Initialize global telemetry"""
    global _global_telemetry
    _global_telemetry = WhisTelemetry(service_name)
    return _global_telemetry