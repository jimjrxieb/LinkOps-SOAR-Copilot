#!/usr/bin/env python3
"""
WHIS Senior Knowledge Base Embedding Generator
Creates embeddings for DevSecOps senior-level scenarios
"""

import json
import numpy as np
import faiss
import os
from pathlib import Path
from sentence_transformers import SentenceTransformer
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WhisEmbeddingGenerator:
    def __init__(self):
        self.model_name = "all-MiniLM-L6-v2"  # Fast, good quality embeddings
        self.model = None
        self.chunks_dir = Path("../chunks")
        self.vectorstore_dir = Path("../vectorstore")
        self.vectorstore_dir.mkdir(exist_ok=True)
        
    def load_model(self):
        """Load embedding model"""
        print(f"📥 Loading embedding model: {self.model_name}")
        try:
            self.model = SentenceTransformer(self.model_name)
            print("✅ Model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise
    
    def load_knowledge_base(self):
        """Load processed knowledge base"""
        kb_file = self.chunks_dir / "whis_vectorization_ready.json"
        
        if not kb_file.exists():
            raise FileNotFoundError(f"Knowledge base not found: {kb_file}")
        
        print(f"📚 Loading knowledge base: {kb_file}")
        with open(kb_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"  📊 Total chunks: {len(data['chunks'])}")
        return data
    
    def create_embeddings(self, chunks):
        """Generate embeddings for all chunks"""
        print("🧠 Generating embeddings...")
        
        texts = [chunk["text"] for chunk in chunks]
        
        # Generate embeddings in batches for memory efficiency
        batch_size = 32
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            print(f"  Processing batch {i//batch_size + 1}/{(len(texts)-1)//batch_size + 1}")
            
            embeddings = self.model.encode(batch, show_progress_bar=False)
            all_embeddings.extend(embeddings)
        
        embeddings_array = np.array(all_embeddings).astype('float32')
        print(f"✅ Generated embeddings shape: {embeddings_array.shape}")
        
        return embeddings_array
    
    def build_faiss_index(self, embeddings):
        """Build FAISS index for similarity search"""
        print("🔍 Building FAISS index...")
        
        dimension = embeddings.shape[1]
        
        # Use IndexFlatIP for inner product similarity (good for sentence embeddings)
        index = faiss.IndexFlatIP(dimension)
        
        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(embeddings)
        
        # Add embeddings to index
        index.add(embeddings)
        
        print(f"✅ FAISS index built with {index.ntotal} vectors")
        return index
    
    def save_vectorstore(self, index, knowledge_base):
        """Save vectorstore and metadata"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save FAISS index
        index_file = self.vectorstore_dir / f"whis_senior_knowledge_{timestamp}.faiss"
        faiss.write_index(index, str(index_file))
        
        # Save metadata
        metadata = {
            "created_at": datetime.now().isoformat(),
            "model_name": self.model_name,
            "total_chunks": len(knowledge_base["chunks"]),
            "embedding_dimension": index.d,
            "categories": list(set(chunk["metadata"]["category"] for chunk in knowledge_base["chunks"])),
            "tags": list(set(tag for chunk in knowledge_base["chunks"] for tag in chunk["metadata"]["tags"])),
            "chunks": knowledge_base["chunks"]
        }
        
        metadata_file = self.vectorstore_dir / f"whis_senior_metadata_{timestamp}.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Vectorstore saved:")
        print(f"  🔍 Index: {index_file}")
        print(f"  📄 Metadata: {metadata_file}")
        
        # Create symlinks to latest
        latest_index = self.vectorstore_dir / "whis_senior_knowledge_latest.faiss"
        latest_metadata = self.vectorstore_dir / "whis_senior_metadata_latest.json"
        
        if latest_index.is_symlink() or latest_index.exists():
            latest_index.unlink()
        if latest_metadata.is_symlink() or latest_metadata.exists():
            latest_metadata.unlink()
            
        latest_index.symlink_to(index_file.name)
        latest_metadata.symlink_to(metadata_file.name)
        
        print(f"🔗 Latest links created")
        
        return index_file, metadata_file
    
    def test_search(self, index, metadata, query="How do you handle patch management with business constraints?"):
        """Test the vectorstore with a sample query"""
        print(f"\n🧪 Testing vectorstore with query: '{query}'")
        
        # Generate query embedding
        query_embedding = self.model.encode([query])
        faiss.normalize_L2(query_embedding.astype('float32'))
        
        # Search for top 3 similar chunks
        scores, indices = index.search(query_embedding.astype('float32'), 3)
        
        print(f"\n🔍 Top 3 matches:")
        for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
            chunk = metadata["chunks"][idx]
            print(f"\n{i+1}. Score: {score:.3f}")
            print(f"   Title: {chunk['metadata']['category']} - {chunk['text'][:100]}...")
            print(f"   Tags: {', '.join(chunk['metadata']['tags'][:3])}")
    
    def generate_complete_vectorstore(self):
        """Complete pipeline to generate vectorstore"""
        print("🚀 WHIS SENIOR KNOWLEDGE VECTORSTORE GENERATOR")
        print("=" * 60)
        
        # Load model
        self.load_model()
        
        # Load knowledge base
        knowledge_base = self.load_knowledge_base()
        
        # Generate embeddings
        embeddings = self.create_embeddings(knowledge_base["chunks"])
        
        # Build FAISS index
        index = self.build_faiss_index(embeddings)
        
        # Save vectorstore
        index_file, metadata_file = self.save_vectorstore(index, knowledge_base)
        
        # Load metadata for testing
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        
        # Test search
        self.test_search(index, metadata)
        
        print(f"\n✅ VECTORSTORE GENERATION COMPLETE!")
        print(f"📊 Summary:")
        print(f"  📚 Knowledge chunks: {len(knowledge_base['chunks'])}")
        print(f"  🧠 Embedding model: {self.model_name}")
        print(f"  📐 Vector dimension: {embeddings.shape[1]}")
        print(f"  🏷️  Categories: {len(set(chunk['metadata']['category'] for chunk in knowledge_base['chunks']))}")
        print(f"  🔖 Unique tags: {len(set(tag for chunk in knowledge_base['chunks'] for tag in chunk['metadata']['tags']))}")
        
        return index_file, metadata_file

def main():
    generator = WhisEmbeddingGenerator()
    generator.generate_complete_vectorstore()

if __name__ == "__main__":
    main()