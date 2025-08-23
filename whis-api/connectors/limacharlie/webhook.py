#!/usr/bin/env python3
"""
🔄 Enhanced LimaCharlie Webhook Integration for WHIS SOAR-Copilot
Handles: LC Detection → Normalize → Whis Analysis → HEC Enrichment
"""

import json
import logging
import hashlib
import hmac
import os
from datetime import datetime
from typing import Dict, Any, Optional

# Import our enhanced components
import sys
sys.path.append('/home/jimmie/linkops-industries/SOAR-copilot/apps/api')
from normalizer import event_normalizer, NormalizedEvent
from hec_client import hec_client

logger = logging.getLogger(__name__)

class EnhancedLimaCharlieWebhookProcessor:
    """
    Enhanced LimaCharlie webhook processor with full integration pipeline:
    
    LC Detection → Normalize → Whis Analysis → HEC Enrichment → Correlation
    """
    
    def __init__(self, whis_engine=None):
        self.whis_engine = whis_engine
        self.webhook_secret = os.getenv("LC_WEBHOOK_SECRET")
        
        logger.info("✅ Enhanced LimaCharlie webhook processor initialized")
    
    def validate_webhook_signature(self, request, body: bytes) -> bool:
        """Validate LimaCharlie webhook signature for security"""
        if not self.webhook_secret:
            logger.warning("⚠️ Webhook signature validation disabled - configure LC_WEBHOOK_SECRET")
            return True
            
        signature = getattr(request, 'headers', {}).get("X-LC-Signature")
        if not signature:
            logger.warning("Missing X-LC-Signature header")
            return False
            
        expected_signature = hmac.new(
            self.webhook_secret.encode(),
            body,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(f"sha256={expected_signature}", signature)
    
    async def process_lc_detection(
        self, 
        detection_data: Dict[str, Any], 
        correlation_id: str
    ) -> Dict[str, Any]:
        """
        Full LimaCharlie detection processing pipeline:
        
        1. Normalize LC detection → Unified event schema
        2. Generate Whis analysis → Action schema
        3. Send enrichment to HEC → Correlation in Splunk
        4. Return processing results
        """
        start_time = datetime.now()
        
        try:
            # Step 1: Normalize LimaCharlie detection
            logger.info(f"[{correlation_id}] 🔄 Normalizing LC detection...")
            normalized_event = event_normalizer.normalize_limacharlie_detection(detection_data)
            
            # Step 2: Generate Whis analysis (if engine available)
            whis_analysis = None
            if self.whis_engine:
                logger.info(f"[{correlation_id}] 🧠 Generating Whis analysis...")
                whis_analysis = self.whis_engine.explain_event(normalized_event.to_dict())
            else:
                logger.warning(f"[{correlation_id}] ⚠️ Whis engine not available - using fallback")
                whis_analysis = self._generate_fallback_analysis(normalized_event)
            
            # Step 3: Send enrichment to Splunk HEC
            processing_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            
            hec_success = False
            if hec_client.enabled:
                logger.info(f"[{correlation_id}] 📤 Sending enrichment to Splunk HEC...")
                hec_success = await hec_client.send_enrichment(
                    event_id=normalized_event.event_id,
                    original_event=normalized_event.to_dict(),
                    whis_enrichment=whis_analysis,
                    correlation_id=correlation_id,
                    processing_time_ms=processing_time_ms,
                    source_system="limacharlie"
                )
            
            # Step 4: Build response
            response = {
                "status": "success",
                "correlation_id": correlation_id,
                "event_id": normalized_event.event_id,
                "detection_type": normalized_event.event_type,
                "host": normalized_event.host,
                "user": normalized_event.user,
                "sensor_id": normalized_event.sensor_id,
                "processing_time_ms": processing_time_ms,
                "normalized_event": normalized_event.to_dict(),
                "whis_analysis": whis_analysis,
                "hec_enrichment_sent": hec_success,
                "timestamp": datetime.now().isoformat(),
                
                # Correlation helpers for Splunk searches
                "splunk_correlation_query": hec_client.get_event_correlation_query(normalized_event.event_id) if hec_client.enabled else None
            }
            
            logger.info(f"[{correlation_id}] ✅ LC detection processed successfully: {normalized_event.event_type}")
            return response
            
        except Exception as e:
            logger.error(f"[{correlation_id}] ❌ Error processing LC detection: {e}")
            return {
                "status": "error",
                "correlation_id": correlation_id,
                "error": str(e),
                "processing_time_ms": int((datetime.now() - start_time).total_seconds() * 1000),
                "timestamp": datetime.now().isoformat()
            }
    
    def _generate_fallback_analysis(self, normalized_event: NormalizedEvent) -> Dict[str, Any]:
        """Generate fallback analysis when Whis engine is unavailable"""
        return {
            "triage_steps": [
                f"Investigate {normalized_event.event_type} on {normalized_event.host}",
                "Review LimaCharlie detection details and artifacts",
                "Check sensor telemetry for additional context",
                "Correlate with other security events in timeline"
            ],
            "containment": [
                "Monitor affected endpoint for suspicious activity",
                "Consider endpoint isolation if threat confirmed",
                "Block malicious network connections or processes",
                "Preserve forensic artifacts for analysis"
            ],
            "remediation": [
                "Remove malicious artifacts if confirmed",
                "Apply security patches and updates", 
                "Update LimaCharlie detection rules",
                "Implement additional monitoring controls"
            ],
            "mitre": ["T1055"],
            "spl_query": f'index=* host="{normalized_event.host}" | search "{normalized_event.event_type}" OR "{normalized_event.process}"',
            "lc_rule": f"op: and\nrules:\n  - op: is\n    path: event/PROCESS_NAME\n    value: {normalized_event.process}\n  - op: is\n    path: routing/hostname\n    value: {normalized_event.host}",
            "k8s_manifest": "",
            "validation_steps": [
                "Verify LC detection accuracy through sensor data",
                "Confirm containment actions completed",
                "Validate remediation effectiveness",
                "Document findings in incident response"
            ],
            "citations": ["LimaCharlie Detection Data", "Whis Fallback Analysis"],
            "confidence": 0.7,
            "grounded": False
        }
    
    async def test_integration_pipeline(self, correlation_id: str) -> Dict[str, Any]:
        """Test the full LimaCharlie integration pipeline"""
        test_detection = {
            "detect": {
                "event_id": f"test_{correlation_id}",
                "event_type": "SUSPICIOUS_PROCESS",
                "severity": 4,
                "event": {
                    "event_id": 4688,
                    "process_name": "suspicious.exe",
                    "command_line": "suspicious.exe --test-flag --integration",
                    "file_path": "C:\\Temp\\suspicious.exe",
                    "parent": {
                        "file_path": "C:\\Windows\\explorer.exe",
                        "process_id": 1234
                    },
                    "process_id": 5678,
                    "user_name": "test-user"
                },
                "routing": {
                    "hostname": "test-lc-endpoint",
                    "sensor_id": "test-sensor-001"
                }
            },
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"[{correlation_id}] 🧪 Running LC integration pipeline test...")
        return await self.process_lc_detection(test_detection, correlation_id)

    def validate_lc_detection_format(self, detection: Dict[str, Any]) -> bool:
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

    def map_lc_severity(self, lc_severity: int) -> str:
        """Map LimaCharlie severity levels to Whis severity"""
        severity_mapping = {
            1: "low",
            2: "low", 
            3: "medium",
            4: "high",
            5: "critical"
        }
        
        return severity_mapping.get(lc_severity, "medium")

# Factory function
def create_enhanced_limacharlie_webhook_processor(whis_engine=None) -> EnhancedLimaCharlieWebhookProcessor:
    """Create and configure enhanced LimaCharlie webhook processor"""
    return EnhancedLimaCharlieWebhookProcessor(whis_engine=whis_engine)