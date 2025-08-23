#!/usr/bin/env python3
"""
Vector Embeddings Generation for Whis RAG
Run this script to create vector embeddings from processed chunks
"""

import json
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
from datetime import datetime

def create_embeddings():
    print("🔍 Loading processed chunks...")
    with open("rag_chunks_20250822_152640.json", "r") as f:
        chunks = json.load(f)
    
    print(f"📊 Processing {len(chunks)} chunks...")
    
    # Load embedding model
    print("🤗 Loading SentenceTransformer model...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    # Create embeddings
    texts = [chunk["content"] for chunk in chunks]
    embeddings = model.encode(texts, show_progress_bar=True)
    
    print(f"✅ Created embeddings: {embeddings.shape}")
    
    # Create FAISS index
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity
    
    # Normalize embeddings for cosine similarity
    faiss.normalize_L2(embeddings)
    index.add(embeddings.astype('float32'))
    
    # Save index and chunks
    faiss.write_index(index, "whis_knowledge_index.faiss")
    
    # Save chunks with embeddings metadata
    for i, chunk in enumerate(chunks):
        chunk["embedding_index"] = i
        chunk["embedding_model"] = "all-MiniLM-L6-v2"
        chunk["embedding_dimension"] = dimension
    
    with open("whis_rag_chunks_with_embeddings.json", "w") as f:
        json.dump(chunks, f, indent=2)
    
    print("💾 Saved:")
    print("  - whis_knowledge_index.faiss (FAISS vector index)")
    print("  - whis_rag_chunks_with_embeddings.json (chunks with metadata)")
    
    return index, chunks

if __name__ == "__main__":
    create_embeddings()
