#!/usr/bin/env python3
"""
🎯 External Dataset Integration Script
======================================
Integrates Primus, Purple Team, and Open-MalSec datasets into the pipeline

Usage: python3 scripts/integrate_external_datasets.py
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatasetIntegrator:
    """Integrates external security datasets into Whis pipeline"""
    
    def __init__(self):
        self.base_dir = Path("/home/jimmie/linkops-industries/SOAR-copilot")
        self.external_dir = self.base_dir / "ai-training/llm/data/external"
        self.intake_dir = self.base_dir / "data/intake/external"
        self.external_dir.mkdir(parents=True, exist_ok=True)
        self.intake_dir.mkdir(parents=True, exist_ok=True)
        
    def process_primus_dataset(self) -> int:
        """Process Primus multi-agent security dataset"""
        primus_dir = self.external_dir / "primus"
        
        if not primus_dir.exists():
            logger.warning(f"Primus dataset not found at {primus_dir}")
            logger.info("Download with: git clone https://huggingface.co/datasets/trendmicro-ailab/Primus-Security")
            return 0
            
        # Convert Primus format to intake format
        processed = 0
        output_file = self.intake_dir / "primus_security_scenarios.jsonl"
        
        # Process Primus JSONL files
        for jsonl_file in primus_dir.glob("*.jsonl"):
            logger.info(f"Processing Primus file: {jsonl_file.name}")
            
            with open(jsonl_file, 'r') as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        
                        # Convert to intake format
                        intake_event = {
                            "event_id": f"primus_{processed:05d}",
                            "rule_name": data.get("scenario", "Multi-Agent Security Scenario"),
                            "severity": data.get("severity", "medium"),
                            "description": data.get("description", ""),
                            "mitre_technique": data.get("mitre", ""),
                            "response": data.get("response", ""),
                            "source": "primus",
                            "_time": "2025-08-23T12:00:00Z"
                        }
                        
                        with open(output_file, 'a') as out:
                            out.write(json.dumps(intake_event) + '\n')
                        
                        processed += 1
                        
                    except Exception as e:
                        logger.error(f"Error processing Primus entry: {e}")
        
        logger.info(f"✅ Processed {processed} Primus scenarios → {output_file}")
        return processed
    
    def process_purple_team_dataset(self) -> int:
        """Process Purple Team cybersecurity dataset"""
        purple_dir = self.external_dir / "purple_team"
        
        if not purple_dir.exists():
            logger.warning(f"Purple Team dataset not found at {purple_dir}")
            logger.info("Download with: git clone https://huggingface.co/datasets/Canstralian/Purple-Team-Cybersecurity-Dataset")
            return 0
            
        processed = 0
        output_file = self.intake_dir / "purple_team_scenarios.jsonl"
        
        # Process Purple Team files
        for data_file in purple_dir.glob("*.json*"):
            logger.info(f"Processing Purple Team file: {data_file.name}")
            
            try:
                if data_file.suffix == '.json':
                    with open(data_file, 'r') as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            items = data
                        else:
                            items = [data]
                else:  # JSONL
                    items = []
                    with open(data_file, 'r') as f:
                        for line in f:
                            items.append(json.loads(line))
                
                for item in items:
                    # Convert to intake format
                    intake_event = {
                        "event_id": f"purple_{processed:05d}",
                        "rule_name": item.get("attack_name", "Purple Team Exercise"),
                        "severity": item.get("severity", "high"),
                        "red_team_action": item.get("red_team", ""),
                        "blue_team_response": item.get("blue_team", ""),
                        "mitre_technique": item.get("mitre_attack", ""),
                        "source": "purple_team",
                        "_time": "2025-08-23T12:00:00Z"
                    }
                    
                    with open(output_file, 'a') as out:
                        out.write(json.dumps(intake_event) + '\n')
                    
                    processed += 1
                    
            except Exception as e:
                logger.error(f"Error processing Purple Team entry: {e}")
        
        logger.info(f"✅ Processed {processed} Purple Team scenarios → {output_file}")
        return processed
    
    def process_open_malsec_dataset(self) -> int:
        """Process Open-MalSec malware analysis dataset"""
        malsec_dir = self.external_dir / "open_malsec"
        
        if not malsec_dir.exists():
            logger.warning(f"Open-MalSec dataset not found at {malsec_dir}")
            logger.info("Download with: git clone https://huggingface.co/datasets/tegridydev/open-malsec")
            return 0
            
        processed = 0
        output_file = self.intake_dir / "open_malsec_malware.jsonl"
        
        # Process Open-MalSec files
        for data_file in malsec_dir.glob("*.json*"):
            logger.info(f"Processing Open-MalSec file: {data_file.name}")
            
            try:
                with open(data_file, 'r') as f:
                    for line in f:
                        try:
                            data = json.loads(line) if data_file.suffix == '.jsonl' else json.load(f)
                            
                            # Convert to intake format
                            intake_event = {
                                "event_id": f"malsec_{processed:05d}",
                                "rule_name": "Malware Analysis",
                                "severity": "critical",
                                "malware_family": data.get("family", "Unknown"),
                                "malware_type": data.get("type", ""),
                                "iocs": data.get("iocs", []),
                                "analysis": data.get("analysis", ""),
                                "mitre_technique": data.get("techniques", ""),
                                "source": "open_malsec",
                                "_time": "2025-08-23T12:00:00Z"
                            }
                            
                            with open(output_file, 'a') as out:
                                out.write(json.dumps(intake_event) + '\n')
                            
                            processed += 1
                            
                        except Exception as e:
                            logger.error(f"Error processing MalSec entry: {e}")
                            
            except Exception as e:
                logger.error(f"Error reading MalSec file: {e}")
        
        logger.info(f"✅ Processed {processed} Open-MalSec samples → {output_file}")
        return processed
    
    def create_integration_manifest(self, stats: Dict[str, int]):
        """Create manifest for integrated datasets"""
        manifest = {
            "integration_date": "2025-08-23T12:00:00Z",
            "datasets": {
                "primus": {
                    "events": stats.get("primus", 0),
                    "source": "trendmicro-ailab/Primus-Security",
                    "type": "multi-agent security scenarios"
                },
                "purple_team": {
                    "events": stats.get("purple_team", 0),
                    "source": "Canstralian/Purple-Team-Cybersecurity-Dataset",
                    "type": "red/blue team exercises"
                },
                "open_malsec": {
                    "events": stats.get("open_malsec", 0),
                    "source": "tegridydev/open-malsec",
                    "type": "malware analysis"
                }
            },
            "total_events": sum(stats.values()),
            "output_directory": str(self.intake_dir)
        }
        
        manifest_file = self.base_dir / "data/manifests/external_datasets_manifest.json"
        manifest_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(manifest_file, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        logger.info(f"📋 Integration manifest saved: {manifest_file}")
        return manifest_file
    
    def run_integration(self):
        """Run full dataset integration"""
        print("🎯 EXTERNAL DATASET INTEGRATION")
        print("=" * 60)
        
        stats = {}
        
        # Process each dataset
        print("\n📚 Processing Primus Security Dataset...")
        stats["primus"] = self.process_primus_dataset()
        
        print("\n🟣 Processing Purple Team Dataset...")
        stats["purple_team"] = self.process_purple_team_dataset()
        
        print("\n🦠 Processing Open-MalSec Dataset...")
        stats["open_malsec"] = self.process_open_malsec_dataset()
        
        # Create manifest
        manifest_path = self.create_integration_manifest(stats)
        
        # Summary
        print("\n" + "=" * 60)
        print("✅ INTEGRATION COMPLETE!")
        print(f"Total events processed: {sum(stats.values())}")
        print(f"Output directory: {self.intake_dir}")
        print(f"Manifest: {manifest_path}")
        
        print("\n📝 Next Steps:")
        print("1. Run: make sanitize   # Clean and normalize data")
        print("2. Run: make curate     # Generate training pairs")
        print("3. View: http://localhost:8000  # Monitor pipeline progress")
        
        return stats

if __name__ == "__main__":
    integrator = DatasetIntegrator()
    integrator.run_integration()