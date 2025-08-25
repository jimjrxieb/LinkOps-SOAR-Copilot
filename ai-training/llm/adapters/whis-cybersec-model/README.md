---
license: llama2
base_model: codellama/CodeLlama-7b-Instruct-hf
tags:
- cybersecurity
- soar
- security-automation
- incident-response
- lora
- peft
library_name: peft
---

# Whis Cybersecurity SOAR Copilot

A specialized cybersecurity copilot fine-tuned for Security Orchestration, Automation & Response (SOAR) tasks.

## Model Details

- **Base Model**: CodeLlama-7B-Instruct
- **Fine-tuning Method**: LoRA (Low-Rank Adaptation)
- **Trainable Parameters**: 16,777,216 (16.7M)
- **Training Examples**: 23 cybersecurity scenarios
- **Training Duration**: 20 seconds
- **Final Loss**: 1.944

## Capabilities

- **Teacher Mode**: Educational cybersecurity explanations with MITRE ATT&CK references
- **Assistant Mode**: Automated SOAR playbook generation and incident response
- **RAG Integration**: Enhanced with cybersecurity knowledge base
- **Multi-domain**: Windows Events, Splunk SIEM, LimaCharlie EDR, Threat Intelligence

## Usage

```python
from peft import PeftModel, PeftConfig
from transformers import AutoModelForCausalLM, AutoTokenizer

# Load the model
config = PeftConfig.from_pretrained("jimjrxieb/whis-cybersec-soar-copilot")
base_model = AutoModelForCausalLM.from_pretrained(config.base_model_name_or_path)
model = PeftModel.from_pretrained(base_model, "jimjrxieb/whis-cybersec-soar-copilot")
tokenizer = AutoTokenizer.from_pretrained(config.base_model_name_or_path)

# Generate response
prompt = "Explain MITRE ATT&CK T1110.004 with detection strategies"
inputs = tokenizer(prompt, return_tensors="pt")
outputs = model.generate(**inputs, max_length=512)
response = tokenizer.decode(outputs[0], skip_special_tokens=True)
```

## Training Data

Trained on specialized cybersecurity scenarios including:
- Authentication attack responses
- MITRE ATT&CK technique explanations  
- SOAR playbook automation
- Threat intelligence analysis
- Incident response procedures

## License

Licensed under Llama 2 Community License.
