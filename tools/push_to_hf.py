#!/usr/bin/env python3
"""
Push Whis trained model to Hugging Face Hub
"""

from huggingface_hub import HfApi, create_repo
import os
from pathlib import Path

# Configuration
MODEL_PATH = "./whis-cybersec-model"
REPO_NAME = "whis-cybersec-soar-copilot"
REPO_ID = f"jimjrxieb/{REPO_NAME}"

print("🚀 PUSHING WHIS MODEL TO HUGGING FACE HUB")
print("=" * 50)

# Initialize HF API
api = HfApi()

# Check if model exists
if not os.path.exists(MODEL_PATH):
    print(f"❌ Model not found at {MODEL_PATH}")
    exit(1)

print(f"📦 Model found at: {MODEL_PATH}")
print(f"🎯 Target repo: {REPO_ID}")

try:
    # Create repository if it doesn't exist
    print("\n📝 Creating repository...")
    create_repo(
        repo_id=REPO_ID,
        repo_type="model",
        exist_ok=True,
        private=False
    )
    print("✅ Repository created/verified")
    
    # Create model card
    model_card = f"""---
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
config = PeftConfig.from_pretrained("{REPO_ID}")
base_model = AutoModelForCausalLM.from_pretrained(config.base_model_name_or_path)
model = PeftModel.from_pretrained(base_model, "{REPO_ID}")
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
"""

    # Save model card
    with open(os.path.join(MODEL_PATH, "README.md"), "w") as f:
        f.write(model_card)
    
    # Upload entire model folder
    print("📤 Uploading model files...")
    api.upload_folder(
        folder_path=MODEL_PATH,
        repo_id=REPO_ID,
        repo_type="model",
        commit_message="Initial upload of Whis cybersecurity SOAR copilot LoRA adapter"
    )
    
    print(f"✅ SUCCESS! Model uploaded to: https://huggingface.co/{REPO_ID}")
    
except Exception as e:
    print(f"❌ Upload failed: {e}")
    raise e