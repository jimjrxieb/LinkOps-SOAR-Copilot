#!/usr/bin/env python3
"""
🎯 Whis SOAR API - Pydantic Schemas & Contracts
==================================================
TAGS: #api-contracts #pydantic-schemas #input-validation

Defines all API request/response models with validation.
Contracts over vibes - every endpoint has strict typing.

Security Features:
- Input validation with Pydantic
- Automatic data sanitization  
- Type safety with generics
- Documentation generation
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Union, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator, root_validator
from pydantic.types import constr, confloat, conint

# ==============================================================================
# 🔒 Base Models & Security
# ==============================================================================

class WhisBaseModel(BaseModel):
    """Base model with common security and validation features"""
    
    class Config:
        # Security settings
        validate_assignment = True  # Validate on assignment
        use_enum_values = True     # Use enum values in JSON
        populate_by_name = True    # Updated for Pydantic v2
        
        # Performance settings  
        validate_default = True    # Updated for Pydantic v2
        extra = "forbid"  # Reject unknown fields
        
        # JSON encoding
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }

    @validator('*', pre=True)
    def sanitize_strings(cls, v):
        """Basic string sanitization"""
        if isinstance(v, str):
            # Remove potential script injection
            v = v.replace('<script', '&lt;script')
            v = v.replace('</script>', '&lt;/script&gt;')
            # Limit length
            if len(v) > 10000:
                v = v[:10000] + "... [truncated]"
        return v

class CorrelationMixin(BaseModel):
    """Mixin for correlation ID tracking"""
    correlation_id: Optional[str] = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique request correlation ID for tracing"
    )

# ==============================================================================
# 🔍 Explain Endpoint Schemas
# ==============================================================================

class SecurityEventData(WhisBaseModel):
    """Security event data structure"""
    
    # Required fields
    search_name: constr(min_length=1, max_length=200) = Field(
        ..., 
        description="Security alert or event name",
        example="APT29 Lateral Movement Detected"
    )
    
    host: constr(min_length=1, max_length=100) = Field(
        ...,
        description="Affected host or system",
        example="DC01-PROD"
    )
    
    description: constr(min_length=10, max_length=5000) = Field(
        ...,
        description="Detailed event description",
        example="PowerShell Empire C2 beacon detected with credential dumping activity"
    )
    
    # Optional enrichment fields
    severity: Optional[Literal["low", "medium", "high", "critical"]] = Field(
        default="medium",
        description="Event severity level"
    )
    
    user: Optional[constr(max_length=100)] = Field(
        default=None,
        description="Associated user account",
        example="DOMAIN\\admin"
    )
    
    source_ip: Optional[constr(pattern=r'^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$')] = Field(
        default=None,
        description="Source IP address",
        example="10.0.1.15"
    )
    
    dest_ip: Optional[constr(pattern=r'^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$')] = Field(
        default=None,
        description="Destination IP address", 
        example="10.0.1.10"
    )
    
    process: Optional[constr(max_length=200)] = Field(
        default=None,
        description="Process name or path",
        example="powershell.exe"
    )
    
    command_line: Optional[constr(max_length=2000)] = Field(
        default=None,
        description="Command line arguments"
    )
    
    mitre_techniques: Optional[List[constr(pattern=r'^T\d{4}(\.\d{3})?$')]] = Field(
        default=[],
        description="MITRE ATT&CK technique IDs",
        example=["T1003.001", "T1059.001"]
    )
    
    timestamp: Optional[datetime] = Field(
        default_factory=datetime.now,
        description="Event timestamp"
    )
    
    # Metadata fields
    index: Optional[str] = Field(default=None, description="SIEM index name")
    sourcetype: Optional[str] = Field(default=None, description="SIEM source type")
    confidence: Optional[confloat(ge=0.0, le=1.0)] = Field(
        default=None, 
        description="Detection confidence score"
    )

class ExplainRequest(CorrelationMixin):
    """Request schema for /explain endpoint"""
    
    event_data: SecurityEventData = Field(
        ...,
        description="Security event data to analyze"
    )
    
    # Optional request parameters
    include_citations: bool = Field(
        default=True,
        description="Include RAG citations in response"
    )
    
    rag_k: Optional[conint(ge=1, le=20)] = Field(
        default=6,
        description="Number of RAG chunks to retrieve"
    )
    
    domains: Optional[List[Literal["nist_core", "nist_delta", "vendor_task", "k8s_security", "siem_patterns", "guardpoint"]]] = Field(
        default=["nist_core", "siem_patterns"],
        description="RAG domains to search"
    )

class ActionSchema(WhisBaseModel):
    """Generated Action Schema response structure"""
    
    # NIST Framework alignment
    nist_functions: List[Literal["Identify", "Protect", "Detect", "Respond", "Recover"]] = Field(
        ...,
        description="Relevant NIST Cybersecurity Framework functions"
    )
    
    nist_categories: List[str] = Field(
        ...,
        description="NIST categories (e.g., ID.AM, PR.AC)",
        example=["ID.AM-1", "DE.CM-1", "RS.AN-1"]
    )
    
    # MITRE ATT&CK mapping
    mitre: List[Dict[str, Any]] = Field(
        default=[],
        description="MITRE ATT&CK techniques with context",
        example=[
            {
                "technique_id": "T1003.001", 
                "technique_name": "OS Credential Dumping: LSASS Memory",
                "tactic": "Credential Access",
                "severity": "high"
            }
        ]
    )
    
    # Triage and response
    triage_steps: List[str] = Field(
        ...,
        description="Ordered triage and investigation steps",
        min_items=1
    )
    
    recommendations: List[str] = Field(
        ..., 
        description="Security recommendations and countermeasures",
        min_items=1
    )
    
    # Risk assessment
    risk_score: confloat(ge=0.0, le=10.0) = Field(
        ...,
        description="Calculated risk score (0-10 scale)"
    )
    
    confidence: confloat(ge=0.0, le=1.0) = Field(
        ...,
        description="AI confidence in the analysis"
    )
    
    # Integration outputs
    spl_query: Optional[str] = Field(
        default=None,
        description="Generated Splunk SPL query for hunting"
    )
    
    lc_rule: Optional[str] = Field(
        default=None, 
        description="Generated LimaCharlie detection rule"
    )
    
    # Metadata
    processing_time_ms: Optional[confloat(ge=0)] = Field(
        default=None,
        description="Processing time in milliseconds"
    )

class Citation(WhisBaseModel):
    """RAG citation with source tracking"""
    
    source: str = Field(..., description="Source document name")
    shard: str = Field(..., description="RAG shard name")
    chunk_id: str = Field(..., description="Unique chunk identifier")
    relevance_score: confloat(ge=0.0, le=1.0) = Field(..., description="Relevance score")
    content: constr(max_length=1000) = Field(..., description="Cited content")
    page_ref: Optional[Union[int, List[int]]] = Field(default=None, description="Page reference")

class ModelBOM(WhisBaseModel):
    """Model Bill of Materials for response tracking"""
    
    whis_model: str = Field(..., description="Whis model identifier")
    base_model: str = Field(..., description="Base LLM model")
    rag_version: str = Field(..., description="RAG index version")
    adapter_id: Optional[str] = Field(default=None, description="Fine-tuned adapter ID")
    context_chunks: Optional[int] = Field(default=None, description="Number of RAG chunks used")

class ExplainResponse(CorrelationMixin):
    """Response schema for /explain endpoint"""
    
    action_schema: ActionSchema = Field(
        ...,
        description="Generated Action Schema with analysis"
    )
    
    citations: List[Citation] = Field(
        default=[],
        description="RAG citations supporting the analysis"
    )
    
    processing_time_ms: confloat(ge=0) = Field(
        ...,
        description="Total processing time in milliseconds"
    )
    
    model_bom: ModelBOM = Field(
        ...,
        description="Model bill of materials for traceability"
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Response generation timestamp"
    )

# ==============================================================================
# 🔧 HOW Endpoint Schemas  
# ==============================================================================

class HOWRequest(CorrelationMixin):
    """Request schema for /how endpoint"""
    
    prompt: constr(min_length=10, max_length=1000) = Field(
        ...,
        description="Natural language request for infrastructure automation",
        example="Enable certificate authority pilot for staging environment"
    )
    
    environment: Optional[Literal["dev", "staging", "prod"]] = Field(
        default="staging",
        description="Target environment for deployment"
    )
    
    validate_artifacts: bool = Field(
        default=True,
        description="Run validation on generated artifacts"
    )
    
    security_scan: bool = Field(
        default=True,
        description="Perform security scanning on artifacts"
    )

class HOWStep(WhisBaseModel):
    """Individual implementation step"""
    
    step: str = Field(..., description="Step description")
    type: Literal["terraform", "k8s_manifest", "vault_config", "script", "manual"] = Field(
        ..., 
        description="Artifact type"
    )
    dependencies: List[str] = Field(
        default=[],
        description="Dependencies on other steps"
    )
    estimated_time: Optional[str] = Field(
        default=None,
        description="Estimated completion time"
    )

class HOWArtifact(WhisBaseModel):
    """Generated infrastructure artifact"""
    
    name: str = Field(..., description="Artifact filename")
    type: Literal["terraform", "k8s_manifest", "vault_policy", "script", "runbook"] = Field(
        ...,
        description="Artifact type"
    )
    content: str = Field(..., description="Artifact content")
    checksum: str = Field(..., description="Content checksum for integrity")
    
class HOWValidation(WhisBaseModel):
    """Artifact validation result"""
    
    validator: str = Field(..., description="Validator name")
    status: Literal["passed", "failed", "warning"] = Field(..., description="Validation status")
    message: Optional[str] = Field(default=None, description="Validation message")
    details: Optional[Dict[str, Any]] = Field(default={}, description="Detailed results")

class HOWResponse(CorrelationMixin):
    """Response schema for /how endpoint"""
    
    plan: List[HOWStep] = Field(
        ...,
        description="Implementation plan with ordered steps"
    )
    
    artifacts: List[HOWArtifact] = Field(
        ...,
        description="Generated infrastructure artifacts",
        min_items=1
    )
    
    validations: List[HOWValidation] = Field(
        default=[],
        description="Artifact validation results"
    )
    
    rollback_plan: str = Field(
        ...,
        description="Automated rollback procedure"
    )
    
    processing_time_ms: confloat(ge=0) = Field(
        ...,
        description="Processing time in milliseconds"
    )
    
    model_bom: Dict[str, str] = Field(
        ...,
        description="HOW engine model information"
    )

# ==============================================================================
# 📊 Score Endpoint Schemas
# ==============================================================================

class ScoreRequest(CorrelationMixin):
    """Request schema for /score endpoint"""
    
    question: str = Field(..., description="Original question or prompt")
    candidate_answer: str = Field(..., description="Answer to evaluate")
    reference_answer: Optional[str] = Field(default=None, description="Ground truth answer")
    context: Optional[List[str]] = Field(default=[], description="Context used for answer")

class ScoreResponse(CorrelationMixin):
    """Response schema for /score endpoint"""
    
    scores: Dict[str, confloat(ge=0.0, le=1.0)] = Field(
        ...,
        description="Score breakdown by dimension"
    )
    
    explanation: str = Field(
        ...,
        description="Human-readable explanation of scores"
    )
    
    processing_time_ms: confloat(ge=0) = Field(
        ..., 
        description="Processing time in milliseconds"
    )

# ==============================================================================
# 🏥 Health Endpoint Schemas
# ==============================================================================

class DependencyStatus(WhisBaseModel):
    """Individual dependency health status"""
    
    status: Literal["healthy", "degraded", "unhealthy"] = Field(..., description="Health status")
    last_check: Optional[datetime] = Field(default=None, description="Last health check")
    response_time_ms: Optional[float] = Field(default=None, description="Response time")
    details: Dict[str, Any] = Field(default={}, description="Additional status details")

class HealthResponse(WhisBaseModel):
    """Response schema for /health endpoint"""
    
    status: Literal["healthy", "degraded", "unhealthy"] = Field(
        ...,
        description="Overall system health"
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Health check timestamp"
    )
    
    version: str = Field(..., description="API version")
    
    dependencies: Dict[str, Any] = Field(
        default={},
        description="Dependency health status"
    )
    
    model_bom: Dict[str, Any] = Field(
        default={},
        description="Model bill of materials"
    )
    
    uptime_seconds: Optional[float] = Field(
        default=None,
        description="Service uptime in seconds"
    )

# ==============================================================================
# 🚨 SOAR Incident Normalization & Automation
# ==============================================================================

class AssetMetadata(WhisBaseModel):
    """Asset classification and metadata"""
    host: str = Field(..., description="Host identifier")
    user: Optional[str] = Field(default=None, description="Associated user")
    tenant: Optional[str] = Field(default=None, description="Tenant/organization")
    asset_class: Literal["workstation", "server", "domain_controller", "database", "network_device"] = Field(
        default="workstation",
        description="Asset classification for policy gates"
    )
    environment: Literal["dev", "staging", "prod"] = Field(
        default="prod",
        description="Environment classification"
    )
    criticality: Literal["low", "medium", "high", "critical"] = Field(
        default="medium",
        description="Asset criticality level"
    )

class ArtifactData(WhisBaseModel):
    """Security artifacts extracted from events"""
    event_id: Optional[str] = Field(default=None, description="SIEM event ID")
    hash: Optional[constr(pattern=r'^[a-fA-F0-9]{32,64}$')] = Field(default=None, description="File hash")
    ip_addresses: List[constr(pattern=r'^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$')] = Field(
        default=[], description="IP addresses involved"
    )
    urls: List[str] = Field(default=[], description="URLs/domains involved")
    processes: List[str] = Field(default=[], description="Processes involved")
    files: List[str] = Field(default=[], description="Files involved")

class IncidentEvent(WhisBaseModel):
    """Normalized incident event schema - core SOAR data structure"""
    
    # Source identification
    source: Literal["splunk", "limacharlie", "manual"] = Field(..., description="Alert source system")
    rule_id: str = Field(..., description="Detection rule identifier")
    
    # Core event data
    title: constr(min_length=1, max_length=200) = Field(..., description="Incident title")
    description: constr(min_length=10, max_length=5000) = Field(..., description="Detailed description")
    severity: Literal["low", "medium", "high", "critical"] = Field(..., description="Incident severity")
    
    # MITRE ATT&CK mapping
    tactic: Optional[str] = Field(default=None, description="Primary MITRE tactic")
    techniques: List[constr(pattern=r'^T\d{4}(\.\d{3})?$')] = Field(
        default=[], description="MITRE technique IDs"
    )
    
    # Asset and artifact data
    asset: AssetMetadata = Field(..., description="Affected asset metadata")
    artifacts: ArtifactData = Field(default_factory=ArtifactData, description="Security artifacts")
    
    # Temporal data
    first_seen: datetime = Field(..., description="First occurrence timestamp")
    last_seen: datetime = Field(..., description="Last occurrence timestamp")
    
    # Confidence and quality
    confidence: confloat(ge=0.0, le=1.0) = Field(..., description="Detection confidence")
    
    # Raw data pointer (never execute/template this)
    raw_pointer: Optional[str] = Field(
        default=None, 
        description="Reference to raw alert data - NEVER use in prompts or templates"
    )

class RunbookAction(WhisBaseModel):
    """Individual runbook action with guardrails"""
    id: str = Field(..., description="Action identifier")
    tool: str = Field(..., description="Tool name (e.g., edr.isolate_host)")
    description: str = Field(..., description="Human-readable action description")
    args: Dict[str, Any] = Field(default={}, description="Tool arguments")
    preconditions: List[str] = Field(default=[], description="Required preconditions")
    postconditions: List[str] = Field(default=[], description="Expected postconditions")
    autonomy_level: Literal["L0", "L1", "L2", "L3"] = Field(..., description="Required autonomy level")
    timeout_seconds: int = Field(default=300, description="Action timeout")
    rollback_action: Optional[str] = Field(default=None, description="Rollback action ID")

class RunbookDefinition(WhisBaseModel):
    """SOAR runbook definition"""
    id: str = Field(..., pattern=r'^RB-\d{3}$', description="Runbook ID (RB-XXX)")
    name: str = Field(..., description="Runbook name")
    mitre_techniques: List[str] = Field(..., description="Applicable MITRE techniques")
    category: str = Field(..., description="Incident category")
    
    # Input requirements
    required_inputs: List[str] = Field(default=[], description="Required input fields")
    asset_class_filter: Optional[List[str]] = Field(default=None, description="Applicable asset classes")
    
    # Actions and conditions
    actions: List[RunbookAction] = Field(..., description="Ordered actions to execute")
    global_preconditions: List[str] = Field(default=[], description="Global preconditions")
    global_postconditions: List[str] = Field(default=[], description="Global postconditions")

class AutonomyPolicy(WhisBaseModel):
    """Autonomy level configuration"""
    level: Literal["L0", "L1", "L2", "L3"] = Field(..., description="Autonomy level")
    description: str = Field(..., description="Level description")
    allowed_tools: List[str] = Field(..., description="Allowed tool patterns")
    requires_approval: bool = Field(..., description="Requires human approval")
    asset_class_restrictions: List[str] = Field(default=[], description="Restricted asset classes")
    max_blast_radius: int = Field(..., description="Maximum affected assets")

class SafetyGate(WhisBaseModel):
    """Safety gate configuration"""
    name: str = Field(..., description="Gate name")
    condition: str = Field(..., description="Gate condition (Python expression)")
    message: str = Field(..., description="Block message")
    exemption_roles: List[str] = Field(default=[], description="Roles that can exempt")

class SOARDecision(WhisBaseModel):
    """SOAR decision graph result"""
    incident_id: str = Field(..., description="Incident identifier")
    category: str = Field(..., description="Classified incident category")
    runbook_id: str = Field(..., description="Selected runbook")
    confidence: confloat(ge=0.0, le=1.0) = Field(..., description="Decision confidence")
    reasoning: str = Field(..., description="Decision reasoning")
    planned_actions: List[RunbookAction] = Field(..., description="Actions to execute")
    safety_gates_triggered: List[str] = Field(default=[], description="Triggered safety gates")
    requires_approval: bool = Field(..., description="Requires human approval")

class ActionResult(WhisBaseModel):
    """Result of a runbook action execution"""
    action_id: str = Field(..., description="Action identifier")
    status: Literal["pending", "running", "success", "failed", "blocked"] = Field(..., description="Execution status")
    start_time: Optional[datetime] = Field(default=None, description="Start timestamp")
    end_time: Optional[datetime] = Field(default=None, description="End timestamp")
    
    # Execution details
    dry_run_result: Optional[str] = Field(default=None, description="Dry run plan")
    output: Optional[str] = Field(default=None, description="Action output")
    error: Optional[str] = Field(default=None, description="Error message")
    
    # Verification
    postconditions_verified: bool = Field(default=False, description="Postconditions verified")
    verification_details: Dict[str, Any] = Field(default={}, description="Verification results")

class SOARExecution(WhisBaseModel):
    """SOAR execution state and results"""
    execution_id: str = Field(..., description="Execution identifier")
    incident_id: str = Field(..., description="Associated incident")
    runbook_id: str = Field(..., description="Executed runbook")
    status: Literal["planned", "executing", "completed", "failed", "rolled_back"] = Field(..., description="Execution status")
    
    # Execution tracking
    current_action: Optional[int] = Field(default=None, description="Current action index")
    action_results: List[ActionResult] = Field(default=[], description="Action execution results")
    
    # Approval and overrides
    approval_token: Optional[str] = Field(default=None, description="Approval token")
    approved_by: Optional[str] = Field(default=None, description="Approver identity")
    overrides: List[str] = Field(default=[], description="Applied overrides")
    
    # Timing
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    started_at: Optional[datetime] = Field(default=None, description="Start timestamp")
    completed_at: Optional[datetime] = Field(default=None, description="Completion timestamp")

# ==============================================================================
# 🚨 SOAR API Endpoints
# ==============================================================================

class SOARIngestRequest(CorrelationMixin):
    """Request to ingest and process security incident"""
    incident: IncidentEvent = Field(..., description="Normalized incident event")
    autonomy_level: Optional[Literal["L0", "L1", "L2", "L3"]] = Field(
        default="L0", description="Override autonomy level"
    )
    force_runbook: Optional[str] = Field(default=None, description="Force specific runbook")

class SOARIngestResponse(CorrelationMixin):
    """Response from SOAR incident ingestion"""
    incident_id: str = Field(..., description="Generated incident ID")
    decision: SOARDecision = Field(..., description="SOAR decision result")
    execution: Optional[SOARExecution] = Field(default=None, description="Execution state (if not L0)")
    processing_time_ms: float = Field(..., description="Processing time")

class SOARApprovalRequest(CorrelationMixin):
    """Request to approve SOAR execution"""
    execution_id: str = Field(..., description="Execution to approve")
    approver: str = Field(..., description="Approver identity")
    overrides: List[str] = Field(default=[], description="Safety gate overrides")

class SOARStatusResponse(CorrelationMixin):
    """SOAR execution status response"""
    execution: SOARExecution = Field(..., description="Current execution state")
    next_action: Optional[RunbookAction] = Field(default=None, description="Next planned action")
    can_rollback: bool = Field(default=False, description="Rollback available")

# ==============================================================================
# ❌ Error Response Schemas
# ==============================================================================

class ErrorDetail(WhisBaseModel):
    """Detailed error information"""
    
    type: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    field: Optional[str] = Field(default=None, description="Field that caused error")
    code: Optional[str] = Field(default=None, description="Error code")

class ErrorResponse(WhisBaseModel):
    """Standard error response format"""
    
    error: str = Field(..., description="Error summary")
    details: List[ErrorDetail] = Field(default=[], description="Detailed error information")
    correlation_id: Optional[str] = Field(default=None, description="Request correlation ID")
    timestamp: datetime = Field(default_factory=datetime.now, description="Error timestamp")
    
    class Config:
        schema_extra = {
            "example": {
                "error": "Validation failed",
                "details": [
                    {
                        "type": "value_error",
                        "message": "Field is required",
                        "field": "event_data.search_name"
                    }
                ],
                "correlation_id": "explain-1234567890",
                "timestamp": "2024-02-01T10:00:00Z"
            }
        }