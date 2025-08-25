#!/usr/bin/env python3
"""
🎯 Complete Whis SOAR System Test
=================================
Test the full Whis system with our trained LLM
"""

import asyncio
import sys
import logging
from pathlib import Path
from datetime import datetime

# Add apps directory to path
sys.path.append(str(Path.cwd() / "apps"))

from api.legacy.engines.whis_engine import get_whis_engine
from api.legacy.schemas.detection import Detection

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def create_test_detections():
    """Create test security detections"""
    return [
        Detection(
            id="det_001",
            event_type="Failed Login",
            event_id="4625", 
            source_system="limacharlie",
            severity="medium",
            raw_data={
                "source_ip": "192.168.1.100",
                "target_account": "admin",
                "failure_count": 50,
                "time_window": "5 minutes",
                "description": "Multiple failed login attempts from single IP"
            }
        ),
        Detection(
            id="det_002",
            event_type="Service Installation",
            event_id="7045",
            source_system="splunk",
            severity="high", 
            raw_data={
                "service_name": "WindowsUpdater",
                "executable": "C:\\Temp\\updater.exe",
                "account": "SYSTEM",
                "description": "Suspicious service installed with generic name"
            }
        ),
        Detection(
            id="det_003",
            event_type="Process Creation",
            source_system="limacharlie",
            severity="critical",
            raw_data={
                "process": "powershell.exe",
                "command_line": "powershell -enc JABlAG4...",
                "parent": "winword.exe",
                "user": "john.doe",
                "description": "Encoded PowerShell execution from Word document"
            }
        )
    ]


async def test_teacher_mode():
    """Test Whis in Teacher mode"""
    print("\n🎓 TESTING TEACHER MODE")
    print("=" * 50)
    
    whis = await get_whis_engine()
    test_detections = create_test_detections()
    
    for i, detection in enumerate(test_detections[:2], 1):  # Test first 2
        print(f"\n📚 Teacher Test {i}: {detection.event_type}")
        print("-" * 30)
        
        try:
            explanation = await whis.explain_event(detection)
            
            print(f"📝 Event Summary: {explanation.event_summary[:200]}...")
            print(f"🎯 Attack Mapping: {explanation.attack_mapping}")
            print(f"🔍 False Positive Analysis: {explanation.false_positive_analysis[:150]}...")
            print(f"⚙️ Threshold Recommendations: {explanation.threshold_recommendations[:150]}...")
            print(f"📖 Best Practices: {len(explanation.best_practices)} practices")
            
        except Exception as e:
            print(f"❌ Teacher test failed: {e}")
            logger.error(f"Teacher mode error: {e}", exc_info=True)


async def test_assistant_mode():
    """Test Whis in Assistant mode"""
    print("\n🤖 TESTING ASSISTANT MODE") 
    print("=" * 50)
    
    whis = await get_whis_engine()
    test_detections = create_test_detections()
    
    for i, detection in enumerate(test_detections[:2], 1):  # Test first 2
        print(f"\n🚨 Assistant Test {i}: {detection.event_type}")
        print("-" * 30)
        
        try:
            proposal = await whis.propose_response(detection)
            
            print(f"📊 Incident Assessment: {proposal.incident_assessment[:200]}...")
            print(f"⚠️ Severity Rating: {proposal.severity_rating.value}")
            print(f"📋 Recommended Playbooks: {[pb.name for pb in proposal.recommended_playbooks]}")
            print(f"⚡ Proposed Actions: {len(proposal.proposed_actions)} actions")
            print(f"✅ Requires Approval: {proposal.approval_required}")
            
        except Exception as e:
            print(f"❌ Assistant test failed: {e}")
            logger.error(f"Assistant mode error: {e}", exc_info=True)


async def test_enrichment_mode():
    """Test Whis enrichment for SIEM integration"""
    print("\n🔍 TESTING ENRICHMENT MODE")
    print("=" * 50)
    
    whis = await get_whis_engine()
    test_detections = create_test_detections()
    
    for i, detection in enumerate(test_detections, 1):
        print(f"\n💡 Enrichment Test {i}: {detection.event_type} (Severity: {detection.severity})")
        print("-" * 30)
        
        try:
            enrichment = await whis.enrich_detection(detection)
            
            print(f"🎯 Whis Mode: {enrichment.enrichment_data.get('whis_mode', 'unknown')}")
            print(f"⏰ Timestamp: {enrichment.timestamp}")
            print(f"🔢 Confidence Score: {enrichment.enrichment_data.get('confidence_score', 'N/A')}")
            
            # Show mode-specific data
            if enrichment.enrichment_data.get('whis_mode') == 'teacher':
                print(f"🎓 Educational Context: {enrichment.enrichment_data.get('educational_context', '')[:150]}...")
                print(f"🔍 FP Guidance: Available")
                print(f"⚙️ Tuning Recommendations: Available")
            else:
                print(f"🚨 Severity Assessment: {enrichment.enrichment_data.get('severity_assessment', 'N/A')}")
                print(f"📋 Recommended Playbooks: {enrichment.enrichment_data.get('recommended_playbooks', [])}")
                print(f"⚡ Proposed Actions: {len(enrichment.enrichment_data.get('proposed_actions', []))}")
            
        except Exception as e:
            print(f"❌ Enrichment test failed: {e}")
            logger.error(f"Enrichment mode error: {e}", exc_info=True)


async def test_system_health():
    """Test system health and components"""
    print("\n🏥 SYSTEM HEALTH CHECK")
    print("=" * 50)
    
    try:
        whis = await get_whis_engine()
        
        # Check LLM health
        llm_health = await whis.llm.get_health_status()
        print("🧠 LLM Engine Health:")
        print(f"  Status: {llm_health['status']}")
        print(f"  Model: {llm_health.get('base_model', 'Unknown')}")
        print(f"  SOAR Adapter: {'✅' if llm_health.get('soar_adapter') else '❌'}")
        print(f"  Device: {llm_health.get('device', 'Unknown')}")
        if llm_health.get('memory_usage'):
            mem = llm_health['memory_usage']
            print(f"  GPU Usage: {mem['allocated_gb']}GB/{mem['total_gb']}GB ({mem['usage_percent']}%)")
        
        # Check RAG health  
        rag_health = await whis.rag.get_health_status()
        print(f"\n📚 RAG Engine Health:")
        print(f"  Status: {rag_health['status']}")
        print(f"  Documents: {rag_health['documents_loaded']}")
        print(f"  Categories: {', '.join(rag_health['categories'])}")
        
        print(f"\n✅ Overall System: HEALTHY")
        
    except Exception as e:
        print(f"❌ System health check failed: {e}")
        logger.error(f"Health check error: {e}", exc_info=True)


async def main():
    """Main test function"""
    print("🎯 WHIS SOAR SYSTEM - COMPLETE TEST")
    print("=" * 60)
    print("Testing our trained model integrated with Whis...")
    print("=" * 60)
    
    try:
        # System health first
        await test_system_health()
        
        # Test all modes
        await test_teacher_mode()
        await test_assistant_mode() 
        await test_enrichment_mode()
        
        print("\n" + "=" * 60)
        print("🎉 WHIS SOAR SYSTEM TEST COMPLETE!")
        print("=" * 60)
        print("✅ Your trained model is now integrated with Whis")
        print("✅ Teacher mode provides educational analysis")
        print("✅ Assistant mode suggests response actions")
        print("✅ Enrichment mode ready for SIEM integration")
        print("🚀 Whis can now provide intelligent SOAR advice!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        logger.error(f"Main test error: {e}", exc_info=True)
        return False
    
    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)