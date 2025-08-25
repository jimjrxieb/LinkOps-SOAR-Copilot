# 🎯 WHIS SOAR-Copilot Operations Playbook

**Senior-Level ML Operations - Copy-Pasteable Runbook**

---

## What Actually Runs, and When

### A) After **Each Session** (Conversation, Training, Code Changes)

**Trigger:** Session completion, git push to main, significant conversation

```bash
# Session delta processing
python ai-training/rag/delta_indexing.py \
  --session-type conversation \
  --changes-summary "User discussed new security controls and updated playbooks"

# What happens:
# 1. Session Delta: Auto-generate "what changed/decisions/facts/TODOs"  
# 2. Sanitize: PII/secrets redaction, normalize to Record schema
# 3. Chunk: Code (function/class-aware) + prose (200-400 tokens)
# 4. Embed & Upsert: Only new/changed chunks → vector store
# 5. Smoke RAG Eval: 10-20 golden Qs to catch regressions
# 6. Promote: Update index pointer if smoke tests pass
```

**SLO:** ≤ 5 minutes from session end to live index

### B) **Splunk & LimaCharlie** (Event-Driven, Real-Time)

**Trigger:** Webhook on HIGH/CRITICAL detections

```bash
# Example webhook processing
curl -X POST http://localhost:8000/webhooks/splunk \
  -H "Content-Type: application/json" \
  -d @splunk_critical_alert.json

# What happens:
# 1. Intake: HIGH/CRITICAL notable events only
# 2. Normalize: Convert to Detection/Incident Summary:
#    - What/where/when/evidence/ATT&CK/triage/outcome
# 3. Sanitize: Strip tokens/IDs, neutralize instructions
# 4. Summarize: Playbook-quality narrative + structured fields
# 5. Embed & Upsert: Summary only (NOT raw logs)
# 6. Daily RAG Eval: SOC Q&A validation
```

**SLO:** ≤ 2 minutes from event to searchable knowledge

### C) **Nightly Maintenance Jobs**

**Trigger:** Cron schedule (2 AM daily)

```bash
# Full pipeline maintenance
python ai-training/ci/index_refresh.py --trigger nightly

# What runs:
# 1. Compaction & Dedupe: Merge near-duplicates, drop stale versions
# 2. Full RAG Eval: Complete RAGAS suite (faithfulness, precision, recall)
# 3. Drift Scan: Flag domains with retrieval decay  
# 4. Canary Swap: index@next → index@live if evals pass
# 5. Cleanup: Remove expired detections (TTL), old versions
```

**SLO:** Complete maintenance window ≤ 30 minutes

---

## Selection Rules (Keep Index Clean)

### ✅ **Include:**
- Code/API docs, READMEs, runbooks
- Incident/detection summaries (HIGH+ severity only)
- Post-mortems, architectural decisions
- Config intent, deployment guides
- Session outcomes and decisions

### ❌ **Exclude:**
- Raw event logs, stack traces with secrets
- Transient noise, debug output
- Credentials, tokens, internal IPs
- Giant binaries, temporary files
- Test alerts, maintenance notifications

### 🕐 **TTL Rules:**
- **Operational items:** 90 days (detections, incidents)
- **Documentation:** No expiry (code, playbooks)
- **Session notes:** 365 days
- **Temporary mitigations:** 30 days

---

## Decision Table: Embed vs Fine-Tune

| Need | Action | Example |
|------|--------|---------|
| New facts/docs/code | **Embed** (RAG) | API changes, new detections, runbooks |
| Tool-use format, JSON schema, "voice" | **Fine-tune** (LoRA) | Response templates, security refusals |
| Both | Fine-tune behavior + embed docs | New tool integration |

---

## Command Reference

### Daily Operations

```bash
# Check system status
make status

# Process session outcome  
python ai-training/rag/delta_indexing.py \
  --session-data session.json

# Test SOC ingestion
python ai-training/rag/soc_ingestion.py \
  --test-splunk critical_alert.json \
  --source splunk

# Run smoke evaluation
python ai-training/rag/delta_indexing.py --smoke-eval-only

# Full RAG evaluation
python ai-training/eval/run_eval.py \
  --base-model models/whis-base \
  --rag-config ai-training/configs/rag.yaml \
  --benchmarks security_qa
```

### Repository Changes

```bash
# Process code changes since last commit
python ai-training/rag/repo_ingestion.py \
  --since-commit abc123 \
  --output ai-training/rag/delta_chunks.json

# Hybrid retrieval test
python ai-training/rag/hybrid_retrieval.py \
  --query "How do I investigate lateral movement?" \
  --top-k 5 \
  --context "security_investigation"
```

### CI/CD Integration

```bash
# Git hook for automatic processing
# .git/hooks/post-receive
#!/bin/bash
python ai-training/ci/index_refresh.py \
  --trigger git_push \
  --since-commit $oldrev

# GitHub Actions workflow
# .github/workflows/rag-refresh.yml
on:
  push:
    branches: [main]
jobs:
  refresh-index:
    runs-on: ubuntu-latest
    steps:
      - name: Delta Index Refresh
        run: |
          python ai-training/ci/index_refresh.py \
            --trigger github_action
```

