#!/usr/bin/env python3
"""
RAG Vectorization Preparation Script
Prepare SecOps knowledge base for vector embedding and retrieval
"""

import os
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple
import re

class RAGKnowledgePrepper:
    """Prepare knowledge documents for RAG vectorization"""
    
    def __init__(self, knowledge_dir: str = "./knowledge"):
        self.knowledge_dir = Path(knowledge_dir)
        self.documents = []
        
    def chunk_document(self, content: str, doc_id: str, max_chunk_size: int = 1000) -> List[Dict]:
        """Split document into semantic chunks for vectorization"""
        chunks = []
        
        # Split by major sections (##)
        sections = re.split(r'\n## ', content)
        
        for i, section in enumerate(sections):
            if not section.strip():
                continue
                
            # Extract section title
            lines = section.split('\n')
            title = lines[0].replace('##', '').strip()
            section_content = '\n'.join(lines[1:])
            
            # Further split large sections by subsections (###)
            if len(section_content) > max_chunk_size:
                subsections = re.split(r'\n### ', section_content)
                
                for j, subsection in enumerate(subsections):
                    if not subsection.strip():
                        continue
                        
                    subsection_lines = subsection.split('\n')
                    subtitle = subsection_lines[0].replace('###', '').strip()
                    sub_content = '\n'.join(subsection_lines[1:])
                    
                    chunk = {
                        "chunk_id": f"{doc_id}_section_{i}_subsection_{j}",
                        "document_id": doc_id,
                        "title": f"{title} - {subtitle}",
                        "content": sub_content.strip(),
                        "section_type": "subsection",
                        "section_index": i,
                        "subsection_index": j,
                        "word_count": len(sub_content.split()),
                        "content_hash": hashlib.md5(sub_content.encode()).hexdigest()[:8]
                    }
                    chunks.append(chunk)
            else:
                # Keep section as single chunk
                chunk = {
                    "chunk_id": f"{doc_id}_section_{i}",
                    "document_id": doc_id,
                    "title": title,
                    "content": section_content.strip(),
                    "section_type": "section",
                    "section_index": i,
                    "word_count": len(section_content.split()),
                    "content_hash": hashlib.md5(section_content.encode()).hexdigest()[:8]
                }
                chunks.append(chunk)
        
        return chunks
    
    def extract_metadata(self, content: str) -> Dict:
        """Extract metadata from document header"""
        metadata = {}
        
        # Look for metadata section
        lines = content.split('\n')
        in_metadata = False
        
        for line in lines:
            if '## Document Metadata' in line:
                in_metadata = True
                continue
            elif in_metadata and line.startswith('- **'):
                # Parse metadata line: - **Key**: Value
                match = re.match(r'- \*\*([^*]+)\*\*:\s*(.+)', line)
                if match:
                    key = match.group(1).lower().replace(' ', '_')
                    value = match.group(2)
                    metadata[key] = value
            elif in_metadata and line.startswith('---'):
                break
        
        return metadata
    
    def process_knowledge_documents(self) -> List[Dict]:
        """Process all knowledge documents in the directory"""
        processed_docs = []
        
        # Find all markdown files
        md_files = list(self.knowledge_dir.rglob("*.md"))
        
        print(f"📚 Processing {len(md_files)} knowledge documents...")
        
        for md_file in md_files:
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Extract metadata
                metadata = self.extract_metadata(content)
                doc_id = metadata.get('id', md_file.stem)
                
                # Create document chunks
                chunks = self.chunk_document(content, doc_id)
                
                # Add file-level metadata to each chunk
                for chunk in chunks:
                    chunk.update({
                        "source_file": str(md_file),
                        "document_metadata": metadata,
                        "created_date": datetime.now().isoformat(),
                        "tags": metadata.get('tags', '').split(', ') if metadata.get('tags') else []
                    })
                
                processed_docs.extend(chunks)
                print(f"  ✅ {md_file.name}: {len(chunks)} chunks created")
                
            except Exception as e:
                print(f"  ❌ Failed to process {md_file.name}: {e}")
        
        return processed_docs
    
    def create_rag_manifest(self, documents: List[Dict]) -> Dict:
        """Create RAG system manifest"""
        manifest = {
            "rag_system": "whis_knowledge_base",
            "created_date": datetime.now().isoformat(),
            "total_documents": len(set(doc["document_id"] for doc in documents)),
            "total_chunks": len(documents),
            "chunk_statistics": {
                "avg_word_count": sum(doc["word_count"] for doc in documents) / len(documents),
                "total_words": sum(doc["word_count"] for doc in documents),
                "content_types": {}
            },
            "retrieval_config": {
                "teacher_mode": {
                    "k": 6,
                    "min_sources": 2,
                    "fallback_policy": "insufficient_evidence_response"
                },
                "assistant_mode": {
                    "k": 8,
                    "required_patterns": ["attack_technique", "tool_specific"],
                    "fallback_policy": "generic_with_disclaimer"
                }
            },
            "citation_format": "source_title + section + hash[:8]",
            "documents": {}
        }
        
        # Group by document
        by_doc = {}
        for doc in documents:
            doc_id = doc["document_id"]
            if doc_id not in by_doc:
                by_doc[doc_id] = []
            by_doc[doc_id].append(doc)
        
        # Create document summaries
        for doc_id, chunks in by_doc.items():
            manifest["documents"][doc_id] = {
                "chunk_count": len(chunks),
                "total_words": sum(chunk["word_count"] for chunk in chunks),
                "sections": [chunk["title"] for chunk in chunks],
                "tags": chunks[0]["tags"] if chunks else [],
                "source_file": chunks[0]["source_file"] if chunks else "",
                "content_hash": hashlib.md5(
                    ''.join(chunk["content"] for chunk in chunks).encode()
                ).hexdigest()[:8]
            }
        
        return manifest
    
    def save_rag_dataset(self, documents: List[Dict], output_dir: str = "./rag_data"):
        """Save processed documents for RAG system"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save chunks dataset
        chunks_file = output_path / f"rag_chunks_{timestamp}.json"
        with open(chunks_file, 'w', encoding='utf-8') as f:
            json.dump(documents, f, indent=2, ensure_ascii=False)
        
        # Create manifest
        manifest = self.create_rag_manifest(documents)
        manifest_file = output_path / f"rag_manifest_{timestamp}.json"
        with open(manifest_file, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        
        # Create vector embeddings preparation script
        embed_script = f'''#!/usr/bin/env python3
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
    with open("{chunks_file}", "r") as f:
        chunks = json.load(f)
    
    print(f"📊 Processing {{len(chunks)}} chunks...")
    
    # Load embedding model
    print("🤗 Loading SentenceTransformer model...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    # Create embeddings
    texts = [chunk["content"] for chunk in chunks]
    embeddings = model.encode(texts, show_progress_bar=True)
    
    print(f"✅ Created embeddings: {{embeddings.shape}}")
    
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
'''
        
        embed_script_file = output_path / "create_embeddings.py"
        with open(embed_script_file, 'w') as f:
            f.write(embed_script)
        
        # Make executable
        os.chmod(embed_script_file, 0o755)
        
        print(f"\n💾 RAG Dataset Saved:")
        print(f"  📄 Chunks: {chunks_file}")
        print(f"  📋 Manifest: {manifest_file}")  
        print(f"  🔍 Embeddings script: {embed_script_file}")
        
        return {
            "chunks_file": str(chunks_file),
            "manifest_file": str(manifest_file),
            "embedding_script": str(embed_script_file),
            "total_chunks": len(documents)
        }

def main():
    """Main RAG preparation pipeline"""
    print("🔍 RAG Knowledge Base Preparation Pipeline")
    print("=" * 50)
    
    # Initialize processor
    processor = RAGKnowledgePrepper()
    
    # Process documents
    documents = processor.process_knowledge_documents()
    
    if not documents:
        print("❌ No documents found to process")
        return
    
    # Save RAG dataset
    result = processor.save_rag_dataset(documents)
    
    print(f"\n🎯 RAG Preparation Complete!")
    print(f"📊 Processed {result['total_chunks']} knowledge chunks")
    print("🚀 Ready for vector embedding generation!")
    
    return result

if __name__ == "__main__":
    main()