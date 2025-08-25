# 🧠 RAG Shards - Knowledge Architecture

## Shard Strategy & Design

### Why Shards?
- **Performance**: Targeted retrieval reduces noise and latency
- **Governance**: Different freshness/quality requirements per domain  
- **Security**: Isolation prevents cross-domain information leakage
- **Maintenance**: Independent updates and rollbacks per shard

### Shard Architecture
```
pipelines/rag/
├── chunks/
│   ├── nist_core/          # NIST CSF, RMF, 800-series
│   ├── nist_delta/         # Framework updates & deltas
│   ├── vendor_task/        # Vendor-specific procedures  
│   ├── k8s_security/       # Kubernetes hardening
│   ├── siem_patterns/      # Detection rules & queries
│   └── guardpoint/         # Internal security tooling
├── vectorstore/
│   ├── nist_core.faiss     # FAISS index + metadata
│   ├── manifest.json       # Shard registry & versions
│   └── embeddings_config.yaml
└── scripts/
    ├── chunk.py            # Document → chunks pipeline
    ├── embed.py            # Chunks → vectors pipeline  
    └── validate.py         # Quality gates & freshness
```

## Shard Specifications

### 🏛️ **NIST Core Shard** (`nist_core`)
**Purpose**: Authoritative cybersecurity frameworks and controls
**Sources**: CSF 2.0, RMF, 800-53, 800-61, 800-137
**Chunk Size**: 512 tokens (control-level granularity)
**Freshness**: ≤ 48 hours from NIST publication
**Retrieval**: `k=6`, cosine threshold 0.3

**Metadata Schema**:
```yaml
framework: "CSF_2.0"
control_id: "ID.AM-1"  
category: "Identify"
subcategory: "Asset Management"
criticality: "high"
implementation_tier: [1, 2, 3, 4]
sector_applicability: ["all"]
last_updated: "2024-02-01"
```

**Quality Gates**:
- ✅ Control completeness: 100% of published controls indexed
- ✅ Cross-references resolved: Links to related controls functional
- ✅ Grounded rate: ≥ 95% (highest accuracy requirement)

### 🔄 **NIST Delta Shard** (`nist_delta`)  
**Purpose**: Framework updates, clarifications, and version deltas
**Sources**: NIST updates feed, revision notes, implementation guidance
**Chunk Size**: 256 tokens (change-focused granularity)
**Freshness**: ≤ 24 hours from publication
**Retrieval**: `k=4`, temporal boosting for recent changes

**Use Cases**:
- "What changed in CSF 2.0 from 1.1?"
- "Recent NIST guidance on zero trust"
- "Updated implementation examples"

### 🏢 **Vendor Task Shard** (`vendor_task`)
**Purpose**: Vendor-specific security procedures and configurations  
**Sources**: Azure Sentinel, Splunk Enterprise, CrowdStrike, Palo Alto
**Chunk Size**: 1024 tokens (procedure-level granularity)
**Freshness**: ≤ 7 days (vendor update cycles)
**Retrieval**: `k=8`, MMR enabled (diverse vendor perspectives)

**Security**: Summary-only indexing (no proprietary configs)
**CODEOWNERS**: Requires Architecture Team approval

### 🚢 **K8s Security Shard** (`k8s_security`)
**Purpose**: Kubernetes security hardening and policies
**Sources**: CIS benchmarks, NSA/CISA guidance, security policies
**Chunk Size**: 768 tokens (policy-level granularity)  
**Freshness**: ≤ 14 days
**Retrieval**: `k=6`, security-context boosting

**Artifact Types**:
- NetworkPolicies, PodSecurityPolicies
- RBAC configurations
- Admission controller configs
- Security scanning policies

### 🔍 **SIEM Patterns Shard** (`siem_patterns`)
**Purpose**: Detection rules, queries, and correlation patterns
**Sources**: Sigma rules, Splunk SPL, KQL queries, detection logic
**Chunk Size**: 384 tokens (rule-level granularity)
**Freshness**: ≤ 3 days (threat landscape velocity)
**Retrieval**: `k=10`, technique-based clustering

**Metadata Enhancement**:
```yaml
rule_type: "detection"
mitre_technique: "T1003.001"
platform: ["windows", "linux"]  
data_source: "process_creation"
severity: "high"
false_positive_rate: "low"
```

