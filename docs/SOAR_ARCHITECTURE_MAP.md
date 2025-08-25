# 🗺️ WHIS SOAR SYSTEM - TECHNICAL ARCHITECTURE MAP
*Clean, organized structure - no duplicates, easy navigation*

---

## 📁 PROJECT STRUCTURE (What Goes Where)

```
SOAR-copilot/
│
├── 📋 DOCUMENTATION (Start Here)
│   ├── SOAR_SYSTEM_OVERVIEW.md          ← Executive summary (for managers)
│   ├── SOAR_ARCHITECTURE_MAP.md         ← This file (technical roadmap)
│   ├── docs/
│   │   ├── ARCHITECTURE.md              ← System design details
│   │   ├── HOW_ENGINE.md                ← How the engine works
│   │   └── DATA_GOVERNANCE.md           ← Data handling policies
│   └── documentation/playbooks/
│       └── registry.yaml                 ← All runbook definitions (RB-101 to RB-501)
│
├── 🧠 CORE ENGINE
│   ├── apps/api/
│   │   ├── schemas.py                   ← Data models (IncidentEvent, SOARDecision, etc.)
│   │   ├── engines/
│   │   │   ├── decision_graph.yaml      ← Decision state machine (no code, just rules)
│   │   │   └── postcondition_verifier.py ← Verification system
│   │   └── legacy/connectors/
│   │       ├── splunk/webhook.py        ← Splunk alert ingestion
│   │       └── limacharlie/webhook.py   ← LimaCharlie alert ingestion
│
├── 🔧 AUTOMATION TOOLS
│   └── tools/mcp-tools/
│       ├── edr.py                       ← Endpoint tools (isolate, kill process, block hash)
│       ├── idp.py                       ← Identity tools (disable user, revoke tokens)
│       ├── network.py                   ← Network tools (block IP, block domains)
│       └── siem.py                      ← SIEM tools (search, gather context)
│
├── 🔒 SECURITY & CONFIG
│   └── ai-training/configs/
│       └── security.yaml                 ← Autonomy levels (L0-L3), safety gates, policies
│
├── 🧪 TESTING
│   └── tests/
│       ├── golden/                      ← Golden test sets
│       ├── e2e/                         ← End-to-end tests
│       └── security/                    ← Security validation
│
└── 🚀 LAUNCH SCRIPTS
    ├── LAUNCH-FULL-WHIS.sh              ← Production launch script
    └── scripts/
        └── start-integrated-api.sh       ← API server startup
```

---

## 🔄 DATA FLOW (How Information Moves)

```
1. ALERT INGESTION
   Splunk/LimaCharlie → Webhook → Normalizer → IncidentEvent
   
2. DECISION MAKING  
   IncidentEvent → Decision Graph → Category → Runbook Selection
   
3. SAFETY CHECKS
   Runbook → Autonomy Level Check → Safety Gates → Approval (if needed)
   
4. ACTION EXECUTION
   Approved Action → MCP Tool → Target System → Result
   
5. VERIFICATION
   Result → Postcondition Verifier → Success/Rollback
```

---

## 🎯 KEY COMPONENTS EXPLAINED

### 1️⃣ **Incident Normalization** (`apps/api/schemas.py`)
- **Purpose:** Convert different alert formats into standard structure
- **Input:** Splunk alerts, LimaCharlie detections
- **Output:** `IncidentEvent` with consistent fields
- **Why:** One format to rule them all

### 2️⃣ **Decision Graph** (`apps/api/engines/decision_graph.yaml`)
- **Purpose:** Deterministic incident classification
- **Input:** Normalized incident
- **Output:** Category + Runbook ID
- **Why:** No AI randomness, predictable decisions

### 3️⃣ **Runbook Registry** (`documentation/playbooks/registry.yaml`)
- **Purpose:** Define exact response procedures
- **Contents:** 6 runbooks (RB-101 to RB-501)
- **Each has:** Actions, preconditions, postconditions
- **Why:** Standardized, auditable responses

### 4️⃣ **MCP Tools** (`tools/mcp-tools/`)
- **Purpose:** Safe wrappers for dangerous operations
- **Features:** Dry-run, preconditions, rollback data
- **Tools:** EDR, Identity, Network, SIEM
- **Why:** Guardrails prevent disasters

### 5️⃣ **Security Config** (`ai-training/configs/security.yaml`)
- **Purpose:** Control what can be automated
- **Levels:** L0 (Shadow) → L3 (Manual)
- **Gates:** Blast radius, asset class, cooldowns
- **Why:** Progressive trust model

