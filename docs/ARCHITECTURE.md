# 🏗️ Whis SOAR - AI Engineer Architecture

## North Star Principles

* **Separation of lanes:** `intake → sanitize → curate → embed/train → evaluate → serve → observe`
* **Contracts over vibes:** every lane has schemas, CLI entrypoints, logs, and CI gates
* **Security by default:** no secrets in code; scanners + PII/secret redaction in intake; audit trails everywhere
* **Reproducible:** Makefiles, pinned deps, manifests, and artifact versioning

## System Overview

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐    ┌──────────────┐
│   INTAKE    │───▶│   SANITIZE   │───▶│   CURATE    │───▶│     RAG      │
│ (untrusted) │    │ (PII scrub)  │    │ (approved)  │    │ (vectorized) │
└─────────────┘    └──────────────┘    └─────────────┘    └──────────────┘
                                                                    │
┌─────────────┐    ┌──────────────┐    ┌─────────────┐            │
│   OBSERVE   │◀───│    SERVE     │◀───│  LLM TRAIN  │◀───────────┘
│ (telemetry) │    │   (API)      │    │ (behavior)  │
└─────────────┘    └──────────────┘    └─────────────┘
                            │
                    ┌──────────────┐
                    │ HOW ENGINE   │
                    │ (LangGraph)  │
                    └──────────────┘
```

## Lane Responsibilities

### 🚪 **Intake Lane** (`pipelines/intake/`)
- **Purpose**: Ingest data from multiple sources (NIST, GuardPoint, vendor docs)
- **Security**: Secret scanning, license validation, content-type whitelisting
- **Outputs**: Raw data in `data/intake/` with provenance manifests
- **CLI**: `python -m pipelines.intake.cli --source <src> --out data/intake/<date>/<src>`

### 🧹 **Sanitize Lane** (`pipelines/sanitize/`)
- **Purpose**: Strip PII/secrets, normalize domains, remove prompt injection
- **Security**: PII redaction, secret replacement with `[REDACTED:<type>]`
- **Outputs**: Clean data in `data/staging/` with redaction logs
- **CLI**: `python -m pipelines.sanitize.cli --in data/intake/... --out data/staging/...`

### ✅ **Curate Lane** (`pipelines/curate/`)
- **Purpose**: Human-approved datasets with domain labeling
- **Security**: CODEOWNERS approval for sensitive data
- **Outputs**: Approved data in `data/curated/` with NIST/ATT&CK crosswalks
- **CLI**: `python -m pipelines.curate.cli --in data/staging/... --out data/curated/...`

### 🧠 **RAG Lane** (`pipelines/rag/`)
- **Purpose**: Sharded vector indexes with metadata
- **Components**: Chunker, embeddings, FAISS indexes, validators
- **Security**: Freshness gates, grounded_rate ≥ 0.9, contradiction ≤ 0.03
- **CLI**: `python -m pipelines.rag.scripts.{chunk,embed,validate}`

### 🎯 **LLM Lane** (`pipelines/llm/`)
- **Purpose**: Fine-tune behavior (Action Schema + HOW), not facts
- **Security**: Teacher ≥ 0.80, assistant ≥ 0.75, safety = 1.0 gates
- **Outputs**: LoRA adapters in `pipelines/llm/models/<run>/`
- **CLI**: `python -m pipelines.llm.train --config pipelines/llm/configs/lora.yaml`

### 🔧 **HOW Engine Lane** (`pipelines/how/`)
- **Purpose**: Transform "do X" into plan/apply/validate/rollback + artifacts
- **Security**: Validator passes, no secrets, includes rollback procedures
- **Components**: LangGraph prompts, Terraform/K8s templates, validators
- **CLI**: `python -m pipelines.how.run --prompt "Enable CA pilot" --out artifacts/`

### 🚀 **Serve Lane** (`apps/api/`)
- **Purpose**: Predictable API contracts
- **Endpoints**: `/explain`, `/how`, `/score`, `/health`
- **Security**: CSP headers, CORS restrictions, input validation, secret redaction
- **Contracts**: Pydantic models + JSON Schema

### 👁️ **Observe Lane** (cross-cutting)
- **Purpose**: Telemetry, metrics, traces, audit trails
- **Components**: Structured logs, correlation IDs, model BOM tracking
- **Metrics**: p50/p95 latency, grounded_rate, contradiction_rate

## Security Architecture

### Data Flow Security
```
🔓 Untrusted Input → 🔍 Secret Scan → 🧹 PII Redaction → ✅ Human Approval → 🔒 Serve
```

### Threat Model Coverage
- **Data Leakage**: Intake scanners + staging isolation
- **Prompt Injection**: Two-pass sanitization + retrieval guards  
- **Secret Sprawl**: Environment-only secrets + audit trails
- **Stale Data**: Freshness CI gates + manifest validation

## Quality Gates

### CI/CD Gates
- ✅ Zero secrets/PII in artifacts or logs
- ✅ RAG grounded_rate ≥ 0.9; contradiction ≤ 0.03
- ✅ Golden eval gates: assistant ≥ 0.75, teacher ≥ 0.80, safety = 1.0
- ✅ HOW artifacts pass validators (tf fmt, kubeconform, JSON schema)
- ✅ UI smoke tests: buttons work, chat functional, Explain/How render

### Runtime Gates
- API security headers (CSP, CORS)
- Input validation with Pydantic
- Correlation ID tracking
- Model BOM in responses

## Developer Experience

### Quick Start Commands
```bash
make bootstrap  # Setup environment
make lint      # Code quality
make test      # Unit tests
make smoke     # E2E smoke tests
make eval      # Golden gates
make up        # Start services
```

### Clear Entrypoints
- **Add docs**: `docs/RAG_SHARDS.md` → `pipelines/rag/chunks/<shard>/`
- **Retrain**: `pipelines/llm/README.md` → `make eval`
- **Test UI**: `tests/e2e/README.md` → `pnpm playwright test`
- **Deploy**: `infra/terraform/README.md` → `./deploy.sh`

## Migration Plan

1. **Phase 1**: Move existing code into new structure
2. **Phase 2**: Implement intake/sanitize/curate lanes
3. **Phase 3**: Add RAG sharding and LLM training
4. **Phase 4**: Build HOW engine with LangGraph
5. **Phase 5**: Comprehensive observability and CI/CD

This architecture transforms Whis SOAR into a production-ready AI system with clear boundaries, security by default, and batteries-included operations.