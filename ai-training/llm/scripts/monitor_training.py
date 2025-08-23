#!/usr/bin/env python3
"""
Training Progress Monitor for Whis
Real-time monitoring of fine-tuning progress
"""

import os
import time
import json
import psutil
from pathlib import Path
from datetime import datetime

def check_gpu_usage():
    """Check GPU memory usage"""
    try:
        import torch
        if torch.cuda.is_available():
            gpu_memory = torch.cuda.memory_allocated() / 1e9
            gpu_total = torch.cuda.get_device_properties(0).total_memory / 1e9
            return f"GPU: {gpu_memory:.1f}GB / {gpu_total:.1f}GB ({gpu_memory/gpu_total*100:.1f}%)"
        else:
            return "No GPU available"
    except:
        return "GPU info unavailable"

def check_training_progress():
    """Check training progress from logs and checkpoints"""
    model_dir = Path("./whis-cybersec-model")
    
    info = {
        "timestamp": datetime.now().isoformat(),
        "model_directory_exists": model_dir.exists(),
        "checkpoints": [],
        "logs": [],
        "gpu_status": check_gpu_usage()
    }
    
    # Check for checkpoints
    if model_dir.exists():
        checkpoints = list(model_dir.glob("checkpoint-*"))
        info["checkpoints"] = [cp.name for cp in sorted(checkpoints)]
        
        # Check for training logs
        log_files = list(model_dir.glob("*.log"))
        info["logs"] = [log.name for log in log_files]
        
        # Check for training state
        if (model_dir / "trainer_state.json").exists():
            with open(model_dir / "trainer_state.json") as f:
                trainer_state = json.load(f)
                info["training_state"] = {
                    "epoch": trainer_state.get("epoch", 0),
                    "global_step": trainer_state.get("global_step", 0),
                    "total_flos": trainer_state.get("total_flos", 0)
                }
    
    return info

def monitor_loop():
    """Main monitoring loop"""
    print("🛡️ Whis Training Monitor")
    print("=" * 50)
    
    while True:
        try:
            progress = check_training_progress()
            
            print(f"\n⏰ {progress['timestamp']}")
            print(f"💾 {progress['gpu_status']}")
            
            if progress['model_directory_exists']:
                print(f"📁 Model dir exists: ✅")
                print(f"🏁 Checkpoints: {len(progress['checkpoints'])}")
                
                if progress['checkpoints']:
                    latest_checkpoint = progress['checkpoints'][-1]
                    print(f"📍 Latest: {latest_checkpoint}")
                
                if 'training_state' in progress:
                    state = progress['training_state']
                    print(f"📊 Epoch: {state['epoch']:.2f}")
                    print(f"🔄 Step: {state['global_step']}")
            else:
                print("📁 Model dir: ⏳ Not created yet")
            
            print("-" * 30)
            time.sleep(30)  # Check every 30 seconds
            
        except KeyboardInterrupt:
            print("\n👋 Monitoring stopped")
            break
        except Exception as e:
            print(f"❌ Monitor error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    monitor_loop()