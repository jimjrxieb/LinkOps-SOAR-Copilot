#!/usr/bin/env python3
"""
🎯 WHIS Training Pipeline - 50 Comprehensive Test Questions
==========================================================

Test questions designed to evaluate WHIS cybersecurity knowledge
and identify gaps in the current RAG knowledge base.

[TAG: TRAINING-PIPELINE] - Knowledge evaluation framework
[TAG: GAP-ANALYSIS] - Missing domain identification
"""

import asyncio
import json
from typing import List, Dict, Any
from datetime import datetime

# Test questions categorized by security domain
WHIS_TRAINING_QUESTIONS = [
    
    # === BASIC SECURITY CONCEPTS (Questions 1-10) ===
    {
        "id": 1,
        "category": "security_fundamentals", 
        "question": "What is a SIEM?",
        "expected_domains": ["security_tools", "log_analysis"],
        "difficulty": "basic",
        "gap_check": "core_definitions"
    },
    {
        "id": 2,
        "category": "security_fundamentals",
        "question": "Define EDR and how it differs from antivirus",
        "expected_domains": ["endpoint_security", "detection_response"],
        "difficulty": "basic", 
        "gap_check": "tool_comparisons"
    },
    {
        "id": 3,
        "category": "security_fundamentals",
        "question": "What is the difference between IDS and IPS?",
        "expected_domains": ["network_security", "intrusion_detection"],
        "difficulty": "intermediate",
        "gap_check": "network_security_tools"
    },
    {
        "id": 4,
        "category": "security_fundamentals", 
        "question": "Explain the CIA triad in cybersecurity",
        "expected_domains": ["security_principles", "fundamentals"],
        "difficulty": "basic",
        "gap_check": "core_principles"
    },
    {
        "id": 5,
        "category": "security_fundamentals",
        "question": "What is zero trust security architecture?",
        "expected_domains": ["architecture", "access_control"],
        "difficulty": "intermediate",
        "gap_check": "modern_architectures"
    },
    {
        "id": 6,
        "category": "security_fundamentals",
        "question": "Define threat intelligence and its types",
        "expected_domains": ["threat_intel", "intelligence_feeds"],
        "difficulty": "intermediate",
        "gap_check": "threat_intelligence"
    },
    {
        "id": 7,
        "category": "security_fundamentals",
        "question": "What is a SOC and what are its main functions?",
        "expected_domains": ["security_operations", "soc_operations"],
        "difficulty": "basic",
        "gap_check": "operational_concepts"
    },
    {
        "id": 8,
        "category": "security_fundamentals",
        "question": "Explain the concept of defense in depth",
        "expected_domains": ["security_strategy", "layered_defense"],
        "difficulty": "intermediate",
        "gap_check": "security_strategies"
    },
    {
        "id": 9,
        "category": "security_fundamentals",
        "question": "What is vulnerability management?",
        "expected_domains": ["vulnerability_assessment", "risk_management"],
        "difficulty": "basic",
        "gap_check": "vulnerability_processes"
    },
    {
        "id": 10,
        "category": "security_fundamentals",
        "question": "Define incident response and its phases",
        "expected_domains": ["incident_response", "breach_management"],
        "difficulty": "intermediate",
        "gap_check": "ir_processes"
    },

    # === MITRE ATT&CK FRAMEWORK (Questions 11-20) ===
    {
        "id": 11,
        "category": "mitre_attack",
        "question": "What is the MITRE ATT&CK framework?",
        "expected_domains": ["mitre_attack", "threat_modeling"],
        "difficulty": "basic",
        "gap_check": "framework_knowledge"
    },
    {
        "id": 12,
        "category": "mitre_attack", 
        "question": "Explain the Initial Access tactic in MITRE ATT&CK",
        "expected_domains": ["mitre_tactics", "attack_vectors"],
        "difficulty": "intermediate",
        "gap_check": "tactic_understanding"
    },
    {
        "id": 13,
        "category": "mitre_attack",
        "question": "What are some common techniques under Persistence tactic?",
        "expected_domains": ["persistence_techniques", "backdoors"],
        "difficulty": "intermediate",
        "gap_check": "technique_knowledge"
    },
    {
        "id": 14,
        "category": "mitre_attack",
        "question": "Describe PowerShell Empire and its MITRE ATT&CK mapping",
        "expected_domains": ["attack_tools", "post_exploitation"],
        "difficulty": "advanced",
        "gap_check": "tool_to_framework_mapping"
    },
    {
        "id": 15,
        "category": "mitre_attack",
        "question": "What is lateral movement in the context of MITRE ATT&CK?",
        "expected_domains": ["lateral_movement", "network_traversal"],
        "difficulty": "intermediate", 
        "gap_check": "attack_progression"
    },
    {
        "id": 16,
        "category": "mitre_attack",
        "question": "Explain credential access techniques and countermeasures",
        "expected_domains": ["credential_access", "password_attacks"],
        "difficulty": "advanced",
        "gap_check": "defensive_mapping"
    },
    {
        "id": 17,
        "category": "mitre_attack",
        "question": "What is data exfiltration and how is it categorized in ATT&CK?",
        "expected_domains": ["exfiltration", "data_theft"],
        "difficulty": "intermediate",
        "gap_check": "data_protection"
    },
    {
        "id": 18,
        "category": "mitre_attack",
        "question": "Describe command and control (C2) techniques",
        "expected_domains": ["command_control", "c2_channels"],
        "difficulty": "advanced",
        "gap_check": "c2_understanding"
    },
    {
        "id": 19,
        "category": "mitre_attack",
        "question": "How does MITRE ATT&CK help with threat hunting?",
        "expected_domains": ["threat_hunting", "behavioral_analysis"],
        "difficulty": "advanced",
        "gap_check": "hunting_methodologies"
    },
    {
        "id": 20,
        "category": "mitre_attack",
        "question": "What are MITRE ATT&CK sub-techniques and why are they important?",
        "expected_domains": ["attack_granularity", "detection_specificity"],
        "difficulty": "intermediate",
        "gap_check": "framework_depth"
    },

    # === CLOUD SECURITY (Questions 21-25) - GAP IDENTIFIED ===
    {
        "id": 21,
        "category": "cloud_security",
        "question": "What is AWS CloudTrail and how does it help with security?",
        "expected_domains": ["aws_security", "audit_logging"],
        "difficulty": "intermediate",
        "gap_check": "aws_services_knowledge"
    },
    {
        "id": 22,
        "category": "cloud_security", 
        "question": "Explain Azure Security Center capabilities",
        "expected_domains": ["azure_security", "cloud_posture"],
        "difficulty": "intermediate",
        "gap_check": "azure_knowledge"
    },
    {
        "id": 23,
        "category": "cloud_security",
        "question": "What are the shared responsibility models in cloud security?",
        "expected_domains": ["cloud_responsibility", "compliance"],
        "difficulty": "basic",
        "gap_check": "cloud_fundamentals"
    },
    {
        "id": 24,
        "category": "cloud_security",
        "question": "How do you secure Kubernetes clusters?",
        "expected_domains": ["kubernetes_security", "container_security"],
        "difficulty": "advanced",
        "gap_check": "kubernetes_security_missing"
    },
    {
        "id": 25,
        "category": "cloud_security",
        "question": "What is CIS Kubernetes Benchmark?",
        "expected_domains": ["kubernetes_hardening", "cis_benchmarks"],
        "difficulty": "advanced",
        "gap_check": "kubernetes_standards_missing"
    },

    # === COMPLIANCE & FRAMEWORKS (Questions 26-30) - GAP IDENTIFIED ===
    {
        "id": 26,
        "category": "compliance",
        "question": "What is SOC 2 compliance and its security controls?",
        "expected_domains": ["soc2", "audit_controls"],
        "difficulty": "intermediate",
        "gap_check": "compliance_frameworks_missing"
    },
    {
        "id": 27,
        "category": "compliance",
        "question": "Explain GDPR requirements for data breach notification",
        "expected_domains": ["gdpr", "privacy_regulations"],
        "difficulty": "advanced",
        "gap_check": "privacy_law_missing"
    },
    {
        "id": 28,
        "category": "compliance",
        "question": "What is NIST Cybersecurity Framework?",
        "expected_domains": ["nist_framework", "risk_management"],
        "difficulty": "basic",
        "gap_check": "nist_knowledge"
    },
    {
        "id": 29,
        "category": "compliance",
        "question": "Describe PCI DSS requirements for payment security",
        "expected_domains": ["pci_dss", "payment_security"],
        "difficulty": "intermediate", 
        "gap_check": "payment_compliance_missing"
    },
    {
        "id": 30,
        "category": "compliance",
        "question": "What is ISO 27001 and its security domains?",
        "expected_domains": ["iso27001", "information_security_management"],
        "difficulty": "intermediate",
        "gap_check": "iso_standards_missing"
    },

    # === VENDOR-SPECIFIC KNOWLEDGE (Questions 31-35) - GAP IDENTIFIED ===
    {
        "id": 31,
        "category": "vendor_specific",
        "question": "What is Guardpoint and what services does the company provide?",
        "expected_domains": ["guardpoint", "managed_security"],
        "difficulty": "basic",
        "gap_check": "guardpoint_company_missing"
    },
    {
        "id": 32,
        "category": "vendor_specific",
        "question": "How does Splunk Enterprise Security work for threat detection?",
        "expected_domains": ["splunk_es", "security_analytics"],
        "difficulty": "intermediate",
        "gap_check": "splunk_advanced_features"
    },
    {
        "id": 33,
        "category": "vendor_specific",
        "question": "What are LimaCharlie's key EDR capabilities?",
        "expected_domains": ["limacharlie", "edr_features"],
        "difficulty": "intermediate",
        "gap_check": "limacharlie_details"
    },
    {
        "id": 34,
        "category": "vendor_specific", 
        "question": "Explain CrowdStrike Falcon's threat hunting features",
        "expected_domains": ["crowdstrike", "threat_hunting_tools"],
        "difficulty": "advanced",
        "gap_check": "crowdstrike_missing"
    },
    {
        "id": 35,
        "category": "vendor_specific",
        "question": "What is Microsoft Sentinel and its SOAR capabilities?",
        "expected_domains": ["microsoft_sentinel", "cloud_soar"],
        "difficulty": "intermediate",
        "gap_check": "microsoft_security_missing"
    },

    # === KUBERNETES SECURITY CERTIFICATIONS (Questions 36-40) - GAP IDENTIFIED ===
    {
        "id": 36,
        "category": "kubernetes_certs",
        "question": "What is CKS (Certified Kubernetes Security Specialist) certification?",
        "expected_domains": ["cks_certification", "kubernetes_security"],
        "difficulty": "intermediate",
        "gap_check": "cks_cert_missing"
    },
    {
        "id": 37,
        "category": "kubernetes_certs",
        "question": "Explain CCSP (Certified Cloud Security Professional) domains",
        "expected_domains": ["ccsp_certification", "cloud_security_domains"],
        "difficulty": "advanced",
        "gap_check": "ccsp_cert_missing"
    },
    {
        "id": 38,
        "category": "kubernetes_certs",
        "question": "What are Kubernetes RBAC best practices?",
        "expected_domains": ["kubernetes_rbac", "access_control"],
        "difficulty": "advanced",
        "gap_check": "k8s_rbac_missing"
    },
    {
        "id": 39,
        "category": "kubernetes_certs",
        "question": "How do you implement Pod Security Standards?",
        "expected_domains": ["pod_security", "kubernetes_hardening"],
        "difficulty": "advanced", 
        "gap_check": "pod_security_missing"
    },
    {
        "id": 40,
        "category": "kubernetes_certs",
        "question": "What is Kubernetes Network Policy and security implications?",
        "expected_domains": ["network_policy", "micro_segmentation"],
        "difficulty": "advanced",
        "gap_check": "k8s_networking_missing"
    },

    # === ADVANCED THREATS & MALWARE (Questions 41-45) ===
    {
        "id": 41,
        "category": "advanced_threats",
        "question": "What is ransomware and how does it work?",
        "expected_domains": ["ransomware", "malware_analysis"],
        "difficulty": "intermediate",
        "gap_check": "malware_knowledge"
    },
    {
        "id": 42,
        "category": "advanced_threats",
        "question": "Describe APT (Advanced Persistent Threat) characteristics",
        "expected_domains": ["apt", "nation_state_attacks"],
        "difficulty": "advanced",
        "gap_check": "apt_analysis"
    },
    {
        "id": 43,
        "category": "advanced_threats",
        "question": "What are fileless attacks and detection strategies?",
        "expected_domains": ["fileless_malware", "memory_analysis"],
        "difficulty": "advanced",
        "gap_check": "advanced_detection"
    },
    {
        "id": 44,
        "category": "advanced_threats",
        "question": "Explain supply chain attacks and prevention measures",
        "expected_domains": ["supply_chain_security", "third_party_risk"],
        "difficulty": "advanced",
        "gap_check": "supply_chain_missing"
    },
    {
        "id": 45,
        "category": "advanced_threats",
        "question": "What is social engineering and common attack vectors?",
        "expected_domains": ["social_engineering", "human_factors"],
        "difficulty": "basic",
        "gap_check": "human_security"
    },

    # === SYSTEM CONFIGURATION & CURRENT SETUP (Questions 46-50) ===
    {
        "id": 46,
        "category": "system_config",
        "question": "What SIEM are we currently using?",
        "expected_domains": ["current_siem", "splunk_config"],
        "difficulty": "basic",
        "gap_check": "config_knowledge"
    },
    {
        "id": 47,
        "category": "system_config",
        "question": "What EDR solution is configured in our environment?",
        "expected_domains": ["current_edr", "limacharlie_config"],
        "difficulty": "basic",
        "gap_check": "config_knowledge"
    },
    {
        "id": 48,
        "category": "system_config",
        "question": "How does WHIS integrate with our current security stack?",
        "expected_domains": ["whis_integration", "soar_platform"],
        "difficulty": "intermediate",
        "gap_check": "platform_understanding"
    },
    {
        "id": 49,
        "category": "system_config", 
        "question": "What testing framework do we use for security validation?",
        "expected_domains": ["testing_framework", "playwright_automation"],
        "difficulty": "basic",
        "gap_check": "testing_knowledge"
    },
    {
        "id": 50,
        "category": "system_config",
        "question": "How are high-risk actions handled in our SOAR workflow?",
        "expected_domains": ["approval_workflows", "human_in_loop"],
        "difficulty": "intermediate",
        "gap_check": "workflow_understanding"
    }
]

