#!/usr/bin/env python3
"""
Push Whis LoRA Adapter to HuggingFace Hub
Security-compliant upload of only LoRA weights (no base model)
"""

import os
import json
from pathlib import Path
from datetime import datetime
from huggingface_hub import HfApi, create_repo, upload_folder
from huggingface_hub.utils import RepositoryNotFoundError

class WhisHFUploader:
    """Secure HuggingFace Hub uploader for Whis LoRA adapters"""
    
    def __init__(self, model_name: str = "whis-cybersec-lora"):
        self.model_name = model_name
        self.api = HfApi()
        self.repo_id = None
        
    def validate_lora_only(self, model_dir: Path) -> dict:
        """Ensure only LoRA adapters are present (security requirement)"""
        print("🔒 Validating LoRA-only policy...")
        
        # Files that should be present (LoRA adapter)
        allowed_files = [
            "adapter_model.safetensors",
            "adapter_config.json", 
            "adapter_model.bin",
            "tokenizer.json",
            "tokenizer_config.json",
            "special_tokens_map.json",
            "README.md",
            "training_log.json"
        ]
        
        # Files that should NOT be present (base model weights)
        forbidden_files = [
            "pytorch_model.bin",
            "model.safetensors",
            "pytorch_model-*.bin",
            "model-*.safetensors"
        ]
        
        validation_result = {
            "lora_files_found": [],
            "forbidden_files_found": [],
            "validation_passed": True,
            "total_size_mb": 0
        }
        
        # Check for LoRA files
        for pattern in allowed_files:
            if "*" in pattern:
                matches = list(model_dir.glob(pattern))
            else:
                matches = [model_dir / pattern] if (model_dir / pattern).exists() else []
            
            for match in matches:
                if match.exists():
                    size_mb = match.stat().st_size / (1024 * 1024)
                    validation_result["lora_files_found"].append({
                        "file": match.name,
                        "size_mb": round(size_mb, 2)
                    })
                    validation_result["total_size_mb"] += size_mb
        
        # Check for forbidden files
        for pattern in forbidden_files:
            if "*" in pattern:
                matches = list(model_dir.glob(pattern))
            else:
                matches = [model_dir / pattern] if (model_dir / pattern).exists() else []
            
            for match in matches:
                if match.exists():
                    validation_result["forbidden_files_found"].append(match.name)
                    validation_result["validation_passed"] = False
        
        validation_result["total_size_mb"] = round(validation_result["total_size_mb"], 2)
        
        if not validation_result["validation_passed"]:
            print(f"❌ Base model files detected: {validation_result['forbidden_files_found']}")
            print("🚫 Upload blocked - only LoRA adapters allowed")
        else:
            print(f"✅ LoRA-only validation passed")
            print(f"📦 Total size: {validation_result['total_size_mb']} MB")
            print(f"📁 Files: {[f['file'] for f in validation_result['lora_files_found']]}")
        
        return validation_result
    
    def create_model_card(self, model_dir: Path, training_config: dict = None) -> str:
        """Create comprehensive model card"""
        
        model_card = f"""---
license: llama2
base_model: codellama/CodeLlama-7b-Instruct-hf
tags:
- cybersecurity
- soar
- security-operations
- lora
- peft
datasets:
- custom-cybersec-dataset
language:
- en
pipeline_tag: text-generation
---

# Whis Cybersecurity SOAR Copilot - LoRA Adapter

## Model Description

Whis is a specialized cybersecurity SOAR (Security Orchestration, Automation & Response) copilot fine-tuned from CodeLlama-7B-Instruct. This model operates in two modes:

- **Teacher Mode**: Explains security events with educational context, MITRE ATT&CK mapping, and detection guidance
- **Assistant Mode**: Proposes response actions and routes to playbooks with human approval requirements

## Training Details

- **Base Model**: CodeLlama-7B-Instruct-hf  
- **Fine-tuning Method**: LoRA (Low-Rank Adaptation)
- **Training Data**: Cybersecurity-focused examples covering SIEM, EDR, MITRE ATT&CK
- **Optimization**: 4-bit quantization with bfloat16 compute
- **Safety**: All LimaCharlie actions require `approval_required: true`

## Usage

This is a LoRA adapter that must be loaded with the base CodeLlama model:

```python
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

# Load base model
base_model = AutoModelForCausalLM.from_pretrained("codellama/CodeLlama-7b-Instruct-hf")
tokenizer = AutoTokenizer.from_pretrained("codellama/CodeLlama-7b-Instruct-hf")

# Load LoRA adapter
model = PeftModel.from_pretrained(base_model, "linkops/whis-cybersec-lora")
```

## Example Prompts

### Teacher Mode
```
Explain Windows Event **4625**. Return (1) meaning & key fields (**LogonType, AccountName, IpAddress**), (2) common false positives, (3) escalation threshold. Map to **MITRE ATT&CK T1110** and cite sources.
```

### Assistant Mode  
```
Assistant mode: we saw repeated 4625s indicating brute force. Return four sections:
1. **detection_outline** (SIEM-agnostic + one Splunk SPL example),  
2. **playbook_choice** with **preconditions** & **rollback**,
3. **limacharlie_actions** with **approval_required: true**,
4. **team_update** (Slack-ready). Include citations.
```

## Security & Compliance

- ✅ Only LoRA adapter weights (no base model redistribution)
- ✅ All training data PII-redacted with synthetic examples
- ✅ Approval gates required for all high-risk actions
- ✅ MITRE ATT&CK technique mapping for transparency

## Limitations

- Requires human approval for all LimaCharlie EDR actions
- Knowledge cutoff based on training data
- Should not be used for fully autonomous security operations

## Training Configuration

{json.dumps(training_config or {{}}, indent=2) if training_config else "Training configuration not available"}

## Citation

```bibtex
@misc{{whis-cybersec-lora,
  title={{Whis Cybersecurity SOAR Copilot}},
  author={{LinkOps Industries}},
  year={{2025}},
  url={{https://huggingface.co/linkops/whis-cybersec-lora}}
}}
```

## Developed By

LinkOps Industries - Cybersecurity AI Research Team

Created: {datetime.now().strftime("%Y-%m-%d")}
"""
        
        return model_card
    
    def prepare_upload_directory(self, model_dir: Path) -> Path:
        """Prepare clean upload directory with only necessary files"""
        upload_dir = Path("./hf_upload_staging")
        upload_dir.mkdir(exist_ok=True)
        
        # Clear previous staging
        import shutil
        if upload_dir.exists():
            shutil.rmtree(upload_dir)
        upload_dir.mkdir()
        
        # Copy only allowed files
        allowed_extensions = [".json", ".safetensors", ".bin", ".md"]
        forbidden_names = ["pytorch_model", "model.safetensors"]
        
        files_copied = []
        
        for file_path in model_dir.rglob("*"):
            if file_path.is_file():
                # Check extension
                if any(file_path.suffix == ext for ext in allowed_extensions):
                    # Check forbidden names
                    if not any(forbidden in file_path.name for forbidden in forbidden_names):
                        dest_path = upload_dir / file_path.name
                        shutil.copy2(file_path, dest_path)
                        files_copied.append(file_path.name)
        
        print(f"📁 Staged {len(files_copied)} files for upload: {files_copied}")
        
        return upload_dir
    
    def upload_to_hub(self, model_dir: str, username: str, repo_name: str = None, private: bool = False):
        """Upload LoRA adapter to HuggingFace Hub"""
        
        model_path = Path(model_dir)
        if not model_path.exists():
            raise ValueError(f"Model directory not found: {model_dir}")
        
        repo_name = repo_name or self.model_name
        self.repo_id = f"{username}/{repo_name}"
        
        print(f"🚀 Uploading Whis LoRA to HuggingFace Hub")
        print(f"📍 Repository: {self.repo_id}")
        print("=" * 50)
        
        # Step 1: Validate LoRA-only policy
        validation = self.validate_lora_only(model_path)
        if not validation["validation_passed"]:
            raise ValueError("LoRA-only validation failed - upload blocked")
        
        # Step 2: Check authentication
        try:
            user_info = self.api.whoami()
            print(f"👤 Authenticated as: {user_info['name']}")
        except Exception as e:
            print("❌ HuggingFace authentication failed")
            print("💡 Run: huggingface-cli login")
            raise e
        
        # Step 3: Create repository
        try:
            print(f"📦 Creating repository: {self.repo_id}")
            create_repo(
                repo_id=self.repo_id,
                token=None,  # Use default token
                private=private,
                exist_ok=True
            )
            print("✅ Repository created/verified")
        except Exception as e:
            print(f"❌ Failed to create repository: {e}")
            raise e
        
        # Step 4: Prepare upload directory
        upload_dir = self.prepare_upload_directory(model_path)
        
        # Step 5: Create model card
        model_card = self.create_model_card(model_path)
        with open(upload_dir / "README.md", "w") as f:
            f.write(model_card)
        
        # Step 6: Upload files
        try:
            print(f"📤 Uploading files from {upload_dir}")
            upload_folder(
                folder_path=str(upload_dir),
                repo_id=self.repo_id,
                token=None,  # Use default token
                commit_message=f"Upload Whis LoRA adapter - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            )
            print("✅ Upload completed successfully!")
            print(f"🔗 Model available at: https://huggingface.co/{self.repo_id}")
            
        except Exception as e:
            print(f"❌ Upload failed: {e}")
            raise e
        
        # Cleanup staging directory
        import shutil
        shutil.rmtree(upload_dir)
        
        return self.repo_id

def main():
    """Main upload workflow"""
    print("🤗 WHIS HUGGINGFACE HUB UPLOADER")
    print("=" * 50)
    
    # Check for trained model
    model_dirs = [
        "./whis-cybersec-model",
        "./models/whis-cybersec-model", 
        "./results/whis-cybersec-model"
    ]
    
    model_dir = None
    for dir_path in model_dirs:
        if Path(dir_path).exists():
            model_dir = dir_path
            break
    
    if not model_dir:
        print("❌ No trained model found!")
        print("💡 Make sure training completed and model directory exists")
        print(f"🔍 Checked: {model_dirs}")
        return False
    
    print(f"📁 Found model at: {model_dir}")
    
    # Get HuggingFace username
    username = input("Enter your HuggingFace username: ").strip()
    if not username:
        print("❌ Username required")
        return False
    
    # Upload options
    repo_name = input(f"Repository name (default: whis-cybersec-lora): ").strip() or "whis-cybersec-lora"
    private = input("Make repository private? (y/N): ").strip().lower() == 'y'
    
    # Initialize uploader
    uploader = WhisHFUploader()
    
    try:
        repo_id = uploader.upload_to_hub(
            model_dir=model_dir,
            username=username,
            repo_name=repo_name,
            private=private
        )
        
        print(f"\\n🎉 SUCCESS!")
        print(f"🔗 Your model: https://huggingface.co/{repo_id}")
        print(f"📚 Usage docs: https://huggingface.co/docs/peft/quicktour")
        
        return True
        
    except Exception as e:
        print(f"\\n❌ Upload failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)