"""
LLM Engine: Hugging Face model integration for Whis SOAR
Uses our locally trained SOAR model for security analysis
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any
from pathlib import Path
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel
import json

logger = logging.getLogger(__name__)


class LLMEngine:
    """
    LLM Engine using our trained SOAR model
    Provides async interface for Whis integration
    """
    
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model_loaded = False
        
        # Model paths
        self.base_model_path = "/home/jimmie/linkops-industries/SOAR-copilot/ai-training/llm/scripts/codellama-cache"
        self.trained_model_path = "/home/jimmie/linkops-industries/SOAR-copilot/models/soar_model_final"
        
    async def initialize(self):
        """Initialize the LLM model asynchronously"""
        if self.model_loaded:
            return True
            
        logger.info("🚀 Initializing SOAR LLM Engine...")
        logger.info(f"📦 Base model: {self.base_model_path}")
        logger.info(f"🎯 Trained model: {self.trained_model_path}")
        
        try:
            # Run model loading in thread pool to avoid blocking
            await asyncio.get_event_loop().run_in_executor(
                None, self._load_model
            )
            
            self.model_loaded = True
            logger.info("✅ SOAR LLM Engine initialized successfully!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize LLM Engine: {e}")
            return False
    
    def _load_model(self):
        """Load the model synchronously (runs in thread pool)"""
        # Check if trained model exists
        if not Path(self.trained_model_path).exists():
            logger.warning(f"⚠️ Trained model not found at {self.trained_model_path}")
            logger.info("Using base model without SOAR training...")
            trained_model_path = None
        else:
            trained_model_path = self.trained_model_path
        
        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.base_model_path, 
            trust_remote_code=True
        )
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        
        # Load base model
        self.model = AutoModelForCausalLM.from_pretrained(
            self.base_model_path,
            torch_dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32,
            device_map="auto" if torch.cuda.is_available() else None,
            trust_remote_code=True
        )
        
        # Load trained adapter if available
        if trained_model_path:
            logger.info("🎯 Loading trained SOAR adapter...")
            self.model = PeftModel.from_pretrained(self.model, trained_model_path)
            logger.info("✅ SOAR adapter loaded!")
        
    async def generate_response(
        self, 
        prompt: str, 
        max_tokens: int = 500, 
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """
        Generate response from the LLM
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            
        Returns:
            Generated response text
        """
        if not self.model_loaded:
            logger.warning("⚠️ Model not initialized, initializing now...")
            await self.initialize()
        
        if not self.model_loaded:
            raise RuntimeError("LLM Engine failed to initialize")
        
        try:
            # Run generation in thread pool to avoid blocking
            response = await asyncio.get_event_loop().run_in_executor(
                None, 
                self._generate_sync,
                prompt,
                max_tokens,
                temperature
            )
            
            return response
            
        except Exception as e:
            logger.error(f"❌ LLM generation failed: {e}")
            return f"Error generating response: {str(e)}"
    
    def _generate_sync(self, prompt: str, max_tokens: int, temperature: float) -> str:
        """Synchronous generation (runs in thread pool)"""
        # Format prompt for SOAR model training format
        formatted_prompt = f"<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n"
        
        # Tokenize
        inputs = self.tokenizer(
            formatted_prompt, 
            return_tensors="pt", 
            truncation=True, 
            max_length=1024
        )
        
        # Move to device
        if torch.cuda.is_available():
            inputs = {k: v.to(self.model.device) for k, v in inputs.items()}
        
        # Generate
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                temperature=temperature,
                do_sample=temperature > 0,
                pad_token_id=self.tokenizer.eos_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
                repetition_penalty=1.1
            )
        
        # Decode
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract assistant response
        if "<|im_start|>assistant\n" in response:
            response = response.split("<|im_start|>assistant\n")[-1].strip()
        
        # Clean up response
        if "<|im_end|>" in response:
            response = response.split("<|im_end|>")[0].strip()
            
        return response
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get engine health status"""
        return {
            "status": "healthy" if self.model_loaded else "not_ready",
            "model_loaded": self.model_loaded,
            "device": self.device,
            "base_model": "CodeLlama-7B" if self.model_loaded else None,
            "soar_adapter": Path(self.trained_model_path).exists(),
            "memory_usage": self._get_memory_usage() if torch.cuda.is_available() else None
        }
    
    def _get_memory_usage(self) -> Dict[str, float]:
        """Get GPU memory usage if available"""
        if torch.cuda.is_available():
            allocated = torch.cuda.memory_allocated() / 1024**3  # GB
            cached = torch.cuda.memory_reserved() / 1024**3     # GB
            total = torch.cuda.get_device_properties(0).total_memory / 1024**3  # GB
            
            return {
                "allocated_gb": round(allocated, 2),
                "cached_gb": round(cached, 2), 
                "total_gb": round(total, 2),
                "usage_percent": round((allocated / total) * 100, 1)
            }
        return {}


# Global instance
_llm_engine = None

async def get_llm_engine() -> LLMEngine:
    """Get or create global LLM engine instance"""
    global _llm_engine
    if _llm_engine is None:
        _llm_engine = LLMEngine()
        await _llm_engine.initialize()
    
    return _llm_engine


async def test_llm_engine():
    """Test function for the LLM engine"""
    print("🧪 Testing LLM Engine...")
    
    engine = await get_llm_engine()
    
    # Test prompt
    test_prompt = """
    Analyze this security event:
    - Event ID: 4625 (Failed logon)
    - Source IP: 192.168.1.100
    - Target Account: admin
    - Frequency: 50 attempts in 5 minutes
    
    Provide SOAR analysis and recommendations.
    """
    
    print("📝 Test prompt:", test_prompt[:100] + "...")
    
    response = await engine.generate_response(
        prompt=test_prompt,
        max_tokens=300,
        temperature=0.7
    )
    
    print("🤖 Response:", response)
    
    # Health check
    health = await engine.get_health_status()
    print("🏥 Health status:", json.dumps(health, indent=2))


if __name__ == "__main__":
    asyncio.run(test_llm_engine())