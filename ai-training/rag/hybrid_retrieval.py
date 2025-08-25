#!/usr/bin/env python3
"""
🔍 Hybrid Retrieval System
==========================
Vector + BM25 + repo structure bias with dual embedders.

Senior-level retrieval:
- Dual embedders (code-tuned + general prose)
- BM25 for exact keyword matching
- Repository structure bias (prefer same package/module) 
- Cross-encoder reranking
- Query routing (code vs docs)
- Citation tracking with file path + commit hash
"""

import os
import json
import pickle
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
import re

import numpy as np
from dataclasses import dataclass, asdict
from sentence_transformers import SentenceTransformer, CrossEncoder

# BM25 implementation
try:
    from rank_bm25 import BM25Okapi
    BM25_AVAILABLE = True
except ImportError:
    print("⚠️  BM25 not available. Install with: pip install rank-bm25")
    BM25_AVAILABLE = False

import chromadb
from chromadb.config import Settings


@dataclass 
class RetrievalResult:
    """Structured retrieval result with citations"""
    content: str
    file_path: str
    symbol_name: str
    symbol_type: str
    start_line: int
    end_line: int
    language: str
    commit_hash: str
    module_path: str
    chunk_type: str
    
    # Retrieval metadata
    vector_score: float
    bm25_score: float
    rerank_score: float
    final_score: float
    retrieval_method: str  # vector, bm25, hybrid
    
    def to_citation(self) -> Dict[str, Any]:
        """Convert to citation format"""
        return {
            "file_path": self.file_path,
            "symbol_name": self.symbol_name,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "commit_hash": self.commit_hash,
            "url": f"https://github.com/repo/blob/{self.commit_hash}/{self.file_path}#L{self.start_line}-L{self.end_line}"
        }


