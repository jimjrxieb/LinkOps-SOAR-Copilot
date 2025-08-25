#!/usr/bin/env python3
"""
🚀 Simplified SOAR Training
============================
Uses existing trained models and focuses on dataset integration
"""

import os
import json
import logging
from pathlib import Path
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def consolidate_training_data():
    """Consolidate all training datasets into one comprehensive file"""
    logger.info("🎯 Consolidating all SOAR training data...")
    
    all_examples = []
    
    # Load Open-MalSec
    malsec_dir = Path("open-malsec")
    if malsec_dir.exists():
        logger.info("🦠 Processing Open-MalSec datasets...")
        for json_file in malsec_dir.glob("*.json"):
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        for item in data:
                            if 'instruction' in item and 'output' in item:
                                all_examples.append({
                                    "instruction": item['instruction'],
                                    "response": item['output'],
                                    "source": f"open-malsec:{json_file.stem}",
                                    "category": "malware_analysis"
                                })
                logger.info(f"  ✓ {json_file.name}: {len(data) if isinstance(data, list) else 1} examples")
            except:
                logger.warning(f"  ⚠️ Skipping {json_file.name}")
    
    # Load pipeline data
    curated_dir = Path("data/curated/llm")
    if curated_dir.exists():
        logger.info("🎓 Processing pipeline-generated data...")
        for jsonl_file in curated_dir.glob("*.jsonl"):
            with open(jsonl_file, 'r') as f:
                for line in f:
                    try:
                        item = json.loads(line)
                        if 'instruction' in item:
                            response = item.get('output', item.get('response', ''))
                            if response:
                                all_examples.append({
                                    "instruction": item['instruction'],
                                    "response": json.dumps(response) if isinstance(response, dict) else response,
                                    "source": f"pipeline:{jsonl_file.stem}",
                                    "category": "soar_response"
                                })
                    except:
                        pass
    
    # Load existing Whis data
    whis_dir = Path("ai-training/llm/data")
    if whis_dir.exists():
        logger.info("🤖 Processing Whis training data...")
        for jsonl_file in whis_dir.glob("whis_*.jsonl"):
            with open(jsonl_file, 'r') as f:
                for line in f:
                    try:
                        item = json.loads(line)
                        if 'instruction' in item and 'response' in item:
                            all_examples.append({
                                "instruction": item['instruction'],
                                "response": item['response'],
                                "source": f"whis:{jsonl_file.stem}",
                                "category": "whis_knowledge"
                            })
                    except:
                        pass
    
    # Save consolidated dataset
    output_dir = Path("ai-training/llm/data")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    consolidated_file = output_dir / f"soar_consolidated_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
    
    with open(consolidated_file, 'w') as f:
        for example in all_examples:
            f.write(json.dumps(example) + '\\n')
    
    # Create metadata
    metadata = {
        "created": datetime.now().isoformat(),
        "total_examples": len(all_examples),
        "categories": {
            "malware_analysis": len([e for e in all_examples if e['category'] == 'malware_analysis']),
            "soar_response": len([e for e in all_examples if e['category'] == 'soar_response']),
            "whis_knowledge": len([e for e in all_examples if e['category'] == 'whis_knowledge'])
        },
        "sources": list(set(e['source'] for e in all_examples))
    }
    
    metadata_file = output_dir / f"soar_metadata_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    logger.info(f"\\n✅ Consolidated dataset created!")
    logger.info(f"📁 Dataset: {consolidated_file}")
    logger.info(f"📋 Metadata: {metadata_file}")
    logger.info(f"📊 Total examples: {len(all_examples)}")
    
    for category, count in metadata['categories'].items():
        logger.info(f"  - {category}: {count}")
    
    return consolidated_file, metadata

def create_training_summary():
    """Create training readiness summary"""
    logger.info("📊 Creating training readiness summary...")
    
    summary = {
        "timestamp": datetime.now().isoformat(),
        "status": "READY_FOR_TRAINING",
        "datasets": {
            "open_malsec": {
                "path": "open-malsec/",
                "files": len(list(Path("open-malsec").glob("*.json"))),
                "status": "integrated"
            },
            "pipeline_generated": {
                "path": "data/curated/llm/",
                "files": len(list(Path("data/curated/llm").glob("*.jsonl"))),
                "status": "generated"
            },
            "whis_existing": {
                "path": "ai-training/llm/data/",
                "files": len(list(Path("ai-training/llm/data").glob("whis_*.jsonl"))),
                "status": "available"
            }
        },
        "recommendations": [
            "Use existing whis-mega-model as base",
            "Fine-tune on consolidated dataset",
            "Validate on security scenarios",
            "Deploy to HuggingFace Hub"
        ],
        "next_steps": [
            "cd ai-training/llm/scripts",
            "python3 enhanced_train.py",
            "python3 test_whis_model.py"
        ]
    }
    
    summary_file = Path("results/training_readiness.json")
    summary_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"📋 Training readiness: {summary_file}")
    return summary

def main():
    print("=" * 60)
    print("🎯 SOAR TRAINING DATA CONSOLIDATION")
    print("=" * 60)
    
    # Consolidate datasets
    consolidated_file, metadata = consolidate_training_data()
    
    # Create training summary
    summary = create_training_summary()
    
    print("\\n" + "=" * 60)
    print("✅ TRAINING DATA READY!")
    print("=" * 60)
    print(f"📊 Total examples: {metadata['total_examples']}")
    print(f"📁 Consolidated file: {consolidated_file}")
    
    print("\\n🚀 Ready to train with:")
    for category, count in metadata['categories'].items():
        print(f"  - {category.replace('_', ' ').title()}: {count} examples")
    
    print("\\n📋 Next steps:")
    print("  1. Use existing whis-mega-model as base")  
    print("  2. Fine-tune on consolidated dataset")
    print("  3. Test security scenario responses")
    print("  4. Deploy to production")
    
    print("\\n🎯 View progress: http://localhost:8000")

if __name__ == "__main__":
    main()