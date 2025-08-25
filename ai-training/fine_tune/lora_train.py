#!/usr/bin/env python3
"""
🧠 Fine-tuning Pipeline (SEPARATED from RAG)
==========================================
Fine-tunes Whis using LoRA adapters on curated datasets.
Fine-tuning produces ADAPTER WEIGHTS, not a new base model.

Mentor corrections applied:
- Separated from RAG pipeline
- Proper experiment tracking
- Version pinning
- Security compliance
"""

import os
import yaml
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

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
from datasets import Dataset, load_dataset
import mlflow
import mlflow.transformers


class WhisFineTuner:
    """Fine-tuning pipeline for Whis SOAR copilot"""
    
    def __init__(self, config_path: str = "configs/model.whis.yaml"):
        """Initialize fine-tuner with configuration"""
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.experiment_id = None
        self.model = None
        self.tokenizer = None
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration with security validation"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config not found: {self.config_path}")
            
        with open(self.config_path, 'r') as f:
            config = yaml.safe_load(f)
            
        # Security: Ensure no secrets in config
        config_str = yaml.dump(config)
        forbidden_patterns = ["password", "secret", "key", "token", "api_key"]
        for pattern in forbidden_patterns:
            if pattern.lower() in config_str.lower():
                raise ValueError(f"Forbidden pattern '{pattern}' found in config")
                
        return config
        
    def _setup_experiment_tracking(self) -> None:
        """Setup MLflow experiment tracking"""
        mlflow.set_experiment("whis_fine_tuning")
        
        # Start MLflow run with metadata
        mlflow.start_run()
        
        # Log configuration
        mlflow.log_params({
            "base_model": self.config["model"]["base"]["name"],
            "lora_r": self.config["model"]["adapter"]["r"],
            "lora_alpha": self.config["model"]["adapter"]["lora_alpha"],
            "learning_rate": self.config["training"]["learning_rate"],
            "epochs": self.config["training"]["num_train_epochs"],
            "batch_size": self.config["training"]["per_device_train_batch_size"]
        })
        
        # Log versioning info
        mlflow.log_params({
            "dataset_hash": os.getenv("DATASET_HASH", "unknown"),
            "commit_hash": os.getenv("COMMIT_HASH", "unknown"),
            "config_hash": self._get_config_hash()
        })
        
    def _get_config_hash(self) -> str:
        """Get hash of configuration for reproducibility"""
        config_str = yaml.dump(self.config, sort_keys=True)
        return hashlib.sha256(config_str.encode()).hexdigest()[:8]
        
    def load_model_and_tokenizer(self) -> None:
        """Load base model and tokenizer with security validations"""
        print("🔧 Loading base model and tokenizer...")
        
        base_config = self.config["model"]["base"]
        
        # Security: Verify model path exists and is expected location
        model_path = Path(base_config["path"])
        if not model_path.exists():
            raise FileNotFoundError(f"Base model not found: {model_path}")
            
        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            base_config["path"],
            trust_remote_code=base_config["trust_remote_code"]
        )
        
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        self.tokenizer.padding_side = "right"
        
        # Setup quantization config
        quant_config = self.config["model"]["quantization"]
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=quant_config["load_in_4bit"],
            bnb_4bit_compute_dtype=getattr(torch, quant_config["bnb_4bit_compute_dtype"]),
            bnb_4bit_use_double_quant=quant_config["bnb_4bit_use_double_quant"],
            bnb_4bit_quant_type=quant_config["bnb_4bit_quant_type"]
        )
        
        # Load base model
        self.model = AutoModelForCausalLM.from_pretrained(
            base_config["path"],
            quantization_config=bnb_config,
            device_map="auto",
            trust_remote_code=base_config["trust_remote_code"],
            torch_dtype=torch.bfloat16
        )
        
        # Prepare for k-bit training
        self.model = prepare_model_for_kbit_training(self.model)
        
        # Setup LoRA configuration
        adapter_config = self.config["model"]["adapter"]
        lora_config = LoraConfig(
            task_type=getattr(TaskType, adapter_config["task_type"]),
            inference_mode=False,
            r=adapter_config["r"],
            lora_alpha=adapter_config["lora_alpha"],
            lora_dropout=adapter_config["lora_dropout"],
            target_modules=adapter_config["target_modules"],
            bias=adapter_config["bias"]
        )
        
        # Apply LoRA
        self.model = get_peft_model(self.model, lora_config)
        
        print("✅ Model and tokenizer loaded successfully")
        
    def load_dataset(self, dataset_path: str) -> Dataset:
        """Load and validate training dataset"""
        print(f"📚 Loading dataset: {dataset_path}")
        
        dataset_file = Path(dataset_path)
        if not dataset_file.exists():
            raise FileNotFoundError(f"Dataset not found: {dataset_path}")
            
        # Load dataset based on file extension
        if dataset_path.endswith(".jsonl"):
            with open(dataset_file, 'r') as f:
                data = [json.loads(line) for line in f if line.strip()]
        else:
            raise ValueError(f"Unsupported dataset format: {dataset_path}")
            
        # Validate dataset schema
        required_fields = ["instruction", "response"]
        for i, example in enumerate(data):
            missing_fields = [f for f in required_fields if f not in example]
            if missing_fields:
                raise ValueError(f"Example {i}: Missing fields {missing_fields}")
                
        # Security: Check for potential secrets in dataset
        dataset_str = json.dumps(data)
        forbidden_patterns = ["password", "api_key", "secret", "token"]
        for pattern in forbidden_patterns:
            if pattern in dataset_str.lower():
                print(f"⚠️  Warning: Potential secret pattern '{pattern}' in dataset")
                
        # Convert to HuggingFace dataset
        hf_dataset = Dataset.from_list(data)
        
        print(f"✅ Loaded {len(data)} examples")
        return hf_dataset
        
    def tokenize_dataset(self, dataset: Dataset) -> Dataset:
        """Tokenize dataset for training"""
        print("🔤 Tokenizing dataset...")
        
        chat_template = self.config["format"]["chat_template"]
        
        def format_example(example):
            """Format example using chat template"""
            formatted = chat_template.format(
                instruction=example["instruction"],
                response=example["response"]
            )
            return {"text": formatted}
            
        def tokenize_function(examples):
            """Tokenize examples"""
            return self.tokenizer(
                examples["text"],
                truncation=True,
                max_length=2048,
                padding=False
            )
            
        # Format and tokenize
        formatted_dataset = dataset.map(format_example)
        tokenized_dataset = formatted_dataset.map(
            tokenize_function,
            batched=True,
            remove_columns=formatted_dataset.column_names
        )
        
        print("✅ Dataset tokenized successfully")
        return tokenized_dataset
        
    def train(self, train_dataset: Dataset, eval_dataset: Optional[Dataset] = None) -> str:
        """Execute fine-tuning with experiment tracking"""
        print("🚀 Starting fine-tuning...")
        
        # Setup training arguments
        training_config = self.config["training"]
        training_args = TrainingArguments(
            output_dir=training_config["output_dir"],
            per_device_train_batch_size=training_config["per_device_train_batch_size"],
            gradient_accumulation_steps=training_config["gradient_accumulation_steps"],
            num_train_epochs=training_config["num_train_epochs"],
            learning_rate=training_config["learning_rate"],
            bf16=training_config["bf16"],
            logging_steps=training_config["logging_steps"],
            save_steps=training_config["save_steps"],
            warmup_steps=training_config["warmup_steps"],
            dataloader_drop_last=training_config["dataloader_drop_last"],
            report_to=training_config["report_to"],
            remove_unused_columns=training_config["remove_unused_columns"],
            save_strategy=training_config["save_strategy"],
            evaluation_strategy=training_config.get("evaluation_strategy", "no"),
            eval_steps=training_config.get("eval_steps", 500) if eval_dataset else None,
            load_best_model_at_end=training_config.get("load_best_model_at_end", False),
            metric_for_best_model=training_config.get("metric_for_best_model", "eval_loss"),
            run_name=f"whis_finetune_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        
        # Data collator
        data_collator = DataCollatorForLanguageModeling(
            tokenizer=self.tokenizer,
            mlm=False,
            pad_to_multiple_of=8
        )
        
        # Trainer
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=eval_dataset,
            data_collator=data_collator,
            tokenizer=self.tokenizer
        )
        
        # Train
        train_result = trainer.train()
        
        # Save adapter
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        adapter_name = f"whis_adapter_{timestamp}"
        adapter_path = Path(training_config["output_dir"]) / adapter_name
        
        trainer.save_model(str(adapter_path))
        self.tokenizer.save_pretrained(str(adapter_path))
        
        # Log training results
        mlflow.log_metrics({
            "train_loss": train_result.training_loss,
            "train_steps": train_result.global_step,
            "train_samples": len(train_dataset)
        })
        
        # Log adapter artifacts
        mlflow.log_artifacts(str(adapter_path), "adapter")
        
        print(f"✅ Training completed. Adapter saved to: {adapter_path}")
        return str(adapter_path)


