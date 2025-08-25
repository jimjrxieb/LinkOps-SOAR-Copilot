#!/usr/bin/env python3
"""
📝 WHIS Unified Logging
======================
Structured logging with security-aware redaction, correlation IDs,
and multi-destination output for production observability.
"""

import os
import sys
import json
import logging
import logging.handlers
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
import traceback
import uuid
from contextvars import ContextVar
from dataclasses import dataclass, asdict
import re


# Context variables for request correlation
request_id: ContextVar[Optional[str]] = ContextVar('request_id', default=None)
session_id: ContextVar[Optional[str]] = ContextVar('session_id', default=None)
user_id: ContextVar[Optional[str]] = ContextVar('user_id', default=None)


@dataclass
class LogContext:
    """Structured log context"""
    timestamp: str
    level: str
    logger: str
    message: str
    request_id: Optional[str] = None
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    component: Optional[str] = None
    operation: Optional[str] = None
    duration_ms: Optional[float] = None
    extra: Optional[Dict[str, Any]] = None


class SensitiveDataFilter(logging.Filter):
    """Filter to redact sensitive information from logs"""
    
    SENSITIVE_PATTERNS = [
        # API Keys and tokens
        (re.compile(r'(api[_-]?key["\s]*[:=]["\s]*)([^"\s]+)', re.IGNORECASE), r'\1[REDACTED]'),
        (re.compile(r'(bearer["\s]+)([a-zA-Z0-9\-._~+/]+=*)', re.IGNORECASE), r'\1[REDACTED]'),
        (re.compile(r'(token["\s]*[:=]["\s]*)([^"\s]+)', re.IGNORECASE), r'\1[REDACTED]'),
        
        # Passwords
        (re.compile(r'(password["\s]*[:=]["\s]*)([^"\s]+)', re.IGNORECASE), r'\1[REDACTED]'),
        (re.compile(r'(pwd["\s]*[:=]["\s]*)([^"\s]+)', re.IGNORECASE), r'\1[REDACTED]'),
        
        # Secrets and private keys
        (re.compile(r'(secret["\s]*[:=]["\s]*)([^"\s]+)', re.IGNORECASE), r'\1[REDACTED]'),
        (re.compile(r'(private[_-]?key["\s]*[:=]["\s]*)([^"\s]+)', re.IGNORECASE), r'\1[REDACTED]'),
        
        # Email addresses (partial redaction)
        (re.compile(r'([a-zA-Z0-9._%+-]+)@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'), r'****@\2'),
        
        # Credit card numbers
        (re.compile(r'\b(\d{4})[- ]?(\d{4})[- ]?(\d{4})[- ]?(\d{4})\b'), r'\1-****-****-\4'),
        
        # SSN-like patterns
        (re.compile(r'\b(\d{3})[- ]?(\d{2})[- ]?(\d{4})\b'), r'***-**-\3'),
        
        # IP addresses (partial redaction for privacy)
        (re.compile(r'\b(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})\b'), r'\1.\2.***.\4'),
    ]
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Filter and redact sensitive data from log records"""
        # Redact message
        record.msg = self._redact_sensitive_data(str(record.msg))
        
        # Redact args if present
        if record.args:
            record.args = tuple(
                self._redact_sensitive_data(str(arg)) if isinstance(arg, str) else arg
                for arg in record.args
            )
        
        return True
    
    def _redact_sensitive_data(self, text: str) -> str:
        """Apply all redaction patterns to text"""
        for pattern, replacement in self.SENSITIVE_PATTERNS:
            text = pattern.sub(replacement, text)
        return text


class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON"""
        
        # Build context
        context = LogContext(
            timestamp=datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            level=record.levelname,
            logger=record.name,
            message=record.getMessage(),
            request_id=request_id.get(),
            session_id=session_id.get(),
            user_id=user_id.get(),
            component=getattr(record, 'component', None),
            operation=getattr(record, 'operation', None),
            duration_ms=getattr(record, 'duration_ms', None),
            extra=getattr(record, 'extra', None)
        )
        
        # Convert to dict and remove None values
        log_dict = {k: v for k, v in asdict(context).items() if v is not None}
        
        # Add exception info if present
        if record.exc_info:
            log_dict['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }
        
        # Add any additional fields from record
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                          'filename', 'module', 'lineno', 'funcName', 'created',
                          'msecs', 'relativeCreated', 'thread', 'threadName',
                          'processName', 'process', 'getMessage', 'exc_info',
                          'exc_text', 'stack_info', 'component', 'operation',
                          'duration_ms', 'extra']:
                log_dict[f'meta_{key}'] = value
        
        return json.dumps(log_dict, ensure_ascii=False, default=str)


