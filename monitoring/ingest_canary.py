#!/usr/bin/env python3
"""
WHIS Ingest Canary - Monitor Splunk/LimaCharlie ingestion pipeline
Sends signed test events and measures arrival lag
"""

import asyncio
import json
import time
import uuid
import hashlib
import httpx
from datetime import datetime, timezone
from typing import Dict, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global state for tracking sent canaries
SENT_CANARIES: Dict[str, Dict] = {}
INGEST_METRICS = {
    "splunk_lag_seconds": 0.0,
    "limacharlie_lag_seconds": 0.0,
    "splunk_status": "unknown",
    "limacharlie_status": "unknown",
    "last_check": None
}

def create_canary_event(destination: str) -> Dict:
    """Create a signed canary event for testing ingest"""
    canary_id = f"canary_{uuid.uuid4().hex[:12]}"
    timestamp = datetime.now(timezone.utc).isoformat()
    
    # Create signed event
    event = {
        "canary_id": canary_id,
        "timestamp": timestamp,
        "destination": destination,
        "event_type": "whis_ingest_test",
        "test_data": {
            "sequence": int(time.time()),
            "source": "whis_canary",
            "tenant": "test",
            "signature": None  # Will be calculated
        }
    }
    
    # Sign the event (simple hash for detection)
    event_str = json.dumps(event, sort_keys=True)
    signature = hashlib.sha256(event_str.encode()).hexdigest()[:16]
    event["test_data"]["signature"] = signature
    
    return event

async def send_splunk_canary() -> Optional[str]:
    """Send canary event to Splunk HEC"""
    try:
        canary = create_canary_event("splunk")
        canary_id = canary["canary_id"]
        
        # Mock Splunk HEC endpoint (replace with actual in production)
        # In production: http://splunk:8088/services/collector/event
        mock_splunk_url = "http://localhost:8001/api/mock/splunk/hec"
        
        headers = {
            "Authorization": "Splunk mock-hec-token",
            "Content-Type": "application/json"
        }
        
        # HEC format
        hec_event = {
            "time": canary["timestamp"],
            "event": canary,
            "sourcetype": "whis:canary",
            "index": "test"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                mock_splunk_url,
                json=hec_event,
                headers=headers,
                timeout=5.0
            )
            
            if response.status_code == 200:
                SENT_CANARIES[canary_id] = {
                    "sent_at": time.time(),
                    "destination": "splunk",
                    "event": canary
                }
                logger.info(f"Splunk canary sent: {canary_id}")
                return canary_id
            else:
                logger.error(f"Splunk canary failed: {response.status_code}")
                
    except Exception as e:
        logger.error(f"Splunk canary error: {e}")
        INGEST_METRICS["splunk_status"] = "error"
    
    return None

async def send_limacharlie_canary() -> Optional[str]:
    """Send canary event to LimaCharlie"""
    try:
        canary = create_canary_event("limacharlie")
        canary_id = canary["canary_id"]
        
        # Mock LimaCharlie endpoint (replace with actual in production)
        # In production: https://api.limacharlie.io/v1/org/{org_id}/sensor/{sensor_id}/task
        mock_lc_url = "http://localhost:8001/api/mock/limacharlie/event"
        
        headers = {
            "Authorization": "Bearer mock-lc-token",
            "Content-Type": "application/json"
        }
        
        # LC format
        lc_event = {
            "task_type": "test_event",
            "event_data": canary,
            "routing": {"dest": "siem"}
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                mock_lc_url,
                json=lc_event,
                headers=headers,
                timeout=5.0
            )
            
            if response.status_code == 200:
                SENT_CANARIES[canary_id] = {
                    "sent_at": time.time(),
                    "destination": "limacharlie",
                    "event": canary
                }
                logger.info(f"LimaCharlie canary sent: {canary_id}")
                return canary_id
            else:
                logger.error(f"LimaCharlie canary failed: {response.status_code}")
                
    except Exception as e:
        logger.error(f"LimaCharlie canary error: {e}")
        INGEST_METRICS["limacharlie_status"] = "error"
    
    return None

async def check_canary_arrival(canary_id: str) -> Optional[float]:
    """Check if canary event has arrived (mock implementation)"""
    if canary_id not in SENT_CANARIES:
        return None
    
    canary_info = SENT_CANARIES[canary_id]
    sent_time = canary_info["sent_at"]
    destination = canary_info["destination"]
    
    # Mock arrival check (in production, query Splunk/LC for the canary)
    # Simulate realistic lag: Splunk 10-60s, LimaCharlie 5-20s
    current_time = time.time()
    elapsed = current_time - sent_time
    
    if destination == "splunk":
        # Mock: canary "arrives" after 15-45 seconds with some randomness
        arrival_lag = 30.0 + (hash(canary_id) % 30)  # Deterministic but varied
        if elapsed >= arrival_lag:
            return arrival_lag
    elif destination == "limacharlie":
        # Mock: canary "arrives" after 5-15 seconds
        arrival_lag = 10.0 + (hash(canary_id) % 10)
        if elapsed >= arrival_lag:
            return arrival_lag
    
    return None  # Not arrived yet

async def monitor_ingest_lag():
    """Main monitoring loop - sends canaries and tracks lag"""
    logger.info("🕊️ Starting ingest canary monitoring")
    
    while True:
        try:
            # Send canaries to both destinations
            splunk_canary = await send_splunk_canary()
            lc_canary = await send_limacharlie_canary()
            
            # Wait a bit for potential arrival
            await asyncio.sleep(5)
            
            # Check for arrived canaries and calculate lag
            arrived_canaries = []
            for canary_id, canary_info in list(SENT_CANARIES.items()):
                lag = await check_canary_arrival(canary_id)
                if lag is not None:
                    dest = canary_info["destination"]
                    INGEST_METRICS[f"{dest}_lag_seconds"] = lag
                    INGEST_METRICS[f"{dest}_status"] = "healthy" if lag < 120 else "warning"
                    
                    logger.info(f"📊 {dest.title()} lag: {lag:.1f}s")
                    arrived_canaries.append(canary_id)
            
            # Clean up arrived canaries
            for canary_id in arrived_canaries:
                del SENT_CANARIES[canary_id]
            
            # Clean up old canaries (>5 minutes = considered failed)
            current_time = time.time()
            expired = [
                cid for cid, info in SENT_CANARIES.items()
                if current_time - info["sent_at"] > 300
            ]
            
            for canary_id in expired:
                dest = SENT_CANARIES[canary_id]["destination"]
                INGEST_METRICS[f"{dest}_status"] = "error"
                logger.warning(f"❌ {dest.title()} canary expired: {canary_id}")
                del SENT_CANARIES[canary_id]
            
            INGEST_METRICS["last_check"] = datetime.now(timezone.utc).isoformat()
            
            # Wait 1 minute before sending next canaries
            await asyncio.sleep(60)
            
        except Exception as e:
            logger.error(f"Monitor loop error: {e}")
            await asyncio.sleep(10)

def get_ingest_metrics() -> Dict:
    """Get current ingest metrics for Prometheus"""
    return INGEST_METRICS.copy()

if __name__ == "__main__":
    # Run the monitoring loop
    asyncio.run(monitor_ingest_lag())