class DualEmbedder:
    """Dual embedding system: code-tuned + general prose"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # Code embedder (optimized for code similarity)
        print("🔧 Loading code embedder...")
        self.code_embedder = SentenceTransformer(config["code_embedder"]["model"])
        
        # Prose embedder (general text)
        print("🔧 Loading prose embedder...")
        self.prose_embedder = SentenceTransformer(config["prose_embedder"]["model"])
        
        # Cross-encoder for reranking
        if config["reranking"]["enabled"]:
            print("🔧 Loading cross-encoder for reranking...")
            self.cross_encoder = CrossEncoder(config["reranking"]["model"])
        else:
            self.cross_encoder = None
            
    def embed_chunk(self, chunk: Dict[str, Any]) -> Dict[str, np.ndarray]:
        """Embed chunk with appropriate embedder"""
        content = chunk["content"]
        chunk_type = chunk.get("chunk_type", "code")
        language = chunk.get("language", "text")
        
        embeddings = {}
        
        # Choose embedder based on content type
        if chunk_type == "code" and language in ["python", "javascript", "typescript", "go", "java", "cpp"]:
            # Use code-tuned embedder
            embeddings["code"] = self.code_embedder.encode(content, normalize_embeddings=True)
        else:
            # Use general embedder for docs, configs, etc.
            embeddings["prose"] = self.prose_embedder.encode(content, normalize_embeddings=True)
            
        return embeddings
        
    def embed_query(self, query: str, query_type: str = "auto") -> Dict[str, np.ndarray]:
        """Embed query with appropriate embedder"""
        embeddings = {}
        
        if query_type == "code" or self._looks_like_code_query(query):
            # Code query
            embeddings["code"] = self.code_embedder.encode(query, normalize_embeddings=True)
        else:
            # General query
            embeddings["prose"] = self.prose_embedder.encode(query, normalize_embeddings=True)
            
        return embeddings
        
    def _looks_like_code_query(self, query: str) -> bool:
        """Heuristic to detect code-related queries"""
        code_indicators = [
            "function", "class", "method", "variable", "import", "defined",
            "implementation", "where is", "how is", "def ", "class ", "import ",
            "function(", "method(", ".py", ".js", ".go", "API", "endpoint"
        ]
        
        query_lower = query.lower()
        return any(indicator in query_lower for indicator in code_indicators)
        
    def rerank(self, query: str, results: List[RetrievalResult], top_k: int = 10) -> List[RetrievalResult]:
        """Rerank results using cross-encoder"""
        if not self.cross_encoder or len(results) <= 1:
            return results[:top_k]
            
        # Prepare query-document pairs
        pairs = [(query, result.content) for result in results]
        
        # Get reranking scores
        rerank_scores = self.cross_encoder.predict(pairs)
        
        # Update results with rerank scores
        for result, score in zip(results, rerank_scores):
            result.rerank_score = float(score)
            
        # Sort by rerank score
        reranked = sorted(results, key=lambda x: x.rerank_score, reverse=True)
        return reranked[:top_k]


class QueryRouter:
    """Route queries to appropriate indexes and retrieval methods"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
    def route_query(self, query: str) -> Dict[str, Any]:
        """Determine query type and routing strategy"""
        query_lower = query.lower()
        
        # Code-specific patterns
        if any(pattern in query_lower for pattern in [
            "where is", "how is", "defined", "implementation", "function", "class",
            "method", "api", "endpoint", ".py", ".js", ".go", "import"
        ]):
            return {
                "query_type": "code",
                "indexes": ["code"],
                "retrieval_methods": ["vector", "bm25"],
                "boost_same_module": True,
                "prefer_symbols": True
            }
            
        # Documentation patterns
        elif any(pattern in query_lower for pattern in [
            "how to", "what is", "explain", "guide", "tutorial", "documentation",
            "readme", "architecture", "design", "overview"
        ]):
            return {
                "query_type": "docs", 
                "indexes": ["docs", "config"],
                "retrieval_methods": ["vector"],
                "boost_same_module": False,
                "prefer_symbols": False
            }
            
        # Configuration/deployment patterns
        elif any(pattern in query_lower for pattern in [
            "deploy", "config", "environment", "setup", "install", "run",
            "docker", "kubernetes", "ci/cd", "pipeline"
        ]):
            return {
                "query_type": "config",
                "indexes": ["config", "ci", "docs"],
                "retrieval_methods": ["vector", "bm25"],
                "boost_same_module": False,
                "prefer_symbols": False
            }
            
        # Default to hybrid search
        else:
            return {
                "query_type": "hybrid",
                "indexes": ["code", "docs", "config"],
                "retrieval_methods": ["vector", "bm25"],
                "boost_same_module": False,
                "prefer_symbols": False
            }


