#!/usr/bin/env python3
"""
📊 Knowledge Gap Schemas & Data Models
======================================
Structured schemas for abstain → notify → learn pipeline

[TAG: SCHEMA] - UnansweredQuestion.v1 data model
[TAG: DATA-LAKE] - Structured storage for knowledge gaps
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from enum import Enum

class AbstainReason(str, Enum):
    """Why WHIS abstained from answering"""
    NO_RAG_HITS = "no_rag_hits"
    LOW_CONFIDENCE = "low_confidence" 
    NO_CITATIONS = "no_citations"
    GLOSSARY_MISS = "glossary_miss"
    TOOL_FAILURE = "tool_failure"
    POLICY_BLOCK = "policy_block"
    INCOMPLETE_CONTEXT = "incomplete_context"

class IntentCategory(str, Enum):
    """Query intent classification"""
    DEFINITION = "definition"
    HOW_TO = "how_to"
    TROUBLESHOOTING = "troubleshooting"
    ANALYSIS = "analysis"
    CONFIGURATION = "configuration"
    INVESTIGATION = "investigation"
    UNKNOWN = "unknown"

class ApprovalState(str, Enum):
    """Knowledge gap review status"""
    PENDING = "pending"
    REVIEWED = "reviewed"
    PROMOTED = "promoted"
    DISMISSED = "dismissed"
    ESCALATED = "escalated"

class RAGHitMeta(BaseModel):
    """Metadata about RAG retrieval attempts"""
    doc_title: str
    score: float
    chunk_id: str
    source_type: str  # playbook, glossary, incident, etc.
    excerpt: str = Field(max_length=200)

class PIIRedactionSummary(BaseModel):
    """Summary of PII redaction applied"""
    patterns_found: List[str] = Field(default_factory=list)
    redaction_count: int = 0
    safe_for_external: bool = True
    redaction_version: str = "1.0.0"

class UnansweredQuestionV1(BaseModel):
    """
    Schema for questions WHIS couldn't answer confidently
    
    [TAG: DATA-LAKE] - Primary storage schema
    [TAG: GOVERNANCE] - PII redaction enforced
    """
    
    # Identity & Context
    id: str = Field(description="Unique question ID")
    timestamp: datetime = Field(description="When question was asked")
    tenant: str = Field(default="default", description="Multi-tenant identifier")
    channel: str = Field(description="Source channel (chat, slack, api)")
    user_hash: str = Field(description="Anonymized user identifier")
    session_id: Optional[str] = Field(None, description="Chat session context")
    
    # Question Details
    query_text_redacted: str = Field(description="User question with PII removed")
    query_hash: str = Field(description="Hash for deduplication")
    intent: IntentCategory = Field(description="Classified question intent")
    tokens: int = Field(description="Token count of original query")
    language: str = Field(default="en", description="Query language")
    
    # Abstain Context
    why_abstained: AbstainReason = Field(description="Primary reason for abstaining")
    confidence_score: float = Field(ge=0.0, le=1.0, description="WHIS confidence level")
    
    # RAG & Retrieval
    rag_topk_meta: List[RAGHitMeta] = Field(default_factory=list, description="Top retrieval results")
    has_citations: bool = Field(description="Whether any citations were found")
    corpus_versions: Dict[str, str] = Field(default_factory=dict, description="Knowledge base versions used")
    
    # Technical Context
    environment: str = Field(description="prod, staging, dev")
    model_version: str = Field(description="WHIS model version")
    latency_ms: float = Field(description="Response time in milliseconds")
    gpu_ms: Optional[float] = Field(None, description="GPU compute time if applicable")
    
    # Privacy & Governance
    pii_redaction: PIIRedactionSummary = Field(description="PII handling summary")
    
    # Review & Resolution
    approval_state: ApprovalState = Field(default=ApprovalState.PENDING)
    reviewer_id: Optional[str] = Field(None, description="Who reviewed this gap")
    reviewed_at: Optional[datetime] = Field(None, description="When reviewed")
    resolution_notes: Optional[str] = Field(None, description="Review outcome notes")
    promoted_to_glossary: bool = Field(default=False, description="Added to knowledge base")
    
    # External Escalation (Optional)
    teacher_escalated: bool = Field(default=False, description="Sent to teacher model")
    teacher_response: Optional[str] = Field(None, description="Draft response from teacher")
    
    class Config:
        """Pydantic configuration"""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class KnowledgeGapAlert(BaseModel):
    """
    Slack/notification alert for knowledge gaps
    
    [TAG: SLACK-ALERT] - Notification payload
    """
    
    gap_id: str
    timestamp: str
    query_preview: str = Field(max_length=100, description="Truncated question")
    why_abstained: AbstainReason
    intent: IntentCategory
    confidence_score: float
    tenant: str
    channel: str
    
    # Context for triage
    top_k_titles: List[str] = Field(max_length=3, description="Closest matching docs")
    corpus_version: str
    trace_id: str
    
    # Action buttons
    actions: List[Dict[str, str]] = Field(default_factory=lambda: [
        {"type": "button", "text": "View in Console", "action": "view_console"},
        {"type": "button", "text": "Promote to Teacher", "action": "escalate_teacher"},
        {"type": "button", "text": "Dismiss", "action": "dismiss"}
    ])

class TeacherEscalationRequest(BaseModel):
    """
    Request to external teacher model (GPT-5)
    
    [TAG: ESCALATION-POLICY] - Gated external model access
    """
    
    escalation_id: str
    gap_id: str
    query_redacted: str
    intent: IntentCategory
    
    # Safe context only
    top_k_excerpts: List[str] = Field(max_length=5, description="Relevant doc excerpts")
    corpus_context: str = Field(max_length=500, description="Safe background context")
    
    # Constraints
    max_tokens: int = Field(default=80, le=150)
    require_source_binding: bool = Field(default=True)
    
    # Governance
    tenant_approved: bool = Field(description="Tenant opted into external escalation")
    pii_redaction_passed: bool = Field(description="Passed PII safety check")
    cost_approved: bool = Field(description="Within cost limits")

class TeacherResponse(BaseModel):
    """
    Response from teacher model
    
    [TAG: TEACHER-RESPONSE] - External model output
    """
    
    escalation_id: str
    teacher_model: str = Field(description="Which teacher model was used")
    response_text: str = Field(max_length=300, description="Draft response")
    suggested_glossary_location: Optional[str] = Field(None, description="Where this should live in corpus")
    confidence: float = Field(ge=0.0, le=1.0)
    
    # Audit trail
    tokens_used: int
    cost_cents: int
    response_hash: str = Field(description="Hash for audit (no content stored)")
    generated_at: datetime

class GlossaryPromotionRequest(BaseModel):
    """
    Request to promote gap resolution to glossary
    
    [TAG: CONSOLE-REVIEW] - Human review workflow
    """
    
    gap_id: str
    reviewer_id: str
    
    # Content
    glossary_term: str
    definition: str = Field(max_length=500)
    location: str = Field(description="File path in core_glossary/")
    tags: List[str] = Field(default_factory=list)
    
    # Validation
    smoke_eval_passed: bool = Field(description="Automated eval passed")
    citations_included: bool = Field(description="Has proper citations")
    
class KnowledgeGapMetrics(BaseModel):
    """
    Metrics for knowledge gap tracking
    
    [TAG: DASHBOARD-TILE] - Observability data
    """
    
    timestamp: datetime
    window_hours: int = Field(default=24)
    
    # Core metrics
    total_queries: int
    gaps_count: int
    gap_rate: float = Field(ge=0.0, le=1.0, description="gaps/total_queries")
    
    # By category
    gaps_by_intent: Dict[IntentCategory, int] = Field(default_factory=dict)
    gaps_by_reason: Dict[AbstainReason, int] = Field(default_factory=dict)
    
    # Resolution metrics
    pending_review: int
    promoted_count: int
    dismissed_count: int
    avg_time_to_resolution_hours: Optional[float] = None
    
    # Teacher model usage (if enabled)
    teacher_escalations: int = 0
    teacher_success_rate: float = 0.0
    
class DataLakePartition(BaseModel):
    """
    Data lake partitioning scheme
    
    [TAG: CATALOG] - Storage organization
    """
    
    date: str = Field(pattern=r"\d{4}-\d{2}-\d{2}", description="YYYY-MM-DD")
    tenant: str
    intent: IntentCategory
    
    # Statistics
    record_count: int
    total_size_bytes: int
    last_updated: datetime
    
    # Data quality
    pii_redaction_failures: int = 0
    quarantined_records: int = 0

# Constants and Configuration
CONFIDENCE_GATE_THRESHOLD = 0.6  # Below this = abstain
MAX_RAG_HITS_TO_STORE = 5  # Limit metadata storage
MAX_QUERY_LENGTH_CHARS = 1000  # Prevent abuse
PII_PATTERNS = [
    r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
    r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
    r'\b(?:\d{4}[-\s]?){3}\d{4}\b',  # Credit card
]

# Export all schemas
__all__ = [
    'UnansweredQuestionV1',
    'KnowledgeGapAlert', 
    'TeacherEscalationRequest',
    'TeacherResponse',
    'GlossaryPromotionRequest',
    'KnowledgeGapMetrics',
    'AbstainReason',
    'IntentCategory',
    'ApprovalState'
]