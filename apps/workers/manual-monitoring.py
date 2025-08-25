#!/usr/bin/env python3
"""
Manual Monitoring Dashboard for Whis SOAR
Since Docker/Grafana requires permissions, this creates a simple monitoring dashboard
"""

import requests
import json
import time
import threading
from datetime import datetime
import sqlite3
from collections import defaultdict, deque

class WhisMonitor:
    def __init__(self):
        self.whis_api_url = "http://localhost:8001"
        self.frontend_url = "http://localhost:5000"
        self.metrics = defaultdict(deque)
        self.alerts = []
        self.running = True
        
    def collect_whis_metrics(self):
        """Collect metrics from Whis API"""
        try:
            # Health check
            response = requests.get(f"{self.whis_api_url}/health", timeout=5)
            if response.status_code == 200:
                health = response.json()
                self.metrics['whis_health'].append({
                    'timestamp': datetime.now(),
                    'status': health.get('status'),
                    'model_loaded': health.get('model_loaded', False)
                })
            
            # Test explain endpoint performance
            start_time = time.time()
            test_event = {
                "event_data": {
                    "search_name": "Monitor Test",
                    "host": "monitoring",
                    "description": "Health check from monitoring system"
                }
            }
            
            explain_response = requests.post(
                f"{self.whis_api_url}/explain",
                json=test_event,
                timeout=10
            )
            
            response_time = time.time() - start_time
            
            if explain_response.status_code == 200:
                result = explain_response.json()
                self.metrics['whis_performance'].append({
                    'timestamp': datetime.now(),
                    'response_time_ms': response_time * 1000,
                    'processing_time_ms': result.get('processing_time_ms', 0),
                    'status': 'success'
                })
            else:
                self.metrics['whis_performance'].append({
                    'timestamp': datetime.now(),
                    'response_time_ms': response_time * 1000,
                    'status': 'error'
                })
                
        except Exception as e:
            self.metrics['whis_errors'].append({
                'timestamp': datetime.now(),
                'error': str(e)
            })
    
    def collect_frontend_metrics(self):
        """Collect metrics from frontend"""
        try:
            response = requests.get(self.frontend_url, timeout=5, allow_redirects=False)
            self.metrics['frontend_health'].append({
                'timestamp': datetime.now(),
                'status_code': response.status_code,
                'response_time_ms': response.elapsed.total_seconds() * 1000
            })
        except Exception as e:
            self.metrics['frontend_errors'].append({
                'timestamp': datetime.now(),
                'error': str(e)
            })
    
    def generate_report(self):
        """Generate monitoring report"""
        report = []
        report.append("🔍 WHIS SOAR MONITORING REPORT")
        report.append("=" * 50)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Whis API Status
        if self.metrics['whis_health']:
            latest_health = self.metrics['whis_health'][-1]
            status = "✅ ONLINE" if latest_health['status'] == 'healthy' else "❌ OFFLINE"
            model_status = "✅ LOADED" if latest_health['model_loaded'] else "⚠️ NOT LOADED"
            
            report.append(f"🤖 WHIS API STATUS: {status}")
            report.append(f"🧠 MODEL STATUS: {model_status}")
        else:
            report.append("🤖 WHIS API STATUS: ❌ NO DATA")
        
        # Performance Metrics
        if self.metrics['whis_performance']:
            recent_perf = list(self.metrics['whis_performance'])[-10:]  # Last 10 requests
            avg_response = sum(p['response_time_ms'] for p in recent_perf) / len(recent_perf)
            success_rate = sum(1 for p in recent_perf if p['status'] == 'success') / len(recent_perf) * 100
            
            report.append(f"⚡ AVG RESPONSE TIME: {avg_response:.1f}ms")
            report.append(f"📊 SUCCESS RATE: {success_rate:.1f}%")
        
        # Frontend Status
        if self.metrics['frontend_health']:
            latest_frontend = self.metrics['frontend_health'][-1]
            fe_status = "✅ ONLINE" if latest_frontend['status_code'] in [200, 302] else "❌ OFFLINE"
            report.append(f"🌐 FRONTEND STATUS: {fe_status}")
            report.append(f"🕒 FRONTEND RESPONSE: {latest_frontend['response_time_ms']:.1f}ms")
        
        # Error Summary
        whis_errors = len(self.metrics['whis_errors'])
        frontend_errors = len(self.metrics['frontend_errors'])
        
        if whis_errors > 0 or frontend_errors > 0:
            report.append("")
            report.append("🚨 ERRORS DETECTED:")
            report.append(f"   Whis API Errors: {whis_errors}")
            report.append(f"   Frontend Errors: {frontend_errors}")
            
            # Show recent errors
            if self.metrics['whis_errors']:
                recent_error = self.metrics['whis_errors'][-1]
                report.append(f"   Last Whis Error: {recent_error['error']}")
        else:
            report.append("")
            report.append("✅ NO ERRORS DETECTED")
        
        # Recommendations
        report.append("")
        report.append("🔧 RECOMMENDATIONS:")
        
        if not self.metrics['whis_health'] or self.metrics['whis_health'][-1]['status'] != 'healthy':
            report.append("   - Check Whis API service status")
            
        if self.metrics['whis_health'] and not self.metrics['whis_health'][-1]['model_loaded']:
            report.append("   - Load AI model for full functionality")
            
        if whis_errors > 5:
            report.append("   - Investigate Whis API connection issues")
            
        if frontend_errors > 5:
            report.append("   - Check frontend service and dependencies")
        
        # Recent Activity
        report.append("")
        report.append("📈 RECENT ACTIVITY (Last 5 requests):")
        if self.metrics['whis_performance']:
            recent_activity = list(self.metrics['whis_performance'])[-5:]
            for i, activity in enumerate(recent_activity, 1):
                timestamp = activity['timestamp'].strftime('%H:%M:%S')
                response_time = activity['response_time_ms']
                status = activity['status']
                status_icon = "✅" if status == 'success' else "❌"
                report.append(f"   {i}. [{timestamp}] {status_icon} {response_time:.1f}ms")
        
        return "\n".join(report)
    
    def monitor_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                self.collect_whis_metrics()
                self.collect_frontend_metrics()
                
                # Keep only last 100 entries per metric
                for metric_name in self.metrics:
                    if len(self.metrics[metric_name]) > 100:
                        self.metrics[metric_name] = deque(
                            list(self.metrics[metric_name])[-100:], 
                            maxlen=100
                        )
                
                time.sleep(30)  # Collect every 30 seconds
                
            except Exception as e:
                print(f"Monitoring error: {e}")
                time.sleep(60)
    
    def start_monitoring(self):
        """Start monitoring in background thread"""
        monitor_thread = threading.Thread(target=self.monitor_loop)
        monitor_thread.daemon = True
        monitor_thread.start()
        return monitor_thread
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self.running = False

def main():
    monitor = WhisMonitor()
    
    print("🚀 Starting Whis SOAR Monitoring...")
    print("Press Ctrl+C to stop")
    
    # Start monitoring
    monitor_thread = monitor.start_monitoring()
    
    try:
        while True:
            # Generate and display report every 60 seconds
            time.sleep(60)
            
            print("\n" + "="*80)
            report = monitor.generate_report()
            print(report)
            print("="*80 + "\n")
            
    except KeyboardInterrupt:
        print("\n🛑 Stopping monitoring...")
        monitor.stop_monitoring()
        
        # Final report
        print("\n📊 FINAL MONITORING REPORT:")
        print(monitor.generate_report())

if __name__ == "__main__":
    main()