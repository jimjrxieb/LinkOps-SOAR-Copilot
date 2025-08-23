#!/usr/bin/env python3
"""
Mega Training Script for Whis with 101 High-Quality Examples
Uses the integrated mega dataset with enhanced SecOps capabilities
"""

import json
import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    BitsAndBytesConfig,
    DataCollatorForLanguageModeling
)
from peft import LoraConfig, TaskType, get_peft_model, prepare_model_for_kbit_training
from datasets import Dataset
from pathlib import Path
import time
from datetime import datetime

print("🚀 WHIS MEGA TRAINING - 101 HIGH-QUALITY EXAMPLES")
print("=" * 55)

class WhisMegaTrainer:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"🔧 Device: {self.device}")
        
    def load_mega_dataset(self):
        """Load the integrated mega dataset"""
        print("📚 Loading mega dataset with 101 high-quality examples...")
        
        # Find the most recent mega dataset
        mega_files = list(Path("training/processed_data").glob("whis_mega_dataset_*.json"))
        if not mega_files:
            raise FileNotFoundError("No mega dataset found! Run mega_dataset_integration.py first.")
            
        latest_mega = max(mega_files, key=lambda x: x.stat().st_mtime)
        print(f"📖 Loading: {latest_mega}")
        
        with open(latest_mega, 'r') as f:
            mega_data = json.load(f)
            
        print(f"🎯 Mega dataset loaded: {len(mega_data)} examples")
        
        # Calculate quality stats
        quality_scores = [ex.get("metadata", {}).get("quality_score", 0.8) for ex in mega_data]
        avg_quality = sum(quality_scores) / len(quality_scores)
        high_quality = sum(1 for score in quality_scores if score >= 0.9)
        
        print(f"⭐ Average quality: {avg_quality:.3f}")
        print(f"🏆 High quality examples: {high_quality}/{len(mega_data)}")
        
        # Clean data for training (remove metadata to avoid tensor conflicts)
        clean_data = [{"text": item["text"]} for item in mega_data]
        
        return Dataset.from_list(clean_data)
        
    def setup_model_and_tokenizer(self):
        """Setup model and tokenizer with 4-bit quantization"""
        print("🔧 Setting up mega training model...")
        
        base_model_path = "/home/jimmie/linkops-industries/SOAR-copilot/training/codellama-cache"
        
        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(base_model_path, trust_remote_code=True)
        self.tokenizer.pad_token = self.tokenizer.eos_token
        self.tokenizer.padding_side = "right"
        
        # 4-bit quantization config
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.bfloat16,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4"
        )
        
        # Load base model
        self.model = AutoModelForCausalLM.from_pretrained(
            base_model_path,
            quantization_config=bnb_config,
            device_map="auto",
            trust_remote_code=True,
            torch_dtype=torch.bfloat16
        )
        
        # Prepare for k-bit training
        self.model = prepare_model_for_kbit_training(self.model)
        
        print("✅ Mega model and tokenizer loaded!")
        
    def setup_mega_lora_config(self):
        """Setup enhanced LoRA configuration for mega training"""
        print("🔗 Configuring mega LoRA adapters...")
        
        # Enhanced LoRA config optimized for larger dataset
        lora_config = LoraConfig(
            task_type=TaskType.CAUSAL_LM,
            inference_mode=False,
            r=64,  # Higher rank for better capacity with more data
            lora_alpha=128,  # Higher alpha for stronger adaptation
            lora_dropout=0.1,  # Slightly higher dropout for better generalization
            target_modules=[
                "q_proj", "v_proj", "k_proj", "o_proj",
                "gate_proj", "up_proj", "down_proj"
            ]
        )
        
        self.model = get_peft_model(self.model, lora_config)
        
        # Print trainable parameters
        trainable_params = sum(p.numel() for p in self.model.parameters() if p.requires_grad)
        total_params = sum(p.numel() for p in self.model.parameters())
        print(f"🎯 Trainable parameters: {trainable_params:,} ({100 * trainable_params / total_params:.2f}%)")
        
    def tokenize_mega_dataset(self, dataset):
        """Tokenize mega dataset for training"""
        print("🔤 Tokenizing mega dataset...")
        
        def tokenize_function(examples):
            # Tokenize with optimized settings for larger dataset
            return self.tokenizer(
                examples["text"],
                truncation=True,
                max_length=768,  # Increased for richer SecOps content
                padding=False
            )
        
        tokenized_dataset = dataset.map(
            tokenize_function,
            batched=True,
            remove_columns=dataset.column_names
        )
        
        print(f"✅ Mega dataset tokenized: {len(tokenized_dataset)} examples")
        return tokenized_dataset
        
    def train_mega_model(self, tokenized_dataset):
        """Train the mega model with 101 high-quality examples"""
        print("🚀 Starting mega training with enhanced dataset...")
        
        # Mega training arguments optimized for quality dataset
        training_args = TrainingArguments(
            output_dir="./whis-mega-model",
            per_device_train_batch_size=1,
            gradient_accumulation_steps=8,  # Higher accumulation for stability
            num_train_epochs=5,  # More epochs for comprehensive learning
            learning_rate=2e-4,  # Higher LR for more aggressive learning
            fp16=True,
            logging_steps=10,
            save_steps=25,
            eval_steps=25,
            warmup_steps=20,  # More warmup for stability
            lr_scheduler_type="cosine",
            weight_decay=0.01,
            dataloader_drop_last=True,
            report_to=None,
            remove_unused_columns=False,
            max_grad_norm=1.0  # Gradient clipping for stability
        )
        
        # Data collator for language modeling
        data_collator = DataCollatorForLanguageModeling(
            tokenizer=self.tokenizer,
            mlm=False,
            pad_to_multiple_of=8
        )
        
        # Mega trainer
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=tokenized_dataset,
            data_collator=data_collator,
            tokenizer=self.tokenizer,
        )
        
        # Start mega training
        print("💪 Initiating mega training with 101 high-quality examples...")
        start_time = time.time()
        trainer.train()
        training_time = time.time() - start_time
        
        print(f"✅ Mega training completed in {training_time:.1f} seconds!")
        
        # Save mega model
        trainer.save_model("./whis-mega-model")
        self.tokenizer.save_pretrained("./whis-mega-model")
        
        print("💾 Mega model saved to: ./whis-mega-model")
        return trainer
        
    def run_mega_training(self):
        """Run complete mega training pipeline"""
        print("🎯 Starting Whis Mega Training Pipeline")
        print("=" * 45)
        
        # Step 1: Load mega dataset
        mega_dataset = self.load_mega_dataset()
        
        # Step 2: Setup model and tokenizer
        self.setup_model_and_tokenizer()
        
        # Step 3: Configure mega LoRA
        self.setup_mega_lora_config()
        
        # Step 4: Tokenize mega dataset
        tokenized_dataset = self.tokenize_mega_dataset(mega_dataset)
        
        # Step 5: Train mega model
        trainer = self.train_mega_model(tokenized_dataset)
        
        print("\n🎉 MEGA WHIS TRAINING COMPLETE!")
        print("=" * 40)
        print("📊 Mega Training Summary:")
        print(f"  - Total examples: {len(mega_dataset)}")
        print(f"  - Enhanced LoRA rank: 64")
        print(f"  - Training epochs: 5")
        print(f"  - Model saved: ./whis-mega-model")
        print("🚀 Mega model ready for advanced SecOps automation!")
        
        return trainer

def main():
    trainer = WhisMegaTrainer()
    return trainer.run_mega_training()

if __name__ == "__main__":
    main()