class TextFormatter(logging.Formatter):
    """Human-readable text formatter"""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as readable text"""
        timestamp = datetime.fromtimestamp(record.created, tz=timezone.utc)
        
        # Build base message
        parts = [
            timestamp.strftime("%Y-%m-%d %H:%M:%S UTC"),
            f"[{record.levelname}]",
            f"{record.name}:",
            record.getMessage()
        ]
        
        # Add context if available
        req_id = request_id.get()
        if req_id:
            parts.insert(-1, f"req:{req_id[:8]}")
        
        sess_id = session_id.get()
        if sess_id:
            parts.insert(-1, f"sess:{sess_id[:8]}")
        
        component = getattr(record, 'component', None)
        if component:
            parts.insert(-1, f"[{component}]")
        
        duration = getattr(record, 'duration_ms', None)
        if duration:
            parts.append(f"({duration:.2f}ms)")
        
        message = " ".join(parts)
        
        # Add exception info if present
        if record.exc_info:
            message += "\n" + self.formatException(record.exc_info)
        
        return message


class WhisLogger:
    """Enhanced logger with context management and security features"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self._original_level = None
    
    def with_context(self, **kwargs) -> 'WhisLogger':
        """Create logger with additional context"""
        # This creates a new logger instance that will include the context
        # in all subsequent log calls
        new_logger = WhisLogger(self.logger.name)
        new_logger.logger = self.logger
        new_logger._context = kwargs
        return new_logger
    
    def _log_with_context(self, level: int, msg: str, *args, **kwargs):
        """Log message with context"""
        extra = kwargs.get('extra', {})
        
        # Add stored context if available
        if hasattr(self, '_context'):
            extra.update(self._context)
        
        # Add any additional context from kwargs
        for key in ['component', 'operation', 'duration_ms', 'extra']:
            if key in kwargs:
                if key == 'extra':
                    if 'extra' not in extra:
                        extra['extra'] = {}
                    extra['extra'].update(kwargs[key])
                else:
                    extra[key] = kwargs.pop(key)
        
        kwargs['extra'] = extra
        self.logger.log(level, msg, *args, **kwargs)
    
    def debug(self, msg: str, *args, **kwargs):
        """Log debug message"""
        self._log_with_context(logging.DEBUG, msg, *args, **kwargs)
    
    def info(self, msg: str, *args, **kwargs):
        """Log info message"""
        self._log_with_context(logging.INFO, msg, *args, **kwargs)
    
    def warning(self, msg: str, *args, **kwargs):
        """Log warning message"""
        self._log_with_context(logging.WARNING, msg, *args, **kwargs)
    
    def error(self, msg: str, *args, **kwargs):
        """Log error message"""
        self._log_with_context(logging.ERROR, msg, *args, **kwargs)
    
    def critical(self, msg: str, *args, **kwargs):
        """Log critical message"""
        self._log_with_context(logging.CRITICAL, msg, *args, **kwargs)
    
    def exception(self, msg: str, *args, **kwargs):
        """Log exception with traceback"""
        kwargs['exc_info'] = True
        self.error(msg, *args, **kwargs)
    
    def security(self, msg: str, *args, **kwargs):
        """Log security-related event"""
        kwargs['component'] = 'SECURITY'
        self.warning(f"🔒 SECURITY: {msg}", *args, **kwargs)
    
    def audit(self, action: str, resource: str = None, user: str = None, **kwargs):
        """Log audit event"""
        audit_msg = f"AUDIT: {action}"
        if resource:
            audit_msg += f" on {resource}"
        if user:
            audit_msg += f" by {user}"
        
        kwargs['component'] = 'AUDIT'
        kwargs['extra'] = kwargs.get('extra', {})
        kwargs['extra'].update({
            'action': action,
            'resource': resource,
            'user': user
        })
        
        self.info(audit_msg, **kwargs)
    
    def performance(self, operation: str, duration_ms: float, **kwargs):
        """Log performance metrics"""
        kwargs['component'] = 'PERFORMANCE'
        kwargs['operation'] = operation
        kwargs['duration_ms'] = duration_ms
        
        if duration_ms > 5000:  # > 5 seconds
            level = 'warning'
        elif duration_ms > 1000:  # > 1 second
            level = 'info'
        else:
            level = 'debug'
        
        getattr(self, level)(f"⚡ {operation} completed in {duration_ms:.2f}ms", **kwargs)


