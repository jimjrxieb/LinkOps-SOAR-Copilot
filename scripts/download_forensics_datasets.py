#!/usr/bin/env python3
"""
🔍 Forensics Datasets Downloader
===============================
Downloads and organizes SIEM/logs/forensics datasets for RAG training

[TAG: FORENSICS-DATASETS] - SIEM log analysis training data
[TAG: INCIDENT-TELEMETRY] - Labeled incident samples
[TAG: DFIR-REASONING] - Digital forensics reasoning datasets
"""

import os
import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime
import logging

# HuggingFace datasets
try:
    from datasets import load_dataset
    HF_AVAILABLE = True
except ImportError:
    print("⚠️  datasets library not available. Install with: pip install datasets")
    HF_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ForensicsDatasetDownloader:
    """Download and organize forensics datasets for RAG training"""
    
    def __init__(self, output_dir: str = "ai-training/rag/forensics-data"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Dataset configurations
        self.datasets = [
            {
                "name": "witfoo/syslog-to-artifact",
                "description": "Syslog lines mapped to security artifacts",
                "sample_size": 1000,
                "text_columns": ["syslog", "artifact"],
                "category": "siem_logs"
            },
            {
                "name": "witfoo/witfoo-incidents", 
                "description": "Labeled incident/telemetry samples",
                "sample_size": 500,
                "text_columns": ["incident_data", "classification"],
                "category": "incident_telemetry"
            },
            {
                "name": "0xyf/windows-log-QnA",
                "description": "Windows event log question-answer pairs",
                "sample_size": 800,
                "text_columns": ["question", "answer"],
                "category": "log_analysis_qa"
            },
            {
                "name": "LockeLamora2077/hayabusa_llm_report_forensic_reasoning",
                "description": "DFIR-style reasoning samples", 
                "sample_size": 200,
                "text_columns": ["question", "reasoning", "answer"],
                "category": "dfir_reasoning"
            }
        ]
        
        self.download_stats = {
            "total_datasets": len(self.datasets),
            "successful_downloads": 0,
            "total_samples": 0,
            "categories": {}
        }
    
    def download_dataset(self, config: Dict[str, Any]) -> bool:
        """Download a single forensics dataset"""
        
        if not HF_AVAILABLE:
            logger.error("❌ HuggingFace datasets library not available")
            return False
        
        dataset_name = config["name"]
        logger.info(f"📥 Downloading {dataset_name}...")
        
        try:
            # Load dataset
            dataset = load_dataset(dataset_name, split="train", streaming=True)
            
            # Create category directory
            category_dir = self.output_dir / config["category"]
            category_dir.mkdir(exist_ok=True)
            
            # Sample and process data
            samples = []
            count = 0
            
            for example in dataset:
                if count >= config["sample_size"]:
                    break
                
                # Extract relevant text fields
                sample_data = {}
                for column in config["text_columns"]:
                    if column in example:
                        sample_data[column] = str(example[column])
                    else:
                        # Try common alternative column names
                        alt_columns = {
                            "incident_data": ["data", "telemetry", "content"],
                            "classification": ["label", "category", "type"],
                            "reasoning": ["analysis", "explanation", "context"]
                        }
                        
                        if column in alt_columns:
                            for alt_col in alt_columns[column]:
                                if alt_col in example:
                                    sample_data[column] = str(example[alt_col])
                                    break
                
                # Only keep samples with meaningful content
                if any(len(str(v)) > 20 for v in sample_data.values()):
                    sample_data["dataset"] = dataset_name
                    sample_data["category"] = config["category"]
                    sample_data["downloaded_at"] = datetime.utcnow().isoformat()
                    samples.append(sample_data)
                    count += 1
            
            # Save as JSONL
            output_file = category_dir / f"{dataset_name.replace('/', '_')}_samples.jsonl"
            with open(output_file, 'w') as f:
                for sample in samples:
                    f.write(json.dumps(sample) + '\n')
            
            # Save metadata
            metadata = {
                "dataset_name": dataset_name,
                "description": config["description"],
                "category": config["category"],
                "sample_count": len(samples),
                "columns": list(config["text_columns"]),
                "file_path": str(output_file),
                "downloaded_at": datetime.utcnow().isoformat()
            }
            
            metadata_file = category_dir / f"{dataset_name.replace('/', '_')}_metadata.json"
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"✅ Downloaded {len(samples)} samples from {dataset_name}")
            logger.info(f"   📁 Data: {output_file}")
            logger.info(f"   📋 Metadata: {metadata_file}")
            
            # Update stats
            self.download_stats["successful_downloads"] += 1
            self.download_stats["total_samples"] += len(samples)
            self.download_stats["categories"][config["category"]] = len(samples)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to download {dataset_name}: {e}")
            return False
    
    def create_combined_dataset(self):
        """Create a combined forensics dataset for RAG ingestion"""
        
        logger.info("🔗 Creating combined forensics dataset...")
        
        combined_samples = []
        
        # Collect all samples from different categories
        for category_dir in self.output_dir.iterdir():
            if category_dir.is_dir():
                for jsonl_file in category_dir.glob("*_samples.jsonl"):
                    with open(jsonl_file, 'r') as f:
                        for line in f:
                            sample = json.loads(line.strip())
                            combined_samples.append(sample)
        
        # Save combined dataset
        combined_file = self.output_dir / "combined_forensics_dataset.jsonl"
        with open(combined_file, 'w') as f:
            for sample in combined_samples:
                f.write(json.dumps(sample) + '\n')
        
        # Create comprehensive metadata
        combined_metadata = {
            "combined_dataset": True,
            "total_samples": len(combined_samples),
            "categories": {},
            "datasets": [],
            "created_at": datetime.utcnow().isoformat(),
            "description": "Combined forensics and SIEM datasets for RAG training"
        }
        
        # Aggregate category stats
        for sample in combined_samples:
            category = sample.get("category", "unknown")
            if category not in combined_metadata["categories"]:
                combined_metadata["categories"][category] = 0
            combined_metadata["categories"][category] += 1
            
            dataset = sample.get("dataset", "unknown")
            if dataset not in combined_metadata["datasets"]:
                combined_metadata["datasets"].append(dataset)
        
        metadata_file = self.output_dir / "combined_forensics_metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(combined_metadata, f, indent=2)
        
        logger.info(f"✅ Combined dataset created: {combined_file}")
        logger.info(f"   📊 Total samples: {len(combined_samples)}")
        logger.info(f"   📋 Metadata: {metadata_file}")
        
        return combined_file, metadata_file
    
    def generate_rag_chunks(self):
        """Generate RAG-ready chunks from forensics data"""
        
        logger.info("🧩 Generating RAG chunks from forensics data...")
        
        chunks_dir = Path("ai-training/rag/chunks/forensics")
        chunks_dir.mkdir(parents=True, exist_ok=True)
        
        chunk_count = 0
        
        # Process each category
        for category_dir in self.output_dir.iterdir():
            if category_dir.is_dir():
                for jsonl_file in category_dir.glob("*_samples.jsonl"):
                    dataset_name = jsonl_file.stem.replace("_samples", "")
                    
                    with open(jsonl_file, 'r') as f:
                        for i, line in enumerate(f):
                            sample = json.loads(line.strip())
                            
                            # Create RAG chunk based on category
                            if sample["category"] == "siem_logs":
                                chunk_content = self._create_siem_chunk(sample)
                            elif sample["category"] == "incident_telemetry":
                                chunk_content = self._create_incident_chunk(sample)
                            elif sample["category"] == "log_analysis_qa":
                                chunk_content = self._create_qa_chunk(sample)
                            elif sample["category"] == "dfir_reasoning":
                                chunk_content = self._create_dfir_chunk(sample)
                            else:
                                continue
                            
                            # Save individual chunk
                            chunk_file = chunks_dir / f"{dataset_name}_{i}.md"
                            with open(chunk_file, 'w') as cf:
                                cf.write(chunk_content)
                            
                            chunk_count += 1
        
        logger.info(f"✅ Generated {chunk_count} RAG chunks in {chunks_dir}")
        return chunks_dir, chunk_count
    
    def _create_siem_chunk(self, sample: Dict[str, Any]) -> str:
        """Create SIEM log analysis chunk"""
        return f"""# SIEM Log Analysis

**Log Entry**: {sample.get('syslog', 'N/A')}

**Security Artifact**: {sample.get('artifact', 'N/A')}

**Analysis**: This syslog entry indicates {sample.get('artifact', 'security').lower()} activity that should be investigated by security analysts.

**Dataset**: {sample.get('dataset', 'Unknown')}
**Category**: SIEM Log Analysis
"""
    
    def _create_incident_chunk(self, sample: Dict[str, Any]) -> str:
        """Create incident telemetry chunk"""
        return f"""# Security Incident Analysis

**Incident Data**: {sample.get('incident_data', 'N/A')}

**Classification**: {sample.get('classification', 'N/A')}

**Analysis**: This telemetry data represents a {sample.get('classification', 'security').lower()} incident that requires security team attention.

**Dataset**: {sample.get('dataset', 'Unknown')}
**Category**: Incident Telemetry
"""
    
    def _create_qa_chunk(self, sample: Dict[str, Any]) -> str:
        """Create Q&A chunk for log analysis"""
        return f"""# Windows Log Analysis Q&A

**Question**: {sample.get('question', 'N/A')}

**Answer**: {sample.get('answer', 'N/A')}

**Analysis**: This Windows event log question and answer helps security analysts understand log analysis techniques and event interpretation.

**Dataset**: {sample.get('dataset', 'Unknown')}
**Category**: Log Analysis Q&A
"""
    
    def _create_dfir_chunk(self, sample: Dict[str, Any]) -> str:
        """Create DFIR reasoning chunk"""
        content = f"""# Digital Forensics & Incident Response

**Question**: {sample.get('question', 'N/A')}

"""
        if sample.get('reasoning'):
            content += f"**Forensic Reasoning**: {sample.get('reasoning')}\n\n"
        
        content += f"""**Answer**: {sample.get('answer', 'N/A')}

**Analysis**: This DFIR scenario demonstrates forensic reasoning and incident response techniques used by security analysts.

**Dataset**: {sample.get('dataset', 'Unknown')}
**Category**: DFIR Reasoning
"""
        return content
    
    def run_download_pipeline(self):
        """Run the complete forensics dataset download pipeline"""
        
        logger.info("🚀 Starting forensics datasets download pipeline...")
        
        if not HF_AVAILABLE:
            logger.error("❌ HuggingFace datasets library required. Install with: pip install datasets")
            return False
        
        # Download each dataset
        for config in self.datasets:
            success = self.download_dataset(config)
            if not success:
                logger.warning(f"⚠️  Failed to download {config['name']}, continuing...")
        
        # Create combined dataset
        combined_file, metadata_file = self.create_combined_dataset()
        
        # Generate RAG chunks
        chunks_dir, chunk_count = self.generate_rag_chunks()
        
        # Final report
        print(f"\n🎉 FORENSICS DATASETS DOWNLOAD COMPLETE!")
        print("=" * 50)
        print(f"📊 Successfully downloaded: {self.download_stats['successful_downloads']}/{self.download_stats['total_datasets']} datasets")
        print(f"📈 Total samples: {self.download_stats['total_samples']}")
        print(f"🧩 RAG chunks generated: {chunk_count}")
        print(f"📁 Data directory: {self.output_dir}")
        print(f"🔗 Combined dataset: {combined_file}")
        print(f"📋 Metadata: {metadata_file}")
        print(f"🧩 RAG chunks: {chunks_dir}")
        
        print(f"\n📂 Category breakdown:")
        for category, count in self.download_stats["categories"].items():
            print(f"  - {category}: {count} samples")
        
        print(f"\n✅ Ready for RAG integration!")
        return True

def main():
    """Main execution function"""
    print("🔍 Forensics Datasets Downloader")
    print("=" * 40)
    
    downloader = ForensicsDatasetDownloader()
    success = downloader.run_download_pipeline()
    
    if success:
        print("\n🔗 Next steps:")
        print("1. Update your RAG knowledge base builder to include forensics chunks")
        print("2. Run the knowledge base rebuild to integrate forensics data")
        print("3. Test WHIS with forensics-related questions")
    else:
        print("\n❌ Download pipeline failed")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())