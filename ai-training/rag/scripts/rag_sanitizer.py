#!/usr/bin/env python3
"""
Whis RAG Sanitizer - Production Grade
Based on mentor guidance for PII redaction and provenance tracking
"""

import os
import re
import hmac
import hashlib
import json
import unicodedata
from datetime import datetime
from typing import Dict, Tuple, List
from pathlib import Path

class WhisRAGSanitizer:
    """Production-grade sanitizer for Whis RAG pipeline"""
    
    def __init__(self):
        self.salt = os.environ.get("WHIS_REDACT_SALT", "CHANGE_ME_IN_ENV")
        if self.salt == "CHANGE_ME_IN_ENV":
            print("⚠️ WARNING: WHIS_REDACT_SALT not set - using default (NOT SECURE)")
        
        # Compiled patterns for performance
        self.patterns = self._compile_patterns()
        
    def _compile_patterns(self):
        """Compile all redaction patterns"""
        return {
            'EMAIL': re.compile(r"\b[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}\b", re.I),
            'IPV4': re.compile(r"\b(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)\b"),
            'IPV6': re.compile(r"\b(?:[0-9a-f]{0,4}:){2,7}[0-9a-f]{0,4}\b", re.I),
            'UUID': re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", re.I),
            'TIMESTAMP': re.compile(r"\b(?:\d{4}[-/]\d{2}[-/]\d{2}[ T_]\d{2}:\d{2}:\d{2}(?:\.\d+)?Z?)\b"),
            'WINPATH': re.compile(r"[A-Za-z]:\\(?:[^\\/:*?\"<>|\r\n]+\\)*[^\\/:*?\"<>|\r\n]*"),
            'URL': re.compile(r"\bhttps?://[^\s)>\]]+", re.I),
            'AWS_KEY': re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
            'GENERIC_TOKEN': re.compile(r"\b(?:xoxb|ghp|hf_[A-Za-z0-9]{20,})[A-Za-z0-9_=-]{10,}\b"),
            'HIGH_ENTROPY': re.compile(r"\b[A-Za-z0-9+/]{28,}={0,2}\b")
        }
    
    def _h(self, token: str) -> str:
        """Deterministic pseudonym (HMAC-SHA256) preserves joins without exposing value"""
        return hmac.new(self.salt.encode(), token.encode(), hashlib.sha256).hexdigest()[:10]
    
    def normalize_text(self, text: str) -> str:
        """Unicode cleanup & whitespace normalization"""
        # Unicode normalization
        t = unicodedata.normalize("NFKC", text)
        
        # Line ending cleanup
        t = t.replace("\r\n", "\n").replace("\r", "\n")
        
        # Whitespace cleanup
        t = re.sub(r"[ \t]+\n", "\n", t)
        t = re.sub(r"\n{3,}", "\n\n", t)
        
        return t.strip()
    
    def redact_and_canon(self, text: str) -> Tuple[str, Dict[str, int]]:
        """Apply redaction and canonicalization patterns"""
        counts = {}
        out = text
        
        # Define replacement functions
        replacements = {
            'EMAIL': lambda m: f"<EMAIL:{self._h(m.group(0))}>",
            'IPV4': lambda m: f"<IP:{self._h(m.group(0))}>", 
            'IPV6': lambda m: f"<IP6:{self._h(m.group(0))}>",
            'UUID': lambda m: f"<UUID:{self._h(m.group(0))}>",
            'TIMESTAMP': lambda m: "<TS>",
            'WINPATH': lambda m: "<PATH>",
            'URL': lambda m: "<URL>",
            'AWS_KEY': lambda m: "<SECRET:AWS_KEY>",
            'GENERIC_TOKEN': lambda m: "<SECRET:TOKEN>",
            'HIGH_ENTROPY': lambda m: "<SECRET:ENTROPY>"
        }
        
        # Apply patterns
        for pattern_name, pattern in self.patterns.items():
            before = out
            repl_func = replacements[pattern_name]
            out = pattern.sub(repl_func, out)
            if out != before:
                counts[pattern_name] = counts.get(pattern_name, 0) + len(pattern.findall(before))
        
        return out, counts
    
    def sanitize(self, text: str, title: str, source_path: str, tags=None) -> Dict:
        """Main sanitization pipeline"""
        tags = tags or []
        
        # Step 1: Normalize
        t0 = self.normalize_text(text)
        
        # Step 2: Redact and canonicalize
        t1, stats = self.redact_and_canon(t0)
        
        # Step 3: Preserve minimal heading structure
        t1 = re.sub(r"(?m)^(#+\s+)", r"\n\1", t1)
        t1 = re.sub(r"\n{3,}", "\n\n", t1)
        
        # Generate content hash
        sha = hashlib.sha256(t1.encode()).hexdigest()
        
        return {
            "chunk_id": f"kb-{sha[:12]}",
            "title": title,
            "text": t1,
            "source_path": source_path,
            "sha256": sha,
            "tags": tags,
            "ingested_at": datetime.utcnow().isoformat() + "Z",
            "pii_redacted": True,
            "redaction_stats": stats
        }
    
    def split_into_chunks(self, text: str, max_chars=3500, overlap=400) -> List[str]:
        """Heading-aware chunking with overlap"""
        parts = []
        cursor = 0
        
        while cursor < len(text):
            window = text[cursor: cursor + max_chars]
            
            # Prefer to cut before next heading
            cut = window.rfind("\n## ")
            if cut < max_chars * 0.4:
                cut = window.rfind("\n\n")
            if cut < max_chars * 0.4:
                cut = len(window)
            
            parts.append(text[cursor: cursor + cut].strip())
            cursor += cut - overlap if cut > overlap else cut
        
        return [p for p in parts if p]
    
    def build_chunks(self, doc_title: str, source_path: str, raw_text: str, tags=None) -> List[Dict]:
        """Build production-ready chunks from document"""
        sanitized = self.sanitize(raw_text, doc_title, source_path, tags)
        chunks = []
        
        for i, piece in enumerate(self.split_into_chunks(sanitized["text"])):
            chunk = dict(sanitized)
            chunk["chunk_id"] = f'{sanitized["chunk_id"]}-{i:03d}'
            chunk["text"] = piece
            chunk["provenance"] = {
                "section": f"part-{i}",
                "vendor": "internal",
                "chunk_index": i
            }
            chunks.append(chunk)
        
        return chunks
    
    def process_knowledge_base(self, knowledge_dir: str = "./knowledge") -> List[Dict]:
        """Process entire knowledge base with sanitization"""
        sanitizer = WhisRAGSanitizer()
        all_chunks = []
        
        knowledge_path = Path(knowledge_dir)
        
        # Process markdown files
        md_files = list(knowledge_path.rglob("*.md"))
        
        print(f"🔒 Processing {len(md_files)} files with PII sanitization...")
        
        for md_file in md_files:
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Extract tags from filename/path
                tags = []
                if "attack" in str(md_file).lower():
                    tags.append("ATTACK")
                if "T1110" in str(md_file):
                    tags.append("ATTACK:T1110")
                if "teacher" in str(md_file).lower():
                    tags.append("Teacher")
                if "assistant" in str(md_file).lower():
                    tags.append("Assistant")
                
                title = md_file.stem.replace("-", " ").title()
                chunks = sanitizer.build_chunks(title, str(md_file), content, tags)
                
                all_chunks.extend(chunks)
                print(f"  ✅ {md_file.name}: {len(chunks)} sanitized chunks")
                
            except Exception as e:
                print(f"  ❌ Failed to process {md_file.name}: {e}")
        
        return all_chunks
    
    def save_jsonl(self, chunks: List[Dict], output_path: str):
        """Save chunks as JSONL for embedding"""
        with open(output_path, 'w', encoding='utf-8') as f:
            for chunk in chunks:
                f.write(json.dumps(chunk, ensure_ascii=False) + "\n")
        
        print(f"💾 Saved {len(chunks)} chunks to {output_path}")

