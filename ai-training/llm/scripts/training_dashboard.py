#!/usr/bin/env python3
"""
Real-time Training Dashboard for Whis
Monitor training progress, GPU usage, and pipeline status
"""

import time
import os
import json
import subprocess
from datetime import datetime
from pathlib import Path

def get_gpu_info():
    """Get GPU memory and utilization"""
    try:
        result = subprocess.run(['nvidia-smi', '--query-gpu=memory.used,memory.total,utilization.gpu', '--format=csv,noheader,nounits'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            memory_used, memory_total, gpu_util = result.stdout.strip().split(', ')
            return {
                "memory_used_mb": int(memory_used),
                "memory_total_mb": int(memory_total), 
                "gpu_utilization": int(gpu_util),
                "memory_percent": round(int(memory_used) / int(memory_total) * 100, 1)
            }
    except:
        pass
    return {"error": "GPU info unavailable"}

def get_model_download_status():
    """Check CodeLlama download progress"""
    cache_path = Path.home() / ".cache/huggingface/hub/models--codellama--CodeLlama-7b-Instruct-hf"
    if cache_path.exists():
        size_gb = subprocess.run(['du', '-sh', str(cache_path)], capture_output=True, text=True)
        if size_gb.returncode == 0:
            size = size_gb.stdout.split()[0]
            return {
                "downloaded": True,
                "size": size,
                "estimated_complete": float(size[:-1]) >= 13.0 if size.endswith('G') else False
            }
    return {"downloaded": False}

def get_training_status():
    """Check training process and model directory status"""
    status = {
        "process_running": False,
        "model_dir_exists": False,
        "checkpoints": [],
        "latest_checkpoint": None,
        "training_active": False
    }
    
    # Check if training process is running
    try:
        result = subprocess.run(['pgrep', '-f', 'train_whis.py'], capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            status["process_running"] = True
    except:
        pass
    
    # Check model directory
    model_dir = Path("./whis-cybersec-model")
    if model_dir.exists():
        status["model_dir_exists"] = True
        
        # Check for checkpoints
        checkpoints = list(model_dir.glob("checkpoint-*"))
        if checkpoints:
            status["checkpoints"] = [cp.name for cp in sorted(checkpoints)]
            status["latest_checkpoint"] = status["checkpoints"][-1]
            status["training_active"] = True
    
    return status

def get_preprocessing_status():
    """Check preprocessing pipeline status"""
    processed_dir = Path("./processed_data")
    if processed_dir.exists():
        train_files = list(processed_dir.glob("train_dataset_*.json"))
        if train_files:
            latest_file = max(train_files, key=os.path.getctime)
            with open(latest_file) as f:
                data = json.load(f)
            return {
                "completed": True,
                "train_examples": len(data),
                "latest_file": latest_file.name
            }
    return {"completed": False}

def print_dashboard():
    """Print real-time dashboard"""
    os.system('clear' if os.name == 'posix' else 'cls')
    
    print("🛡️  WHIS CYBERSECURITY LLM TRAINING DASHBOARD")
    print("=" * 70)
    print(f"⏰ Last Updated: {datetime.now().strftime('%H:%M:%S')}")
    
    # GPU Status
    gpu_info = get_gpu_info()
    print(f"\n🚀 GPU STATUS:")
    if "error" not in gpu_info:
        memory_bar = "█" * int(gpu_info["memory_percent"] / 5) + "░" * (20 - int(gpu_info["memory_percent"] / 5))
        util_bar = "█" * int(gpu_info["gpu_utilization"] / 5) + "░" * (20 - int(gpu_info["gpu_utilization"] / 5))
        
        print(f"  Memory: [{memory_bar}] {gpu_info['memory_percent']}% ({gpu_info['memory_used_mb']}MB/{gpu_info['memory_total_mb']}MB)")
        print(f"  Util:   [{util_bar}] {gpu_info['gpu_utilization']}%")
        
        if gpu_info["gpu_utilization"] > 50:
            print("  Status: 🔥 TRAINING ACTIVE")
        elif gpu_info["memory_used_mb"] > 1000:
            print("  Status: ⏳ MODEL LOADED, WAITING")
        else:
            print("  Status: 💤 IDLE")
    else:
        print("  Status: ❌ GPU INFO UNAVAILABLE")
    
    # Model Download Status
    download_info = get_model_download_status()
    print(f"\n📥 MODEL DOWNLOAD:")
    if download_info["downloaded"]:
        if download_info.get("estimated_complete", False):
            print(f"  Status: ✅ COMPLETE ({download_info['size']})")
        else:
            print(f"  Status: ⏳ IN PROGRESS ({download_info['size']})")
    else:
        print("  Status: ❌ NOT STARTED")
    
    # Training Status
    training_info = get_training_status()
    print(f"\n🏋️ TRAINING STATUS:")
    print(f"  Process Running: {'✅' if training_info['process_running'] else '❌'}")
    print(f"  Model Directory: {'✅' if training_info['model_dir_exists'] else '⏳'}")
    
    if training_info["checkpoints"]:
        print(f"  Checkpoints: {len(training_info['checkpoints'])}")
        print(f"  Latest: {training_info['latest_checkpoint']}")
        print("  Status: 🎯 TRAINING IN PROGRESS")
    elif training_info["process_running"]:
        print("  Status: ⏳ INITIALIZING")
    else:
        print("  Status: 💤 NOT STARTED")
    
    # Preprocessing Status
    preprocessing_info = get_preprocessing_status()
    print(f"\n📊 DATA PREPROCESSING:")
    if preprocessing_info["completed"]:
        print(f"  Status: ✅ COMPLETE")
        print(f"  Training Examples: {preprocessing_info['train_examples']}")
        print(f"  Dataset: {preprocessing_info['latest_file']}")
    else:
        print("  Status: ⏳ PENDING")
    
    # Pipeline Status Summary
    print(f"\n🎯 PIPELINE STATUS:")
    
    stages = [
        ("Data Collection", "✅"),
        ("Preprocessing", "✅" if preprocessing_info["completed"] else "⏳"),
        ("Model Download", "✅" if download_info.get("estimated_complete") else "⏳"),
        ("Initial Training", "🔄" if training_info["training_active"] else "⏳"),
        ("Model Testing", "⏳"),
        ("Robust Retraining", "⏳")
    ]
    
    for stage, status in stages:
        print(f"  {stage}: {status}")
    
    # Next Steps
    print(f"\n📋 NEXT STEPS:")
    if not download_info.get("estimated_complete"):
        print("  • Waiting for model download to complete...")
    elif not training_info["training_active"]:
        print("  • Training will begin shortly...")
    elif training_info["training_active"]:
        print("  • Training in progress - monitor for completion")
        print("  • Test model once training finishes")
        print("  • Run robust retraining with 100+ examples")
    
    print("=" * 70)

def main():
    """Main dashboard loop"""
    try:
        while True:
            print_dashboard()
            time.sleep(30)  # Update every 30 seconds
    except KeyboardInterrupt:
        print("\n👋 Dashboard stopped")

if __name__ == "__main__":
    main()