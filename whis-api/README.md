# 🔒 Whis SOAR-Copilot API

Production-ready cybersecurity AI with frozen contracts and SIEM/EDR integrations.

## Quick Start

```bash
# Start minimal production API
cd apps/api
python whis_minimal_api.py

# Test frozen contracts
curl -X POST http://localhost:8003/explain \
  -H "Content-Type: application/json" \
  -d '{"event_data": {"search_name": "Suspicious Activity", "host": "server-01"}}'
```

## 🔒 Frozen API Contracts (v1.0)

### Core Endpoints
- `POST /explain` - Core SOAR explanation with Action Schema
- `POST /score` - Response quality evaluation  
- `POST /chat` - General SecOps conversation
- `POST /webhooks/splunk` - Inbound Splunk alert processing
- `POST /webhooks/limacharlie` - Inbound LimaCharlie detection processing

### Action Schema Contract (IMMUTABLE)
All `/explain` responses return this exact JSON structure:

```json
{
  "triage_steps": ["Step 1", "Step 2", "Step 3"],
  "containment": ["Action 1", "Action 2"], 
  "remediation": ["Fix 1", "Fix 2"],
  "mitre": ["T1055", "T1059.001"],
  "spl_query": "index=security | search suspicious_activity",
  "lc_rule": "event_type = \"SUSPICIOUS_PROCESS\"",
  "k8s_manifest": "apiVersion: v1\nkind: NetworkPolicy...",
  "validation_steps": ["Verify 1", "Verify 2"],
  "citations": ["Source 1", "Source 2"],
  "confidence": 0.85,
  "grounded": true
}
```

**Schema Validation**: 100% compliance required. Tests validate every field.

## Configuration

Set via environment variables:
- `SPLUNK_HEC_URL` / `SPLUNK_HEC_TOKEN` - HEC integration
- `LIMACHARLIE_OID` / `LIMACHARLIE_KEY` - EDR integration  

## Connectors

- **Splunk**: Alert → Whis → HEC enrichment pipeline
- **LimaCharlie**: EDR detection → Whis → Analysis pipeline
- **Action Schema**: Structured SOAR responses for all integrations

## Performance

- **Mega-model inference**: ~24 seconds first run, faster subsequent
- **Concurrent processing**: Full correlation ID tracking
- **Production ready**: Security headers, rate limiting, CORS configured