class HybridRetriever:
    """Hybrid retrieval system with multiple strategies"""
    
    def __init__(self, config_path: str = "ai-training/configs/hybrid_retrieval.yaml"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        
        # Initialize components
        self.dual_embedder = DualEmbedder(self.config["embedders"])
        self.query_router = QueryRouter(self.config["routing"])
        
        # Initialize vector stores
        self.vector_stores = {}
        self._init_vector_stores()
        
        # Initialize BM25 indexes
        self.bm25_indexes = {}
        self.documents = {}  # Store documents for BM25
        if BM25_AVAILABLE:
            self._init_bm25_indexes()
            
    def _load_config(self) -> Dict[str, Any]:
        """Load hybrid retrieval configuration"""
        if not self.config_path.exists():
            default_config = {
                "embedders": {
                    "code_embedder": {
                        "model": "microsoft/codebert-base",  # Code-tuned embedder
                        "device": "auto"
                    },
                    "prose_embedder": {
                        "model": "sentence-transformers/all-MiniLM-L6-v2",  # General embedder
                        "device": "auto"
                    },
                    "reranking": {
                        "enabled": True,
                        "model": "cross-encoder/ms-marco-MiniLM-L-6-v2",
                        "top_k_rerank": 20
                    }
                },
                "vector_stores": {
                    "chroma_path": "ai-training/rag/hybrid_index",
                    "collections": {
                        "code": "whis_code_index",
                        "docs": "whis_docs_index", 
                        "config": "whis_config_index",
                        "schema": "whis_schema_index"
                    }
                },
                "retrieval": {
                    "vector_weight": 0.7,
                    "bm25_weight": 0.3,
                    "top_k_vector": 20,
                    "top_k_bm25": 20,
                    "top_k_final": 10,
                    "score_threshold": 0.5,
                    "same_module_boost": 1.2,
                    "same_file_boost": 1.5
                },
                "routing": {
                    "enable_routing": True,
                    "fallback_to_all": True
                }
            }
            
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            import yaml
            with open(self.config_path, 'w') as f:
                yaml.dump(default_config, f, indent=2)
                
            return default_config
            
        import yaml
        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)
            
    def _init_vector_stores(self):
        """Initialize ChromaDB vector stores for each index type"""
        chroma_path = Path(self.config["vector_stores"]["chroma_path"])
        chroma_path.mkdir(parents=True, exist_ok=True)
        
        client = chromadb.PersistentClient(
            path=str(chroma_path),
            settings=Settings(anonymized_telemetry=False)
        )
        
        collections = self.config["vector_stores"]["collections"]
        
        for index_type, collection_name in collections.items():
            try:
                collection = client.get_collection(collection_name)
                print(f"📚 Using existing collection: {collection_name}")
            except:
                collection = client.create_collection(collection_name)
                print(f"📚 Created new collection: {collection_name}")
                
            self.vector_stores[index_type] = collection
            
    def _init_bm25_indexes(self):
        """Initialize BM25 indexes from existing vector stores"""
        print("🔧 Initializing BM25 indexes...")
        
        for index_type, collection in self.vector_stores.items():
            try:
                # Get all documents from collection
                results = collection.get(include=["documents", "metadatas"])
                
                if results["documents"]:
                    # Tokenize documents for BM25
                    tokenized_docs = []
                    documents = []
                    
                    for doc, metadata in zip(results["documents"], results["metadatas"]):
                        # Simple tokenization
                        tokens = doc.lower().split()
                        tokenized_docs.append(tokens)
                        documents.append({
                            "content": doc,
                            "metadata": metadata
                        })
                        
                    # Create BM25 index
                    bm25 = BM25Okapi(tokenized_docs)
                    self.bm25_indexes[index_type] = bm25
                    self.documents[index_type] = documents
                    
                    print(f"📊 BM25 index for {index_type}: {len(documents)} documents")
                    
            except Exception as e:
                print(f"⚠️  Failed to initialize BM25 for {index_type}: {e}")
                
    def vector_search(self, query: str, query_embeddings: Dict[str, np.ndarray], 
                     index_types: List[str], top_k: int) -> List[RetrievalResult]:
        """Perform vector similarity search"""
        results = []
        
        for index_type in index_types:
            if index_type not in self.vector_stores:
                continue
                
            collection = self.vector_stores[index_type]
            
            # Choose appropriate embedding
            if index_type == "code" and "code" in query_embeddings:
                query_embedding = query_embeddings["code"]
            elif "prose" in query_embeddings:
                query_embedding = query_embeddings["prose"]
            else:
                continue
                
            try:
                # Search collection
                search_results = collection.query(
                    query_embeddings=[query_embedding.tolist()],
                    n_results=top_k,
                    include=["documents", "metadatas", "distances"]
                )
                
                # Convert to RetrievalResult objects
                for i, (doc, metadata, distance) in enumerate(zip(
                    search_results["documents"][0],
                    search_results["metadatas"][0], 
                    search_results["distances"][0]
                )):
                    result = RetrievalResult(
                        content=doc,
                        file_path=metadata.get("file_path", ""),
                        symbol_name=metadata.get("symbol_name", ""),
                        symbol_type=metadata.get("symbol_type", ""),
                        start_line=metadata.get("start_line", 0),
                        end_line=metadata.get("end_line", 0),
                        language=metadata.get("language", ""),
                        commit_hash=metadata.get("commit_hash", ""),
                        module_path=metadata.get("module_path", ""),
                        chunk_type=metadata.get("chunk_type", ""),
                        vector_score=1.0 - distance,  # Convert distance to similarity
                        bm25_score=0.0,
                        rerank_score=0.0,
                        final_score=1.0 - distance,
                        retrieval_method="vector"
                    )
                    results.append(result)
                    
            except Exception as e:
                print(f"⚠️  Vector search failed for {index_type}: {e}")
                
        return results
        
    def bm25_search(self, query: str, index_types: List[str], top_k: int) -> List[RetrievalResult]:
        """Perform BM25 keyword search"""
        if not BM25_AVAILABLE:
            return []
            
        results = []
        query_tokens = query.lower().split()
        
        for index_type in index_types:
            if index_type not in self.bm25_indexes:
                continue
                
            bm25 = self.bm25_indexes[index_type]
            documents = self.documents[index_type]
            
            try:
                # Get BM25 scores
                scores = bm25.get_scores(query_tokens)
                
                # Get top-k results
                top_indices = np.argsort(scores)[-top_k:][::-1]
                
                for idx in top_indices:
                    if scores[idx] > 0:  # Only include positive scores
                        doc = documents[idx]
                        metadata = doc["metadata"]
                        
                        result = RetrievalResult(
                            content=doc["content"],
                            file_path=metadata.get("file_path", ""),
                            symbol_name=metadata.get("symbol_name", ""),
                            symbol_type=metadata.get("symbol_type", ""),
                            start_line=metadata.get("start_line", 0),
                            end_line=metadata.get("end_line", 0),
                            language=metadata.get("language", ""),
                            commit_hash=metadata.get("commit_hash", ""),
                            module_path=metadata.get("module_path", ""),
                            chunk_type=metadata.get("chunk_type", ""),
                            vector_score=0.0,
                            bm25_score=float(scores[idx]),
                            rerank_score=0.0,
                            final_score=float(scores[idx]),
                            retrieval_method="bm25"
                        )
                        results.append(result)
                        
            except Exception as e:
                print(f"⚠️  BM25 search failed for {index_type}: {e}")
                
        return results
        
    def apply_repo_bias(self, results: List[RetrievalResult], 
                       query_context: Optional[str] = None) -> List[RetrievalResult]:
        """Apply repository structure bias to boost related modules"""
        if not query_context:
            return results
            
        # Extract module from context (simplified)
        context_module = ""
        if query_context:
            # Would implement proper module extraction
            pass
            
        boosted_results = []
        
        for result in results:
            boost_factor = 1.0
            
            # Same module boost
            if result.module_path and context_module:
                if result.module_path.startswith(context_module):
                    boost_factor *= self.config["retrieval"]["same_module_boost"]
                    
            # Same file boost
            if query_context and result.file_path in query_context:
                boost_factor *= self.config["retrieval"]["same_file_boost"]
                
            # Apply boost
            result.final_score *= boost_factor
            boosted_results.append(result)
            
        return boosted_results
        
    def hybrid_search(self, query: str, context: Optional[str] = None, 
                     top_k: int = 10) -> List[RetrievalResult]:
        """Perform hybrid search with routing, vector, BM25, and reranking"""
        
        # Route query
        routing = self.query_router.route_query(query)
        print(f"🧭 Query routed as: {routing['query_type']}")
        
        # Get query embeddings
        query_embeddings = self.dual_embedder.embed_query(query, routing["query_type"])
        
        # Get retrieval config
        retrieval_config = self.config["retrieval"]
        vector_weight = retrieval_config["vector_weight"]
        bm25_weight = retrieval_config["bm25_weight"]
        
        all_results = []
        
        # Vector search
        if "vector" in routing["retrieval_methods"]:
            vector_results = self.vector_search(
                query, query_embeddings, routing["indexes"], 
                retrieval_config["top_k_vector"]
            )
            all_results.extend(vector_results)
            
        # BM25 search
        if "bm25" in routing["retrieval_methods"] and BM25_AVAILABLE:
            bm25_results = self.bm25_search(
                query, routing["indexes"], 
                retrieval_config["top_k_bm25"]
            )
            all_results.extend(bm25_results)
            
        # Combine and deduplicate results
        combined_results = self._combine_results(all_results, vector_weight, bm25_weight)
        
        # Apply repository structure bias
        if routing["boost_same_module"]:
            combined_results = self.apply_repo_bias(combined_results, context)
            
        # Rerank results
        if self.dual_embedder.cross_encoder:
            rerank_top_k = min(self.config["embedders"]["reranking"]["top_k_rerank"], len(combined_results))
            combined_results = self.dual_embedder.rerank(query, combined_results[:rerank_top_k])
            
        # Apply score threshold and return top-k
        filtered_results = [
            r for r in combined_results 
            if r.final_score >= retrieval_config["score_threshold"]
        ]
        
        return filtered_results[:top_k]
        
    def _combine_results(self, results: List[RetrievalResult], 
                        vector_weight: float, bm25_weight: float) -> List[RetrievalResult]:
        """Combine vector and BM25 results with weighted scores"""
        # Group results by content/file_path for deduplication
        result_map = {}
        
        for result in results:
            key = f"{result.file_path}:{result.start_line}:{result.end_line}"
            
            if key in result_map:
                # Merge scores
                existing = result_map[key]
                existing.vector_score = max(existing.vector_score, result.vector_score)
                existing.bm25_score = max(existing.bm25_score, result.bm25_score)
                
                # Update retrieval method
                if existing.retrieval_method != result.retrieval_method:
                    existing.retrieval_method = "hybrid"
            else:
                result_map[key] = result
                
        # Calculate final scores
        for result in result_map.values():
            result.final_score = (
                result.vector_score * vector_weight + 
                result.bm25_score * bm25_weight
            )
            
        # Sort by final score
        return sorted(result_map.values(), key=lambda x: x.final_score, reverse=True)
        
    def get_citations(self, results: List[RetrievalResult]) -> List[Dict[str, Any]]:
        """Extract citations from results"""
        return [result.to_citation() for result in results]


