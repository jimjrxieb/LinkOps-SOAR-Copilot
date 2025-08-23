#!/usr/bin/env python3
"""
Simple LoRA Training - Direct Transformers approach
No TRL complications, just pure HuggingFace Transformers
"""

import torch
from transformers import (
    AutoModelForCausalLM, 
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling,
    BitsAndBytesConfig
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
import json
from datetime import datetime
from datasets import Dataset

print("🚀 SIMPLE WHIS TRAINING - NO TRL")
print("=" * 50)

# Load dataset
print("📊 Loading dataset...")
with open('training/processed_data/train_dataset_20250822_150258.json', 'r') as f:
    data = json.load(f)

# Take first 23 examples  
training_data = data[:23]
print(f"✅ Loaded {len(training_data)} examples")

# Create dataset - remove metadata to avoid column conflicts
clean_data = [{"text": item["text"]} for item in training_data]
dataset = Dataset.from_list(clean_data)

# Model setup
model_name = "/home/jimmie/linkops-industries/SOAR-copilot/training/codellama-cache"
print(f"\n📦 Loading tokenizer from {model_name}...")

tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
tokenizer.pad_token = tokenizer.eos_token
tokenizer.padding_side = "right"

print("🤖 Loading model with 4-bit quantization...")

# 4-bit config
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.bfloat16,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4"
)

model = AutoModelForCausalLM.from_pretrained(
    model_name,
    quantization_config=bnb_config,
    device_map="auto",
    trust_remote_code=True
)

print("✅ Model loaded!")

# Prepare for LoRA
model = prepare_model_for_kbit_training(model)
model.config.use_cache = False

# LoRA config
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
trainable_params = model.get_nb_trainable_parameters()
print(f"✅ LoRA configured: {trainable_params[0]:,} trainable parameters")

# Tokenize dataset
def tokenize_function(examples):
    tokenized = tokenizer(
        examples["text"],
        truncation=True,
        padding="max_length",
        max_length=512,
        return_tensors=None
    )
    # For causal LM, labels are the same as input_ids
    tokenized["labels"] = tokenized["input_ids"].copy()
    return tokenized

tokenized_dataset = dataset.map(tokenize_function, batched=True)

# Data collator with explicit padding
data_collator = DataCollatorForLanguageModeling(
    tokenizer=tokenizer,
    mlm=False,  # Causal LM, not masked
    pad_to_multiple_of=8,  # More efficient for GPU
)

# Training arguments
output_dir = "./whis-cybersec-model"
print(f"\n⚙️ Output directory: {output_dir}")

training_args = TrainingArguments(
    output_dir=output_dir,
    num_train_epochs=1,
    per_device_train_batch_size=1,
    gradient_accumulation_steps=2,
    gradient_checkpointing=True,
    warmup_steps=10,
    save_steps=50,
    logging_steps=5,
    learning_rate=2e-4,
    fp16=False,
    bf16=True,
    max_grad_norm=0.3,
    optim="paged_adamw_8bit",
    save_total_limit=2,
    report_to=[],
    remove_unused_columns=True,  # Remove unused columns to avoid conflicts
)

# Create trainer
print("\n🏋️ Creating trainer...")
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_dataset,
    data_collator=data_collator,
)

print("🎯 Starting training!")
start_time = datetime.now()

try:
    # Train the model
    trainer.train()
    
    # Save model
    print("\n💾 Saving model...")
    trainer.save_model()
    tokenizer.save_pretrained(output_dir)
    
    elapsed = (datetime.now() - start_time).seconds
    print(f"\n✅ TRAINING COMPLETED in {elapsed}s!")
    print(f"📁 Model saved to: {output_dir}")
    
    # Create completion marker
    with open(f"{output_dir}/training_complete.json", "w") as f:
        json.dump({
            "completed": True,
            "timestamp": datetime.now().isoformat(),
            "examples": len(training_data),
            "duration_seconds": elapsed,
            "trainable_params": trainable_params[0]
        }, f, indent=2)
    
    print("🎉 SUCCESS! Whis LoRA adapter trained and saved!")
    
except Exception as e:
    print(f"\n❌ Training failed: {e}")
    raise e
finally:
    # Cleanup
    torch.cuda.empty_cache()