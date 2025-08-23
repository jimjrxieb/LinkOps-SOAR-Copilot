#!/usr/bin/env python3
"""
Integrate sanitized RAG data with existing training datasets
Creates comprehensive training dataset for enhanced Whis model
"""

import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

class TrainingDataIntegrator:
    def __init__(self):
        self.llm_data_dir = Path("../../llm/data")
        self.sanitized_dir = Path("sanitized_rag_data")
        self.output_dir = Path("../../llm/data")
        
    def load_existing_training_data(self) -> List[Dict]:
        """Load existing JSONL training data"""
        existing_data = []
        
        # Load existing training files
        training_files = [
            "devsecops_senior_scenarios.jsonl",
            "security_interview_questions.jsonl",
            "whis_action_schema_100.jsonl"  # If it exists
        ]
        
        for file_name in training_files:
            file_path = self.llm_data_dir / file_name
            if file_path.exists():
                print(f"📚 Loading {file_name}")
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line_num, line in enumerate(f, 1):
                        try:
                            if line.strip():
                                data = json.loads(line)
                                existing_data.append({
                                    "source_file": file_name,
                                    "line_number": line_num,
                                    **data
                                })
                        except json.JSONDecodeError as e:
                            print(f"  ⚠️ Skipped malformed line {line_num}: {e}")
                
                print(f"  ✅ Loaded {sum(1 for d in existing_data if d['source_file'] == file_name)} entries")
        
        return existing_data
    
    def load_sanitized_rag_chunks(self) -> List[Dict]:
        """Load sanitized RAG chunks"""
        # Find the latest sanitized file
        sanitized_files = list(self.sanitized_dir.glob("sanitized_chunks_*.jsonl"))
        if not sanitized_files:
            raise FileNotFoundError("No sanitized RAG chunks found")
        
        latest_file = max(sanitized_files, key=lambda x: x.stat().st_mtime)
        print(f"📖 Loading sanitized RAG chunks: {latest_file}")
        
        chunks = []
        with open(latest_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    if line.strip():
                        chunk = json.loads(line)
                        chunks.append(chunk)
                except json.JSONDecodeError as e:
                    print(f"  ⚠️ Skipped malformed chunk {line_num}: {e}")
        
        print(f"  ✅ Loaded {len(chunks)} sanitized RAG chunks")
        return chunks
    
    def convert_rag_to_training_format(self, chunks: List[Dict]) -> List[Dict]:
        """Convert RAG chunks to training format"""
        print("🔄 Converting RAG chunks to training format...")
        
        training_examples = []
        
        for chunk in chunks:
            # Extract scenario information from the chunk
            content = chunk.get('content', '')
            title = chunk.get('title', 'Security Scenario')
            
            # Create instruction based on the content
            if 'Problem' in content and 'Economics' in content:
                # This is a cost scenario
                instruction = f"How would you handle this business scenario: {title}"
                
                # Extract key information
                problem_match = content.find('**Problem**:')
                economics_match = content.find('Economics')
                analysis_match = content.find('Analysis')
                
                # Create simplified response focusing on action schema
                response = {
                    "triage_steps": [
                        "Assess business impact and financial risks",
                        "Evaluate current security posture and gaps", 
                        "Calculate ROI and cost-benefit analysis"
                    ],
                    "containment": [
                        "Implement immediate risk mitigation measures",
                        "Deploy temporary security controls",
                        "Coordinate with business stakeholders"
                    ],
                    "remediation": [
                        "Execute comprehensive security improvement plan",
                        "Implement automated controls and monitoring", 
                        "Establish ongoing governance and measurement"
                    ],
                    "mitre": ["T1190 - Exploit Public-Facing Application"],
                    "guidance": f"Business-focused security implementation for {title.lower()}. Balance security requirements with operational needs and cost constraints. Use risk-based approach with measurable ROI.",
                    "citations": ["Industry Best Practices", "Cost-Benefit Analysis Framework"],
                    "confidence": 0.87
                }
                
                training_examples.append({
                    "instruction": instruction,
                    "input": "",
                    "output": json.dumps(response, separators=(',', ':')),
                    "source_chunk_id": chunk.get('chunk_id'),
                    "metadata": {
                        "category": "senior_devsecops",
                        "source": "sanitized_rag",
                        "tags": chunk.get('tags', [])
                    }
                })
        
        print(f"  ✅ Created {len(training_examples)} training examples from RAG chunks")
        return training_examples
    
    def deduplicate_training_data(self, all_data: List[Dict]) -> List[Dict]:
        """Remove duplicate training examples"""
        print("🔍 Deduplicating training data...")
        
        seen_hashes = set()
        unique_data = []
        
        for item in all_data:
            # Create hash from instruction + output for deduplication
            content = item.get('instruction', '') + item.get('output', '')
            content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
            
            if content_hash not in seen_hashes:
                seen_hashes.add(content_hash)
                unique_data.append(item)
        
        duplicates_removed = len(all_data) - len(unique_data)
        print(f"  📊 Removed {duplicates_removed} duplicates, kept {len(unique_data)} unique examples")
        
        return unique_data
    
    def create_enhanced_training_dataset(self):
        """Create comprehensive enhanced training dataset"""
        print("🚀 WHIS ENHANCED TRAINING DATA INTEGRATION")
        print("=" * 60)
        
        # Load existing training data
        existing_data = self.load_existing_training_data()
        print(f"📊 Total existing training examples: {len(existing_data)}")
        
        # Load and convert sanitized RAG chunks
        rag_chunks = self.load_sanitized_rag_chunks()
        rag_training = self.convert_rag_to_training_format(rag_chunks)
        
        # Combine all training data
        all_training_data = []
        
        # Add existing JSONL data (convert to unified format)
        for item in existing_data:
            unified_item = {
                "instruction": item.get('instruction', ''),
                "input": item.get('input', ''),
                "output": item.get('output', ''),
                "metadata": {
                    "source": item.get('source_file', 'existing'),
                    "category": "existing_training"
                }
            }
            all_training_data.append(unified_item)
        
        # Add RAG-derived training data
        all_training_data.extend(rag_training)
        
        print(f"📈 Combined dataset size: {len(all_training_data)} examples")
        
        # Deduplicate
        unique_data = self.deduplicate_training_data(all_training_data)
        
        # Create enhanced dataset
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save as JSONL for training
        output_file = self.output_dir / f"whis_enhanced_training_{timestamp}.jsonl"
        with open(output_file, 'w', encoding='utf-8') as f:
            for item in unique_data:
                f.write(json.dumps(item, ensure_ascii=False, separators=(',', ':')) + '\n')
        
        # Create metadata file
        metadata = {
            "created_at": datetime.now().isoformat(),
            "total_examples": len(unique_data),
            "sources": {
                "existing_training": len([d for d in unique_data if d['metadata']['source'] != 'sanitized_rag']),
                "sanitized_rag": len([d for d in unique_data if d['metadata']['source'] == 'sanitized_rag'])
            },
            "categories": list(set(d['metadata']['category'] for d in unique_data)),
            "description": "Enhanced WHIS training dataset with senior DevSecOps scenarios"
        }
        
        metadata_file = self.output_dir / f"whis_enhanced_metadata_{timestamp}.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        # Create symlink to latest
        latest_file = self.output_dir / "whis_enhanced_training_latest.jsonl"
        latest_metadata = self.output_dir / "whis_enhanced_metadata_latest.json"
        
        if latest_file.exists() or latest_file.is_symlink():
            latest_file.unlink()
        if latest_metadata.exists() or latest_metadata.is_symlink():
            latest_metadata.unlink()
        
        latest_file.symlink_to(output_file.name)
        latest_metadata.symlink_to(metadata_file.name)
        
        print(f"\n✅ ENHANCED TRAINING DATASET CREATED")
        print(f"📁 Training file: {output_file}")
        print(f"📄 Metadata file: {metadata_file}")
        print(f"🔗 Latest link: {latest_file}")
        
        print(f"\n📊 DATASET SUMMARY:")
        print(f"  📚 Total examples: {len(unique_data)}")
        print(f"  📖 Existing training: {metadata['sources']['existing_training']}")
        print(f"  🧠 RAG-derived: {metadata['sources']['sanitized_rag']}")
        print(f"  🏷️  Categories: {len(metadata['categories'])}")
        
        return output_file, metadata_file

def main():
    integrator = TrainingDataIntegrator()
    output_file, metadata_file = integrator.create_enhanced_training_dataset()
    
    print(f"\n🎯 Ready for Whis model retraining!")
    print(f"   Use training file: {output_file}")

if __name__ == "__main__":
    main()