#!/usr/bin/env python3
"""
RAG Dataset Consolidator
Combines all RAG training datasets into unified format for vectorization
"""

import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Set

class RAGDatasetConsolidator:
    """Consolidate multiple RAG datasets"""
    
    def __init__(self):
        self.consolidated_examples = []
        self.deduplication_hashes = set()
        
    def load_dataset(self, file_path: str) -> Dict:
        """Load a JSON dataset"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"⚠️ Dataset not found: {file_path}")
            return {"examples": []}
        except json.JSONDecodeError:
            print(f"⚠️ Invalid JSON in: {file_path}")
            return {"examples": []}
    
    def deduplicate_example(self, example: Dict) -> bool:
        """Check if example is duplicate based on query hash"""
        query_hash = hashlib.md5(example["query"].encode()).hexdigest()
        if query_hash in self.deduplication_hashes:
            return False
        self.deduplication_hashes.add(query_hash)
        return True
    
    def normalize_example(self, example: Dict, source_dataset: str) -> Dict:
        """Normalize example format and add source tracking"""
        normalized = {
            "id": example.get("id", f"unknown_{len(self.consolidated_examples):03d}"),
            "query": example["query"],
            "context": example["context"],
            "expected_response": example["expected_response"],
            "knowledge_source": example.get("knowledge_source", "Unknown"),
            "tags": example.get("tags", []),
            "source_dataset": source_dataset,
            "created_date": example.get("created_date", datetime.now().isoformat()),
            "content_hash": example.get("content_hash", hashlib.md5(example["query"].encode()).hexdigest()[:8]),
            "retrieval_type": example.get("retrieval_type", "supervised_learning"),
            "complexity_level": example.get("complexity_level", "standard"),
            "intelligence_type": example.get("intelligence_type", "tactical")
        }
        return normalized
    
    def consolidate_datasets(self) -> Dict:
        """Consolidate all available RAG datasets"""
        
        dataset_files = [
            ("enhanced_rag_training_data.json", "basic_rag"),
            ("advanced_rag_training_data.json", "advanced_rag"), 
            ("threat_intel_rag_training_data.json", "threat_intel_rag"),
            ("soar_automation_rag_training_data.json", "soar_automation_rag")
        ]
        
        total_loaded = 0
        total_deduplicated = 0
        dataset_stats = {}
        
        print("📊 Loading and consolidating RAG datasets...")
        print("=" * 50)
        
        for file_path, source_name in dataset_files:
            print(f"\\n🔍 Processing: {file_path}")
            dataset = self.load_dataset(file_path)
            
            if "examples" not in dataset:
                print(f"  ⚠️ No examples found in {file_path}")
                continue
                
            examples = dataset["examples"]
            loaded_count = len(examples)
            total_loaded += loaded_count
            
            # Process examples
            unique_examples = []
            for example in examples:
                if self.deduplicate_example(example):
                    normalized = self.normalize_example(example, source_name)
                    unique_examples.append(normalized)
                    self.consolidated_examples.append(normalized)
                else:
                    total_deduplicated += 1
            
            dataset_stats[source_name] = {
                "loaded": loaded_count,
                "unique": len(unique_examples),
                "duplicates": loaded_count - len(unique_examples)
            }
            
            print(f"  ✅ Loaded: {loaded_count} examples")
            print(f"  🔄 Unique: {len(unique_examples)} examples")
            print(f"  ❌ Duplicates: {loaded_count - len(unique_examples)} examples")
        
        # Generate consolidated dataset
        consolidated = {
            "dataset_info": {
                "name": "Whis Consolidated RAG Training Data",
                "version": "4.0",
                "created_date": datetime.now().isoformat(),
                "total_examples": len(self.consolidated_examples),
                "total_loaded": total_loaded,
                "total_deduplicated": total_deduplicated,
                "deduplication_rate": f"{(total_deduplicated/total_loaded)*100:.1f}%" if total_loaded > 0 else "0.0%",
                "source_datasets": dataset_stats,
                "categories": self._generate_category_stats(),
                "complexity_distribution": self._generate_complexity_stats(),
                "tag_distribution": self._generate_tag_stats()
            },
            "examples": self.consolidated_examples
        }
        
        print(f"\\n📈 CONSOLIDATION SUMMARY:")
        print(f"  📊 Total Examples Loaded: {total_loaded}")
        print(f"  ✅ Unique Examples: {len(self.consolidated_examples)}")
        print(f"  ❌ Duplicates Removed: {total_deduplicated}")
        print(f"  🎯 Deduplication Rate: {consolidated['dataset_info']['deduplication_rate']}")
        
        return consolidated
    
    def _generate_category_stats(self) -> Dict:
        """Generate category statistics"""
        categories = {}
        for example in self.consolidated_examples:
            tags = example.get("tags", [])
            for tag in tags:
                categories[tag] = categories.get(tag, 0) + 1
        return dict(sorted(categories.items(), key=lambda x: x[1], reverse=True))
    
    def _generate_complexity_stats(self) -> Dict:
        """Generate complexity level statistics"""
        complexity = {}
        for example in self.consolidated_examples:
            level = example.get("complexity_level", "standard")
            complexity[level] = complexity.get(level, 0) + 1
        return complexity
    
    def _generate_tag_stats(self) -> Dict:
        """Generate top tag statistics"""
        tag_counts = {}
        for example in self.consolidated_examples:
            tags = example.get("tags", [])
            for tag in tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        # Return top 15 tags
        sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
        return dict(sorted_tags[:15])
    
    def save_consolidated_dataset(self, output_file: str = "consolidated_rag_training_data.json"):
        """Save consolidated dataset"""
        
        consolidated = self.consolidate_datasets()
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(consolidated, f, indent=2, ensure_ascii=False)
        
        print(f"\\n💾 Saved consolidated dataset to: {output_file}")
        
        return consolidated
    
    def generate_vectorization_manifest(self, dataset: Dict, manifest_file: str = "rag_vectorization_manifest.json"):
        """Generate manifest for vectorization pipeline"""
        
        manifest = {
            "vectorization_config": {
                "dataset_file": "consolidated_rag_training_data.json",
                "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
                "vector_dimension": 384,
                "chunk_size": 512,
                "chunk_overlap": 64,
                "similarity_threshold": 0.75,
                "index_type": "faiss_flat"
            },
            "preprocessing_config": {
                "sanitization_required": True,
                "pii_redaction": True,
                "content_validation": True,
                "quality_threshold": 0.8
            },
            "dataset_summary": {
                "total_examples": dataset["dataset_info"]["total_examples"],
                "categories": len(dataset["dataset_info"]["categories"]),
                "complexity_levels": list(dataset["dataset_info"]["complexity_distribution"].keys()),
                "source_datasets": list(dataset["dataset_info"]["source_datasets"].keys())
            },
            "quality_metrics": {
                "deduplication_rate": dataset["dataset_info"]["deduplication_rate"],
                "avg_query_length": sum(len(ex["query"]) for ex in dataset["examples"]) // len(dataset["examples"]),
                "avg_response_length": sum(len(ex["expected_response"]) for ex in dataset["examples"]) // len(dataset["examples"]),
                "coverage_score": len(dataset["dataset_info"]["categories"]) / 50  # Assuming 50 ideal categories
            },
            "created_date": datetime.now().isoformat(),
            "ready_for_vectorization": True
        }
        
        with open(manifest_file, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        
        print(f"📋 Generated vectorization manifest: {manifest_file}")
        
        return manifest

def main():
    """Consolidate RAG datasets"""
    print("🔄 RAG DATASET CONSOLIDATOR")
    print("=" * 50)
    
    consolidator = RAGDatasetConsolidator()
    
    # Consolidate datasets
    consolidated_dataset = consolidator.save_consolidated_dataset()
    
    # Generate vectorization manifest
    manifest = consolidator.generate_vectorization_manifest(consolidated_dataset)
    
    print(f"\\n📊 FINAL DATASET STATISTICS:")
    print(f"  🎯 Total Examples: {consolidated_dataset['dataset_info']['total_examples']}")
    print(f"  📚 Categories: {len(consolidated_dataset['dataset_info']['categories'])}")
    print(f"  🏷️ Top Tags: {list(consolidated_dataset['dataset_info']['tag_distribution'].keys())[:5]}")
    print(f"  📈 Quality Score: {manifest['quality_metrics']['coverage_score']:.2f}")
    
    print(f"\\n✅ RAG consolidation complete!")
    print(f"🚀 Ready for vectorization pipeline!")
    
    return consolidated_dataset, manifest

if __name__ == "__main__":
    main()