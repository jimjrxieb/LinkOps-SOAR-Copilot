#!/usr/bin/env python3
"""
📝 WHIS SOAR Observability - Structured Logging
==============================================

Production-ready structured logging for SOAR system observability.

Features:
- JSON structured logs for machine parsing
- Correlation ID tracking across requests
- PII redaction for security compliance
- Audit trail for all SOAR decisions and actions
- Performance tracking and error monitoring
- Integration with ELK/Loki log aggregation

Log Categories:
- AUDIT: All SOAR decisions, actions, approvals
- SECURITY: Safety gate triggers, threat detections
- PERFORMANCE: Timing, resource usage, bottlenecks  
- ERROR: Failures, exceptions, error conditions
- DEBUG: Development and troubleshooting info
"""

import json
import logging
import re
import hashlib
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
from contextvars import ContextVar
from functools import wraps

import structlog
from structlog.stdlib import LoggerFactory

# Context variables for request tracking
correlation_id: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)
user_id: ContextVar[Optional[str]] = ContextVar('user_id', default=None)
autonomy_level: ContextVar[Optional[str]] = ContextVar('autonomy_level', default=None)

# PII patterns for redaction
PII_PATTERNS = {
    'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
    'ip_address': re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'),
    'ssn': re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
    'credit_card': re.compile(r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b'),
    'phone': re.compile(r'\b\d{3}-\d{3}-\d{4}\b'),
}

# Secret patterns for redaction
SECRET_PATTERNS = {
    'api_key': re.compile(r'\b[Aa][Pp][Ii][-_]?[Kk][Ee][Yy]\s*[:=]\s*[\'"]?([a-zA-Z0-9_-]{20,})[\'"]?'),
    'password': re.compile(r'\b[Pp][Aa][Ss][Ss][Ww]?[Oo]?[Rr]?[Dd]\s*[:=]\s*[\'"]?([^\s\'"]{8,})[\'"]?'),
    'token': re.compile(r'\b[Tt][Oo][Kk][Ee][Nn]\s*[:=]\s*[\'"]?([a-zA-Z0-9._-]{20,})[\'"]?'),
    'bearer': re.compile(r'\b[Bb][Ee][Aa][Rr][Ee][Rr]\s+([a-zA-Z0-9._-]{20,})'),
}

class PIIRedactionProcessor:
    """Processor to redact PII and secrets from log messages"""
    
    def __init__(self):
        self.enabled = True
        self.redaction_marker = "[REDACTED]"
    
    def __call__(self, logger, method_name, event_dict):
        """Process log entry and redact sensitive data"""
        
        if not self.enabled:
            return event_dict
        
        # Redact PII and secrets from all string values
        for key, value in event_dict.items():
            if isinstance(value, str):
                event_dict[key] = self._redact_sensitive_data(value)
            elif isinstance(value, dict):
                event_dict[key] = self._redact_dict(value)
        
        return event_dict
    
    def _redact_sensitive_data(self, text: str) -> str:
        """Redact PII and secrets from text"""
        
        # Redact PII
        for pattern_name, pattern in PII_PATTERNS.items():
            if pattern_name == 'ip_address':
                # Only redact private IPs, keep public for threat intel
                text = re.sub(r'\b(?:10\.|192\.168\.|172\.(?:1[6-9]|2[0-9]|3[01])\.)(?:[0-9]{1,3}\.){1,2}[0-9]{1,3}\b',
                             '[IP_REDACTED]', text)
            else:
                text = pattern.sub(self.redaction_marker, text)
        
        # Redact secrets
        for pattern_name, pattern in SECRET_PATTERNS.items():
            text = pattern.sub(f'{pattern_name.upper()}_{self.redaction_marker}', text)
        
        return text
    
    def _redact_dict(self, data: dict) -> dict:
        """Recursively redact dictionary values"""
        
        result = {}
        for key, value in data.items():
            if isinstance(value, str):
                result[key] = self._redact_sensitive_data(value)
            elif isinstance(value, dict):
                result[key] = self._redact_dict(value)
            elif isinstance(value, list):
                result[key] = [self._redact_sensitive_data(item) if isinstance(item, str) else item for item in value]
            else:
                result[key] = value
        
        return result

class ContextualProcessor:
    """Add contextual information to log entries"""
    
    def __call__(self, logger, method_name, event_dict):
        """Add context variables to log entry"""
        
        # Add correlation ID if available
        if correlation_id.get():
            event_dict['correlation_id'] = correlation_id.get()
        
        # Add user ID if available
        if user_id.get():
            event_dict['user_id'] = user_id.get()
        
        # Add autonomy level if available  
        if autonomy_level.get():
            event_dict['autonomy_level'] = autonomy_level.get()
        
        # Add timestamp
        event_dict['timestamp'] = datetime.now().isoformat()
        
        # Add log level
        event_dict['level'] = method_name.upper()
        
        return event_dict

class AuditTrailProcessor:
    """Special processor for audit trail logs"""
    
    def __init__(self):
        self.audit_categories = {
            'INCIDENT_PROCESSED',
            'RUNBOOK_SELECTED', 
            'ACTION_EXECUTED',
            'SAFETY_GATE_TRIGGERED',
            'APPROVAL_REQUESTED',
            'APPROVAL_GRANTED',
            'AUTONOMY_LEVEL_CHANGED',
            'EMERGENCY_STOP',
            'POSTCONDITION_VERIFIED'
        }
    
    def __call__(self, logger, method_name, event_dict):
        """Process audit trail entries"""
        
        # Mark as audit log
        if event_dict.get('audit_category') in self.audit_categories:
            event_dict['log_type'] = 'AUDIT'
            event_dict['requires_retention'] = True
            
            # Generate audit hash for integrity
            audit_data = {
                'category': event_dict.get('audit_category'),
                'timestamp': event_dict.get('timestamp'),
                'correlation_id': event_dict.get('correlation_id'),
                'user_id': event_dict.get('user_id'),
                'data_hash': self._hash_data(event_dict)
            }
            
            event_dict['audit_hash'] = hashlib.sha256(
                json.dumps(audit_data, sort_keys=True).encode()
            ).hexdigest()[:16]
        
        return event_dict
    
    def _hash_data(self, data: dict) -> str:
        """Generate hash of log data for integrity"""
        # Remove fields that change between identical events
        clean_data = {k: v for k, v in data.items() 
                     if k not in ['timestamp', 'audit_hash']}
        return hashlib.md5(json.dumps(clean_data, sort_keys=True).encode()).hexdigest()

def configure_soar_logging(log_level: str = "INFO", enable_audit: bool = True):
    """Configure structured logging for SOAR system"""
    
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        ContextualProcessor(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        PIIRedactionProcessor(),
    ]
    
    if enable_audit:
        processors.append(AuditTrailProcessor())
    
    processors.extend([
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ])
    
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=None,
        level=getattr(logging, log_level.upper()),
    )

