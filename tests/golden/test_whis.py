#!/usr/bin/env python3
"""
Whis Model Testing Suite
Tests the trained cybersecurity SOAR copilot with validation cases
"""

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import PeftModel, PeftConfig
from knowledge.rag_retriever import WhisRAGRetriever
import json
from datetime import datetime

print("🧪 WHIS MODEL TESTING SUITE")
print("=" * 50)

class WhisTester:
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.rag_retriever = WhisRAGRetriever()
        self.test_results = []
        
    def load_model(self):
        """Load the trained Whis model"""
        print("📦 Loading Whis trained model...")
        
        # Model paths
        base_model_path = "/home/jimmie/linkops-industries/SOAR-copilot/training/codellama-cache"
        lora_model_path = "./whis-cybersec-model"
        
        # Load tokenizer
        print("  🔤 Loading tokenizer...")
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
        print("  🤖 Loading base model with 4-bit quantization...")
        base_model = AutoModelForCausalLM.from_pretrained(
            base_model_path,
            quantization_config=bnb_config,
            device_map="auto",
            trust_remote_code=True
        )
        
        # Load LoRA adapter
        print("  🔧 Loading LoRA adapter...")
        self.model = PeftModel.from_pretrained(base_model, lora_model_path)
        
        print("✅ Whis model loaded successfully!")
        return self.model
        
    def generate_response(self, prompt: str, max_length: int = 512, temperature: float = 0.7) -> str:
        """Generate response from Whis model"""
        inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=1024)
        inputs = {k: v.to(self.model.device) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_length=inputs['input_ids'].shape[1] + max_length,
                temperature=temperature,
                do_sample=True,
                top_p=0.9,
                repetition_penalty=1.1,
                pad_token_id=self.tokenizer.eos_token_id
            )
        
        # Decode only the new tokens (response)
        response = self.tokenizer.decode(
            outputs[0][inputs['input_ids'].shape[1]:], 
            skip_special_tokens=True
        ).strip()
        
        return response
        
    def test_teacher_mode(self):
        """Test Teacher mode responses"""
        print("\n👨‍🏫 TESTING TEACHER MODE")
        print("-" * 30)
        
        teacher_tests = [
            {
                "name": "MITRE ATT&CK Explanation",
                "prompt": "Explain MITRE ATT&CK T1110.004 (Credential Stuffing) with detection strategies.",
                "expected_elements": ["T1110.004", "credential stuffing", "detection", "authentication", "failed logon"]
            },
            {
                "name": "Windows Event Analysis", 
                "prompt": "What is Windows Event ID 4625 and how is it used for security monitoring?",
                "expected_elements": ["4625", "failed logon", "security", "authentication", "monitoring"]
            },
            {
                "name": "Splunk Query Education",
                "prompt": "How do you create a Splunk search to detect brute force attacks?",
                "expected_elements": ["splunk", "search", "brute force", "EventCode=4625", "authentication"]
            }
        ]
        
        for i, test in enumerate(teacher_tests, 1):
            print(f"\n🔬 Test {i}: {test['name']}")
            
            # Create RAG-enhanced prompt
            rag_prompt = self.rag_retriever.generate_rag_prompt(
                test['prompt'], 
                mode="teacher"
            )
            
            print(f"📝 Prompt: {test['prompt']}")
            
            # Generate response
            response = self.generate_response(rag_prompt, max_length=300)
            print(f"🤖 Response: {response[:200]}{'...' if len(response) > 200 else ''}")
            
            # Check for expected elements
            matches = sum(1 for element in test['expected_elements'] 
                         if element.lower() in response.lower())
            score = matches / len(test['expected_elements'])
            
            print(f"✅ Score: {score:.2f} ({matches}/{len(test['expected_elements'])} elements found)")
            
            self.test_results.append({
                "mode": "teacher",
                "test": test['name'],
                "prompt": test['prompt'],
                "response": response,
                "score": score,
                "elements_found": matches,
                "total_elements": len(test['expected_elements'])
            })
            
    def test_assistant_mode(self):
        """Test Assistant mode responses"""
        print("\n🤖 TESTING ASSISTANT MODE")  
        print("-" * 30)
        
        assistant_tests = [
            {
                "name": "SOAR Playbook Generation",
                "prompt": "Create a SOAR response plan for a brute force authentication attack with 50 failed logons from external IP.",
                "expected_elements": ["playbook", "response", "authentication", "block", "investigate", "containment"]
            },
            {
                "name": "LimaCharlie Automation",
                "prompt": "Generate LimaCharlie EDR automation rules to detect and respond to suspicious process injection.",
                "expected_elements": ["limacharlie", "automation", "detection", "process injection", "response", "rule"]
            },
            {
                "name": "Incident Response Actions",
                "prompt": "Provide immediate response actions for a detected ransomware attack on domain controller.",
                "expected_elements": ["ransomware", "domain controller", "isolate", "containment", "backup", "forensics"]
            }
        ]
        
        for i, test in enumerate(assistant_tests, 1):
            print(f"\n🔬 Test {i}: {test['name']}")
            
            # Create RAG-enhanced prompt
            rag_prompt = self.rag_retriever.generate_rag_prompt(
                test['prompt'], 
                mode="assistant"
            )
            
            print(f"📝 Prompt: {test['prompt']}")
            
            # Generate response
            response = self.generate_response(rag_prompt, max_length=400)
            print(f"🤖 Response: {response[:200]}{'...' if len(response) > 200 else ''}")
            
            # Check for expected elements
            matches = sum(1 for element in test['expected_elements'] 
                         if element.lower() in response.lower())
            score = matches / len(test['expected_elements'])
            
            print(f"✅ Score: {score:.2f} ({matches}/{len(test['expected_elements'])} elements found)")
            
            self.test_results.append({
                "mode": "assistant",
                "test": test['name'],
                "prompt": test['prompt'],
                "response": response,
                "score": score,
                "elements_found": matches,
                "total_elements": len(test['expected_elements'])
            })
            
    def test_rag_retrieval(self):
        """Test RAG retrieval accuracy"""
        print("\n🔍 TESTING RAG RETRIEVAL")
        print("-" * 30)
        
        rag_tests = [
            {
                "query": "MITRE ATT&CK brute force detection",
                "expected_domains": ["mitre", "attack", "brute force"]
            },
            {
                "query": "Windows Event 4625 failed authentication",  
                "expected_domains": ["windows", "event", "4625", "authentication"]
            },
            {
                "query": "Splunk SIEM correlation rules",
                "expected_domains": ["splunk", "siem", "correlation"]
            }
        ]
        
        for i, test in enumerate(rag_tests, 1):
            print(f"\n🔍 RAG Test {i}: {test['query']}")
            
            results = self.rag_retriever.search(test['query'], k=3)
            print(f"📊 Retrieved {len(results)} results")
            
            if results:
                best_result = results[0]
                print(f"🎯 Best match (Score: {best_result['score']:.3f})")
                
                entry = best_result['entry']
                if isinstance(entry, dict) and 'query' in entry:
                    print(f"   Query: {entry['query'][:100]}...")
                
                # Check domain relevance
                response_text = json.dumps(entry).lower() if isinstance(entry, dict) else str(entry).lower()
                matches = sum(1 for domain in test['expected_domains'] 
                             if domain.lower() in response_text)
                score = matches / len(test['expected_domains'])
                
                print(f"✅ Relevance: {score:.2f} ({matches}/{len(test['expected_domains'])} domains found)")
            else:
                print("❌ No results found")
                score = 0.0
                
            self.test_results.append({
                "mode": "rag",
                "test": f"RAG Retrieval {i}",
                "query": test['query'],
                "results_count": len(results),
                "score": score,
                "best_result": results[0] if results else None
            })
            
    def generate_report(self):
        """Generate test results report"""
        print("\n📊 TEST RESULTS SUMMARY")
        print("=" * 40)
        
        # Calculate overall scores
        teacher_scores = [r['score'] for r in self.test_results if r['mode'] == 'teacher']
        assistant_scores = [r['score'] for r in self.test_results if r['mode'] == 'assistant'] 
        rag_scores = [r['score'] for r in self.test_results if r['mode'] == 'rag']
        
        print(f"👨‍🏫 Teacher Mode Average: {sum(teacher_scores)/len(teacher_scores):.2f}")
        print(f"🤖 Assistant Mode Average: {sum(assistant_scores)/len(assistant_scores):.2f}")
        print(f"🔍 RAG Retrieval Average: {sum(rag_scores)/len(rag_scores):.2f}")
        
        overall_score = sum(r['score'] for r in self.test_results) / len(self.test_results)
        print(f"\n🎯 Overall Score: {overall_score:.2f}")
        
        # Save detailed results
        report = {
            "timestamp": datetime.now().isoformat(),
            "model_path": "./whis-cybersec-model",
            "test_count": len(self.test_results),
            "overall_score": overall_score,
            "mode_averages": {
                "teacher": sum(teacher_scores)/len(teacher_scores) if teacher_scores else 0,
                "assistant": sum(assistant_scores)/len(assistant_scores) if assistant_scores else 0,
                "rag": sum(rag_scores)/len(rag_scores) if rag_scores else 0
            },
            "detailed_results": self.test_results
        }
        
        report_path = "whis_test_results.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
            
        print(f"📄 Detailed report saved to: {report_path}")
        
        # Print pass/fail status
        if overall_score >= 0.7:
            print("🎉 TESTS PASSED - Whis is ready for deployment!")
        elif overall_score >= 0.5:
            print("⚠️  TESTS MARGINAL - Consider additional training")
        else:
            print("❌ TESTS FAILED - Model needs improvement")
            
        return report

def main():
    tester = WhisTester()
    
    # Load model and RAG system
    tester.load_model()
    tester.rag_retriever.load_vector_store()
    
    # Run all tests
    tester.test_teacher_mode()
    tester.test_assistant_mode() 
    tester.test_rag_retrieval()
    
    # Generate report
    report = tester.generate_report()
    
    return report

if __name__ == "__main__":
    main()