"""
HuggingFace Model Configuration for Whis Cybersecurity LLM
Optimized for SOAR operations, security analysis, and technical documentation
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
import torch
from transformers import (
    LlamaForCausalLM, 
    CodeLlamaTokenizer,
    TrainingArguments,
    BitsAndBytesConfig
)
from peft import LoraConfig, TaskType

@dataclass
class WhisModelConfig:
    """Configuration for Whis cybersecurity LLM"""
    
    # Base Model Selection
    base_model_id: str = "codellama/CodeLlama-7b-Instruct-hf"
    model_name: str = "whis-cybersec-7b"
    
    # Model Parameters
    max_sequence_length: int = 4096  # Good for security incident context
    temperature: float = 0.3  # Lower for more deterministic security analysis
    top_p: float = 0.9
    do_sample: bool = True
    
    # Fine-tuning Configuration
    use_lora: bool = True  # LoRA for efficient fine-tuning
    lora_rank: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.1
    target_modules: List[str] = None
    
    # Quantization for efficiency
    use_4bit: bool = True
    bnb_4bit_compute_dtype: str = "float16"
    bnb_4bit_quant_type: str = "nf4"
    use_nested_quant: bool = False
    
    # Training Parameters
    output_dir: str = "./whis-cybersec-model"
    num_train_epochs: int = 3
    per_device_train_batch_size: int = 4
    per_device_eval_batch_size: int = 4
    gradient_accumulation_steps: int = 4
    learning_rate: float = 2e-4
    weight_decay: float = 0.001
    warmup_ratio: float = 0.03
    max_grad_norm: float = 0.3
    
    # Logging and Evaluation
    logging_steps: int = 10
    eval_steps: int = 100
    save_steps: int = 500
    evaluation_strategy: str = "steps"
    save_strategy: str = "steps"
    load_best_model_at_end: bool = True
    
    def __post_init__(self):
        """Set default target modules for LoRA"""
        if self.target_modules is None:
            self.target_modules = [
                "q_proj",
                "k_proj", 
                "v_proj",
                "o_proj",
                "gate_proj",
                "up_proj",
                "down_proj",
                "lm_head"
            ]

    def get_bnb_config(self) -> BitsAndBytesConfig:
        """Configure 4-bit quantization for memory efficiency"""
        return BitsAndBytesConfig(
            load_in_4bit=self.use_4bit,
            bnb_4bit_compute_dtype=getattr(torch, self.bnb_4bit_compute_dtype),
            bnb_4bit_quant_type=self.bnb_4bit_quant_type,
            bnb_4bit_use_double_quant=self.use_nested_quant,
        )

    def get_lora_config(self) -> LoraConfig:
        """Configure LoRA for parameter-efficient fine-tuning"""
        return LoraConfig(
            r=self.lora_rank,
            lora_alpha=self.lora_alpha,
            target_modules=self.target_modules,
            lora_dropout=self.lora_dropout,
            bias="none",
            task_type=TaskType.CAUSAL_LM,
        )

    def get_training_arguments(self) -> TrainingArguments:
        """Configure training parameters"""
        return TrainingArguments(
            output_dir=self.output_dir,
            num_train_epochs=self.num_train_epochs,
            per_device_train_batch_size=self.per_device_train_batch_size,
            per_device_eval_batch_size=self.per_device_eval_batch_size,
            gradient_accumulation_steps=self.gradient_accumulation_steps,
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
            report_to="tensorboard",
            fp16=True,  # Mixed precision training
            dataloader_pin_memory=False,
            remove_unused_columns=False,
        )

# Cybersecurity Domain Specializations
CYBERSEC_DOMAINS = {
    "attack_techniques": {
        "description": "MITRE ATT&CK techniques and tactics",
        "examples": ["T1110 Brute Force", "T1566 Phishing", "T1055 Process Injection"]
    },
    "detection_rules": {
        "description": "SIEM detection rules and queries",
        "examples": ["Splunk SPL", "Sigma rules", "LimaCharlie D&R rules"]
    },
    "incident_response": {
        "description": "IR playbooks and procedures", 
        "examples": ["Containment actions", "Evidence collection", "Remediation steps"]
    },
    "vulnerability_analysis": {
        "description": "CVE analysis and exploitation techniques",
        "examples": ["CVE-2023-34362", "Log4Shell analysis", "Windows privilege escalation"]
    },
    "compliance_frameworks": {
        "description": "Security standards and certifications",
        "examples": ["NIST CSF", "CIS Controls", "SOC 2", "ISO 27001"]
    },
    "cloud_security": {
        "description": "Cloud security best practices",
        "examples": ["AWS security", "Azure security", "Kubernetes security", "CKS concepts"]
    },
    "security_tools": {
        "description": "Security tool configuration and usage",
        "examples": ["Splunk administration", "LimaCharlie deployment", "SOAR automation"]
    }
}

def get_model_info() -> Dict:
    """Get comprehensive model information"""
    return {
        "model_name": "Whis Cybersecurity LLM",
        "base_model": "CodeLlama-7B-Instruct",
        "specialization": "Security Operations & Analysis",
        "capabilities": [
            "MITRE ATT&CK technique explanation",
            "Security incident analysis",
            "Detection rule creation",
            "SOAR playbook routing",
            "Compliance framework guidance",
            "Vulnerability assessment",
            "Code security analysis"
        ],
        "training_domains": list(CYBERSEC_DOMAINS.keys()),
        "target_certifications": ["CKS", "CCSP", "CISSP", "GCIH", "GIAC"],
        "integration_points": [
            "Splunk SIEM",
            "LimaCharlie EDR",
            "SOAR platforms",
            "Threat intelligence feeds"
        ]
    }