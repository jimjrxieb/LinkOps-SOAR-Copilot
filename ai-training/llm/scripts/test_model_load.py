#!/usr/bin/env python3
"""
Test if CodeLlama model loads correctly
"""

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
import time

print("🧪 TESTING MODEL LOAD")
print("=" * 40)

# Check GPU
print(f"🎮 CUDA Available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"📍 GPU Device: {torch.cuda.get_device_name(0)}")
    print(f"💾 GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")

print("\n📦 Loading tokenizer...")
start = time.time()

try:
    tokenizer = AutoTokenizer.from_pretrained(
        "codellama/CodeLlama-7b-Instruct-hf",
        trust_remote_code=True,
        local_files_only=False  # Allow downloading if needed
    )
    print(f"✅ Tokenizer loaded in {time.time() - start:.1f}s")
    
    print("\n🤖 Loading model with 4-bit quantization...")
    start = time.time()
    
    # 4-bit config for memory efficiency
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4"
    )
    
    model = AutoModelForCausalLM.from_pretrained(
        "codellama/CodeLlama-7b-Instruct-hf",
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
        local_files_only=False  # Allow downloading if needed
    )
    
    print(f"✅ Model loaded in {time.time() - start:.1f}s")
    
    # Test generation
    print("\n🧪 Testing generation...")
    test_prompt = "def hello_world():"
    inputs = tokenizer(test_prompt, return_tensors="pt")
    
    with torch.no_grad():
        outputs = model.generate(
            inputs.input_ids.to(model.device),
            max_new_tokens=20,
            temperature=0.7
        )
    
    result = tokenizer.decode(outputs[0], skip_special_tokens=True)
    print(f"📝 Generated: {result}")
    
    print("\n✅ MODEL LOAD TEST SUCCESSFUL!")
    
except Exception as e:
    print(f"\n❌ Error loading model: {e}")
    print("\n💡 Troubleshooting:")
    print("1. Check internet connection")
    print("2. Try: huggingface-cli login")
    print("3. Clear cache: rm -rf ~/.cache/huggingface/hub/models--codellama*")
    
finally:
    # Cleanup
    if 'model' in locals():
        del model
    torch.cuda.empty_cache()