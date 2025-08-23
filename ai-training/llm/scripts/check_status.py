#!/usr/bin/env python3
"""Quick training status checker"""

import os
import torch
from pathlib import Path
from datetime import datetime

def check_status():
    print(f"🛡️ Whis Training Status - {datetime.now().strftime('%H:%M:%S')}")
    print("=" * 50)
    
    # Check model directory
    model_dir = Path("./whis-cybersec-model")
    if model_dir.exists():
        checkpoints = list(model_dir.glob("checkpoint-*"))
        print(f"📁 Model directory: ✅ ({len(checkpoints)} checkpoints)")
        
        if checkpoints:
            latest = sorted(checkpoints)[-1]
            print(f"📍 Latest checkpoint: {latest.name}")
    else:
        print("📁 Model directory: ⏳ Still initializing...")
    
    # Check GPU status
    if torch.cuda.is_available():
        allocated = torch.cuda.memory_allocated() / 1e9
        total = torch.cuda.get_device_properties(0).total_memory / 1e9
        print(f"🚀 GPU Memory: {allocated:.1f}GB / {total:.1f}GB ({allocated/total*100:.1f}%)")
        
        if allocated > 1:
            print("✅ Training is actively using GPU!")
        elif allocated > 0.1:
            print("🔄 Model loading into GPU...")
        else:
            print("⏳ Waiting for GPU utilization...")
    else:
        print("❌ No GPU available")
    
    print("=" * 50)

if __name__ == "__main__":
    check_status()