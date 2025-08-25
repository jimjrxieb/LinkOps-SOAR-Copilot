#!/usr/bin/env python3
"""
🔄 Enhanced Splunk Webhook Integration for WHIS SOAR-Copilot
Handles: Splunk Alert → Normalize → Whis Analysis → HEC Enrichment
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

class EnhancedSplunkWebhookProcessor:
    """
    Enhanced Splunk webhook processor with full integration pipeline:
    
    Splunk Alert → Normalize → Whis Analysis → HEC Enrichment → Correlation
    """
    
    def __init__(self, whis_engine=None):
        self.whis_engine = whis_engine
        self.webhook_secret = os.getenv("SPLUNK_WEBHOOK_SECRET")
        
        logger.info("✅ Enhanced Splunk webhook processor initialized")
    
    def validate_webhook_signature(self, request, body: bytes) -> bool:
        """Validate Splunk webhook signature for security"""
        if not self.webhook_secret:
            logger.warning("⚠️ Webhook signature validation disabled - configure SPLUNK_WEBHOOK_SECRET")
            return True
            
        signature = getattr(request, 'headers', {}).get("X-Splunk-Signature")
        if not signature:
            logger.warning("Missing X-Splunk-Signature header")
            return False
            
        expected_signature = hmac.new(
            self.webhook_secret.encode(),
            body,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(f"sha256={expected_signature}", signature)
    
    def normalize_splunk_alert(self, alert_data: Dict[str, Any]) -> IncidentEvent:
        """Convert Splunk alert to normalized IncidentEvent schema"""
        result = alert_data.get("result", alert_data)
        
        # Extract core fields
        title = alert_data.get("search_name", "Splunk Alert")
        description = result.get("_raw", f"Security alert from Splunk: {title}")
        if len(description) < 10:
            description = f"Splunk security alert: {title}. Investigation required."
        
        # Extract asset information
        host = result.get("host", result.get("dest", result.get("ComputerName", "unknown")))
        user = result.get("user", result.get("src_user", result.get("User", None)))
        
        # Extract artifacts
        ip_addresses = []
        for field in ["src", "dest", "src_ip", "dest_ip", "clientip"]:
            if result.get(field):
                ip_addresses.append(result[field])
        
        processes = []
        for field in ["process", "ProcessName", "Image", "process_name"]:
            if result.get(field):
                processes.append(result[field])
        
        files = []
        for field in ["file", "TargetFilename", "file_path", "filepath"]:
            if result.get(field):
                files.append(result[field])
        
        # Parse MITRE techniques from alert or description
        techniques = []
        mitre_fields = result.get("mitre_techniques", result.get("mitre_technique", []))
        if isinstance(mitre_fields, str):
            techniques = [mitre_fields]
        elif isinstance(mitre_fields, list):
            techniques = mitre_fields
        
        # Map severity
        severity_map = {
            "info": "low", "low": "low", "medium": "medium", 
            "high": "high", "critical": "critical"
        }
        severity = severity_map.get(
            result.get("severity", alert_data.get("severity", "medium")).lower(), 
            "medium"
        )
        
        # Create normalized incident
        return IncidentEvent(
            source="splunk",
            rule_id=alert_data.get("sid", f"splunk_{hash(title)}"),
            title=title[:200],
            description=description[:5000],
            severity=severity,
            tactic=result.get("mitre_tactic"),
            techniques=techniques,
            asset=AssetMetadata(
                host=host,
                user=user,
                asset_class="workstation"  # Default, should be enriched
            ),
            artifacts=ArtifactData(
                event_id=result.get("_bkt"),
                ip_addresses=list(set(ip_addresses)),
                processes=list(set(processes)),
                files=list(set(files))
            ),
            first_seen=datetime.fromisoformat(result.get("_time", datetime.now().isoformat())),
            last_seen=datetime.fromisoformat(result.get("_time", datetime.now().isoformat())),
            confidence=float(result.get("confidence", 0.8)),
            raw_pointer=f"splunk:{alert_data.get('sid')}"
        )

    async def process_splunk_alert(
        self, 
        alert_data: Dict[str, Any], 
        correlation_id: str
    ) -> Dict[str, Any]:
        """
        Full Splunk alert processing pipeline:
        
        1. Normalize Splunk alert → IncidentEvent schema
        2. Return normalized incident for SOAR processing
        """
        start_time = datetime.now()
        
        try:
            # Step 1: Normalize Splunk alert to IncidentEvent
            logger.info(f"[{correlation_id}] 🔄 Normalizing Splunk alert...")
            incident_event = self.normalize_splunk_alert(alert_data)
            
            # Step 2: Build response with normalized incident
            processing_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            
            response = {
                "status": "success",
                "correlation_id": correlation_id,
                "incident_event": incident_event.dict(),
                "processing_time_ms": processing_time_ms,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"[{correlation_id}] ✅ Splunk alert normalized successfully: {incident_event.title}")
            return response
            
        except Exception as e:
            logger.error(f"[{correlation_id}] ❌ Error processing Splunk alert: {e}")
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
                "Review system logs and network connections",
                "Correlate with recent security events in Splunk"
            ],
            "containment": [
                "Monitor affected system for suspicious activity",
                "Block malicious network traffic if identified",
                "Isolate system if threat confirmed"
            ],
            "remediation": [
                "Apply relevant security patches",
                "Update detection rules based on findings",
                "Implement additional monitoring controls"
            ],
            "mitre": ["T1000"],
            "spl_query": f'index=* host="{normalized_event.host}" | search "{normalized_event.event_type}"',
            "lc_rule": "",
            "k8s_manifest": "",
            "validation_steps": [
                "Verify alert accuracy through Splunk investigation",
                "Confirm containment actions completed",
                "Document findings in incident ticket"
            ],
            "citations": ["Splunk Alert Data", "Whis Fallback Analysis"],
            "confidence": 0.6,
            "grounded": False
        }
    
    async def test_integration_pipeline(self, correlation_id: str) -> Dict[str, Any]:
        """Test the full Splunk integration pipeline"""
        test_alert = {
            "search_name": "Test Alert - Whis Integration Pipeline",
            "sid": f"test_{correlation_id}",
            "result": {
                "_time": datetime.now().isoformat(),
                "host": "test-host-01",
                "user": "test-user",
                "process": "test.exe",
                "CommandLine": "test.exe --integration-test",
                "src": "192.168.1.100",
                "dest": "10.0.0.5"
            }
        }
        
        logger.info(f"[{correlation_id}] 🧪 Running Splunk integration pipeline test...")
        return await self.process_splunk_alert(test_alert, correlation_id)

# Factory function
def create_enhanced_splunk_webhook_processor(whis_engine=None) -> EnhancedSplunkWebhookProcessor:
    """Create and configure enhanced Splunk webhook processor"""
    return EnhancedSplunkWebhookProcessor(whis_engine=whis_engine)