#!/usr/bin/env python3
"""
Whis Cybersecurity LLM Data Preprocessing Pipeline
Comprehensive data preparation, validation, and formatting for robust training
"""

import json
import re
import os
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import hashlib
import logging
from collections import Counter, defaultdict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PreprocessingStats:
    """Statistics from preprocessing pipeline"""
    original_count: int
    processed_count: int
    filtered_count: int
    duplicate_count: int
    invalid_count: int
    avg_instruction_length: float
    avg_output_length: float
    category_distribution: Dict[str, int]
    quality_scores: List[float]

class CybersecDataPreprocessor:
    """Comprehensive preprocessing pipeline for cybersecurity training data"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or self._default_config()
        self.stats = None
        self.processed_examples = []
        
    def _default_config(self) -> Dict:
        """Default preprocessing configuration"""
        return {
            "min_instruction_length": 20,
            "max_instruction_length": 1000,
            "min_output_length": 50,
            "max_output_length": 4000,
            "min_quality_score": 0.6,
            "remove_duplicates": True,
            "normalize_whitespace": True,
            "validate_cybersec_content": True,
            "required_tags": ["Teacher", "Assistant"],  # At least one required
            "cybersec_keywords": [
                "security", "attack", "threat", "vulnerability", "incident",
                "detection", "response", "MITRE", "ATT&CK", "SOAR", "SIEM",
                "authentication", "authorization", "malware", "phishing"
            ],
            "prompt_template": "alpaca",  # "alpaca" or "chat" format
            "sequence_length": 2048,
            "validation_split": 0.1,
            "test_split": 0.1
        }
    
    def load_datasets(self, dataset_paths: List[str]) -> List[Dict]:
        """Load and combine multiple datasets"""
        logger.info(f"📂 Loading {len(dataset_paths)} datasets...")
        
        all_examples = []
        
        for path in dataset_paths:
            logger.info(f"  Loading: {path}")
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Handle different data formats
                if "examples" in data:
                    examples = data["examples"]
                elif isinstance(data, list):
                    examples = data
                elif isinstance(data, dict) and len(data) > 0:
                    # Assume it's categorized data
                    examples = []
                    for category, items in data.items():
                        if isinstance(items, list):
                            examples.extend(items)
                
                all_examples.extend(examples)
                logger.info(f"    ✅ Loaded {len(examples)} examples")
                
            except Exception as e:
                logger.error(f"    ❌ Failed to load {path}: {e}")
                continue
        
        logger.info(f"📊 Total examples loaded: {len(all_examples)}")
        return all_examples
    
    def validate_example(self, example: Dict) -> Tuple[bool, List[str]]:
        """Validate a single training example"""
        issues = []
        
        # Check required fields
        required_fields = ["instruction", "output"]
        for field in required_fields:
            if field not in example or not example[field]:
                issues.append(f"Missing required field: {field}")
        
        if issues:
            return False, issues
        
        # Length validation
        instruction_len = len(example["instruction"])
        output_len = len(example["output"])
        
        if instruction_len < self.config["min_instruction_length"]:
            issues.append(f"Instruction too short: {instruction_len} chars")
        
        if instruction_len > self.config["max_instruction_length"]:
            issues.append(f"Instruction too long: {instruction_len} chars")
        
        if output_len < self.config["min_output_length"]:
            issues.append(f"Output too short: {output_len} chars")
        
        if output_len > self.config["max_output_length"]:
            issues.append(f"Output too long: {output_len} chars")
        
        # Cybersecurity content validation
        if self.config["validate_cybersec_content"]:
            combined_text = (example["instruction"] + " " + example["output"]).lower()
            keyword_matches = sum(1 for keyword in self.config["cybersec_keywords"] 
                                if keyword.lower() in combined_text)
            
            if keyword_matches < 2:
                issues.append("Insufficient cybersecurity content")
        
        # Tag validation
        if "tags" in example and self.config["required_tags"]:
            example_tags = set(example["tags"])
            has_required = any(req_tag in tag for tag in example_tags 
                             for req_tag in self.config["required_tags"])
            if not has_required:
                issues.append("Missing required tags")
        
        return len(issues) == 0, issues
    
    def calculate_quality_score(self, example: Dict) -> float:
        """Calculate quality score for an example"""
        score = 0.0
        max_score = 0.0
        
        # Content diversity score
        instruction_words = set(example["instruction"].lower().split())
        output_words = set(example["output"].lower().split())
        vocab_diversity = len(instruction_words | output_words) / max(len(instruction_words) + len(output_words), 1)
        score += vocab_diversity * 0.2
        max_score += 0.2
        
        # Cybersecurity relevance score
        combined_text = (example["instruction"] + " " + example["output"]).lower()
        keyword_matches = sum(1 for keyword in self.config["cybersec_keywords"] 
                            if keyword.lower() in combined_text)
        relevance_score = min(1.0, keyword_matches / 5.0)  # Normalize to max 5 keywords
        score += relevance_score * 0.3
        max_score += 0.3
        
        # Structure and completeness score
        structure_score = 0.0
        if "**" in example["output"]:  # Has formatting
            structure_score += 0.3
        if "```" in example["output"]:  # Has code blocks
            structure_score += 0.4
        if any(phrase in example["output"].lower() for phrase in 
               ["steps:", "actions:", "detection:", "response:", "mitigation:"]):
            structure_score += 0.3
        
        score += min(1.0, structure_score) * 0.3
        max_score += 0.3
        
        # Length appropriateness score
        instruction_len = len(example["instruction"])
        output_len = len(example["output"])
        
        # Ideal lengths: instruction 50-200 chars, output 200-1500 chars
        instr_score = 1.0 - abs(125 - instruction_len) / 125 if instruction_len <= 250 else 0.5
        output_score = 1.0 - abs(850 - output_len) / 850 if output_len <= 1700 else 0.5
        length_score = (max(0, instr_score) + max(0, output_score)) / 2
        
        score += length_score * 0.2
        max_score += 0.2
        
        return score / max_score if max_score > 0 else 0.0
    
    def remove_duplicates(self, examples: List[Dict]) -> List[Dict]:
        """Remove duplicate examples based on content similarity"""
        if not self.config["remove_duplicates"]:
            return examples
        
        logger.info("🔍 Removing duplicate examples...")
        
        # Create content hashes
        seen_hashes = set()
        unique_examples = []
        duplicates_removed = 0
        
        for example in examples:
            # Create hash of instruction + output (normalized)
            content = example["instruction"].strip() + " " + example["output"].strip()
            content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
            
            if content_hash not in seen_hashes:
                seen_hashes.add(content_hash)
                unique_examples.append(example)
            else:
                duplicates_removed += 1
        
        logger.info(f"  ✅ Removed {duplicates_removed} duplicates")
        return unique_examples
    
    def normalize_text(self, text: str) -> str:
        """Normalize text content"""
        if not self.config["normalize_whitespace"]:
            return text
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Fix common formatting issues
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)  # Multiple newlines
        text = re.sub(r'[ \t]+', ' ', text)  # Multiple spaces/tabs
        
        return text
    
    def format_for_training(self, example: Dict) -> str:
        """Format example according to specified template"""
        template = self.config["prompt_template"]
        
        if template == "alpaca":
            if "input" in example and example["input"].strip():
                formatted = f"""Below is an instruction that describes a cybersecurity task, paired with an input that provides further context. Write a response that appropriately completes the request.

