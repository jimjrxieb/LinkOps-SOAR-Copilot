#!/usr/bin/env python3
"""
Manual SOAR Testing - Direct RAG queries
"""

import sys
sys.path.append('.')

from apps.api.engines.rag_retriever import get_rag_retriever

def test_manual_soar():
    print("🚀 MANUAL SOAR CAPABILITY TEST")
    print("=" * 50)
    
    # Force fresh RAG retriever load
    rag_retriever = get_rag_retriever()
    
    # Test questions
    questions = [
        "What is the NIST incident response procedure for ransomware?",
        "How do I handle a malware incident step by step?", 
        "What are the phases of incident response?",
        "Tell me about SOAR playbooks",
        "How do you contain a security breach?",
        "What is the complete ransomware response playbook?",
        "Walk me through incident response preparation phase",
        "What are the key steps in security incident containment?"
    ]
    
    for i, question in enumerate(questions, 1):
        print(f"\n📝 Question {i}: {question}")
        print("-" * 60)
        
        try:
            answer, citations = rag_retriever.get_answer_with_citations(question)
            
            if answer and len(answer) > 50:
                print(f"✅ Answer ({len(answer)} chars): {answer[:300]}...")
                print(f"📚 Citations: {len(citations)} sources")
                
                # Check for SOAR keywords
                soar_keywords = ["incident response", "playbook", "containment", "nist", "preparation", "detection", "eradication", "recovery"]
                found = [kw for kw in soar_keywords if kw.lower() in answer.lower()]
                
                if found:
                    print(f"🎯 SOAR keywords found: {', '.join(found)}")
                else:
                    print("⚠️ No SOAR keywords found")
            else:
                print(f"❌ Weak answer: {answer}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Check vector count
    print(f"\n📊 Knowledge Base Status:")
    print(f"Vector count: {getattr(rag_retriever, 'total_chunks', 'Unknown')}")

if __name__ == "__main__":
    test_manual_soar()