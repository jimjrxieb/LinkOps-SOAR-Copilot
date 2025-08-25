#!/usr/bin/env python3
"""
Vectorize Open-MalSec data for WHIS RAG system
Converts real-world threat intelligence into searchable knowledge chunks
"""

import json
import os
from datetime import datetime
from pathlib import Path
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss

def load_open_malsec_data():
    """Load all Open-MalSec JSON files"""
    data_dir = Path("open-malsec")
    chunks = []
    
    json_files = list(data_dir.glob("*.json"))
    print(f"📂 Found {len(json_files)} Open-MalSec files")
    
    for json_file in json_files:
        print(f"📖 Processing {json_file.name}")
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            category = json_file.stem.replace('-', '_')
            
            for item in data:
                # Create searchable chunk from each threat example
                chunk = create_rag_chunk(item, category)
                if chunk:
                    chunks.append(chunk)
                    
        except json.JSONDecodeError as e:
            print(f"⚠️ Skipping {json_file.name}: JSON parse error - {e}")
            continue
        except Exception as e:
            print(f"⚠️ Error processing {json_file.name}: {e}")
            continue
    
    print(f"✅ Created {len(chunks)} threat intelligence chunks")
    return chunks

def create_rag_chunk(item, category):
    """Convert Open-MalSec item to RAG chunk format"""
    try:
        # Build searchable content
        content_parts = []
        
        # Add instruction as title
        if 'instruction' in item:
            content_parts.append(f"# {item['instruction']}")
        
        # Add input details
        if 'input' in item:
            input_data = item['input']
            if isinstance(input_data, dict):
                content_parts.append("## Threat Example:")
                for key, value in input_data.items():
                    if isinstance(value, str) and len(value) < 500:
                        content_parts.append(f"**{key.title()}:** {value}")
            else:
                content_parts.append(f"## Example: {str(input_data)[:300]}")
        
        # Add analysis/output
        if 'output' in item:
            output_data = item['output']
            content_parts.append("## Analysis:")
            
            if isinstance(output_data, dict):
                if 'classification' in output_data:
                    content_parts.append(f"**Classification:** {output_data['classification']}")
                if 'description' in output_data:
                    content_parts.append(f"**Description:** {output_data['description']}")
                if 'indicators' in output_data:
                    content_parts.append("**Indicators:**")
                    for indicator in output_data['indicators'][:5]:  # Limit to top 5
                        content_parts.append(f"• {indicator}")
            else:
                content_parts.append(str(output_data)[:300])
        
        # Create searchable text for embeddings
        search_text = " ".join(content_parts)
        
        # Create metadata
        metadata = {
            "id": f"malsec_{category}_{item.get('id', 'unknown')}",
            "category": category,
            "threat_type": category.replace('_', ' ').title(),
            "classification": item.get('output', {}).get('classification', 'unknown'),
            "source": "Open-MalSec",
            "file": f"open-malsec/{category.replace('_', '-')}.json"
        }
        
        return {
            "content": "\n".join(content_parts),
            "search_text": search_text,
            "metadata": metadata,
            "title": item.get('instruction', f"{category.title()} Example")
        }
        
    except Exception as e:
        print(f"⚠️ Error processing item: {e}")
        return None

def create_threat_intel_index(chunks):
    """Create FAISS index for threat intelligence"""
    print("🧠 Loading embedding model...")
    encoder = SentenceTransformer('all-MiniLM-L6-v2')
    
    # Extract search texts for embedding
    texts = [chunk['search_text'] for chunk in chunks]
    
    print(f"🔮 Creating embeddings for {len(texts)} chunks...")
    embeddings = encoder.encode(texts, show_progress_bar=True)
    
    # Create FAISS index
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)  # Inner product for similarity
    
    # Normalize embeddings for cosine similarity
    faiss.normalize_L2(embeddings)
    index.add(embeddings.astype(np.float32))
    
    print(f"✅ Created FAISS index: {index.ntotal} vectors, {dimension}D")
    
    return index, encoder, embeddings

def save_enhanced_rag_system(chunks, index, encoder):
    """Save enhanced RAG system with threat intelligence"""
    rag_dir = Path("ai-training/rag/vectorstore")
    rag_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save FAISS index
    index_path = rag_dir / f"whis_threat_intel_{timestamp}.faiss"
    faiss.write_index(index, str(index_path))
    print(f"💾 Saved FAISS index: {index_path}")
    
    # Save metadata
    metadata = []
    for i, chunk in enumerate(chunks):
        metadata.append({
            "chunk_id": i,
            "title": chunk["title"],
            "content": chunk["content"],
            "source": chunk["metadata"]["file"],
            "category": chunk["metadata"]["category"],
            "threat_type": chunk["metadata"]["threat_type"],
            "classification": chunk["metadata"]["classification"]
        })
    
    metadata_path = rag_dir / f"whis_threat_intel_{timestamp}.metadata.json"
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    print(f"📋 Saved metadata: {metadata_path}")
    
    # Update pointers to include threat intel index
    pointers_path = Path("ai-training/rag/indices/pointers.json")
    if pointers_path.exists():
        with open(pointers_path, 'r') as f:
            pointers = json.load(f)
    else:
        pointers = {"current_index": "", "indices": {}}
    
    # Add new threat intel index
    index_name = f"whis_threat_intel_{timestamp}"
    pointers["indices"][index_name] = {
        "faiss_file": str(index_path),
        "metadata_file": str(metadata_path),
        "created_at": datetime.now().isoformat(),
        "version": "1.1.0",
        "chunk_count": len(chunks),
        "description": "Enhanced with Open-MalSec threat intelligence"
    }
    
    # Optionally make it current (for testing)
    print(f"\n🔄 Available indices:")
    for name, config in pointers["indices"].items():
        print(f"  - {name}: {config['chunk_count']} chunks ({config['description']})")
    
    print(f"\n💡 To switch WHIS to threat intel index:")
    print(f'   Update pointers.json "current_index": "{index_name}"')
    
    with open(pointers_path, 'w') as f:
        json.dump(pointers, f, indent=2)
    
    return index_path, metadata_path

def main():
    print("="*60)
    print("🛡️ WHIS Threat Intelligence Vectorization")
    print("="*60)
    
    # Load Open-MalSec data
    chunks = load_open_malsec_data()
    
    if not chunks:
        print("❌ No data found to vectorize")
        return
    
    # Create enhanced RAG index
    index, encoder, embeddings = create_threat_intel_index(chunks)
    
    # Save enhanced system
    index_path, metadata_path = save_enhanced_rag_system(chunks, index, encoder)
    
    print("\n" + "="*60)
    print("✅ THREAT INTELLIGENCE VECTORIZATION COMPLETE")
    print("="*60)
    print(f"📊 Total chunks: {len(chunks)}")
    print(f"🎯 Categories: {len(set(chunk['metadata']['category'] for chunk in chunks))}")
    print(f"💾 Index: {index_path}")
    print(f"📋 Metadata: {metadata_path}")
    print("\n🔮 WHIS now has access to:")
    
    categories = {}
    for chunk in chunks:
        cat = chunk['metadata']['threat_type']
        categories[cat] = categories.get(cat, 0) + 1
    
    for category, count in sorted(categories.items()):
        print(f"  • {category}: {count} examples")
    
    print("\n💡 This enables WHIS to answer questions like:")
    print("  - 'How do I detect PayPal phishing?'")
    print("  - 'What are common romance scam indicators?'") 
    print("  - 'Show me ransomware IOCs'")
    print("  - 'Analyze this suspicious email'")

if __name__ == "__main__":
    main()