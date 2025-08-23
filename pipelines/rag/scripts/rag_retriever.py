#!/usr/bin/env python3
"""
RAG Retrieval System for Whis
Provides semantic search and context retrieval from vectorized knowledge base
"""

import json
import numpy as np
import pickle
from pathlib import Path
from typing import List, Dict, Any, Tuple
from sentence_transformers import SentenceTransformer
import faiss

class WhisRAGRetriever:
    def __init__(self, vector_dir="knowledge/vectors"):
        self.vector_dir = Path(vector_dir)
        self.model = None
        self.faiss_index = None
        self.metadata = None
        self.knowledge_base = None
        self.loaded = False
        
    def load_vector_store(self):
        """Load the vectorized knowledge base"""
        print("📦 Loading Whis RAG vector store...")
        
        # Load manifest
        manifest_path = self.vector_dir / "vector_store_manifest.json"
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        print(f"  📄 Manifest: {manifest['entries']} entries, {manifest['embedding_dimension']}D")
        
        # Load sentence transformer model
        model_name = manifest['model']
        self.model = SentenceTransformer(model_name)
        print(f"  🤖 Model: {model_name}")
        
        # Load FAISS index
        faiss_path = self.vector_dir / "whis_rag.faiss"
        self.faiss_index = faiss.read_index(str(faiss_path))
        print(f"  🔍 FAISS Index: {self.faiss_index.ntotal} entries")
        
        # Load metadata
        metadata_path = self.vector_dir / "metadata.pkl"
        with open(metadata_path, 'rb') as f:
            self.metadata = pickle.load(f)
        print(f"  📊 Metadata: {len(self.metadata)} entries")
        
        # Load knowledge base
        kb_path = self.vector_dir / "knowledge_base.json"
        with open(kb_path, 'r') as f:
            self.knowledge_base = json.load(f)
        print(f"  📚 Knowledge Base: {len(self.knowledge_base)} entries")
        
        self.loaded = True
        print("✅ RAG vector store loaded successfully!")
        return manifest
        
    def search(self, query: str, k: int = 5, threshold: float = 1.5) -> List[Dict[str, Any]]:
        """
        Search for relevant knowledge entries
        
        Args:
            query: Search query
            k: Number of results to return
            threshold: Distance threshold (lower = more similar)
            
        Returns:
            List of relevant knowledge entries with scores
        """
        if not self.loaded:
            self.load_vector_store()
            
        # Embed the query
        query_embedding = self.model.encode([query])
        
        # Search in FAISS index
        distances, indices = self.faiss_index.search(query_embedding.astype(np.float32), k)
        
        # Format results
        results = []
        for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
            if distance <= threshold:  # Filter by threshold
                entry = self.metadata[idx]['original_entry']
                result = {
                    'rank': i + 1,
                    'score': float(1.0 / (1.0 + distance)),  # Convert distance to similarity score
                    'distance': float(distance),
                    'entry': entry,
                    'metadata': {
                        'id': self.metadata[idx]['id'],
                        'source': self.metadata[idx].get('source', 'unknown'),
                        'domain': self.metadata[idx].get('domain', 'cybersecurity')
                    }
                }
                results.append(result)
        
        return results
        
    def get_context(self, query: str, max_entries: int = 3) -> str:
        """
        Get formatted context for RAG generation
        
        Args:
            query: Search query
            max_entries: Maximum context entries to include
            
        Returns:
            Formatted context string
        """
        results = self.search(query, k=max_entries * 2, threshold=1.2)[:max_entries]
        
        if not results:
            return "No relevant cybersecurity knowledge found."
            
        context_parts = []
        context_parts.append(f"🔍 Found {len(results)} relevant knowledge entries:")
        
        for result in results:
            entry = result['entry']
            score = result['score']
            
            context_parts.append(f"\n📋 **Context {result['rank']}** (Relevance: {score:.3f})")
            
            # Add query/question
            if isinstance(entry, dict):
                if 'query' in entry:
                    context_parts.append(f"**Query:** {entry['query']}")
                elif 'question' in entry:
                    context_parts.append(f"**Query:** {entry['question']}")
                
                # Add context if available
                if 'context' in entry and entry['context']:
                    context_parts.append(f"**Context:** {entry['context'][:300]}...")
                
                # Add response/answer
                if 'expected_response' in entry:
                    context_parts.append(f"**Response:** {entry['expected_response'][:500]}...")
                elif 'answer' in entry:
                    context_parts.append(f"**Response:** {entry['answer'][:500]}...")
                elif 'response' in entry:
                    context_parts.append(f"**Response:** {entry['response'][:500]}...")
            else:
                context_parts.append(f"**Content:** {str(entry)[:500]}...")
                
            context_parts.append("---")
        
        return "\n".join(context_parts)
        
    def generate_rag_prompt(self, user_query: str, mode: str = "assistant") -> str:
        """
        Generate a RAG-enhanced prompt for the LLM
        
        Args:
            user_query: User's question/request
            mode: "teacher" or "assistant" mode
            
        Returns:
            Complete prompt with context
        """
        context = self.get_context(user_query, max_entries=3)
        
        if mode.lower() == "teacher":
            system_prompt = """You are Whis, a cybersecurity education expert. Provide detailed, educational explanations with:
- Clear technical concepts
- MITRE ATT&CK references where relevant
- Step-by-step detection strategies
- Learning-focused content
- Professional tone suitable for training"""
        else:  # assistant mode
            system_prompt = """You are Whis, a cybersecurity SOAR assistant. Provide actionable, operational responses with:
- Specific detection queries and rules
- Incident response procedures  
- SOAR playbook recommendations
- Technical implementation details
- Approval gates for automated actions"""
        
        rag_prompt = f"""Below is an instruction that describes a cybersecurity task, paired with relevant knowledge context. Write a response that appropriately completes the request using the provided context.

### System:
{system_prompt}

### Context:
{context}

### Instruction:
{user_query}

### Response:"""
        
        return rag_prompt
        
    def interactive_search(self):
        """Interactive search interface for testing"""
        if not self.loaded:
            self.load_vector_store()
            
        print("\n🔎 WHIS RAG INTERACTIVE SEARCH")
        print("=" * 40)
        print("Enter queries to search the knowledge base. Type 'quit' to exit.")
        
        while True:
            query = input("\n📝 Query: ").strip()
            if query.lower() in ['quit', 'exit', 'q']:
                break
                
            if not query:
                continue
                
            print(f"\n🔍 Searching: '{query}'")
            results = self.search(query, k=3)
            
            if not results:
                print("❌ No relevant results found.")
                continue
                
            print(f"📊 Found {len(results)} relevant entries:")
            
            for result in results:
                entry = result['entry']
                print(f"\n  📋 Rank {result['rank']} (Score: {result['score']:.3f})")
                
                if isinstance(entry, dict):
                    if 'query' in entry:
                        print(f"     Query: {entry['query'][:100]}...")
                    if 'domain' in entry:
                        print(f"     Domain: {entry['domain']}")
                else:
                    print(f"     Content: {str(entry)[:100]}...")

def main():
    retriever = WhisRAGRetriever()
    
    # Test searches
    test_queries = [
        "MITRE ATT&CK brute force detection",
        "Windows Event 4625 analysis", 
        "Splunk SIEM query for authentication failures",
        "LimaCharlie EDR response automation",
        "SOAR playbook for incident response"
    ]
    
    print("🧪 Testing RAG retrieval with sample queries...")
    retriever.load_vector_store()
    
    for query in test_queries:
        print(f"\n🔍 Query: {query}")
        results = retriever.search(query, k=2)
        print(f"📊 Results: {len(results)}")
        
        for result in results:
            print(f"  - Score: {result['score']:.3f} | {result['entry'].get('query', 'N/A')[:60]}...")
    
    # Generate sample RAG prompt
    print(f"\n📝 Sample RAG Prompt (Teacher Mode):")
    sample_prompt = retriever.generate_rag_prompt(
        "Explain how to detect brute force attacks using Windows Event Logs", 
        mode="teacher"
    )
    print(sample_prompt[:500] + "...")

if __name__ == "__main__":
    main()