# Specialized loggers for different purposes
def get_audit_logger():
    """Get audit trail logger"""
    return structlog.get_logger("soar.audit")

def get_security_logger(): 
    """Get security events logger"""
    return structlog.get_logger("soar.security")

def get_performance_logger():
    """Get performance logger"""
    return structlog.get_logger("soar.performance")

def get_error_logger():
    """Get error logger"""
    return structlog.get_logger("soar.error")

# Context managers for setting correlation context
class correlation_context:
    """Context manager for correlation ID tracking"""
    
    def __init__(self, correlation_id_value: str = None):
        self.correlation_id_value = correlation_id_value or str(uuid.uuid4())
        self.token = None
    
    def __enter__(self):
        self.token = correlation_id.set(self.correlation_id_value)
        return self.correlation_id_value
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        correlation_id.reset(self.token)

class user_context:
    """Context manager for user ID tracking"""
    
    def __init__(self, user_id_value: str):
        self.user_id_value = user_id_value
        self.token = None
    
    def __enter__(self):
        self.token = user_id.set(self.user_id_value)
        return self.user_id_value
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        user_id.reset(self.token)

class autonomy_context:
    """Context manager for autonomy level tracking"""
    
    def __init__(self, autonomy_level_value: str):
        self.autonomy_level_value = autonomy_level_value
        self.token = None
    
    def __enter__(self):
        self.token = autonomy_level.set(self.autonomy_level_value)
        return self.autonomy_level_value
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        autonomy_level.reset(self.token)

