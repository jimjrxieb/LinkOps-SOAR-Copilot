#!/usr/bin/env python3
"""
🔍 RAG Retriever Engine
=======================
FAISS-based vector search for cybersecurity knowledge retrieval

[TAG: RAG-INTEGRATION] - Vector search implementation
[TAG: FAISS-SEARCH] - Semantic similarity retrieval
[TAG: CITATION-GENERATION] - Source attribution
"""

import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import logging

# FAISS and embeddings
try:
    import faiss
    from sentence_transformers import SentenceTransformer
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False

logger = logging.getLogger(__name__)

class RAGResult:
    """Single RAG retrieval result"""
    def __init__(self, content: str, title: str, source: str, score: float, chunk_id: str):
        self.content = content
        self.title = title
        self.source = source
        self.score = score
        self.chunk_id = chunk_id

class WHISRAGRetriever:
    """
    Production RAG retriever for WHIS cybersecurity knowledge
    
    [TAG: RAG-INTEGRATION] - Main retrieval engine
    """
    
    def __init__(self, pointers_file: str = "ai-training/rag/indices/pointers.json"):
        self.pointers_file = Path(pointers_file)
        self.index = None
        self.embeddings_model = None
        self.chunks = []
        self.metadata = {}
        self.loaded = False
        
        if RAG_AVAILABLE:
            self._load_index()
    
    def _load_index(self):
        """Load FAISS index and metadata"""
        try:
            # Load pointers
            if not self.pointers_file.exists():
                logger.warning(f"Pointers file not found: {self.pointers_file}")
                return False
            
            with open(self.pointers_file) as f:
                pointers = json.load(f)
            
            current_index = pointers.get("current_index")
            if not current_index:
                logger.error("No current index specified in pointers")
                return False
            
            index_info = pointers["indices"][current_index]
            
            # Load FAISS index
            faiss_path = Path(index_info["faiss_file"])
            if not faiss_path.exists():
                logger.error(f"FAISS index not found: {faiss_path}")
                return False
            
            self.index = faiss.read_index(str(faiss_path))
            logger.info(f"✅ Loaded FAISS index: {self.index.ntotal} vectors")
            
            # Load metadata
            metadata_path = Path(index_info["metadata_file"])
            if not metadata_path.exists():
                logger.error(f"Metadata file not found: {metadata_path}")
                return False
            
            with open(metadata_path) as f:
                metadata = json.load(f)
            
            self.chunks = metadata["chunks"]
            self.metadata = metadata["knowledge_base"]
            
            logger.info(f"✅ Loaded metadata: {len(self.chunks)} chunks")
            
            # Load embeddings model
            logger.info("🧮 Loading embeddings model...")
            self.embeddings_model = SentenceTransformer('all-MiniLM-L6-v2')
            
            self.loaded = True
            logger.info("✅ RAG retriever ready!")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load RAG index: {e}")
            return False
    
    def is_available(self) -> bool:
        """Check if RAG is available"""
        return RAG_AVAILABLE and self.loaded
    
    def search(self, query: str, k: int = 5, min_score: float = 0.3) -> List[RAGResult]:
        """
        Search for relevant cybersecurity knowledge
        
        [TAG: FAISS-SEARCH] - Vector similarity search
        """
        
        if not self.is_available():
            logger.warning("RAG not available")
            return []
        
        try:
            # Create query embedding
            query_embedding = self.embeddings_model.encode([query], convert_to_tensor=False)
            query_embedding = np.array(query_embedding).astype('float32')
            
            # Normalize for cosine similarity
            faiss.normalize_L2(query_embedding)
            
            # Search FAISS index
            scores, indices = self.index.search(query_embedding, k)
            
            results = []
            for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
                if idx == -1 or score < min_score:  # No match or low score
                    continue
                
                chunk = self.chunks[idx]
                result = RAGResult(
                    content=chunk["content"],
                    title=chunk["title"],
                    source=chunk["source"], 
                    score=float(score),
                    chunk_id=chunk["id"]
                )
                results.append(result)
            
            logger.info(f"RAG search for '{query[:50]}...': {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"RAG search failed: {e}")
            return []
    
    def get_answer_with_citations(self, query: str, k: int = 3) -> Tuple[str, List[str]]:
        """
        Get answer with proper citations for knowledge questions
        
        [TAG: CITATION-GENERATION] - Source attribution
        """
        
        results = self.search(query, k=k, min_score=0.4)
        
        if not results:
            return "", []
        
        # Use the best result for the answer
        best_result = results[0]
        
        # For definition-style questions, provide concise answer
        if any(word in query.lower() for word in ['what is', 'define', 'definition']):
            # Extract definition from content
            content_lines = best_result.content.split('\n')
            definition_line = ""
            
            for line in content_lines:
                if line.startswith('**Definition**:'):
                    definition_line = line.replace('**Definition**:', '').strip()
                    break
                elif 'definition' in line.lower() and ':' in line:
                    definition_line = line.split(':', 1)[1].strip()
                    break
            
            if definition_line:
                answer = definition_line
            else:
                # Fallback to first substantial paragraph
                for line in content_lines:
                    if len(line.strip()) > 50 and not line.startswith('#'):
                        answer = line.strip()
                        break
                else:
                    answer = best_result.content[:200].strip() + "..."
        else:
            # For other questions, provide more context
            answer = best_result.content[:300].strip()
            if len(best_result.content) > 300:
                answer += "..."
        
        # Generate citations
        citations = []
        for result in results[:3]:  # Top 3 sources
            if result.source == "core_glossary":
                citation = f"core_glossary/{result.chunk_id.replace('glossary_', '')}.md"
            elif result.source == "system_config":
                citation = "system_configuration.md"
            else:
                citation = f"{result.source} (HF dataset)"
            citations.append(citation)
        
        return answer, citations
    
    def get_config_answer(self, query: str) -> Tuple[str, List[str]]:
        """
        Answer configuration questions about WHIS system
        
        [TAG: CONFIG-LOOKUP] - System configuration queries
        """
        
        query_lower = query.lower()
        
        # System configuration mappings
        config_answers = {
            "siem": {
                "answer": "Configured SIEM: **Splunk**",
                "citation": "system_configuration.md:siem_system"
            },
            "edr": {
                "answer": "Configured EDR: **LimaCharlie**", 
                "citation": "system_configuration.md:edr_system"
            },
            "soar": {
                "answer": "SOAR Platform: **WHIS** (Workforce Hybrid Intelligence System)",
                "citation": "system_configuration.md:soar_platform"
            },
            "orchestration": {
                "answer": "Orchestration: **Slack Integration** with interactive workflows",
                "citation": "system_configuration.md:orchestration"
            },
            "testing": {
                "answer": "Testing Framework: **Playwright Automation** for security validation",
                "citation": "system_configuration.md:testing"
            }
        }
        
        # Match query to configuration
        if "siem" in query_lower:
            return config_answers["siem"]["answer"], [config_answers["siem"]["citation"]]
        elif "edr" in query_lower or "limacharlie" in query_lower:
            return config_answers["edr"]["answer"], [config_answers["edr"]["citation"]]
        elif "soar" in query_lower:
            return config_answers["soar"]["answer"], [config_answers["soar"]["citation"]]
        elif "orchestr" in query_lower or "slack" in query_lower:
            return config_answers["orchestration"]["answer"], [config_answers["orchestration"]["citation"]]
        elif "test" in query_lower or "playwright" in query_lower:
            return config_answers["testing"]["answer"], [config_answers["testing"]["citation"]]
        
        # Fallback to general RAG search
        return self.get_answer_with_citations(query)
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get RAG system health status"""
        return {
            "retriever_loaded": self.loaded,
            "backend": "faiss",
            "index_count": self.index.ntotal if self.index else 0,
            "chunk_count": len(self.chunks),
            "pointer_version": self.metadata.get("version", "unknown"),
            "last_indexed_at": self.metadata.get("created_at", "unknown"),
            "embeddings_model": "all-MiniLM-L6-v2" if self.embeddings_model else None
        }

# Global instance
_rag_retriever = None

def get_rag_retriever() -> WHISRAGRetriever:
    """Get global RAG retriever instance"""
    global _rag_retriever
    if _rag_retriever is None:
        _rag_retriever = WHISRAGRetriever()
    return _rag_retriever

if __name__ == "__main__":
    # Test the RAG retriever
    retriever = WHISRAGRetriever()
    
    if not retriever.is_available():
        print("❌ RAG not available")
        exit(1)
    
    print("✅ RAG retriever loaded successfully!")
    print(f"Health: {retriever.get_health_status()}")
    
    # Test queries
    test_queries = [
        "what is a siem",
        "what siem are we using",
        "what is cybersecurity",
        "define edr",
        "what is mitre attack"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Query: {query}")
        
        if "are we using" in query or "siem are" in query:
            answer, citations = retriever.get_config_answer(query)
        else:
            answer, citations = retriever.get_answer_with_citations(query)
        
        print(f"📝 Answer: {answer}")
        print(f"📚 Citations: {citations}")