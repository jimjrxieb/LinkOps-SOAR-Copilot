# 🏗️ WHIS SOAR Architecture & Implementation Guide

## Architecture Tags & Components

### [TAG: SCHEMAS] - Contract Definitions
**Location:** `ai-training/use_schema.json`  
**Owner:** Platform Team  
**Status:** 🟡 In Progress

```yaml
Components:
  - ChatRequest/Response: Core AI interaction schemas
  - IncidentSummary: Normalized security incident format
  - DetectionSummary: SIEM/EDR detection normalization
  - PlaySpec: Playbook specification schema
  - PlayRun: Execution tracking schema
  - PlayResult: Execution result schema
  - PlaywrightTask: Browser automation task schema
  - ToolError: Standardized error format
```

**Acceptance Criteria:**
- [ ] All schemas render in `/docs` endpoint
- [ ] Invalid payloads return `{error:{code,message,fields}}`
- [ ] Version tracking for schema evolution

---

### [TAG: ERROR-SHAPE] - Unified Error Handling
**Location:** `apps/api/utils/errors.py`  
**Owner:** API Team  
**Status:** 🔴 Not Started

```yaml
Error Format:
  {
    "error": {
      "code": "string",  # Machine-readable error code
      "message": "string",  # Human-readable message
      "fields": {},  # Field-specific errors
      "trace_id": "string"  # Correlation ID
    }
  }
```

**Acceptance Criteria:**
- [ ] Fuzz tests show consistent errors across all endpoints
- [ ] No stack traces in production errors
- [ ] Error codes documented in API spec

---

### [TAG: INTAKE] - SOC Data Ingestion
**Location:** `soar-platform/ingestion/soc_intake.py`  
**Owner:** Integrations Team  
**Status:** 🟡 In Progress

```yaml
Connectors:
  Splunk:
    - Method: HEC token via secret store
    - Queries: Parameterized search templates
    - Sanitization: PII/secret redaction
    
  LimaCharlie:
    - Method: Event webhooks/stream
    - Mapping: To DetectionSummary schema
    - Deduplication: By event_id + timestamp
```

**Acceptance Criteria:**
- [ ] Sample events flow to `data/staging/soc/`
- [ ] Governance failures rejected with audit log
- [ ] ATT&CK/TLP metadata attached

---

### [TAG: SUMMARIZE] - Incident Summarization
**Location:** `soar-platform/engines/summarizer.py`  
**Owner:** ML Team  
**Status:** 🔴 Not Started

```yaml
Pipeline:
  1. Ingest raw detection/alert
  2. Extract: what/where/when/why
  3. Enrich: ATT&CK techniques, IOCs
  4. Generate: IncidentSummary
  5. Store: RAG chunks + structured JSON
```

**Acceptance Criteria:**
- [ ] RAG smoke eval ≥ 0.75 RAGAS on SOC summaries
- [ ] Hit@5 ≥ 0.85 for playbook recommendations
- [ ] Summaries include evidence citations

---

### [TAG: SLACK-APP] - Slack Integration
**Location:** `soar-platform/integrations/slack_orchestrator.py`  
**Owner:** Frontend Team  
**Status:** ✅ Implemented (needs tags)

```yaml
Features:
  - OAuth: Bot/user tokens via secret store
  - Events: message.im, app_mention, shortcuts, slash
  - Commands: /whis, /playbook
  - Interactions: Buttons for approve/reject/investigate
```

**Acceptance Criteria:**
- [ ] `/whis` opens validated modal
- [ ] Ephemeral responses for sensitive data
- [ ] Rate limiting with backoff

---

### [TAG: DSL] - Playbook Definition Language
**Location:** `soar-platform/playbooks/schema.yaml`  
**Owner:** Security Team  
**Status:** 🔴 Not Started

```yaml
PlaySpec:
  meta:
    name: string
    description: string
    severity: [low, medium, high, critical]
    mitre_techniques: [string]
    
  inputs:
    - name: string
      type: [string, number, boolean, object]
      required: boolean
      validation: string  # JSONSchema
      
  prechecks:
    - type: [query_splunk, query_lc, check_permission]
      condition: string  # Expression
      
  steps:
    - id: string
      type: [query_splunk, query_lc, open_ticket, notify_slack, run_playwright]
      params: object
      on_failure: [continue, stop, rollback]
      requires_approval: boolean
      
  rollback:
    - step_id: string
      action: object
      
  safety:
    max_duration: number  # seconds
    dry_run_required: boolean
    approval_roles: [string]
```

---

### [TAG: RUNNER] - Playbook Execution Engine
**Location:** `soar-platform/engines/play_runner.py`  
**Owner:** Platform Team  
**Status:** 🔴 Not Started