def main():
    """Main fine-tuning execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Fine-tune Whis SOAR copilot")
    parser.add_argument("--config", default="configs/model.whis.yaml", help="Config file")
    parser.add_argument("--dataset", required=True, help="Training dataset path")
    parser.add_argument("--eval-dataset", help="Evaluation dataset path")
    
    args = parser.parse_args()
    
    # Initialize trainer
    trainer = WhisFineTuner(args.config)
    
    # Setup experiment tracking
    trainer._setup_experiment_tracking()
    
    try:
        # Load model and tokenizer
        trainer.load_model_and_tokenizer()
        
        # Load and tokenize datasets
        train_dataset = trainer.load_dataset(args.dataset)
        tokenized_train = trainer.tokenize_dataset(train_dataset)
        
        eval_dataset = None
        if args.eval_dataset:
            eval_dataset = trainer.load_dataset(args.eval_dataset)
            eval_dataset = trainer.tokenize_dataset(eval_dataset)
            
        # Train
        adapter_path = trainer.train(tokenized_train, eval_dataset)
        
        print(f"🎉 Fine-tuning completed successfully!")
        print(f"📦 Adapter saved to: {adapter_path}")
        
    finally:
        # End MLflow run
        mlflow.end_run()


if __name__ == "__main__":
    main()