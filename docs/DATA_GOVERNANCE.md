# 📊 Data Governance - Whis SOAR

## Data Flow & Classification

### Classification Levels
- **P1 (Public)**: NIST frameworks, public CVEs, open-source docs
- **P2 (Internal)**: Company security policies, internal runbooks
- **P3 (Confidential)**: Customer data, proprietary methodologies, access credentials

### Data Lanes & Security Gates

```
┌─────────────┐  Secret Scan   ┌─────────────┐  PII Redaction ┌─────────────┐
│   INTAKE    │───────────────▶│  SANITIZE   │───────────────▶│   CURATE    │
│ (untrusted) │     GATE 1     │ (cleaned)   │     GATE 2     │ (approved)  │
└─────────────┘                └─────────────┘                └─────────────┘
       │                              │                              │
    📋 Manifest                   📋 Redaction Log              📋 Approval Log
```

## Lane-by-Lane Governance

### 🚪 **Intake Lane** - Zero Trust Input
**Location**: `data/intake/`
**Sources**: NIST feeds, vendor docs, GuardPoint exports, security blogs
**Security Gates**:
- ✅ Entropy-based secret detection (fail on API keys, tokens)
- ✅ License validation (NIST=public, vendor=summary-only)
- ✅ Content-type whitelisting (PDF, HTML, MD, JSONL only)
- ✅ Size limits (max 100MB per file)

**Manifest Schema** (`data/manifests/intake_<src>_<ts>.json`):
```json
{
  "source": "nist_csf_2.0",
  "license": "public_domain",
  "owner": "security_team",
  "doc_date": "2024-02-01",
  "hash_sha256": "abc123...",
  "bytes": 1048576,
  "content_type": "application/pdf",
  "confidentiality": "P1",
  "provenance": "https://nist.gov/csf/2.0/download"
}
```

**Prohibited Content**:
- ❌ Executable files or scripts
- ❌ API keys, passwords, certificates
- ❌ PII (emails, SSNs, addresses)
- ❌ Customer-specific configurations

### 🧹 **Sanitize Lane** - PII & Security Scrubbing
**Location**: `data/staging/`
**Purpose**: Make data safe for ML training and RAG indexing

**PII Redaction Rules**:
- Email addresses → `[REDACTED:EMAIL]`
- Phone numbers → `[REDACTED:PHONE]`
- IP addresses → `10.0.1.X` (preserve network context)
- Domain names → `example.local` (preserve structure)
- User IDs → `${USER_ID}` (parameterized)

**Secret Detection Patterns**:
- API keys (AWS, Azure, GCP patterns)
- Private keys (PEM blocks)
- Database connection strings
- JWT tokens and bearer tokens

**Prompt Injection Scrubbing**:
- Remove "ignore previous instructions"
- Strip executable directives unless marked as code samples
- Neutralize social engineering attempts

**Quality Gates**:
- ✅ Zero P3 data allowed to pass
- ✅ PII redaction count logged for audit
- ✅ Before/after diff samples saved for spot-checking

### ✅ **Curate Lane** - Human Approval & Labeling
**Location**: `data/curated/`
**Purpose**: Human-validated, domain-labeled training data

**Domain Labels**:
- `nist_core`: Core NIST framework controls
- `nist_delta`: Framework updates and deltas  
- `vendor_task`: Vendor-specific procedures
- `k8s`: Kubernetes security configs
- `siem`: SIEM rules and queries
- `guardpoint`: Internal security tooling

**CODEOWNERS Requirements**:
- `guardpoint/*` requires Security Team approval
- `vendor_task/*` requires Architecture Team approval
- `k8s/*` requires Platform Team approval

**Metadata Enhancement**:
```json
{
  "domain": "nist_core",
  "framework": "CSF_2.0", 
  "control_id": "ID.AM-1",
  "provider": "internal",
  "stability": "stable",
  "doc_date": "2024-02-01",
  "mitre_techniques": ["T1003.001", "T1059.001"],
  "criticality": "high"
}
```

## Data Retention & Lifecycle

### Retention Policies
- **Intake**: 90 days (compliance window)
- **Staging**: 180 days (reprocessing buffer) 
- **Curated**: 2 years (training history)
- **Manifests**: Permanent (audit trail)

### Freshness Requirements
- **NIST frameworks**: Updates within 48 hours
- **Vendor docs**: Monthly refresh cycle
- **Internal procedures**: Weekly sync from GuardPoint
- **Threat intelligence**: Daily feeds

### Data Quality SLAs
- **Grounded Rate**: ≥ 90% (RAG retrieval accuracy)
- **Contradiction Rate**: ≤ 3% (conflicting guidance)
- **Coverage**: ≥ 95% NIST controls represented
- **Staleness**: ≤ 180 days for core frameworks

## Compliance & Auditing

### Audit Trails
Every data transformation creates immutable audit logs:
```json
{
  "correlation_id": "uuid4",
  "timestamp": "2024-02-01T10:00:00Z",
  "lane": "sanitize",
  "input_hash": "abc123...",
  "output_hash": "def456...", 
  "transformations": ["pii_redacted", "secrets_scrubbed"],
  "redaction_count": 3,
  "approver": "security_team"
}
```

### Privacy Controls
- **Data Minimization**: Only security-relevant content processed
- **Purpose Limitation**: Data used solely for security automation
- **Consent**: Internal data governance approval required
- **Subject Rights**: Redaction logs enable data subject requests

### Security Reviews
- **Monthly**: Data classification accuracy review
- **Quarterly**: PII/secret redaction effectiveness audit  
- **Annually**: Full data governance policy review
- **Ad-hoc**: Incident-triggered security assessment

## Data Governance CLI

### Quick Commands
```bash
# Validate manifest schemas
python -m tools.data_governance validate --manifest data/manifests/

# Run PII detection scan
python -m tools.data_governance scan-pii --input data/staging/

# Generate compliance report
python -m tools.data_governance report --output reports/

# Audit data lineage
python -m tools.data_governance lineage --trace-id <uuid>
```

### Emergency Procedures
- **Data Breach**: Immediate intake freeze + forensics
- **PII Exposure**: Automated redaction + notification
- **License Violation**: Content quarantine + legal review
- **Quality Degradation**: Rollback to last-known-good state

This governance framework ensures Whis SOAR maintains security, privacy, and quality standards while enabling AI/ML operations at scale.