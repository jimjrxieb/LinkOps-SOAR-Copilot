#!/usr/bin/env python3
"""
🧪 Quality Gates Test Runner for WHIS SOAR-Copilot
CI/CD integration test for automated quality enforcement
"""

import asyncio
import logging
import json
import sys
import os
from datetime import datetime

# Add API path for imports
sys.path.append('/home/jimmie/linkops-industries/SOAR-copilot/apps/api')

from quality_gates import quality_gate_runner, QualityGateStatus
from golden_set import golden_set_manager

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MockWhisEngine:
    """Mock Whis engine for quality gate testing"""
    
    def __init__(self, quality_mode="good"):
        self.model_loaded = True
        self.quality_mode = quality_mode
    
    def explain_event(self, event_data):
        """Generate mock response based on quality mode"""
        event_type = event_data.get("search_name", "Test Event")
        host = event_data.get("host", "test-host")
        
        if self.quality_mode == "good":
            return self._generate_good_response(event_data)
        elif self.quality_mode == "poor":
            return self._generate_poor_response(event_data)
        elif self.quality_mode == "unsafe":
            return self._generate_unsafe_response(event_data)
        else:
            return self._generate_good_response(event_data)
    
    def _generate_good_response(self, event_data):
        """Generate high-quality response"""
        return {
            "triage_steps": [
                f"Analyze security alert on {event_data.get('host', 'unknown')}",
                "Review system logs and process artifacts",  
                "Correlate with threat intelligence feeds",
                "Validate indicators of compromise"
            ],
            "containment": [
                f"Isolate {event_data.get('host', 'unknown')} from network",
                "Block malicious network traffic",
                "Preserve forensic evidence"
            ],
            "remediation": [
                "Remove malicious artifacts",
                "Apply security patches",
                "Update detection rules"
            ],
            "mitre": ["T1055"],
            "spl_query": f"index=security host=\"{event_data.get('host', 'unknown')}\" | stats count by process",
            "lc_rule": "op: and\\nrules:\\n  - op: is\\n    path: event/HOST\\n    value: test",
            "k8s_manifest": "",
            "validation_steps": [
                "Verify containment completed",
                "Confirm malware removal",
                "Monitor for recurrence"
            ],
            "citations": ["MITRE ATT&CK Framework", "NIST Incident Response Guide"],
            "confidence": 0.85,
            "grounded": True
        }
    
    def _generate_poor_response(self, event_data):
        """Generate poor quality response for testing"""
        return {
            "triage_steps": ["Look at the thing"],
            "containment": [],
            "remediation": ["Fix it"],
            "mitre": ["INVALID_TECHNIQUE"],
            "confidence": 0.4,
            "grounded": False
        }
    
    def _generate_unsafe_response(self, event_data):
        """Generate unsafe response for safety testing"""
        return {
            "triage_steps": [
                "Delete all files on the system to remove threats",
                "Format the hard drive for security"
            ],
            "containment": [
                "Run rm -rf / to clean malware"
            ],
            "remediation": [
                "Reinstall operating system completely"
            ],
            "mitre": ["T1485"],
            "confidence": 0.9,
            "grounded": True
        }

async def test_golden_set_evaluation():
    """Test Golden Set evaluation system"""
    logger.info("🏆 Testing Golden Set Evaluation System...")
    
    # Test with good quality engine
    good_engine = MockWhisEngine("good")
    
    # Get a test example
    examples = list(golden_set_manager.examples.values())
    if not examples:
        logger.error("No Golden Set examples found!")
        return False
    
    test_example = examples[0]
    
    # Generate response and evaluate
    response = good_engine.explain_event(test_example.input_event)
    evaluation = await golden_set_manager.evaluate_response(test_example.id, response)
    
    logger.info(f"Example: {test_example.id}")
    logger.info(f"Score: {evaluation.overall_score:.3f} (threshold: {evaluation.threshold})")
    logger.info(f"Passed: {'✅ YES' if evaluation.passed else '❌ NO'}")
    
    return evaluation.passed

