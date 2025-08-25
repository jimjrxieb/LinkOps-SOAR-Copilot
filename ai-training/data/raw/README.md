# 📥 Drop Zone - Raw Data Intake

**This is where you drop your raw training materials.**

## 🎯 What to Put Here

### **🧠 LLM Training Data**
```bash
# Examples of files to drop here:
my_security_training.jsonl          # JSONL with instruction/response pairs
huggingface_security_dataset.json   # Downloaded HF datasets  
soar_playbook_examples.json         # Custom training examples
incident_response_data.jsonl        # Real-world IR scenarios
```

### **📚 RAG Knowledge**
```bash  
# Knowledge base materials:
mitre_attack_framework.md           # MITRE ATT&CK documentation
security_playbooks.md               # Incident response playbooks
nist_cybersecurity_framework.txt    # Compliance frameworks
threat_intelligence_reports.md      # Threat intel for context
```

### **🧪 Test Scenarios** 
```bash
# Validation data:
security_test_scenarios.csv         # Test cases for validation
golden_set_responses.json           # Expected model outputs
benchmark_datasets.jsonl            # Industry benchmarks
```

## ⚡ Quick Demo

Drop a sample file to test the system:

```json
// sample_training.jsonl
{"instruction": "A user reports suspicious email with attachment 'invoice.exe'. What should I do?", "response": "1. DO NOT open the attachment. 2. Isolate the user's workstation immediately. 3. Report to IT security team. 4. Scan the email headers for IOCs. 5. Check for similar emails in organization.", "category": "phishing_response"}
{"instruction": "PowerShell process spawned by Word document detected. Immediate actions?", "response": "1. Kill the PowerShell process immediately. 2. Isolate the affected machine from network. 3. Collect forensic image of memory and disk. 4. Check for persistence mechanisms. 5. Scan for lateral movement indicators.", "category": "malware_response"}
```

## 🔄 Processing Flow

1. **Drop files here** → Automatic detection
2. **Run preprocessing notebook** → Data validation & sanitization  
3. **Routed to pipelines** → LLM, RAG, or Testing
4. **Original files archived** → Moved to `archive/` subfolder

## 📊 File Support

| Extension | Type | Pipeline Route |
|-----------|------|----------------|
| `.jsonl`, `.json` | Training data | → LLM Pipeline |
| `.md`, `.txt` | Knowledge docs | → RAG Pipeline |  
| `.csv`, `.xlsx` | Test scenarios | → Testing Pipeline |
| `.zip` | HF datasets | → Auto-extract & route |

**🚨 Security**: All data is automatically sanitized (PII removal, validation, content filtering) before processing.