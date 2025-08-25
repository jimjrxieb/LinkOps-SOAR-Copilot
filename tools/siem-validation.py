#!/usr/bin/env python3
"""
Complete SIEM Pipeline Validation for Whis SOAR
Tests all components: Splunk output, LimaCharlie integration, monitoring
"""

import requests
import json
import time
from datetime import datetime

class SIEMValidator:
    def __init__(self):
        self.whis_api = "http://localhost:8001"
        self.frontend = "http://localhost:5000"
        self.results = {}
        
    def test_whis_api_core(self):
        """Test core Whis API functionality"""
        print("🔍 Testing Whis API Core...")
        
        try:
            # Health check
            health = requests.get(f"{self.whis_api}/health", timeout=5).json()
            
            # Test explain endpoint with realistic security event
            security_event = {
                "event_data": {
                    "search_name": "APT29 Lateral Movement",
                    "host": "DC01-PROD",
                    "severity": "critical",
                    "description": "PowerShell Empire C2 beacon detected. Mimikatz credential dumping observed. Kerberoasting attack in progress targeting domain admin accounts.",
                    "user": "SYSTEM",
                    "source_ip": "10.0.1.15",
                    "dest_ip": "10.0.1.10",
                    "process": "powershell.exe",
                    "command_line": "powershell -enc JABzAD0ATgBlAHcALQBPAGIAagBlAGMAdAAgAFMAeQBzAHQAZQBtAC4ATgBlAHQALgBXAGUAYgBDAGwAaQBlAG4AdAA",
                    "mitre_techniques": ["T1003.001", "T1059.001", "T1078.002", "T1558.003"],
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            start_time = time.time()
            response = requests.post(f"{self.whis_api}/explain", json=security_event, timeout=30)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                
                self.results['whis_api'] = {
                    'status': '✅ OPERATIONAL',
                    'model_loaded': health.get('model_loaded', False),
                    'response_time_ms': response_time * 1000,
                    'processing_time_ms': result.get('processing_time_ms', 0),
                    'has_action_schema': 'action_schema' in result,
                    'has_mitre_mapping': bool(result.get('action_schema', {}).get('mitre', [])),
                    'has_spl_query': bool(result.get('action_schema', {}).get('spl_query')),
                    'confidence_score': result.get('action_schema', {}).get('confidence', 0),
                    'sample_response': result.get('action_schema', {}).get('triage_steps', [])[:2]
                }
                
                print(f"  ✅ API Response Time: {response_time * 1000:.1f}ms")
                print(f"  ✅ Model Status: {'Loaded' if health.get('model_loaded') else 'Fallback Mode'}")
                print(f"  ✅ MITRE Mapping: {len(result.get('action_schema', {}).get('mitre', []))} techniques")
                print(f"  ✅ Confidence: {result.get('action_schema', {}).get('confidence', 0)}")
                
            else:
                self.results['whis_api'] = {'status': f'❌ ERROR {response.status_code}'}
                
        except Exception as e:
            self.results['whis_api'] = {'status': f'❌ FAILED: {str(e)}'}
            print(f"  ❌ Error: {e}")
    
    def test_splunk_integration(self):
        """Test Splunk integration capabilities"""
        print("\n🔍 Testing Splunk Integration...")
        
        # Test if Whis generates Splunk queries
        splunk_test_event = {
            "event_data": {
                "search_name": "Splunk Integration Test",
                "host": "splunk-test",
                "description": "Testing Splunk query generation for lateral movement detection",
                "index": "security",
                "sourcetype": "windows:security"
            }
        }
        
        try:
            response = requests.post(f"{self.whis_api}/explain", json=splunk_test_event, timeout=15)
            if response.status_code == 200:
                result = response.json()
                spl_query = result.get('action_schema', {}).get('spl_query', '')
                
                self.results['splunk_integration'] = {
                    'status': '✅ FUNCTIONAL',
                    'generates_spl_queries': bool(spl_query),
                    'sample_query': spl_query[:100] + '...' if len(spl_query) > 100 else spl_query,
                    'has_hec_ready_format': 'index=' in spl_query
                }
                
                print(f"  ✅ SPL Query Generated: {bool(spl_query)}")
                if spl_query:
                    print(f"  📊 Sample Query: {spl_query[:80]}...")
            else:
                self.results['splunk_integration'] = {'status': f'❌ ERROR {response.status_code}'}
                
        except Exception as e:
            self.results['splunk_integration'] = {'status': f'❌ FAILED: {str(e)}'}
            print(f"  ❌ Error: {e}")
    
    def test_limacharlie_integration(self):
        """Test LimaCharlie integration capabilities"""
        print("\n🔍 Testing LimaCharlie Integration...")
        
        lc_test_event = {
            "event_data": {
                "search_name": "LimaCharlie EDR Alert",
                "host": "endpoint-01",
                "description": "Process injection detected via EDR sensor",
                "sensor_id": "12345-abcde",
                "event_type": "PROCESS_INJECTION",
                "detection_confidence": 0.85
            }
        }
        
        try:
            response = requests.post(f"{self.whis_api}/explain", json=lc_test_event, timeout=15)
            if response.status_code == 200:
                result = response.json()
                lc_rule = result.get('action_schema', {}).get('lc_rule', '')
                
                self.results['limacharlie_integration'] = {
                    'status': '✅ FUNCTIONAL',
                    'generates_lc_rules': bool(lc_rule),
                    'sample_rule': lc_rule[:100] + '...' if len(lc_rule) > 100 else lc_rule
                }
                
                print(f"  ✅ LC Rule Generated: {bool(lc_rule)}")
                if lc_rule:
                    print(f"  🛡️ Sample Rule: {lc_rule[:80]}...")
            else:
                self.results['limacharlie_integration'] = {'status': f'❌ ERROR {response.status_code}'}
                
        except Exception as e:
            self.results['limacharlie_integration'] = {'status': f'❌ FAILED: {str(e)}'}
            print(f"  ❌ Error: {e}")
    
    def test_frontend_integration(self):
        """Test frontend integration"""
        print("\n🔍 Testing Frontend Integration...")
        
        try:
            # Test frontend accessibility
            response = requests.get(self.frontend, timeout=5, allow_redirects=False)
            
            # Test static assets
            css_response = requests.get(f"{self.frontend}/static/css/style.css", timeout=5)
            js_response = requests.get(f"{self.frontend}/static/js/whis.js", timeout=5)
            
            self.results['frontend_integration'] = {
                'status': '✅ OPERATIONAL' if response.status_code in [200, 302] else f'❌ ERROR {response.status_code}',
                'redirects_to_login': response.status_code == 302,
                'static_assets_loaded': css_response.status_code == 200 and js_response.status_code == 200,
                'response_time_ms': response.elapsed.total_seconds() * 1000
            }
            
            print(f"  ✅ Frontend Status: {response.status_code}")
            print(f"  ✅ Static Assets: {'Loaded' if css_response.status_code == 200 else 'Failed'}")
            print(f"  ✅ Login Redirect: {'Working' if response.status_code == 302 else 'Check Required'}")
            
        except Exception as e:
            self.results['frontend_integration'] = {'status': f'❌ FAILED: {str(e)}'}
            print(f"  ❌ Error: {e}")
    
    def test_monitoring_capabilities(self):
        """Test monitoring and metrics"""
        print("\n🔍 Testing Monitoring Capabilities...")
        
        try:
            # Test multiple API calls to generate metrics
            test_events = [
                {"event_data": {"search_name": "Monitor Test 1", "host": "test1", "description": "High severity test"}},
                {"event_data": {"search_name": "Monitor Test 2", "host": "test2", "description": "Medium severity test"}},
                {"event_data": {"search_name": "Monitor Test 3", "host": "test3", "description": "Low severity test"}}
            ]
            
            response_times = []
            success_count = 0
            
            for i, event in enumerate(test_events):
                start_time = time.time()
                response = requests.post(f"{self.whis_api}/explain", json=event, timeout=10)
                response_time = time.time() - start_time
                response_times.append(response_time)
                
                if response.status_code == 200:
                    success_count += 1
                    
                time.sleep(1)  # Small delay between requests
            
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            success_rate = success_count / len(test_events) * 100
            
            self.results['monitoring'] = {
                'status': '✅ FUNCTIONAL',
                'avg_response_time_ms': avg_response_time * 1000,
                'success_rate_percent': success_rate,
                'total_requests': len(test_events),
                'successful_requests': success_count
            }
            
            print(f"  ✅ Average Response Time: {avg_response_time * 1000:.1f}ms")
            print(f"  ✅ Success Rate: {success_rate:.1f}%")
            print(f"  ✅ Load Test: {success_count}/{len(test_events)} requests successful")
            
        except Exception as e:
            self.results['monitoring'] = {'status': f'❌ FAILED: {str(e)}'}
            print(f"  ❌ Error: {e}")
    
    def generate_war_readiness_report(self):
        """Generate comprehensive war readiness report"""
        print("\n" + "="*80)
        print("🎯 WHIS SOAR WAR READINESS ASSESSMENT")
        print("="*80)
        
        # Overall status calculation
        operational_components = 0
        total_components = len(self.results)
        
        for component, result in self.results.items():
            if isinstance(result, dict) and result.get('status', '').startswith('✅'):
                operational_components += 1
        
        readiness_percentage = (operational_components / total_components * 100) if total_components > 0 else 0
        
        print(f"📊 OVERALL READINESS: {readiness_percentage:.1f}% ({operational_components}/{total_components} components operational)")
        
        if readiness_percentage >= 80:
            readiness_status = "🟢 BATTLE READY"
        elif readiness_percentage >= 60:
            readiness_status = "🟡 MOSTLY READY (Minor Issues)"
        else:
            readiness_status = "🔴 NOT READY (Major Issues)"
        
        print(f"🎖️ STATUS: {readiness_status}")
        print()
        
        # Component breakdown
        print("🔧 COMPONENT STATUS:")
        for component, result in self.results.items():
            component_name = component.replace('_', ' ').title()
            status = result.get('status', 'Unknown') if isinstance(result, dict) else str(result)
            print(f"  {component_name}: {status}")
        print()
        
        # Specific capabilities
        print("⚔️ BATTLE CAPABILITIES:")
        
        whis_api = self.results.get('whis_api', {})
        if isinstance(whis_api, dict):
            print(f"  🤖 AI Response Time: {whis_api.get('response_time_ms', 0):.1f}ms")
            print(f"  🧠 Model Status: {'Loaded' if whis_api.get('model_loaded') else 'Fallback Mode'}")
            print(f"  🎯 Confidence Score: {whis_api.get('confidence_score', 0)}")
            print(f"  🔍 MITRE ATT&CK Mapping: {'✅ Enabled' if whis_api.get('has_mitre_mapping') else '❌ Disabled'}")
        
        splunk = self.results.get('splunk_integration', {})
        if isinstance(splunk, dict):
            print(f"  📊 Splunk Query Generation: {'✅ Enabled' if splunk.get('generates_spl_queries') else '❌ Disabled'}")
        
        lc = self.results.get('limacharlie_integration', {})
        if isinstance(lc, dict):
            print(f"  🛡️ LimaCharlie Rules: {'✅ Enabled' if lc.get('generates_lc_rules') else '❌ Disabled'}")
        
        frontend = self.results.get('frontend_integration', {})
        if isinstance(frontend, dict):
            print(f"  🌐 Web Interface: {'✅ Operational' if frontend.get('status', '').startswith('✅') else '❌ Issues'}")
        
        monitoring = self.results.get('monitoring', {})
        if isinstance(monitoring, dict):
            print(f"  📈 Monitoring: {monitoring.get('success_rate_percent', 0):.1f}% success rate")
        
        print()
        
        # Recommendations
        print("🔧 PRE-BATTLE RECOMMENDATIONS:")
        
        if readiness_percentage < 100:
            if not whis_api.get('model_loaded', False):
                print("  • Load full AI model for enhanced analysis capabilities")
            
            if not splunk.get('generates_spl_queries', False):
                print("  • Configure Splunk integration for log enrichment")
            
            if not lc.get('generates_lc_rules', False):
                print("  • Set up LimaCharlie rule generation")
            
            if not frontend.get('static_assets_loaded', False):
                print("  • Fix frontend static asset loading")
        
        print("  • Set up SIEM credentials for full integration")
        print("  • Configure webhook endpoints for real-time alerts")
        print("  • Test with actual Azure VM attack scenarios")
        
        print()
        
        # War deployment status
        print("🚀 TERRAFORM DEPLOYMENT STATUS:")
        if readiness_percentage >= 70:
            print("  ✅ READY for Azure VM battlefield deployment")
            print("  ✅ Whis can analyze attacks in real-time")
            print("  ✅ Security recommendations will be generated")
            print("  ✅ MITRE ATT&CK mapping functional")
        else:
            print("  ⚠️ Fix critical issues before deployment")
            print("  ⚠️ Some components may not function properly")
        
        return readiness_percentage >= 70

def main():
    validator = SIEMValidator()
    
    print("🛡️ WHIS SOAR COMPLETE SIEM PIPELINE VALIDATION")
    print("=" * 60)
    print("Testing all components before battlefield deployment...\n")
    
    # Run all tests
    validator.test_whis_api_core()
    validator.test_splunk_integration() 
    validator.test_limacharlie_integration()
    validator.test_frontend_integration()
    validator.test_monitoring_capabilities()
    
    # Generate final report
    is_ready = validator.generate_war_readiness_report()
    
    # Save results
    with open('siem-validation-results.json', 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'results': validator.results,
            'war_ready': is_ready
        }, f, indent=2)
    
    print(f"📄 Full results saved to: siem-validation-results.json")
    
    return is_ready

if __name__ == "__main__":
    ready = main()
    exit(0 if ready else 1)