#!/usr/bin/env python3
"""
📥 Download Forensics & SIEM Datasets for WHIS
==============================================
Fetches specialized log analysis and forensics datasets

Datasets:
- witfoo/syslog-to-artifact - Syslog to security artifacts mapping
- witfoo/witfoo-incidents - Labeled incident telemetry
- 0xyf/windows-log-QnA - Windows event log Q&A (already have)
- LockeLamora2077/hayabusa_llm_report_forensic_reasoning - DFIR reasoning
"""

import os
import json
from pathlib import Path
from datasets import load_dataset
import logging
from tqdm import tqdm

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ForensicsDatasetDownloader:
    def __init__(self, output_dir: str = "data/forensics"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.datasets = [
            {
                "name": "witfoo/syslog-to-artifact",
                "description": "Syslog lines mapped to security artifacts",
                "max_samples": 1000
            },
            {
                "name": "witfoo/witfoo-incidents", 
                "description": "Labeled incident and telemetry samples",
                "max_samples": 1000
            },
            {
                "name": "LockeLamora2077/hayabusa_llm_report_forensic_reasoning",
                "description": "DFIR-style forensic reasoning samples",
                "max_samples": 500
            }
        ]
    
    def download_all(self):
        """Download all forensics datasets"""
        
        logger.info("📥 Starting forensics dataset downloads...")
        
        for dataset_config in self.datasets:
            self.download_dataset(dataset_config)
        
        logger.info("✅ All datasets downloaded successfully!")
    
    def download_dataset(self, config: dict):
        """Download a single dataset"""
        
        dataset_name = config["name"]
        logger.info(f"\n📥 Downloading {dataset_name}...")
        logger.info(f"   {config['description']}")
        
        try:
            # Load dataset
            dataset = load_dataset(dataset_name, split="train")
            
            # Create output directory
            dataset_slug = dataset_name.replace("/", "_")
            dataset_dir = self.output_dir / dataset_slug
            dataset_dir.mkdir(exist_ok=True)
            
            # Process samples
            samples = []
            max_samples = min(config.get("max_samples", 1000), len(dataset))
            
            for i in tqdm(range(max_samples), desc=f"Processing {dataset_name}"):
                sample = dataset[i]
                
                # Normalize the sample structure
                normalized = self.normalize_sample(sample, dataset_name)
                if normalized:
                    samples.append(normalized)
            
            # Save to JSON
            output_file = dataset_dir / "samples.json"
            with open(output_file, 'w') as f:
                json.dump({
                    "dataset": dataset_name,
                    "description": config["description"],
                    "sample_count": len(samples),
                    "samples": samples
                }, f, indent=2)
            
            logger.info(f"✅ Saved {len(samples)} samples to {output_file}")
            
            # Create summary for RAG ingestion
            self.create_rag_summary(dataset_name, samples, dataset_dir)
            
        except Exception as e:
            logger.error(f"❌ Failed to download {dataset_name}: {e}")
    
    def normalize_sample(self, sample: dict, dataset_name: str) -> dict:
        """Normalize dataset samples to common format"""
        
        normalized = {
            "source_dataset": dataset_name,
            "type": "forensics"
        }
        
        # Dataset-specific normalization
        if "syslog-to-artifact" in dataset_name:
            normalized.update({
                "log_line": sample.get("syslog_line", sample.get("text", "")),
                "artifact": sample.get("artifact", sample.get("label", "")),
                "category": "syslog_analysis"
            })
        
        elif "witfoo-incidents" in dataset_name:
            normalized.update({
                "incident_type": sample.get("incident_type", "unknown"),
                "telemetry": sample.get("telemetry", sample.get("text", "")),
                "severity": sample.get("severity", "medium"),
                "category": "incident_telemetry"
            })
        
        elif "hayabusa" in dataset_name:
            normalized.update({
                "forensic_question": sample.get("question", sample.get("input", "")),
                "forensic_analysis": sample.get("answer", sample.get("output", "")),
                "reasoning": sample.get("reasoning", ""),
                "category": "dfir_reasoning"
            })
        
        else:
            # Generic normalization
            normalized.update({
                "text": str(sample.get("text", sample)),
                "label": sample.get("label", ""),
                "category": "generic_forensics"
            })
        
        return normalized
    
    def create_rag_summary(self, dataset_name: str, samples: list, output_dir: Path):
        """Create summary chunks for RAG ingestion"""
        
        logger.info(f"📝 Creating RAG summary for {dataset_name}...")
        
        # Group samples by category
        categories = {}
        for sample in samples:
            cat = sample.get("category", "unknown")
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(sample)
        
        # Create summary chunks
        rag_chunks = []
        
        for category, cat_samples in categories.items():
            # Create category overview chunk
            chunk_content = f"# Forensics Knowledge: {category.replace('_', ' ').title()}\n\n"
            chunk_content += f"**Source Dataset**: {dataset_name}\n\n"
            chunk_content += f"**Sample Count**: {len(cat_samples)}\n\n"
            
            # Add representative examples
            chunk_content += "## Representative Examples:\n\n"
            
            for sample in cat_samples[:5]:  # First 5 examples
                if "syslog" in category:
                    chunk_content += f"- **Log**: `{sample.get('log_line', '')[:100]}`\n"
                    chunk_content += f"  **Artifact**: {sample.get('artifact', 'unknown')}\n\n"
                
                elif "incident" in category:
                    chunk_content += f"- **Type**: {sample.get('incident_type', 'unknown')}\n"
                    chunk_content += f"  **Severity**: {sample.get('severity', 'unknown')}\n"
                    chunk_content += f"  **Telemetry**: {sample.get('telemetry', '')[:150]}...\n\n"
                
                elif "dfir" in category:
                    chunk_content += f"- **Question**: {sample.get('forensic_question', '')[:100]}\n"
                    chunk_content += f"  **Analysis**: {sample.get('forensic_analysis', '')[:150]}...\n\n"
            
            rag_chunks.append({
                "id": f"forensics_{dataset_name.replace('/', '_')}_{category}",
                "content": chunk_content,
                "title": f"Forensics: {category.replace('_', ' ').title()}",
                "source": dataset_name,
                "category": "forensics_knowledge",
                "type": "reference"
            })
        
        # Save RAG chunks
        rag_file = output_dir / "rag_chunks.json"
        with open(rag_file, 'w') as f:
            json.dump(rag_chunks, f, indent=2)
        
        logger.info(f"✅ Created {len(rag_chunks)} RAG chunks")

def main():
    """Download all forensics datasets"""
    downloader = ForensicsDatasetDownloader()
    downloader.download_all()
    
    print("\n✅ Forensics datasets ready for integration!")
    print("Next steps:")
    print("1. Run knowledge base builder to integrate forensics data")
    print("2. Execute teacher pipeline for synthetic test generation")
    print("3. Run training session with expanded datasets")

if __name__ == "__main__":
    main()