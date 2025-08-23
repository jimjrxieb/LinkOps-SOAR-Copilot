#!/usr/bin/env python3
"""
Safe Whis Training with Process Management
Prevents duplicate processes and provides better monitoring
"""

import sys
import os
import signal
import atexit
from pathlib import Path
from process_manager import WhisProcessManager

# Initialize process manager
manager = WhisProcessManager()

def cleanup_on_exit():
    """Cleanup function called on exit"""
    print("\n🧹 Cleaning up training process...")
    manager.remove_lockfile()

def signal_handler(signum, frame):
    """Handle interruption signals"""
    print(f"\n🛑 Received signal {signum} - cleaning up...")
    manager.remove_lockfile()
    sys.exit(0)

# Register cleanup handlers
atexit.register(cleanup_on_exit)
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def main():
    """Main safe training workflow"""
    print("🛡️ SAFE WHIS TRAINING WITH PROCESS MANAGEMENT")
    print("=" * 60)
    
    # Check for conflicts and cleanup
    start_check = manager.safe_training_start()
    
    if not start_check['can_start_new']:
        print(f"❌ Cannot start training: {start_check.get('message', 'Unknown reason')}")
        
        if start_check.get('existing_process'):
            proc = start_check['existing_process']
            print(f"📍 Existing process: PID {proc['pid']} using {proc['memory_mb']}MB")
            
            user_input = input("\\nKill existing process and start fresh? (y/N): ").strip().lower()
            
            if user_input == 'y':
                print("🔪 Killing existing process...")
                kill_result = manager.kill_duplicate_processes(keep_newest=False)
                print(f"✅ {kill_result['message']}")
                
                # Wait and retry
                import time
                time.sleep(3)
                
                start_check = manager.safe_training_start()
                if not start_check['can_start_new']:
                    print("❌ Still cannot start training")
                    return False
            else:
                print("👋 Exiting - existing training continues")
                return False
    
    print("🚀 Starting safe training process...")
    
    # Import and run original training logic
    try:
        # Import the original training script content
        import train_whis
        
        print("📚 Imported training module successfully")
        
        # Run training if it has a main function
        if hasattr(train_whis, 'main'):
            result = train_whis.main()
        else:
            # Execute the training logic directly
            exec(open('train_whis.py').read())
            result = True
        
        if result:
            print("✅ Training completed successfully!")
            manager.log_process_event('training_success', {
                'completion_time': datetime.now().isoformat()
            })
        else:
            print("⚠️ Training completed with warnings")
            
    except ImportError:
        print("📝 Running training script directly...")
        
        # Run the original script as subprocess for better isolation
        import subprocess
        
        try:
            result = subprocess.run([
                sys.executable, 'train_whis.py'
            ], check=True)
            
            print("✅ Training subprocess completed successfully!")
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Training failed with exit code: {e.returncode}")
            manager.log_process_event('training_failed', {
                'error_code': e.returncode,
                'error_time': datetime.now().isoformat()
            })
            return False
            
    except KeyboardInterrupt:
        print("\\n🛑 Training interrupted by user")
        return False
        
    except Exception as e:
        print(f"❌ Training failed with error: {e}")
        manager.log_process_event('training_error', {
            'error': str(e),
            'error_time': datetime.now().isoformat()
        })
        return False
    
    finally:
        # Always cleanup
        manager.remove_lockfile()
    
    return True

if __name__ == "__main__":
    from datetime import datetime
    
    success = main()
    
    if success:
        print("\\n🎉 SAFE TRAINING COMPLETED SUCCESSFULLY!")
        print("🔗 Ready for HuggingFace Hub upload")
    else:
        print("\\n❌ Training did not complete successfully")
    
    exit(0 if success else 1)