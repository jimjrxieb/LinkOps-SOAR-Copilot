#!/usr/bin/env python3
"""
📊 Real-time Training Monitor
============================
Monitors SOAR model training progress in real-time
"""

import time
import subprocess
from pathlib import Path
import json

def get_gpu_stats():
    """Get GPU utilization stats"""
    try:
        result = subprocess.run([
            'nvidia-smi', 
            '--query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu',
            '--format=csv,noheader,nounits'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            gpu_util, mem_used, mem_total, temp = result.stdout.strip().split(', ')
            return {
                'utilization': int(gpu_util),
                'memory_used': int(mem_used),
                'memory_total': int(mem_total),
                'temperature': int(temp),
                'memory_pct': int(mem_used) / int(mem_total) * 100
            }
    except:
        pass
    return None

def check_training_logs():
    """Check for training log files"""
    model_dir = Path("models/soar-copilot-phi")
    if model_dir.exists():
        log_files = list(model_dir.glob("*.log")) + list(model_dir.glob("training_args.json"))
        return len(log_files) > 0
    return False

def main():
    print("📊 TRAINING MONITOR STARTED")
    print("=" * 50)
    print("Monitoring: GPU usage, training logs, model checkpoints")
    print("Press Ctrl+C to stop")
    print()
    
    training_started = False
    
    while True:
        try:
            # Get timestamp
            timestamp = time.strftime("%H:%M:%S")
            
            # Get GPU stats
            gpu_stats = get_gpu_stats()
            
            if gpu_stats:
                util = gpu_stats['utilization']
                mem_pct = gpu_stats['memory_pct']
                temp = gpu_stats['temperature']
                
                # Determine training status
                if util > 10 and not training_started:
                    print(f"🚀 [{timestamp}] TRAINING STARTED! GPU active")
                    training_started = True
                
                # Print stats
                status = "🔥 TRAINING" if util > 10 else "⏳ Loading..."
                print(f"{status} [{timestamp}] GPU: {util:2d}% | Memory: {mem_pct:4.1f}% | Temp: {temp}°C")
                
            else:
                print(f"⚠️  [{timestamp}] GPU not available")
            
            # Check for model files
            model_dir = Path("models/soar-copilot-phi")
            if model_dir.exists():
                checkpoints = list(model_dir.glob("checkpoint-*"))
                if checkpoints:
                    latest = sorted(checkpoints)[-1].name
                    print(f"💾 [{timestamp}] Latest checkpoint: {latest}")
            
            time.sleep(10)  # Update every 10 seconds
            
        except KeyboardInterrupt:
            print("\n👋 Training monitor stopped")
            break
        except Exception as e:
            print(f"❌ Monitor error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()