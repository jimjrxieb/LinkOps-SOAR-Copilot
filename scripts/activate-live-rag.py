#!/usr/bin/env python3
"""
🧠 WHIS Live RAG Activation
==========================
Deploy real-time RAG indexing with delta updates, continuous learning,
and intelligent threat intelligence integration.
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
import sys
import os
from typing import Dict, List, Any, Optional
import aiohttp
import schedule

# Add project root
sys.path.append(str(Path(__file__).parent.parent))

from ai_training.rag.delta_indexing import DeltaIndexing
from ai_training.rag.hybrid_retrieval import HybridRetrieval
from ai_training.core.logging import get_logger, configure_logging
from ai_training.monitoring.telemetry import get_telemetry


class LiveRAGEngine:
    """Live RAG engine with real-time updates and threat intelligence"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.telemetry = get_telemetry()
        self.engine_id = f"live_rag_{int(time.time())}"
        self.project_root = Path(__file__).parent.parent
        
        # RAG components
        self.delta_indexer = None
        self.hybrid_retrieval = None
        
        # Live data sources
        self.active_sources = []
        self.last_update = {}
        self.update_queue = asyncio.Queue()
        
        # Performance metrics
        self.metrics = {
            "total_updates": 0,
            "successful_updates": 0,
            "failed_updates": 0,
            "average_update_time": 0.0,
            "total_indexed_items": 0,
            "last_health_check": None
        }
        
        self.logger.info(f"🧠 Live RAG Engine initialized: {self.engine_id}")
    
    async def initialize_rag_components(self):
        """Initialize RAG pipeline components"""
        self.logger.info("🔧 Initializing RAG components...")
        
        try:
            # Initialize delta indexing
            self.delta_indexer = DeltaIndexing("ai-training/configs/rag.yaml")
            await self.delta_indexer.initialize()
            
            # Initialize hybrid retrieval
            self.hybrid_retrieval = HybridRetrieval("ai-training/configs/rag.yaml")
            await self.hybrid_retrieval.initialize()
            
            self.logger.info("✅ RAG components initialized successfully")
            return True
            
        except Exception as e:
            self.logger.exception(f"Failed to initialize RAG components: {e}")
            return False
    
    def setup_live_data_sources(self):
        """Configure live data sources for continuous indexing"""
        self.logger.info("📡 Setting up live data sources...")
        
        # Define data sources
        data_sources = [
            {
                "name": "threat_intelligence_feed",
                "type": "api",
                "url": "https://api.threatintel.example.com/indicators",
                "update_interval": 300,  # 5 minutes
                "last_update": None,
                "enabled": False  # Mock source
            },
            {
                "name": "security_research_papers",
                "type": "rss",
                "url": "https://feeds.feedburner.com/SecurityMagazine", 
                "update_interval": 1800,  # 30 minutes
                "last_update": None,
                "enabled": False  # Mock source
            },
            {
                "name": "cve_database_updates",
                "type": "api",
                "url": "https://cve.mitre.org/data/downloads/allitems-cvrf.xml",
                "update_interval": 3600,  # 1 hour
                "last_update": None,
                "enabled": False  # Mock source
            },
            {
                "name": "internal_playbook_updates",
                "type": "filesystem",
                "path": "data/playbooks/",
                "update_interval": 900,  # 15 minutes
                "last_update": None,
                "enabled": True  # Always enabled
            },
            {
                "name": "whis_session_outcomes",
                "type": "database",
                "update_interval": 60,  # 1 minute
                "last_update": None,
                "enabled": True  # Always enabled
            }
        ]
        
        # Configure active sources
        self.active_sources = [source for source in data_sources if source["enabled"]]
        
        self.logger.info(f"✅ Configured {len(self.active_sources)} active data sources")
        for source in self.active_sources:
            self.logger.info(f"   📡 {source['name']}: {source['update_interval']}s interval")
        
        return self.active_sources
    
    async def process_threat_intelligence_update(self, indicators: List[Dict]) -> Dict[str, Any]:
        """Process threat intelligence indicators for indexing"""
        processed_items = []
        
        for indicator in indicators:
            # Convert threat intel to searchable format
            processed_item = {
                "id": f"threat_intel_{indicator.get('id', int(time.time()))}",
                "text": f"""Threat Intelligence Indicator:
Type: {indicator.get('type', 'unknown')}
Value: {indicator.get('value', 'N/A')}
Confidence: {indicator.get('confidence', 'unknown')}
Threat Level: {indicator.get('threat_level', 'unknown')}
Description: {indicator.get('description', 'No description available')}
Detection Guidance: {indicator.get('detection_notes', 'Standard detection protocols apply')}
Response Actions: {indicator.get('response_actions', 'Follow standard containment procedures')}""",
                "metadata": {
                    "type": "threat_intelligence",
                    "indicator_type": indicator.get('type'),
                    "confidence": indicator.get('confidence'),
                    "threat_level": indicator.get('threat_level'),
                    "source": "threat_intelligence_feed",
                    "timestamp": datetime.now().isoformat(),
                    "tags": indicator.get('tags', [])
                },
                "embedding_priority": "high"  # Threat intel gets priority
            }
            processed_items.append(processed_item)
        
        return {
            "items": processed_items,
            "source": "threat_intelligence",
            "processed_count": len(processed_items)
        }
    
    async def process_session_outcomes(self) -> Dict[str, Any]:
        """Process WHIS session outcomes for continuous learning"""
        # Mock session outcomes (in production, this would pull from database)
        mock_sessions = [
            {
                "session_id": f"session_{int(time.time())}_001",
                "user_query": "How do I investigate suspicious PowerShell activity?",
                "whis_response": """To investigate suspicious PowerShell activity:

1. INITIAL TRIAGE:
   - Check PowerShell event logs (4103, 4104, 4105, 4106)
   - Look for encoded commands (base64, compressed)
   - Identify execution policy bypasses

2. BEHAVIORAL ANALYSIS:
   - Monitor for unusual script block logging
   - Check for obfuscated command patterns
   - Identify remote execution attempts

3. ARTIFACT COLLECTION:
   - Capture PowerShell history files
   - Extract script block contents
   - Correlate with process creation events

4. THREAT HUNTING:
   - Search for known malicious cmdlets
   - Check for download cradles (IEX, DownloadString)
   - Look for persistence mechanisms""",
                "feedback": "helpful",
                "rating": 4.5,
                "context_sources": ["powershell_forensics.md", "threat_hunting_guide.pdf"],
                "timestamp": datetime.now().isoformat()
            },
            {
                "session_id": f"session_{int(time.time())}_002", 
                "user_query": "Create incident response plan for data exfiltration",
                "whis_response": """DATA EXFILTRATION INCIDENT RESPONSE:

IMMEDIATE RESPONSE (0-1 hour):
1. Activate incident response team
2. Preserve evidence and system states
3. Block suspected exfiltration channels
4. Identify scope of potential data access

CONTAINMENT (1-4 hours):
1. Isolate affected systems
2. Revoke compromised credentials
3. Block suspicious network destinations
4. Implement DLP controls

INVESTIGATION (4-24 hours):
1. Analyze network flows for data transfers
2. Review access logs for unauthorized access
3. Identify data classification and sensitivity
4. Correlate with threat intelligence

RECOVERY & COMMUNICATION:
1. Assess legal/regulatory notification requirements
2. Coordinate with PR and legal teams
3. Implement additional monitoring controls
4. Document lessons learned""",
                "feedback": "very_helpful",
                "rating": 4.8,
                "context_sources": ["data_breach_response.pdf", "legal_requirements.md"],
                "timestamp": datetime.now().isoformat()
            }
        ]
        
        processed_items = []
        
        for session in mock_sessions:
            # Create enhanced training data from successful sessions
            if session["feedback"] in ["helpful", "very_helpful"] and session["rating"] >= 4.0:
                processed_item = {
                    "id": f"session_outcome_{session['session_id']}",
                    "text": f"""Query: {session['user_query']}

Expert Response: {session['whis_response']}

Quality Score: {session['rating']}/5.0
User Feedback: {session['feedback']}
Context Sources: {', '.join(session['context_sources'])}""",
                    "metadata": {
                        "type": "session_outcome",
                        "session_id": session["session_id"],
                        "rating": session["rating"],
                        "feedback": session["feedback"],
                        "source": "whis_sessions",
                        "timestamp": session["timestamp"],
                        "tags": ["high_quality", "user_validated"]
                    },
                    "embedding_priority": "medium"
                }
                processed_items.append(processed_item)
        
        return {
            "items": processed_items,
            "source": "session_outcomes",
            "processed_count": len(processed_items)
        }
    
    async def process_playbook_updates(self) -> Dict[str, Any]:
        """Process updated security playbooks"""
        playbooks_dir = self.project_root / "data" / "playbooks"
        playbooks_dir.mkdir(parents=True, exist_ok=True)
        
        # Create sample playbook update
        sample_playbook = {
            "name": "Advanced Persistent Threat (APT) Response",
            "version": "2.1",
            "last_updated": datetime.now().isoformat(),
            "content": """APT INCIDENT RESPONSE PLAYBOOK v2.1

PHASE 1: DETECTION & INITIAL RESPONSE
- Monitor for advanced TTPs (MITRE ATT&CK framework)
- Look for living-off-the-land techniques
- Identify lateral movement patterns
- Check for data staging activities

PHASE 2: CONTAINMENT WITHOUT ALERTING ADVERSARY  
- Implement covert monitoring
- Strengthen authentication controls
- Deploy additional logging
- Prepare for coordinated response

PHASE 3: INVESTIGATION & ATTRIBUTION
- Collect comprehensive forensic evidence
- Analyze C2 infrastructure
- Map attack timeline and methods
- Correlate with threat intelligence

PHASE 4: ERADICATION & RECOVERY
- Coordinate simultaneous remediation
- Rebuild compromised systems
- Implement enhanced security controls
- Monitor for reinfection attempts

PHASE 5: POST-INCIDENT ACTIVITIES
- Conduct thorough lessons learned
- Update security architecture
- Share indicators with community
- Enhance detection capabilities"""
        }
        
        processed_item = {
            "id": f"playbook_apt_response_v21",
            "text": f"Security Playbook: {sample_playbook['name']}\n\n{sample_playbook['content']}",
            "metadata": {
                "type": "security_playbook",
                "playbook_name": sample_playbook["name"],
                "version": sample_playbook["version"],
                "source": "playbook_updates",
                "timestamp": sample_playbook["last_updated"],
                "tags": ["apt", "incident_response", "advanced_threats"]
            },
            "embedding_priority": "high"
        }
        
        return {
            "items": [processed_item],
            "source": "playbook_updates", 
            "processed_count": 1
        }
    
    async def execute_delta_update(self, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute delta update to RAG index"""
        start_time = time.time()
        
        try:
            # Process items through delta indexer
            result = await self.delta_indexer.process_delta_batch(update_data["items"])
            
            update_duration = time.time() - start_time
            
            # Update metrics
            self.metrics["total_updates"] += 1
            self.metrics["successful_updates"] += 1
            self.metrics["total_indexed_items"] += result.get("items_added", 0)
            self.metrics["average_update_time"] = (
                (self.metrics["average_update_time"] * (self.metrics["successful_updates"] - 1) + update_duration) 
                / self.metrics["successful_updates"]
            )
            
            update_result = {
                "status": "success",
                "source": update_data["source"],
                "items_processed": update_data["processed_count"],
                "items_added": result.get("items_added", 0),
                "duration_seconds": update_duration,
                "timestamp": datetime.now().isoformat()
            }
            
            self.logger.info(f"✅ Delta update completed: {update_data['source']} (+{result.get('items_added', 0)} items)")
            return update_result
            
        except Exception as e:
            self.metrics["failed_updates"] += 1
            self.logger.exception(f"Delta update failed for {update_data['source']}: {e}")
            
            return {
                "status": "failed",
                "source": update_data["source"],
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def live_update_worker(self):
        """Background worker for processing live updates"""
        self.logger.info("🔄 Starting live update worker...")
        
        while True:
            try:
                # Wait for update in queue
                update_data = await self.update_queue.get()
                
                # Process the update
                result = await self.execute_delta_update(update_data)
                
                # Log result
                if result["status"] == "success":
                    self.logger.debug(f"Processed update from {result['source']}")
                else:
                    self.logger.warning(f"Update failed: {result}")
                
                # Mark task done
                self.update_queue.task_done()
                
            except Exception as e:
                self.logger.exception(f"Update worker error: {e}")
                await asyncio.sleep(1)
    
    async def scheduled_data_collection(self):
        """Collect data from all active sources on schedule"""
        self.logger.info("📡 Running scheduled data collection...")
        
        for source in self.active_sources:
            try:
                current_time = time.time()
                last_update = self.last_update.get(source["name"], 0)
                
                # Check if update is due
                if current_time - last_update >= source["update_interval"]:
                    self.logger.debug(f"Collecting data from {source['name']}...")
                    
                    # Process different source types
                    if source["name"] == "whis_session_outcomes":
                        update_data = await self.process_session_outcomes()
                    elif source["name"] == "internal_playbook_updates":
                        update_data = await self.process_playbook_updates()
                    elif source["name"] == "threat_intelligence_feed":
                        # Mock threat intel data
                        mock_indicators = [
                            {"id": "IOC_001", "type": "domain", "value": "malicious.example.com", 
                             "confidence": "high", "threat_level": "critical"},
                            {"id": "IOC_002", "type": "ip", "value": "192.168.1.100", 
                             "confidence": "medium", "threat_level": "high"}
                        ]
                        update_data = await self.process_threat_intelligence_update(mock_indicators)
                    else:
                        continue  # Skip unknown sources
                    
                    # Queue update for processing
                    if update_data["items"]:
                        await self.update_queue.put(update_data)
                        self.last_update[source["name"]] = current_time
                        self.logger.info(f"📊 Queued {update_data['processed_count']} items from {source['name']}")
                
            except Exception as e:
                self.logger.exception(f"Data collection failed for {source['name']}: {e}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on live RAG system"""
        health_status = {
            "timestamp": datetime.now().isoformat(),
            "engine_id": self.engine_id,
            "status": "healthy",
            "components": {
                "delta_indexer": self.delta_indexer is not None,
                "hybrid_retrieval": self.hybrid_retrieval is not None,
                "update_worker": True,  # Assume running if we got here
                "data_sources": len(self.active_sources)
            },
            "metrics": self.metrics.copy(),
            "queue_size": self.update_queue.qsize(),
            "active_sources": [s["name"] for s in self.active_sources],
            "last_updates": self.last_update.copy()
        }
        
        # Test retrieval functionality
        try:
            test_results = await self.hybrid_retrieval.hybrid_search("test query", top_k=1)
            health_status["retrieval_test"] = "passed" if test_results else "failed"
        except Exception as e:
            health_status["retrieval_test"] = f"failed: {str(e)}"
            health_status["status"] = "degraded"
        
        self.metrics["last_health_check"] = health_status["timestamp"]
        return health_status
    
    async def run_live_rag_engine(self):
        """Main execution loop for live RAG engine"""
        self.logger.info("🚀 Starting Live RAG Engine...")
        
        try:
            # Initialize components
            if not await self.initialize_rag_components():
                raise Exception("Failed to initialize RAG components")
            
            # Setup data sources
            self.setup_live_data_sources()
            
            # Start background worker
            worker_task = asyncio.create_task(self.live_update_worker())
            
            # Schedule periodic data collection
            collection_interval = 60  # Check every minute
            
            self.logger.info("✅ Live RAG Engine is now ACTIVE!")
            self.logger.info(f"🔄 Data collection interval: {collection_interval}s")
            self.logger.info(f"📡 Active sources: {len(self.active_sources)}")
            
            # Main execution loop
            while True:
                # Collect data from sources
                await self.scheduled_data_collection()
                
                # Perform health check every 10 minutes
                if int(time.time()) % 600 == 0:
                    health = await self.health_check()
                    self.logger.info(f"🏥 Health check: {health['status']} | Queue: {health['queue_size']} | Updates: {health['metrics']['total_updates']}")
                
                # Wait before next collection cycle
                await asyncio.sleep(collection_interval)
                
        except KeyboardInterrupt:
            self.logger.info("🛑 Live RAG Engine stopped by user")
        except Exception as e:
            self.logger.exception(f"Live RAG Engine error: {e}")
        finally:
            if 'worker_task' in locals():
                worker_task.cancel()
            
            # Final health report
            final_health = await self.health_check()
            self.logger.info(f"📊 Final metrics: {final_health['metrics']}")


async def main():
    """Main execution function"""
    # Configure logging
    configure_logging({
        "level": "INFO", 
        "handlers": {
            "console": {"enabled": True, "level": "INFO", "format": "text"},
            "file": {"enabled": True, "path": "logs/live-rag.log", "level": "DEBUG"}
        }
    })
    
    # Start Live RAG Engine
    engine = LiveRAGEngine()
    await engine.run_live_rag_engine()


if __name__ == "__main__":
    asyncio.run(main())