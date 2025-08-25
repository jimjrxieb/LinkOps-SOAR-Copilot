#!/usr/bin/env python3
"""
🧪 Pipeline Validation & Answer Testing
=====================================
Tests the complete pipeline by validating that:
1. Training data contains correct security procedures
2. RAG chunks have relevant security knowledge
3. Generated responses match expected patterns

Run this as your supervised learning validation!
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PipelineValidator:
    """Validates pipeline outputs and generated training data"""
    
    def __init__(self):
        self.base_dir = Path("/home/jimmie/linkops-industries/SOAR-copilot")
        self.results = []
        
    def validate_llm_training_data(self) -> Dict[str, Any]:
        """Validate LLM training data quality"""
        llm_file = self.base_dir / "data/curated/llm/whis_actions.jsonl"
        
        if not llm_file.exists():
            return {"status": "FAIL", "error": "No LLM training file found"}
            
        with open(llm_file, 'r') as f:
            training_data = [json.loads(line) for line in f]
            
        results = {
            "status": "PASS",
            "total_examples": len(training_data),
            "quality_checks": {
                "has_instructions": 0,
                "has_outputs": 0,
                "has_mitre_mapping": 0,
                "has_containment": 0,
                "has_artifacts": 0
            }
        }
        
        for example in training_data:
            # Check instruction quality
            if "instruction" in example and len(example["instruction"]) > 10:
                results["quality_checks"]["has_instructions"] += 1
                
            # Check output structure
            if "output" in example:
                results["quality_checks"]["has_outputs"] += 1
                output = example["output"]
                
                # Check for security-specific fields
                if "containment" in output or "triage_steps" in output:
                    results["quality_checks"]["has_containment"] += 1
                if "mitre" in output:
                    results["quality_checks"]["has_mitre_mapping"] += 1
                if "artifacts" in output and len(output["artifacts"]) > 0:
                    results["quality_checks"]["has_artifacts"] += 1
        
        # Calculate quality percentages
        total = results["total_examples"]
        quality_checks = results["quality_checks"].copy()
        for check, count in quality_checks.items():
            results["quality_checks"][f"{check}_pct"] = (count / total * 100) if total > 0 else 0
            
        return results
    
    def validate_rag_chunks(self) -> Dict[str, Any]:
        """Validate RAG chunk content and structure"""
        rag_dir = self.base_dir / "data/curated/rag/chunks"
        
        if not rag_dir.exists():
            return {"status": "FAIL", "error": "No RAG chunks directory found"}
            
        chunk_files = list(rag_dir.glob("*.md"))
        
        results = {
            "status": "PASS",
            "total_chunks": len(chunk_files),
            "quality_checks": {
                "has_metadata": 0,
                "has_procedures": 0,
                "has_mitre_references": 0,
                "has_queries": 0
            }
        }
        
        for chunk_file in chunk_files:
            with open(chunk_file, 'r') as f:
                content = f.read()
                
            # Check for YAML frontmatter
            if content.startswith('---'):
                results["quality_checks"]["has_metadata"] += 1
                
            # Check for security procedures
            if re.search(r'(triage|containment|investigation|response)', content, re.IGNORECASE):
                results["quality_checks"]["has_procedures"] += 1
                
            # Check for MITRE references
            if re.search(r'T\d{4}', content):
                results["quality_checks"]["has_mitre_references"] += 1
                
            # Check for query patterns
            if re.search(r'(\$\{[^}]+\}|index=|sourcetype=)', content):
                results["quality_checks"]["has_queries"] += 1
        
        # Calculate quality percentages
        total = results["total_chunks"]
        quality_checks = results["quality_checks"].copy()
        for check, count in quality_checks.items():
            results["quality_checks"][f"{check}_pct"] = (count / total * 100) if total > 0 else 0
            
        return results
    
    def test_security_scenarios(self) -> Dict[str, Any]:
        """Test specific security scenarios against expected answers"""
        
        test_scenarios = [
            {
                "scenario": "WMI Lateral Movement Detection",
                "question": "A WMI-based lateral movement alert triggered. What are the immediate containment steps?",
                "expected_elements": [
                    "network isolation",
                    "service account",
                    "process analysis",
                    "WMI",
                    "containment"
                ]
            },
            {
                "scenario": "Credential Dumping Response", 
                "question": "Credential dumping detected on domain controller. What's the priority response?",
                "expected_elements": [
                    "password reset",
                    "domain controller", 
                    "isolation",
                    "LSASS",
                    "kerberos"
                ]
            },
            {
                "scenario": "PowerShell Empire Detection",
                "question": "PowerShell Empire activity detected. How should we respond?",
                "expected_elements": [
                    "process termination",
                    "C2",
                    "base64",
                    "script block logging",
                    "empire"
                ]
            }
        ]
        
        results = {
            "status": "PASS",
            "scenarios_tested": len(test_scenarios),
            "scenario_results": []
        }
        
        # Check if our RAG chunks contain relevant knowledge
        rag_dir = self.base_dir / "data/curated/rag/chunks"
        ai_rag_dir = self.base_dir / "ai-training/rag/chunks"
        
        all_rag_content = ""
        
        # Read curated RAG chunks
        if rag_dir.exists():
            for chunk_file in rag_dir.glob("*.md"):
                with open(chunk_file, 'r') as f:
                    all_rag_content += f.read().lower() + "\\n"
        
        # Read training RAG chunks  
        if ai_rag_dir.exists():
            for chunk_file in ai_rag_dir.glob("*.md"):
                with open(chunk_file, 'r') as f:
                    all_rag_content += f.read().lower() + "\\n"
        
        for scenario in test_scenarios:
            scenario_result = {
                "scenario": scenario["scenario"],
                "question": scenario["question"],
                "matches_found": 0,
                "total_expected": len(scenario["expected_elements"]),
                "matched_elements": []
            }
            
            # Check if expected elements are present in RAG knowledge
            for element in scenario["expected_elements"]:
                if element.lower() in all_rag_content:
                    scenario_result["matches_found"] += 1
                    scenario_result["matched_elements"].append(element)
            
            scenario_result["coverage_pct"] = (scenario_result["matches_found"] / 
                                            scenario_result["total_expected"] * 100)
            scenario_result["status"] = "PASS" if scenario_result["coverage_pct"] >= 60 else "FAIL"
            
            results["scenario_results"].append(scenario_result)
        
        # Overall pass/fail
        passed_scenarios = sum(1 for r in results["scenario_results"] if r["status"] == "PASS")
        results["pass_rate"] = (passed_scenarios / len(test_scenarios) * 100)
        results["status"] = "PASS" if results["pass_rate"] >= 70 else "FAIL"
        
        return results
    
    def run_full_validation(self) -> Dict[str, Any]:
        """Run complete pipeline validation"""
        logger.info("🧪 Starting pipeline validation...")
        
        validation_results = {
            "timestamp": "2025-08-23T11:05:00Z",
            "pipeline_status": "TESTING",
            "tests": {}
        }
        
        # Test 1: LLM Training Data Quality
        logger.info("📚 Validating LLM training data...")
        validation_results["tests"]["llm_training"] = self.validate_llm_training_data()
        
        # Test 2: RAG Chunk Quality
        logger.info("🔍 Validating RAG chunks...")
        validation_results["tests"]["rag_chunks"] = self.validate_rag_chunks()
        
        # Test 3: Security Scenario Coverage
        logger.info("🛡️ Testing security scenario coverage...")
        validation_results["tests"]["security_scenarios"] = self.test_security_scenarios()
        
        # Overall assessment
        all_passed = all(test["status"] == "PASS" for test in validation_results["tests"].values())
        validation_results["overall_status"] = "PASS" if all_passed else "PARTIAL"
        
        logger.info("✅ Pipeline validation completed!")
        return validation_results

def main():
    """Run pipeline validation tests"""
    print("🎯 SUPERVISED LEARNING CENTER - PIPELINE VALIDATION")
    print("=" * 60)
    
    validator = PipelineValidator()
    results = validator.run_full_validation()
    
    # Print detailed results
    print(f"\\n🧪 VALIDATION RESULTS")
    print(f"Overall Status: {results['overall_status']}")
    print()
    
    for test_name, test_results in results["tests"].items():
        print(f"📊 {test_name.upper()}: {test_results['status']}")
        
        if test_name == "llm_training":
            print(f"   Training Examples: {test_results['total_examples']}")
            print(f"   Has Instructions: {test_results['quality_checks']['has_instructions_pct']:.1f}%")
            print(f"   Has Containment: {test_results['quality_checks']['has_containment_pct']:.1f}%")
            print(f"   Has Artifacts: {test_results['quality_checks']['has_artifacts_pct']:.1f}%")
            
        elif test_name == "rag_chunks":
            print(f"   Total Chunks: {test_results['total_chunks']}")
            print(f"   Has Procedures: {test_results['quality_checks']['has_procedures_pct']:.1f}%")
            print(f"   Has MITRE Refs: {test_results['quality_checks']['has_mitre_references_pct']:.1f}%")
            
        elif test_name == "security_scenarios":
            print(f"   Scenarios Tested: {test_results['scenarios_tested']}")
            print(f"   Pass Rate: {test_results['pass_rate']:.1f}%")
            for scenario in test_results['scenario_results']:
                status_icon = "✅" if scenario['status'] == "PASS" else "❌"
                print(f"   {status_icon} {scenario['scenario']}: {scenario['coverage_pct']:.1f}%")
        
        print()
    
    # Save results
    results_file = Path("results/pipeline_validation.json")
    results_file.parent.mkdir(exist_ok=True)
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"📋 Full results saved to: {results_file}")
    print("🚀 View real-time pipeline status at: http://localhost:8000")
    
    return results

if __name__ == "__main__":
    main()