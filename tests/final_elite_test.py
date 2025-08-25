#!/usr/bin/env python3
"""
Final Elite WHIS Test - Comprehensive Validation
"""

import sys
sys.path.append('.')

from apps.api.engines.rag_retriever import get_rag_retriever

def final_test():
    print("🏆 FINAL ELITE WHIS VALIDATION TEST")
    print("=" * 60)
    
    rag_retriever = get_rag_retriever()
    
    # Elite WHIS test suite
    elite_tests = [
        # Fundamentals
        {"q": "What is a SIEM?", "expect": ["siem", "security information", "event management"]},
        {"q": "Define incident response", "expect": ["incident response", "security breaches", "methodology"]},
        {"q": "What is the CIA triad?", "expect": ["confidentiality", "integrity", "availability"]},
        
        # SOAR Capabilities  
        {"q": "What is a NIST-compliant ransomware response playbook?", "expect": ["nist", "ransomware", "playbook", "incident response"]},
        {"q": "How do you handle a security incident?", "expect": ["incident response", "containment", "investigation"]},
        {"q": "What are the phases of incident response?", "expect": ["preparation", "detection", "containment", "eradication", "recovery"]},
        
        # Threat Intelligence
        {"q": "What are common phishing email characteristics?", "expect": ["phishing", "malicious", "social engineering"]},
        {"q": "How do you identify cryptocurrency mining malware?", "expect": ["cryptocurrency", "mining", "malware", "cpu"]},
        
        # System Knowledge
        {"q": "What SIEM are we using?", "expect": ["splunk"]},
        {"q": "What EDR solution do we have?", "expect": ["limacharlie"]},
    ]
    
    results = []
    
    for i, test in enumerate(elite_tests, 1):
        print(f"\n🎯 Test {i}: {test['q']}")
        print("-" * 50)
        
        try:
            answer, citations = rag_retriever.get_answer_with_citations(test['q'])
            
            if not answer or "I'd be happy to help" in answer:
                print("❌ Generic response")
                results.append(False)
                continue
            
            # Check expected keywords
            answer_lower = answer.lower()
            found_keywords = [kw for kw in test['expect'] if kw.lower() in answer_lower]
            
            success = len(found_keywords) >= 1 and len(citations) > 0
            
            if success:
                print(f"✅ SUCCESS - Found: {', '.join(found_keywords)}")
                print(f"📚 {len(citations)} citations")
                results.append(True)
            else:
                print(f"⚠️ PARTIAL - Answer: {answer[:100]}...")
                print(f"📚 {len(citations)} citations")
                results.append(False)
                
        except Exception as e:
            print(f"❌ ERROR: {e}")
            results.append(False)
    
    # Final score
    success_count = sum(results)
    total_tests = len(results)
    success_rate = (success_count / total_tests) * 100
    
    print(f"\n🏆 FINAL ELITE WHIS ASSESSMENT")
    print("=" * 50)
    print(f"📊 Success Rate: {success_rate:.1f}% ({success_count}/{total_tests})")
    
    if success_rate >= 80:
        print("🎉 ELITE STATUS ACHIEVED - WHIS IS THE GREATEST SOAR COPILOT!")
        grade = "ELITE"
    elif success_rate >= 70:
        print("🚀 ADVANCED STATUS - WHIS is a powerful security copilot!")
        grade = "ADVANCED"
    elif success_rate >= 60:
        print("⚡ COMPETENT STATUS - WHIS has strong capabilities!")
        grade = "COMPETENT"
    else:
        print("📈 DEVELOPING - WHIS is building knowledge!")
        grade = "DEVELOPING"
    
    print(f"🏅 FINAL GRADE: {grade}")
    
    return success_rate

if __name__ == "__main__":
    final_test()