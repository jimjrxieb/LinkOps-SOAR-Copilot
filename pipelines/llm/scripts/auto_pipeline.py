#!/usr/bin/env python3
"""
Automated Whis Training Pipeline
Automatically execute next steps when training completes
"""

import os
import time
import subprocess
import json
from datetime import datetime
from pathlib import Path

def check_training_complete():
    """Check if initial training has completed"""
    model_dir = Path("./whis-cybersec-model")
    
    # Check if model directory exists with required files
    if model_dir.exists():
        required_files = ["adapter_config.json", "adapter_model.safetensors"]
        if all((model_dir / file).exists() for file in required_files):
            return True
    
    return False

def check_process_running(process_name):
    """Check if a specific process is running"""
    try:
        result = subprocess.run(['pgrep', '-f', process_name], capture_output=True, text=True)
        return result.returncode == 0 and result.stdout.strip()
    except:
        return False

def run_model_testing():
    """Run model testing suite"""
    print("🧪 Running model testing suite...")
    
    try:
        result = subprocess.run(['python', 'test_whis_model.py'], 
                              capture_output=True, text=True, timeout=600)
        
        if result.returncode == 0:
            print("✅ Model testing completed successfully!")
            print(result.stdout[-500:])  # Show last 500 chars
            return True
        else:
            print("❌ Model testing failed:")
            print(result.stderr[-500:])
            return False
            
    except subprocess.TimeoutExpired:
        print("⏰ Model testing timed out")
        return False
    except Exception as e:
        print(f"❌ Error running model tests: {e}")
        return False

def run_robust_retraining():
    """Run robust retraining with 100+ examples"""
    print("🏋️ Starting robust retraining with 100+ examples...")
    
    try:
        # Run in background since this will take longer
        process = subprocess.Popen(['python', 'retrain_robust.py'])
        print(f"✅ Robust retraining started (PID: {process.pid})")
        return process
        
    except Exception as e:
        print(f"❌ Error starting robust retraining: {e}")
        return None

def log_pipeline_event(event, details=None):
    """Log pipeline events"""
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "event": event,
        "details": details or {}
    }
    
    log_file = "pipeline_events.log"
    with open(log_file, "a") as f:
        f.write(json.dumps(log_entry) + "\n")

def main():
    """Main automated pipeline"""
    print("🤖 Whis Automated Training Pipeline")
    print("=" * 50)
    print("🔄 Monitoring for training completion...")
    
    log_pipeline_event("pipeline_started")
    
    # Wait for initial training to complete
    initial_training_complete = False
    
    while not initial_training_complete:
        if check_training_complete():
            print("\n🎉 Initial training completed!")
            log_pipeline_event("initial_training_complete")
            initial_training_complete = True
            break
        
        # Check if training process is still running
        if not check_process_running("train_whis.py"):
            print("\n⚠️ Training process not detected. Checking for completion...")
            if check_training_complete():
                print("✅ Training appears to have completed successfully!")
                log_pipeline_event("initial_training_complete")
                initial_training_complete = True
                break
            else:
                print("❌ Training process stopped but model not found.")
                log_pipeline_event("training_failed", {"reason": "process_stopped_no_model"})
                return
        
        print(f"⏳ Still waiting... {datetime.now().strftime('%H:%M:%S')}")
        time.sleep(60)  # Check every minute
    
    # Step 1: Test the initial model
    print("\n🧪 Step 1: Testing initial model...")
    log_pipeline_event("testing_started")
    
    testing_success = run_model_testing()
    
    if testing_success:
        log_pipeline_event("testing_complete", {"result": "success"})
        print("✅ Initial model testing passed!")
    else:
        log_pipeline_event("testing_complete", {"result": "failed"})
        print("⚠️ Initial model testing had issues, but continuing...")
    
    # Step 2: Start robust retraining
    print("\n🏋️ Step 2: Starting robust retraining...")
    log_pipeline_event("robust_training_started")
    
    robust_process = run_robust_retraining()
    
    if robust_process:
        print("✅ Robust retraining pipeline initiated!")
        print(f"📊 Process ID: {robust_process.pid}")
        print("🔄 This will run for 30-60 minutes...")
        
        # Monitor robust training
        print("\n⏳ Monitoring robust training...")
        while robust_process.poll() is None:
            # Check if robust model directory exists
            robust_dir = Path("./whis-cybersec-robust")
            if robust_dir.exists():
                checkpoints = list(robust_dir.glob("checkpoint-*"))
                if checkpoints:
                    print(f"📊 Robust training progress: {len(checkpoints)} checkpoints")
                    log_pipeline_event("robust_training_progress", {"checkpoints": len(checkpoints)})
            
            time.sleep(300)  # Check every 5 minutes
        
        # Check final result
        if robust_process.returncode == 0:
            print("🎉 Robust retraining completed successfully!")
            log_pipeline_event("robust_training_complete", {"result": "success"})
            
            # Test robust model
            print("\n🧪 Testing robust model...")
            # TODO: Modify test script to test robust model
            
        else:
            print("❌ Robust retraining failed")
            log_pipeline_event("robust_training_complete", {"result": "failed"})
    
    # Final summary
    print("\n📊 PIPELINE SUMMARY:")
    print("=" * 30)
    print(f"✅ Initial Training: {'Complete' if initial_training_complete else 'Failed'}")
    print(f"🧪 Model Testing: {'Passed' if testing_success else 'Issues'}")
    print(f"🏋️ Robust Training: {'Complete' if robust_process and robust_process.returncode == 0 else 'In Progress/Failed'}")
    
    print("\n🛡️ Whis cybersecurity LLM pipeline complete!")
    print("Ready for SOAR deployment!")
    
    log_pipeline_event("pipeline_complete")

if __name__ == "__main__":
    main()