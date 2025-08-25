#!/usr/bin/env python3
"""
🧪 Integration Pipeline Test for WHIS SOAR-Copilot
Tests: Event → Normalize → Analyze → Enrich → HEC
"""

import json
import asyncio
import logging
from datetime import datetime
from normalizer import event_normalizer
from hec_client import hec_client
from connectors.splunk.webhook import create_enhanced_splunk_webhook_processor
from connectors.limacharlie.webhook import create_enhanced_limacharlie_webhook_processor

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MockWhisEngine:
    """Mock Whis engine for testing"""
    
    def __init__(self):
        self.model_loaded = False
    
    def explain_event(self, event_data):
        """Generate mock analysis"""
        event_type = event_data.get("event_type", "Unknown Event")
        host = event_data.get("host", "unknown")
        
        return {
            "triage_steps": [
                f"Investigate {event_type} on {host}",
                "Review event details and context",
                "Correlate with other security events"
            ],
            "containment": [
                "Monitor affected system",
                "Block malicious activity if confirmed",
                "Isolate system if necessary"
            ],
            "remediation": [
                "Apply security patches",
                "Update detection rules",
                "Implement monitoring controls"
            ],
            "mitre": ["T1055"],
            "spl_query": f"index=* host=\"{host}\" | search \"{event_type}\"",
            "lc_rule": "op: and\nrules:\n  - op: is\n    path: event/HOST\n    value: test",
            "k8s_manifest": "",
            "validation_steps": [
                "Verify containment completed",
                "Confirm remediation applied",
                "Monitor for recurrence"
            ],
            "citations": ["Mock Whis Engine Test"],
            "confidence": 0.9,
            "grounded": True
        }

async def test_splunk_integration():
    """Test Splunk webhook integration pipeline"""
    logger.info("🧪 Testing Splunk integration pipeline...")
    
    # Create mock Whis engine and Splunk processor
    whis_engine = MockWhisEngine()
    splunk_processor = create_enhanced_splunk_webhook_processor(whis_engine)
    
    # Test Splunk alert data
    test_alert = {
        "search_name": "Test - Suspicious Process Execution",
        "sid": "test_splunk_001",
        "result": {
            "_time": datetime.now().isoformat(),
            "host": "test-endpoint-01",
            "user": "test-user",
            "process": "malicious.exe",
            "CommandLine": "malicious.exe --test-flag",
            "src": "192.168.1.100",
            "dest": "10.0.0.5"
        }
    }
    
    # Process alert
    correlation_id = "test_splunk_correlation_001"
    result = await splunk_processor.process_splunk_alert(test_alert, correlation_id)
    
    # Verify results
    assert result["status"] == "success"
    assert "event_id" in result
    assert "whis_analysis" in result
    assert "normalized_event" in result
    
    logger.info("✅ Splunk integration test passed")
    return result

async def test_limacharlie_integration():
    """Test LimaCharlie webhook integration pipeline"""
    logger.info("🧪 Testing LimaCharlie integration pipeline...")
    
    # Create mock Whis engine and LC processor
    whis_engine = MockWhisEngine()
    lc_processor = create_enhanced_limacharlie_webhook_processor(whis_engine)
    
    # Test LC detection data
    test_detection = {
        "detect": {
            "event_id": "test_lc_001",
            "event_type": "SUSPICIOUS_PROCESS",
            "severity": 4,
            "event": {
                "event_id": 4688,
                "process_name": "suspicious.exe",
                "command_line": "suspicious.exe --test-integration",
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
    
    # Process detection
    correlation_id = "test_lc_correlation_001"
    result = await lc_processor.process_lc_detection(test_detection, correlation_id)
    
    # Verify results
    assert result["status"] == "success"
    assert "event_id" in result
    assert "whis_analysis" in result
    assert "normalized_event" in result
    
    logger.info("✅ LimaCharlie integration test passed")
    return result

async def test_normalizer():
    """Test event normalizer components"""
    logger.info("🧪 Testing event normalizer...")
    
    # Test Splunk normalization
    splunk_alert = {
        "search_name": "Test Alert",
        "sid": "test_001",
        "result": {
            "_time": datetime.now().isoformat(),
            "host": "test-host",
            "user": "test-user",
            "process": "test.exe",
            "CommandLine": "test.exe --flag"
        }
    }
    
    normalized_splunk = event_normalizer.normalize_splunk_alert(splunk_alert)
    assert normalized_splunk.source_system == "splunk"
    assert normalized_splunk.host == "test-host"
    assert normalized_splunk.user == "test-user"
    
    # Test LC normalization
    lc_detection = {
        "detect": {
            "event_id": "test_001",
            "event_type": "TEST_EVENT",
            "event": {
                "process_name": "test.exe",
                "user_name": "test-user"
            },
            "routing": {
                "hostname": "test-host"
            }
        }
    }
    
    normalized_lc = event_normalizer.normalize_limacharlie_detection(lc_detection)
    assert normalized_lc.source_system == "limacharlie"
    assert normalized_lc.host == "test-host"
    assert normalized_lc.user == "test-user"
    
    logger.info("✅ Event normalizer test passed")

async def test_hec_client():
    """Test HEC client connectivity (if configured)"""
    logger.info("🧪 Testing HEC client...")
    
    if hec_client.enabled:
        # Test connectivity
        test_result = await hec_client.test_connection("test_integration")
        logger.info(f"HEC connectivity test: {'✅ PASS' if test_result else '❌ FAIL'}")
    else:
        logger.info("⚠️ HEC client not configured - skipping connectivity test")
    
    logger.info("✅ HEC client test completed")

async def run_full_integration_test():
    """Run complete integration test suite"""
    logger.info("🚀 Starting WHIS SOAR-Copilot Integration Test Suite...")
    
    try:
        # Test individual components
        await test_normalizer()
        await test_hec_client()
        
        # Test integration pipelines
        splunk_result = await test_splunk_integration()
        lc_result = await test_limacharlie_integration()
        
        # Summary
        logger.info("=" * 60)
        logger.info("🎉 INTEGRATION TEST RESULTS")
        logger.info("=" * 60)
        logger.info(f"✅ Splunk Pipeline: {splunk_result['status']}")
        logger.info(f"✅ LimaCharlie Pipeline: {lc_result['status']}")
        logger.info(f"✅ Event Normalizer: PASS")
        logger.info(f"✅ HEC Client: {'CONFIGURED' if hec_client.enabled else 'DISABLED'}")
        logger.info("=" * 60)
        logger.info("🔥 ALL INTEGRATION TESTS PASSED!")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Integration test failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(run_full_integration_test())
    exit(0 if success else 1)