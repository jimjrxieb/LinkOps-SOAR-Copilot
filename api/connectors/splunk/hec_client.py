"""
Splunk HEC (HTTP Event Collector) Client
Handles LC → Splunk integration for enriched detections
"""

import aiohttp
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from ...core.config import get_settings
from ...schemas.detection import EnrichmentResult

logger = logging.getLogger(__name__)
settings = get_settings()


class SplunkHECClient:
    """Splunk HTTP Event Collector client for sending enriched events"""
    
    def __init__(self):
        self.hec_url = settings.SPLUNK_HEC_URL
        self.hec_token = settings.SPLUNK_HEC_TOKEN
        self.index = settings.SPLUNK_INDEX or "main"
        
        if not self.hec_url or not self.hec_token:
            logger.warning("Splunk HEC not configured - enrichment will be logged only")
    
    async def send_event(
        self, 
        event_data: Dict[str, Any],
        source: str = "whis:enrichment",
        sourcetype: str = "whis:json",
        index: Optional[str] = None
    ) -> bool:
        """
        Send enriched event to Splunk HEC
        
        Format: LC detection + Whis enrichment → Splunk for correlation
        """
        if not self.hec_url or not self.hec_token:
            logger.info(f"Would send to Splunk: {json.dumps(event_data, indent=2)}")
            return True
        
        try:
            # Format for Splunk HEC
            hec_event = {
                "time": int(datetime.now().timestamp()),
                "host": "whis-copilot",
                "source": source,
                "sourcetype": sourcetype,
                "index": index or self.index,
                "event": event_data
            }
            
            headers = {
                "Authorization": f"Splunk {self.hec_token}",
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.hec_url}/services/collector/event",
                    headers=headers,
                    json=hec_event,
                    ssl=False  # Configure SSL properly in production
                ) as response:
                    if response.status == 200:
                        logger.info(f"Successfully sent event to Splunk: {source}")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"Splunk HEC error {response.status}: {error_text}")
                        return False
                        
        except Exception as e:
            logger.error(f"Failed to send event to Splunk: {e}")
            return False
    
    async def send_enrichment(self, enrichment: EnrichmentResult) -> bool:
        """Send Whis enrichment to Splunk for correlation"""
        
        # Format enrichment for Splunk
        event_data = {
            "whis_enrichment": {
                "detection_id": enrichment.detection_id,
                "enrichment_source": enrichment.source,
                "timestamp": enrichment.enrichment_data.get("timestamp"),
                "whis_version": enrichment.enrichment_data.get("whis_version"),
                "confidence_score": enrichment.enrichment_data.get("confidence_score"),
                
                # Core enrichment data
                **enrichment.enrichment_data
            }
        }
        
        return await self.send_event(
            event_data=event_data,
            source="whis:enrichment",
            sourcetype="whis:detection_enrichment"
        )
    
    async def send_limacharlie_detection(
        self, 
        lc_detection: Dict[str, Any],
        whis_enrichment: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send LimaCharlie detection with optional Whis enrichment
        
        Used for LC → Whis → Splunk flow
        """
        
        # Combine LC detection with Whis enrichment
        event_data = {
            "limacharlie_detection": lc_detection,
            "detection_timestamp": lc_detection.get("timestamp"),
            "source_sensor": lc_detection.get("routing", {}).get("hostname"),
            "event_type": lc_detection.get("event_type"),
        }
        
        # Add Whis enrichment if available
        if whis_enrichment:
            event_data["whis_enrichment"] = whis_enrichment
            event_data["enrichment_applied"] = True
        else:
            event_data["enrichment_applied"] = False
        
        return await self.send_event(
            event_data=event_data,
            source="limacharlie:detection" if not whis_enrichment else "whis:enriched_detection",
            sourcetype="limacharlie:json"
        )
    
    async def test_connection(self) -> bool:
        """Test Splunk HEC connectivity"""
        if not self.hec_url or not self.hec_token:
            logger.warning("Splunk HEC not configured")
            return False
        
        test_event = {
            "message": "Whis SOAR-Copilot connection test",
            "timestamp": datetime.now().isoformat(),
            "test": True
        }
        
        return await self.send_event(
            event_data=test_event,
            source="whis:test",
            sourcetype="whis:connectivity"
        )


# Global client instance
_hec_client = None

def get_hec_client() -> SplunkHECClient:
    """Get or create global HEC client"""
    global _hec_client
    if _hec_client is None:
        _hec_client = SplunkHECClient()
    return _hec_client


# Convenience functions
async def send_enrichment(enrichment: EnrichmentResult, source: str = "whis:enrichment") -> bool:
    """Send enrichment to Splunk HEC"""
    client = get_hec_client()
    return await client.send_enrichment(enrichment)


async def send_lc_detection_with_enrichment(
    lc_detection: Dict[str, Any],
    whis_enrichment: Optional[Dict[str, Any]] = None
) -> bool:
    """Send LC detection with Whis enrichment to Splunk"""
    client = get_hec_client()
    return await client.send_limacharlie_detection(lc_detection, whis_enrichment)


async def test_splunk_connectivity() -> bool:
    """Test Splunk HEC connection"""
    client = get_hec_client()
    return await client.test_connection()