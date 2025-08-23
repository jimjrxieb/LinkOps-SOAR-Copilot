#!/usr/bin/env python3
"""
⚡ WHIS API - AI SECURITY ANALYSIS ENGINE
Core AI service that analyzes security events and provides expert recommendations

WHAT THIS DOES:
- Receives security events from SIEM/EDR systems
- Uses AI to provide instant triage and containment steps
- Maps incidents to MITRE ATT&CK framework
- Learns from analyst feedback to improve over time

WHO USES THIS:
- Security Analysts
- SOC Teams
- Automated Security Tools (via API)

INTEGRATION POINTS:
- Splunk (HTTP Event Collector)
- LimaCharlie EDR
- Microsoft Sentinel
- Any SIEM via REST API

REQUIREMENTS:
- Python 3.11+
- PyTorch + Transformers
- Fine-tuned CodeLlama model
"""

import sys
import os
import uvicorn
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Start the Whis AI API"""
    print("⚡ Starting Whis SOAR-Copilot AI Engine...")
    print("🧠 AI Security Analysis - Expert-Level Incident Response")
    print("🌐 API will be available at: http://localhost:8000")
    print()
    print("AI CAPABILITIES:")
    print("✅ Instant security event triage")
    print("✅ MITRE ATT&CK technique mapping")
    print("✅ Containment action recommendations")
    print("✅ False positive detection")
    print("✅ Learns from analyst feedback")
    print()
    print("INTEGRATION READY:")
    print("📊 Splunk HEC endpoint")
    print("🛡️  LimaCharlie webhooks")
    print("🔌 REST API for any SIEM")
    print()
    
    try:
        # Start the API server
        uvicorn.run(
            "whis_api:app",
            host="0.0.0.0", 
            port=8000,
            reload=False,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n👋 Whis API stopped by user")
    except Exception as e:
        print(f"❌ Error starting Whis API: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())