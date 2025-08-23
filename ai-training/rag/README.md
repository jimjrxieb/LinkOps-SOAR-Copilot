# 📚 RAG Knowledge Pipeline

Sanitize, chunk, and vectorize cybersecurity knowledge for Whis retrieval augmentation.

## Quick Start

```bash
# Sanitize raw knowledge chunks
cd pipelines/rag/scripts
python rag_sanitizer.py --in ../chunks/raw/ --out ../chunks/sanitized/

# Generate consolidated datasets  
python consolidate_rag_datasets.py --out ../chunks/consolidated_rag_training_data.json

# Vectorize knowledge base
python vectorize_rag.py --manifest ../vectorstore/whis_production_manifest.json

# Test retrieval
python rag_retriever.py --query "How to respond to T1110 brute force?"

# Check vectorstore manifest
cat ../vectorstore/whis_production_manifest_*.json
```

## Outputs
- **Manifests**: `vectorstore/*.json` (tracked in Git)
- **Large indices**: Generated outside Git (see manifest for paths & sizes)
- **Embedding size**: 106 vectorized knowledge entries

## Structure

- `scripts/` - Data generators, sanitizers, and vectorization tools
- `chunks/` - Raw and sanitized document chunks (JSON/JSONL)
- `vectorstore/` - Vector index manifests and metadata (no large binaries)

## Knowledge Domains

- 🎯 MITRE ATT&CK techniques and detection
- 🛡️ Kubernetes security and CKS practices
- 📊 SIEM/SOAR automation playbooks
- 🔍 Threat intelligence and IOCs
- 📋 Compliance frameworks (SOC2, ISO27001)

## Vectorstore

Large vector indices (*.faiss, *.npy, *.pkl) stored externally. Manifests in `vectorstore/` contain download/rebuild instructions.