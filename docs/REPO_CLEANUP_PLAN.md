# 🧹 WHIS SOAR-Copilot Repository Cleanup Plan

**Senior-Level ML Operations - From Good to Production-Ready**

---

## Phase 1 — Hygiene & Safety

### ✅ **[CLEAN] Remove committed environments & caches**
```bash
# Remove committed virtual environments
rm -rf apps/ui/whis-frontend/venv/
rm -rf ai-training/llm/scripts/codellama-cache/
find . -name "venv" -type d -exec rm -rf {} +
find . -name "__pycache__" -type d -exec rm -rf {} +

# Remove stray version strings and cache files
find . -name "=0.41.0" -delete
find . -name "*.pyc" -delete
find . -name ".DS_Store" -delete
```
- [ ] **Status:** Not Started
- **Rationale:** Non-portable, huge, and drift-prone
- **Owner:** DevOps
- **Priority:** High

### ✅ **[MOVE|ARTIFACTS] Extract heavy artifacts from git**
```bash
# Identify heavy artifacts (>10MB)
find . -type f -size +10M | grep -E '\.(safetensors|bin|faiss|jsonl)$'

# Move to external artifact store
# Target: HF Hub/S3/MinIO bucket
# Keep small manifests with checksums only
```
- [ ] **Status:** Not Started
- **Paths:** `*.safetensors`, `*.bin`, `*.faiss`, large `*.jsonl`, `runs/`
- **Owner:** MLOps
- **Priority:** Critical

### ✅ **[LINKS] Replace absolute symlinks**
```bash
# Fix absolute symlink
rm ai-training/llm/data/external/open_malsec_data
# Replace with relative path or fetch script
```
- [ ] **Status:** Not Started  
- **Path:** `ai-training/llm/data/external/open_malsec_data -> /home/jimmie/...`
- **Owner:** Data Engineering
- **Priority:** High

### ✅ **[POLICY ENFORCE] Quarantine gate**
```bash
# Create quarantine enforcement
mkdir -p data/quarantine/
# Implement fail-closed policy for raw data
```
- [ ] **Status:** Not Started
- **Rule:** `data/raw/{splunk,limacharlie}` → fail until `pii_redaction.py` signs off
- **Owner:** Security
- **Priority:** Critical

### ✅ **[IGNORE MAP] Consolidate .gitignore / LFS rules**
- [ ] **Status:** Not Started
- **Action:** One policy file at repo root; reference in `ai-training/README.md`
- **Owner:** DevOps
- **Priority:** Medium

---

## Phase 2 — Structure & Naming (Boring & Predictable)

### ✅ **[UNIFY MODELS] Standardize adapter storage**
```bash
# Move all LoRA adapters to single location
mkdir -p ai-training/fine_tune/adapters/
mv ai-training/llm/models/* ai-training/fine_tune/adapters/
mv models/* ai-training/fine_tune/adapters/
```
- [ ] **Status:** Not Started
- **Naming:** `whis-lora-{task}-{yyyymmdd}-{gitsha}`
- **Example:** `whis-lora-tooluse-20250823-a1b2c3`
- **Owner:** MLOps
- **Priority:** High

### ✅ **[SERVE FOLDERS] Merge serving dirs**
```bash
# Consolidate serving directories
mv serve/api_server.py ai-training/serving/
rm -rf serve/
# Ensure registry holds release manifests
```
- [ ] **Status:** Not Started
- **Target:** Single `ai-training/serving/` directory
- **Owner:** Backend
- **Priority:** High

### ✅ **[INDEX REGISTRY] Add pointer manifests**
```bash
# Create index version tracking
mkdir -p ai-training/rag/indices/
# Create pointers.json with active versions
```
- [ ] **Status:** Not Started
- **File:** `rag/indices/pointers.json` 
- **Content:** Active versions per corpus (repo/docs/SOC) + refresh times
- **Owner:** MLOps
- **Priority:** High

### ✅ **[RESULTS] Co-locate eval outputs**
```bash
# Move scattered results
mv results/{rag_eval,llm_eval} ai-training/eval/reports/
# Keep root results/ only for cross-cutting dashboards
```
- [ ] **Status:** Not Started
- **Target:** `ai-training/eval/reports/` with subfolders by suite/date
- **Owner:** ML Engineering
- **Priority:** Medium