### Instruction:
{example['instruction']}

### Input:
{example['input']}

### Response:
{example['output']}"""
            else:
                formatted = f"""Below is an instruction that describes a cybersecurity task. Write a response that appropriately completes the request.

### Instruction:
{example['instruction']}

### Response:
{example['output']}"""
        
        elif template == "chat":
            formatted = f"""<|im_start|>system
You are Whis, a cybersecurity AI assistant specialized in SOAR (Security Orchestration, Automation & Response) operations.<|im_end|>
<|im_start|>user
{example['instruction']}
{example.get('input', '')}<|im_end|>
<|im_start|>assistant
{example['output']}<|im_end|>"""
        
        else:
            # Simple format
            formatted = f"Instruction: {example['instruction']}\nResponse: {example['output']}"
        
        return formatted
    
    def split_dataset(self, examples: List[Dict]) -> Tuple[List[Dict], List[Dict], List[Dict]]:
        """Split dataset into train/validation/test sets"""
        logger.info("📊 Splitting dataset...")
        
        # Shuffle examples
        np.random.seed(42)  # For reproducibility
        shuffled = examples.copy()
        np.random.shuffle(shuffled)
        
        total = len(shuffled)
        test_size = int(total * self.config["test_split"])
        val_size = int(total * self.config["validation_split"])
        train_size = total - test_size - val_size
        
        train_set = shuffled[:train_size]
        val_set = shuffled[train_size:train_size + val_size]
        test_set = shuffled[train_size + val_size:]
        
        logger.info(f"  📈 Train: {len(train_set)} examples")
        logger.info(f"  📊 Validation: {len(val_set)} examples")
        logger.info(f"  🧪 Test: {len(test_set)} examples")
        
        return train_set, val_set, test_set
    
    def analyze_dataset(self, examples: List[Dict]) -> Dict:
        """Analyze dataset characteristics"""
        logger.info("🔍 Analyzing dataset characteristics...")
        
        analysis = {
            "total_examples": len(examples),
            "avg_instruction_length": np.mean([len(ex["instruction"]) for ex in examples]),
            "avg_output_length": np.mean([len(ex["output"]) for ex in examples]),
            "instruction_length_std": np.std([len(ex["instruction"]) for ex in examples]),
            "output_length_std": np.std([len(ex["output"]) for ex in examples]),
        }
        
        # Tag distribution
        all_tags = []
        for example in examples:
            if "tags" in example:
                all_tags.extend(example["tags"])
        
        tag_counts = Counter(all_tags)
        analysis["tag_distribution"] = dict(tag_counts.most_common(10))
        
        # Quality scores
        quality_scores = [self.calculate_quality_score(ex) for ex in examples]
        analysis["avg_quality_score"] = np.mean(quality_scores)
        analysis["quality_score_std"] = np.std(quality_scores)
        analysis["low_quality_examples"] = sum(1 for score in quality_scores 
                                             if score < self.config["min_quality_score"])
        
        # Content analysis
        has_code = sum(1 for ex in examples if "```" in ex["output"])
        has_formatting = sum(1 for ex in examples if "**" in ex["output"])
        has_lists = sum(1 for ex in examples if any(marker in ex["output"] 
                       for marker in ["- ", "1. ", "* "]))
        
        analysis["content_features"] = {
            "examples_with_code": has_code,
            "examples_with_formatting": has_formatting,
            "examples_with_lists": has_lists
        }
        
        return analysis
    
    def process_dataset(self, dataset_paths: List[str], output_dir: str = "processed_data") -> Dict:
        """Main preprocessing pipeline"""
        logger.info("🛡️ Starting Whis cybersecurity dataset preprocessing...")
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Load datasets
        raw_examples = self.load_datasets(dataset_paths)
        original_count = len(raw_examples)
        
        # Validation and filtering
        logger.info("🔍 Validating examples...")
        valid_examples = []
        invalid_count = 0
        
        for i, example in enumerate(raw_examples):
            is_valid, issues = self.validate_example(example)
            
            if is_valid:
                # Calculate quality score
                quality_score = self.calculate_quality_score(example)
                example["_quality_score"] = quality_score
                
                if quality_score >= self.config["min_quality_score"]:
                    # Normalize text content
                    example["instruction"] = self.normalize_text(example["instruction"])
                    example["output"] = self.normalize_text(example["output"])
                    if "input" in example:
                        example["input"] = self.normalize_text(example["input"])
                    
                    valid_examples.append(example)
                else:
                    logger.debug(f"Low quality example {i}: score={quality_score:.3f}")
            else:
                invalid_count += 1
                logger.debug(f"Invalid example {i}: {issues}")
        
        logger.info(f"  ✅ Valid examples: {len(valid_examples)}")
        logger.info(f"  ❌ Invalid examples: {invalid_count}")
        
        # Remove duplicates
        unique_examples = self.remove_duplicates(valid_examples)
        duplicate_count = len(valid_examples) - len(unique_examples)
        
        # Split dataset
        train_set, val_set, test_set = self.split_dataset(unique_examples)
        
        # Format for training
        logger.info("📝 Formatting examples for training...")
        
        formatted_train = []
        for example in train_set:
            formatted = self.format_for_training(example)
            formatted_train.append({
                "text": formatted,
                "metadata": {
                    "quality_score": example["_quality_score"],
                    "tags": example.get("tags", []),
                    "original_instruction": example["instruction"][:100] + "..." if len(example["instruction"]) > 100 else example["instruction"]
                }
            })
        
        formatted_val = []
        for example in val_set:
            formatted = self.format_for_training(example)
            formatted_val.append({
                "text": formatted,
                "metadata": {
                    "quality_score": example["_quality_score"],
                    "tags": example.get("tags", [])
                }
            })
        
        # Save processed datasets
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        train_file = f"{output_dir}/train_dataset_{timestamp}.json"
        val_file = f"{output_dir}/val_dataset_{timestamp}.json"
        test_file = f"{output_dir}/test_dataset_{timestamp}.json"
        
        with open(train_file, 'w', encoding='utf-8') as f:
            json.dump(formatted_train, f, indent=2, ensure_ascii=False)
        
        with open(val_file, 'w', encoding='utf-8') as f:
            json.dump(formatted_val, f, indent=2, ensure_ascii=False)
        
        with open(test_file, 'w', encoding='utf-8') as f:
            json.dump([self.format_for_training(ex) for ex in test_set], f, indent=2, ensure_ascii=False)
        
        # Generate analysis report
        analysis = self.analyze_dataset(unique_examples)
        
        # Create comprehensive stats
        self.stats = PreprocessingStats(
            original_count=original_count,
            processed_count=len(unique_examples),
            filtered_count=original_count - len(valid_examples),
            duplicate_count=duplicate_count,
            invalid_count=invalid_count,
            avg_instruction_length=analysis["avg_instruction_length"],
            avg_output_length=analysis["avg_output_length"],
            category_distribution=analysis["tag_distribution"],
            quality_scores=[ex["_quality_score"] for ex in unique_examples]
        )
        
        # Save preprocessing report
        report = {
            "preprocessing_config": self.config,
            "statistics": {
                "original_examples": original_count,
                "processed_examples": len(unique_examples),
                "filtered_examples": original_count - len(valid_examples),
                "duplicate_examples": duplicate_count,
                "invalid_examples": invalid_count,
                "train_examples": len(train_set),
                "validation_examples": len(val_set),
                "test_examples": len(test_set)
            },
            "dataset_analysis": analysis,
            "output_files": {
                "train_dataset": train_file,
                "validation_dataset": val_file,
                "test_dataset": test_file
            },
            "processing_timestamp": datetime.now().isoformat()
        }
        
        report_file = f"{output_dir}/preprocessing_report_{timestamp}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # Print summary
        self.print_preprocessing_summary(report)
        
        logger.info(f"💾 Preprocessing complete!")
        logger.info(f"📁 Output directory: {output_dir}")
        logger.info(f"📊 Report: {report_file}")
        
        return report
    
    def print_preprocessing_summary(self, report: Dict):
        """Print preprocessing summary"""
        stats = report["statistics"]
        analysis = report["dataset_analysis"]
        
        print("\n" + "="*60)
        print("🛡️ WHIS CYBERSECURITY DATASET PREPROCESSING SUMMARY")
        print("="*60)
        
        print(f"\n📊 DATASET STATISTICS:")
        print(f"  Original examples: {stats['original_examples']:,}")
        print(f"  Processed examples: {stats['processed_examples']:,}")
        print(f"  Filtered out: {stats['filtered_examples']:,}")
        print(f"  Duplicates removed: {stats['duplicate_examples']:,}")
        print(f"  Invalid examples: {stats['invalid_examples']:,}")
        
        print(f"\n📈 TRAIN/VAL/TEST SPLIT:")
        print(f"  Training: {stats['train_examples']:,} examples")
        print(f"  Validation: {stats['validation_examples']:,} examples")
        print(f"  Test: {stats['test_examples']:,} examples")
        
        print(f"\n📏 CONTENT ANALYSIS:")
        print(f"  Avg instruction length: {analysis['avg_instruction_length']:.0f} chars")
        print(f"  Avg output length: {analysis['avg_output_length']:.0f} chars")
        print(f"  Avg quality score: {analysis['avg_quality_score']:.3f}")
        
        print(f"\n🏷️ TOP CATEGORIES:")
        for tag, count in list(analysis['tag_distribution'].items())[:5]:
            print(f"  {tag}: {count}")
        
        print(f"\n📝 CONTENT FEATURES:")
        for feature, count in analysis['content_features'].items():
            print(f"  {feature.replace('_', ' ').title()}: {count}")
        
        print("="*60)

def main():
    """Main preprocessing function"""
    
    # Configuration for Whis cybersecurity training
    config = {
        "min_instruction_length": 30,
        "max_instruction_length": 800, 
        "min_output_length": 100,
        "max_output_length": 3000,
        "min_quality_score": 0.65,
        "prompt_template": "alpaca",
        "sequence_length": 2048,
        "validation_split": 0.15,
        "test_split": 0.1,
        "cybersec_keywords": [
            "security", "attack", "threat", "vulnerability", "incident",
            "detection", "response", "MITRE", "ATT&CK", "T1110", "4625",
            "authentication", "SOAR", "SIEM", "Splunk", "LimaCharlie",
            "brute force", "failed logon", "playbook", "containment"
        ]
    }
    
    # Find all dataset files
    data_dir = Path("training_data")
    dataset_files = list(data_dir.glob("*.json"))
    
    if not dataset_files:
        print("❌ No dataset files found in training_data/")
        return
    
    print(f"📂 Found {len(dataset_files)} dataset files:")
    for file in dataset_files:
        print(f"  • {file.name}")
    
    # Initialize preprocessor
    preprocessor = CybersecDataPreprocessor(config)
    
    # Process datasets
    report = preprocessor.process_dataset(
        [str(f) for f in dataset_files],
        output_dir="processed_data"
    )
    
    return report

if __name__ == "__main__":
    main()