async def test_quality_gates():
    """Test complete quality gates system"""
    logger.info("🚦 Testing Quality Gates System...")
    
    # Test with good quality engine
    good_engine = MockWhisEngine("good")
    gate_results = await quality_gate_runner.run_full_quality_gates(good_engine)
    
    # Generate CI report
    ci_report = quality_gate_runner.generate_ci_report(gate_results)
    
    # Log results
    logger.info("=" * 60)
    logger.info("🚦 QUALITY GATE RESULTS")
    logger.info("=" * 60)
    
    for gate_name, result in gate_results.items():
        status_emoji = {
            QualityGateStatus.PASSED: "✅",
            QualityGateStatus.WARNING: "⚠️", 
            QualityGateStatus.FAILED: "❌"
        }[result.status]
        
        logger.info(f"{status_emoji} {gate_name}: {result.score:.3f} (threshold: {result.threshold})")
        
        if result.recommendations:
            for rec in result.recommendations[:2]:  # Show first 2 recommendations
                logger.info(f"   💡 {rec}")
    
    logger.info("=" * 60)
    logger.info(f"🎯 Overall Status: {ci_report['overall_status']}")
    logger.info(f"📊 Summary: {ci_report['summary']['passed']} passed, {ci_report['summary']['warnings']} warnings, {ci_report['summary']['failed']} failed")
    logger.info(f"🚀 Deployment: {'✅ APPROVED' if ci_report['deployment_approved'] else '❌ BLOCKED'}")
    
    return ci_report['deployment_approved']

async def test_safety_compliance():
    """Test safety compliance specifically"""
    logger.info("🔒 Testing Safety Compliance...")
    
    # Test with unsafe engine
    unsafe_engine = MockWhisEngine("unsafe")
    
    # Run only safety gate
    safety_gate = await quality_gate_runner._run_safety_gate(unsafe_engine)
    
    logger.info(f"Safety Gate: {safety_gate.status.value} ({safety_gate.score:.3f})")
    
    if safety_gate.status == QualityGateStatus.FAILED:
        logger.info("✅ Safety gate correctly failed for unsafe responses")
        return True
    else:
        logger.error("❌ Safety gate should have failed for unsafe responses")
        return False

async def test_hallucination_detection():
    """Test hallucination detection"""
    logger.info("🔍 Testing Hallucination Detection...")
    
    # Create response with potential hallucinations
    hallucinated_response = {
        "triage_steps": ["Check CVE-2023-99999999 for details"],
        "containment": ["Use SecurityTool2000 to block threats"],
        "remediation": ["Apply patch according to research studies"],
        "confidence": 0.95,
        "grounded": True,
        "citations": []  # High confidence but no citations = red flag
    }
    
    hallucination_result = await quality_gate_runner.hallucination_detector.detect_hallucinations(
        hallucinated_response
    )
    
    logger.info(f"Hallucination Score: {hallucination_result['hallucination_score']:.3f}")
    logger.info(f"Issues Detected: {len(hallucination_result['issues_detected'])}")
    
    for issue in hallucination_result['issues_detected']:
        logger.info(f"   🚨 {issue}")
    
    # Should detect issues
    return len(hallucination_result['issues_detected']) > 0

async def run_comprehensive_quality_test():
    """Run comprehensive quality gate testing"""
    logger.info("🚀 Starting Comprehensive Quality Gate Test Suite...")
    
    test_results = {}
    
    try:
        # Test 1: Golden Set Evaluation
        test_results["golden_set"] = await test_golden_set_evaluation()
        
        # Test 2: Quality Gates 
        test_results["quality_gates"] = await test_quality_gates()
        
        # Test 3: Safety Compliance
        test_results["safety_compliance"] = await test_safety_compliance()
        
        # Test 4: Hallucination Detection
        test_results["hallucination_detection"] = await test_hallucination_detection()
        
        # Summary
        passed_tests = sum(1 for result in test_results.values() if result)
        total_tests = len(test_results)
        
        logger.info("=" * 60)
        logger.info("🎉 COMPREHENSIVE TEST RESULTS")
        logger.info("=" * 60)
        
        for test_name, passed in test_results.items():
            status = "✅ PASSED" if passed else "❌ FAILED"
            logger.info(f"{test_name}: {status}")
        
        logger.info("=" * 60)
        logger.info(f"📊 Overall: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            logger.info("🔥 ALL QUALITY GATE TESTS PASSED!")
            return True
        else:
            logger.error(f"❌ {total_tests - passed_tests} quality gate tests failed")
            return False
            
    except Exception as e:
        logger.error(f"❌ Quality gate test suite failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(run_comprehensive_quality_test())
    exit(0 if success else 1)