#!/usr/bin/env python3
"""
🛡️ RESOURCE-SAFE CHUNKED TRAINING
==================================
Trains in 25% chunks to prevent system overload
Uses existing whis-mega-consolidated-v1 SOAR dataset
"""

import json
import logging
import torch
import gc
import time
from pathlib import Path
from datetime import datetime
import sys
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

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

class ChunkedTrainer:
    def __init__(self, chunk_size=0.25):
        """Initialize with 25% chunk size for resource safety"""
        self.chunk_size = chunk_size
        self.dataset_path = None
        self.total_examples = 0
        self.current_chunk = 0
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = None
        self.tokenizer = None
        
    def find_soar_dataset(self):
        """Find the SOAR consolidated dataset"""
        data_dir = Path("ai-training/llm/data")
        
        # Look for fixed dataset first, then consolidated
        fixed_path = data_dir / "soar_fixed.jsonl"
        if fixed_path.exists():
            self.dataset_path = fixed_path
        else:
            candidates = list(data_dir.glob("soar_consolidated_*.jsonl"))
            if candidates:
                self.dataset_path = candidates[0]  # Use most recent
        
        if self.dataset_path:
            logger.info(f"📚 Found dataset: {self.dataset_path}")
            return True
            
        logger.error("❌ No SOAR consolidated dataset found!")
        return False
    
    def load_dataset_info(self):
        """Load dataset and count examples"""
        if not self.dataset_path:
            return False
            
        try:
            examples = []
            with open(self.dataset_path, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if line:
                        try:
                            examples.append(json.loads(line))
                        except json.JSONDecodeError as e:
                            logger.warning(f"⚠️ Skipping malformed line {line_num}: {str(e)[:50]}")
            
            self.total_examples = len(examples)
            logger.info(f"📊 Total examples: {self.total_examples}")
            
            # Show breakdown
            categories = {}
            for ex in examples:
                cat = ex.get('category', 'unknown')
                categories[cat] = categories.get(cat, 0) + 1
                
            logger.info("🎯 Dataset breakdown:")
            for cat, count in categories.items():
                logger.info(f"  - {cat.replace('_', ' ').title()}: {count}")
                
            return True
            
        except Exception as e:
            logger.error(f"❌ Error loading dataset: {e}")
            return False
    
    def get_chunk_data(self, chunk_num):
        """Get specific chunk of data (0-based)"""
        chunk_size_int = int(self.total_examples * self.chunk_size)
        start_idx = chunk_num * chunk_size_int
        end_idx = min(start_idx + chunk_size_int, self.total_examples)
        
        if start_idx >= self.total_examples:
            return None, 0, 0
            
        all_examples = []
        with open(self.dataset_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        all_examples.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
            
        chunk_data = all_examples[start_idx:end_idx]
        return chunk_data, start_idx, end_idx
    
    def clear_gpu_memory(self):
        """Aggressively clear GPU memory"""
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()
        gc.collect()
        time.sleep(2)  # Give system time to recover
        
    def monitor_gpu_usage(self):
        """Monitor and display GPU usage"""
        if torch.cuda.is_available():
            gpu_memory = torch.cuda.get_device_properties(0).total_memory // 1024**3
            gpu_allocated = torch.cuda.memory_allocated() // 1024**3  
            gpu_cached = torch.cuda.memory_reserved() // 1024**3
            gpu_free = gpu_memory - gpu_allocated
            usage_percent = (gpu_allocated / gpu_memory) * 100
            
            logger.info(f"🔥 GPU: {gpu_allocated}GB/{gpu_memory}GB ({usage_percent:.1f}%) | Free: {gpu_free}GB")
            
            if usage_percent > 90:
                logger.warning("⚠️ HIGH GPU USAGE - Consider reducing batch size")
            
            return usage_percent
        return 0
        
    def setup_model_and_tokenizer(self):
        """Setup model and tokenizer with 4-bit quantization for GPU training"""
        if self.model is not None:
            return True  # Already loaded
            
        logger.info("🔧 Setting up GPU model and tokenizer...")
        
        # Look for existing model
        model_paths = [
            "/home/jimmie/linkops-industries/SOAR-copilot/ai-training/llm/scripts/codellama-cache",
            "/home/jimmie/linkops-industries/SOAR-copilot/training/codellama-cache",
            "microsoft/DialoGPT-medium"  # Fallback
        ]
        
        base_model_path = None
        for path in model_paths:
            if Path(path).exists() or "/" in path:
                base_model_path = path
                break
                
        if not base_model_path:
            logger.error("❌ No suitable model found!")
            return False
            
        logger.info(f"📦 Using model: {base_model_path}")
        
        try:
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(base_model_path, trust_remote_code=True)
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            self.tokenizer.padding_side = "right"
            
            if torch.cuda.is_available():
                # 4-bit quantization config for GPU
                bnb_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=torch.bfloat16,
                    bnb_4bit_use_double_quant=True,
                    bnb_4bit_quant_type="nf4"
                )
                
                # Load model with quantization
                self.model = AutoModelForCausalLM.from_pretrained(
                    base_model_path,
                    quantization_config=bnb_config,
                    device_map="auto",
                    trust_remote_code=True,
                    torch_dtype=torch.bfloat16
                )
                
                # Prepare for k-bit training
                self.model = prepare_model_for_kbit_training(self.model)
                
                # LoRA config
                lora_config = LoraConfig(
                    task_type=TaskType.CAUSAL_LM,
                    inference_mode=False,
                    r=16,  # Moderate rank for chunked training
                    lora_alpha=32,
                    lora_dropout=0.1,
                    target_modules=["q_proj", "v_proj", "k_proj", "o_proj"]
                )
                
                # Check if we have an existing trained adapter
                adapter_path = "/home/jimmie/linkops-industries/SOAR-copilot/ai-training/llm/models/whis-mega-model"
                if Path(adapter_path).exists():
                    logger.info("🎯 Loading existing whis-mega-model adapter...")
                    from peft import PeftModel
                    self.model = PeftModel.from_pretrained(self.model, adapter_path)
                else:
                    # Create new LoRA adapter
                    self.model = get_peft_model(self.model, lora_config)
                
            else:
                # CPU fallback
                self.model = AutoModelForCausalLM.from_pretrained(
                    base_model_path,
                    trust_remote_code=True,
                    torch_dtype=torch.float32
                )
            
            logger.info("✅ GPU model and tokenizer loaded!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error setting up model: {e}")
            return False
        
    def train_single_chunk(self, chunk_num):
        """Train on a single chunk safely"""
        logger.info(f"\n🔥 TRAINING CHUNK {chunk_num + 1}")
        logger.info("=" * 50)
        
        # Clear memory before starting
        self.clear_gpu_memory()
        
        # Get chunk data
        chunk_data, start_idx, end_idx = self.get_chunk_data(chunk_num)
        
        if chunk_data is None:
            logger.info("✅ All chunks completed!")
            return False
            
        logger.info(f"📊 Chunk {chunk_num + 1}: {len(chunk_data)} examples ({start_idx}-{end_idx})")
        
        # Check GPU memory before training
        self.monitor_gpu_usage()
        
        if torch.cuda.is_available():
            usage_percent = torch.cuda.memory_allocated() / torch.cuda.get_device_properties(0).total_memory * 100
            if usage_percent > 80:
                logger.warning("⚠️ High GPU memory usage detected - clearing cache")
                self.clear_gpu_memory()
        
        # Save chunk for training
        chunk_file = f"temp_chunk_{chunk_num}.jsonl"
        with open(chunk_file, 'w') as f:
            for example in chunk_data:
                f.write(json.dumps(example) + '\n')
                
        logger.info(f"💾 Chunk saved to: {chunk_file}")
        
        # Real GPU training
        logger.info("🚀 Training chunk...")
        
        # Setup model if not already loaded
        if not self.setup_model_and_tokenizer():
            logger.error("❌ Failed to setup model for training")
            return False
            
        logger.info("   → Processing examples...")
        
        # Convert chunk to training format
        training_examples = []
        for example in chunk_data:
            # Convert SOAR format to text format
            instruction = example.get('instruction', '')
            response = example.get('response', '')
            
            if isinstance(response, dict):
                response = json.dumps(response)
                
            text = f"<|im_start|>user\n{instruction}<|im_end|>\n<|im_start|>assistant\n{response}<|im_end|>"
            training_examples.append({"text": text})
        
        # Create dataset
        chunk_dataset = Dataset.from_list(training_examples)
        
        # Tokenize
        def tokenize_function(examples):
            return self.tokenizer(
                examples["text"],
                truncation=True,
                max_length=512,
                padding=False
            )
        
        tokenized_dataset = chunk_dataset.map(
            tokenize_function,
            batched=True,
            remove_columns=chunk_dataset.column_names
        )
        
        logger.info("   → Setting up training...")
        
        # Training arguments for chunk
        training_args = TrainingArguments(
            output_dir=f"./results/training_chunks/chunk_model_{chunk_num}",
            per_device_train_batch_size=1,
            gradient_accumulation_steps=2,
            num_train_epochs=1,  # Single epoch per chunk
            learning_rate=2e-4,
            bf16=True,  # Use bf16 instead of fp16 for RTX 5080
            logging_steps=10,
            save_steps=1000,
            warmup_steps=5,
            dataloader_drop_last=True,
            report_to=None,
            remove_unused_columns=False,
            save_strategy="no",  # Don't save intermediate checkpoints
            dataloader_num_workers=0,  # Avoid multiprocessing issues
            group_by_length=False,  # Simplify for stability
            optim="adamw_torch"  # Use standard optimizer
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
            train_dataset=tokenized_dataset,
            data_collator=data_collator,
            tokenizer=self.tokenizer,
        )
        
        logger.info("   → GPU training in progress...")
        
        # Train the chunk
        trainer.train()
        
        logger.info("   → Saving progress...")
        
        # Save only if final chunk
        if chunk_num >= self.get_total_chunks() - 1:
            trainer.save_model(f"./models/soar_model_final")
            self.tokenizer.save_pretrained(f"./models/soar_model_final")
            logger.info("   → Final model saved to ./models/soar_model_final!")
        
        # Clean up but keep model loaded for next chunk
        Path(chunk_file).unlink(missing_ok=True)
        
        # Only clear cache, don't destroy the model
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        gc.collect()
        
        logger.info(f"✅ Chunk {chunk_num + 1} complete!")
        
        # Save progress
        progress = {
            "timestamp": datetime.now().isoformat(),
            "chunk": chunk_num + 1,
            "total_chunks": self.get_total_chunks(),
            "examples_processed": end_idx,
            "total_examples": self.total_examples,
            "completion_percentage": round((end_idx / self.total_examples) * 100, 1)
        }
        
        Path("results").mkdir(exist_ok=True)
        with open(f"results/chunk_{chunk_num + 1}_progress.json", 'w') as f:
            json.dump(progress, f, indent=2)
            
        logger.info(f"📈 Progress: {progress['completion_percentage']}% complete")
        
        return True
    
    def get_total_chunks(self):
        """Calculate total number of chunks needed"""
        return (self.total_examples + int(self.total_examples * self.chunk_size) - 1) // int(self.total_examples * self.chunk_size)
    
    def train_all_chunks(self):
        """Train all chunks sequentially"""
        logger.info("\n🚀 STARTING CHUNKED TRAINING")
        logger.info("=" * 60)
        logger.info(f"📊 Dataset: {self.total_examples} examples")
        logger.info(f"🔢 Chunk size: {int(self.chunk_size * 100)}% ({int(self.total_examples * self.chunk_size)} examples per chunk)")
        logger.info(f"📦 Total chunks: {self.get_total_chunks()}")
        
        chunk_num = 0
        while True:
            success = self.train_single_chunk(chunk_num)
            if not success:
                break
                
            chunk_num += 1
            
            # Pause between chunks for system recovery
            logger.info("⏸️ Pausing 10 seconds for system recovery...")
            time.sleep(10)
            
        logger.info("\n🎉 ALL CHUNKS COMPLETED!")
        logger.info("=" * 60)
        
        # Final summary
        final_summary = {
            "timestamp": datetime.now().isoformat(),
            "status": "TRAINING_COMPLETE",
            "total_examples": self.total_examples,
            "chunks_processed": chunk_num,
            "chunk_size_percentage": int(self.chunk_size * 100),
            "dataset_file": str(self.dataset_path)
        }
        
        with open("results/final_training_summary.json", 'w') as f:
            json.dump(final_summary, f, indent=2)
            
        logger.info(f"📋 Final summary: results/final_training_summary.json")

def main():
    print("🛡️ RESOURCE-SAFE SOAR TRAINING")
    print("=" * 60)
    
    # Initialize trainer
    trainer = ChunkedTrainer(chunk_size=0.25)  # 25% chunks
    
    # Find and load dataset
    if not trainer.find_soar_dataset():
        print("❌ Could not find SOAR dataset")
        sys.exit(1)
        
    if not trainer.load_dataset_info():
        print("❌ Could not load dataset info")
        sys.exit(1)
    
    # Check system resources
    if torch.cuda.is_available():
        gpu_name = torch.cuda.get_device_name()
        gpu_memory = torch.cuda.get_device_properties(0).total_memory // 1024**3
        print(f"🔥 GPU: {gpu_name} ({gpu_memory}GB)")
        
        if gpu_memory < 8:
            print("⚠️ Warning: Low GPU memory. Consider smaller chunks if training fails.")
    else:
        print("⚠️ No GPU detected - using CPU (will be slower)")
    
    print("\n🛡️ SAFETY FEATURES ACTIVE:")
    print("✅ 25% chunk size to prevent overload")
    print("✅ Memory clearing between chunks")  
    print("✅ 10-second recovery pauses")
    print("✅ Progress saving after each chunk")
    print("✅ Automatic cleanup of temp files")
    
    # Ask for confirmation
    print(f"\n🎯 Ready to train {trainer.total_examples} examples in {trainer.get_total_chunks()} chunks")
    response = input("Continue? (y/N): ")
    
    if response.lower() != 'y':
        print("❌ Training cancelled")
        sys.exit(0)
    
    # Start training
    trainer.train_all_chunks()
    
    print("\n🎉 TRAINING COMPLETE!")
    print("🔍 Check results/ directory for progress files")

if __name__ == "__main__":
    main()