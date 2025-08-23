#!/usr/bin/env python3
"""
Mega Dataset Integration for Whis Training
Combines all available training datasets into one comprehensive dataset
"""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict
import hashlib

class WhisMegaDatasetBuilder:
    def __init__(self):
        self.mega_dataset = []
        self.stats = {
            "datasets_integrated": 0,
            "total_examples": 0,
            "duplicates_removed": 0,
            "quality_scores": [],
            "categories": {},
            "sources": {}
        }
        self.dedup_hashes = set()
        
    def calculate_content_hash(self, text: str) -> str:
        """Calculate hash for deduplication"""
        return hashlib.md5(text.encode()).hexdigest()[:12]
        
    def load_dataset(self, dataset_path: Path, source_name: str) -> List[Dict]:
        """Load a dataset file"""
        print(f"📥 Loading: {source_name}")
        
        try:
            with open(dataset_path, 'r') as f:
                data = json.load(f)
                
            examples_loaded = len(data)
            self.stats["sources"][source_name] = {
                "path": str(dataset_path),
                "examples": examples_loaded,
                "loaded_at": datetime.now().isoformat()
            }
            
            print(f"  ✅ {examples_loaded} examples loaded")
            return data
            
        except Exception as e:
            print(f"  ❌ Error loading {source_name}: {e}")
            return []
            
    def deduplicate_example(self, example: Dict) -> bool:
        """Check if example is duplicate"""
        text = example.get("text", "")
        content_hash = self.calculate_content_hash(text)
        
        if content_hash in self.dedup_hashes:
            self.stats["duplicates_removed"] += 1
            return False
            
        self.dedup_hashes.add(content_hash)
        return True
        
    def integrate_datasets(self):
        """Integrate all available training datasets"""
        print("🚀 WHIS MEGA DATASET INTEGRATION")
        print("=" * 50)
        
        # Define all available datasets
        datasets_to_integrate = [
            {
                "path": Path("training/processed_data/train_dataset_20250822_150258.json"),
                "name": "Original Training Dataset",
                "priority": 1
            },
            {
                "path": Path("training/processed_data/performance_boost_dataset.json"),
                "name": "Performance Boost Dataset", 
                "priority": 2
            },
            {
                "path": Path("training/processed_data/whis_action_schema_processed_20250822_204902.json"),
                "name": "Action Schema Dataset (100 examples)",
                "priority": 3
            }
        ]
        
        # Load and integrate datasets
        for dataset_info in datasets_to_integrate:
            if dataset_info["path"].exists():
                dataset = self.load_dataset(dataset_info["path"], dataset_info["name"])
                
                # Process each example
                for example in dataset:
                    if self.deduplicate_example(example):
                        # Add source information
                        if "metadata" not in example:
                            example["metadata"] = {}
                        example["metadata"]["dataset_source"] = dataset_info["name"]
                        example["metadata"]["priority"] = dataset_info["priority"]
                        example["metadata"]["integrated_at"] = datetime.now().isoformat()
                        
                        # Track quality scores
                        quality_score = example.get("metadata", {}).get("quality_score", 0.8)
                        self.stats["quality_scores"].append(quality_score)
                        
                        # Track categories
                        category = example.get("metadata", {}).get("category", "unknown")
                        self.stats["categories"][category] = self.stats["categories"].get(category, 0) + 1
                        
                        self.mega_dataset.append(example)
                        
                self.stats["datasets_integrated"] += 1
            else:
                print(f"  ⚠️ Dataset not found: {dataset_info['path']}")
                
        self.stats["total_examples"] = len(self.mega_dataset)
        
        print(f"\n📊 INTEGRATION SUMMARY")
        print("-" * 30)
        print(f"📚 Datasets integrated: {self.stats['datasets_integrated']}")
        print(f"📈 Total examples: {self.stats['total_examples']}")
        print(f"🔄 Duplicates removed: {self.stats['duplicates_removed']}")
        
        # Quality analysis
        if self.stats["quality_scores"]:
            avg_quality = sum(self.stats["quality_scores"]) / len(self.stats["quality_scores"])
            high_quality = sum(1 for score in self.stats["quality_scores"] if score >= 0.9)
            print(f"⭐ Average quality: {avg_quality:.3f}")
            print(f"🏆 High quality examples: {high_quality}")
            
        return self.mega_dataset
        
    def save_mega_dataset(self):
        """Save the integrated mega dataset"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save main dataset
        dataset_path = Path(f"training/processed_data/whis_mega_dataset_{timestamp}.json")
        dataset_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(dataset_path, 'w') as f:
            json.dump(self.mega_dataset, f, indent=2)
            
        # Save stats
        stats_path = Path(f"training/processed_data/mega_integration_stats_{timestamp}.json")
        with open(stats_path, 'w') as f:
            json.dump(self.stats, f, indent=2)
            
        print(f"\n💾 MEGA DATASET SAVED")
        print("-" * 25)
        print(f"📄 Dataset: {dataset_path}")
        print(f"📊 Stats: {stats_path}")
        
        # Display source breakdown
        print(f"\n📚 SOURCE BREAKDOWN")
        print("-" * 20)
        for source, info in self.stats["sources"].items():
            print(f"  {source}: {info['examples']} examples")
            
        # Display category breakdown
        if self.stats["categories"]:
            print(f"\n🏷️ CATEGORY BREAKDOWN") 
            print("-" * 22)
            for category, count in sorted(self.stats["categories"].items()):
                if category != "unknown":
                    print(f"  {category}: {count}")
                    
        return {
            "dataset_path": str(dataset_path),
            "stats_path": str(stats_path),
            "total_examples": self.stats["total_examples"],
            "datasets_integrated": self.stats["datasets_integrated"],
            "average_quality": sum(self.stats["quality_scores"]) / len(self.stats["quality_scores"]) if self.stats["quality_scores"] else 0
        }

def main():
    """Main integration process"""
    builder = WhisMegaDatasetBuilder()
    mega_dataset = builder.integrate_datasets()
    result = builder.save_mega_dataset()
    
    print(f"\n🎉 MEGA DATASET INTEGRATION COMPLETE!")
    print(f"🚀 Ready for training with {result['total_examples']} high-quality examples!")
    
    return result

if __name__ == "__main__":
    main()