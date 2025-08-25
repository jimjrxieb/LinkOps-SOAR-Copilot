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
from typing import Dict, Any, Optional, List

# Import our enhanced components
import sys
sys.path.append('/home/jimmie/linkops-industries/SOAR-copilot/apps/api')
from schemas import IncidentEvent, AssetMetadata, ArtifactData

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
    
    def normalize_lc_detection(self, detection_data: Dict[str, Any]) -> IncidentEvent:
        """Convert LimaCharlie detection to normalized IncidentEvent schema"""
        detect = detection_data.get("detect", detection_data)
        event_data = detect.get("event", {})
        routing = detect.get("routing", {})
        
        # Extract core fields
        title = f"LimaCharlie: {detect.get('event_type', 'Security Detection')}"
        description = f"LimaCharlie detection: {detect.get('event_type')}. "
        
        # Add event details to description
        if event_data.get("command_line"):
            description += f"Command: {event_data['command_line'][:200]}. "
        if event_data.get("file_path"):
            description += f"File: {event_data['file_path']}. "
        
        # Ensure minimum description length
        if len(description) < 10:
            description = f"LimaCharlie security detection requiring investigation: {title}"
        
        # Extract asset information
        host = routing.get("hostname", routing.get("ext_ip", "unknown"))
        user = event_data.get("user_name", event_data.get("user", None))
        
        # Extract artifacts
        ip_addresses = []
        if routing.get("ext_ip"):
            ip_addresses.append(routing["ext_ip"])
        if routing.get("int_ip"):
            ip_addresses.append(routing["int_ip"])
        
        processes = []
        if event_data.get("process_name"):
            processes.append(event_data["process_name"])
        if event_data.get("parent", {}).get("file_path"):
            processes.append(event_data["parent"]["file_path"])
        
        files = []
        if event_data.get("file_path"):
            files.append(event_data["file_path"])
        if event_data.get("target_file"):
            files.append(event_data["target_file"])
        
        # Map severity (LC uses 1-5 scale)
        lc_severity = detect.get("severity", 3)
        severity_map = {1: "low", 2: "low", 3: "medium", 4: "high", 5: "critical"}
        severity = severity_map.get(lc_severity, "medium")
        
        # Extract MITRE techniques (if available)
        techniques = detect.get("mitre_techniques", [])
        if isinstance(techniques, str):
            techniques = [techniques]
        
        # Create normalized incident
        return IncidentEvent(
            source="limacharlie",
            rule_id=detect.get("rule_name", f"lc_{detect.get('event_type', 'detection')}"),
            title=title[:200],
            description=description[:5000],
            severity=severity,
            tactic=detect.get("mitre_tactic"),
            techniques=techniques,
            asset=AssetMetadata(
                host=host,
                user=user,
                asset_class="workstation"  # Default, should be enriched
            ),
            artifacts=ArtifactData(
                event_id=detect.get("event_id"),
                ip_addresses=list(set(ip_addresses)),
                processes=list(set(processes)),
                files=list(set(files))
            ),
            first_seen=datetime.fromisoformat(
                detection_data.get("timestamp", datetime.now().isoformat())
            ),
            last_seen=datetime.fromisoformat(
                detection_data.get("timestamp", datetime.now().isoformat())
            ),
            confidence=detect.get("confidence", 0.8),
            raw_pointer=f"limacharlie:{routing.get('sensor_id')}:{detect.get('event_id')}"
        )

    async def process_lc_detection(
        self, 
        detection_data: Dict[str, Any], 
        correlation_id: str
    ) -> Dict[str, Any]:
        """
        Full LimaCharlie detection processing pipeline:
        
        1. Normalize LC detection → IncidentEvent schema
        2. Return normalized incident for SOAR processing
        """
        start_time = datetime.now()
        
        try:
            # Step 1: Normalize LimaCharlie detection to IncidentEvent
            logger.info(f"[{correlation_id}] 🔄 Normalizing LC detection...")
            incident_event = self.normalize_lc_detection(detection_data)
            
            # Step 2: Build response with normalized incident
            processing_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            
            response = {
                "status": "success",
                "correlation_id": correlation_id,
                "incident_event": incident_event.dict(),
                "processing_time_ms": processing_time_ms,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"[{correlation_id}] ✅ LC detection normalized successfully: {incident_event.title}")
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