def main():
    """CLI for hybrid retrieval testing"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Hybrid retrieval system")
    parser.add_argument("--config", default="ai-training/configs/hybrid_retrieval.yaml")
    parser.add_argument("--query", required=True, help="Search query")
    parser.add_argument("--top-k", type=int, default=10, help="Number of results")
    parser.add_argument("--context", help="Query context for repo bias")
    
    args = parser.parse_args()
    
    # Initialize retriever
    retriever = HybridRetriever(args.config)
    
    # Perform search
    results = retriever.hybrid_search(args.query, args.context, args.top_k)
    
    # Display results
    print(f"\n🔍 Search results for: '{args.query}'")
    print(f"📊 Found {len(results)} results")
    print("=" * 80)
    
    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result.symbol_name} ({result.symbol_type})")
        print(f"   📁 {result.file_path}:{result.start_line}-{result.end_line}")
        print(f"   🏷️  {result.language} | {result.chunk_type} | {result.retrieval_method}")
        print(f"   📊 Vector: {result.vector_score:.3f} | BM25: {result.bm25_score:.3f} | Final: {result.final_score:.3f}")
        print(f"   📝 {result.content[:200]}...")
        
        citation = result.to_citation()
        print(f"   🔗 Citation: {citation['url']}")
        
    # Show citations
    citations = retriever.get_citations(results)
    print(f"\n📚 Citations ({len(citations)}):")
    for citation in citations:
        print(f"  - {citation['file_path']}:{citation['start_line']} ({citation['symbol_name']})")


if __name__ == "__main__":
    main()