# Decorators for automatic logging
def log_soar_operation(category: str):
    """Decorator to automatically log SOAR operations"""
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            audit_logger = get_audit_logger()
            
            start_time = datetime.now()
            
            try:
                result = func(*args, **kwargs)
                
                execution_time = (datetime.now() - start_time).total_seconds() * 1000
                
                audit_logger.info(
                    f"SOAR operation completed: {func.__name__}",
                    audit_category=category,
                    function=func.__name__,
                    execution_time_ms=round(execution_time, 2),
                    success=True,
                    result_type=type(result).__name__ if result else 'None'
                )
                
                return result
                
            except Exception as e:
                execution_time = (datetime.now() - start_time).total_seconds() * 1000
                
                get_error_logger().error(
                    f"SOAR operation failed: {func.__name__}",
                    function=func.__name__,
                    execution_time_ms=round(execution_time, 2),
                    error=str(e),
                    error_type=type(e).__name__,
                    success=False
                )
                
                raise
        
        return wrapper
    return decorator

# Audit trail convenience functions
def log_incident_processed(incident_id: str, runbook_id: str, classification: str, 
                         confidence: float, processing_time_ms: float):
    """Log incident processing for audit trail"""
    
    get_audit_logger().info(
        "Incident processed and classified",
        audit_category="INCIDENT_PROCESSED",
        incident_id=incident_id,
        runbook_id=runbook_id,
        classification=classification,
        confidence=confidence,
        processing_time_ms=processing_time_ms
    )

def log_runbook_selected(incident_id: str, runbook_id: str, decision_path: List[str],
                        safety_gates_evaluated: List[str]):
    """Log runbook selection for audit trail"""
    
    get_audit_logger().info(
        "Runbook selected for incident response",
        audit_category="RUNBOOK_SELECTED",
        incident_id=incident_id, 
        runbook_id=runbook_id,
        decision_path=decision_path,
        safety_gates_evaluated=safety_gates_evaluated
    )

def log_action_executed(action_id: str, action_type: str, tool_name: str,
                       target: str, success: bool, execution_time_ms: float):
    """Log action execution for audit trail"""
    
    get_audit_logger().info(
        "SOAR action executed",
        audit_category="ACTION_EXECUTED",
        action_id=action_id,
        action_type=action_type,
        tool_name=tool_name,
        target=target,
        success=success,
        execution_time_ms=execution_time_ms
    )

def log_safety_gate_triggered(gate_name: str, runbook_id: str, reason: str, 
                            blocked_actions: List[str]):
    """Log safety gate activation for audit trail"""
    
    get_security_logger().warning(
        "Safety gate triggered - actions blocked", 
        audit_category="SAFETY_GATE_TRIGGERED",
        gate_name=gate_name,
        runbook_id=runbook_id,
        reason=reason,
        blocked_actions=blocked_actions
    )

def log_approval_requested(approval_id: str, action_type: str, risk_level: str,
                         required_approvers: List[str]):
    """Log approval request for audit trail"""
    
    get_audit_logger().info(
        "Approval requested for high-risk action",
        audit_category="APPROVAL_REQUESTED",
        approval_id=approval_id,
        action_type=action_type,
        risk_level=risk_level,
        required_approvers=required_approvers
    )

def log_autonomy_level_changed(old_level: str, new_level: str, changed_by: str,
                             reason: str):
    """Log autonomy level changes for audit trail"""
    
    get_audit_logger().info(
        "SOAR autonomy level changed",
        audit_category="AUTONOMY_LEVEL_CHANGED", 
        old_level=old_level,
        new_level=new_level,
        changed_by=changed_by,
        reason=reason
    )

def log_emergency_stop(triggered_by: str, reason: str, actions_halted: int):
    """Log emergency stop activation for audit trail"""
    
    get_security_logger().critical(
        "EMERGENCY STOP activated - all automation halted",
        audit_category="EMERGENCY_STOP",
        triggered_by=triggered_by,
        reason=reason,
        actions_halted=actions_halted
    )

# Initialize logging on module import
configure_soar_logging()