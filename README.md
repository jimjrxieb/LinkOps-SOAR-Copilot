# Whis: SOAR Copilot

**Teacher & Assistant for Security Operations**

## 🧠 Vision

Whis is a SOAR Copilot that serves dual roles:
- **🎓 Teacher**: Explains logs, correlates with ATT&CK framework, shares IR best practices
- **🤖 Assistant**: Drafts response actions, routes playbooks, enriches detections (human-approved)

**Operating Model**: *Explain → Propose → Approve → Execute (SOAR) → Enrich back to SIEM → Learn*

## 🎯 Stack Clarity

- **SIEM (Splunk)**: Data lake + search engine
- **EDR/XDR (LimaCharlie)**: Signal generation + attack replay
- **SOAR**: Execution guardrails + workflow orchestration  
- **Whis**: Reasoning layer + enrichment engine

## 🔄 Core Capabilities

### 🎓 Teacher Mode
- **ATT&CK Correlation**: Maps events to MITRE techniques (T1110, etc.)
- **False Positive Analysis**: Explains common noise patterns
- **Threshold Guidance**: Recommends detection tuning
- **Best Practice Sharing**: IR playbook education

### 🤖 Assistant Mode  
- **Detection Enrichment**: Context + threat intel overlay
- **Playbook Routing**: Suggests appropriate response workflows
- **Action Drafting**: Prepares LC queries, Slack updates
- **Human-in-the-Loop**: All actions require approval

## 🏗️ Data Flow Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   LimaCharlie   │───▶│      Whis       │───▶│     Splunk      │
│   (Detections)  │    │   (Reasoning)   │    │  (Enrichment)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       ▼                       │
         │              ┌─────────────────┐               │
         │              │ Knowledge Base  │               │
         │              │ ATT&CK/NIST/CIS │               │
         │              │ IR Playbooks    │               │
         │              │ Compliance      │               │
         │              └─────────────────┘               │
         │                       │                       │
         └──────────────────────▶│◀──────────────────────┘
                                 ▼
                    ┌─────────────────────────┐
                    │ Human Approval Gateway  │
                    │ (RBAC + Audit Trail)    │
                    └─────────────────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │     SOAR Execution      │
                    │   (Guardrails Active)   │
                    └─────────────────────────┘
```

## 🎯 Integration Flows

### LC → Whis → Splunk
1. **LimaCharlie** sends detection via webhook
2. **Whis** enriches with ATT&CK mapping + context  
3. **Splunk HEC** receives enriched event as `whis:enrichment`

### Whis Teacher Flow (4625 Example)
1. **Input**: Multiple 4625 failed logon events
2. **Explain**: "This maps to ATT&CK T1110 (Brute Force)"
3. **Educate**: "Common false positives: service accounts, time sync"
4. **Recommend**: "Threshold: >5 failures/5min, exclude known service accounts"

### Whis Assistant Flow  
1. **Detect**: Confirmed brute force attempt
2. **Propose**: "Execute playbook: Account Lockdown + User Notification"
3. **Route**: Present LC containment actions + Slack alert draft
4. **Approve**: Human reviews and authorizes
5. **Execute**: SOAR runs approved actions
6. **Enrich**: Results flow back to Splunk for correlation

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/jimjrxieb/LinkOps-SOAR-Copilot.git
cd LinkOps-SOAR-Copilot

# Setup development environment
make setup

# Start services
make dev
```

## 📋 Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Node.js 18+
- Splunk Universal Forwarder (for data ingestion)
- LimaCharlie API credentials

## 🔧 Configuration

Create your environment configuration:

```bash
cp .env.example .env
# Edit .env with your credentials
```

## 📚 Documentation

- [Installation Guide](docs/installation.md)
- [Configuration](docs/configuration.md)
- [Playbook Development](docs/playbooks.md)
- [API Reference](docs/api.md)
- [Security Best Practices](docs/security.md)

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🏢 LinkOps Industries

Built with ❤️ by the LinkOps Industries team for the cybersecurity community.

---

**⚠️ Security Notice**: This tool handles sensitive security data. Always follow your organization's security policies and ensure proper access controls are in place.