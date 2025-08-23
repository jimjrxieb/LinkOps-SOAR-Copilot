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
from typing import Dict, Any, Optional

# Import our enhanced components
import sys
sys.path.append('/home/jimmie/linkops-industries/SOAR-copilot/apps/api')
from normalizer import event_normalizer, NormalizedEvent
from hec_client import hec_client

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
    
    async def process_splunk_alert(
        self, 
        alert_data: Dict[str, Any], 
        correlation_id: str
    ) -> Dict[str, Any]:
        """
        Full Splunk alert processing pipeline:
        
        1. Normalize Splunk alert → Unified event schema
        2. Generate Whis analysis → Action schema
        3. Send enrichment to HEC → Correlation in Splunk
        4. Return processing results
        """
        start_time = datetime.now()
        
        try:
            # Step 1: Normalize Splunk alert
            logger.info(f"[{correlation_id}] 🔄 Normalizing Splunk alert...")
            normalized_event = event_normalizer.normalize_splunk_alert(alert_data)
            
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
                    source_system="splunk"
                )
            
            # Step 4: Build response
            response = {
                "status": "success",
                "correlation_id": correlation_id,
                "event_id": normalized_event.event_id,
                "alert_name": normalized_event.event_type,
                "host": normalized_event.host,
                "user": normalized_event.user,
                "processing_time_ms": processing_time_ms,
                "normalized_event": normalized_event.to_dict(),
                "whis_analysis": whis_analysis,
                "hec_enrichment_sent": hec_success,
                "timestamp": datetime.now().isoformat(),
                
                # Correlation helpers for Splunk searches
                "splunk_correlation_query": hec_client.get_event_correlation_query(normalized_event.event_id) if hec_client.enabled else None
            }
            
            logger.info(f"[{correlation_id}] ✅ Splunk alert processed successfully: {normalized_event.event_type}")
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