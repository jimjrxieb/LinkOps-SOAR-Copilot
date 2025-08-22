"""
Whis API Routes: Teacher and Assistant endpoints
Implements the core Explain → Propose → Approve → Execute workflow
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import Dict, List, Optional
import logging
from datetime import datetime

from ..engines.whis_engine import get_whis_engine, WhisMode
from ..schemas.detection import Detection, EnrichmentResult
from ..schemas.whis import (
    TeacherRequest, TeacherResponse,
    AssistantRequest, AssistantResponse,
    EnrichmentRequest, ApprovalRequest
)
from ..models.incident import Incident
from ..services.approval_service import ApprovalService
from ..connectors.splunk.hec_client import send_enrichment
from ..core.auth import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/teacher/explain", response_model=TeacherResponse)
async def explain_security_event(
    request: TeacherRequest,
    current_user = Depends(get_current_user),
    whis = Depends(get_whis_engine)
):
    """
    🎓 Teacher Mode: Explain security events with educational context
    
    Example: 4625 failed logons → ATT&CK T1110 explanation + tuning guidance
    """
    try:
        logger.info(f"Teacher request from {current_user.username} for event {request.event_id}")
        
        # Convert request to detection object
        detection = Detection(
            id=f"teacher_{request.event_id}_{int(datetime.now().timestamp())}",
            event_id=request.event_id,
            event_type=request.event_type,
            source_system=request.source_system,
            raw_data=request.event_data,
            severity="informational",  # Teacher mode is educational
            timestamp=datetime.now()
        )
        
        # Get explanation from Whis
        explanation = await whis.explain_event(detection)
        
        # Format response for frontend
        return TeacherResponse(
            mode="teacher",
            event_summary=explanation.event_summary,
            attack_mapping=explanation.attack_mapping,
            false_positive_analysis=explanation.false_positive_analysis,
            threshold_recommendations=explanation.threshold_recommendations,
            best_practices=explanation.best_practices,
            learning_resources=explanation.learning_resources,
            confidence_score=0.85,  # Teacher mode explanations are high confidence
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Teacher mode error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to explain event: {str(e)}")


@router.post("/assistant/propose", response_model=AssistantResponse)  
async def propose_response_actions(
    request: AssistantRequest,
    current_user = Depends(get_current_user),
    whis = Depends(get_whis_engine)
):
    """
    🤖 Assistant Mode: Propose response actions and playbook routing
    
    Example: Confirmed brute force → Account lockdown + investigation playbook
    """
    try:
        logger.info(f"Assistant request from {current_user.username} for detection {request.detection_id}")
        
        # Convert request to detection object
        detection = Detection(
            id=request.detection_id,
            event_id=request.event_id,
            event_type=request.event_type,
            source_system=request.source_system,
            raw_data=request.event_data,
            severity=request.severity,
            timestamp=datetime.now()
        )
        
        # Get proposal from Whis
        proposal = await whis.propose_response(detection)
        
        # Create approval workflow
        approval_service = ApprovalService()
        approval_id = await approval_service.create_approval_request(
            user_id=current_user.id,
            detection_id=detection.id,
            proposed_actions=proposal.proposed_actions,
            playbooks=proposal.recommended_playbooks
        )
        
        # Format response
        return AssistantResponse(
            mode="assistant",
            detection_id=detection.id,
            incident_assessment=proposal.incident_assessment,
            severity_rating=proposal.severity_rating,
            recommended_playbooks=[{
                "id": pb.id,
                "name": pb.name,
                "description": pb.description,
                "estimated_duration": "15-30 minutes"
            } for pb in proposal.recommended_playbooks],
            proposed_actions=[{
                "id": action.id,
                "name": action.name,
                "description": action.description,
                "requires_approval": action.requires_approval,
                "risk_level": "low"
            } for action in proposal.proposed_actions],
            approval_id=approval_id,
            enrichment_context=proposal.enrichment_context,
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Assistant mode error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to propose response: {str(e)}")


@router.post("/enrich")
async def enrich_detection(
    request: EnrichmentRequest,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user),
    whis = Depends(get_whis_engine)
):
    """
    🔍 Detection Enrichment: Add Whis intelligence for SIEM correlation
    
    Enriches detection and sends to Splunk as whis:enrichment
    """
    try:
        logger.info(f"Enrichment request for detection {request.detection_id}")
        
        # Convert to detection object
        detection = Detection(
            id=request.detection_id,
            event_id=request.event_id,
            event_type=request.event_type,
            source_system=request.source_system or "limacharlie",
            raw_data=request.raw_data,
            severity=request.severity,
            timestamp=datetime.now()
        )
        
        # Get enrichment from Whis
        enrichment = await whis.enrich_detection(detection)
        
        # Send to Splunk HEC in background
        if request.send_to_splunk:
            background_tasks.add_task(
                send_enrichment_to_splunk,
                enrichment,
                source="whis:enrichment"
            )
        
        return {
            "status": "enriched",
            "detection_id": detection.id,
            "enrichment": enrichment.enrichment_data,
            "sent_to_splunk": request.send_to_splunk,
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        logger.error(f"Enrichment error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to enrich detection: {str(e)}")


@router.post("/approve/{approval_id}")
async def approve_proposed_actions(
    approval_id: str,
    request: ApprovalRequest,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user)
):
    """
    ✅ Human Approval Gateway: Approve or reject proposed actions
    
    Part of the Explain → Propose → Approve → Execute workflow
    """
    try:
        approval_service = ApprovalService()
        
        # Get approval request
        approval_request = await approval_service.get_approval_request(approval_id)
        if not approval_request:
            raise HTTPException(status_code=404, detail="Approval request not found")
        
        # Process approval/rejection
        if request.approved:
            logger.info(f"User {current_user.username} approved actions for {approval_id}")
            
            # Execute approved actions via SOAR
            background_tasks.add_task(
                execute_approved_actions,
                approval_request,
                request.selected_actions,
                current_user.id
            )
            
            await approval_service.approve_request(
                approval_id,
                current_user.id,
                request.approval_notes
            )
            
            return {
                "status": "approved",
                "approval_id": approval_id,
                "message": "Actions approved and queued for execution",
                "execution_tracking_id": f"exec_{approval_id}",
                "timestamp": datetime.now()
            }
        else:
            logger.info(f"User {current_user.username} rejected actions for {approval_id}")
            
            await approval_service.reject_request(
                approval_id, 
                current_user.id,
                request.rejection_reason
            )
            
            return {
                "status": "rejected",
                "approval_id": approval_id,
                "message": "Actions rejected by user",
                "timestamp": datetime.now()
            }
        
    except Exception as e:
        logger.error(f"Approval processing error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process approval: {str(e)}")


@router.get("/demo/4625")
async def demo_4625_scenario(
    current_user = Depends(get_current_user),
    whis = Depends(get_whis_engine)
):
    """
    🎭 Demo Scenario: 4625 Failed Logon Analysis
    
    Demonstrates both Teacher and Assistant modes for demo purposes
    """
    try:
        # Create mock 4625 detection
        detection = Detection(
            id="demo_4625_001",
            event_id=4625,
            event_type="failed_logon",
            source_system="windows_dc",
            raw_data={
                "Account_Name": "admin",
                "Source_IP": "192.168.1.100", 
                "Failure_Reason": "Unknown user name or bad password",
                "Logon_Type": 3,
                "Process_Name": "-",
                "count": 15
            },
            severity="medium",
            timestamp=datetime.now()
        )
        
        # Get both teacher and assistant responses
        teacher_response = await whis.explain_event(detection)
        assistant_response = await whis.propose_response(detection)
        
        return {
            "demo": "4625 Failed Logon Scenario",
            "teacher_mode": {
                "explanation": teacher_response.event_summary,
                "attack_mapping": teacher_response.attack_mapping,
                "false_positives": teacher_response.false_positive_analysis,
                "recommendations": teacher_response.threshold_recommendations
            },
            "assistant_mode": {
                "assessment": assistant_response.incident_assessment,
                "severity": assistant_response.severity_rating.value,
                "playbooks": [pb.name for pb in assistant_response.recommended_playbooks],
                "actions": [action.description for action in assistant_response.proposed_actions]
            },
            "demo_complete": True,
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        logger.error(f"Demo scenario error: {e}")
        raise HTTPException(status_code=500, detail=f"Demo failed: {str(e)}")


async def send_enrichment_to_splunk(enrichment: EnrichmentResult, source: str):
    """Background task to send enrichment to Splunk HEC"""
    try:
        await send_enrichment(enrichment, source=source)
        logger.info(f"Enrichment sent to Splunk: {enrichment.detection_id}")
    except Exception as e:
        logger.error(f"Failed to send enrichment to Splunk: {e}")


async def execute_approved_actions(approval_request, selected_actions: List[str], user_id: str):
    """Background task to execute approved actions via SOAR"""
    try:
        from ..services.soar_execution import execute_playbook_actions
        
        await execute_playbook_actions(
            approval_request.playbooks,
            selected_actions,
            user_id
        )
        
        logger.info(f"Actions executed for approval {approval_request.id}")
    except Exception as e:
        logger.error(f"Failed to execute actions: {e}")