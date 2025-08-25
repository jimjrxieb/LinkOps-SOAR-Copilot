#!/usr/bin/env python3
"""
📊 WHIS Real-Time Monitoring Dashboard
======================================
Live monitoring and observability for production WHIS deployment
"""

import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
import sys
import psutil
import requests
from typing import Dict, Any
import os

# Add project root
sys.path.append(str(Path(__file__).parent.parent))

from ai_training.monitoring.telemetry import get_telemetry
from ai_training.core.logging import get_logger, configure_logging


class ProductionMonitor:
    """Real-time production monitoring dashboard"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.telemetry = get_telemetry()
        self.start_time = time.time()
        self.api_url = "http://localhost:8000"
        
        # Metrics tracking
        self.metrics_history = []
        self.alert_history = []
        
        self.logger.info("📊 Production monitor initialized")
    
    async def check_system_health(self) -> Dict[str, Any]:
        """Check overall system health"""
        health_data = {
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": time.time() - self.start_time,
            "system": {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage('/').percent,
                "load_average": os.getloadavg() if hasattr(os, 'getloadavg') else [0, 0, 0]
            },
            "services": {},
            "alerts": []
        }
        
        # Check API service health
        try:
            response = requests.get(f"{self.api_url}/health", timeout=5)
            if response.status_code == 200:
                api_health = response.json()
                health_data["services"]["api"] = {
                    "status": "healthy",
                    "details": api_health
                }
            else:
                health_data["services"]["api"] = {
                    "status": "unhealthy",
                    "error": f"HTTP {response.status_code}"
                }
                health_data["alerts"].append({
                    "severity": "critical",
                    "message": "API service unhealthy",
                    "details": f"HTTP {response.status_code}"
                })
        except requests.RequestException as e:
            health_data["services"]["api"] = {
                "status": "unreachable",
                "error": str(e)
            }
            health_data["alerts"].append({
                "severity": "critical",
                "message": "API service unreachable",
                "details": str(e)
            })
        
        # Check metrics endpoint
        try:
            response = requests.get(f"{self.api_url}/metrics", timeout=5)
            if response.status_code == 200:
                health_data["services"]["metrics"] = {"status": "healthy"}
            else:
                health_data["services"]["metrics"] = {"status": "degraded"}
        except requests.RequestException:
            health_data["services"]["metrics"] = {"status": "unavailable"}
        
        # System alerts
        if health_data["system"]["cpu_percent"] > 80:
            health_data["alerts"].append({
                "severity": "warning",
                "message": f"High CPU usage: {health_data['system']['cpu_percent']:.1f}%"
            })
        
        if health_data["system"]["memory_percent"] > 85:
            health_data["alerts"].append({
                "severity": "critical",
                "message": f"High memory usage: {health_data['system']['memory_percent']:.1f}%"
            })
        
        if health_data["system"]["disk_percent"] > 90:
            health_data["alerts"].append({
                "severity": "critical",
                "message": f"High disk usage: {health_data['system']['disk_percent']:.1f}%"
            })
        
        return health_data
    
    async def test_api_functionality(self) -> Dict[str, Any]:
        """Test API endpoints functionality"""
        test_results = {
            "timestamp": datetime.now().isoformat(),
            "tests": {}
        }
        
        # Test health endpoint
        try:
            start_time = time.time()
            response = requests.get(f"{self.api_url}/health", timeout=10)
            duration = time.time() - start_time
            
            test_results["tests"]["health_endpoint"] = {
                "status": "passed" if response.status_code == 200 else "failed",
                "duration_ms": duration * 1000,
                "response_code": response.status_code
            }
        except Exception as e:
            test_results["tests"]["health_endpoint"] = {
                "status": "failed",
                "error": str(e)
            }
        
        # Test chat endpoint with sample query
        try:
            start_time = time.time()
            test_payload = {
                "message": "How do I detect network intrusions?",
                "use_rag": True,
                "max_tokens": 100,
                "temperature": 0.7
            }
            
            response = requests.post(
                f"{self.api_url}/chat", 
                json=test_payload,
                timeout=30,
                headers={"Content-Type": "application/json"}
            )
            duration = time.time() - start_time
            
            if response.status_code == 200:
                chat_data = response.json()
                test_results["tests"]["chat_endpoint"] = {
                    "status": "passed",
                    "duration_ms": duration * 1000,
                    "response_length": len(chat_data.get("response", "")),
                    "sources_count": len(chat_data.get("sources", []))
                }
            else:
                test_results["tests"]["chat_endpoint"] = {
                    "status": "failed",
                    "response_code": response.status_code,
                    "duration_ms": duration * 1000
                }
                
        except Exception as e:
            test_results["tests"]["chat_endpoint"] = {
                "status": "failed",
                "error": str(e)
            }
        
        return test_results
    
    def display_dashboard(self, health_data: Dict[str, Any], test_results: Dict[str, Any] = None):
        """Display real-time dashboard"""
        # Clear screen
        os.system('clear' if os.name == 'posix' else 'cls')
        
        uptime_hours = health_data["uptime_seconds"] / 3600
        
        print("🚀 WHIS SOAR-Copilot - LIVE Production Dashboard")
        print("=" * 60)
        print(f"⏰ Uptime: {uptime_hours:.2f} hours")
        print(f"🕒 Last Update: {datetime.now().strftime('%H:%M:%S')}")
        print()
        
        # System metrics
        print("💻 System Metrics:")
        print(f"  CPU: {health_data['system']['cpu_percent']:5.1f}% {'🔥' if health_data['system']['cpu_percent'] > 80 else '✅'}")
        print(f"  RAM: {health_data['system']['memory_percent']:5.1f}% {'🔥' if health_data['system']['memory_percent'] > 85 else '✅'}")
        print(f"  Disk: {health_data['system']['disk_percent']:4.1f}% {'🔥' if health_data['system']['disk_percent'] > 90 else '✅'}")
        print()
        
        # Service status
        print("🔌 Service Status:")
        for service, status in health_data["services"].items():
            status_icon = {
                "healthy": "✅",
                "unhealthy": "❌", 
                "degraded": "⚠️",
                "unreachable": "🚫",
                "unavailable": "❓"
            }.get(status["status"], "❓")
            
            print(f"  {service.upper()}: {status_icon} {status['status']}")
            
            if status["status"] == "healthy" and service == "api" and "details" in status:
                details = status["details"]
                print(f"    Model Loaded: {'✅' if details.get('model_loaded') else '❌'}")
                print(f"    RAG Available: {'✅' if details.get('rag_available') else '❌'}")
        print()
        
        # API functionality tests
        if test_results:
            print("🧪 API Tests:")
            for test_name, result in test_results["tests"].items():
                status_icon = "✅" if result["status"] == "passed" else "❌"
                duration = result.get("duration_ms", 0)
                print(f"  {test_name}: {status_icon} {result['status']} ({duration:.0f}ms)")
                
                if test_name == "chat_endpoint" and result["status"] == "passed":
                    print(f"    Response Length: {result.get('response_length', 0)} chars")
                    print(f"    RAG Sources: {result.get('sources_count', 0)}")
            print()
        
        # Active alerts
        if health_data["alerts"]:
            print("🚨 Active Alerts:")
            for alert in health_data["alerts"]:
                severity_icon = {
                    "critical": "🔴",
                    "warning": "🟡",
                    "info": "🔵"
                }.get(alert["severity"], "⚪")
                
                print(f"  {severity_icon} {alert['severity'].upper()}: {alert['message']}")
            print()
        else:
            print("✅ No Active Alerts")
            print()
        
        # Quick stats
        healthy_services = sum(1 for s in health_data["services"].values() if s["status"] == "healthy")
        total_services = len(health_data["services"])
        
        print("📊 Quick Stats:")
        print(f"  Services Online: {healthy_services}/{total_services}")
        print(f"  Alert Level: {'🔴 CRITICAL' if any(a['severity'] == 'critical' for a in health_data['alerts']) else '🟢 NORMAL'}")
        print()
        
        print("🎯 WHIS is LIVE and serving SOC operations! 🎯")
        print("Press Ctrl+C to exit monitoring...")
        print("=" * 60)
    
    async def run_monitoring_loop(self):
        """Main monitoring loop"""
        self.logger.info("🚀 Starting production monitoring loop")
        
        try:
            while True:
                # Collect health data
                health_data = await self.check_system_health()
                
                # Run API tests every 5th iteration (reduce load)
                test_results = None
                if int(time.time()) % 30 == 0:  # Every 30 seconds
                    test_results = await self.test_api_functionality()
                
                # Store metrics for history
                self.metrics_history.append(health_data)
                if len(self.metrics_history) > 100:  # Keep last 100 readings
                    self.metrics_history.pop(0)
                
                # Update telemetry
                self.telemetry.collect_system_metrics()
                
                # Display dashboard
                self.display_dashboard(health_data, test_results)
                
                # Check for critical alerts
                critical_alerts = [a for a in health_data["alerts"] if a["severity"] == "critical"]
                if critical_alerts:
                    for alert in critical_alerts:
                        self.logger.critical(f"CRITICAL ALERT: {alert['message']}")
                
                # Wait before next update
                await asyncio.sleep(5)
                
        except KeyboardInterrupt:
            self.logger.info("🛑 Monitoring stopped by user")
            print("\n\n🛑 Monitoring stopped. WHIS continues running in background.")
            print("✨ Thanks for keeping watch! The SOC is in good hands. ✨")
        
        except Exception as e:
            self.logger.exception(f"Monitoring error: {e}")
            print(f"\n❌ Monitoring error: {e}")
        
        finally:
            # Export final metrics
            final_report = {
                "monitoring_session": {
                    "start_time": datetime.fromtimestamp(self.start_time).isoformat(),
                    "end_time": datetime.now().isoformat(),
                    "duration_seconds": time.time() - self.start_time,
                    "metrics_collected": len(self.metrics_history)
                },
                "final_health": self.metrics_history[-1] if self.metrics_history else {},
                "telemetry_summary": self.telemetry.get_health_status()
            }
            
            report_path = f"logs/monitoring_report_{int(time.time())}.json"
            with open(report_path, 'w') as f:
                json.dump(final_report, f, indent=2)
            
            print(f"📊 Final monitoring report saved: {report_path}")


async def main():
    """Main monitoring application"""
    # Configure logging
    logging_config = {
        "level": "INFO",
        "handlers": {
            "console": {"enabled": False},  # Disable console to not interfere with dashboard
            "file": {"enabled": True, "path": "logs/monitoring.log", "level": "INFO"}
        }
    }
    configure_logging(logging_config)
    
    # Start monitoring
    monitor = ProductionMonitor()
    await monitor.run_monitoring_loop()


if __name__ == "__main__":
    asyncio.run(main())