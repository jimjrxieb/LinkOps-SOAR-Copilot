"""
LimaCharlie Webhook Handler
Receives detections from LC and triggers Whis enrichment
"""

from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
import json
import logging
from typing import Dict, Any
from datetime import datetime

from ...engines.whis_engine import get_whis_engine
from ...schemas.detection import Detection
from ..splunk.hec_client import send_lc_detection_with_enrichment
from ...core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter()


@router.post("/limacharlie/webhook")
async def limacharlie_webhook(
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    LimaCharlie webhook endpoint for detection ingestion
    
    Flow: LC detection → Whis enrichment → Splunk HEC
    """
    try:
        # Parse LC detection
        lc_detection = await request.json()
        
        logger.info(f"Received LC detection: {lc_detection.get('detect', {}).get('event_type', 'unknown')}")
        
        # Validate LC detection format
        if not _validate_lc_detection(lc_detection):
            raise HTTPException(status_code=400, detail="Invalid LimaCharlie detection format")
        
        # Process detection in background
        background_tasks.add_task(
            process_lc_detection,
            lc_detection
        )
        
        return {
            "status": "received",
            "detection_id": lc_detection.get("detect", {}).get("event_id"),
            "timestamp": datetime.now().isoformat(),
            "processing": "background"
        }
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    except Exception as e:
        logger.error(f"LC webhook error: {e}")
        raise HTTPException(status_code=500, detail=f"Webhook processing failed: {str(e)}")


async def process_lc_detection(lc_detection: Dict[str, Any]):
    """
    Background processing of LC detection
    
    1. Convert LC detection to Whis Detection format
    2. Get Whis enrichment
    3. Send enriched detection to Splunk HEC
    """
    try:
        # Extract detection details from LC format
        detect_info = lc_detection.get("detect", {})
        event_info = detect_info.get("event", {})
        
        # Convert to Whis Detection format
        detection = Detection(
            id=f"lc_{detect_info.get('event_id', 'unknown')}_{int(datetime.now().timestamp())}",
            event_id=event_info.get("event_id"),
            event_type=detect_info.get("event_type", "unknown"),
            source_system="limacharlie",
            raw_data=lc_detection,
            severity=_map_lc_severity(detect_info.get("severity", 3)),
            timestamp=datetime.now()
        )
        
        logger.info(f"Processing LC detection: {detection.id}")
        
        # Get Whis enrichment
        whis = await get_whis_engine()
        enrichment = await whis.enrich_detection(detection)
        
        # Send to Splunk with enrichment
        success = await send_lc_detection_with_enrichment(
            lc_detection=lc_detection,
            whis_enrichment=enrichment.enrichment_data
        )
        
        if success:
            logger.info(f"Successfully processed and enriched LC detection: {detection.id}")
        else:
            logger.warning(f"Failed to send enriched detection to Splunk: {detection.id}")
            
    except Exception as e:
        logger.error(f"Failed to process LC detection: {e}")


def _validate_lc_detection(detection: Dict[str, Any]) -> bool:
    """Validate LimaCharlie detection format"""
    required_fields = ["detect"]
    
    for field in required_fields:
        if field not in detection:
            logger.warning(f"Missing required field in LC detection: {field}")
            return False
    
    detect_info = detection.get("detect", {})
    if not detect_info.get("event_type"):
        logger.warning("Missing event_type in LC detection")
        return False
    
    return True


def _map_lc_severity(lc_severity: int) -> str:
    """Map LimaCharlie severity levels to Whis severity"""
    severity_mapping = {
        1: "low",
        2: "low", 
        3: "medium",
        4: "high",
        5: "critical"
    }
    
    return severity_mapping.get(lc_severity, "medium")


@router.post("/limacharlie/test")
async def test_lc_webhook():
    """Test endpoint for LimaCharlie webhook configuration"""
    
    # Mock LC detection for testing
    mock_detection = {
        "detect": {
            "event_id": "test_001",
            "event_type": "SUSPICIOUS_PROCESS",
            "severity": 3,
            "event": {
                "event_id": 4688,
                "process_name": "suspicious.exe",
                "command_line": "suspicious.exe --malicious-flag",
                "parent_process": "explorer.exe"
            },
            "routing": {
                "hostname": "test-endpoint",
                "sensor_id": "test-sensor-001"
            }
        },
        "timestamp": datetime.now().isoformat()
    }
    
    try:
        # Process test detection
        await process_lc_detection(mock_detection)
        
        return {
            "status": "test_successful", 
            "message": "LimaCharlie webhook test completed",
            "test_detection_processed": True,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"LC webhook test failed: {e}")
        raise HTTPException(status_code=500, detail=f"Test failed: {str(e)}")


@router.get("/limacharlie/status")
async def lc_webhook_status():
    """Get LimaCharlie webhook status and configuration"""
    
    return {
        "webhook_status": "active",
        "lc_integration": "enabled" if settings.LIMACHARLIE_OID else "disabled",
        "splunk_hec": "enabled" if settings.SPLUNK_HEC_TOKEN else "disabled",
        "whis_enrichment": "enabled",
        "supported_events": [
            "SUSPICIOUS_PROCESS",
            "NETWORK_CONNECTION", 
            "FILE_MODIFICATION",
            "REGISTRY_MODIFICATION",
            "AUTHENTICATION_EVENT"
        ],
        "webhook_url": "/api/connectors/limacharlie/webhook",
        "test_url": "/api/connectors/limacharlie/test"
    }