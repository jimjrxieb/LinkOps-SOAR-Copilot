#!/usr/bin/env python3
"""
Senior Whis Training Script
Trains Whis model with comprehensive senior-level DevSecOps dataset
"""

import json
import torch
import argparse
import logging
from pathlib import Path
from datetime import datetime
from transformers import (
    AutoModelForCausalLM, 
    AutoTokenizer, 
    TrainingArguments, 
    Trainer,
    DataCollatorForLanguageModeling
)
from datasets import Dataset
from peft import LoraConfig, get_peft_model, TaskType
import accelerate

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SeniorWhisTrainer:
    def __init__(self, training_file: str, output_dir: str):
        self.training_file = Path(training_file)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Model configuration
        self.model_name = "codellama/CodeLlama-7b-Instruct-hf"
        self.max_length = 2048
        
        # Training parameters
        self.learning_rate = 2e-4
        self.num_epochs = 3
        self.batch_size = 4
        self.gradient_accumulation_steps = 4
        
        # LoRA configuration
        self.lora_config = LoraConfig(
            r=16,
            lora_alpha=32,
            target_modules=["q_proj", "v_proj", "k_proj", "o_proj"],
            lora_dropout=0.05,
            bias="none",
            task_type=TaskType.CAUSAL_LM
        )
        
    def load_training_data(self):
        """Load comprehensive training dataset"""
        print(f"📚 Loading training data from {self.training_file}")
        
        training_examples = []
        
        if not self.training_file.exists():
            raise FileNotFoundError(f"Training file not found: {self.training_file}")
        
        with open(self.training_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    if line.strip():
                        example = json.loads(line)
                        training_examples.append(example)
                except json.JSONDecodeError as e:
                    logger.warning(f"Skipped malformed line {line_num}: {e}")
        
        print(f"  ✅ Loaded {len(training_examples)} training examples")
        return training_examples
    
    def format_training_example(self, example):
        """Format example for Whis training"""
        instruction = example.get('instruction', '')
        user_input = example.get('input', '')
        output = example.get('output', '')
        
        # Create conversation format
        if user_input:
            prompt = f"### Instruction:\n{instruction}\n\n### Input:\n{user_input}\n\n### Response:\n"
        else:
            prompt = f"### Instruction:\n{instruction}\n\n### Response:\n"
        
        return prompt + output
    
    def prepare_dataset(self, training_examples):
        """Prepare dataset for training"""
        print("🔄 Preparing dataset for training...")
        
        formatted_texts = []
        for example in training_examples:
            formatted_text = self.format_training_example(example)
            formatted_texts.append(formatted_text)
        
        # Create dataset
        dataset = Dataset.from_dict({"text": formatted_texts})
        
        print(f"  ✅ Created dataset with {len(dataset)} examples")
        return dataset
    
    def tokenize_function(self, examples):
        """Tokenize examples for training"""
        tokenized = self.tokenizer(
            examples["text"],
            truncation=True,
            padding=False,
            max_length=self.max_length,
            return_tensors="pt"
        )
        
        # Set labels to be the same as input_ids for causal language modeling
        tokenized["labels"] = tokenized["input_ids"].clone()
        
        return tokenized
    
    def setup_model_and_tokenizer(self):
        """Setup model and tokenizer with LoRA"""
        print(f"🤖 Loading base model: {self.model_name}")
        
        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name, trust_remote_code=True)
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        
        # Load model
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            torch_dtype=torch.float16,
            device_map="auto",
            trust_remote_code=True
        )
        
        # Apply LoRA
        print("🔧 Applying LoRA configuration...")
        self.model = get_peft_model(self.model, self.lora_config)
        self.model.print_trainable_parameters()
        
        return self.model, self.tokenizer
    
    def train_model(self):
        """Train the model with senior-level dataset"""
        print("🚀 SENIOR WHIS TRAINING")
        print("=" * 50)
        
        # Load training data
        training_examples = self.load_training_data()
        
        # Setup model and tokenizer
        model, tokenizer = self.setup_model_and_tokenizer()
        
        # Prepare dataset
        dataset = self.prepare_dataset(training_examples)
        
        # Tokenize dataset
        print("🔤 Tokenizing dataset...")
        tokenized_dataset = dataset.map(
            self.tokenize_function,
            batched=True,
            remove_columns=dataset.column_names
        )
        
        # Split dataset (use 90% for training, 10% for validation)
        split_dataset = tokenized_dataset.train_test_split(test_size=0.1, seed=42)
        train_dataset = split_dataset["train"]
        eval_dataset = split_dataset["test"]
        
        print(f"  📊 Training examples: {len(train_dataset)}")
        print(f"  📊 Validation examples: {len(eval_dataset)}")
        
        # Data collator
        data_collator = DataCollatorForLanguageModeling(
            tokenizer=tokenizer,
            mlm=False
        )
        
        # Training arguments
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        training_args = TrainingArguments(
            output_dir=self.output_dir / f"whis-senior-{timestamp}",
            num_train_epochs=self.num_epochs,
            per_device_train_batch_size=self.batch_size,
            per_device_eval_batch_size=self.batch_size,
            gradient_accumulation_steps=self.gradient_accumulation_steps,
            warmup_steps=10,
            logging_steps=5,
            evaluation_strategy="steps",
            eval_steps=20,
            save_steps=20,
            learning_rate=self.learning_rate,
            fp16=True,
            remove_unused_columns=False,
            dataloader_pin_memory=False,
            load_best_model_at_end=True,
            metric_for_best_model="eval_loss",
            greater_is_better=False,
            report_to=[],  # Disable wandb logging
            save_total_limit=2
        )
        
        # Create trainer
        trainer = Trainer(
            model=model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=eval_dataset,
            data_collator=data_collator,
            tokenizer=tokenizer
        )
        
        # Train the model
        print("🔥 Starting training...")
        train_result = trainer.train()
        
        print(f"\n✅ Training completed!")
        print(f"📈 Training Loss: {train_result.training_loss:.4f}")
        
        # Save the model
        final_model_dir = self.output_dir / f"whis-senior-final-{timestamp}"
        trainer.save_model(final_model_dir)
        
        # Save training summary
        training_summary = {
            "timestamp": timestamp,
            "training_file": str(self.training_file),
            "base_model": self.model_name,
            "training_examples": len(training_examples),
            "training_loss": train_result.training_loss,
            "learning_rate": self.learning_rate,
            "num_epochs": self.num_epochs,
            "batch_size": self.batch_size,
            "lora_config": {
                "r": self.lora_config.r,
                "lora_alpha": self.lora_config.lora_alpha,
                "lora_dropout": self.lora_config.lora_dropout
            }
        }
        
        with open(final_model_dir / "training_summary.json", 'w') as f:
            json.dump(training_summary, f, indent=2)
        
        print(f"💾 Model saved to: {final_model_dir}")
        print(f"📊 Training summary saved")
        
        return final_model_dir

def main():
    parser = argparse.ArgumentParser(description="Train Senior Whis Model")
    parser.add_argument("--training_file", type=str, required=True, help="Path to training JSONL file")
    parser.add_argument("--output_dir", type=str, default="../models", help="Output directory for trained model")
    parser.add_argument("--epochs", type=int, default=3, help="Number of training epochs")
    parser.add_argument("--batch_size", type=int, default=4, help="Batch size")
    parser.add_argument("--learning_rate", type=float, default=2e-4, help="Learning rate")
    
    args = parser.parse_args()
    
    trainer = SeniorWhisTrainer(args.training_file, args.output_dir)
    trainer.num_epochs = args.epochs
    trainer.batch_size = args.batch_size  
    trainer.learning_rate = args.learning_rate
    
    model_dir = trainer.train_model()
    print(f"\n🎉 Senior Whis training complete!")
    print(f"🚀 Model available at: {model_dir}")

if __name__ == "__main__":
    main()