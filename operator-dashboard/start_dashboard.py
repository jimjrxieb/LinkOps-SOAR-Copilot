#!/usr/bin/env python3
"""
🖥️ OPERATOR DASHBOARD - MANAGEMENT INTERFACE
Simple script to start the Whis SOAR-Copilot operator dashboard

WHAT THIS DOES:
- Starts web dashboard at http://localhost:8080
- Shows real-time incident monitoring
- Provides approval workflows for AI recommendations
- Displays team performance metrics

WHO USES THIS:
- SOC Managers
- Security Operations Teams
- IT Leadership

REQUIREMENTS:
- Python 3.11+
- FastAPI dependencies
"""

import sys
import os
import uvicorn
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Start the operator dashboard"""
    print("🖥️ Starting Whis SOAR-Copilot Operator Dashboard...")
    print("📊 Management Interface - Real-time Security Operations")
    print("🌐 Dashboard will be available at: http://localhost:8080")
    print()
    print("FEATURES:")
    print("✅ Real-time incident monitoring")
    print("✅ AI recommendation approvals")
    print("✅ Team performance metrics") 
    print("✅ Training pipeline oversight")
    print()
    
    try:
        # Start the dashboard
        uvicorn.run(
            "whis_operator_ui:app",
            host="0.0.0.0",
            port=8080,
            reload=False,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n👋 Dashboard stopped by user")
    except Exception as e:
        print(f"❌ Error starting dashboard: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())