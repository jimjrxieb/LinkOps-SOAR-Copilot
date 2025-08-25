#!/usr/bin/env python3
"""
Fix comprehensive FAISS index metadata structure
Properly merge original cybersecurity knowledge with threat intelligence
"""

import json
import numpy as np
from datetime import datetime
from pathlib import Path
import faiss

def load_original_kb():
    """Load original cybersecurity knowledge base"""
    kb_path = "ai-training/rag/vectorstore/whis_cybersecurity_knowledge.metadata.json"
    
    with open(kb_path, 'r') as f:
        kb_data = json.load(f)
    
    # Extract chunks from the nested structure
    if "chunks" in kb_data:
        chunks = kb_data["chunks"]
    else:
        chunks = kb_data  # Fallback if structure is flat
    
    print(f"📚 Loaded {len(chunks)} original KB chunks")
    return chunks

def load_threat_intel():
    """Load threat intelligence metadata"""
    threat_path = "ai-training/rag/vectorstore/whis_threat_intel_20250824_203341.metadata.json"
    
    with open(threat_path, 'r') as f:
        threat_data = json.load(f)
    
    print(f"🛡️ Loaded {len(threat_data)} threat intel chunks")
    return threat_data

def create_unified_metadata(kb_chunks, threat_chunks):
    """Create properly structured unified metadata"""
    unified = []
    
    # Add KB chunks with standardized structure
    for i, chunk in enumerate(kb_chunks):
        unified_chunk = {
            "chunk_id": i,
            "title": chunk.get("title", f"KB Entry {i}"),
            "content": chunk.get("content", ""),
            "source": chunk.get("source", "knowledge_base"),
            "category": chunk.get("category", "general"),
            "type": chunk.get("type", "definition"),
            "source_type": "knowledge_base"
        }
        unified.append(unified_chunk)
    
    # Add threat intel chunks with adjusted IDs
    kb_count = len(kb_chunks)
    for j, chunk in enumerate(threat_chunks):
        unified_chunk = {
            "chunk_id": kb_count + j,
            "title": chunk.get("title", f"Threat Intel {j}"),
            "content": chunk.get("content", ""),
            "source": chunk.get("source", "threat_intelligence"),
            "category": chunk.get("category", "unknown"),
            "threat_type": chunk.get("threat_type", "unknown"),
            "classification": chunk.get("classification", "unknown"),
            "source_type": "threat_intelligence"
        }
        unified.append(unified_chunk)
    
    print(f"✅ Created {len(unified)} unified chunks")
    print(f"  - Knowledge base: {len(kb_chunks)} chunks")
    print(f"  - Threat intel: {len(threat_chunks)} chunks")
    
    return unified

def rebuild_faiss_index(unified_metadata):
    """Rebuild FAISS index with proper metadata alignment"""
    from sentence_transformers import SentenceTransformer
    
    print("🧠 Loading embedding model...")
    encoder = SentenceTransformer('all-MiniLM-L6-v2')
    
    # Create search texts for embedding
    search_texts = []
    for chunk in unified_metadata:
        # Create searchable text from title + content
        title = chunk.get('title', '')
        content = chunk.get('content', '')
        search_text = f"{title} {content}"[:1000]  # Limit length
        search_texts.append(search_text)
    
    print(f"🔮 Creating embeddings for {len(search_texts)} chunks...")
    embeddings = encoder.encode(search_texts, show_progress_bar=True)
    
    # Create FAISS index
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)
    
    # Normalize embeddings for cosine similarity
    faiss.normalize_L2(embeddings)
    index.add(embeddings.astype(np.float32))
    
    print(f"✅ Created FAISS index: {index.ntotal} vectors, {dimension}D")
    
    return index, encoder

def save_fixed_index(index, metadata):
    """Save the fixed comprehensive index"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    rag_dir = Path("ai-training/rag/vectorstore")
    
    # Save FAISS index
    index_path = rag_dir / f"whis_fixed_{timestamp}.faiss"
    faiss.write_index(index, str(index_path))
    print(f"💾 Saved fixed index: {index_path}")
    
    # Save metadata with proper structure
    metadata_path = rag_dir / f"whis_fixed_{timestamp}.metadata.json"
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    print(f"📋 Saved metadata: {metadata_path}")
    
    # Update pointers
    pointers_path = Path("ai-training/rag/indices/pointers.json")
    with open(pointers_path, 'r') as f:
        pointers = json.load(f)
    
    # Add fixed index and make it current
    index_name = f"whis_fixed_{timestamp}"
    pointers["indices"][index_name] = {
        "faiss_file": str(index_path),
        "metadata_file": str(metadata_path),
        "created_at": datetime.now().isoformat(),
        "version": "2.1.0",
        "chunk_count": len(metadata),
        "description": "Fixed: cybersecurity knowledge + threat intelligence"
    }
    
    pointers["current_index"] = index_name
    
    with open(pointers_path, 'w') as f:
        json.dump(pointers, f, indent=2)
    
    print(f"🎯 Set as current index: {index_name}")
    
    return index_path, metadata_path

def main():
    print("="*60)
    print("🔧 WHIS Comprehensive Index Repair")
    print("="*60)
    
    try:
        # Load both data sources
        kb_chunks = load_original_kb()
        threat_chunks = load_threat_intel()
        
        # Create unified metadata structure
        unified_metadata = create_unified_metadata(kb_chunks, threat_chunks)
        
        # Rebuild FAISS index with proper alignment
        index, encoder = rebuild_faiss_index(unified_metadata)
        
        # Save fixed version
        index_path, metadata_path = save_fixed_index(index, unified_metadata)
        
        print("\n" + "="*60)
        print("✅ COMPREHENSIVE INDEX REPAIRED")
        print("="*60)
        print(f"📊 Total chunks: {len(unified_metadata)}")
        print(f"💾 Index: {index_path}")
        print(f"📋 Metadata: {metadata_path}")
        
        # Show breakdown
        kb_count = sum(1 for chunk in unified_metadata if chunk.get("source_type") == "knowledge_base")
        threat_count = sum(1 for chunk in unified_metadata if chunk.get("source_type") == "threat_intelligence")
        
        print(f"\n📚 Content breakdown:")
        print(f"  • Knowledge base: {kb_count} chunks")
        print(f"  • Threat intelligence: {threat_count} chunks")
        
        print(f"\n🚀 Restart WHIS API to load the fixed index!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())