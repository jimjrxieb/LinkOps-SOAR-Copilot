#!/usr/bin/env python3
"""
Merge WHIS cybersecurity knowledge with Open-MalSec threat intelligence
Creates a comprehensive RAG index combining both knowledge bases
"""

import json
import numpy as np
from datetime import datetime
from pathlib import Path
from sentence_transformers import SentenceTransformer
import faiss

def load_existing_index():
    """Load existing cybersecurity knowledge index"""
    pointers_path = Path("ai-training/rag/indices/pointers.json")
    
    with open(pointers_path, 'r') as f:
        pointers = json.load(f)
    
    # Load the original cybersecurity knowledge
    kb_config = pointers["indices"]["whis_cybersecurity_knowledge"]
    
    print(f"📖 Loading existing index: {kb_config['chunk_count']} chunks")
    
    # Load FAISS index
    faiss_index = faiss.read_index(kb_config["faiss_file"])
    
    # Load metadata
    with open(kb_config["metadata_file"], 'r') as f:
        metadata = json.load(f)
    
    return faiss_index, metadata, kb_config

def load_threat_intel_index():
    """Load threat intelligence index"""
    pointers_path = Path("ai-training/rag/indices/pointers.json")
    
    with open(pointers_path, 'r') as f:
        pointers = json.load(f)
    
    # Find the latest threat intel index
    threat_config = None
    for name, config in pointers["indices"].items():
        if name.startswith("whis_threat_intel_"):
            threat_config = config
            break
    
    if not threat_config:
        raise Exception("No threat intelligence index found")
    
    print(f"📖 Loading threat intel: {threat_config['chunk_count']} chunks")
    
    # Load FAISS index
    faiss_index = faiss.read_index(threat_config["faiss_file"])
    
    # Load metadata
    with open(threat_config["metadata_file"], 'r') as f:
        metadata = json.load(f)
    
    return faiss_index, metadata, threat_config

def merge_indices(kb_index, kb_metadata, threat_index, threat_metadata):
    """Merge two FAISS indices and their metadata"""
    print(f"🔗 Merging indices...")
    
    # Get vectors from both indices
    kb_vectors = np.zeros((kb_index.ntotal, kb_index.d), dtype=np.float32)
    kb_index.reconstruct_n(0, kb_index.ntotal, kb_vectors)
    
    threat_vectors = np.zeros((threat_index.ntotal, threat_index.d), dtype=np.float32)
    threat_index.reconstruct_n(0, threat_index.ntotal, threat_vectors)
    
    # Combine vectors
    merged_vectors = np.vstack([kb_vectors, threat_vectors])
    
    # Create new merged index
    merged_index = faiss.IndexFlatIP(merged_vectors.shape[1])
    merged_index.add(merged_vectors)
    
    # Merge metadata (adjust chunk_ids for threat intel)
    merged_metadata = []
    
    # Add existing KB metadata
    for item in kb_metadata:
        merged_metadata.append(item)
    
    # Add threat intel metadata with adjusted chunk_ids
    kb_count = len(kb_metadata)
    for i, item in enumerate(threat_metadata):
        new_item = item.copy()
        new_item["chunk_id"] = kb_count + i
        # Add threat intel marker
        new_item["source_type"] = "threat_intelligence"
        merged_metadata.append(new_item)
    
    print(f"✅ Merged index: {merged_index.ntotal} total chunks")
    print(f"  - Knowledge base: {len(kb_metadata)} chunks") 
    print(f"  - Threat intel: {len(threat_metadata)} chunks")
    
    return merged_index, merged_metadata

def save_merged_index(merged_index, merged_metadata):
    """Save the merged comprehensive index"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    rag_dir = Path("ai-training/rag/vectorstore")
    
    # Save merged FAISS index
    index_path = rag_dir / f"whis_comprehensive_{timestamp}.faiss"
    faiss.write_index(merged_index, str(index_path))
    print(f"💾 Saved merged index: {index_path}")
    
    # Save merged metadata
    metadata_path = rag_dir / f"whis_comprehensive_{timestamp}.metadata.json"
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(merged_metadata, f, indent=2, ensure_ascii=False)
    print(f"📋 Saved merged metadata: {metadata_path}")
    
    # Update pointers
    pointers_path = Path("ai-training/rag/indices/pointers.json")
    with open(pointers_path, 'r') as f:
        pointers = json.load(f)
    
    # Add merged index
    index_name = f"whis_comprehensive_{timestamp}"
    pointers["indices"][index_name] = {
        "faiss_file": str(index_path),
        "metadata_file": str(metadata_path),
        "created_at": datetime.now().isoformat(),
        "version": "2.0.0",
        "chunk_count": len(merged_metadata),
        "description": "Comprehensive: cybersecurity knowledge + threat intelligence"
    }
    
    # Make it the current index
    pointers["current_index"] = index_name
    
    with open(pointers_path, 'w') as f:
        json.dump(pointers, f, indent=2)
    
    print(f"🎯 Set as current index: {index_name}")
    
    return index_path, metadata_path, index_name

def main():
    print("="*70)
    print("🔗 WHIS Comprehensive RAG Index Merger")
    print("="*70)
    
    try:
        # Load both indices
        kb_index, kb_metadata, kb_config = load_existing_index()
        threat_index, threat_metadata, threat_config = load_threat_intel_index()
        
        # Merge them
        merged_index, merged_metadata = merge_indices(
            kb_index, kb_metadata, threat_index, threat_metadata
        )
        
        # Save merged index
        index_path, metadata_path, index_name = save_merged_index(
            merged_index, merged_metadata
        )
        
        print("\n" + "="*70)
        print("✅ COMPREHENSIVE RAG INDEX CREATED")
        print("="*70)
        print(f"📊 Total chunks: {len(merged_metadata)}")
        print(f"💾 Index: {index_path}")
        print(f"📋 Metadata: {metadata_path}")
        
        # Count categories
        kb_chunks = sum(1 for item in merged_metadata if item.get("source_type") != "threat_intelligence")
        threat_chunks = sum(1 for item in merged_metadata if item.get("source_type") == "threat_intelligence")
        
        print(f"\n📚 Content breakdown:")
        print(f"  • Cybersecurity Knowledge: {kb_chunks} chunks")
        print(f"  • Threat Intelligence: {threat_chunks} chunks")
        
        # Show threat categories
        threat_categories = {}
        for item in merged_metadata:
            if item.get("source_type") == "threat_intelligence":
                cat = item.get("category", "unknown")
                threat_categories[cat] = threat_categories.get(cat, 0) + 1
        
        print(f"\n🛡️ Threat intelligence categories:")
        for cat, count in sorted(threat_categories.items()):
            print(f"  • {cat.replace('_', ' ').title()}: {count} examples")
        
        print(f"\n🚀 WHIS can now answer:")
        print("  • 'What is Kubernetes?' (from knowledge base)")
        print("  • 'How do romance scams work?' (from threat intel)")
        print("  • 'Show me ransomware indicators' (from threat intel)")
        print("  • 'What is NIST CSF?' (from knowledge base)")
        print("  • 'Detect phishing emails' (from threat intel)")
        
        print(f"\n⚡ Restart WHIS API to load the new comprehensive index!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())