### 🛡️ **GuardPoint Shard** (`guardpoint`)
**Purpose**: Internal security tooling and procedures
**Sources**: Internal runbooks, tool configurations, incident procedures
**Chunk Size**: 640 tokens (procedure-level granularity)
**Freshness**: ≤ 1 day (operational requirements)
**Retrieval**: `k=5`, role-based filtering

**Security**: Highest classification, restricted access
**CODEOWNERS**: Security Team exclusive approval

## Retrieval Configuration

### Default Retrieval Pipeline
```yaml
strategy: "hybrid"           # BM25 + semantic vectors
rerank: true                 # Top 50 candidates
mmr_enabled: true           # Maximal marginal relevance  
cosine_floor: 0.25          # Minimum similarity threshold
temporal_boost: 0.1         # Recent content bonus
```

### Shard-Specific Tuning
```yaml
nist_core:
  k: 6
  cosine_threshold: 0.3     # High precision
  temporal_boost: 0.0       # Stability over recency
  
nist_delta:  
  k: 4
  cosine_threshold: 0.25    # Broader recall
  temporal_boost: 0.2       # Favor recent changes

vendor_task:
  k: 8  
  cosine_threshold: 0.2     # Cast wide net
  mmr_lambda: 0.7           # High diversity

siem_patterns:
  k: 10
  cosine_threshold: 0.2     # High recall for detection
  technique_boost: 0.15     # MITRE technique clustering
```

## Quality & Freshness Gates

### Automated Quality Checks
```bash
# Schema validation
python -m pipelines.rag.scripts.validate --schema

# Freshness audit  
python -m pipelines.rag.scripts.validate --freshness --max-age 180d

# Cross-reference integrity
python -m pipelines.rag.scripts.validate --links

# Embedding quality
python -m pipelines.rag.scripts.validate --embeddings --sample-size 100
```

### Quality Metrics Dashboard
- **Grounded Rate**: % queries with relevant chunks retrieved
- **Contradiction Rate**: % responses with conflicting information  
- **Coverage**: % NIST controls with indexed guidance
- **Staleness**: Median age of chunks per shard
- **Retrieval Latency**: p50/p95 search performance

### Freshness SLAs
| Shard | Max Age | Update Frequency | Degradation Alert |
|-------|---------|------------------|-------------------|
| nist_core | 180 days | On NIST publication | 90 days |
| nist_delta | 30 days | Daily scan | 14 days |  
| vendor_task | 90 days | Weekly refresh | 45 days |
| k8s_security | 60 days | Bi-weekly | 30 days |
| siem_patterns | 14 days | Daily | 7 days |
| guardpoint | 7 days | Real-time sync | 3 days |

## Chunking Strategy

### Chunk Boundaries
- **NIST Controls**: Natural control boundaries (ID.AM-1 complete)
- **Procedures**: Step-by-step task boundaries
- **Code**: Function or configuration block boundaries
- **Policies**: Policy statement or rule boundaries

### Chunk Metadata Template
```yaml
---
shard: "nist_core"
chunk_id: "CSF_ID_AM_1_chunk_001"
source_doc: "nist_csf_2.0.pdf" 
page_ref: [12, 13]
control_id: "ID.AM-1"
keywords: ["asset inventory", "hardware", "software"]
last_updated: "2024-02-01T10:00:00Z"
confidence_score: 0.95
---

# Asset Management (ID.AM-1)

The organization identifies and manages physical devices and systems within the organization...
```

### Overlap Strategy
- **15% overlap** between adjacent chunks for context preservation
- **Semantic boundaries** respected (don't split sentences mid-concept)
- **Cross-references** maintained with explicit chunk linking

## Operational Procedures

### Adding New Shards
1. **Plan**: Define shard purpose, sources, and quality gates
2. **Approve**: CODEOWNERS review for new shard creation
3. **Implement**: Create directory structure + configuration
4. **Validate**: Schema compliance + quality gate testing
5. **Deploy**: Gradual rollout with monitoring

### Shard Maintenance
- **Daily**: Freshness monitoring and delta detection
- **Weekly**: Quality metrics review and degradation alerts
- **Monthly**: Cross-shard consistency audit
- **Quarterly**: Shard performance optimization review

### Emergency Procedures
- **Quality Degradation**: Auto-rollback to last-known-good state
- **Freshness Violation**: Immediate re-indexing trigger
- **Cross-Contamination**: Shard isolation verification
- **Performance Issues**: Traffic routing to healthy shards

This shard architecture enables Whis SOAR to maintain high-quality, domain-specific knowledge retrieval while ensuring security, freshness, and operational excellence.