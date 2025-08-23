#!/usr/bin/env python3
"""
Monitor CodeLlama download progress in real-time
"""

import subprocess
import time
import os
from datetime import datetime

def get_cache_size():
    """Get current cache size"""
    cache_path = os.path.expanduser("~/.cache/huggingface/hub/models--codellama--CodeLlama-7b-Instruct-hf")
    try:
        result = subprocess.run(['du', '-sh', cache_path], capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.split()[0]
        return "0B"
    except:
        return "Error"

def main():
    """Monitor download every 10 seconds"""
    print("📥 Monitoring CodeLlama download progress...")
    print("Press Ctrl+C to stop")
    
    try:
        while True:
            size = get_cache_size()
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            # Estimate completion
            if size.endswith('G'):
                size_gb = float(size[:-1])
                if size_gb >= 13.5:
                    print(f"✅ {timestamp} - Download COMPLETE: {size}")
                    break
                else:
                    progress = (size_gb / 13.5) * 100
                    print(f"🔄 {timestamp} - Progress: {size} ({progress:.1f}%)")
            else:
                print(f"⏳ {timestamp} - Size: {size}")
            
            time.sleep(10)
            
    except KeyboardInterrupt:
        print(f"\n👋 Monitoring stopped at {datetime.now().strftime('%H:%M:%S')}")

if __name__ == "__main__":
    main()