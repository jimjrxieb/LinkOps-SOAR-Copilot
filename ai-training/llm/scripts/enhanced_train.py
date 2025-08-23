#!/usr/bin/env python3
"""
Enhanced Whis Training - Performance Boost Integration
Combines original training data with high-quality performance boost examples
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

print("🚀 ENHANCED WHIS TRAINING - PERFORMANCE BOOST")
print("=" * 50)

class EnhancedWhisTrainer:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"🔧 Device: {self.device}")
        
    def load_combined_dataset(self):
        """Load and combine original + performance boost datasets"""
        print("📚 Loading combined training datasets...")
        
        # Load original dataset
        original_path = Path("training/processed_data/train_dataset_20250822_150258.json")
        with open(original_path, 'r') as f:
            original_data = json.load(f)
        print(f"📖 Original dataset: {len(original_data)} examples")
        
        # Load performance boost dataset
        boost_path = Path("training/processed_data/performance_boost_dataset.json")
        with open(boost_path, 'r') as f:
            boost_data = json.load(f)
        print(f"🚀 Performance boost: {len(boost_data)} high-quality examples")
        
        # Combine datasets
        combined_data = original_data + boost_data
        print(f"🔗 Combined dataset: {len(combined_data)} total examples")
        
        # Clean data for training (remove metadata to avoid tensor conflicts)
        clean_data = [{"text": item["text"]} for item in combined_data]
        
        return Dataset.from_list(clean_data)
        
    def setup_model_and_tokenizer(self):
        """Setup model and tokenizer with 4-bit quantization"""
        print("🔧 Setting up enhanced model and tokenizer...")
        
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
        
        print("✅ Enhanced model and tokenizer loaded!")
        
    def setup_lora_config(self):
        """Setup LoRA configuration for enhanced training"""
        print("🔗 Configuring enhanced LoRA adapters...")
        
        # Enhanced LoRA config for better performance
        lora_config = LoraConfig(
            task_type=TaskType.CAUSAL_LM,
            inference_mode=False,
            r=32,  # Increased rank for better capacity
            lora_alpha=64,  # Increased alpha for stronger adaptation
            lora_dropout=0.05,  # Lower dropout for stability
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
        
    def tokenize_dataset(self, dataset):
        """Tokenize dataset for training"""
        print("🔤 Tokenizing enhanced dataset...")
        
        def tokenize_function(examples):
            # Tokenize with proper truncation and padding
            return self.tokenizer(
                examples["text"],
                truncation=True,
                max_length=512,  # Reduced for stability
                padding=False
            )
        
        tokenized_dataset = dataset.map(
            tokenize_function,
            batched=True,
            remove_columns=dataset.column_names
        )
        
        print(f"✅ Dataset tokenized: {len(tokenized_dataset)} examples")
        return tokenized_dataset
        
    def train_enhanced_model(self, tokenized_dataset):
        """Train the enhanced model with performance boost data"""
        print("🚀 Starting enhanced training...")
        
        # Enhanced training arguments
        training_args = TrainingArguments(
            output_dir="./whis-enhanced-model",
            per_device_train_batch_size=1,  # Small batch for stability
            gradient_accumulation_steps=4,  # Effective batch size 4
            num_train_epochs=3,  # More epochs for better learning
            learning_rate=1e-4,  # Slightly lower for stability
            fp16=True,
            logging_steps=5,
            save_steps=50,
            eval_steps=50,
            warmup_steps=10,
            lr_scheduler_type="cosine",
            weight_decay=0.01,
            dataloader_drop_last=True,
            report_to=None,
            remove_unused_columns=False
        )
        
        # Data collator for language modeling
        data_collator = DataCollatorForLanguageModeling(
            tokenizer=self.tokenizer,
            mlm=False,
            pad_to_multiple_of=8
        )
        
        # Enhanced trainer
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=tokenized_dataset,
            data_collator=data_collator,
            tokenizer=self.tokenizer,
        )
        
        # Start enhanced training
        start_time = time.time()
        trainer.train()
        training_time = time.time() - start_time
        
        print(f"✅ Enhanced training completed in {training_time:.1f} seconds!")
        
        # Save enhanced model
        trainer.save_model("./whis-enhanced-model")
        self.tokenizer.save_pretrained("./whis-enhanced-model")
        
        print("💾 Enhanced model saved to: ./whis-enhanced-model")
        return trainer
        
    def run_enhanced_training(self):
        """Run complete enhanced training pipeline"""
        print("🎯 Starting Enhanced Whis Training Pipeline")
        print("=" * 50)
        
        # Step 1: Load combined dataset
        combined_dataset = self.load_combined_dataset()
        
        # Step 2: Setup model and tokenizer
        self.setup_model_and_tokenizer()
        
        # Step 3: Configure LoRA
        self.setup_lora_config()
        
        # Step 4: Tokenize dataset
        tokenized_dataset = self.tokenize_dataset(combined_dataset)
        
        # Step 5: Train enhanced model
        trainer = self.train_enhanced_model(tokenized_dataset)
        
        print("\n🎉 ENHANCED WHIS TRAINING COMPLETE!")
        print("=" * 50)
        print("📊 Training Summary:")
        print(f"  - Total examples: {len(combined_dataset)}")
        print(f"  - Enhanced LoRA rank: 32")
        print(f"  - Training epochs: 3")
        print(f"  - Model saved: ./whis-enhanced-model")
        print("🚀 Enhanced model ready for testing!")
        
        return trainer

def main():
    trainer = EnhancedWhisTrainer()
    return trainer.run_enhanced_training()

if __name__ == "__main__":
    main()