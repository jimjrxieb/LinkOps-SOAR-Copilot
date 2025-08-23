#!/usr/bin/env python3
"""
🔒 FROZEN API Contract Validators
Immutable schema validation for Whis SOAR-Copilot v1.0
"""

import json
import logging
from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field, validator
from datetime import datetime

logger = logging.getLogger(__name__)

# =============================================================================
# 🔒 FROZEN ACTION SCHEMA v1.0 (IMMUTABLE)
# =============================================================================

class ActionSchemaValidator(BaseModel):
    """
    🔒 FROZEN v1.0: Action Schema for SOAR responses
    
    This schema is IMMUTABLE - breaking changes are NOT allowed.
    Any modifications require a new API version.
    """
    triage_steps: List[str] = Field(
        description="Ordered list of investigation steps",
        min_items=1,
        max_items=10
    )
    containment: List[str] = Field(
        description="Immediate containment actions", 
        min_items=1,
        max_items=8
    )
    remediation: List[str] = Field(
        description="Long-term remediation steps",
        min_items=1,
        max_items=8
    )
    mitre: List[str] = Field(
        description="MITRE ATT&CK technique IDs (T1234 format)",
        min_items=1,
        max_items=5
    )
    spl_query: str = Field(
        description="Splunk search query for investigation",
        min_length=10,
        max_length=1000
    )
    lc_rule: str = Field(
        description="LimaCharlie detection rule",
        default="",
        max_length=500
    )
    k8s_manifest: str = Field(
        description="Kubernetes security manifest",
        default="",
        max_length=2000
    )
    validation_steps: List[str] = Field(
        description="Steps to validate the response",
        min_items=1,
        max_items=6
    )
    citations: List[str] = Field(
        description="Sources and references",
        min_items=1,
        max_items=5
    )
    confidence: float = Field(
        description="Confidence score 0.0-1.0",
        ge=0.0,
        le=1.0
    )
    grounded: bool = Field(
        description="Whether response is grounded in retrieved knowledge"
    )

    @validator('mitre')
    def validate_mitre_format(cls, v):
        """Validate MITRE ATT&CK technique ID format"""
        for technique in v:
            if not technique.startswith('T') or not any(c.isdigit() for c in technique):
                raise ValueError(f"Invalid MITRE technique format: {technique}")
        return v

    @validator('confidence')
    def validate_confidence_precision(cls, v):
        """Ensure confidence is reasonable precision"""
        return round(v, 3)

    class Config:
        schema_extra = {
            "example": {
                "triage_steps": [
                    "Investigate suspicious process on affected system",
                    "Correlate with recent security events",
                    "Validate indicators of compromise"
                ],
                "containment": [
                    "Isolate affected system if confirmed malicious",
                    "Block suspicious network traffic",
                    "Preserve evidence for analysis"
                ],
                "remediation": [
                    "Apply relevant security patches",
                    "Update detection rules",
                    "Implement additional monitoring"
                ],
                "mitre": ["T1055", "T1059.001"],
                "spl_query": "index=security | search suspicious_activity | stats count by host, user",
                "lc_rule": "event_type = \"SUSPICIOUS_PROCESS\"",
                "k8s_manifest": "apiVersion: networking.k8s.io/v1\nkind: NetworkPolicy",
                "validation_steps": [
                    "Verify containment effectiveness",
                    "Confirm remediation steps completed",
                    "Monitor for recurrence"
                ],
                "citations": ["MITRE ATT&CK Framework", "Whis SOAR Knowledge Base"],
                "confidence": 0.85,
                "grounded": True
            }
        }

# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class ExplainRequest(BaseModel):
    """Request model for /explain endpoint"""
    event_data: Dict[str, Any] = Field(description="Security event data")
    
    class Config:
        schema_extra = {
            "example": {
                "event_data": {
                    "search_name": "Suspicious PowerShell Execution",
                    "host": "workstation-01",
                    "user": "alice.smith",
                    "process": "powershell.exe",
                    "timestamp": "2025-08-22T21:30:00Z"
                }
            }
        }

class ExplainResponse(BaseModel):
    """Response model for /explain endpoint"""
    action_schema: ActionSchemaValidator
    response_id: str = Field(description="Unique response identifier")
    timestamp: str = Field(description="Response timestamp")
    model_version: str = Field(description="Model version used")
    processing_time_ms: int = Field(description="Processing time in milliseconds")
    chunks_retrieved: int = Field(description="Number of RAG chunks retrieved")
    retrieval_score: float = Field(description="RAG retrieval confidence score")

class ScoreRequest(BaseModel):
    """Request model for /score endpoint"""
    response_id: str = Field(description="Response ID to score")
    action_schema: ActionSchemaValidator = Field(description="Action schema to evaluate")
    ground_truth: Optional[ActionSchemaValidator] = Field(
        description="Ground truth for comparison (optional)",
        default=None
    )

