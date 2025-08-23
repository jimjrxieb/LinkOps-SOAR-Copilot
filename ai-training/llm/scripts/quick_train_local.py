#!/usr/bin/env python3
"""
Quick local training using cached model
"""

import os
os.environ["HF_HUB_OFFLINE"] = "1"  # Force offline mode to use cache

import torch
from transformers import (
    AutoModelForCausalLM, 
    AutoTokenizer,
    TrainingArguments,
    BitsAndBytesConfig
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from trl import SFTTrainer
from datasets import Dataset
import json
from datetime import datetime

print("🚀 QUICK LOCAL TRAINING - USING CACHED MODEL")
print("=" * 50)

# Load dataset
print("📊 Loading dataset...")
with open('processed_data/train_dataset_20250822_150258.json', 'r') as f:
    data = json.load(f)

# Prepare dataset - data is already formatted!
training_data = data[:23]  # Use first 23 examples

dataset = Dataset.from_list(training_data)
print(f"✅ Loaded {len(training_data)} examples")

# GPU check
print(f"\n🎮 GPU Available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"📍 Device: {torch.cuda.get_device_name(0)}")

# Model configuration
model_name = "./codellama-cache"  # Use local downloaded copy

print(f"\n📦 Loading tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(
    model_name,
    trust_remote_code=True,
    padding_side='right',
    local_files_only=True  # Use local cache
)
tokenizer.pad_token = tokenizer.eos_token

print("🤖 Loading model from cache...")
# 4-bit config
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.bfloat16,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4"
)

try:
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
        local_files_only=True  # Use local cache
    )
    print("✅ Model loaded from cache!")
except Exception as e:
    print(f"❌ Error loading from cache: {e}")
    print("💡 Trying without local_files_only...")
    
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True
    )

# Prepare for training
model = prepare_model_for_kbit_training(model)
model.config.use_cache = False

print("\n🔧 Configuring LoRA...")
lora_config = LoraConfig(
    r=16,
    lora_alpha=32,
    target_modules=["q_proj", "v_proj", "k_proj", "o_proj"],
    lora_dropout=0.1,
    bias="none",
    task_type="CAUSAL_LM"
)

model = get_peft_model(model, lora_config)
print(f"✅ LoRA configured: {model.get_nb_trainable_parameters()} trainable params")

# Training arguments
output_dir = "./whis-cybersec-model"
print(f"\n⚙️ Output directory: {output_dir}")

training_args = TrainingArguments(
    output_dir=output_dir,
    num_train_epochs=1,  # Quick single epoch
    per_device_train_batch_size=1,  # Small batch for safety
    gradient_accumulation_steps=2,
    gradient_checkpointing=True,
    warmup_steps=10,
    save_steps=50,
    logging_steps=10,
    learning_rate=2e-4,
    fp16=False,
    bf16=True,
    max_grad_norm=0.3,
    optim="paged_adamw_8bit",
    save_total_limit=2,
    report_to=[]  # No external reporting
)

print("\n🏋️ Starting training...")
start_time = datetime.now()

# Trainer
trainer = SFTTrainer(
    model=model,
    train_dataset=dataset,
    args=training_args,
    dataset_text_field="text",
    max_seq_length=512,  # Shorter for faster training
    tokenizer=tokenizer,
    peft_config=lora_config
)

# Train
try:
    trainer.train()
    
    # Save model
    print("\n💾 Saving model...")
    trainer.save_model()
    tokenizer.save_pretrained(output_dir)
    
    elapsed = (datetime.now() - start_time).seconds
    print(f"\n✅ TRAINING COMPLETED in {elapsed}s!")
    print(f"📁 Model saved to: {output_dir}")
    
    # Create success marker
    with open(f"{output_dir}/training_complete.json", "w") as f:
        json.dump({
            "completed": True,
            "timestamp": datetime.now().isoformat(),
            "examples": len(training_data),
            "duration_seconds": elapsed
        }, f, indent=2)
    
except Exception as e:
    print(f"\n❌ Training failed: {e}")
    raise e
finally:
    # Cleanup
    del model
    torch.cuda.empty_cache()