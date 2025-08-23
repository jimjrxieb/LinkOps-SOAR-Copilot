#!/usr/bin/env python3
"""
RAG Markdown Chunk Processor
Converts markdown knowledge chunks into vectorizable format
"""

import os
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

class MarkdownRAGProcessor:
    def __init__(self, chunks_dir: str = "../chunks", output_dir: str = "../chunks"):
        self.chunks_dir = Path(chunks_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
    def process_markdown_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Process a markdown file into RAG chunks"""
        print(f"🔍 Processing: {file_path.name}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Split by scenarios (## headings)
        sections = content.split('\n## ')
        chunks = []
        
        for i, section in enumerate(sections):
            if i == 0:
                # First section includes the title
                if section.strip():
                    parts = section.split('\n## ', 1)
                    if len(parts) > 1:
                        title = parts[0].strip('# ').strip()
                        section = parts[1]
                    else:
                        continue
                else:
                    continue
            
            if not section.strip():
                continue
                
            # Extract scenario title
            lines = section.split('\n', 1)
            scenario_title = lines[0].strip()
            scenario_content = lines[1] if len(lines) > 1 else ""
            
            # Create chunk
            chunk_id = hashlib.md5(f"{file_path.stem}_{scenario_title}".encode()).hexdigest()[:12]
            
            chunk = {
                "chunk_id": chunk_id,
                "source_file": file_path.name,
                "title": scenario_title,
                "content": scenario_content.strip(),
                "metadata": {
                    "category": self.categorize_content(file_path.name, scenario_title),
                    "complexity": "senior",
                    "format": "scenario_analysis",
                    "tags": self.extract_tags(scenario_title, scenario_content)
                },
                "timestamp": datetime.now().isoformat()
            }
            
            chunks.append(chunk)
            
        print(f"  ✅ Extracted {len(chunks)} scenarios")
        return chunks
    
    def categorize_content(self, filename: str, title: str) -> str:
        """Categorize content based on filename and title"""
        if "devsecops" in filename.lower():
            return "devsecops_economics"
        elif "cloud" in filename.lower():
            return "cloud_security"
        elif "incident" in filename.lower():
            return "incident_response"
        elif "compliance" in filename.lower():
            return "compliance_automation"
        elif "vendor" in filename.lower():
            return "vendor_risk_management"
        else:
            return "general_security"
    
    def extract_tags(self, title: str, content: str) -> List[str]:
        """Extract relevant tags from content"""
        tags = set()
        
        # Add title-based tags
        title_lower = title.lower()
        if "cost" in title_lower or "roi" in title_lower:
            tags.add("cost_optimization")
        if "patch" in title_lower:
            tags.add("patch_management")
        if "mfa" in title_lower:
            tags.add("multi_factor_auth")
        if "cloud" in title_lower:
            tags.add("cloud_security")
        if "compliance" in title_lower:
            tags.add("regulatory_compliance")
        if "vendor" in title_lower:
            tags.add("third_party_risk")
        if "api" in title_lower:
            tags.add("api_security")
        
        # Add content-based tags
        content_lower = content.lower()
        if "$" in content and ("million" in content_lower or "k " in content_lower):
            tags.add("financial_impact")
        if "azure" in content_lower or "aws" in content_lower or "gcp" in content_lower:
            tags.add("multi_cloud")
        if "container" in content_lower or "kubernetes" in content_lower:
            tags.add("container_security")
        if "gdpr" in content_lower or "pci" in content_lower or "sox" in content_lower:
            tags.add("regulatory_frameworks")
        
        return list(tags)
    
    def process_all_chunks(self) -> Dict[str, Any]:
        """Process all markdown files in chunks directory"""
        print("🔄 RAG MARKDOWN PROCESSOR")
        print("=" * 50)
        
        all_chunks = []
        file_count = 0
        
        # Process all .md files
        for md_file in self.chunks_dir.glob("*.md"):
            if md_file.name.startswith('.'):
                continue
                
            chunks = self.process_markdown_file(md_file)
            all_chunks.extend(chunks)
            file_count += 1
        
        # Create consolidated dataset
        dataset = {
            "metadata": {
                "name": "WHIS Senior DevSecOps Knowledge Base",
                "description": "Comprehensive senior-level DevSecOps scenarios with cost-benefit analysis",
                "version": "1.0",
                "created_at": datetime.now().isoformat(),
                "total_chunks": len(all_chunks),
                "source_files": file_count,
                "categories": list(set(chunk["metadata"]["category"] for chunk in all_chunks)),
                "tags": list(set(tag for chunk in all_chunks for tag in chunk["metadata"]["tags"]))
            },
            "chunks": all_chunks
        }
        
        # Save consolidated dataset
        output_file = self.output_dir / "whis_senior_knowledge_base.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(dataset, f, indent=2, ensure_ascii=False)
        
        print(f"\n📈 PROCESSING SUMMARY:")
        print(f"  📁 Files Processed: {file_count}")
        print(f"  📚 Total Chunks: {len(all_chunks)}")
        print(f"  🏷️  Categories: {len(dataset['metadata']['categories'])}")
        print(f"  🔖 Unique Tags: {len(dataset['metadata']['tags'])}")
        print(f"  💾 Output File: {output_file}")
        
        # Create vectorization-ready format
        vectorization_data = {
            "dataset_id": "whis_senior_knowledge_base",
            "version": "1.0",
            "chunks": [
                {
                    "id": chunk["chunk_id"],
                    "text": f"# {chunk['title']}\n\n{chunk['content']}",
                    "metadata": {
                        "source": chunk["source_file"],
                        "category": chunk["metadata"]["category"],
                        "tags": chunk["metadata"]["tags"],
                        "timestamp": chunk["timestamp"]
                    }
                }
                for chunk in all_chunks
            ]
        }
        
        vector_file = self.output_dir / "whis_vectorization_ready.json"
        with open(vector_file, 'w', encoding='utf-8') as f:
            json.dump(vectorization_data, f, indent=2, ensure_ascii=False)
        
        print(f"  🚀 Vectorization File: {vector_file}")
        
        return dataset

def main():
    processor = MarkdownRAGProcessor()
    dataset = processor.process_all_chunks()
    
    print("\n✅ RAG processing complete!")
    print("🎯 Ready for vectorization and embedding generation")

if __name__ == "__main__":
    main()