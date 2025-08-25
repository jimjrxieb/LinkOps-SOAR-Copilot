#!/usr/bin/env python3
"""
📚 RAG Pipeline (SEPARATED from Fine-tuning) 
===========================================
Embeds documents into vector store for retrieval at inference time.
RAG does NOT change model weights - it augments prompts with retrieved context.

Mentor corrections applied:
- Separated from fine-tuning pipeline  
- Proper terminology (embed vs vectorize)
- Security guardrails for prompt injection
- RAGAS evaluation integration
"""

import os
import yaml
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from langchain.text_splitter import RecursiveCharacterTextSplitter
import mlflow
import mlflow.sklearn


class WhisRAGPipeline:
    """RAG pipeline for Whis knowledge base"""
    
    def __init__(self, config_path: str = "configs/rag.yaml"):
        """Initialize RAG pipeline with configuration"""
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.client = None
        self.collection = None
        self.embedder = None
        self.text_splitter = None
        
    def _load_config(self) -> Dict[str, Any]:
        """Load RAG configuration with validation"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"RAG config not found: {self.config_path}")
            
        with open(self.config_path, 'r') as f:
            config = yaml.safe_load(f)
            
        return config
        
    def initialize(self) -> None:
        """Initialize RAG components"""
        print("🚀 Initializing RAG pipeline...")
        
        # Setup experiment tracking
        mlflow.set_experiment("whis_rag_embedding")
        mlflow.start_run(run_name=f"rag_embed_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        
        # Log configuration
        mlflow.log_params({
            "embedding_model": self.config["retriever"]["model"],
            "chunk_size": self.config["chunking"]["chunk_size"], 
            "chunk_overlap": self.config["chunking"]["chunk_overlap"],
            "top_k": self.config["retrieval"]["top_k"],
            "score_threshold": self.config["retrieval"]["score_threshold"]
        })
        
        # Initialize embedding model
        print(f"📦 Loading embedding model: {self.config['retriever']['model']}")
        self.embedder = SentenceTransformer(
            self.config["retriever"]["model"],
            device=self.config["retriever"]["device"]
        )
        
        # Initialize text splitter
        chunking_config = self.config["chunking"]
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunking_config["chunk_size"],
            chunk_overlap=chunking_config["chunk_overlap"], 
            separators=chunking_config["separators"]
        )
        
        # Initialize ChromaDB
        vector_config = self.config["vector_store"]
        persist_dir = Path(vector_config["persist_directory"])
        persist_dir.mkdir(parents=True, exist_ok=True)
        
        self.client = chromadb.PersistentClient(
            path=str(persist_dir),
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Get or create collection
        try:
            self.collection = self.client.get_collection(vector_config["collection_name"])
            print(f"📚 Using existing collection: {vector_config['collection_name']}")
        except:
            self.collection = self.client.create_collection(vector_config["collection_name"])
            print(f"📚 Created new collection: {vector_config['collection_name']}")
            
        print("✅ RAG pipeline initialized")
        
    def _sanitize_content(self, content: str) -> str:
        """Sanitize content to prevent prompt injection"""
        security_config = self.config["security"]
        
        # Filter forbidden patterns
        for pattern in security_config["forbidden_patterns"]:
            content = content.replace(pattern, "[FILTERED]")
            
        # Limit content length  
        if len(content) > security_config["max_query_length"] * 2:  # Allow 2x for chunks
            content = content[:security_config["max_query_length"] * 2] + "...[TRUNCATED]"
            
        return content
        
    def chunk_documents(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Chunk documents into smaller pieces for embedding"""
        print(f"✂️  Chunking {len(documents)} documents...")
        
        chunks = []
        
        for doc_id, doc in enumerate(documents):
            content = doc.get("content", doc.get("text", ""))
            if not content:
                print(f"⚠️  Warning: Empty content in document {doc_id}")
                continue
                
            # Sanitize content
            content = self._sanitize_content(content)
            
            # Split into chunks
            doc_chunks = self.text_splitter.split_text(content)
            
            for chunk_id, chunk_text in enumerate(doc_chunks):
                chunk_metadata = {
                    "document_id": doc.get("id", str(doc_id)),
                    "chunk_id": f"{doc_id}_{chunk_id}",
                    "source": doc.get("source", "unknown"),
                    "title": doc.get("title", ""),
                    "category": doc.get("category", "general"),
                    "chunk_index": chunk_id,
                    "total_chunks": len(doc_chunks),
                    "created_at": datetime.now().isoformat()
                }
                
                chunks.append({
                    "id": chunk_metadata["chunk_id"],
                    "text": chunk_text,
                    "metadata": chunk_metadata
                })
                
        print(f"✅ Created {len(chunks)} chunks from {len(documents)} documents")
        
        # Log chunking stats
        mlflow.log_metrics({
            "input_documents": len(documents),
            "output_chunks": len(chunks),
            "avg_chunks_per_doc": len(chunks) / len(documents) if documents else 0
        })
        
        return chunks
        
    def embed_chunks(self, chunks: List[Dict[str, Any]]) -> None:
        """Embed chunks and store in vector database"""
        print(f"🧮 Embedding {len(chunks)} chunks...")
        
        if not chunks:
            print("⚠️  No chunks to embed")
            return
            
        # Extract texts for embedding
        texts = [chunk["text"] for chunk in chunks]
        
        # Generate embeddings in batches
        embedding_config = self.config["embedding"]
        batch_size = embedding_config["batch_size"]
        
        all_embeddings = []
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            
            batch_embeddings = self.embedder.encode(
                batch_texts,
                normalize_embeddings=embedding_config["normalize_embeddings"],
                show_progress_bar=embedding_config["show_progress"]
            )
            
            all_embeddings.extend(batch_embeddings.tolist())
            
        # Prepare data for ChromaDB
        ids = [chunk["id"] for chunk in chunks]
        documents = [chunk["text"] for chunk in chunks]
        metadatas = [chunk["metadata"] for chunk in chunks]
        
        # Store in vector database
        self.collection.add(
            ids=ids,
            documents=documents,
            embeddings=all_embeddings,
            metadatas=metadatas
        )
        
        print(f"✅ Embedded and stored {len(chunks)} chunks")
        
        # Log embedding stats
        mlflow.log_metrics({
            "chunks_embedded": len(chunks),
            "embedding_dimension": len(all_embeddings[0]) if all_embeddings else 0,
            "collection_size": self.collection.count()
        })
        
    def build_index(self, data_directory: str) -> str:
        """Build vector index from documents directory"""
        print(f"🏗️  Building index from: {data_directory}")
        
        data_path = Path(data_directory)
        if not data_path.exists():
            raise FileNotFoundError(f"Data directory not found: {data_directory}")
            
        # Load documents from various formats
        documents = []
        
        # Load JSON/JSONL files
        for json_file in data_path.rglob("*.json"):
            with open(json_file, 'r') as f:
                try:
                    data = json.load(f)
                    if isinstance(data, list):
                        documents.extend(data)
                    else:
                        documents.append(data)
                except json.JSONDecodeError as e:
                    print(f"⚠️  Error loading {json_file}: {e}")
                    
        for jsonl_file in data_path.rglob("*.jsonl"):
            with open(jsonl_file, 'r') as f:
                for line_no, line in enumerate(f, 1):
                    try:
                        if line.strip():
                            documents.append(json.loads(line))
                    except json.JSONDecodeError as e:
                        print(f"⚠️  Error in {jsonl_file}:{line_no}: {e}")
                        
        # Load Markdown files
        for md_file in data_path.rglob("*.md"):
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
                documents.append({
                    "id": md_file.stem,
                    "content": content,
                    "source": str(md_file),
                    "title": md_file.stem,
                    "category": "documentation"
                })
                
        print(f"📚 Loaded {len(documents)} documents")
        
        # Chunk documents
        chunks = self.chunk_documents(documents)
        
        # Embed and store
        self.embed_chunks(chunks)
        
        # Save index metadata
        index_metadata = {
            "created_at": datetime.now().isoformat(),
            "total_documents": len(documents),
            "total_chunks": len(chunks),
            "collection_name": self.config["vector_store"]["collection_name"],
            "embedding_model": self.config["retriever"]["model"],
            "config_hash": self._get_config_hash()
        }
        
        metadata_path = Path(self.config["vector_store"]["persist_directory"]) / "index_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(index_metadata, f, indent=2)
            
        # Log final artifacts
        mlflow.log_artifacts(str(metadata_path.parent), "index")
        
        print(f"✅ Index built successfully: {len(chunks)} chunks indexed")
        return str(metadata_path)
        
    def query(self, query_text: str, top_k: Optional[int] = None) -> List[Dict[str, Any]]:
        """Query the vector index for relevant chunks"""
        if not self.collection:
            raise RuntimeError("RAG pipeline not initialized. Call initialize() first.")
            
        # Use config default if not specified
        if top_k is None:
            top_k = self.config["retrieval"]["top_k"]
            
        # Security: Sanitize query
        query_text = self._sanitize_content(query_text)
        
        # Limit query length
        max_query_len = self.config["security"]["max_query_length"]
        if len(query_text) > max_query_len:
            query_text = query_text[:max_query_len]
            print(f"⚠️  Query truncated to {max_query_len} characters")
            
        # Generate query embedding
        query_embedding = self.embedder.encode([query_text])[0].tolist()
        
        # Search vector database
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
        
        # Format results
        formatted_results = []
        if results["ids"] and results["ids"][0]:
            for i in range(len(results["ids"][0])):
                result = {
                    "id": results["ids"][0][i],
                    "text": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i] if results.get("distances") else None
                }
                
                # Apply score threshold
                score_threshold = self.config["retrieval"]["score_threshold"]
                if result["distance"] is None or result["distance"] <= score_threshold:
                    formatted_results.append(result)
                    
        return formatted_results
        
    def _get_config_hash(self) -> str:
        """Get configuration hash for versioning"""
        config_str = yaml.dump(self.config, sort_keys=True)
        return hashlib.sha256(config_str.encode()).hexdigest()[:8]


def main():
    """Main RAG pipeline execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Build Whis RAG index")
    parser.add_argument("--config", default="configs/rag.yaml", help="RAG config file")
    parser.add_argument("--data-dir", required=True, help="Documents directory")
    parser.add_argument("--query", help="Test query after building index")
    
    args = parser.parse_args()
    
    # Initialize pipeline
    pipeline = WhisRAGPipeline(args.config)
    pipeline.initialize()
    
    try:
        # Build index
        metadata_path = pipeline.build_index(args.data_dir)
        print(f"📋 Index metadata: {metadata_path}")
        
        # Test query if provided
        if args.query:
            print(f"\n🔍 Testing query: {args.query}")
            results = pipeline.query(args.query)
            
            print(f"📊 Retrieved {len(results)} chunks:")
            for i, result in enumerate(results, 1):
                print(f"\n  {i}. {result['text'][:100]}...")
                print(f"     Source: {result['metadata'].get('source', 'unknown')}")
                print(f"     Distance: {result.get('distance', 'N/A')}")
                
        print("\n🎉 RAG pipeline completed successfully!")
        
    finally:
        # End MLflow run
        mlflow.end_run()


if __name__ == "__main__":
    main()