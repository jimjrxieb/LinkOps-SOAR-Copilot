#!/usr/bin/env python3
"""
JSONL Dataset Processor for Whis Training
Processes the whis_action_schema_100.jsonl file and converts to training format
"""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict
import hashlib

class WhisJSONLProcessor:
    def __init__(self):
        self.processed_data = []
        self.stats = {
            "total_examples": 0,
            "converted_examples": 0,
            "domains": {},
            "mitre_techniques": set(),
            "quality_scores": []
        }
        
    def process_jsonl_file(self, jsonl_path: Path) -> List[Dict]:
        """Process JSONL file and convert to Whis training format"""
        print(f"📥 Processing JSONL file: {jsonl_path}")
        
        with open(jsonl_path, 'r') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    example = json.loads(line.strip())
                    converted = self.convert_example(example, line_num)
                    if converted:
                        self.processed_data.append(converted)
                        self.stats["converted_examples"] += 1
                    self.stats["total_examples"] += 1
                except json.JSONDecodeError as e:
                    print(f"⚠️ Line {line_num}: JSON decode error - {e}")
                except Exception as e:
                    print(f"⚠️ Line {line_num}: Processing error - {e}")
                    
        print(f"✅ Processed {self.stats['converted_examples']}/{self.stats['total_examples']} examples")
        return self.processed_data
        
    def convert_example(self, example: Dict, line_num: int) -> Dict:
        """Convert JSONL example to Whis training format"""
        try:
            # Extract instruction and response
            instruction = example.get("instruction", "")
            input_text = example.get("input", "")
            output_text = example.get("output", "")
            metadata = example.get("metadata", {})
            
            # Parse the JSON output to extract MITRE techniques
            try:
                output_json = json.loads(output_text)
                mitre_techniques = output_json.get("mitre", [])
                for technique in mitre_techniques:
                    self.stats["mitre_techniques"].add(technique)
            except:
                mitre_techniques = []
            
            # Track domain stats
            domain = metadata.get("domain", "unknown")
            self.stats["domains"][domain] = self.stats["domains"].get(domain, 0) + 1
            
            # Create Whis training format
            if input_text:
                prompt_text = f"{instruction}\n\nInput: {input_text}"
            else:
                prompt_text = instruction
                
            whis_format = {
                "text": f"""Below is an instruction that describes a cybersecurity task, paired with an input that provides further context. Write a response that appropriately completes the request.

### Instruction:
{instruction}

### Input:
{input_text if input_text else "N/A"}

### Response:
{output_text}""",
                "metadata": {
                    "original_line": line_num,
                    "domain": domain,
                    "tags": metadata.get("tags", []) + ["SecOps", "SOAR", "ActionSchema"],
                    "difficulty": metadata.get("difficulty", "intermediate"),
                    "mitre_techniques": mitre_techniques,
                    "quality_score": self.calculate_quality_score(instruction, output_text, metadata),
                    "source": "whis_action_schema_100.jsonl",
                    "processed_at": datetime.now().isoformat()
                }
            }
            
            # Track quality score
            self.stats["quality_scores"].append(whis_format["metadata"]["quality_score"])
            
            return whis_format
            
        except Exception as e:
            print(f"⚠️ Line {line_num}: Conversion error - {e}")
            return None
            
    def calculate_quality_score(self, instruction: str, output: str, metadata: Dict) -> float:
        """Calculate quality score for the example"""
        score = 0.7  # Base score
        
        # Instruction quality
        if len(instruction) > 50:
            score += 0.1
        if "JSON object" in instruction:
            score += 0.1
        if "SecOps" in instruction:
            score += 0.05
            
        # Output quality
        try:
            output_json = json.loads(output)
            required_keys = ["triage_steps", "containment", "remediation", "mitre", "spl_query"]
            found_keys = sum(1 for key in required_keys if key in output_json and output_json[key])
            score += (found_keys / len(required_keys)) * 0.15
            
            # Check for detailed responses
            if isinstance(output_json.get("triage_steps"), list) and len(output_json["triage_steps"]) >= 3:
                score += 0.05
            if output_json.get("spl_query") and len(output_json["spl_query"]) > 20:
                score += 0.05
                
        except:
            score -= 0.1  # Penalize invalid JSON
            
        return min(score, 1.0)
        
    def save_processed_dataset(self, output_path: Path):
        """Save processed dataset to file"""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(self.processed_data, f, indent=2)
            
        print(f"💾 Processed dataset saved to: {output_path}")
        
    def generate_stats_report(self) -> Dict:
        """Generate processing statistics"""
        avg_quality = sum(self.stats["quality_scores"]) / len(self.stats["quality_scores"]) if self.stats["quality_scores"] else 0
        
        return {
            "processing_summary": {
                "total_examples": self.stats["total_examples"],
                "converted_examples": self.stats["converted_examples"],
                "success_rate": self.stats["converted_examples"] / self.stats["total_examples"] if self.stats["total_examples"] > 0 else 0,
                "average_quality_score": avg_quality
            },
            "domain_breakdown": dict(self.stats["domains"]),
            "mitre_techniques_found": len(self.stats["mitre_techniques"]),
            "mitre_techniques": sorted(list(self.stats["mitre_techniques"])),
            "quality_distribution": {
                "high_quality": sum(1 for score in self.stats["quality_scores"] if score >= 0.9),
                "medium_quality": sum(1 for score in self.stats["quality_scores"] if 0.7 <= score < 0.9),
                "low_quality": sum(1 for score in self.stats["quality_scores"] if score < 0.7)
            }
        }
        
    def process_data_drop(self, input_file: str = "data_drops/llm_training/whis_action_schema_100.jsonl"):
        """Process the dropped JSONL file"""
        print("🚀 WHIS JSONL DATASET PROCESSOR")
        print("=" * 50)
        
        jsonl_path = Path(input_file)
        if not jsonl_path.exists():
            print(f"❌ File not found: {jsonl_path}")
            return None
            
        # Process the JSONL file
        self.process_jsonl_file(jsonl_path)
        
        # Generate stats
        stats = self.generate_stats_report()
        
        # Save processed dataset
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = Path(f"training/processed_data/whis_action_schema_processed_{timestamp}.json")
        self.save_processed_dataset(output_path)
        
        # Save stats report
        stats_path = Path(f"training/processed_data/processing_stats_{timestamp}.json")
        with open(stats_path, 'w') as f:
            json.dump(stats, f, indent=2)
            
        print("\n📊 PROCESSING STATISTICS")
        print("-" * 30)
        print(f"📈 Total examples: {stats['processing_summary']['total_examples']}")
        print(f"✅ Converted: {stats['processing_summary']['converted_examples']}")
        print(f"🎯 Success rate: {stats['processing_summary']['success_rate']:.2%}")
        print(f"⭐ Average quality: {stats['processing_summary']['average_quality_score']:.3f}")
        print(f"🏷️ MITRE techniques: {stats['mitre_techniques_found']}")
        print(f"📊 Domains: {len(stats['domain_breakdown'])}")
        
        print("\n🏆 QUALITY DISTRIBUTION")
        print("-" * 25)
        for quality_level, count in stats["quality_distribution"].items():
            print(f"  {quality_level.replace('_', ' ').title()}: {count}")
            
        print(f"\n💾 Files saved:")
        print(f"  Dataset: {output_path}")
        print(f"  Stats: {stats_path}")
        
        return {
            "dataset_path": str(output_path),
            "stats": stats,
            "examples_count": len(self.processed_data)
        }

def main():
    processor = WhisJSONLProcessor()
    return processor.process_data_drop()

if __name__ == "__main__":
    main()