#!/usr/bin/env python3
"""Track CodeLlama download progress"""

import subprocess
import time
from datetime import datetime

def get_cache_size():
    try:
        result = subprocess.run(
            ['du', '-sb', '/home/jimmie/.cache/huggingface/hub/models--codellama--CodeLlama-7b-Instruct-hf/'], 
            capture_output=True, text=True
        )
        if result.returncode == 0:
            return int(result.stdout.split()[0])
        return 0
    except:
        return 0

def main():
    print("📥 CodeLlama-7B Download Progress Tracker")
    print("=" * 50)
    
    # Typical CodeLlama-7B size (approximate)
    expected_size = 13.5 * 1024**3  # ~13.5GB in bytes
    
    start_time = time.time()
    last_size = 0
    
    for i in range(20):  # Check 20 times over ~10 minutes
        current_size = get_cache_size()
        progress_pct = (current_size / expected_size) * 100
        
        if current_size > last_size:
            speed_mbps = (current_size - last_size) / (30 * 1024**2) if i > 0 else 0
            
            print(f"⏰ {datetime.now().strftime('%H:%M:%S')}")
            print(f"📦 Downloaded: {current_size / 1024**3:.1f}GB / {expected_size / 1024**3:.1f}GB ({progress_pct:.1f}%)")
            if speed_mbps > 0:
                print(f"🚀 Speed: {speed_mbps:.1f} MB/s")
            
            # Estimate completion time
            if speed_mbps > 0 and progress_pct < 95:
                remaining_gb = (expected_size - current_size) / 1024**3
                eta_minutes = (remaining_gb * 1024) / (speed_mbps * 60)
                print(f"⏳ ETA: ~{eta_minutes:.0f} minutes")
            
            print("-" * 30)
        
        last_size = current_size
        
        if progress_pct >= 95:
            print("✅ Download nearly complete! Training should start soon.")
            break
            
        time.sleep(30)  # Check every 30 seconds

if __name__ == "__main__":
    main()