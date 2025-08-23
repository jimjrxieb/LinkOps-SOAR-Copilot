#!/usr/bin/env python3
"""
Whis Training Process Manager
Prevents multiple training processes and provides process management
"""

import os
import psutil
import signal
import time
from pathlib import Path
from datetime import datetime
import json

class WhisProcessManager:
    """Manages Whis training processes to prevent conflicts"""
    
    def __init__(self):
        self.lockfile = Path("./training.lock")
        self.process_log = Path("./process_log.json")
        
    def is_training_running(self) -> dict:
        """Check if training is already running"""
        training_processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time', 'memory_info']):
            try:
                cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
                
                # Look for training processes
                if any(pattern in cmdline.lower() for pattern in ['train_whis.py', 'whis_cybersec_finetuning']):
                    training_processes.append({
                        'pid': proc.info['pid'],
                        'name': proc.info['name'],
                        'cmdline': cmdline,
                        'create_time': datetime.fromtimestamp(proc.info['create_time']).isoformat(),
                        'memory_mb': round(proc.info['memory_info'].rss / (1024*1024), 1) if proc.info['memory_info'] else 0
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        return {
            'is_running': len(training_processes) > 0,
            'process_count': len(training_processes),
            'processes': training_processes
        }
    
    def create_lockfile(self, process_info: dict) -> bool:
        """Create lockfile to prevent multiple training"""
        if self.lockfile.exists():
            # Check if the locked process is still running
            try:
                with open(self.lockfile, 'r') as f:
                    lock_data = json.load(f)
                
                locked_pid = lock_data.get('pid')
                if locked_pid and psutil.pid_exists(locked_pid):
                    return False  # Still locked
                else:
                    # Stale lock, remove it
                    self.lockfile.unlink()
            except:
                # Corrupted lock, remove it
                self.lockfile.unlink()
        
        # Create new lock
        lock_data = {
            'pid': os.getpid(),
            'command': ' '.join(process_info.get('cmdline', [])),
            'start_time': datetime.now().isoformat(),
            'gpu_reserved': True
        }
        
        with open(self.lockfile, 'w') as f:
            json.dump(lock_data, f, indent=2)
        
        return True
    
    def remove_lockfile(self):
        """Remove lockfile when training completes"""
        if self.lockfile.exists():
            self.lockfile.unlink()
    
    def kill_duplicate_processes(self, keep_newest: bool = True) -> dict:
        """Kill duplicate training processes"""
        status = self.is_training_running()
        
        if status['process_count'] <= 1:
            return {
                'action': 'none_needed',
                'processes_killed': 0,
                'message': f"Only {status['process_count']} training process found"
            }
        
        processes = status['processes']
        
        # Sort by creation time
        processes.sort(key=lambda p: p['create_time'])
        
        if keep_newest:
            # Keep the newest, kill older ones
            to_kill = processes[:-1]
            to_keep = processes[-1:]
        else:
            # Keep the oldest, kill newer ones
            to_kill = processes[1:]
            to_keep = processes[:1]
        
        killed_pids = []
        
        for proc in to_kill:
            try:
                pid = proc['pid']
                os.kill(pid, signal.SIGTERM)
                killed_pids.append(pid)
                print(f"🔪 Killed duplicate training process: PID {pid}")
                
                # Wait for graceful shutdown
                time.sleep(2)
                
                # Force kill if still running
                if psutil.pid_exists(pid):
                    os.kill(pid, signal.SIGKILL)
                    print(f"💀 Force killed PID {pid}")
                    
            except (ProcessLookupError, psutil.NoSuchProcess):
                print(f"✅ Process {pid} already terminated")
            except Exception as e:
                print(f"❌ Failed to kill PID {pid}: {e}")
        
        return {
            'action': 'processes_killed',
            'processes_killed': len(killed_pids),
            'killed_pids': killed_pids,
            'kept_process': to_keep[0] if to_keep else None,
            'message': f"Killed {len(killed_pids)} duplicate processes"
        }
    
    def log_process_event(self, event_type: str, details: dict):
        """Log process management events"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'details': details
        }
        
        # Load existing log
        log_data = []
        if self.process_log.exists():
            try:
                with open(self.process_log, 'r') as f:
                    log_data = json.load(f)
            except:
                log_data = []
        
        # Add new entry
        log_data.append(log_entry)
        
        # Keep only last 50 entries
        log_data = log_data[-50:]
        
        # Save log
        with open(self.process_log, 'w') as f:
            json.dump(log_data, f, indent=2)
    
    def safe_training_start(self) -> dict:
        """Safely start training with duplicate prevention"""
        print("🛡️ WHIS TRAINING PROCESS MANAGER")
        print("=" * 40)
        
        # Check current status
        status = self.is_training_running()
        
        print(f"🔍 Current training processes: {status['process_count']}")
        
        if status['process_count'] > 1:
            print("⚠️ Multiple training processes detected!")
            
            for proc in status['processes']:
                print(f"  📍 PID {proc['pid']}: {proc['memory_mb']}MB RAM, started {proc['create_time']}")
            
            # Kill duplicates
            kill_result = self.kill_duplicate_processes(keep_newest=True)
            print(f"🔪 {kill_result['message']}")
            
            self.log_process_event('duplicate_cleanup', kill_result)
            
            # Wait for cleanup
            time.sleep(3)
            
            # Recheck
            status = self.is_training_running()
        
        elif status['process_count'] == 1:
            proc = status['processes'][0]
            print(f"✅ Single training process found: PID {proc['pid']}")
            print(f"📊 Memory usage: {proc['memory_mb']}MB")
            print(f"⏰ Started: {proc['create_time']}")
            
            return {
                'action': 'existing_process_found',
                'can_start_new': False,
                'existing_process': proc,
                'recommendation': 'Wait for current training to complete or kill it manually'
            }
        
        # Try to create lockfile
        if not self.create_lockfile({'cmdline': ['train_whis.py']}):
            return {
                'action': 'lockfile_exists',
                'can_start_new': False,
                'message': 'Training lockfile exists - another process may be starting'
            }
        
        print("🚀 Ready to start training - no conflicts detected")
        
        return {
            'action': 'ready_to_start',
            'can_start_new': True,
            'lockfile_created': True
        }
    
    def monitor_training_completion(self, check_interval: int = 30) -> dict:
        """Monitor training and cleanup when complete"""
        print(f"👀 Monitoring training completion (checking every {check_interval}s)")
        
        while True:
            status = self.is_training_running()
            
            if not status['is_running']:
                print("✅ Training completed - cleaning up")
                self.remove_lockfile()
                
                self.log_process_event('training_completed', {
                    'completion_time': datetime.now().isoformat()
                })
                
                return {
                    'status': 'completed',
                    'message': 'Training finished and lockfile removed'
                }
            
            print(f"⏳ Training still running: {status['process_count']} processes")
            time.sleep(check_interval)

def main():
    """Main process management"""
    manager = WhisProcessManager()
    
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "status":
            status = manager.is_training_running()
            print(json.dumps(status, indent=2))
            
        elif command == "cleanup":
            result = manager.kill_duplicate_processes()
            print(json.dumps(result, indent=2))
            
        elif command == "safe-start":
            result = manager.safe_training_start()
            print(json.dumps(result, indent=2))
            
        elif command == "monitor":
            result = manager.monitor_training_completion()
            print(json.dumps(result, indent=2))
            
        else:
            print(f"Unknown command: {command}")
            print("Usage: python process_manager.py [status|cleanup|safe-start|monitor]")
    else:
        # Default: safe start check
        result = manager.safe_training_start()
        print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()