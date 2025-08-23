# 🧠 LLM Training Pipeline

Fine-tune Whis cybersecurity SOAR copilot using LoRA adapters on CodeLlama-7B-Instruct.

## Quick Start

```bash
# Preprocess training data
cd pipelines/llm/scripts
python preprocessing_pipeline.py

# Train Whis model with Action Schema
python mega_train.py --data ../data/whis_action_schema_100.jsonl --out ../models/whis-mega-model

# Evaluate model performance  
python mentor_validation.py --model ../models/whis-mega-model --eval ../../tests/golden/

# Test trained model
python test_whis_model.py --model ../models/whis-mega-model
```

## Action Schema Contract
All models must output this exact structure:
```json
{
  "triage_steps": [], "containment": [], "remediation": [],
  "mitre": [], "spl_query": "", "lc_rule": "", "k8s_manifest": "",
  "validation_steps": [], "citations": [], "confidence": 0.0, "grounded": false
}
```

## Structure

- `data/` - JSONL/CSV training datasets (small files only)
- `scripts/` - Training, evaluation, and pipeline scripts
- `results/` - Metrics, test results, and training reports (JSON format)
- `models/` - LoRA adapters and model outputs (use Git-LFS for large files)

## Latest Results

- **whis-mega-model**: 101 examples, 0.044 final loss ✨
- **Processing time**: ~7 minutes with 4-bit quantization
- **Model size**: 159.9M trainable parameters with LoRA rank 64

## Outputs

All training results land in `results/`. Models saved to `models/` with Git-LFS or external storage.