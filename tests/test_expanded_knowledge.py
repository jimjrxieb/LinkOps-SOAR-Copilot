#!/usr/bin/env python3
"""
🧪 Test Expanded Knowledge Base
==============================
Test key gap questions against the expanded WHIS knowledge base
"""

import sys
sys.path.append('.')

from apps.api.engines.rag_retriever import get_rag_retriever

def test_gap_questions():
    """Test critical gap questions from the analysis"""
    
    print("🧪 Testing Expanded WHIS Knowledge Base")
    print("=" * 50)
    
    retriever = get_rag_retriever()
    
    if not retriever.is_available():
        print("❌ RAG not available")
        return
    
    # Test gap questions
    gap_questions = [
        # Guardpoint company
        "What is Guardpoint and what services does the company provide?",
        
        # Kubernetes security
        "What is CKS certification?",
        "What is CCSP certification?", 
        "What are Kubernetes RBAC best practices?",
        "What is Pod Security Standards?",
        
        # Cloud security
        "What is AWS CloudTrail?",
        "What is Azure Security Center?",
        "What are shared responsibility models?",
        
        # Compliance
        "What is SOC 2 compliance?",
        "What is GDPR?",
        "What is PCI DSS?",
        "What is ISO 27001?",
        "What is NIST Cybersecurity Framework?",
        
        # Vendor tools
        "What is CrowdStrike Falcon?",
        "What is Microsoft Sentinel?",
        "What is Splunk Enterprise Security?",
        
        # Advanced concepts
        "What is zero trust architecture?",
        "What is supply chain attack?",
        "What is APT?",
        "What is ransomware?",
        
        # Network security
        "What is the difference between IDS and IPS?",
        "What is a SOC?",
        "What is vulnerability management?",
        "What is defense in depth?"
    ]
    
    successful_tests = 0
    total_tests = len(gap_questions)
    
    for i, question in enumerate(gap_questions, 1):
        print(f"\n[TEST {i:02d}] {question}")
        
        try:
            answer, citations = retriever.get_answer_with_citations(question, k=3)
            
            if answer and citations:
                print(f"✅ PASS - Answer: {answer[:100]}...")
                print(f"   Citations: {citations}")
                successful_tests += 1
            else:
                print("❌ FAIL - No answer or citations")
                
        except Exception as e:
            print(f"❌ ERROR - {e}")
    
    print(f"\n" + "=" * 50)
    print(f"🎯 RESULTS: {successful_tests}/{total_tests} tests passed ({successful_tests/total_tests*100:.1f}%)")
    
    if successful_tests == total_tests:
        print("🎉 ALL GAPS SUCCESSFULLY FILLED!")
    elif successful_tests >= total_tests * 0.8:
        print("✅ Major gaps successfully addressed")
    else:
        print("⚠️  Some gaps remain - knowledge base may need more expansion")

if __name__ == "__main__":
    test_gap_questions()