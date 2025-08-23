"""
Cybersecurity LLM Evaluation Metrics
Specialized evaluation for security domain tasks
"""

import torch
import numpy as np
import json
import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import logging
from transformers import AutoTokenizer
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class EvaluationResult:
    """Evaluation result for a single example"""
    example_id: str
    category: str
    instruction: str
    expected_output: str
    generated_output: str
    
    # Scoring metrics
    bleu_score: float
    rouge_score: float
    semantic_similarity: float
    technical_accuracy: float
    completeness_score: float
    security_relevance: float
    
    # Binary flags
    contains_code: bool
    contains_attack_id: bool
    contains_detection_rule: bool
    contains_mitigation: bool
    
    # Overall quality
    overall_score: float
    quality_grade: str

class CybersecurityEvaluator:
    """Specialized evaluator for cybersecurity LLM responses"""
    
    def __init__(self):
        self.semantic_model = None
        self.security_keywords = self._load_security_keywords()
        self.attack_patterns = self._load_attack_patterns()
        self.detection_patterns = self._load_detection_patterns()
        
    def _load_security_keywords(self) -> Dict[str, List[str]]:
        """Load cybersecurity domain keywords for relevance scoring"""
        return {
            "attack_techniques": [
                "MITRE", "ATT&CK", "technique", "tactic", "procedure", "TTP",
                "adversary", "threat", "campaign", "indicator", "IOC",
                "persistence", "escalation", "defense evasion", "discovery",
                "lateral movement", "collection", "exfiltration", "impact"
            ],
            "detection_rules": [
                "SIEM", "Splunk", "Sigma", "detection", "alert", "rule",
                "query", "search", "correlation", "threshold", "baseline",
                "anomaly", "event", "log", "monitoring", "hunting"
            ],
            "incident_response": [
                "incident", "response", "playbook", "containment", "eradication",
                "recovery", "forensics", "timeline", "scope", "impact",
                "stakeholder", "communication", "escalation", "documentation"
            ],
            "cloud_security": [
                "Kubernetes", "container", "pod", "namespace", "RBAC",
                "network policy", "security context", "admission controller",
                "CKS", "CCSP", "cloud", "encryption", "IAM", "compliance"
            ],
            "soar_automation": [
                "SOAR", "automation", "orchestration", "playbook", "workflow",
                "approval", "integration", "API", "webhook", "enrichment",
                "correlation", "decision", "action", "response"
            ]
        }
    
    def _load_attack_patterns(self) -> List[str]:
        """Attack technique ID patterns"""
        return [
            r"T\d{4}(?:\.\d{3})?",  # MITRE ATT&CK technique IDs
            r"CVE-\d{4}-\d{4,}",    # CVE identifiers
            r"CAPEC-\d+",           # CAPEC patterns
        ]
    
    def _load_detection_patterns(self) -> List[str]:
        """Detection rule code patterns"""
        return [
            r"```(?:spl|splunk).*?```",      # Splunk queries
            r"```(?:yaml|yml).*?```",        # YAML rules
            r"```(?:sql).*?```",             # SQL queries
            r"```(?:python|py).*?```",       # Python code
            r"index=\w+",                    # Splunk index searches
            r"sourcetype=[\w:]+",            # Splunk sourcetypes
            r"EventCode=\d+",                # Windows event codes
        ]
    
    async def initialize_semantic_model(self):
        """Initialize semantic similarity model"""
        logger.info("🔍 Loading semantic similarity model...")
        self.semantic_model = SentenceTransformer('all-MiniLM-L6-v2')
        logger.info("✅ Semantic model loaded")
    
    def calculate_bleu_score(self, reference: str, candidate: str) -> float:
        """Calculate BLEU score for text similarity"""
        # Simple BLEU-like scoring based on n-gram overlap
        ref_words = reference.lower().split()
        cand_words = candidate.lower().split()
        
        if not cand_words:
            return 0.0
        
        # 1-gram precision
        ref_1grams = set(ref_words)
        cand_1grams = set(cand_words)
        precision_1 = len(ref_1grams & cand_1grams) / len(cand_1grams) if cand_1grams else 0
        
        # 2-gram precision
        ref_2grams = set(zip(ref_words[:-1], ref_words[1:]))
        cand_2grams = set(zip(cand_words[:-1], cand_words[1:]))
        precision_2 = len(ref_2grams & cand_2grams) / len(cand_2grams) if cand_2grams else 0
        
        # Brevity penalty
        bp = min(1.0, len(cand_words) / len(ref_words)) if ref_words else 0
        
        return bp * (precision_1 * 0.7 + precision_2 * 0.3)
    
    def calculate_rouge_score(self, reference: str, candidate: str) -> float:
        """Calculate ROUGE-L score"""
        ref_words = reference.lower().split()
        cand_words = candidate.lower().split()
        
        if not ref_words or not cand_words:
            return 0.0
        
        # Longest Common Subsequence
        lcs_length = self._lcs_length(ref_words, cand_words)
        
        # ROUGE-L = LCS(X,Y) / len(Y)
        recall = lcs_length / len(ref_words)
        precision = lcs_length / len(cand_words)
        
        if recall + precision == 0:
            return 0.0
        
        f1 = 2 * (recall * precision) / (recall + precision)
        return f1
    
    def _lcs_length(self, x: List[str], y: List[str]) -> int:
        """Calculate Longest Common Subsequence length"""
        m, n = len(x), len(y)
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if x[i-1] == y[j-1]:
                    dp[i][j] = dp[i-1][j-1] + 1
                else:
                    dp[i][j] = max(dp[i-1][j], dp[i][j-1])
        
        return dp[m][n]
    
    def calculate_semantic_similarity(self, reference: str, candidate: str) -> float:
        """Calculate semantic similarity using sentence transformers"""
        if not self.semantic_model:
            return 0.0
        
        ref_embedding = self.semantic_model.encode([reference])
        cand_embedding = self.semantic_model.encode([candidate])
        
        similarity = cosine_similarity(ref_embedding, cand_embedding)[0][0]
        return max(0.0, float(similarity))  # Ensure non-negative
    
    def calculate_technical_accuracy(self, text: str, category: str) -> float:
        """Score technical accuracy based on domain-specific patterns"""
        score = 0.0
        max_score = 0.0
        
        # Check for attack technique references
        for pattern in self.attack_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                score += 0.3
            max_score += 0.3
        
        # Check for detection rule code
        for pattern in self.detection_patterns:
            matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
            if matches:
                score += 0.4
            max_score += 0.4
        
        # Check for domain-specific keywords
        if category in self.security_keywords:
            keywords = self.security_keywords[category]
            found_keywords = sum(1 for keyword in keywords if keyword.lower() in text.lower())
            keyword_score = min(1.0, found_keywords / len(keywords)) * 0.3
            score += keyword_score
            max_score += 0.3
        
        return score / max_score if max_score > 0 else 0.0
    
    def calculate_completeness_score(self, text: str, category: str) -> float:
        """Score response completeness based on expected components"""
        components = {
            "attack_techniques": ["description", "detection", "mitigation", "example"],
            "detection_rules": ["query", "logic", "threshold", "false positive"],
            "incident_response": ["steps", "timeline", "stakeholder", "communication"],
            "cloud_security": ["configuration", "best practice", "security control"],
            "soar_automation": ["workflow", "automation", "approval", "integration"]
        }
        
        if category not in components:
            return 0.5  # Default score for unknown categories
        
        expected_components = components[category]
        found_components = 0
        
        for component in expected_components:
            if component.lower() in text.lower():
                found_components += 1
        
        return found_components / len(expected_components)
    
    def calculate_security_relevance(self, text: str, category: str) -> float:
        """Score security domain relevance"""
        relevance_score = 0.0
        
        # General security terms
        security_terms = [
            "security", "threat", "vulnerability", "risk", "attack",
            "defense", "protection", "monitoring", "incident", "malware",
            "encryption", "authentication", "authorization", "audit"
        ]
        
        found_terms = sum(1 for term in security_terms if term.lower() in text.lower())
        general_score = min(1.0, found_terms / 10) * 0.5
        
        # Category-specific terms
        if category in self.security_keywords:
            keywords = self.security_keywords[category]
            found_keywords = sum(1 for keyword in keywords if keyword.lower() in text.lower())
            specific_score = min(1.0, found_keywords / len(keywords)) * 0.5
        else:
            specific_score = 0.0
        
        return general_score + specific_score
    
    def check_content_flags(self, text: str) -> Dict[str, bool]:
        """Check for specific content types in the response"""
        return {
            "contains_code": "```" in text,
            "contains_attack_id": bool(re.search(r"T\d{4}", text)),
            "contains_detection_rule": any(re.search(pattern, text, re.IGNORECASE) 
                                         for pattern in ["index=", "sourcetype=", "EventCode="]),
            "contains_mitigation": any(term in text.lower() 
                                    for term in ["mitigation", "remediation", "fix", "patch"])
        }
    
    def calculate_overall_score(self, metrics: Dict[str, float]) -> Tuple[float, str]:
        """Calculate weighted overall score and quality grade"""
        weights = {
            "semantic_similarity": 0.25,
            "technical_accuracy": 0.25,
            "completeness_score": 0.20,
            "security_relevance": 0.15,
            "bleu_score": 0.10,
            "rouge_score": 0.05
        }
        
        weighted_score = sum(metrics[metric] * weight for metric, weight in weights.items())
        
        # Quality grades
        if weighted_score >= 0.9:
            grade = "A"
        elif weighted_score >= 0.8:
            grade = "B"
        elif weighted_score >= 0.7:
            grade = "C"
        elif weighted_score >= 0.6:
            grade = "D"
        else:
            grade = "F"
        
        return weighted_score, grade
    
    async def evaluate_response(self, example_id: str, category: str, instruction: str,
                              expected_output: str, generated_output: str) -> EvaluationResult:
        """Evaluate a single model response"""
        
        # Calculate all metrics
        bleu_score = self.calculate_bleu_score(expected_output, generated_output)
        rouge_score = self.calculate_rouge_score(expected_output, generated_output)
        semantic_similarity = self.calculate_semantic_similarity(expected_output, generated_output)
        technical_accuracy = self.calculate_technical_accuracy(generated_output, category)
        completeness_score = self.calculate_completeness_score(generated_output, category)
        security_relevance = self.calculate_security_relevance(generated_output, category)
        
        # Content flags
        content_flags = self.check_content_flags(generated_output)
        
        # Overall scoring
        metrics = {
            "bleu_score": bleu_score,
            "rouge_score": rouge_score,
            "semantic_similarity": semantic_similarity,
            "technical_accuracy": technical_accuracy,
            "completeness_score": completeness_score,
            "security_relevance": security_relevance
        }
        
        overall_score, quality_grade = self.calculate_overall_score(metrics)
        
        return EvaluationResult(
            example_id=example_id,
            category=category,
            instruction=instruction,
            expected_output=expected_output,
            generated_output=generated_output,
            bleu_score=bleu_score,
            rouge_score=rouge_score,
            semantic_similarity=semantic_similarity,
            technical_accuracy=technical_accuracy,
            completeness_score=completeness_score,
            security_relevance=security_relevance,
            contains_code=content_flags["contains_code"],
            contains_attack_id=content_flags["contains_attack_id"],
            contains_detection_rule=content_flags["contains_detection_rule"],
            contains_mitigation=content_flags["contains_mitigation"],
            overall_score=overall_score,
            quality_grade=quality_grade
        )
    
    async def evaluate_batch(self, test_examples: List[Dict]) -> List[EvaluationResult]:
        """Evaluate a batch of model responses"""
        if not self.semantic_model:
            await self.initialize_semantic_model()
        
        logger.info(f"📊 Evaluating {len(test_examples)} examples...")
        
        results = []
        for i, example in enumerate(test_examples):
            result = await self.evaluate_response(
                example_id=f"eval_{i:03d}",
                category=example["category"],
                instruction=example["instruction"],
                expected_output=example["expected_output"],
                generated_output=example["generated_output"]
            )
            results.append(result)
            
            if (i + 1) % 10 == 0:
                logger.info(f"✅ Evaluated {i + 1}/{len(test_examples)} examples")
        
        return results
    
    def generate_evaluation_report(self, results: List[EvaluationResult]) -> Dict:
        """Generate comprehensive evaluation report"""
        timestamp = datetime.now().isoformat()
        
        # Aggregate statistics
        df = pd.DataFrame([
            {
                "example_id": r.example_id,
                "category": r.category,
                "bleu_score": r.bleu_score,
                "rouge_score": r.rouge_score,
                "semantic_similarity": r.semantic_similarity,
                "technical_accuracy": r.technical_accuracy,
                "completeness_score": r.completeness_score,
                "security_relevance": r.security_relevance,
                "overall_score": r.overall_score,
                "quality_grade": r.quality_grade,
                "contains_code": r.contains_code,
                "contains_attack_id": r.contains_attack_id,
                "contains_detection_rule": r.contains_detection_rule,
                "contains_mitigation": r.contains_mitigation
            }
            for r in results
        ])
        
        # Category-wise performance
        category_stats = df.groupby("category").agg({
            "overall_score": ["mean", "std", "min", "max"],
            "technical_accuracy": "mean",
            "security_relevance": "mean",
            "contains_code": "sum",
            "contains_attack_id": "sum"
        }).round(3)
        
        # Grade distribution
        grade_dist = df["quality_grade"].value_counts().to_dict()
        
        # Overall metrics
        overall_metrics = {
            "total_examples": len(results),
            "average_overall_score": float(df["overall_score"].mean()),
            "score_std": float(df["overall_score"].std()),
            "grade_distribution": grade_dist,
            "category_performance": category_stats.to_dict(),
            "content_analysis": {
                "examples_with_code": int(df["contains_code"].sum()),
                "examples_with_attack_ids": int(df["contains_attack_id"].sum()),
                "examples_with_detection_rules": int(df["contains_detection_rule"].sum()),
                "examples_with_mitigation": int(df["contains_mitigation"].sum())
            }
        }
        
        report = {
            "evaluation_timestamp": timestamp,
            "model_performance": overall_metrics,
            "detailed_results": [
                {
                    "example_id": r.example_id,
                    "category": r.category,
                    "scores": {
                        "overall": r.overall_score,
                        "technical_accuracy": r.technical_accuracy,
                        "security_relevance": r.security_relevance,
                        "semantic_similarity": r.semantic_similarity
                    },
                    "grade": r.quality_grade,
                    "content_flags": {
                        "code": r.contains_code,
                        "attack_id": r.contains_attack_id,
                        "detection_rule": r.contains_detection_rule,
                        "mitigation": r.contains_mitigation
                    }
                }
                for r in results
            ]
        }
        
        return report
    
    def save_evaluation_report(self, report: Dict, output_path: str):
        """Save evaluation report to file"""
        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"📊 Evaluation report saved: {output_path}")

async def main():
    """Demo evaluation pipeline"""
    evaluator = CybersecurityEvaluator()
    await evaluator.initialize_semantic_model()
    
    # Demo test examples
    test_examples = [
        {
            "category": "attack_techniques",
            "instruction": "Explain MITRE ATT&CK technique T1110",
            "expected_output": "T1110 is brute force technique where adversaries attempt to gain access to accounts when passwords are unknown...",
            "generated_output": "MITRE ATT&CK T1110 describes brute force attacks where attackers try multiple password combinations to gain unauthorized access..."
        }
    ]
    
    results = await evaluator.evaluate_batch(test_examples)
    report = evaluator.generate_evaluation_report(results)
    
    print("📊 Evaluation Complete!")
    print(f"Average Score: {report['model_performance']['average_overall_score']:.3f}")

if __name__ == "__main__":
    asyncio.run(main())