"""
Optimized Model Configuration for RTX 5080 (17GB)
Following mentor's recommendations for robust training
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
import torch
from transformers import TrainingArguments, BitsAndBytesConfig
from peft import LoraConfig, TaskType

@dataclass
class OptimizedWhisConfig:
    """Optimized configuration for 17GB RTX 5080"""
    
    # Base Model Selection
    base_model_id: str = "codellama/CodeLlama-7b-Instruct-hf"
    model_name: str = "whis-cybersec-7b-optimized"
    
    # Model Parameters - Optimized for 17GB
    max_sequence_length: int = 2048  # Safe for memory, good for security context
    temperature: float = 0.3  # Deterministic security analysis
    top_p: float = 0.9
    do_sample: bool = True
    
    # LoRA Configuration - Mentor's recommendations
    use_lora: bool = True
    lora_rank: int = 16  # Sweet spot for 17GB GPU
    lora_alpha: int = 32  # 2x rank as recommended
    lora_dropout: float = 0.1
    target_modules: List[str] = None
    
    # Quantization - Optimized for performance
    use_4bit: bool = True
    bnb_4bit_compute_dtype: str = "bfloat16"  # Better than float16
    bnb_4bit_quant_type: str = "nf4"
    use_nested_quant: bool = False
    
    # Training Parameters - Memory optimized
    output_dir: str = "./whis-cybersec-model"
    num_train_epochs: int = 3
    per_device_train_batch_size: int = 2  # Conservative for stability
    per_device_eval_batch_size: int = 2
    gradient_accumulation_steps: int = 4  # Effective batch size = 8
    gradient_checkpointing: bool = True  # Memory optimization
    learning_rate: float = 2e-4
    weight_decay: float = 0.001
    warmup_ratio: float = 0.03
    max_grad_norm: float = 0.3
    
    # Checkpoint and logging - Early saves for demo
    save_steps: int = 100  # Save LoRA adapter every 100 steps
    logging_steps: int = 10
    eval_steps: int = 100
    evaluation_strategy: str = "steps"
    save_strategy: str = "steps"
    load_best_model_at_end: bool = True
    save_total_limit: int = 3  # Keep only 3 checkpoints
    
    # OOM Safety Fallbacks
    fallback_batch_size: int = 1
    fallback_lora_rank: int = 8
    fallback_sequence_length: int = 1536
    
    def __post_init__(self):
        """Set default target modules for LoRA"""
        if self.target_modules is None:
            self.target_modules = [
                "q_proj", "k_proj", "v_proj", "o_proj",
                "gate_proj", "up_proj", "down_proj", "lm_head"
            ]
    
    def get_bnb_config(self) -> BitsAndBytesConfig:
        """Optimized 4-bit quantization config"""
        return BitsAndBytesConfig(
            load_in_4bit=self.use_4bit,
            bnb_4bit_compute_dtype=getattr(torch, self.bnb_4bit_compute_dtype),
            bnb_4bit_quant_type=self.bnb_4bit_quant_type,
            bnb_4bit_use_double_quant=self.use_nested_quant,
        )
    
    def get_lora_config(self) -> LoraConfig:
        """Optimized LoRA configuration"""
        return LoraConfig(
            r=self.lora_rank,
            lora_alpha=self.lora_alpha,
            target_modules=self.target_modules,
            lora_dropout=self.lora_dropout,
            bias="none",
            task_type=TaskType.CAUSAL_LM,
        )
    
    def get_training_arguments(self) -> TrainingArguments:
        """Optimized training arguments"""
        return TrainingArguments(
            output_dir=self.output_dir,
            num_train_epochs=self.num_train_epochs,
            per_device_train_batch_size=self.per_device_train_batch_size,
            per_device_eval_batch_size=self.per_device_eval_batch_size,
            gradient_accumulation_steps=self.gradient_accumulation_steps,
            gradient_checkpointing=self.gradient_checkpointing,
            learning_rate=self.learning_rate,
            weight_decay=self.weight_decay,
            warmup_ratio=self.warmup_ratio,
            max_grad_norm=self.max_grad_norm,
            logging_steps=self.logging_steps,
            eval_steps=self.eval_steps,
            save_steps=self.save_steps,
            evaluation_strategy=self.evaluation_strategy,
            save_strategy=self.save_strategy,
            load_best_model_at_end=self.load_best_model_at_end,
            save_total_limit=self.save_total_limit,
            report_to="tensorboard",
            fp16=False,  # Using bfloat16 via quantization
            bf16=True,   # Better than fp16
            dataloader_pin_memory=False,
            remove_unused_columns=False,
        )
    
    def get_oom_fallback_config(self):
        """Get fallback config if we hit OOM"""
        fallback = OptimizedWhisConfig()
        fallback.per_device_train_batch_size = self.fallback_batch_size
        fallback.lora_rank = self.fallback_lora_rank  
        fallback.max_sequence_length = self.fallback_sequence_length
        fallback.gradient_accumulation_steps = 8  # Maintain effective batch
        return fallback
    
    def log_config(self) -> Dict:
        """Log exact configuration for reproducibility"""
        return {
            "model_config": {
                "base_model": self.base_model_id,
                "max_seq_len": self.max_sequence_length,
                "temperature": self.temperature
            },
            "lora_config": {
                "rank": self.lora_rank,
                "alpha": self.lora_alpha,
                "dropout": self.lora_dropout,
                "target_modules": self.target_modules
            },
            "quantization": {
                "use_4bit": self.use_4bit,
                "compute_dtype": self.bnb_4bit_compute_dtype,
                "quant_type": self.bnb_4bit_quant_type
            },
            "training": {
                "epochs": self.num_train_epochs,
                "batch_size": self.per_device_train_batch_size,
                "gradient_accumulation": self.gradient_accumulation_steps,
                "effective_batch_size": self.per_device_train_batch_size * self.gradient_accumulation_steps,
                "learning_rate": self.learning_rate,
                "gradient_checkpointing": self.gradient_checkpointing
            },
            "hardware": {
                "gpu_memory_gb": 17.1,
                "cuda_version": torch.version.cuda,
                "pytorch_version": torch.__version__
            }
        }

# Global optimized config instance
optimized_config = OptimizedWhisConfig()