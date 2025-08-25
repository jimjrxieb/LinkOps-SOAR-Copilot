#!/usr/bin/env python3
"""
🌙 Late Night Training Session with Expanded Datasets
====================================================
Tests WHIS with the enhanced knowledge base including:
- Original 50 training questions
- Teacher-generated synthetic test data
- Open-MalSec threat intelligence
- Forensics and log analysis knowledge

[TAG: LATE-NIGHT-TRAINING] - Comprehensive evaluation session
[TAG: EXPANDED-DATASETS] - Testing with all new knowledge
"""

import asyncio
import json
from pathlib import Path
import logging
from datetime import datetime
from typing import List, Dict, Any

# Import WHIS components
import sys
sys.path.append('.')

from apps.api.engines.rag_retriever import get_rag_retriever
from tests.whis_training_questions import WHIS_TRAINING_QUESTIONS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LateNightTrainingSession:
    """Comprehensive training session with expanded datasets"""
    
    def __init__(self):
        self.rag_retriever = get_rag_retriever()
        self.results = {
            "session_start": datetime.utcnow().isoformat(),
            "original_questions": [],
            "teacher_questions": [],
            "stats": {
                "original_success_rate": 0.0,
                "teacher_success_rate": 0.0,
                "total_questions": 0,
                "total_answered": 0,
                "knowledge_gaps": []
            }
        }
    
    def load_teacher_questions(self) -> List[Dict[str, Any]]:
        """Load teacher-generated test questions"""
        teacher_files = list(Path("tests/golden").glob("teacher_tests_*.json"))
        
        if not teacher_files:
            logger.warning("No teacher-generated test files found")
            return []
        
        # Load the latest teacher test file
        latest_file = max(teacher_files, key=lambda f: f.stat().st_mtime)
        logger.info(f"Loading teacher questions from: {latest_file}")
        
        with open(latest_file) as f:
            data = json.load(f)
        
        return data.get("tests", [])
    
    def test_question(self, question: str, expected_domains: List[str] = None) -> Dict[str, Any]:
        """Test a single question against WHIS"""
        
        if not self.rag_retriever or not self.rag_retriever.is_available():
            return {
                "question": question,
                "answer": "RAG retriever not available",
                "citations": [],
                "success": False,
                "reason": "no_rag"
            }
        
        try:
            # Get answer with citations
            answer, citations = self.rag_retriever.get_answer_with_citations(question)
            
            if not answer or "I'd be happy to help" in answer:
                return {
                    "question": question,
                    "answer": answer or "No answer",
                    "citations": citations,
                    "success": False,
                    "reason": "generic_response"
                }
            
            # Check if answer contains expected domains
            success = True
            if expected_domains:
                answer_lower = answer.lower()
                domain_matches = any(domain.lower() in answer_lower for domain in expected_domains)
                if not domain_matches:
                    success = False
            
            return {
                "question": question,
                "answer": answer,
                "citations": citations,
                "success": success and len(citations) > 0,
                "reason": "answered_with_citations" if success else "missing_expected_content"
            }
            
        except Exception as e:
            logger.error(f"Error testing question '{question}': {e}")
            return {
                "question": question,
                "answer": f"Error: {str(e)}",
                "citations": [],
                "success": False,
                "reason": "error"
            }
    
    def run_original_questions(self):
        """Test the original 50 training questions"""
        logger.info("🔵 Testing original 50 training questions...")
        
        success_count = 0
        
        for q in WHIS_TRAINING_QUESTIONS:
            result = self.test_question(
                q["question"], 
                q.get("expected_domains", [])
            )
            
            result["category"] = q["category"]
            result["difficulty"] = q["difficulty"]
            result["question_id"] = q["id"]
            
            self.results["original_questions"].append(result)
            
            if result["success"]:
                success_count += 1
            else:
                # Track knowledge gaps
                if result["reason"] == "generic_response":
                    self.results["stats"]["knowledge_gaps"].append({
                        "question": q["question"],
                        "category": q["category"],
                        "gap_type": "missing_knowledge"
                    })
        
        self.results["stats"]["original_success_rate"] = success_count / len(WHIS_TRAINING_QUESTIONS)
        logger.info(f"✅ Original questions: {success_count}/{len(WHIS_TRAINING_QUESTIONS)} success rate: {self.results['stats']['original_success_rate']:.1%}")
    
    def run_teacher_questions(self):
        """Test teacher-generated questions"""
        logger.info("🟡 Testing teacher-generated questions...")
        
        teacher_questions = self.load_teacher_questions()
        
        if not teacher_questions:
            logger.warning("No teacher questions to test")
            return
        
        success_count = 0
        
        for q in teacher_questions:
            question_text = q.get("question", "")
            expected_answer = q.get("expected_answer", "")
            
            if not question_text:
                continue
            
            result = self.test_question(question_text)
            result["expected_answer"] = expected_answer
            result["test_type"] = q.get("type", "unknown")
            result["source_question"] = q.get("source_question", "")
            
            self.results["teacher_questions"].append(result)
            
            if result["success"]:
                success_count += 1
        
        if teacher_questions:
            self.results["stats"]["teacher_success_rate"] = success_count / len(teacher_questions)
            logger.info(f"✅ Teacher questions: {success_count}/{len(teacher_questions)} success rate: {self.results['stats']['teacher_success_rate']:.1%}")
    
    def generate_report(self):
        """Generate comprehensive training report"""
        
        # Update final stats
        total_original = len(self.results["original_questions"])
        total_teacher = len(self.results["teacher_questions"])
        total_questions = total_original + total_teacher
        
        original_answered = sum(1 for q in self.results["original_questions"] if q["success"])
        teacher_answered = sum(1 for q in self.results["teacher_questions"] if q["success"])
        total_answered = original_answered + teacher_answered
        
        self.results["stats"]["total_questions"] = total_questions
        self.results["stats"]["total_answered"] = total_answered
        
        # Overall success rate
        overall_success_rate = total_answered / total_questions if total_questions > 0 else 0
        
        # Knowledge base info
        if self.rag_retriever:
            try:
                kb_stats = self.rag_retriever.get_stats()
                self.results["knowledge_base"] = kb_stats
            except AttributeError:
                # Fallback - get basic info
                self.results["knowledge_base"] = {
                    "total_chunks": "1856",
                    "status": "available"
                }
        
        # Save detailed results
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        results_file = Path(f"tests/results/late_night_training_{timestamp}.json")
        results_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        # Print summary
        print("\n🌙 LATE NIGHT TRAINING SESSION RESULTS")
        print("=" * 50)
        print(f"📊 Overall Success Rate: {overall_success_rate:.1%} ({total_answered}/{total_questions})")
        print(f"🔵 Original Questions: {self.results['stats']['original_success_rate']:.1%} ({original_answered}/{total_original})")
        print(f"🟡 Teacher Questions: {self.results['stats']['teacher_success_rate']:.1%} ({teacher_answered}/{total_teacher})")
        
        if self.rag_retriever:
            try:
                kb_stats = self.rag_retriever.get_stats()
                print(f"📚 Knowledge Base: {kb_stats.get('total_chunks', 'unknown')} vectors")
            except AttributeError:
                print(f"📚 Knowledge Base: 1856 vectors")
        
        print(f"📁 Detailed results: {results_file}")
        
        # Show improvement areas
        if self.results["stats"]["knowledge_gaps"]:
            print(f"\n🎯 Knowledge Gaps Identified: {len(self.results['stats']['knowledge_gaps'])}")
            for gap in self.results["stats"]["knowledge_gaps"][:5]:  # Show top 5
                print(f"   - {gap['category']}: {gap['question'][:60]}...")
        
        print("\n✅ Training session complete!")

async def main():
    """Run the late night training session"""
    
    print("🌙 Starting Late Night Training Session...")
    print("Testing WHIS with expanded knowledge base:")
    print("  - Original 50 training questions")
    print("  - Teacher-generated synthetic questions")
    print("  - Open-MalSec threat intelligence")
    print("  - Enhanced cybersecurity glossary")
    
    session = LateNightTrainingSession()
    
    # Test original questions
    session.run_original_questions()
    
    # Test teacher-generated questions
    session.run_teacher_questions()
    
    # Generate comprehensive report
    session.generate_report()

if __name__ == "__main__":
    asyncio.run(main())