"""
RAG Engine: Retrieval-Augmented Generation for Whis SOAR
Provides knowledge base retrieval for enhanced responses
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path
import json

logger = logging.getLogger(__name__)


@dataclass
class Document:
    """Document structure for RAG results"""
    content: str
    metadata: Dict[str, Any]
    score: float = 0.0


class RAGEngine:
    """
    RAG Engine for knowledge base retrieval
    Currently uses simple file-based knowledge base
    Can be extended to use vector databases like ChromaDB, Pinecone, etc.
    """
    
    def __init__(self):
        self.knowledge_base = {}
        self.loaded = False
        
        # Knowledge base paths
        self.knowledge_paths = [
            "/home/jimmie/linkops-industries/SOAR-copilot/ai-training/rag/chunks",
            "/home/jimmie/linkops-industries/SOAR-copilot/ai-training/rag/vectorstore"
        ]
    
    async def initialize(self):
        """Initialize the RAG engine"""
        if self.loaded:
            return True
            
        logger.info("🚀 Initializing RAG Engine...")
        
        try:
            # Load knowledge base
            await asyncio.get_event_loop().run_in_executor(
                None, self._load_knowledge_base
            )
            
            self.loaded = True
            logger.info(f"✅ RAG Engine initialized with {len(self.knowledge_base)} documents")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize RAG Engine: {e}")
            return False
    
    def _load_knowledge_base(self):
        """Load knowledge base from files"""
        documents_loaded = 0
        
        for kb_path in self.knowledge_paths:
            path = Path(kb_path)
            if not path.exists():
                logger.warning(f"⚠️ Knowledge base path not found: {kb_path}")
                continue
                
            # Load JSON files
            for json_file in path.glob("*.json"):
                try:
                    with open(json_file, 'r') as f:
                        data = json.load(f)
                        
                    if isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict) and 'content' in item:
                                doc_id = f"{json_file.stem}_{documents_loaded}"
                                self.knowledge_base[doc_id] = Document(
                                    content=item['content'],
                                    metadata={
                                        "source": str(json_file),
                                        "category": item.get('category', 'unknown'),
                                        "type": item.get('type', 'knowledge')
                                    }
                                )
                                documents_loaded += 1
                    
                    elif isinstance(data, dict):
                        doc_id = f"{json_file.stem}_0"
                        content = data.get('content', str(data))
                        self.knowledge_base[doc_id] = Document(
                            content=content,
                            metadata={
                                "source": str(json_file),
                                "category": data.get('category', 'unknown'),
                                "type": "knowledge"
                            }
                        )
                        documents_loaded += 1
                        
                except Exception as e:
                    logger.warning(f"⚠️ Failed to load {json_file}: {e}")
            
            # Load markdown files
            for md_file in path.glob("*.md"):
                try:
                    with open(md_file, 'r') as f:
                        content = f.read()
                    
                    doc_id = f"{md_file.stem}_md"
                    self.knowledge_base[doc_id] = Document(
                        content=content,
                        metadata={
                            "source": str(md_file),
                            "category": "playbook",
                            "type": "markdown"
                        }
                    )
                    documents_loaded += 1
                    
                except Exception as e:
                    logger.warning(f"⚠️ Failed to load {md_file}: {e}")
        
        # Add default SOAR knowledge if no files loaded
        if documents_loaded == 0:
            self._load_default_knowledge()
    
    def _load_default_knowledge(self):
        """Load default SOAR knowledge base"""
        default_docs = {
            "mitre_t1110": Document(
                content="T1110 Brute Force: Adversaries may use brute force techniques to gain access to accounts when passwords are unknown or when password hashes are obtained. Common indicators include multiple failed login attempts from same source, authentication logs showing repeated failures, unusual login times or locations.",
                metadata={"category": "attack_framework", "technique": "T1110", "type": "mitre_attack"}
            ),
            "mitre_t1078": Document(
                content="T1078 Valid Accounts: Adversaries may obtain and abuse credentials of existing accounts to gain unauthorized access. Look for account usage outside normal hours, geographic anomalies, privilege escalation attempts, and access to sensitive resources.",
                metadata={"category": "attack_framework", "technique": "T1078", "type": "mitre_attack"}
            ),
            "incident_response_playbook": Document(
                content="Incident Response Process: 1. Preparation - Establish IR team and procedures. 2. Identification - Detect and analyze potential incidents. 3. Containment - Limit damage and prevent further compromise. 4. Eradication - Remove threat from environment. 5. Recovery - Restore systems to normal operation. 6. Lessons Learned - Document and improve processes.",
                metadata={"category": "playbook", "type": "incident_response"}
            ),
            "nist_framework": Document(
                content="NIST Cybersecurity Framework: Identify (asset management, risk assessment), Protect (access control, data security), Detect (continuous monitoring, detection processes), Respond (response planning, incident analysis), Recover (recovery planning, business continuity).",
                metadata={"category": "framework", "type": "nist_csf"}
            )
        }
        
        self.knowledge_base.update(default_docs)
        logger.info(f"📚 Loaded {len(default_docs)} default knowledge documents")
    
    async def search_knowledge(
        self, 
        query: str, 
        namespace: Optional[str] = None, 
        limit: int = 5
    ) -> List[Document]:
        """
        Search knowledge base for relevant documents
        
        Args:
            query: Search query
            namespace: Optional namespace filter (e.g., "attack_framework")
            limit: Maximum number of results
            
        Returns:
            List of relevant documents
        """
        if not self.loaded:
            await self.initialize()
        
        # Simple text-based search (can be replaced with vector search)
        query_lower = query.lower()
        results = []
        
        for doc_id, doc in self.knowledge_base.items():
            # Filter by namespace if specified
            if namespace and doc.metadata.get('category') != namespace:
                continue
            
            # Simple relevance scoring based on keyword matches
            content_lower = doc.content.lower()
            score = 0
            
            # Score based on query terms in content
            query_terms = query_lower.split()
            for term in query_terms:
                if term in content_lower:
                    score += content_lower.count(term)
            
            # Bonus for metadata matches
            for key, value in doc.metadata.items():
                if isinstance(value, str) and query_lower in value.lower():
                    score += 2
            
            if score > 0:
                doc.score = score
                results.append(doc)
        
        # Sort by score and return top results
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:limit]
    
    async def retrieve(
        self, 
        query: str, 
        k: int = 5, 
        filters: Optional[Dict[str, List[str]]] = None
    ) -> Dict[str, Any]:
        """
        Retrieve relevant context for a query (compatible with main API)
        
        Args:
            query: Search query
            k: Number of chunks to retrieve
            filters: Optional filters (e.g., {"domain": ["nist_core", "siem_patterns"]})
            
        Returns:
            Dictionary with chunks and sources
        """
        # Apply domain filters if specified
        namespace = None
        if filters and "domain" in filters:
            domains = filters["domain"]
            if "nist_core" in domains:
                namespace = "framework"
            elif "attack_framework" in domains:
                namespace = "attack_framework"
        
        # Search knowledge base
        docs = await self.search_knowledge(query, namespace, k)
        
        # Format results
        chunks = []
        sources = []
        
        for doc in docs:
            chunks.append({
                "content": doc.content[:500] + "..." if len(doc.content) > 500 else doc.content,
                "metadata": doc.metadata,
                "score": doc.score
            })
            
            sources.append({
                "source": doc.metadata.get("source", "unknown"),
                "category": doc.metadata.get("category", "unknown"),
                "type": doc.metadata.get("type", "unknown")
            })
        
        return {
            "chunks": chunks,
            "sources": sources,
            "query": query,
            "total_results": len(docs)
        }
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get RAG engine health status"""
        return {
            "status": "healthy" if self.loaded else "not_ready",
            "documents_loaded": len(self.knowledge_base),
            "knowledge_paths": [str(p) for p in self.knowledge_paths],
            "categories": list(set(doc.metadata.get('category', 'unknown') 
                                 for doc in self.knowledge_base.values()))
        }


