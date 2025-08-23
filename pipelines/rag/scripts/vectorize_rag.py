#!/usr/bin/env python3
"""
Vectorize and embed RAG knowledge base for Whis
Creates vector store from consolidated RAG datasets
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any
import numpy as np
from datetime import datetime

# Vector store libraries
from sentence_transformers import SentenceTransformer
import faiss
import pickle

print("🚀 WHIS RAG VECTORIZATION PIPELINE")
print("=" * 50)

class WhisRAGVectorizer:
    def __init__(self):
        # Use a cybersecurity-optimized embedding model
        print("📦 Loading sentence transformer model...")
        self.model = SentenceTransformer('all-MiniLM-L6-v2')  # Fast, good quality
        
        # Storage paths
        self.vector_dir = Path("knowledge/vectors")
        self.vector_dir.mkdir(exist_ok=True)
        
        self.knowledge_base = []
        self.embeddings = None
        self.faiss_index = None
        
    def load_knowledge_base(self):
        """Load all RAG datasets"""
        print("\n📚 Loading RAG knowledge base...")
        
        # Load consolidated RAG datasets
        rag_files = [
            "knowledge/consolidated_rag_training_data.json",
            "knowledge/enhanced_rag_training_data.json", 
            "knowledge/advanced_rag_training_data.json",
            "knowledge/threat_intel_rag_training_data.json",
            "knowledge/soar_automation_rag_training_data.json",
            "knowledge/k8s_security_rag_data.json"
        ]
        
        total_loaded = 0
        for file_path in rag_files:
            if os.path.exists(file_path):
                print(f"  📄 Loading: {file_path}")
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    
                    # Handle different data structures
                    if isinstance(data, list):
                        self.knowledge_base.extend(data)
                        total_loaded += len(data)
                    elif isinstance(data, dict) and 'examples' in data:
                        self.knowledge_base.extend(data['examples'])
                        total_loaded += len(data['examples'])
                        
                print(f"    ✅ Loaded: {len(data) if isinstance(data, list) else len(data.get('examples', []))} entries")
            else:
                print(f"  ⚠️  File not found: {file_path}")
        
        print(f"📊 Total knowledge entries: {total_loaded}")
        return total_loaded
        
    def create_embeddings(self):
        """Create embeddings for all knowledge entries"""
        print(f"\n🔮 Creating embeddings for {len(self.knowledge_base)} entries...")
        
        # Extract text for embedding
        texts_to_embed = []
        metadata = []
        
        for i, entry in enumerate(self.knowledge_base):
            # Combine query, context, and response for rich embedding
            if isinstance(entry, dict):
                text_parts = []
                
                # Add query/question
                if 'query' in entry:
                    text_parts.append(f"Query: {entry['query']}")
                elif 'question' in entry:
                    text_parts.append(f"Query: {entry['question']}")
                
                # Add context if available
                if 'context' in entry:
                    text_parts.append(f"Context: {entry['context']}")
                
                # Add response/answer
                if 'expected_response' in entry:
                    text_parts.append(f"Response: {entry['expected_response']}")
                elif 'answer' in entry:
                    text_parts.append(f"Response: {entry['answer']}")
                elif 'response' in entry:
                    text_parts.append(f"Response: {entry['response']}")
                
                combined_text = " | ".join(text_parts)
                texts_to_embed.append(combined_text)
                
                # Store metadata
                metadata.append({
                    'id': i,
                    'source': entry.get('source', 'unknown'),
                    'domain': entry.get('domain', 'cybersecurity'),
                    'type': entry.get('type', 'rag'),
                    'original_entry': entry
                })
            else:
                texts_to_embed.append(str(entry))
                metadata.append({'id': i, 'original_entry': entry})
        
        print(f"🎯 Embedding {len(texts_to_embed)} text entries...")
        
        # Create embeddings in batches for efficiency
        batch_size = 32
        all_embeddings = []
        
        for i in range(0, len(texts_to_embed), batch_size):
            batch = texts_to_embed[i:i+batch_size]
            print(f"  Processing batch {i//batch_size + 1}/{(len(texts_to_embed) + batch_size - 1)//batch_size}")
            
            batch_embeddings = self.model.encode(batch, show_progress_bar=False)
            all_embeddings.extend(batch_embeddings)
        
        self.embeddings = np.array(all_embeddings)
        self.metadata = metadata
        
        print(f"✅ Created embeddings: {self.embeddings.shape}")
        return self.embeddings
        
    def create_faiss_index(self):
        """Create FAISS index for fast similarity search"""
        print("\n🔍 Creating FAISS index...")
        
        # Use L2 distance (Euclidean) for similarity
        dimension = self.embeddings.shape[1]
        self.faiss_index = faiss.IndexFlatL2(dimension)
        
        # Add embeddings to index
        self.faiss_index.add(self.embeddings.astype(np.float32))
        
        print(f"✅ FAISS index created: {self.faiss_index.ntotal} entries, {dimension}D")
        return self.faiss_index
        
    def save_vector_store(self):
        """Save vector store components"""
        print("\n💾 Saving vector store...")
        
        # Save FAISS index
        faiss_path = self.vector_dir / "whis_rag.faiss"
        faiss.write_index(self.faiss_index, str(faiss_path))
        print(f"  📄 FAISS index: {faiss_path}")
        
        # Save embeddings
        embeddings_path = self.vector_dir / "embeddings.npy"
        np.save(embeddings_path, self.embeddings)
        print(f"  📄 Embeddings: {embeddings_path}")
        
        # Save metadata
        metadata_path = self.vector_dir / "metadata.pkl"
        with open(metadata_path, 'wb') as f:
            pickle.dump(self.metadata, f)
        print(f"  📄 Metadata: {metadata_path}")
        
        # Save knowledge base
        kb_path = self.vector_dir / "knowledge_base.json"
        with open(kb_path, 'w') as f:
            json.dump(self.knowledge_base, f, indent=2)
        print(f"  📄 Knowledge base: {kb_path}")
        
        # Create vector store manifest
        manifest = {
            "created": datetime.now().isoformat(),
            "model": "all-MiniLM-L6-v2", 
            "entries": len(self.knowledge_base),
            "embedding_dimension": self.embeddings.shape[1],
            "index_type": "FAISS_L2",
            "files": {
                "faiss_index": str(faiss_path),
                "embeddings": str(embeddings_path),
                "metadata": str(metadata_path),
                "knowledge_base": str(kb_path)
            }
        }
        
        manifest_path = self.vector_dir / "vector_store_manifest.json"
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        print(f"  📄 Manifest: {manifest_path}")
        
        return manifest
        
    def test_similarity_search(self, query="MITRE ATT&CK brute force detection", k=3):
        """Test the vector store with a sample query"""
        print(f"\n🔎 Testing similarity search: '{query}'")
        
        # Embed query
        query_embedding = self.model.encode([query])
        
        # Search similar entries
        distances, indices = self.faiss_index.search(query_embedding.astype(np.float32), k)
        
        print(f"📊 Top {k} similar entries:")
        for i, (dist, idx) in enumerate(zip(distances[0], indices[0])):
            entry = self.metadata[idx]['original_entry']
            print(f"\n  {i+1}. Distance: {dist:.4f}")
            if isinstance(entry, dict):
                print(f"     Query: {entry.get('query', 'N/A')[:100]}...")
                print(f"     Domain: {entry.get('domain', 'unknown')}")
            else:
                print(f"     Entry: {str(entry)[:100]}...")
        
        return distances, indices

def main():
    vectorizer = WhisRAGVectorizer()
    
    # Step 1: Load knowledge base
    total_entries = vectorizer.load_knowledge_base()
    if total_entries == 0:
        print("❌ No knowledge entries found!")
        return
    
    # Step 2: Create embeddings  
    embeddings = vectorizer.create_embeddings()
    
    # Step 3: Create FAISS index
    faiss_index = vectorizer.create_faiss_index()
    
    # Step 4: Save vector store
    manifest = vectorizer.save_vector_store()
    
    # Step 5: Test search
    vectorizer.test_similarity_search()
    
    print(f"\n🎉 RAG VECTORIZATION COMPLETE!")
    print(f"📊 Total entries vectorized: {total_entries}")
    print(f"📁 Vector store saved to: {vectorizer.vector_dir}")
    print(f"🔗 Ready for RAG retrieval integration!")

if __name__ == "__main__":
    main()