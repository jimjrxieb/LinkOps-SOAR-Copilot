#!/usr/bin/env python3
"""
Red Team Validation Framework for Whis
Tests Whis against sophisticated red team scenarios
"""

import json
import re
import time
import requests
from typing import Dict, List, Any, Tuple
from datetime import datetime

class WhisRedTeamValidator:
    def __init__(self, whis_api_url="http://localhost:8003"):
        self.whis_api_url = whis_api_url
        self.test_results = []
        self.passing_threshold = 0.8  # 80% of criteria must pass
        
    def load_scenarios(self, scenarios_file="red_team_scenarios.json") -> List[Dict]:
        """Load red team test scenarios"""
        try:
            with open(scenarios_file, 'r') as f:
                scenarios = json.load(f)
            print(f"✅ Loaded {len(scenarios)} red team scenarios")
            return scenarios
        except Exception as e:
            print(f"❌ Failed to load scenarios: {e}")
            return []
    
    def query_whis(self, question: str) -> Dict[str, Any]:
        """Query Whis API and return response"""
        try:
            payload = {
                "event_data": {
                    "search_name": "Red Team Validation Query",
                    "host": "validator",
                    "severity": "high",
                    "description": question
                }
            }
            
            response = requests.post(
                f"{self.whis_api_url}/explain",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ API Error {response.status_code}: {response.text}")
                return {"error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            print(f"❌ Query failed: {e}")
            return {"error": str(e)}
    
    def validate_response(self, response: Dict, criteria: Dict) -> Tuple[bool, Dict]:
        """Validate Whis response against passing criteria"""
        results = {}
        passed_count = 0
        total_count = len(criteria)
        
        response_text = str(response).lower()
        
        # Check each criterion
        for criterion, expected in criteria.items():
            passed = False
            
            if criterion == "mentions_nist_800_61":
                passed = any(term in response_text for term in ["nist", "800-61", "incident response"])
                
            elif criterion == "provides_executable_steps":
                # Look for numbered steps, action items, or procedural language
                step_patterns = [r'\d+\.\s+', r'step \d+', r'first.*then', r'next.*', r'finally']
                passed = any(re.search(pattern, response_text) for pattern in step_patterns)
                
            elif criterion == "includes_communication_plan":
                comm_keywords = ["notify", "communicate", "inform", "executive", "stakeholder", "board"]
                passed = sum(1 for word in comm_keywords if word in response_text) >= 2
                
            elif criterion == "addresses_forensics":
                forensic_keywords = ["forensic", "evidence", "preserve", "collect", "investigate"]
                passed = any(word in response_text for word in forensic_keywords)
                
            elif criterion == "timeline_under_30_minutes":
                time_patterns = [r'\d+\s*min', r'immediate', r'asap', r'urgent', r'within.*hour']
                passed = any(re.search(pattern, response_text) for pattern in time_patterns)
                
            elif criterion == "quantifies_financial_risk":
                money_patterns = [r'\$[\d,]+', r'cost', r'budget', r'financial', r'roi', r'million']
                passed = any(re.search(pattern, response_text) for pattern in money_patterns)
                
            elif criterion == "provides_interim_mitigations":
                mitigation_keywords = ["mitigate", "temporary", "interim", "workaround", "patch"]
                passed = any(word in response_text for word in mitigation_keywords)
                
            elif criterion == "executive_friendly_summary":
                exec_indicators = ["business", "risk", "impact", "summary", "recommendation"]
                passed = sum(1 for word in exec_indicators if word in response_text) >= 3
                
            elif criterion == "includes_rollback_plan":
                rollback_keywords = ["rollback", "revert", "undo", "restore", "recovery"]
                passed = any(word in response_text for word in rollback_keywords)
                
            elif criterion == "maintains_discretion":
                discretion_keywords = ["discrete", "confidential", "quietly", "without alerting"]
                passed = any(word in response_text for word in discretion_keywords)
                
            elif criterion == "involves_legal_team":
                legal_keywords = ["legal", "counsel", "attorney", "compliance"]
                passed = any(word in response_text for word in legal_keywords)
                
            elif criterion == "preserves_evidence":
                evidence_keywords = ["evidence", "preserve", "document", "chain of custody"]
                passed = any(word in response_text for word in evidence_keywords)
                
            elif criterion == "coordinates_with_hr":
                hr_keywords = ["hr", "human resources", "personnel", "employee"]
                passed = any(word in response_text for word in hr_keywords)
                
            elif criterion == "immediate_containment_steps":
                containment_keywords = ["contain", "isolate", "disconnect", "block", "stop"]
                passed = sum(1 for word in containment_keywords if word in response_text) >= 2
                
            elif criterion == "executive_communication_ready":
                comm_indicators = ["brief", "present", "communicate", "summary", "status"]
                passed = any(word in response_text for word in comm_indicators)
                
            elif criterion == "recovery_timeline":
                time_keywords = ["timeline", "schedule", "hours", "days", "recovery"]
                passed = sum(1 for word in time_keywords if word in response_text) >= 2
                
            elif criterion == "decision_framework_for_payment":
                payment_keywords = ["ransom", "payment", "bitcoin", "negotiate", "decision"]
                passed = any(word in response_text for word in payment_keywords)
                
            elif criterion == "uses_mentoring_tone":
                mentor_indicators = ["let me", "here's how", "step by step", "don't worry", "you can"]
                passed = sum(1 for phrase in mentor_indicators if phrase in response_text) >= 2
                
            elif criterion == "provides_step_by_step_guidance":
                guidance_patterns = [r'step \d+', r'first.*second.*third', r'\d+\.\s+']
                passed = any(re.search(pattern, response_text) for pattern in guidance_patterns)
                
            elif criterion == "builds_analyst_confidence":
                confidence_keywords = ["you're doing", "good approach", "that's right", "well done"]
                passed = any(phrase in response_text for phrase in confidence_keywords)
                
            else:
                # Generic keyword matching for other criteria
                criterion_words = criterion.replace("_", " ").split()
                passed = sum(1 for word in criterion_words if word in response_text) >= len(criterion_words) // 2
            
            results[criterion] = passed
            if passed:
                passed_count += 1
        
        overall_pass = (passed_count / total_count) >= self.passing_threshold
        return overall_pass, results
    
    def run_scenario_test(self, scenario: Dict) -> Dict:
        """Run a single red team scenario test"""
        print(f"\n🎯 Testing Scenario: {scenario['scenario']}")
        print(f"Query: {scenario['test_query'][:100]}...")
        
        start_time = time.time()
        
        # Query Whis
        response = self.query_whis(scenario['test_query'])
        response_time = time.time() - start_time
        
        if "error" in response:
            return {
                "scenario": scenario["scenario"],
                "status": "ERROR",
                "error": response["error"],
                "response_time": response_time
            }
        
        # Validate response
        overall_pass, detailed_results = self.validate_response(
            response, 
            scenario['passing_criteria']
        )
        
        result = {
            "scenario": scenario["scenario"],
            "status": "PASS" if overall_pass else "FAIL",
            "overall_score": sum(detailed_results.values()) / len(detailed_results),
            "detailed_results": detailed_results,
            "response_time": response_time,
            "response": response,
            "red_team_tricks": scenario.get('red_team_tricks', []),
            "expected_capabilities": scenario.get('expected_capabilities', [])
        }
        
        # Print results
        status_emoji = "✅" if overall_pass else "❌"
        print(f"{status_emoji} {scenario['scenario']}: {result['overall_score']:.2%} ({response_time:.1f}s)")
        
        for criterion, passed in detailed_results.items():
            emoji = "✅" if passed else "❌"
            print(f"  {emoji} {criterion.replace('_', ' ').title()}")
        
        return result
    
    def run_all_tests(self) -> Dict:
        """Run all red team scenarios and generate report"""
        scenarios = self.load_scenarios()
        if not scenarios:
            return {"error": "No scenarios loaded"}
        
        print(f"🚀 Starting Red Team Validation with {len(scenarios)} scenarios")
        print("=" * 60)
        
        results = []
        for scenario in scenarios:
            result = self.run_scenario_test(scenario)
            results.append(result)
            
            # Add delay to avoid overwhelming the API
            time.sleep(2)
        
        # Generate summary report
        total_scenarios = len(results)
        passed_scenarios = sum(1 for r in results if r['status'] == 'PASS')
        failed_scenarios = sum(1 for r in results if r['status'] == 'FAIL')
        error_scenarios = sum(1 for r in results if r['status'] == 'ERROR')
        
        average_score = sum(r.get('overall_score', 0) for r in results) / total_scenarios
        average_response_time = sum(r.get('response_time', 0) for r in results) / total_scenarios
        
        summary = {
            "test_timestamp": datetime.now().isoformat(),
            "total_scenarios": total_scenarios,
            "passed": passed_scenarios,
            "failed": failed_scenarios,
            "errors": error_scenarios,
            "pass_rate": passed_scenarios / total_scenarios,
            "average_score": average_score,
            "average_response_time": average_response_time,
            "detailed_results": results
        }
        
        # Print final report
        print("\n" + "=" * 60)
        print("🏆 RED TEAM VALIDATION RESULTS")
        print("=" * 60)
        print(f"Total Scenarios: {total_scenarios}")
        print(f"✅ Passed: {passed_scenarios}")
        print(f"❌ Failed: {failed_scenarios}")
        print(f"🔥 Errors: {error_scenarios}")
        print(f"📊 Pass Rate: {summary['pass_rate']:.2%}")
        print(f"🎯 Average Score: {average_score:.2%}")
        print(f"⚡ Avg Response Time: {average_response_time:.1f}s")
        
        # Identify red team readiness
        if summary['pass_rate'] >= 0.9:
            print("\n🛡️ RED TEAM READY! Whis is prepared for sophisticated attacks.")
        elif summary['pass_rate'] >= 0.8:
            print("\n⚠️  MOSTLY READY - Some gaps remain but strong overall capability.")
        else:
            print("\n🚨 NOT READY - Significant improvements needed before red team engagement.")
        
        # Save detailed results
        report_filename = f"red_team_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_filename, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"\n📁 Detailed results saved to: {report_filename}")
        
        return summary

if __name__ == "__main__":
    validator = WhisRedTeamValidator()
    
    print("🔴 WHIS RED TEAM VALIDATION FRAMEWORK")
    print("Testing against sophisticated adversarial scenarios...")
    print("This will determine if Whis is ready for red team engagement.")
    
    results = validator.run_all_tests()
    
    if results.get('pass_rate', 0) >= 0.9:
        print("\n🎉 Whis has passed red team validation!")
        print("Ready to defend against sophisticated attacks!")
    else:
        print(f"\n📋 Additional training needed - Current capability: {results.get('pass_rate', 0):.2%}")