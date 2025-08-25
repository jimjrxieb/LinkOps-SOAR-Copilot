# 🧠 AI-Training: Machine Learning Workflows for WHIS SOAR-Copilot

**Production ML workflows across three tracks: fine-tuning, retrieval-augmented generation (RAG), and evaluation/serving.**

---

## 🎯 **CORRECTED ML ARCHITECTURE**

We maintain a single top-level **`ai-training/`** directory that hosts our machine learning workflows across three tracks: **fine-tuning**, **retrieval-augmented generation (RAG)**, and **evaluation/serving**.

* **Model ("Whis")**: a base LLM from Hugging Face. We **fine-tune** Whis using **LoRA adapters** on curated, sanitized datasets. Fine-tuning produces **adapter weights**, not a new base model.
* **Data intake & sanitization**: all raw inputs (documents, transcripts, logs) pass through standardized **ingest → sanitize → normalize** steps (PII redaction, deduplication, chunking, schema validation).
* **RAG pipeline**: we embed documents into a **vector store** (e.g., Qdrant/Chroma) and configure a **retriever** that supplies relevant context to Whis **at inference time**. RAG **does not change model weights**; it augments prompts with retrieved context.
* **Evaluation**: we maintain static **benchmark suites** for both fine-tuned tasks and RAG quality (e.g., exact-match/F1 on task sets, **RAGAS** for retrieval faithfulness, latency/throughput SLOs). Evaluation is reproducible and independent from training.
* **Serving**: we version and serve Whis with selected LoRA adapters and connect it to the retriever for production inference. Config chooses **which adapter** and **which index** are active.
* **Experiment tracking**: all runs log **params, metrics, artifacts, and dataset/version hashes** (e.g., MLflow/W&B), enabling rollback and auditability.
* **MLOps/CI**: automated checks validate data schemas, generate SBOMs for dependencies, run eval suites on PRs, and gate promotion to staging/prod.

---

## 📁 **CORRECTED DIRECTORY STRUCTURE**

```
ai-training/
├── README.md                    # This file
├── configs/                     # Configuration management
│   ├── model.whis.yaml         # Base + adapter config (no secrets)
│   ├── rag.yaml                # Retriever, chunking, embedder config
│   └── eval.yaml               # Benchmark suites, thresholds
├── data/                       # Data governance & versioning
│   ├── raw/                    # Immutable inputs
│   ├── staging/                # Sanitized, deduped, chunked
│   └── datasets/               # Train/val/test splits (versioned)
├── fine_tune/                  # Fine-tuning pipeline (SEPARATE from RAG)
│   ├── lora_train.py          # Fine-tuning script
│   ├── adapters/              # Produced LoRA weights (versioned)
│   └── experiments/           # MLflow or logs
├── rag/                        # RAG pipeline (SEPARATE from fine-tuning)
│   ├── embed.py               # Document embedding
│   ├── index/                 # Vector store metadata (not secrets)
│   └── retriever/             # Retriever configs, prompts
├── eval/                       # Evaluation pipeline (INDEPENDENT)
│   ├── benchmarks/            # Golden sets, RAGAS configs
│   ├── run_eval.py            # Produces reproducible reports
│   └── reports/               # Evaluation results
├── serving/                    # Production serving
│   ├── inference_server.py    # Loads base + adapter, connects retriever
│   └── router.py              # Chooses adapter/index per env
└── scripts/                    # Shared utilities
    ├── ingest_sanitize.py     # Data intake and sanitization
    ├── make_splits.py         # Dataset splitting
    └── export_artifacts.py    # Artifact management
```

---

## 🔧 **TERMINOLOGY CORRECTIONS**

* **❌ "RAG vectorizes data for Whis to use"**
  * **✅ "RAG embeds documents into a vector store used by the retriever, which supplies context to Whis at inference"**

* **❌ "Test pipeline trains until master"**
  * **✅ "Evaluation pipeline measures performance on held-out benchmarks; training remains separate"**

* **❌ "Learns with LoRA like Google Colab"**
  * **✅ "Fine-tunes with LoRA adapters (as we previously prototyped in Colab)"**

---

## 🎯 **MISSING COMPONENTS IDENTIFIED**

### **Data Governance**
- [ ] PII redaction policies
- [ ] License tracking  
- [ ] Dataset versioning (DVC or data registry)
- [ ] Lineage tracking (which model used which dataset)

### **Experiment Tracking**
- [ ] MLflow/W&B run logs
- [ ] Metrics and artifacts logging
- [ ] Commit hash + dataset version pinning

### **Clear Metrics**
- [ ] **Fine-tune**: accuracy/F1/ROUGE/BLEU, loss curves, calibration
- [ ] **RAG**: RAGAS (faithfulness, answer relevance, context precision/recall), retrieval hit@k, latency p95

### **Serving/Rollout**
- [ ] Canary adapters
- [ ] Shadow traffic
- [ ] Rollback plan

### **Guardrails**
- [ ] JSON schema validation for outputs
- [ ] Refusal policies
- [ ] Prompt-injection defenses for RAG

### **Resource Policy**
- [ ] GPU/VRAM budgeting
- [ ] Fallbacks (CPU)
- [ ] Device selection

---

## 🛡️ **SECURITY CHECKLIST (ML/RAG Specific)**

### **Data Security**
- [ ] **Data leakage/PII**: sanitize + redact before embedding or training; store redaction logs
- [ ] **Prompt injection via RAG**: strip/neutralize instructions from retrieved docs; use system prompts and content-binding; cap context length
- [ ] **Model inversion risks**: avoid training on secrets; add canary phrases to detect leakage; refuse requests for verbatim training data

### **Supply Chain Security**
- [ ] Pin HF model + tokenizer versions; verify checksums
- [ ] Lock dependency versions; generate SBOM
- [ ] **Secrets**: keep API keys, DB creds in env/secret stores only; never in repo or artifacts

### **Production Security**
- [ ] No secrets in code/artifacts; all via env/secret store
- [ ] Data sanitize/redact enforced; datasets versioned
- [ ] Fine-tune and RAG separated; configs pinned
- [ ] Eval suites (incl. RAGAS) with promotion gates
- [ ] Dependency versions pinned; SBOM + scans documented
- [ ] Inference enforces output schema/guardrails
- [ ] Canary/rollback for adapter deployments

---

## 🚀 **EXECUTION PLAN (No Code Implementation)**

1. **Split pipelines**: create `fine_tune/` and `rag/` with distinct entry points and configs
2. **Data contract**: define a `Record` schema (source, text, labels, redaction flags) and a `Chunk` schema (id, text, meta). Enforce in sanitize step
3. **Version everything**: dataset hashes; adapter versions; index versions; config snapshots
4. **Eval first**: lock a small golden set + RAGAS suite; define pass/fail gates (e.g., RAGAS ≥ 0.75, p95 latency ≤ 3s)
5. **Serving plan**: one command loads base + chosen adapter + retriever; support canary adapter via config
6. **CI hooks**: on PR, run sanitize validation, tiny training smoke (1 epoch), RAGAS sample eval, and security scans

---

**Status**: Architecture corrected according to mentor feedback. Ready for proper ML pipeline implementation.