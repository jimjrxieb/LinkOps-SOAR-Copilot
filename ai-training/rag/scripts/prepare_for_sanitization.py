#!/usr/bin/env python3
"""
Prepare RAG knowledge for sanitization
Converts our processed chunks back to markdown format for the sanitizer
"""

import json
from pathlib import Path
from datetime import datetime

def convert_to_sanitizer_format():
    """Convert our vectorization-ready format to markdown for sanitization"""
    
    # Load our processed knowledge base
    kb_file = Path("../chunks/whis_vectorization_ready.json")
    with open(kb_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"📚 Loaded {len(data['chunks'])} chunks for sanitization")
    
    # Group chunks by source file
    by_source = {}
    for chunk in data['chunks']:
        source = chunk['metadata']['source']
        if source not in by_source:
            by_source[source] = []
        by_source[source].append(chunk)
    
    # Create markdown files for each source
    sanitization_dir = Path("../chunks_for_sanitization")
    sanitization_dir.mkdir(exist_ok=True)
    
    for source_file, chunks in by_source.items():
        # Create markdown content
        md_content = f"# {source_file.replace('.md', '').replace('_', ' ').title()}\n\n"
        
        for chunk in chunks:
            md_content += chunk['text'] + "\n\n---\n\n"
        
        # Save as markdown file
        output_file = sanitization_dir / source_file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        print(f"  ✅ Created {output_file} with {len(chunks)} chunks")
    
    print(f"\n💾 Created {len(by_source)} markdown files in {sanitization_dir}")
    print("🔄 Ready for sanitization with rag_sanitizer.py")
    
    return sanitization_dir

def main():
    print("🔄 PREPARING KNOWLEDGE FOR SANITIZATION")
    print("=" * 50)
    
    sanitization_dir = convert_to_sanitizer_format()
    
    print(f"\n📋 Next steps:")
    print(f"1. Run: export WHIS_REDACT_SALT='your-secure-salt-here'")
    print(f"2. Run: python rag_sanitizer.py {sanitization_dir}/*.md")
    print(f"3. This will create sanitized JSONL files ready for training")

if __name__ == "__main__":
    main()