def main():
    """Main processing pipeline"""
    print("🛡️ WHIS RAG SANITIZER - PRODUCTION GRADE")
    print("=" * 50)
    
    # Security check
    if os.environ.get("WHIS_REDACT_SALT", "CHANGE_ME_IN_ENV") == "CHANGE_ME_IN_ENV":
        print("⚠️ WARNING: Set WHIS_REDACT_SALT environment variable!")
        print("Example: export WHIS_REDACT_SALT='your-secure-salt-here'")
    
    sanitizer = WhisRAGSanitizer()
    
    # Process knowledge base
    chunks = sanitizer.process_knowledge_base()
    
    if not chunks:
        print("❌ No chunks produced")
        return
    
    # Create output directory
    output_dir = Path("./sanitized_rag_data")
    output_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save as JSONL
    jsonl_path = output_dir / f"sanitized_chunks_{timestamp}.jsonl"
    sanitizer.save_jsonl(chunks, str(jsonl_path))
    
    # Create manifest
    manifest = {
        "sanitizer_version": "1.0",
        "processed_at": datetime.utcnow().isoformat() + "Z",
        "total_chunks": len(chunks),
        "security_controls": {
            "pii_redacted": True,
            "secrets_masked": True,
            "deterministic_pseudonyms": True,
            "provenance_tracking": True
        },
        "retrieval_policy": {
            "teacher_mode": {
                "k": 6,
                "min_sources": 2,
                "fallback": "insufficient_evidence_response"
            },
            "assistant_mode": {
                "k": 8,
                "required_patterns": ["ATTACK", "tool_specific"],
                "fallback": "generic_with_disclaimer"
            }
        },
        "chunks_file": str(jsonl_path)
    }
    
    manifest_path = output_dir / f"sanitized_manifest_{timestamp}.json"
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    print(f"📋 Manifest saved to {manifest_path}")
    print(f"🎯 Sanitized RAG pipeline ready!")
    
    return chunks

if __name__ == "__main__":
    main()