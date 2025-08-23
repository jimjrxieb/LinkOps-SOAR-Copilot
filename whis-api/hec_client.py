#!/usr/bin/env python3
"""
🔄 Enhanced Splunk HEC Client for WHIS SOAR-Copilot  
Handles enrichment delivery with correlation tracking
"""

import aiohttp
import json
import logging
import os
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class WhisHECClient:
    """Enhanced Splunk HEC client for Whis enrichment delivery"""
    
    def __init__(self):
        self.hec_url = os.getenv("SPLUNK_HEC_URL")
        self.hec_token = os.getenv("SPLUNK_HEC_TOKEN") 
        self.index = os.getenv("SPLUNK_INDEX", "secops")
        self.timeout = int(os.getenv("HEC_TIMEOUT", "10"))
        
        if not self.hec_url or not self.hec_token:
            logger.warning("⚠️ Splunk HEC not configured - enrichments will be logged only")
            self.enabled = False
        else:
            logger.info(f"✅ HEC Client initialized: {self.hec_url} -> index={self.index}")
            self.enabled = True
    
    async def send_enrichment(
        self,
        event_id: str,
        original_event: Dict[str, Any],
        whis_enrichment: Dict[str, Any],
        correlation_id: str,
        processing_time_ms: int,
        source_system: str = "whis"
    ) -> bool:
        """
        Send Whis enrichment to Splunk HEC with full correlation
        
        This creates a linked event in Splunk that can be correlated
        with the original alert/detection
        """
        if not self.enabled:
            logger.info(f"[{correlation_id}] HEC disabled - would send enrichment for {event_id}")
            return True
        
        try:
            # Build enrichment event for HEC
            enrichment_event = {
                "whis_enrichment": {
                    # Correlation fields
                    "correlation_id": correlation_id,
                    "original_event_id": event_id,
                    "source_system": source_system,
                    "enrichment_timestamp": datetime.now().isoformat(),
                    
                    # Performance metrics
                    "processing_time_ms": processing_time_ms,
                    "model_version": "whis-mega-v1.0",
                    
                    # Original event summary (for correlation)
                    "original_summary": {
                        "event_type": original_event.get("event_type", "unknown"),
                        "host": original_event.get("host", "unknown"),
                        "user": original_event.get("user", "unknown"),
                        "severity": original_event.get("severity", "medium")
                    },
                    
                    # Whis analysis results
                    "triage_steps": whis_enrichment.get("triage_steps", []),
                    "containment": whis_enrichment.get("containment", []),
                    "remediation": whis_enrichment.get("remediation", []),
                    "mitre_techniques": whis_enrichment.get("mitre", []),
                    "spl_query": whis_enrichment.get("spl_query", ""),
                    "lc_rule": whis_enrichment.get("lc_rule", ""),
                    "k8s_manifest": whis_enrichment.get("k8s_manifest", ""),
                    "validation_steps": whis_enrichment.get("validation_steps", []),
                    "citations": whis_enrichment.get("citations", []),
                    "confidence": whis_enrichment.get("confidence", 0.0),
                    "grounded": whis_enrichment.get("grounded", False),
                    
                    # Searchable fields for Splunk
                    "enrichment_applied": True,
                    "whis_version": "1.0"
                }
            }
            
            # Format for HEC ingestion
            hec_payload = {
                "time": int(datetime.now().timestamp()),
                "host": "whis-copilot",
                "source": f"whis:{source_system}",
                "sourcetype": "whis:enrichment",
                "index": self.index,
                "event": enrichment_event
            }
            
            # Send to HEC
            headers = {
                "Authorization": f"Splunk {self.hec_token}",
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.post(
                    f"{self.hec_url}/services/collector/event",
                    headers=headers,
                    json=hec_payload,
                    ssl=False  # Configure SSL properly in production
                ) as response:
                    
                    if response.status == 200:
                        logger.info(f"[{correlation_id}] ✅ Enrichment sent to Splunk HEC: {event_id}")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"[{correlation_id}] ❌ HEC error {response.status}: {error_text}")
                        return False
                        
        except Exception as e:
            logger.error(f"[{correlation_id}] ❌ Failed to send enrichment to HEC: {e}")
            return False
    
    async def send_raw_event(
        self,
        event_data: Dict[str, Any],
        source: str = "whis:raw",
        sourcetype: str = "whis:json",
        correlation_id: str = "unknown"
    ) -> bool:
        """Send raw event data to HEC (for testing/debugging)"""
        if not self.enabled:
            logger.info(f"[{correlation_id}] HEC disabled - would send raw event")
            return True
        
        try:
            hec_payload = {
                "time": int(datetime.now().timestamp()),
                "host": "whis-copilot",
                "source": source,
                "sourcetype": sourcetype,
                "index": self.index,
                "event": event_data
            }
            
            headers = {
                "Authorization": f"Splunk {self.hec_token}",
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.post(
                    f"{self.hec_url}/services/collector/event",
                    headers=headers,
                    json=hec_payload,
                    ssl=False
                ) as response:
                    
                    if response.status == 200:
                        logger.info(f"[{correlation_id}] ✅ Raw event sent to HEC")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"[{correlation_id}] ❌ HEC error {response.status}: {error_text}")
                        return False
                        
        except Exception as e:
            logger.error(f"[{correlation_id}] ❌ Failed to send raw event to HEC: {e}")
            return False
    
    async def test_connection(self, correlation_id: str = "test") -> bool:
        """Test HEC connectivity"""
        if not self.enabled:
            logger.warning("HEC not configured - skipping connection test")
            return False
        
        test_event = {
            "message": "Whis SOAR-Copilot HEC connectivity test",
            "timestamp": datetime.now().isoformat(),
            "test_correlation_id": correlation_id,
            "test": True
        }
        
        return await self.send_raw_event(
            event_data=test_event,
            source="whis:test",
            sourcetype="whis:connectivity",
            correlation_id=correlation_id
        )
    
    def get_search_query(self, correlation_id: str) -> str:
        """Generate Splunk search query to find enrichments by correlation ID"""
        return f'index={self.index} sourcetype="whis:enrichment" whis_enrichment.correlation_id="{correlation_id}"'
    
    def get_event_correlation_query(self, event_id: str) -> str:
        """Generate Splunk search to correlate original event with enrichment"""
        return f'index={self.index} (sourcetype="whis:enrichment" whis_enrichment.original_event_id="{event_id}") OR (_raw="*{event_id}*")'

# Global HEC client instance
hec_client = WhisHECClient()