---

## Security Checklist

### 🔒 **Pre-Ingestion**
- [ ] PII/secrets redaction active
- [ ] Severity thresholds enforced (HIGH/CRITICAL only)
- [ ] Source system authentication verified
- [ ] Content sanitization applied
- [ ] Injection patterns neutralized

### 🛡️ **Processing**
- [ ] Delta indexing only (no full rebuilds)
- [ ] Versioned index pointers with rollback
- [ ] Smoke evals gate every promotion
- [ ] Query sanitization active
- [ ] Response schema validation

### 📊 **Monitoring**
- [ ] Citation coverage ≥ 95%
- [ ] RAGAS faithfulness ≥ 0.75
- [ ] P95 latency ≤ 3s
- [ ] Index freshness ≤ 5 min (sessions), ≤ 2 min (SOC)
- [ ] Access logs and audit trail

---

## SLOs & Thresholds

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| **Index Freshness** | Sessions ≤ 5min, SOC ≤ 2min | > 10min |
| **RAG Quality** | RAGAS ≥ 0.75 | < 0.70 |
| **Retrieval Rate** | Hit@5 ≥ 0.9 | < 0.8 |
| **Latency** | P95 ≤ 3s | > 5s |
| **Citation Coverage** | ≥ 95% | < 90% |
| **Rollback Time** | ≤ 30s | > 60s |

---

## Troubleshooting

### Index Not Updating
```bash
# Check delta processing state
cat ai-training/rag/.delta_state.json

# Manual delta processing
python ai-training/rag/delta_indexing.py \
  --session-data manual_session.json

# Check vector store health
python ai-training/cli/whis_status.py --health
```

### Poor Retrieval Quality
```bash
# Run full evaluation with details
python ai-training/eval/run_eval.py \
  --base-model models/whis-base \
  --rag-config ai-training/configs/rag.yaml \
  --benchmarks security_qa

# Check hybrid retrieval settings
python ai-training/rag/hybrid_retrieval.py \
  --query "test query" --debug

# Reindex with code-aware chunking
python ai-training/rag/repo_ingestion.py --force-reindex
```

### SOC Events Not Processing
```bash
# Check SOC ingestion state
cat ai-training/rag/.soc_state.json

# Test detection normalization
python ai-training/rag/soc_ingestion.py \
  --test-splunk sample_alert.json \
  --source splunk

# Check webhook endpoint
curl -X POST http://localhost:8000/webhooks/splunk \
  -H "Authorization: Bearer $WEBHOOK_TOKEN" \
  -d @test_payload.json
```

### Performance Issues
```bash
# Check system metrics
make metrics

# Optimize vector indexes
python -c "
import chromadb
client = chromadb.PersistentClient(path='ai-training/rag/hybrid_index')
for collection in client.list_collections():
    print(f'{collection.name}: {collection.count()} documents')
"

# Profile query performance
python ai-training/rag/hybrid_retrieval.py \
  --query "performance test" \
  --profile
```

---

## Monitoring Dashboard

### CLI Status
```bash
# Live dashboard (refreshes every 10s)
make status-live

# Health check with exit code
make health && echo "System healthy" || echo "Issues detected"

# Detailed adapter information
python ai-training/cli/whis_status.py \
  --adapter whis-soar:v20231201
```

### Key Metrics to Watch
- **Current Index Version:** Live vs staging pointers
- **Last Eval Scores:** RAGAS faithfulness, precision, recall
- **Processing Queue:** Sessions and SOC events pending
- **Error Rate:** Failed ingestions, evaluation failures
- **Storage Growth:** Vector store size trends

---

## Production Deployment Checklist

### Pre-Deployment
- [ ] All smoke evals passing ≥ 24 hours
- [ ] Full RAGAS evaluation score ≥ 0.75
- [ ] Security audit completed
- [ ] Performance benchmarks met
- [ ] Rollback procedure tested

### Deployment
- [ ] Index version promoted to staging
- [ ] Staging validation completed
- [ ] Traffic gradually shifted to new version
- [ ] Real-time monitoring active
- [ ] Rollback triggers configured

### Post-Deployment
- [ ] User acceptance testing
- [ ] Performance metrics within SLOs
- [ ] No regression in retrieval quality
- [ ] SOC ingestion processing normally
- [ ] Documentation updated

---

**This playbook enables senior-level ML operations with:**
- ✅ **Fast, incremental updates** (not full rebuilds)
- ✅ **Quality gates** preventing bad deployments
- ✅ **Real-time SOC integration** (summaries, not raw logs)
- ✅ **Comprehensive monitoring** and rollback capabilities
- ✅ **Security-first architecture** with sanitization and validation

Keep this operations guide as your single source of truth for running the WHIS SOAR-Copilot ML system in production.