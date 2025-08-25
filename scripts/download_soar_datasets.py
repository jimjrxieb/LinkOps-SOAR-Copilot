#!/usr/bin/env python3
"""
🚀 SOAR Datasets Downloader - Making WHIS the Greatest SOAR Copilot Ever!
========================================================================
Downloads incident response playbooks and security operations datasets

[TAG: SOAR-EXCELLENCE] - Building the ultimate security operations copilot
[TAG: IR-PLAYBOOKS] - NIST-style incident response playbooks
[TAG: SECURITY-OPS] - Modern security operations instructions
"""

import os
import json
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

class SOARDatasetsDownloader:
    """Download and integrate SOAR/IR datasets to build the greatest security copilot"""
    
    def __init__(self, output_dir: str = "ai-training/rag/soar-data"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Elite SOAR datasets for the ultimate copilot
        self.datasets = [
            {
                "name": "agamage/incident-response-playbook-samples",
                "description": "NIST-style incident response playbooks",
                "sample_size": 300,
                "category": "ir_playbooks",
                "priority": "high"
            },
            {
                "name": "agamage/incident-response-playbooks", 
                "description": "Additional incident response playbooks",
                "sample_size": 200,
                "category": "ir_playbooks_extended",
                "priority": "high"
            },
            {
                "name": "venkycs/security-dpo",
                "description": "DPO-style security instructions referencing SOPs/playbooks",
                "sample_size": 400,
                "category": "security_dpo",
                "priority": "high"
            },
            {
                "name": "Trendyol/Trendyol-Cybersecurity-Instruction-Tuning-Dataset",
                "description": "Modern security ops instructions with playbook-like tasks",
                "sample_size": 500,
                "category": "modern_secops",
                "priority": "ultra_high"
            }
        ]
        
        self.total_samples = 0
        self.successful_datasets = []
        self.failed_datasets = []
    
    def download_dataset(self, config: Dict[str, Any]) -> bool:
        """Download and process a SOAR dataset"""
        
        if not HF_AVAILABLE:
            logger.error("❌ HuggingFace datasets library required")
            return False
        
        dataset_name = config["name"]
        logger.info(f"🚀 [{config['priority'].upper()}] Downloading {dataset_name}...")
        
        try:
            # Load dataset
            dataset = load_dataset(dataset_name, split="train", streaming=True)
            
            # Create category directory
            category_dir = self.output_dir / config["category"]
            category_dir.mkdir(exist_ok=True)
            
            # Collect and process samples
            samples = []
            count = 0
            
            for example in dataset:
                if count >= config["sample_size"]:
                    break
                
                # Process different dataset structures
                sample = self._process_sample(example, config)
                
                if sample and self._is_quality_sample(sample):
                    sample["dataset"] = dataset_name
                    sample["category"] = config["category"]
                    sample["priority"] = config["priority"]
                    sample["downloaded_at"] = datetime.utcnow().isoformat()
                    samples.append(sample)
                    count += 1
            
            if not samples:
                logger.warning(f"⚠️  No usable samples found in {dataset_name}")
                self.failed_datasets.append(dataset_name)
                return False
            
            # Save as JSONL for RAG integration
            output_file = category_dir / f"{dataset_name.replace('/', '_')}_samples.jsonl"
            with open(output_file, 'w') as f:
                for sample in samples:
                    f.write(json.dumps(sample) + '\n')
            
            # Save metadata
            metadata = {
                "dataset_name": dataset_name,
                "description": config["description"],
                "category": config["category"],
                "priority": config["priority"],
                "sample_count": len(samples),
                "file_path": str(output_file),
                "downloaded_at": datetime.utcnow().isoformat()
            }
            
            metadata_file = category_dir / f"{dataset_name.replace('/', '_')}_metadata.json"
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"✅ Downloaded {len(samples)} samples from {dataset_name}")
            logger.info(f"   📁 Data: {output_file}")
            
            self.total_samples += len(samples)
            self.successful_datasets.append(dataset_name)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to download {dataset_name}: {e}")
            self.failed_datasets.append(dataset_name)
            return False
    
    def _process_sample(self, example: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Process a sample based on dataset type"""
        
        category = config["category"]
        
        if "ir_playbooks" in category:
            return self._process_ir_playbook(example)
        elif category == "security_dpo":
            return self._process_security_dpo(example)
        elif category == "modern_secops":
            return self._process_modern_secops(example)
        else:
            return self._process_generic(example)
    
    def _process_ir_playbook(self, example: Dict[str, Any]) -> Dict[str, Any]:
        """Process incident response playbook samples"""
        
        # Common IR playbook fields
        playbook_fields = ["playbook", "procedure", "response", "steps", "action", "mitigation"]
        incident_fields = ["incident", "scenario", "threat", "attack", "compromise"]
        text_fields = ["text", "content", "description", "instruction"]
        
        playbook_content = ""
        incident_type = ""
        
        # Extract playbook content
        for field in playbook_fields:
            if field in example and example[field]:
                playbook_content = str(example[field])
                break
        
        # Extract incident type
        for field in incident_fields:
            if field in example and example[field]:
                incident_type = str(example[field])
                break
        
        # Fallback to text fields
        if not playbook_content:
            for field in text_fields:
                if field in example and example[field]:
                    playbook_content = str(example[field])
                    break
        
        if not playbook_content:
            return None
        
        return {
            "playbook_content": playbook_content,
            "incident_type": incident_type or "General Incident",
            "response_type": "incident_response",
            "framework": "NIST",
            "content_type": "ir_playbook"
        }
    
    def _process_security_dpo(self, example: Dict[str, Any]) -> Dict[str, Any]:
        """Process DPO-style security instructions"""
        
        # DPO typically has instruction/input/output or chosen/rejected pairs
        instruction = example.get("instruction", example.get("prompt", ""))
        input_text = example.get("input", example.get("context", ""))
        output = example.get("output", example.get("chosen", example.get("response", "")))
        
        if not instruction and not output:
            return None
        
        return {
            "instruction": str(instruction),
            "input": str(input_text),
            "response": str(output),
            "response_type": "security_guidance",
            "framework": "DPO",
            "content_type": "security_instruction"
        }
    
    def _process_modern_secops(self, example: Dict[str, Any]) -> Dict[str, Any]:
        """Process modern security operations instructions"""
        
        # Look for instruction/response patterns
        if "instruction" in example and "output" in example:
            return {
                "instruction": str(example["instruction"]),
                "response": str(example["output"]),
                "input": str(example.get("input", "")),
                "response_type": "security_operations",
                "framework": "Modern SecOps",
                "content_type": "secops_instruction"
            }
        elif "text" in example:
            # Extract from text field
            text = str(example["text"])
            return {
                "instruction": text[:200] + "..." if len(text) > 200 else text,
                "response": text,
                "response_type": "security_operations", 
                "framework": "Modern SecOps",
                "content_type": "secops_guidance"
            }
        
        return None
    
    def _process_generic(self, example: Dict[str, Any]) -> Dict[str, Any]:
        """Generic processing for unknown structures"""
        
        # Find the largest text field
        text_content = ""
        for key, value in example.items():
            if isinstance(value, str) and len(value) > len(text_content):
                text_content = value
        
        if len(text_content) < 50:
            return None
        
        return {
            "content": text_content,
            "response_type": "security_guidance",
            "framework": "Generic",
            "content_type": "security_content"
        }
    
    def _is_quality_sample(self, sample: Dict[str, Any]) -> bool:
        """Check if sample meets quality standards for SOAR copilot"""
        
        # Minimum content length
        content_fields = ["playbook_content", "response", "content", "instruction"]
        has_substantial_content = False
        
        for field in content_fields:
            if field in sample and len(str(sample[field])) >= 50:
                has_substantial_content = True
                break
        
        # Security relevance keywords
        security_keywords = [
            "incident", "response", "playbook", "security", "threat", "attack",
            "malware", "phishing", "breach", "compromise", "mitigation", "containment",
            "investigation", "forensics", "remediation", "recovery", "siem", "soc",
            "alert", "detection", "analysis", "triage"
        ]
        
        sample_text = str(sample).lower()
        has_security_relevance = any(keyword in sample_text for keyword in security_keywords)
        
        return has_substantial_content and has_security_relevance
    
    def create_soar_knowledge_chunks(self):
        """Create RAG-ready chunks optimized for SOAR operations"""
        
        logger.info("🧩 Creating SOAR knowledge chunks...")
        
        chunks_dir = Path("ai-training/rag/chunks/soar-playbooks")
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
                            
                            # Create SOAR-optimized chunk
                            chunk_content = self._create_soar_chunk(sample)
                            
                            if chunk_content:
                                # Save chunk
                                chunk_file = chunks_dir / f"{dataset_name}_{i}.md"
                                with open(chunk_file, 'w') as cf:
                                    cf.write(chunk_content)
                                
                                chunk_count += 1
        
        logger.info(f"✅ Generated {chunk_count} SOAR knowledge chunks")
        return chunks_dir, chunk_count
    
    def _create_soar_chunk(self, sample: Dict[str, Any]) -> str:
        """Create SOAR-optimized knowledge chunk"""
        
        content_type = sample.get("content_type", "security_guidance")
        
        if content_type == "ir_playbook":
            return f"""# Incident Response Playbook

**Incident Type**: {sample.get('incident_type', 'General')}
**Framework**: {sample.get('framework', 'NIST')}

**Playbook Content**:
{sample.get('playbook_content', '')}

**Response Type**: Incident Response
**Category**: SOAR Playbook
**Source**: {sample.get('dataset', 'Unknown')}
"""
        
        elif content_type in ["security_instruction", "secops_instruction"]:
            return f"""# Security Operations Instruction

**Instruction**: {sample.get('instruction', '')}

**Input/Context**: {sample.get('input', 'N/A')}

**Response**: {sample.get('response', '')}

**Framework**: {sample.get('framework', 'Modern SecOps')}
**Response Type**: {sample.get('response_type', 'Security Guidance')}
**Category**: SOAR Instruction
**Source**: {sample.get('dataset', 'Unknown')}
"""
        
        else:
            return f"""# Security Operations Knowledge

**Content**: {sample.get('content', sample.get('response', ''))}

**Framework**: {sample.get('framework', 'Security Operations')}
**Response Type**: {sample.get('response_type', 'Security Guidance')}
**Category**: SOAR Knowledge
**Source**: {sample.get('dataset', 'Unknown')}
"""
    
    def run_soar_pipeline(self):
        """Run the complete SOAR datasets download pipeline"""
        
        print("🚀 BUILDING THE GREATEST SOAR COPILOT EVER!")
        print("=" * 60)
        logger.info("Starting elite SOAR datasets download pipeline...")
        
        if not HF_AVAILABLE:
            logger.error("❌ HuggingFace datasets library required")
            return False
        
        # Download each dataset by priority
        high_priority = [d for d in self.datasets if d["priority"] in ["ultra_high", "high"]]
        
        for config in sorted(high_priority, key=lambda x: x["priority"], reverse=True):
            success = self.download_dataset(config)
            if success:
                logger.info(f"🎯 [{config['priority'].upper()}] Successfully integrated {config['name']}")
        
        # Create SOAR knowledge chunks
        chunks_dir, chunk_count = self.create_soar_knowledge_chunks()
        
        # Final report
        print(f"\n🎉 SOAR DATASETS INTEGRATION COMPLETE!")
        print("=" * 50)
        print(f"🎯 Successfully downloaded: {len(self.successful_datasets)}/{len(self.datasets)} datasets")
        print(f"📈 Total samples: {self.total_samples}")
        print(f"🧩 SOAR chunks generated: {chunk_count}")
        print(f"📁 Data directory: {self.output_dir}")
        print(f"🧩 SOAR chunks: {chunks_dir}")
        
        print(f"\n✅ Successful datasets:")
        for dataset in self.successful_datasets:
            print(f"  ✅ {dataset}")
        
        if self.failed_datasets:
            print(f"\n⚠️  Failed datasets:")
            for dataset in self.failed_datasets:
                print(f"  ❌ {dataset}")
        
        print(f"\n🚀 WHIS is now equipped with elite SOAR capabilities!")
        print("Ready for incident response, playbook execution, and security operations!")
        
        return True

def main():
    """Transform WHIS into the greatest SOAR copilot ever"""
    
    print("🔥 WHIS SOAR TRANSFORMATION INITIATED")
    print("Building the ultimate security operations copilot...")
    
    downloader = SOARDatasetsDownloader()
    success = downloader.run_soar_pipeline()
    
    if success:
        print("\n🚀 Next steps:")
        print("1. Update knowledge base builder to include SOAR datasets")
        print("2. Rebuild FAISS index with new SOAR knowledge")
        print("3. Test WHIS with incident response scenarios")
        print("4. Deploy the world's greatest SOAR copilot!")
    else:
        print("\n❌ SOAR transformation failed")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())