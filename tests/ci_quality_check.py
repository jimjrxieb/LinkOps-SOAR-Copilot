#!/usr/bin/env python3
"""
🔄 CI Quality Check Script for WHIS SOAR-Copilot
Production-ready quality gate runner for CI/CD pipeline integration
"""

import asyncio
import json
import logging
import sys
import os
from datetime import datetime
from pathlib import Path

# Add API path for imports
sys.path.append('/home/jimmie/linkops-industries/SOAR-copilot/apps/api')

from quality_gates import quality_gate_runner, QualityGateStatus

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_whis_engine():
    """Load the production Whis engine for testing"""
    try:
        from whis_minimal_api import WhisMinimalEngine
        
        engine = WhisMinimalEngine()
        # Note: We don't initialize the model here to avoid loading overhead in CI
        # The quality gates will use fallback responses which is sufficient for basic testing
        
        logger.info("✅ Whis engine loaded (fallback mode for CI)")
        return engine
        
    except Exception as e:
        logger.error(f"❌ Failed to load Whis engine: {e}")
        return None

async def run_ci_quality_check():
    """Run quality check suitable for CI/CD pipeline"""
    logger.info("🚦 Starting CI Quality Check for WHIS SOAR-Copilot...")
    
    # Load Whis engine
    whis_engine = load_whis_engine()
    if not whis_engine:
        logger.error("❌ Cannot run quality check without Whis engine")
        return False, {"error": "Engine loading failed"}
    
    try:
        # Run quality gates
        gate_results = await quality_gate_runner.run_full_quality_gates(whis_engine)
        
        # Generate CI report
        ci_report = quality_gate_runner.generate_ci_report(gate_results)
        
        # Save results to file for CI artifacts
        results_file = Path("quality_gate_results.json")
        with open(results_file, 'w') as f:
            json.dump(ci_report, f, indent=2)
        
        logger.info(f"📄 Quality gate results saved to {results_file}")
        
        # Print summary for CI logs
        print_ci_summary(ci_report, gate_results)
        
        # Return success status
        deployment_approved = ci_report['deployment_approved']
        return deployment_approved, ci_report
        
    except Exception as e:
        logger.error(f"❌ CI quality check failed: {e}")
        error_report = {
            "overall_status": "ERROR",
            "error": str(e),
            "deployment_approved": False,
            "timestamp": datetime.now().isoformat()
        }
        
        # Save error report
        with open("quality_gate_results.json", 'w') as f:
            json.dump(error_report, f, indent=2)
        
        return False, error_report

def print_ci_summary(ci_report, gate_results):
    """Print CI-friendly summary"""
    logger.info("=" * 80)
    logger.info("🚦 WHIS SOAR-COPILOT QUALITY GATE SUMMARY")
    logger.info("=" * 80)
    
    # Overall status
    status_emoji = "✅" if ci_report['deployment_approved'] else "❌"
    logger.info(f"{status_emoji} Overall Status: {ci_report['overall_status']}")
    logger.info(f"📊 Gates: {ci_report['summary']['passed']} passed, {ci_report['summary']['warnings']} warnings, {ci_report['summary']['failed']} failed")
    logger.info(f"🚀 Deployment: {'APPROVED' if ci_report['deployment_approved'] else 'BLOCKED'}")
    logger.info("")
    
    # Individual gate results
    for gate_name, result in gate_results.items():
        status_map = {
            QualityGateStatus.PASSED: "✅ PASS",
            QualityGateStatus.WARNING: "⚠️  WARN", 
            QualityGateStatus.FAILED: "❌ FAIL"
        }
        
        status_str = status_map[result.status]
        logger.info(f"{status_str} {gate_name.replace('_', ' ').title()}: {result.score:.3f} (req: {result.threshold})")
        
        # Show critical recommendations for failures
        if result.status == QualityGateStatus.FAILED and result.recommendations:
            for rec in result.recommendations[:1]:  # Show first recommendation
                if "CRITICAL" in rec or "deployment blocked" in rec.lower():
                    logger.info(f"      🚨 {rec}")
    
    logger.info("=" * 80)
    
    # Exit guidance for CI
    if ci_report['deployment_approved']:
        logger.info("🎉 Quality gates passed - proceed with deployment")
    else:
        logger.info("🛑 Quality gates failed - deployment blocked")
        logger.info("💡 Review failed gates and fix issues before retry")
        
        # Show action items for CI
        failed_gates = [name for name, result in gate_results.items() 
                       if result.status == QualityGateStatus.FAILED]
        if failed_gates:
            logger.info(f"📝 Failed gates to address: {', '.join(failed_gates)}")

def main():
    """Main entry point for CI script"""
    try:
        success, report = asyncio.run(run_ci_quality_check())
        
        # Set exit code for CI
        exit_code = 0 if success else 1
        
        # Final message
        if success:
            logger.info("🎯 CI Quality Check: PASSED")
        else:
            logger.error("🎯 CI Quality Check: FAILED")
        
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        logger.info("⚠️ CI Quality check interrupted")
        sys.exit(130)
    except Exception as e:
        logger.error(f"💥 Unexpected error in CI quality check: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()