#!/usr/bin/env python3
"""
✅ Production Validation Script
==============================
Go/No-Go checklist validation for WHIS production readiness.
"""

import asyncio
import json
import requests
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Any, Tuple
import sys


class ProductionValidator:
    """Production readiness validator for WHIS"""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.results = {
            "validation_id": f"prod_val_{int(time.time())}",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC"),
            "overall_status": "PENDING",
            "checks": {},
            "summary": {
                "total_checks": 0,
                "passed_checks": 0,
                "failed_checks": 0,
                "critical_failures": 0
            }
        }
    
    def _add_result(self, check_name: str, passed: bool, message: str, critical: bool = False, details: Dict = None):
        """Add check result"""
        self.results["checks"][check_name] = {
            "passed": passed,
            "message": message,
            "critical": critical,
            "details": details or {},
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC")
        }
        
        self.results["summary"]["total_checks"] += 1
        if passed:
            self.results["summary"]["passed_checks"] += 1
        else:
            self.results["summary"]["failed_checks"] += 1
            if critical:
                self.results["summary"]["critical_failures"] += 1
    
    async def check_routing_and_launch(self) -> bool:
        """Check routing & launch requirements"""
        print("🔍 PHASE 1: Routing & Launch")
        
        # Check single server running
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            if response.status_code == 200:
                health_data = response.json()
                self._add_result(
                    "single_server_running",
                    True,
                    "Integrated server responding correctly",
                    critical=True,
                    details={"status_code": 200, "health_data": health_data}
                )
                
                # Check all required health components
                required_components = ["api", "rag", "retriever", "vectorstore"]
                all_ok = True
                for component in required_components:
                    if component not in health_data or not health_data[component]:
                        all_ok = False
                        break
                
                if all_ok:
                    self._add_result("health_components", True, "All health components OK", critical=True)
                else:
                    self._add_result("health_components", False, "Missing health components", critical=True)
                    
            else:
                self._add_result("single_server_running", False, f"Server returned {response.status_code}", critical=True)
                return False
                
        except Exception as e:
            self._add_result("single_server_running", False, f"Server not accessible: {e}", critical=True)
            return False
        
        # Check dashboard at root
        try:
            response = requests.get(self.base_url, timeout=10)
            if response.status_code == 200 and "WHIS" in response.text:
                self._add_result("dashboard_at_root", True, "Dashboard accessible at root", critical=True)
            else:
                self._add_result("dashboard_at_root", False, "Dashboard not found at root", critical=True)
        except Exception as e:
            self._add_result("dashboard_at_root", False, f"Dashboard error: {e}", critical=True)
        
        # Check API docs
        try:
            response = requests.get(f"{self.base_url}/docs", timeout=10)
            if response.status_code == 200:
                self._add_result("api_docs", True, "API documentation accessible")
            else:
                self._add_result("api_docs", False, "API docs not accessible")
        except Exception as e:
            self._add_result("api_docs", False, f"Docs error: {e}")
        
        return True
    
    async def check_rag_freshness(self) -> bool:
        """Check RAG freshness requirements"""
        print("🧠 PHASE 2: RAG Freshness")
        
        # Check RAG status endpoint
        try:
            response = requests.get(f"{self.base_url}/rag/status", timeout=10)
            if response.status_code == 200:
                rag_data = response.json()
                
                # Check eval metrics meet thresholds
                eval_data = rag_data.get("eval", {})
                ragas_score = eval_data.get("ragas_score", 0)
                hit_at_5 = eval_data.get("hit_at_5", 0)
                
                if ragas_score >= 0.75:
                    self._add_result("ragas_threshold", True, f"RAGAS score {ragas_score:.3f} >= 0.75")
                else:
                    self._add_result("ragas_threshold", False, f"RAGAS score {ragas_score:.3f} < 0.75", critical=True)
                
                if hit_at_5 >= 0.8:
                    self._add_result("hit_at_5_threshold", True, f"Hit@5 score {hit_at_5:.3f} >= 0.8")
                else:
                    self._add_result("hit_at_5_threshold", False, f"Hit@5 score {hit_at_5:.3f} < 0.8", critical=True)
                
                self._add_result("rag_status_endpoint", True, "RAG status endpoint working", details=rag_data)
                
            else:
                self._add_result("rag_status_endpoint", False, "RAG status endpoint not working", critical=True)
                
        except Exception as e:
            self._add_result("rag_status_endpoint", False, f"RAG status error: {e}", critical=True)
        
        return True
    
    async def check_security(self) -> bool:
        """Check security requirements"""
        print("🔒 PHASE 3: Security")
        
        # Test unauthenticated access to protected endpoints
        protected_endpoints = ["/incident", "/threat-hunt"]
        
        for endpoint in protected_endpoints:
            try:
                response = requests.post(
                    f"{self.base_url}{endpoint}",
                    json={"test": "data"},
                    timeout=10
                )
                
                # Should be denied (401/403) for protected endpoints
                if response.status_code in [401, 403]:
                    self._add_result(
                        f"auth_protection_{endpoint.replace('/', '_')}",
                        True,
                        f"Protected endpoint {endpoint} correctly denies unauthorized access"
                    )
                else:
                    self._add_result(
                        f"auth_protection_{endpoint.replace('/', '_')}",
                        False,
                        f"Protected endpoint {endpoint} allows unauthorized access",
                        critical=True
                    )
                    
            except Exception as e:
                self._add_result(f"auth_protection_{endpoint.replace('/', '_')}", False, f"Auth test error: {e}")
        
        # Check CORS headers
        try:
            response = requests.options(f"{self.base_url}/chat", timeout=10)
            cors_headers = response.headers.get("Access-Control-Allow-Origins", "")
            
            if "localhost:8000" in cors_headers or "127.0.0.1:8000" in cors_headers:
                self._add_result("cors_configured", True, "CORS properly configured")
            else:
                self._add_result("cors_configured", False, "CORS not properly configured")
                
        except Exception as e:
            self._add_result("cors_configured", False, f"CORS test error: {e}")
        
        return True
    
    async def check_observability(self) -> bool:
        """Check observability requirements"""
        print("📊 PHASE 4: Observability")
        
        # Check metrics endpoint
        try:
            response = requests.get(f"{self.base_url}/metrics", timeout=10)
            if response.status_code == 200:
                metrics = response.json()
                
                # Check for required metrics
                required_metrics = [
                    "inference_latency_ms_p95",
                    "rag_chunks_upserted_total", 
                    "eval_ragas_score",
                    "ws_connected_clients"
                ]
                
                missing_metrics = [m for m in required_metrics if m not in metrics]
                
                if not missing_metrics:
                    self._add_result("required_metrics", True, "All required metrics present")
                else:
                    self._add_result("required_metrics", False, f"Missing metrics: {missing_metrics}")
                
                self._add_result("metrics_endpoint", True, "Metrics endpoint working", details=metrics)
                
            else:
                self._add_result("metrics_endpoint", False, "Metrics endpoint not working")
                
        except Exception as e:
            self._add_result("metrics_endpoint", False, f"Metrics error: {e}")
        
        # Check dashboard gets metrics
        try:
            response = requests.get(self.base_url, timeout=10)
            if "ai-confidence" in response.text and "active-hunts" in response.text:
                self._add_result("dashboard_metrics", True, "Dashboard displays metrics")
            else:
                self._add_result("dashboard_metrics", False, "Dashboard not displaying metrics")
        except Exception as e:
            self._add_result("dashboard_metrics", False, f"Dashboard metrics error: {e}")
        
        return True
    
    async def check_functionality(self) -> bool:
        """Check core functionality"""
        print("🧪 PHASE 5: Functionality")
        
        # Test chat endpoint
        try:
            response = requests.post(
                f"{self.base_url}/chat",
                json={
                    "message": "How do I detect network intrusions?",
                    "use_rag": True,
                    "max_tokens": 100
                },
                timeout=30
            )
            
            if response.status_code == 200:
                chat_data = response.json()
                
                if "response" in chat_data and len(chat_data["response"]) > 20:
                    self._add_result("chat_functionality", True, "Chat endpoint working correctly")
                else:
                    self._add_result("chat_functionality", False, "Chat response too short or missing")
                    
                # Check confidence score
                if "confidence_score" in chat_data and chat_data["confidence_score"] > 0.5:
                    self._add_result("ai_confidence", True, f"AI confidence: {chat_data['confidence_score']:.3f}")
                else:
                    self._add_result("ai_confidence", False, "AI confidence too low or missing")
                    
            else:
                self._add_result("chat_functionality", False, f"Chat endpoint error: {response.status_code}")
                
        except Exception as e:
            self._add_result("chat_functionality", False, f"Chat test error: {e}")
        
        return True
    
    async def run_validation(self) -> Dict[str, Any]:
        """Run complete production validation"""
        print("🚀 WHIS Production Validation")
        print("=" * 50)
        
        # Run all validation phases
        phases = [
            self.check_routing_and_launch(),
            self.check_rag_freshness(),
            self.check_security(),
            self.check_observability(),
            self.check_functionality()
        ]
        
        for phase in phases:
            await phase
            print()
        
        # Determine overall status
        summary = self.results["summary"]
        
        if summary["critical_failures"] > 0:
            self.results["overall_status"] = "CRITICAL_FAILURE"
        elif summary["failed_checks"] > summary["passed_checks"]:
            self.results["overall_status"] = "FAILURE"
        elif summary["failed_checks"] == 0:
            self.results["overall_status"] = "PASS"
        else:
            self.results["overall_status"] = "PASS_WITH_WARNINGS"
        
        return self.results
    
    def print_summary(self):
        """Print validation summary"""
        print("📊 VALIDATION SUMMARY")
        print("=" * 50)
        
        summary = self.results["summary"]
        status = self.results["overall_status"]
        
        # Status icon
        status_icons = {
            "PASS": "✅",
            "PASS_WITH_WARNINGS": "⚠️",
            "FAILURE": "❌",
            "CRITICAL_FAILURE": "🚨"
        }
        
        print(f"{status_icons.get(status, '❓')} Overall Status: {status}")
        print(f"📊 Total Checks: {summary['total_checks']}")
        print(f"✅ Passed: {summary['passed_checks']}")
        print(f"❌ Failed: {summary['failed_checks']}")
        print(f"🚨 Critical Failures: {summary['critical_failures']}")
        print()
        
        # Show failed checks
        failed_checks = [
            name for name, result in self.results["checks"].items()
            if not result["passed"]
        ]
        
        if failed_checks:
            print("❌ FAILED CHECKS:")
            for check in failed_checks:
                result = self.results["checks"][check]
                critical_flag = " 🚨 CRITICAL" if result["critical"] else ""
                print(f"  • {check}: {result['message']}{critical_flag}")
            print()
        
        # Production readiness verdict
        if status == "PASS":
            print("🎉 WHIS IS PRODUCTION READY!")
        elif status == "PASS_WITH_WARNINGS":
            print("⚠️  WHIS is production ready with minor warnings")
        elif status == "FAILURE":
            print("❌ WHIS is NOT production ready - fix issues and re-validate")
        else:
            print("🚨 WHIS has CRITICAL FAILURES - immediate attention required")


async def main():
    """Main validation runner"""
    validator = ProductionValidator()
    
    print("Starting WHIS production validation...")
    print("Checking if server is running...")
    
    try:
        # Quick ping to see if server is up
        requests.get("http://localhost:8000/health", timeout=5)
    except:
        print("❌ ERROR: WHIS server not running!")
        print("Please start the server first: ./LAUNCH-FULL-WHIS.sh")
        sys.exit(1)
    
    # Run validation
    results = await validator.run_validation()
    
    # Print summary
    validator.print_summary()
    
    # Save results
    results_file = f"validation_results_{results['validation_id']}.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"📄 Detailed results saved to: {results_file}")
    
    # Exit with appropriate code
    if results["overall_status"] in ["PASS", "PASS_WITH_WARNINGS"]:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())