class LoggingManager:
    """Central logging configuration and management"""
    
    def __init__(self):
        self.configured = False
        self.handlers = {}
        self.loggers = {}
    
    def configure(self, config: Dict[str, Any]):
        """Configure logging from configuration dict"""
        if self.configured:
            return
        
        # Set root log level
        root_level = config.get('level', 'INFO')
        logging.getLogger().setLevel(getattr(logging, root_level))
        
        # Configure formatters
        formatters = {
            'structured': StructuredFormatter(),
            'text': TextFormatter()
        }
        
        # Configure handlers
        handlers_config = config.get('handlers', {})
        
        # Console handler
        if handlers_config.get('console', {}).get('enabled', True):
            console_config = handlers_config['console']
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(getattr(logging, console_config.get('level', 'INFO')))
            
            format_type = console_config.get('format', 'text')
            console_handler.setFormatter(formatters[format_type])
            console_handler.addFilter(SensitiveDataFilter())
            
            logging.getLogger().addHandler(console_handler)
            self.handlers['console'] = console_handler
        
        # File handler
        if handlers_config.get('file', {}).get('enabled', True):
            file_config = handlers_config['file']
            log_path = Path(file_config.get('path', 'logs/whis.log'))
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Use rotating file handler
            file_handler = logging.handlers.RotatingFileHandler(
                log_path,
                maxBytes=self._parse_size(file_config.get('max_size', '100MB')),
                backupCount=file_config.get('backup_count', 5)
            )
            file_handler.setLevel(getattr(logging, file_config.get('level', 'INFO')))
            file_handler.setFormatter(formatters['structured'])
            file_handler.addFilter(SensitiveDataFilter())
            
            logging.getLogger().addHandler(file_handler)
            self.handlers['file'] = file_handler
        
        # Remote handler (e.g., to ELK stack)
        if handlers_config.get('remote', {}).get('enabled', False):
            remote_config = handlers_config['remote']
            # This would integrate with external logging systems
            # Implementation depends on specific remote logging service
            pass
        
        # Configure component-specific loggers
        loggers_config = config.get('loggers', {})
        for logger_name, logger_config in loggers_config.items():
            logger = logging.getLogger(logger_name)
            logger.setLevel(getattr(logging, logger_config.get('level', 'INFO')))
        
        self.configured = True
        logging.info("📝 Logging system configured successfully")
    
    def _parse_size(self, size_str: str) -> int:
        """Parse size string like '100MB' to bytes"""
        size_str = size_str.upper()
        multipliers = {'B': 1, 'KB': 1024, 'MB': 1024**2, 'GB': 1024**3}
        
        for suffix, multiplier in multipliers.items():
            if size_str.endswith(suffix):
                return int(size_str[:-len(suffix)]) * multiplier
        
        return int(size_str)  # Assume bytes if no suffix
    
    def get_logger(self, name: str) -> WhisLogger:
        """Get enhanced logger instance"""
        if name not in self.loggers:
            self.loggers[name] = WhisLogger(name)
        return self.loggers[name]
    
    def set_request_context(self, req_id: str = None, sess_id: str = None, user: str = None):
        """Set request context for correlation"""
        if req_id:
            request_id.set(req_id)
        if sess_id:
            session_id.set(sess_id)
        if user:
            user_id.set(user)
    
    def generate_request_id(self) -> str:
        """Generate new request ID"""
        req_id = str(uuid.uuid4())
        request_id.set(req_id)
        return req_id


# Global logging manager
_logging_manager: Optional[LoggingManager] = None


def get_logging_manager() -> LoggingManager:
    """Get global logging manager"""
    global _logging_manager
    if _logging_manager is None:
        _logging_manager = LoggingManager()
    return _logging_manager


def get_logger(name: str) -> WhisLogger:
    """Get enhanced logger instance"""
    return get_logging_manager().get_logger(name)


def configure_logging(config: Dict[str, Any]):
    """Configure global logging"""
    get_logging_manager().configure(config)


def set_request_context(req_id: str = None, sess_id: str = None, user: str = None):
    """Set request context for correlation"""
    get_logging_manager().set_request_context(req_id, sess_id, user)


def generate_request_id() -> str:
    """Generate and set new request ID"""
    return get_logging_manager().generate_request_id()


# Context managers for scoped logging
class LogContext:
    """Context manager for scoped logging context"""
    
    def __init__(self, **context):
        self.context = context
        self.tokens = {}
    
    def __enter__(self):
        # Set context variables
        for key, value in self.context.items():
            if key == 'request_id':
                self.tokens['request_id'] = request_id.set(value)
            elif key == 'session_id':
                self.tokens['session_id'] = session_id.set(value)
            elif key == 'user_id':
                self.tokens['user_id'] = user_id.set(value)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Reset context variables
        for key, token in self.tokens.items():
            if key == 'request_id':
                request_id.set(token)
            elif key == 'session_id':
                session_id.set(token)
            elif key == 'user_id':
                user_id.set(token)