# 🧪 Golden Test Suite

Evaluation prompts and expected outputs for Whis SOAR-Copilot quality gates.

## Quick Start

```bash
# Run golden evaluation suite
cd tests/golden
python test_whis.py

# Run Kubernetes security tests  
python test_k8s_whis.py

# Check results
cat ../reports/evaluation_results_*.json
```

## Test Structure

Golden tests validate:
- ✅ **MITRE ATT&CK** technique mapping accuracy
- ✅ **Action Schema** compliance and completeness  
- ✅ **Triage steps** logical ordering and feasibility
- ✅ **Containment actions** appropriate for threat level
- ✅ **Kubernetes security** CKS-aligned recommendations

## Quality Gates

- **Overall score**: >0.8 required for production
- **Schema validation**: 100% compliance required
- **MITRE mapping**: >90% technique accuracy
- **Response time**: <30s for complex scenarios

## Reports

All evaluation results written to `../reports/` with timestamped JSON format. CI/CD gates check these scores before deployment.