### ✅ **[APPS/API] Retire "legacy" when ready**
- [ ] **Status:** Not Started
- **Action:** Archive `apps/api/legacy/` or fold into single API
- **Note:** Duplicate engines should map to `ai-training/serving` router
- **Owner:** Backend
- **Priority:** Low

---

## Phase 3 — Contracts & Gates (Remove Ambiguity)

### ✅ **[SCHEMA] Pin schemas in one place**
- [ ] **Status:** Not Started
- **File:** Enhance `use_schema.json` with `Record`, `Chunk`, `IncidentSummary`, `EvalReport`
- **Cross-link:** From `configs/eval.yaml` and `configs/data_governance.yaml`
- **Owner:** Data Engineering
- **Priority:** High

### ✅ **[QUALITY GATES] Make thresholds declarative**
```yaml
# configs/eval.yaml must contain:
thresholds:
  ragas_faithfulness: 0.75
  hit_at_5: 0.90
  p95_latency_ms: 3000
  citation_coverage: 0.95
  json_validity: 0.98
  refusal_accuracy: 0.95
  tool_call_success: 0.90
```
- [ ] **Status:** Not Started
- **Action:** Move hardcoded thresholds to config
- **File:** `tests/quality_gates.py` reads these values
- **Owner:** QA Engineering
- **Priority:** Critical

### ✅ **[DELTA ONLY] Wire triggers**
```python
# ci/index_refresh.py should trigger on:
triggers = [
    "on_session_end",
    "on_git_push_main", 
    "on_splunk_notable(high+)",
    "on_limacharlie_detection(ruleX)"
]
```
- [ ] **Status:** Not Started
- **Action:** Wire `ci/index_refresh.py` → `rag/delta_indexing.py`
- **Gate:** Smoke RAG eval before promotion
- **Owner:** DevOps/MLOps
- **Priority:** Critical

### ✅ **[RAG CONTENT] SOC intake discipline**
- [ ] **Status:** Not Started
- **Rule:** Only embed Incident/Debrief Summaries (titles, ATT&CK, steps, outcome, links)
- **Quarantine:** Raw `splunk/*.jsonl` and `limacharlie/*.jsonl` stay in `data/raw/`
- **Owner:** Security/Data Engineering
- **Priority:** Critical

---

## Phase 4 — Observability & "Easy to See"

### ✅ **[CLI] Make `cli/whis_status.py` the truth**
```bash
# Must display:
# - adapter@version
# - index@{repo,docs,SOC}  
# - dataset hashes
# - last passing eval scores
# - freshness (minutes)
# - rollback target
```
- [ ] **Status:** Not Started
- **Action:** Enhance CLI to show complete system state
- **Owner:** Frontend/CLI
- **Priority:** High

### ✅ **[OPERATOR UI] Align dashboards**
- [ ] **Status:** Not Started
- **Action:** `operator-dashboard/` reads same manifests as CLI
- **Features:** Pointer diffs, promotion history, promote/rollback buttons
- **Owner:** Frontend
- **Priority:** Medium

### ✅ **[EVAL HISTORY] Append-only + human**
- [ ] **Status:** Not Started
- **File:** `ai-training/eval/reports/index.json` with rolling history
- **Content:** Last N runs with pass/fail deltas
- **Owner:** ML Engineering
- **Priority:** Medium

---

## Phase 5 — Prune & Consolidate (Reduce Surface Area)

### ✅ **[TRIM SCRIPTS] Collapse near-duplicates**
- [ ] **Status:** Not Started
- **Path:** `ai-training/rag/scripts/` - merge converter/creator variants
- **Path:** `ai-training/llm/scripts/` - keep one trainer per use case
- **Action:** Decommission duplicates, keep READMEs
- **Owner:** ML Engineering
- **Priority:** Medium

### ✅ **[DOCS] Point everything to one HOWTO**
```markdown
# ai-training/README.md must include:
- How to add data (session, repo, SOC)
- When to embed vs fine-tune
- How to promote/rollback  
- What the gates are
- Links to configs/*.yaml and cli/whis_status.py
```
- [ ] **Status:** Not Started
- **Owner:** Technical Writing
- **Priority:** High