class ScoreResponse(BaseModel):
    """Response model for /score endpoint"""
    overall_score: float = Field(description="Overall quality score 0.0-1.0", ge=0.0, le=1.0)
    dimension_scores: Dict[str, float] = Field(description="Per-dimension scores")
    feedback: List[str] = Field(description="Specific feedback points")
    schema_valid: bool = Field(description="Whether schema validation passed")
    grounding_verified: bool = Field(description="Whether grounding claims verified")

class ChatRequest(BaseModel):
    """Request model for /chat endpoint"""
    message: str = Field(description="Chat message", min_length=1, max_length=1000)
    conversation_id: Optional[str] = Field(description="Conversation ID", default=None)

class ChatResponse(BaseModel):
    """Response model for /chat endpoint"""
    message: str = Field(description="Chat response message")
    action_schema: Optional[ActionSchemaValidator] = Field(
        description="Action schema if applicable",
        default=None
    )
    conversation_id: str = Field(description="Conversation ID")

# =============================================================================
# VALIDATION FUNCTIONS
# =============================================================================

def validate_action_schema(data: Dict[str, Any]) -> ActionSchemaValidator:
    """
    Validate and auto-repair Action Schema
    
    Returns validated schema or raises ValidationError
    """
    try:
        # First validation attempt
        return ActionSchemaValidator(**data)
    except Exception as e:
        logger.warning(f"Schema validation failed, attempting repair: {e}")
        
        # Auto-repair attempt
        repaired_data = auto_repair_schema(data)
        try:
            return ActionSchemaValidator(**repaired_data)
        except Exception as repair_error:
            logger.error(f"Schema auto-repair failed: {repair_error}")
            raise ValueError(f"Schema validation failed: {repair_error}")

def auto_repair_schema(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Auto-repair common schema issues
    
    - Ensure required fields exist with defaults
    - Convert types where possible  
    - Fix MITRE format issues
    """
    repaired = data.copy()
    
    # Ensure required list fields exist
    list_fields = ["triage_steps", "containment", "remediation", "mitre", "validation_steps", "citations"]
    for field in list_fields:
        if field not in repaired or not isinstance(repaired[field], list):
            repaired[field] = [f"Generated {field.replace('_', ' ')}"]
    
    # Ensure string fields exist
    string_fields = {"spl_query": "", "lc_rule": "", "k8s_manifest": ""}
    for field, default in string_fields.items():
        if field not in repaired:
            repaired[field] = default
    
    # Fix confidence score
    if "confidence" not in repaired or not isinstance(repaired["confidence"], (int, float)):
        repaired["confidence"] = 0.7
    else:
        repaired["confidence"] = max(0.0, min(1.0, float(repaired["confidence"])))
    
    # Fix grounded boolean
    if "grounded" not in repaired:
        repaired["grounded"] = len(repaired.get("citations", [])) > 0
    
    # Fix MITRE format
    if "mitre" in repaired:
        fixed_mitre = []
        for technique in repaired["mitre"]:
            if isinstance(technique, str) and technique:
                if not technique.startswith("T"):
                    technique = f"T{technique}"
                fixed_mitre.append(technique)
        repaired["mitre"] = fixed_mitre or ["T1000"]
    
    return repaired

def validate_security_input(data: Dict[str, Any]) -> bool:
    """
    Security validation for input data
    
    Checks for potential injection attempts, oversized data, etc.
    """
    # Size limits
    data_str = json.dumps(data)
    if len(data_str) > 100000:  # 100KB limit
        raise ValueError("Input data exceeds size limit")
    
    # Basic injection detection
    dangerous_patterns = [
        "<script", "javascript:", "eval(", "exec(", 
        "import os", "subprocess", "__import__"
    ]
    
    data_lower = data_str.lower()
    for pattern in dangerous_patterns:
        if pattern in data_lower:
            logger.warning(f"Potentially dangerous pattern detected: {pattern}")
            # Continue but log - don't block legitimate security content
    
    return True

# =============================================================================
# QUALITY GATES
# =============================================================================

QUALITY_GATES = {
    "assistant_score": 0.75,
    "teacher_score": 0.80,
    "safety_score": 1.00,
    "rag_score": 0.75,
    "schema_valid_rate": 0.90,
    "p95_response_time_ms": 3000
}

def check_quality_gates(scores: Dict[str, float]) -> bool:
    """Check if response meets quality gates"""
    for gate, threshold in QUALITY_GATES.items():
        if scores.get(gate, 0.0) < threshold:
            logger.error(f"Quality gate failed: {gate} = {scores.get(gate)} < {threshold}")
            return False
    return True