# Global instance
_rag_engine = None

async def get_rag_engine() -> RAGEngine:
    """Get or create global RAG engine instance"""
    global _rag_engine
    if _rag_engine is None:
        _rag_engine = RAGEngine()
        await _rag_engine.initialize()
    
    return _rag_engine


async def test_rag_engine():
    """Test function for the RAG engine"""
    print("🧪 Testing RAG Engine...")
    
    engine = await get_rag_engine()
    
    # Test search
    test_query = "brute force attack T1110 failed login"
    print(f"📝 Test query: {test_query}")
    
    results = await engine.search_knowledge(test_query, limit=3)
    
    print(f"🔍 Found {len(results)} results:")
    for i, doc in enumerate(results, 1):
        print(f"\n📄 Result {i} (score: {doc.score}):")
        print(f"Content: {doc.content[:200]}...")
        print(f"Metadata: {doc.metadata}")
    
    # Test retrieve (API compatible)
    retrieve_results = await engine.retrieve(
        query=test_query,
        k=2,
        filters={"domain": ["attack_framework"]}
    )
    
    print(f"\n📊 Retrieve results: {retrieve_results['total_results']} chunks")
    
    # Health check
    health = await engine.get_health_status()
    print("🏥 Health status:", json.dumps(health, indent=2))


if __name__ == "__main__":
    asyncio.run(test_rag_engine())