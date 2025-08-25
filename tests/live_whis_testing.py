#!/usr/bin/env python3
"""
🔴 Live WHIS Production Testing
===============================
Feed 50 training questions directly to running WHIS server
"""

import asyncio
import aiohttp
import json
import time
from typing import List, Dict, Any

# Import our training questions
from whis_training_questions import WHIS_TRAINING_QUESTIONS

class LiveWHISTest:
    def __init__(self, whis_url: str = "http://localhost:8000"):
        self.whis_url = whis_url
        self.results = []
        
    async def test_question(self, session: aiohttp.ClientSession, question_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test a single question against WHIS"""
        
        question = question_data["question"]
        question_id = question_data["id"]
        category = question_data["category"]
        
        print(f"[Q{question_id:02d}] Testing: {question}")
        
        try:
            # Send question to WHIS
            start_time = time.time()
            
            async with session.post(
                f"{self.whis_url}/chat", 
                json={"message": question},
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                
                response_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    
                    whis_response = data.get("response", "")
                    citations = data.get("sources_used", [])  # Changed from "citations" to "sources_used"
                    intent = data.get("intent_classified", "unknown")  # Changed from "intent" to "intent_classified"
                    
                    # Analyze response quality
                    has_answer = len(whis_response) > 50 and "I'd be happy to help" not in whis_response
                    has_citations = len(citations) > 0
                    response_quality = "good" if has_answer and has_citations else "poor"
                    
                    result = {
                        "question_id": question_id,
                        "category": category,
                        "question": question,
                        "whis_response": whis_response[:200] + "..." if len(whis_response) > 200 else whis_response,
                        "full_response": whis_response,
                        "citations": citations,
                        "intent": intent,
                        "response_time": round(response_time, 2),
                        "response_quality": response_quality,
                        "has_answer": has_answer,
                        "has_citations": has_citations,
                        "status": "success"
                    }
                    
                    if response_quality == "good":
                        print(f"   ✅ PASS ({response_time:.1f}s) - {intent} - {len(citations)} citations")
                    else:
                        print(f"   ❌ FAIL ({response_time:.1f}s) - Generic response or no citations")
                        
                    return result
                    
                else:
                    print(f"   ❌ HTTP {response.status}")
                    return {
                        "question_id": question_id,
                        "category": category, 
                        "question": question,
                        "error": f"HTTP {response.status}",
                        "status": "failed"
                    }
                    
        except Exception as e:
            print(f"   ❌ ERROR - {e}")
            return {
                "question_id": question_id,
                "category": category,
                "question": question, 
                "error": str(e),
                "status": "failed"
            }
    
    async def run_all_tests(self):
        """Run all 50 training questions against WHIS"""
        
        print("🔴 Live WHIS Production Testing")
        print("=" * 60)
        print(f"Testing against: {self.whis_url}")
        print(f"Questions to test: {len(WHIS_TRAINING_QUESTIONS)}")
        print("=" * 60)
        
        # Test server connectivity first
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.whis_url}/health") as response:
                    if response.status == 200:
                        health_data = await response.json()
                        print(f"✅ WHIS server online - {health_data}")
                    else:
                        print(f"⚠️  WHIS server returned {response.status}")
        except Exception as e:
            print(f"❌ Cannot connect to WHIS server: {e}")
            return
        
        # Run all tests concurrently (in batches to avoid overwhelming)
        batch_size = 5
        all_results = []
        
        async with aiohttp.ClientSession() as session:
            for i in range(0, len(WHIS_TRAINING_QUESTIONS), batch_size):
                batch = WHIS_TRAINING_QUESTIONS[i:i+batch_size]
                
                print(f"\n🔄 Testing batch {i//batch_size + 1} ({len(batch)} questions)...")
                
                # Run batch concurrently
                tasks = [self.test_question(session, q) for q in batch]
                batch_results = await asyncio.gather(*tasks)
                all_results.extend(batch_results)
                
                # Small delay between batches
                await asyncio.sleep(1)
        
        self.results = all_results
        self.analyze_results()
        
    def analyze_results(self):
        """Analyze test results and generate report"""
        
        print(f"\n" + "=" * 60)
        print("📊 LIVE WHIS TEST ANALYSIS")
        print("=" * 60)
        
        successful_tests = len([r for r in self.results if r.get("status") == "success" and r.get("response_quality") == "good"])
        failed_tests = len([r for r in self.results if r.get("status") == "failed"]) 
        poor_quality = len([r for r in self.results if r.get("status") == "success" and r.get("response_quality") == "poor"])
        
        total_tests = len(self.results)
        success_rate = (successful_tests / total_tests) * 100 if total_tests > 0 else 0
        
        print(f"📈 OVERALL RESULTS:")
        print(f"   ✅ High Quality Answers: {successful_tests}/{total_tests} ({success_rate:.1f}%)")
        print(f"   ⚠️  Poor Quality Answers: {poor_quality}")
        print(f"   ❌ Failed Requests: {failed_tests}")
        
        # Category breakdown
        categories = {}
        for result in self.results:
            cat = result.get("category", "unknown")
            if cat not in categories:
                categories[cat] = {"total": 0, "good": 0, "poor": 0, "failed": 0}
            
            categories[cat]["total"] += 1
            if result.get("status") == "failed":
                categories[cat]["failed"] += 1
            elif result.get("response_quality") == "good":
                categories[cat]["good"] += 1
            else:
                categories[cat]["poor"] += 1
        
        print(f"\n📊 CATEGORY BREAKDOWN:")
        for cat, stats in categories.items():
            good_pct = (stats["good"] / stats["total"]) * 100 if stats["total"] > 0 else 0
            print(f"   {cat}: {stats['good']}/{stats['total']} good ({good_pct:.1f}%)")
        
        # Response time analysis
        response_times = [r.get("response_time", 0) for r in self.results if r.get("response_time")]
        if response_times:
            avg_time = sum(response_times) / len(response_times)
            max_time = max(response_times)
            print(f"\n⏱️  PERFORMANCE:")
            print(f"   Average Response Time: {avg_time:.1f}s")
            print(f"   Max Response Time: {max_time:.1f}s")
        
        # Save detailed results
        with open("live_whis_results.json", "w") as f:
            json.dump({
                "summary": {
                    "total_tests": total_tests,
                    "successful_tests": successful_tests,
                    "poor_quality": poor_quality,
                    "failed_tests": failed_tests,
                    "success_rate": success_rate,
                    "average_response_time": avg_time if response_times else 0
                },
                "category_breakdown": categories,
                "detailed_results": self.results
            }, f, indent=2)
        
        print(f"\n💾 Detailed results saved to live_whis_results.json")
        
        # Final assessment
        if success_rate >= 90:
            print("\n🎉 EXCELLENT! WHIS is performing exceptionally well!")
        elif success_rate >= 75:
            print("\n✅ GOOD! WHIS knowledge base is working effectively")
        elif success_rate >= 50:
            print("\n⚠️  MODERATE - Some knowledge gaps remain")
        else:
            print("\n❌ NEEDS WORK - Significant issues detected")

async def main():
    tester = LiveWHISTest()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())