---

## Phase 6 — Security Hardening (Explicit)

### ✅ **[SECRETS] Verify none in repo**
```bash
# Scan for secrets
rg -i "api[_-]?key|secret|token|password" --type json
rg -i "api[_-]?key|secret|token|password" --type md
find . -name "*.ipynb" -exec grep -l "api_key\|secret\|token" {} \;
```
- [ ] **Status:** Not Started
- **Action:** Move sensitive data to secret stores, purge history if needed
- **Owner:** Security
- **Priority:** Critical

### ✅ **[PROMPT INJECTION] Retrieval neutralization**
- [ ] **Status:** Not Started
- **File:** Ensure `rag/rag_sanitizer.py` strips executable instructions
- **Rule:** Serving layer treats retrieved context as content, not commands
- **Owner:** Security/Backend
- **Priority:** Critical

### ✅ **[ACCESS] Corpus ACLs**
- [ ] **Status:** Not Started
- **Future:** Isolate per-tenant indices or add row-level ACLs
- **Action:** Log all queries with corpus + user
- **Owner:** Security
- **Priority:** Low

---

## Definition of Done Checklist

- [ ] Heavy artifacts externalized to HF/S3/MinIO with manifests only in git
- [ ] Single `serving/` directory with registry manifests tying base+adapter+index+datasets+configs
- [ ] `whis_status` shows live tuple + eval scores + freshness; dashboard uses same data
- [ ] Delta indexing triggers wired; smoke eval gates block promotion; nightly full eval runs
- [ ] Only sanitized SOC summaries embedded; raw logs quarantined
- [ ] No venvs/caches/symlinks to home paths; clean clone on any machine
- [ ] All secrets purged from repo history
- [ ] Prompt injection neutralization active
- [ ] Single source of truth for all configurations

---

## SECURITY REVIEW - Top Risks & Mitigations

| Risk | Current State | Mitigation | Priority |
|------|---------------|------------|----------|
| **Repo-committed weights** | ✅ Present | Move to artifact store, checksums | Critical |
| **Raw telemetry embedding** | ⚠️ Possible | Sanitize-then-summarize gate | Critical |
| **Prompt injection via RAG** | ⚠️ Possible | Sanitize retrievals, strong system prompt | Critical |
| **Absolute paths** | ✅ Present | Use relative paths, document fetches | High |
| **Duplication drift** | ✅ Present | Consolidate dirs, single manifest | High |
| **Secrets in repo** | ⚠️ Unknown | Scan and purge, use secret stores | Critical |

## SECURITY CHECKLIST

- [ ] No secrets, envs, or tokens in repo/logs/notebooks
- [ ] Heavy artifacts externalized; checksums recorded  
- [ ] Fine-tune adapters and RAG indices versioned + manifest-tied
- [ ] Delta ingestion gated by smoke eval; nightly full eval with thresholds
- [ ] Only curated SOC summaries embedded; raw logs quarantined
- [ ] Prompt-injection neutralization in RAG; outputs schema-validated with citations
- [ ] One serving directory; API reads registry manifest; rollback tested
- [ ] Clean clone works on any machine without local dependencies

---

## Implementation Timeline

### Week 1 (Critical Path)
- [ ] Phase 1: Hygiene & Safety (items 1-5)
- [ ] Phase 3: Quality gates (items 11-14) 
- [ ] Phase 6: Security scan (item 20)

### Week 2 (Structure)  
- [ ] Phase 2: Structure & Naming (items 6-10)
- [ ] Phase 4: CLI observability (item 15)

### Week 3 (Polish)
- [ ] Phase 4: Remaining observability (items 16-17)
- [ ] Phase 5: Consolidation (items 18-19)
- [ ] Phase 6: Final security hardening (items 21-22)

### Week 4 (Validation)
- [ ] End-to-end testing
- [ ] Documentation review
- [ ] Security audit
- [ ] Production readiness assessment

---

**This cleanup transforms your ML architecture from "good" to "senior-level production-ready" with proper artifact management, security hardening, and operational clarity.**