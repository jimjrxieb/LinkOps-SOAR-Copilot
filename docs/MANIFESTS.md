# Whis Knowledge Base Manifests

This document provides transparency into the knowledge sources used by Whis for cybersecurity analysis and response recommendations.

## Dataset Manifests

| ID | Title | Tags | Owner | Ingested | Source | Redaction | Hash |
|---|---|---|---|---|---|---|---|
| KB-ATTACK-T1110 | MITRE ATT&CK T1110 Brute Force | ATTACK:T1110, Authentication | whis-team | 2025-08-22 | mitre.org | PII:on | abc12345 |
| KB-WIN-4625 | Windows Event 4625 Analysis | Windows:4625, FailedLogon | whis-team | 2025-08-22 | microsoft.com | PII:on | def67890 |
| KB-SPLUNK-AUTH | Splunk Authentication Monitoring | Splunk, SIEM, Detection | whis-team | 2025-08-22 | splunk.com | PII:on | ghi34567 |
| KB-LC-DR | LimaCharlie D&R Rules | LimaCharlie, EDR, Response | whis-team | 2025-08-22 | limacharlie.io | PII:on | jkl89012 |

## Training Data Sources

| Dataset | Examples | Quality Score | Focus Area | Last Updated |
|---|---|---|---|---|
| Initial Cybersec Dataset | 23 | 0.85 | 4625/T1110 basics | 2025-08-22 |
| Expanded Dataset | 100 | 0.83 | Teacher/Assistant modes | 2025-08-22 |
| Preprocessed Dataset | 42 | 0.93 | Production quality | 2025-08-22 |

## Knowledge Retrieval Policy

### Teacher Mode
- **Retrieval**: k=6 chunks, require ≥2 distinct sources
- **Fallback**: Return "insufficient evidence" if source diversity too low
- **Citations**: Include source title + section + hash[:8]

### Assistant Mode  
- **Retrieval**: k=8 chunks, must include 1 ATT&CK + 1 tool chunk (Splunk/LC)
- **Fallback**: Generic response with disclaimer about source limitations
- **Citations**: Mandatory for all response actions

## Data Quality Standards

### Synthetic Data Only
- ✅ No real PII in training examples
- ✅ Redacted IP addresses (RFC 5737 ranges)
- ✅ Synthetic account names and hostnames
- ✅ Anonymized organizational references

### Content Standards
- ✅ Cybersecurity relevance score >0.65
- ✅ ATT&CK technique mapping where applicable  
- ✅ Technical accuracy validation
- ✅ Approval requirement flags for high-risk actions

## Security Controls

### Access Controls
- **Model Artifacts**: LoRA adapters only (no base weights)
- **API Keys**: Environment variables only (no hardcoded tokens)
- **Approval Gates**: All LimaCharlie actions require `approval_required: true`

### Audit Trail
- **Training Runs**: Full configuration logged in JSON
- **Validation Results**: Mentor criteria compliance tracking
- **Response Actions**: All Assistant mode outputs include approval workflow

## Compliance Notes

### GDPR/Privacy
- No personal data in training corpus
- Synthetic examples based on public security documentation
- User interaction logs anonymized

### Security Standards
- Follows NIST Cybersecurity Framework principles
- MITRE ATT&CK technique alignment verified
- SOC operational procedures compliance

---

**Last Updated**: 2025-08-22  
**Next Review**: Weekly during development  
**Maintainer**: Whis Development Team  
**Contact**: security-team@organization.local