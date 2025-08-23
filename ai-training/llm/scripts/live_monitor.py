#!/usr/bin/env python3
"""
Live Training Monitor for Whis LLM
Updates every 5 seconds with visual progress
"""

import time
import psutil
import subprocess
from datetime import datetime
from pathlib import Path
import json

def get_gpu_stats():
    """Get GPU utilization stats"""
    try:
        result = subprocess.run([
            'nvidia-smi', '--query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu',
            '--format=csv,noheader,nounits'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            parts = result.stdout.strip().split(', ')
            return {
                'util': int(parts[0]),
                'memory_used': int(parts[1]),
                'memory_total': int(parts[2]),
                'temp': int(parts[3])
            }
    except:
        pass
    return None

def get_training_process():
    """Find training process"""
    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'memory_info', 'cpu_percent']):
        try:
            cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
            if 'train_whis' in cmdline or 'safe_train_whis' in cmdline:
                return {
                    'pid': proc.info['pid'],
                    'memory_mb': proc.info['memory_info'].rss / (1024*1024),
                    'cpu_percent': proc.cpu_percent(interval=0.1)
                }
        except:
            continue
    return None

def check_model_files():
    """Check for model output files"""
    model_dirs = [
        Path('./whis-cybersec-model'),
        Path('./models/whis-cybersec-model'),
        Path('./results/whis-cybersec-model')
    ]
    
    for model_dir in model_dirs:
        if model_dir.exists():
            adapter_files = list(model_dir.glob('adapter*.safetensors'))
            if adapter_files:
                return {
                    'found': True,
                    'path': str(model_dir),
                    'adapter_count': len(adapter_files),
                    'size_mb': sum(f.stat().st_size for f in adapter_files) / (1024*1024)
                }
    return {'found': False}

def create_progress_bar(value, max_value, width=50):
    """Create ASCII progress bar"""
    if max_value == 0:
        return '[' + '?' * width + ']'
    
    filled = int((value / max_value) * width)
    bar = '█' * filled + '░' * (width - filled)
    percent = (value / max_value) * 100
    return f'[{bar}] {percent:.1f}%'

def monitor_training():
    """Main monitoring loop"""
    
    print("🔍 Starting Whis Training Monitor...")
    print("📁 Monitor file: training_monitor.txt")
    print("🔄 Updating every 5 seconds...")
    print("-" * 60)
    
    iteration = 0
    start_time = time.time()
    
    while True:
        iteration += 1
        elapsed = time.time() - start_time
        
        # Gather stats
        gpu_stats = get_gpu_stats()
        process = get_training_process()
        model_files = check_model_files()
        
        # Build status display
        output = []
        output.append("=" * 70)
        output.append("🎯 WHIS LLM TRAINING MONITOR - LIVE PIPELINE")
        output.append("=" * 70)
        output.append(f"📅 Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        output.append(f"⏱️ Running Time: {int(elapsed)}s | Iteration: {iteration}")
        output.append("")
        
        # Process status
        output.append("📊 TRAINING PROCESS:")
        output.append("-" * 30)
        if process:
            output.append(f"✅ Status: ACTIVE (PID {process['pid']})")
            output.append(f"💾 RAM Usage: {process['memory_mb']:.1f} MB")
            output.append(f"🖥️ CPU Usage: {process['cpu_percent']:.1f}%")
        else:
            output.append("❌ Status: NOT RUNNING")
        output.append("")
        
        # GPU status
        output.append("🎮 GPU STATUS:")
        output.append("-" * 30)
        if gpu_stats:
            output.append(f"⚡ Utilization: {create_progress_bar(gpu_stats['util'], 100)}")
            output.append(f"💾 VRAM: {gpu_stats['memory_used']}MB / {gpu_stats['memory_total']}MB")
            temp_f = (gpu_stats['temp'] * 9/5) + 32
            output.append(f"🌡️ Temperature: {temp_f:.1f}°F")
            
            # Training phase detection
            if gpu_stats['util'] > 80:
                output.append("🚀 Phase: ACTIVE TRAINING")
            elif gpu_stats['memory_used'] > 5000:
                output.append("📦 Phase: MODEL LOADED")
            elif gpu_stats['memory_used'] > 1000:
                output.append("⏳ Phase: LOADING MODEL")
            else:
                output.append("🔄 Phase: INITIALIZING")
        else:
            output.append("❌ GPU not detected")
        output.append("")
        
        # LLM Pipeline Stages
        output.append("🔧 LLM FINE-TUNING PIPELINE:")
        output.append("-" * 30)
        
        stages = [
            ("1. Load Dataset", process is not None),
            ("2. Load Base Model", gpu_stats and gpu_stats['memory_used'] > 1000),
            ("3. Apply LoRA Adapters", gpu_stats and gpu_stats['memory_used'] > 5000),
            ("4. Training Loop", gpu_stats and gpu_stats['util'] > 50),
            ("5. Save Checkpoint", model_files['found']),
            ("6. Complete", False)
        ]
        
        for stage, completed in stages:
            status = "✅" if completed else "⏳"
            output.append(f"{status} {stage}")
        output.append("")
        
        # Model output
        output.append("💾 MODEL OUTPUT:")
        output.append("-" * 30)
        if model_files['found']:
            output.append(f"✅ LoRA Adapter Found!")
            output.append(f"📁 Path: {model_files['path']}")
            output.append(f"📦 Size: {model_files['size_mb']:.2f} MB")
            output.append(f"📑 Files: {model_files['adapter_count']} adapter files")
        else:
            output.append("⏳ No model output yet...")
        output.append("")
        
        # Training parameters
        output.append("⚙️ CONFIGURATION:")
        output.append("-" * 30)
        output.append("📚 Base Model: CodeLlama-7b-Instruct")
        output.append("🔧 Method: LoRA (Low-Rank Adaptation)")
        output.append("📊 Dataset: 23 cybersecurity examples")
        output.append("🎯 Optimization: 4-bit quantization")
        output.append("")
        
        # Visual separator
        output.append("=" * 70)
        
        # Write to file
        monitor_file = Path("training_monitor.txt")
        with open(monitor_file, 'w') as f:
            f.write('\n'.join(output))
        
        # Also print to console
        print(f"\r⏱️ Iteration {iteration} | GPU: {gpu_stats['util'] if gpu_stats else 0}% | "
              f"VRAM: {gpu_stats['memory_used'] if gpu_stats else 0}MB | "
              f"{'✅ MODEL SAVED' if model_files['found'] else '⏳ Training...'}", end="")
        
        # Check if training completed
        if model_files['found'] and not process:
            print("\n\n🎉 TRAINING COMPLETED!")
            print(f"✅ Model saved at: {model_files['path']}")
            break
        
        time.sleep(5)

if __name__ == "__main__":
    try:
        monitor_training()
    except KeyboardInterrupt:
        print("\n\n👋 Monitor stopped by user")