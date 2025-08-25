#!/usr/bin/env python3
"""
🚀 SOAR-Copilot Model Training Pipeline
========================================
Trains on:
- Open-MalSec security scenarios
- Pipeline-generated training data
- Existing Whis training datasets

Model: microsoft/Phi-3.5-mini-instruct
"""

import os
import json
import logging
from pathlib import Path
from datetime import datetime
import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling
)
from datasets import Dataset, concatenate_datasets
from huggingface_hub import login
from peft import LoraConfig, get_peft_model, TaskType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# HuggingFace login
HF_TOKEN = os.getenv("HUGGINGFACE_TOKEN")
HF_USER = os.getenv("HUGGINGFACE_USER")

class SOARTrainer:
    def __init__(self):
        self.base_model = "microsoft/Phi-3.5-mini-instruct"
        self.output_dir = "models/soar-copilot-phi"
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        logger.info(f"🎯 Training on: {self.device}")
        logger.info(f"📦 Base model: {self.base_model}")
        
        # Login to HuggingFace
        if HF_TOKEN:
            login(token=HF_TOKEN)
            logger.info(f"✅ Logged in as: {HF_USER}")
    
    def load_datasets(self):
        """Load all training datasets"""
        logger.info("📚 Loading training datasets...")
        
        all_examples = []
        
        # 1. Load Open-MalSec dataset
        malsec_dir = Path("open-malsec")
        if malsec_dir.exists():
            logger.info("🦠 Loading Open-MalSec datasets...")
            for json_file in malsec_dir.glob("*.json"):
                try:
                    with open(json_file, 'r') as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            for item in data[:50]:  # Sample 50 per file
                                if 'instruction' in item and 'output' in item:
                                    all_examples.append({
                                        "text": f"### Instruction:\\n{item['instruction']}\\n\\n### Response:\\n{item['output']}"
                                    })
                    logger.info(f"  ✓ {json_file.name}: {len(data) if isinstance(data, list) else 1} examples")
                except Exception as e:
                    logger.warning(f"  ⚠️ Skipping {json_file.name}: {e}")
        
        # 2. Load pipeline-generated training data
        curated_dir = Path("data/curated/llm")
        if curated_dir.exists():
            logger.info("🎓 Loading pipeline-generated data...")
            for jsonl_file in curated_dir.glob("*.jsonl"):
                with open(jsonl_file, 'r') as f:
                    for line in f:
                        try:
                            item = json.loads(line)
                            if 'instruction' in item:
                                response = item.get('output', item.get('response', ''))
                                if response:
                                    all_examples.append({
                                        "text": f"### Instruction:\\n{item['instruction']}\\n\\n### Response:\\n{json.dumps(response) if isinstance(response, dict) else response}"
                                    })
                        except:
                            pass
                logger.info(f"  ✓ {jsonl_file.name}")
        
        # 3. Load existing Whis training data
        whis_data_dir = Path("ai-training/llm/data")
        if whis_data_dir.exists():
            logger.info("🤖 Loading Whis training datasets...")
            for jsonl_file in whis_data_dir.glob("whis_*.jsonl"):
                with open(jsonl_file, 'r') as f:
                    for line in f:
                        try:
                            item = json.loads(line)
                            if 'instruction' in item and 'response' in item:
                                all_examples.append({
                                    "text": f"### Instruction:\\n{item['instruction']}\\n\\n### Response:\\n{item['response']}"
                                })
                        except:
                            pass
                logger.info(f"  ✓ {jsonl_file.name}")
        
        logger.info(f"\\n📊 Total training examples: {len(all_examples)}")
        
        # Create HuggingFace dataset
        dataset = Dataset.from_list(all_examples)
        
        # Split into train/test
        split_dataset = dataset.train_test_split(test_size=0.1, seed=42)
        
        logger.info(f"  Training: {len(split_dataset['train'])} examples")
        logger.info(f"  Testing: {len(split_dataset['test'])} examples")
        
        return split_dataset
    
    def setup_model(self):
        """Setup model with LoRA for efficient training"""
        logger.info("🔧 Setting up model with LoRA...")
        
        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.base_model,
            trust_remote_code=True,
            padding_side="left"
        )
        
        if not self.tokenizer.pad_token:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        
        # Load model with 4-bit quantization for efficiency
        from transformers import BitsAndBytesConfig
        
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16
        ) if self.device == "cuda" else None
        
        self.model = AutoModelForCausalLM.from_pretrained(
            self.base_model,
            quantization_config=bnb_config if self.device == "cuda" else None,
            device_map="auto" if self.device == "cuda" else None,
            trust_remote_code=True,
            torch_dtype=torch.bfloat16 if self.device == "cuda" else torch.float32
        )
        
        # Configure LoRA
        lora_config = LoraConfig(
            r=16,  # Rank
            lora_alpha=32,
            target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
            lora_dropout=0.1,
            bias="none",
            task_type=TaskType.CAUSAL_LM
        )
        
        self.model = get_peft_model(self.model, lora_config)
        self.model.print_trainable_parameters()
        
        logger.info("✅ Model setup complete")
    
    def tokenize_function(self, examples):
        """Tokenize examples for training"""
        return self.tokenizer(
            examples["text"],
            truncation=True,
            padding="max_length",
            max_length=512
        )
    
    def train(self):
        """Run the training"""
        logger.info("🚀 Starting training...")
        
        # Load datasets
        dataset = self.load_datasets()
        
        # Setup model
        self.setup_model()
        
        # Tokenize datasets
        tokenized_dataset = dataset.map(
            self.tokenize_function,
            batched=True,
            remove_columns=dataset["train"].column_names
        )
        
        # Training arguments
        training_args = TrainingArguments(
            output_dir=self.output_dir,
            num_train_epochs=3,
            per_device_train_batch_size=2 if self.device == "cuda" else 1,
            per_device_eval_batch_size=2 if self.device == "cuda" else 1,
            gradient_accumulation_steps=4,
            warmup_steps=100,
            learning_rate=2e-4,
            fp16=True if self.device == "cuda" else False,
            logging_steps=10,
            eval_strategy="steps",
            eval_steps=50,
            save_strategy="steps",
            save_steps=100,
            save_total_limit=2,
            load_best_model_at_end=True,
            report_to="none",
            push_to_hub=False,
        )
        
        # Data collator
        data_collator = DataCollatorForLanguageModeling(
            tokenizer=self.tokenizer,
            mlm=False
        )
        
        # Create trainer
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=tokenized_dataset["train"],
            eval_dataset=tokenized_dataset["test"],
            data_collator=data_collator,
        )
        
        # Train!
        logger.info("🏋️ Training in progress...")
        trainer.train()
        
        # Save model
        logger.info(f"💾 Saving model to {self.output_dir}")
        trainer.save_model()
        self.tokenizer.save_pretrained(self.output_dir)
        
        # Push to HuggingFace Hub
        if HF_USER:
            try:
                logger.info(f"📤 Pushing to HuggingFace Hub: {HF_USER}/soar-copilot-phi")
                self.model.push_to_hub(f"{HF_USER}/soar-copilot-phi", use_auth_token=HF_TOKEN)
                self.tokenizer.push_to_hub(f"{HF_USER}/soar-copilot-phi", use_auth_token=HF_TOKEN)
                logger.info("✅ Model pushed to Hub successfully!")
            except Exception as e:
                logger.warning(f"Could not push to Hub: {e}")
        
        logger.info("🎉 Training complete!")
        
        # Save training metadata
        metadata = {
            "model": self.base_model,
            "training_completed": datetime.now().isoformat(),
            "device": self.device,
            "datasets": [
                "open-malsec",
                "pipeline-generated",
                "whis-training"
            ],
            "total_examples": len(dataset["train"]) + len(dataset["test"])
        }
        
        with open(f"{self.output_dir}/training_metadata.json", "w") as f:
            json.dump(metadata, f, indent=2)
        
        return trainer

def main():
    print("=" * 60)
    print("🚀 SOAR-COPILOT MODEL TRAINING")
    print("=" * 60)
    
    trainer = SOARTrainer()
    trainer.train()
    
    print("\\n✅ Training pipeline complete!")
    print(f"📁 Model saved to: models/soar-copilot-phi")
    print("🎯 View progress at: http://localhost:8000")

if __name__ == "__main__":
    main()