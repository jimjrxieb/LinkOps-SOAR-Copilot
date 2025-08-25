#!/usr/bin/env python3
"""
📊 Pipeline Progress Tracker
============================
Utility to write pipeline progress updates for real-time monitoring

Usage:
    from pipelines.utils.progress_tracker import ProgressTracker
    
    tracker = ProgressTracker("intake")
    tracker.start()
    tracker.update(events=1500, message="Processing Splunk data")
    tracker.complete(events=5000, message="Intake completed successfully")
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class ProgressTracker:
    """Tracks and logs pipeline progress for real-time monitoring"""
    
    def __init__(self, stage: str):
        self.stage = stage
        self.progress_dir = Path("/home/jimmie/linkops-industries/SOAR-copilot/results/progress")
        self.progress_dir.mkdir(parents=True, exist_ok=True)
        self.status_file = self.progress_dir / "status.jsonl"
        self.start_time = None
        
    def _write_status(self, status: str, **kwargs):
        """Write status update to JSONL file"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "stage": self.stage,
            "status": status,
            **kwargs
        }
        
        try:
            with open(self.status_file, "a") as f:
                f.write(json.dumps(entry) + "\n")
                
            logger.info(f"Progress update: {self.stage} {status} - {kwargs}")
        except Exception as e:
            logger.error(f"Error writing progress: {e}")
    
    def start(self, message: str = ""):
        """Mark stage as started"""
        self.start_time = datetime.now()
        self._write_status("STARTED", message=message)
    
    def update(self, message: str = "", **metrics):
        """Update progress with current metrics"""
        self._write_status("PROGRESS", message=message, **metrics)
    
    def complete(self, message: str = "", **metrics):
        """Mark stage as completed"""
        duration = None
        if self.start_time:
            duration = (datetime.now() - self.start_time).total_seconds()
            
        self._write_status("COMPLETED", message=message, duration=duration, **metrics)
    
    def fail(self, error: str = "", **metrics):
        """Mark stage as failed"""
        duration = None
        if self.start_time:
            duration = (datetime.now() - self.start_time).total_seconds()
            
        self._write_status("FAILED", error=error, duration=duration, **metrics)
    
    def warning(self, message: str = "", **metrics):
        """Log a warning during processing"""
        self._write_status("WARNING", message=message, **metrics)

# Global progress trackers for convenience
def track_intake_progress():
    return ProgressTracker("intake")

def track_sanitize_progress():
    return ProgressTracker("sanitize")

def track_curate_progress():
    return ProgressTracker("curate")