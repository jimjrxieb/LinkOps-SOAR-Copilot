#!/usr/bin/env python3
"""
Enhanced Whis Testing - Kubernetes Security Edition
Tests the model's expanded capabilities with K8s security scenarios
"""

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import PeftModel
from knowledge.rag_retriever import WhisRAGRetriever
import json
from datetime import datetime

print("🔥 WHIS + KUBERNETES SECURITY TESTING")
print("=" * 45)

class EnhancedWhisTester:
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.rag_retriever = WhisRAGRetriever()
        self.test_results = []
        
    def load_model(self):
        """Load the trained Whis model"""
        print("📦 Loading enhanced Whis model...")
        
        base_model_path = "/home/jimmie/linkops-industries/SOAR-copilot/training/codellama-cache"
        lora_model_path = "./whis-cybersec-model"
        
        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(base_model_path, trust_remote_code=True)
        self.tokenizer.pad_token = self.tokenizer.eos_token
        self.tokenizer.padding_side = "right"
        
        # 4-bit config
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.bfloat16,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4"
        )
        
        # Load models
        base_model = AutoModelForCausalLM.from_pretrained(
            base_model_path,
            quantization_config=bnb_config,
            device_map="auto",
            trust_remote_code=True
        )
        
        self.model = PeftModel.from_pretrained(base_model, lora_model_path)
        print("✅ Enhanced Whis model loaded!")
        return self.model
        
    def generate_response(self, prompt: str, max_length: int = 400, temperature: float = 0.7) -> str:
        """Generate response from enhanced Whis model"""
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
        
        response = self.tokenizer.decode(
            outputs[0][inputs['input_ids'].shape[1]:], 
            skip_special_tokens=True
        ).strip()
        
        return response
        
    def test_kubernetes_security(self):
        """Test Kubernetes security capabilities"""
        print("\n🔥 TESTING KUBERNETES SECURITY MODE")
        print("-" * 40)
        
        k8s_tests = [
            {
                "name": "Pod Security Context",
                "prompt": "Create a secure Pod specification with security context best practices",
                "expected_elements": ["runAsNonRoot", "securityContext", "readOnlyRootFilesystem", "capabilities", "drop"]
            },
            {
                "name": "Network Policy Zero Trust",
                "prompt": "Design NetworkPolicies for zero-trust networking in Kubernetes",
                "expected_elements": ["NetworkPolicy", "default-deny", "ingress", "egress", "podSelector"]
            },
            {
                "name": "RBAC Least Privilege",
                "prompt": "Create RBAC configuration for a CI/CD pipeline with least privilege",
                "expected_elements": ["ServiceAccount", "Role", "RoleBinding", "verbs", "resources"]
            },
            {
                "name": "Container Image Security",
                "prompt": "Explain container image signing and verification with cosign",
                "expected_elements": ["cosign", "signing", "verification", "attestation", "supply chain"]
            },
            {
                "name": "Kubernetes Incident Response",
                "prompt": "Respond to a Kubernetes security incident with privileged container escape",
                "expected_elements": ["containment", "isolation", "kubectl", "forensics", "hardening"]
            }
        ]
        
        for i, test in enumerate(k8s_tests, 1):
            print(f"\n🧪 K8s Test {i}: {test['name']}")
            
            # Create RAG-enhanced prompt
            rag_prompt = self.rag_retriever.generate_rag_prompt(
                test['prompt'], 
                mode="assistant"
            )
            
            print(f"📝 Prompt: {test['prompt']}")
            
            # Generate response
            response = self.generate_response(rag_prompt, max_length=500)
            print(f"🤖 Response: {response[:200]}{'...' if len(response) > 200 else ''}")
            
            # Check for expected elements
            matches = sum(1 for element in test['expected_elements'] 
                         if element.lower() in response.lower())
            score = matches / len(test['expected_elements'])
            
            print(f"✅ K8s Score: {score:.2f} ({matches}/{len(test['expected_elements'])} elements found)")
            
            self.test_results.append({
                "mode": "kubernetes",
                "test": test['name'],
                "prompt": test['prompt'],
                "response": response,
                "score": score,
                "elements_found": matches,
                "total_elements": len(test['expected_elements'])
            })
            
    def test_multi_domain_integration(self):
        """Test integration between traditional cybersecurity and K8s security"""
        print("\n🌐 TESTING MULTI-DOMAIN INTEGRATION")
        print("-" * 40)
        
        integration_tests = [
            {
                "name": "SIEM + K8s Monitoring",
                "prompt": "How would you integrate Kubernetes security monitoring with Splunk SIEM for container threat detection?",
                "domains": ["splunk", "kubernetes", "monitoring", "container", "security"]
            },
            {
                "name": "MITRE ATT&CK + K8s",
                "prompt": "Map MITRE ATT&CK techniques to Kubernetes attack vectors and detection strategies",
                "domains": ["mitre", "attack", "kubernetes", "detection", "techniques"]
            },
            {
                "name": "Incident Response Hybrid",
                "prompt": "Create an incident response plan for a breach that spans traditional infrastructure and Kubernetes clusters",
                "domains": ["incident response", "kubernetes", "containment", "forensics", "playbook"]
            }
        ]
        
        for i, test in enumerate(integration_tests, 1):
            print(f"\n🔬 Integration Test {i}: {test['name']}")
            
            rag_prompt = self.rag_retriever.generate_rag_prompt(
                test['prompt'], 
                mode="teacher"
            )
            
            print(f"📝 Prompt: {test['prompt']}")
            
            response = self.generate_response(rag_prompt, max_length=400)
            print(f"🤖 Response: {response[:200]}{'...' if len(response) > 200 else ''}")
            
            # Check domain coverage
            domain_matches = sum(1 for domain in test['domains'] 
                               if domain.lower() in response.lower())
            score = domain_matches / len(test['domains'])
            
            print(f"✅ Integration Score: {score:.2f} ({domain_matches}/{len(test['domains'])} domains covered)")
            
            self.test_results.append({
                "mode": "integration",
                "test": test['name'],
                "prompt": test['prompt'],
                "response": response,
                "score": score,
                "domains_found": domain_matches,
                "total_domains": len(test['domains'])
            })
            
    def test_enhanced_rag_retrieval(self):
        """Test enhanced RAG with K8s knowledge"""
        print("\n🔍 TESTING ENHANCED RAG RETRIEVAL")
        print("-" * 40)
        
        enhanced_queries = [
            "Kubernetes Pod security best practices",
            "NetworkPolicy zero trust implementation", 
            "Container runtime security with gVisor",
            "Kubernetes RBAC service account security",
            "Supply chain security for container images"
        ]
        
        for i, query in enumerate(enhanced_queries, 1):
            print(f"\n🔍 Enhanced RAG Test {i}: {query}")
            
            results = self.rag_retriever.search(query, k=3, threshold=1.0)
            print(f"📊 Retrieved {len(results)} relevant results")
            
            if results:
                best_result = results[0]
                print(f"🎯 Best match (Score: {best_result['score']:.3f})")
                
                # Check if K8s domain is covered
                entry = best_result['entry']
                is_k8s_relevant = any(k8s_term in json.dumps(entry).lower() 
                                    for k8s_term in ['kubernetes', 'pod', 'container', 'rbac', 'network'])
                
                score = best_result['score']
                print(f"✅ RAG Score: {score:.3f} | K8s Relevant: {is_k8s_relevant}")
                
                self.test_results.append({
                    "mode": "enhanced_rag",
                    "test": f"Enhanced RAG {i}",
                    "query": query,
                    "score": score,
                    "k8s_relevant": is_k8s_relevant,
                    "results_count": len(results)
                })
            else:
                print("❌ No relevant results found")
                
    def generate_enhanced_report(self):
        """Generate comprehensive test report"""
        print("\n📊 ENHANCED WHIS TEST RESULTS")
        print("=" * 50)
        
        # Calculate category scores
        k8s_scores = [r['score'] for r in self.test_results if r['mode'] == 'kubernetes']
        integration_scores = [r['score'] for r in self.test_results if r['mode'] == 'integration']
        enhanced_rag_scores = [r['score'] for r in self.test_results if r['mode'] == 'enhanced_rag']
        
        print(f"🔥 Kubernetes Security: {sum(k8s_scores)/len(k8s_scores):.2f}" if k8s_scores else "🔥 Kubernetes Security: No tests")
        print(f"🌐 Multi-Domain Integration: {sum(integration_scores)/len(integration_scores):.2f}" if integration_scores else "🌐 Multi-Domain Integration: No tests")
        print(f"🔍 Enhanced RAG: {sum(enhanced_rag_scores)/len(enhanced_rag_scores):.2f}" if enhanced_rag_scores else "🔍 Enhanced RAG: No tests")
        
        overall_score = sum(r['score'] for r in self.test_results) / len(self.test_results)
        print(f"\n🎯 Overall Enhanced Score: {overall_score:.2f}")
        
        # Save enhanced results
        report = {
            "timestamp": datetime.now().isoformat(),
            "model_version": "whis-cybersec-k8s-enhanced",
            "total_tests": len(self.test_results),
            "overall_score": overall_score,
            "category_scores": {
                "kubernetes_security": sum(k8s_scores)/len(k8s_scores) if k8s_scores else 0,
                "multi_domain_integration": sum(integration_scores)/len(integration_scores) if integration_scores else 0,
                "enhanced_rag": sum(enhanced_rag_scores)/len(enhanced_rag_scores) if enhanced_rag_scores else 0
            },
            "knowledge_base_size": 106,  # Updated size
            "detailed_results": self.test_results
        }
        
        report_path = "whis_enhanced_test_results.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
            
        print(f"📄 Enhanced report saved to: {report_path}")
        
        # Enhanced assessment
        if overall_score >= 0.75:
            print("🎉 ENHANCED WHIS - EXCELLENT! Ready for production deployment!")
        elif overall_score >= 0.6:
            print("✅ ENHANCED WHIS - GOOD! Kubernetes integration successful!")
        elif overall_score >= 0.4:
            print("⚠️ ENHANCED WHIS - FAIR! K8s knowledge integrated but needs refinement")
        else:
            print("❌ ENHANCED WHIS - NEEDS WORK! Further training required")
            
        return report

def main():
    tester = EnhancedWhisTester()
    
    print("🚀 Loading enhanced Whis system...")
    tester.load_model()
    tester.rag_retriever.load_vector_store()
    
    # Run comprehensive enhanced tests
    tester.test_kubernetes_security()
    tester.test_multi_domain_integration()
    tester.test_enhanced_rag_retrieval()
    
    # Generate enhanced report
    report = tester.generate_enhanced_report()
    
    return report

if __name__ == "__main__":
    main()