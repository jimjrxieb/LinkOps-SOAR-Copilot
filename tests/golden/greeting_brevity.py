#!/usr/bin/env python3
"""
Golden Eval: Greeting Brevity Tests
===================================
Ensures WHIS responds concisely to greetings without capability pitches.

[TAG: EVALS] - Behavioral tests for conversational quality
[TAG: ERROR-SHAPE] - Consistent response format validation
"""

import asyncio
import aiohttp
import pytest
from typing import Dict, Any

class GreetingBrevityEvaluator:
    """Test suite for greeting response quality"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        
    async def test_greeting_brevity(self) -> Dict[str, Any]:
        """Test that greetings get brief responses"""
        test_cases = [
            {
                "input": "hello",
                "max_words": 12,
                "forbidden_phrases": ["I can help with", "Try asking me about", "capability", "features"]
            },
            {
                "input": "hi",
                "max_words": 12,
                "forbidden_phrases": ["bullet list", "available options", "What can I do"]
            },
            {
                "input": "hey there",
                "max_words": 15,
                "forbidden_phrases": ["copilot features", "security operations"]
            },
            {
                "input": "thanks",
                "max_words": 10,
                "forbidden_phrases": ["capabilities", "I can help"]
            },
            {
                "input": "thank you",
                "max_words": 10,
                "forbidden_phrases": ["Try asking", "What would you like"]
            },
            {
                "input": "ok",
                "max_words": 6,
                "forbidden_phrases": ["features", "help with"]
            }
        ]
        
        results = []
        
        async with aiohttp.ClientSession() as session:
            for case in test_cases:
                try:
                    # Send chat request
                    async with session.post(
                        f"{self.base_url}/chat",
                        json={"message": case["input"], "use_rag": True}
                    ) as resp:
                        data = await resp.json()
                        response_text = data.get("response", "")
                        
                        # Count words
                        word_count = len(response_text.split())
                        
                        # Check for forbidden phrases
                        forbidden_found = [
                            phrase for phrase in case["forbidden_phrases"]
                            if phrase.lower() in response_text.lower()
                        ]
                        
                        # Check if response contains user input in quotes (intent echo)
                        intent_echo = f'"{case["input"]}"' in response_text
                        
                        results.append({
                            "input": case["input"],
                            "response": response_text,
                            "word_count": word_count,
                            "max_words": case["max_words"],
                            "words_pass": word_count <= case["max_words"],
                            "forbidden_found": forbidden_found,
                            "forbidden_pass": len(forbidden_found) == 0,
                            "intent_echo": intent_echo,
                            "intent_echo_pass": not intent_echo,
                            "overall_pass": (
                                word_count <= case["max_words"] and
                                len(forbidden_found) == 0 and
                                not intent_echo
                            )
                        })
                        
                except Exception as e:
                    results.append({
                        "input": case["input"],
                        "error": str(e),
                        "overall_pass": False
                    })
        
        return {
            "test_name": "greeting_brevity",
            "total_cases": len(test_cases),
            "passed_cases": sum(1 for r in results if r.get("overall_pass", False)),
            "pass_rate": sum(1 for r in results if r.get("overall_pass", False)) / len(test_cases),
            "details": results
        }
    
    async def test_no_capability_pitch_on_first_turn(self) -> Dict[str, Any]:
        """Ensure first turn doesn't contain capability marketing"""
        
        forbidden_first_turn_phrases = [
            "I can help with:",
            "Try asking me about:",
            "What can I do for you?",
            "My capabilities include:",
            "I offer the following:",
            "Available features:",
            "As your AI security copilot, I can help with:",
            "🔍 **Threat Hunting**",
            "🚨 **Incident Response**",
            "📊 **Security Analysis**"
        ]
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/chat",
                json={"message": "hello", "use_rag": True}
            ) as resp:
                data = await resp.json()
                response_text = data.get("response", "")
                
                found_pitches = [
                    phrase for phrase in forbidden_first_turn_phrases
                    if phrase.lower() in response_text.lower()
                ]
                
                return {
                    "test_name": "no_capability_pitch",
                    "response": response_text,
                    "pitch_phrases_found": found_pitches,
                    "overall_pass": len(found_pitches) == 0,
                    "word_count": len(response_text.split())
                }
    
    async def test_ui_chips_present(self) -> Dict[str, Any]:
        """Verify UI chips are present instead of model capability text"""
        
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/") as resp:
                html_content = await resp.text()
                
                # Check for capability chips in UI
                expected_chips = [
                    "Current Incidents",
                    "Hunt Credentials", 
                    "Network Analysis",
                    "Ransomware Response",
                    "System Status"
                ]
                
                chips_found = [
                    chip for chip in expected_chips
                    if chip in html_content
                ]
                
                # Check that capabilities aren't in the initial model message
                model_message_has_capabilities = any(
                    phrase in html_content for phrase in [
                        "I can help with threat hunting",
                        "Try asking me about",
                        "My capabilities"
                    ]
                )
                
                return {
                    "test_name": "ui_chips_present",
                    "expected_chips": expected_chips,
                    "chips_found": chips_found,
                    "all_chips_present": len(chips_found) == len(expected_chips),
                    "model_has_capabilities": model_message_has_capabilities,
                    "overall_pass": (
                        len(chips_found) == len(expected_chips) and
                        not model_message_has_capabilities
                    )
                }
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run complete greeting brevity test suite"""
        
        tests = [
            self.test_greeting_brevity(),
            self.test_no_capability_pitch_on_first_turn(),
            self.test_ui_chips_present()
        ]
        
        results = await asyncio.gather(*tests)
        
        overall_pass = all(result.get("overall_pass", False) for result in results)
        
        return {
            "test_suite": "greeting_brevity_eval",
            "timestamp": asyncio.get_event_loop().time(),
            "overall_pass": overall_pass,
            "tests": results
        }

async def main():
    """Run greeting brevity evaluation"""
    evaluator = GreetingBrevityEvaluator()
    results = await evaluator.run_all_tests()
    
    print("🧪 GREETING BREVITY EVALUATION")
    print("=" * 50)
    
    for test in results["tests"]:
        status = "✅ PASS" if test.get("overall_pass", False) else "❌ FAIL"
        print(f"{status} {test.get('test_name', 'unknown')}")
        
        if not test.get("overall_pass", False):
            if "details" in test:
                for detail in test["details"]:
                    if not detail.get("overall_pass", True):
                        print(f"  • Input: '{detail['input']}' -> {detail.get('word_count', 0)} words (max: {detail.get('max_words', 0)})")
                        print(f"    Response: '{detail.get('response', '')}'")
                        if detail.get("forbidden_found"):
                            print(f"    Forbidden phrases: {detail['forbidden_found']}")
                        if detail.get("intent_echo"):
                            print(f"    Intent echo detected")
            elif "pitch_phrases_found" in test:
                print(f"  • Found capability pitches: {test['pitch_phrases_found']}")
            elif "chips_found" in test:
                missing = set(test["expected_chips"]) - set(test["chips_found"])
                if missing:
                    print(f"  • Missing UI chips: {missing}")
    
    print(f"\n🎯 Overall: {'✅ PASS' if results['overall_pass'] else '❌ FAIL'}")
    
    return results

if __name__ == "__main__":
    asyncio.run(main())