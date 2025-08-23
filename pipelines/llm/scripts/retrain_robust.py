#!/usr/bin/env python3
"""
Robust Whis Retraining Script
Use the 100+ preprocessed examples for production-ready model
"""

import os
import json
import torch
from datetime import datetime
from transformers import (
    AutoTokenizer, AutoModelForCausalLM, 
    TrainingArguments, Trainer, DataCollatorForLanguageModeling
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from datasets import Dataset
import sys

# Import configuration
sys.path.append('.')
from model_config import WhisModelConfig

def load_preprocessed_data():
    """Load the preprocessed training data"""
    # Find the latest preprocessed dataset
    processed_files = [f for f in os.listdir("processed_data") if f.startswith("train_dataset_")]
    if not processed_files:
        print("❌ No preprocessed training data found!")
        print("Run preprocessing_pipeline.py first")
        return None, None
    
    latest_train = sorted(processed_files)[-1]
    latest_val = latest_train.replace("train_", "val_")
    
    print(f"📊 Loading preprocessed data:")
    print(f"  Train: {latest_train}")
    print(f"  Validation: {latest_val}")
    
    with open(f"processed_data/{latest_train}", 'r') as f:
        train_data = json.load(f)
    
    with open(f"processed_data/{latest_val}", 'r') as f:
        val_data = json.load(f)
    
    return train_data, val_data

def main():
    """Robust training with preprocessed data"""
    print("🛡️ Starting Robust Whis Training")
    print(f"⏰ Start time: {datetime.now()}")
    print("🎯 Using preprocessed 100+ example dataset")
    
    # Load preprocessed data
    train_data, val_data = load_preprocessed_data()
    if not train_data:
        return
    
    print(f"📊 Training examples: {len(train_data)}")
    print(f"📊 Validation examples: {len(val_data)}")
    
    # Load configuration (optimized for robust training)
    config = WhisModelConfig()
    config.output_dir = "./whis-cybersec-robust"
    config.num_train_epochs = 5  # More epochs for robust training
    config.per_device_train_batch_size = 2  # Smaller batch for stability
    config.learning_rate = 1e-4  # Lower learning rate for fine control
    config.save_steps = 100
    config.eval_steps = 50
    config.logging_steps = 25
    
    # Initialize model and tokenizer
    print("🤗 Loading CodeLlama model and tokenizer...")
    
    tokenizer = AutoTokenizer.from_pretrained(config.base_model_id)
    tokenizer.pad_token = tokenizer.eos_token
    
    model = AutoModelForCausalLM.from_pretrained(
        config.base_model_id,
        quantization_config=config.get_bnb_config(),
        device_map="auto",
        torch_dtype=torch.float16
    )
    
    # Prepare for training
    model = prepare_model_for_kbit_training(model)
    model = get_peft_model(model, config.get_lora_config())
    
    print("✅ Model prepared for robust training")
    model.print_trainable_parameters()
    
    # Tokenize data
    def tokenize_function(examples):
        tokens = tokenizer(
            examples['text'],
            truncation=True,
            padding=False,
            max_length=config.max_sequence_length,
            return_overflowing_tokens=False
        )
        tokens["labels"] = tokens["input_ids"].copy()
        return tokens
    
    # Create datasets
    train_dataset = Dataset.from_list(train_data)
    val_dataset = Dataset.from_list(val_data)
    
    train_dataset = train_dataset.map(
        tokenize_function, batched=True,
        remove_columns=train_dataset.column_names
    )
    
    val_dataset = val_dataset.map(
        tokenize_function, batched=True,
        remove_columns=val_dataset.column_names
    )
    
    # Setup trainer
    training_args = config.get_training_arguments()
    data_collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)
    
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        tokenizer=tokenizer,
        data_collator=data_collator
    )
    
    # Train model
    print("🏋️ Starting robust training...")
    trainer.train()
    
    # Evaluate model
    print("📊 Evaluating robust model...")
    eval_results = trainer.evaluate()
    
    # Save model
    print("💾 Saving robust model...")
    model.save_pretrained(config.output_dir)
    tokenizer.save_pretrained(config.output_dir)
    
    # Save results
    results = {
        "training_date": datetime.now().isoformat(),
        "config": {
            "model_name": config.model_name,
            "base_model": config.base_model_id,
            "epochs": config.num_train_epochs,
            "batch_size": config.per_device_train_batch_size,
            "learning_rate": config.learning_rate
        },
        "data": {
            "train_examples": len(train_data),
            "val_examples": len(val_data),
            "preprocessing": "100+ curated examples"
        },
        "eval_results": eval_results,
        "mentor_compliance": {
            "target_examples": "100+",
            "achieved_examples": len(train_data),
            "focus": "4625/T1110 + LC Replay",
            "quality_controlled": True
        }
    }
    
    with open(f"{config.output_dir}/robust_training_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"✅ Robust training complete!")
    print(f"📁 Model saved to: {config.output_dir}")
    print(f"🎯 Ready for mentor validation!")

if __name__ == "__main__":
    main()