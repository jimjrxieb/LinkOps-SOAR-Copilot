#!/usr/bin/env python3
"""
FROZEN API CONTRACTS - WHIS SOAR COPILOT
Action Schema and validation contracts - DO NOT MODIFY without versioning

🚨 CRITICAL: These schemas are FROZEN for production stability
Any changes require new version endpoints (v2, v3, etc.)
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime
import uuid

# =============================================================================
# FROZEN ACTION SCHEMA v1.0 - Core SOAR Response Format
# =============================================================================

class WhisActionSchema(BaseModel):
    """
    FROZEN v1.0: Standard SOAR action response schema
    Used by /explain, /score, /chat endpoints
    
    🔒 IMMUTABLE: Do not modify field names or types
    """
    # Core Response Fields
    triage_steps: List[str] = Field(
        description="Ordered list of investigation steps",
        example=["Check event logs for anomalies", "Correlate with threat intel"]
    )
    containment: List[str] = Field(
        description="Immediate containment actions",
        example=["Isolate affected host", "Block malicious IP"]
    )
    remediation: List[str] = Field(
        description="Long-term remediation steps", 
        example=["Patch vulnerable service", "Update detection rules"]
    )
    mitre: List[str] = Field(
        description="MITRE ATT&CK technique IDs",
        example=["T1055.012", "T1112"]
    )
    
    # Query Fields
    spl_query: str = Field(
        description="Splunk search query for investigation",
        example="index=security EventCode=4625 | stats count by src_ip"
    )
    lc_rule: str = Field(
        description="LimaCharlie detection rule (optional)",
        default=""
    )
    k8s_manifest: str = Field(
        description="Kubernetes security manifest (optional)",
        default=""
    )
    
    # Validation & Citations
    validation_steps: List[str] = Field(
        description="Steps to validate the response",
        example=["Run SPL query in 24h window", "Confirm IOCs match"]
    )
    citations: List[str] = Field(
        description="Sources and references",
        example=["MITRE ATT&CK T1055.012", "NIST IR Framework"]
    )
    
    # Quality Metadata
    confidence: float = Field(
        description="Confidence score 0.0-1.0",
        ge=0.0,
        le=1.0,
        default=0.8
    )
    grounded: bool = Field(
        description="Whether response is grounded in retrieved knowledge",
        default=True
    )

    @validator('mitre')
    def validate_mitre_format(cls, v):
        """Validate MITRE technique IDs format"""
        for technique in v:
            if not technique.startswith('T') or len(technique) < 5:
                raise ValueError(f"Invalid MITRE technique format: {technique}")
        return v

    @validator('confidence')
    def validate_confidence_range(cls, v):
        """Ensure confidence is in valid range"""
        if not 0.0 <= v <= 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")
        return v

# =============================================================================
# API REQUEST/RESPONSE MODELS
# =============================================================================

class ExplainRequest(BaseModel):
    """Request model for /explain endpoint"""
    event_data: Dict[str, Any] = Field(
        description="Raw event data from SIEM/EDR"
    )
    context: Optional[Dict[str, Any]] = Field(
        description="Additional context (host, user, environment)",
        default={}
    )
    mode: Literal["assistant", "teacher"] = Field(
        description="Response mode",
        default="assistant"
    )

class ExplainResponse(BaseModel):
    """Response model for /explain endpoint"""
    # Core Action Schema
    action_schema: WhisActionSchema
    
    # Response Metadata
    response_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.now)
    model_version: str = Field(default="whis-mega-v1.0")
    processing_time_ms: int = Field(description="Response generation time")
    
    # Retrieval Info
    chunks_retrieved: int = Field(description="Number of knowledge chunks used")
    retrieval_score: float = Field(description="Quality of retrieved context")

class ScoreRequest(BaseModel):
    """Request model for /score endpoint - Golden Set evaluation"""
    candidate_response: WhisActionSchema
    golden_reference: WhisActionSchema
    evaluation_criteria: Optional[List[str]] = Field(
        default=["completeness", "accuracy", "actionability"]
    )

class ScoreResponse(BaseModel):
    """Response model for /score endpoint"""
    overall_score: float = Field(ge=0.0, le=1.0)
    dimension_scores: Dict[str, float] = Field(
        description="Scores by evaluation dimension"
    )
    feedback: List[str] = Field(
        description="Specific feedback on gaps/improvements"
    )
    
class ChatRequest(BaseModel):
    """Request model for /chat endpoint - General SecOps chat"""
    message: str = Field(description="User message/question")
    context: Optional[Dict[str, Any]] = Field(default={})
    conversation_id: Optional[str] = Field(default=None)

class ChatResponse(BaseModel):
    """Response model for /chat endpoint"""
    message: str = Field(description="Chat response")
    action_schema: Optional[WhisActionSchema] = Field(
        description="Structured action if applicable",
        default=None
    )
    conversation_id: str
    timestamp: datetime = Field(default_factory=datetime.now)

# =============================================================================
# NORMALIZATION SCHEMAS - Unified Event Format
# =============================================================================

class NormalizedEvent(BaseModel):
    """
    Unified event schema for all SIEM/EDR sources
    Abstraction layer over Splunk, LimaCharlie, etc.
    """
    # Event Identity
    event_id: str = Field(description="Unique event identifier")
    source: Literal["splunk", "limacharlie", "manual"] = Field(
        description="Event source system"
    )
    correlation_id: str = Field(
        description="Cross-system correlation identifier"
    )
    
    # Core Event Data  
    timestamp: datetime
    host: Optional[str] = Field(description="Affected host/endpoint")
    user: Optional[str] = Field(description="Affected user account")
    category: str = Field(description="Event category/type")
    severity: Literal["low", "medium", "high", "critical"] = Field(
        default="medium"
    )
    
    # Event Details
    title: str = Field(description="Human readable event title")
    description: str = Field(description="Event description/summary")
    artifacts: List[Dict[str, Any]] = Field(
        description="IOCs, file hashes, IPs, etc.",
        default=[]
    )
    evidence: List[Dict[str, Any]] = Field(
        description="Supporting evidence and context",
        default=[]
    )
    
    # Source-Specific Data
    raw_data: Dict[str, Any] = Field(
        description="Original event data from source"
    )

# =============================================================================
# ENRICHMENT SCHEMAS - Response Tracking
# =============================================================================

class EnrichmentResponse(BaseModel):
    """Schema for enrichment events posted back to SIEM"""
    original_event_id: str
    correlation_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    
    # Processing Results
    whis_response: WhisActionSchema
    processing_time_ms: int
    model_version: str = Field(default="whis-mega-v1.0")
    
    # Quality Metrics
    confidence: float
    grounded: bool
    schema_valid: bool = Field(default=True)
    
    # Retrieval Details
    chunks_used: int
    retrieval_quality: float

# =============================================================================
# ERROR SCHEMAS
# =============================================================================

class ErrorResponse(BaseModel):
    """Standard error response format"""
    error_code: str = Field(description="Machine-readable error code")
    error_message: str = Field(description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(default={})
    timestamp: datetime = Field(default_factory=datetime.now)
    correlation_id: Optional[str] = Field(default=None)

# =============================================================================
# WEBHOOK SCHEMAS - Inbound Event Formats
# =============================================================================

class SplunkWebhookPayload(BaseModel):
    """Splunk notable event webhook payload"""
    search_name: str
    owner: str
    app: str
    result: Dict[str, Any] = Field(description="Splunk event result")
    
    def to_normalized_event(self) -> NormalizedEvent:
        """Convert to unified event format"""
        result = self.result
        return NormalizedEvent(
            event_id=result.get("_key", str(uuid.uuid4())),
            source="splunk",
            correlation_id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            host=result.get("host", "unknown"),
            user=result.get("user", "unknown"), 
            category=self.search_name,
            title=f"Splunk Notable: {self.search_name}",
            description=result.get("_raw", ""),
            raw_data=result
        )

class LimaCharlieWebhookPayload(BaseModel):
    """LimaCharlie detection webhook payload"""
    detect: Dict[str, Any]
    routing: Dict[str, Any]
    
    def to_normalized_event(self) -> NormalizedEvent:
        """Convert to unified event format"""
        detect_data = self.detect
        return NormalizedEvent(
            event_id=detect_data.get("id", str(uuid.uuid4())),
            source="limacharlie",
            correlation_id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            host=self.routing.get("hostname", "unknown"),
            user=detect_data.get("user", "unknown"),
            category=detect_data.get("cat", "unknown"),
            title=f"LC Detection: {detect_data.get('cat')}",
            description=detect_data.get("summary", ""),
            raw_data={"detect": detect_data, "routing": self.routing}
        )