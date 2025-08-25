#!/usr/bin/env python3
"""
🧪 Test Our Trained SOAR Model
==============================
Test if our newly trained model gives good SOAR advice
"""

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel
import json
from pathlib import Path

def load_trained_model():
    """Load our newly trained SOAR model"""
    print("🔧 Loading trained SOAR model...")
    
    # Base model path (CodeLlama)
    base_model_path = "/home/jimmie/linkops-industries/SOAR-copilot/ai-training/llm/scripts/codellama-cache"
    
    # Our trained model path
    trained_model_path = "./models/soar_model_final"
    
    if not Path(trained_model_path).exists():
        print("❌ Trained model not found! Did training complete?")
        return None, None
    
    print(f"📦 Base model: {base_model_path}")
    print(f"🎯 Trained model: {trained_model_path}")
    
    # Load tokenizer
    tokenizer = AutoTokenizer.from_pretrained(base_model_path, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    # Load base model
    model = AutoModelForCausalLM.from_pretrained(
        base_model_path,
        torch_dtype=torch.bfloat16,
        device_map="auto",
        trust_remote_code=True
    )
    
    # Load trained adapter
    model = PeftModel.from_pretrained(model, trained_model_path)
    
    print("✅ Model loaded successfully!")
    return model, tokenizer

def test_soar_questions():
    """Test the model with SOAR-related questions"""
    return [
        {
            "type": "malware_analysis", 
            "question": "I found a suspicious executable making network connections. How should I analyze this potential malware?",
            "expected_topics": ["sandbox", "static analysis", "network analysis", "indicators"]
        },
        {
            "type": "incident_response",
            "question": "We detected multiple failed login attempts from the same IP. What SOAR actions should we take?",
            "expected_topics": ["account lockdown", "IP blocking", "investigation", "monitoring"]
        },
        {
            "type": "threat_hunting",
            "question": "How can I hunt for lateral movement in our network after a potential compromise?",
            "expected_topics": ["network logs", "authentication events", "process monitoring", "indicators"]
        },
        {
            "type": "vulnerability_response",
            "question": "A critical vulnerability was discovered in our web servers. What's the SOAR response plan?",
            "expected_topics": ["patching", "isolation", "assessment", "communication"]
        }
    ]

def generate_response(model, tokenizer, question):
    """Generate response from our trained model"""
    # Format as training format
    prompt = f"<|im_start|>user\n{question}<|im_end|>\n<|im_start|>assistant\n"
    
    # Tokenize
    inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=400)
    inputs = {k: v.to(model.device) for k, v in inputs.items()}
    
    # Generate
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=200,
            temperature=0.7,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id,
            eos_token_id=tokenizer.eos_token_id
        )
    
    # Decode response
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    # Extract just the assistant's response
    if "<|im_start|>assistant\n" in response:
        response = response.split("<|im_start|>assistant\n")[-1]
    
    return response.strip()

def evaluate_response(response, expected_topics):
    """Simple evaluation of response quality"""
    response_lower = response.lower()
    found_topics = []
    
    for topic in expected_topics:
        if any(word in response_lower for word in topic.lower().split()):
            found_topics.append(topic)
    
    coverage = len(found_topics) / len(expected_topics)
    
    return {
        "coverage_score": coverage,
        "found_topics": found_topics,
        "length": len(response.split()),
        "has_actionable_advice": any(word in response_lower for word in ["should", "recommend", "action", "step"])
    }

def main():
    print("🧪 TESTING TRAINED SOAR MODEL")
    print("=" * 50)
    
    # Load model
    model, tokenizer = load_trained_model()
    if model is None:
        return
    
    # Test questions
    questions = test_soar_questions()
    
    results = []
    
    for i, test_case in enumerate(questions, 1):
        print(f"\n📋 TEST {i}: {test_case['type'].title()}")
        print("-" * 40)
        print(f"❓ Question: {test_case['question']}")
        
        # Generate response
        response = generate_response(model, tokenizer, test_case['question'])
        print(f"\n🤖 Response:\n{response}")
        
        # Evaluate
        eval_result = evaluate_response(response, test_case['expected_topics'])
        
        print(f"\n📊 Evaluation:")
        print(f"  Coverage Score: {eval_result['coverage_score']:.2f}")
        print(f"  Found Topics: {eval_result['found_topics']}")
        print(f"  Response Length: {eval_result['length']} words")
        print(f"  Has Actionable Advice: {eval_result['has_actionable_advice']}")
        
        results.append({
            "test_case": test_case,
            "response": response,
            "evaluation": eval_result
        })
        
        print("\n" + "="*50)
    
    # Overall assessment
    avg_coverage = sum(r['evaluation']['coverage_score'] for r in results) / len(results)
    actionable_count = sum(1 for r in results if r['evaluation']['has_actionable_advice'])
    
    print(f"\n🎯 OVERALL RESULTS:")
    print(f"  Average Topic Coverage: {avg_coverage:.2f}")
    print(f"  Tests with Actionable Advice: {actionable_count}/{len(results)}")
    print(f"  Average Response Length: {sum(r['evaluation']['length'] for r in results) / len(results):.1f} words")
    
    # Assessment
    if avg_coverage >= 0.6 and actionable_count >= len(results) * 0.75:
        print("\n✅ MODEL ASSESSMENT: GOOD - Ready for integration!")
        print("The model shows strong SOAR knowledge and provides actionable advice.")
    elif avg_coverage >= 0.4:
        print("\n⚠️ MODEL ASSESSMENT: FAIR - Needs some improvement")
        print("The model has basic SOAR knowledge but could be more comprehensive.")
    else:
        print("\n❌ MODEL ASSESSMENT: POOR - Needs more training")
        print("The model lacks sufficient SOAR knowledge. Consider more training data.")
    
    # Save results
    with open("model_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to: model_test_results.json")

if __name__ == "__main__":
    main()