```yaml
Modes:
  - plan: Generate execution plan only
  - dry-run: No side effects, validate all steps
  - execute: Run with approvals and audit
  - rollback: Compensate failed execution

Guarantees:
  - Idempotency keys prevent duplicate runs
  - Per-step timeouts with compensation
  - Full audit trail with decision history
  - Kill-switch for emergency stop
```

**Acceptance Criteria:**
- [ ] Kill-switch stops plays within 5 seconds
- [ ] Dry-run validates without side effects
- [ ] Audit logs include who/what/when/why

---

### [TAG: SANDBOX] - Playwright Security Sandbox
**Location:** `soar-platform/sandbox/playwright_runner.py`  
**Owner:** Security Team  
**Status:** 🔴 Not Started

```yaml
Security Controls:
  - Container: Ephemeral, read-only filesystem
  - Network: Domain allowlist only
  - Resources: CPU/memory limits
  - Secrets: Via environment, never logged
  - Artifacts: PII redacted before storage
```

**Acceptance Criteria:**
- [ ] Non-allowlisted domains blocked + audited
- [ ] 10 concurrent tasks stay within limits
- [ ] No secret leakage in logs/artifacts

---

### [TAG: TOOLS] - WHIS Tool Library
**Location:** `soar-platform/tools/`  
**Owner:** API Team  
**Status:** 🟡 Partial

```yaml
Available Tools:
  - query_splunk(params): Read-only Splunk queries
  - query_limacharlie(params): Read-only EDR queries
  - run_play(name, inputs, mode): Execute playbook
  - open_ticket(system, fields): Create ticket
  - run_playwright(task): Browser automation
  
Returns: Typed results or ToolError
```

---

### [TAG: LIBRARY SEED] - Initial Playbook Library
**Location:** `soar-platform/playbooks/library/`  
**Owner:** SOC Team  
**Status:** 🔴 Not Started

```yaml
Seed Playbooks:
  1. ransomware_triage.yaml
  2. phishing_response.yaml
  3. c2_beacon_hunt.yaml
  4. credential_stuffing.yaml
  5. web_deface_response.yaml
  6. suspicious_admin_login.yaml
```

---

### [TAG: METRICS] - Observability
**Location:** `soar-platform/monitoring/metrics.py`  
**Owner:** SRE Team  
**Status:** 🔴 Not Started

```yaml
Key Metrics:
  - soar_play_runs_total{status}
  - play_step_latency_ms
  - tool_error_total{tool}
  - rag_quality_score
  - slack_rate_limit_hits
  - sandbox_resource_usage
```

---

### [TAG: AUDIT] - Compliance & Audit Trail
**Location:** `soar-platform/audit/logger.py`  
**Owner:** Compliance Team  
**Status:** 🔴 Not Started

```yaml
Audit Events:
  - Play execution (plan/dry-run/execute/rollback)
  - Approvals (who/when/decision/reason)
  - Tool invocations (params/results)
  - Access attempts (success/failure)
  - Configuration changes
```

---

## Implementation Priority

### Phase 1: Foundation (Week 1-2)
1. [SCHEMAS] - Define all contracts
2. [ERROR-SHAPE] - Unified error handling
3. [DSL] - Playbook schema definition

### Phase 2: Integration (Week 3-4)
1. [INTAKE] - SOC data ingestion
2. [SUMMARIZE] - Incident summarization
3. [TOOLS] - Tool library implementation

### Phase 3: Execution (Week 5-6)
1. [RUNNER] - Play execution engine
2. [SANDBOX] - Playwright security
3. [LIBRARY SEED] - Initial playbooks

### Phase 4: Production (Week 7-8)
1. [METRICS] - Full observability
2. [AUDIT] - Compliance logging
3. [KILL-SWITCH] - Emergency controls

---

## Security Checklist

- [ ] Input validation (schemas) for all REST/WS/tool calls
- [ ] No secrets/PII in logs or indexes
- [ ] Splunk/LC/Ticket tokens least-privilege
- [ ] Play runner with dry-run, approvals, RBAC
- [ ] Playwright sandboxed with allowlist
- [ ] Prompt-injection neutralization
- [ ] Metrics & alerts for all components
- [ ] SBOM + dependency scans clean

---

## Success Metrics

- **RAG Quality:** RAGAS ≥ 0.75, Hit@5 ≥ 0.85
- **Play Success Rate:** ≥ 90% completion
- **Tool Reliability:** < 1% error rate
- **Response Time:** P95 < 3s for decisions
- **Approval Latency:** < 5 min average
- **Sandbox Safety:** 0 breakouts

---

## Next Steps

1. **Request golden eval set specs** for:
   - Play planning (10-15 questions)
   - SOC summarization (10-15 questions)
   - Slack workflow etiquette (10-15 questions)
   - Agentic testing scenarios (10-15 questions)

2. **Request DSL schema** for Plays library implementation

3. **Begin Phase 1** implementation with SCHEMAS and ERROR-SHAPE