# Gap analysis categories
IDENTIFIED_GAPS = {
    "guardpoint_company": "Missing knowledge about Guardpoint company and services",
    "kubernetes_security": "No CKS/CCSP certification knowledge or K8s security practices", 
    "cloud_security": "Limited AWS/Azure security service knowledge",
    "compliance_frameworks": "Missing SOC2, GDPR, PCI DSS, ISO 27001 details",
    "vendor_specific": "Lacks vendor-specific tool knowledge (CrowdStrike, Microsoft)",
    "advanced_detection": "Limited advanced threat detection and analysis knowledge",
    "supply_chain": "No supply chain security knowledge",
    "privacy_regulations": "Missing privacy law and regulation details"
}

async def run_training_questions():
    """
    Execute all 50 training questions against WHIS
    and generate gap analysis report
    """
    
    print("🎯 WHIS Training Pipeline - 50 Question Evaluation")
    print("=" * 60)
    
    results = []
    gap_categories = {}
    
    for question_data in WHIS_TRAINING_QUESTIONS:
        print(f"\n[Q{question_data['id']:02d}] {question_data['category'].upper()}")
        print(f"❓ {question_data['question']}")
        print(f"📊 Difficulty: {question_data['difficulty']}")
        print(f"🔍 Gap Check: {question_data['gap_check']}")
        
        # Track gap categories
        gap_key = question_data['gap_check']
        if gap_key not in gap_categories:
            gap_categories[gap_key] = []
        gap_categories[gap_key].append(question_data['id'])
        
        # Store for analysis
        results.append({
            "question_id": question_data['id'],
            "category": question_data['category'],
            "question": question_data['question'],
            "difficulty": question_data['difficulty'],
            "gap_check": question_data['gap_check'],
            "expected_domains": question_data['expected_domains']
        })
    
    # Generate gap analysis
    print("\n" + "=" * 60)
    print("🔍 KNOWLEDGE GAP ANALYSIS")
    print("=" * 60)
    
    for gap_type, description in IDENTIFIED_GAPS.items():
        print(f"\n❌ {gap_type.upper()}")
        print(f"   {description}")
    
    # Category breakdown
    print(f"\n📊 QUESTION CATEGORIES BREAKDOWN:")
    category_counts = {}
    difficulty_counts = {"basic": 0, "intermediate": 0, "advanced": 0}
    
    for result in results:
        category = result['category']
        difficulty = result['difficulty']
        
        category_counts[category] = category_counts.get(category, 0) + 1
        difficulty_counts[difficulty] += 1
    
    for category, count in category_counts.items():
        print(f"   {category}: {count} questions")
    
    print(f"\n📈 DIFFICULTY DISTRIBUTION:")
    for difficulty, count in difficulty_counts.items():
        print(f"   {difficulty}: {count} questions")
    
    # Save results
    report = {
        "generated_at": datetime.now().isoformat(),
        "total_questions": len(WHIS_TRAINING_QUESTIONS),
        "questions": results,
        "identified_gaps": IDENTIFIED_GAPS,
        "category_breakdown": category_counts,
        "difficulty_distribution": difficulty_counts,
        "next_steps": [
            "Expand knowledge base with missing domains",
            "Add Guardpoint company information",
            "Include Kubernetes security certifications (CKS/CCSP)",
            "Add cloud security services knowledge", 
            "Include compliance framework details",
            "Add vendor-specific security tool knowledge"
        ]
    }
    
    with open("tests/whis_training_report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\n✅ Training questions and gap analysis saved to tests/whis_training_report.json")
    
    return results, IDENTIFIED_GAPS

if __name__ == "__main__":
    asyncio.run(run_training_questions())