### 6️⃣ **Postcondition Verifier** (`apps/api/engines/postcondition_verifier.py`)
- **Purpose:** Verify actions worked
- **Checks:** Host isolated? User disabled? IP blocked?
- **Failure:** Triggers rollback
- **Why:** Ensure effectiveness

---

## 🚦 AUTOMATION LEVELS (Quick Reference)

| Level | Name | Can Execute? | Example Actions | Approval Needed? |
|-------|------|-------------|-----------------|------------------|
| **L0** | Shadow Mode | ❌ No | View recommendations only | Never |
| **L1** | Read-Only | ✅ Read only | SIEM searches, gather context | Never |
| **L2** | Conditional | ✅ With limits | Block external IP, isolate workstation | Sometimes |
| **L3** | Full Manual | ✅ All | Disable user, isolate servers | Always |

---

## 🛡️ SAFETY GATES (Preventing Disasters)

| Gate | Purpose | Example | Override |
|------|---------|---------|----------|
| **Blast Radius** | Limit scope | Max 10 hosts affected | Incident Commander |
| **Asset Class** | Protect critical | Domain Controllers need 2 people | Security Lead + Infra Lead |
| **Cooldown** | Prevent loops | Can't re-isolate for 15min | Emergency mode |
| **Business Hours** | Time restrictions | Critical changes need approval after 5pm | On-call approval |
| **Service Account** | Protect automation | Can't disable svc- accounts | 2-person override |

---

## 🔍 WHERE TO FIND THINGS

### "Where are the runbooks?"
→ `documentation/playbooks/registry.yaml`

### "Where are the automation tools?"
→ `tools/mcp-tools/` (edr.py, idp.py, network.py, siem.py)

### "Where is the decision logic?"
→ `apps/api/engines/decision_graph.yaml`

### "Where are the safety controls?"
→ `ai-training/configs/security.yaml`

### "Where do alerts come in?"
→ `apps/api/legacy/connectors/` (splunk/ and limacharlie/)

### "Where are the data models?"
→ `apps/api/schemas.py` (IncidentEvent, SOARDecision, etc.)

### "Where is verification?"
→ `apps/api/engines/postcondition_verifier.py`

---

## ✅ NO DUPLICATES GUARANTEE

Each component has **ONE** authoritative location:
- ✅ ONE incident schema (IncidentEvent)
- ✅ ONE decision graph
- ✅ ONE runbook registry  
- ✅ ONE security config
- ✅ ONE tool wrapper per service
- ✅ ONE verification system

---

## 🚀 QUICK START COMMANDS

```bash
# View executive overview (for managers)
cat SOAR_SYSTEM_OVERVIEW.md

# Check current autonomy level
grep "is_default: true" ai-training/configs/security.yaml

# List all runbooks
grep "^  RB-" documentation/playbooks/registry.yaml

# Test in shadow mode
./LAUNCH-FULL-WHIS.sh --shadow-mode

# View tool capabilities
ls -la tools/mcp-tools/
```

---

## 📊 SYSTEM HEALTH CHECKS

```bash
# Check if all components present
find . -name "decision_graph.yaml" | wc -l  # Should be 1
find . -name "registry.yaml" | wc -l         # Should be 1
find . -name "postcondition_verifier.py"     # Should exist

# Verify no duplicates
find . -name "*soar*" -name "*.py" | grep -v test | grep -v legacy
# Should only show core engine files, no duplicates
```

---

## 🎯 INTEGRATION POINTS

| External System | Integration File | Purpose |
|----------------|------------------|----------|
| **Splunk** | `connectors/splunk/webhook.py` | Receive alerts |
| **LimaCharlie** | `connectors/limacharlie/webhook.py` | Receive detections |
| **Azure AD** | `tools/mcp-tools/idp.py` | User management |
| **EDR (LC)** | `tools/mcp-tools/edr.py` | Endpoint control |
| **Firewall** | `tools/mcp-tools/network.py` | Network blocking |

---

## 📈 METRICS & MONITORING

- **Decisions:** Logged in decision_graph execution
- **Actions:** Tracked in tool execution logs
- **Verifications:** Recorded in postcondition reports
- **Rollbacks:** Captured with full context
- **Autonomy changes:** Audited in security.yaml history

---

*This architecture is designed for clarity, maintainability, and enterprise-grade security. Each component has a single responsibility and clear interfaces with others.*