#!/usr/bin/env python3
"""
Threat Intelligence RAG Training Data Generator
Creates specialized threat intel and OSINT examples for Whis
"""

import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict

class ThreatIntelRAGGenerator:
    """Generate threat intelligence training examples"""
    
    def __init__(self):
        self.examples = []
        
    def create_ioc_analysis_examples(self) -> List[Dict]:
        """IOC analysis and correlation examples"""
        
        examples = [
            {
                "query": "Analyze IOC 5.45.68.23 for threat attribution and campaign correlation using OSINT sources",
                "context": "IP address IOC analysis requires correlation across multiple threat intelligence sources including VirusTotal, AbuseIPDB, Shodan, passive DNS, and commercial feeds. Attribution involves analyzing associated domains, certificates, infrastructure patterns, and campaign TTPs for threat actor identification.",
                "expected_response": "IOC Analysis for 5.45.68.23: 1) VirusTotal/AbuseIPDB reputation check, 2) Passive DNS for associated domains, 3) Shodan for service fingerprinting, 4) SSL certificate analysis for infrastructure attribution, 5) Campaign correlation via TTP matching, 6) Generate IOC expansion list for proactive hunting. Report confidence level and attribution assessment.",
                "knowledge_source": "Threat Intelligence IOC Analysis",
                "tags": ["threat_intel", "ioc_analysis", "osint", "attribution", "correlation", "teacher_mode"]
            },
            
            {
                "query": "Create YARA rules for detecting APT29 (Cozy Bear) malware families based on recent campaigns",
                "context": "APT29 uses sophisticated malware including SolarWinds backdoor, WellMess, and custom implants. YARA rules should capture unique strings, API calls, encryption routines, and behavioral patterns. Rules must balance detection accuracy with false positive reduction across multiple malware variants.",
                "expected_response": "rule APT29_Generic { strings: $s1 = \"SolarWinds.Orion\" ascii wide $s2 = {48 8B 05 ?? ?? ?? ?? 48 85 C0 74 ??} condition: any of ($s*) and filesize < 10MB } Focus on: API hashing, encryption keys, C2 communication patterns, persistence mechanisms. Include metadata for campaign attribution and confidence scoring.",
                "knowledge_source": "APT29 Malware Analysis Reports",
                "tags": ["threat_intel", "yara_rules", "apt29", "malware_analysis", "detection"]
            },
            
            {
                "query": "Correlate STIX/TAXII threat intelligence feeds with internal security events for automated enrichment",
                "context": "STIX/TAXII provides standardized threat intelligence sharing format. Correlation involves matching IOCs from feeds with SIEM events, EDR alerts, and network logs. Automated enrichment adds threat context, attribution, and recommended actions to security alerts.",
                "expected_response": "STIX/TAXII enrichment pipeline: 1) Parse STIX indicators and TTPs, 2) Normalize IOCs for SIEM correlation, 3) Match indicators with security events using confidence scoring, 4) Enrich alerts with threat context and attribution, 5) Generate automated response recommendations, 6) Update threat hunting queries with new IOCs.",
                "knowledge_source": "STIX/TAXII Implementation Guide",
                "tags": ["threat_intel", "stix_taxii", "automation", "enrichment", "correlation"]
            }
        ]
        
        return examples
    
    def create_osint_investigation_examples(self) -> List[Dict]:
        """OSINT investigation and research examples"""
        
        examples = [
            {
                "query": "Conduct OSINT investigation on suspicious domain using passive DNS and certificate transparency",
                "context": "Domain investigation requires passive DNS analysis, certificate transparency logs, WHOIS history, subdomain enumeration, and infrastructure mapping. Investigation should identify registration patterns, hosting providers, related domains, and potential threat actor infrastructure.",
                "expected_response": "Domain OSINT methodology: 1) Passive DNS (SecurityTrails, VirusTotal) for IP history, 2) Certificate Transparency (crt.sh) for subdomain discovery, 3) WHOIS historical analysis for registration patterns, 4) Subdomain enumeration via DNS brute force, 5) Infrastructure mapping using Shodan/Censys, 6) Timeline correlation with known campaigns.",
                "knowledge_source": "OSINT Domain Investigation Techniques",
                "tags": ["osint", "domain_investigation", "passive_dns", "certificate_transparency", "methodology"]
            },
            
            {
                "query": "Research threat actor infrastructure using social media intelligence and dark web monitoring",
                "context": "Threat actor research combines social media analysis, dark web forum monitoring, and operational security assessment. Investigation focuses on identifying personas, communication patterns, operational capabilities, and infrastructure preferences across multiple platforms.",
                "expected_response": "Threat actor OSINT: 1) Social media persona mapping across platforms, 2) Dark web forum analysis for capabilities and services, 3) Communication pattern analysis for OPSEC assessment, 4) Infrastructure preference identification, 5) Network analysis for associate mapping, 6) Timeline correlation with known campaigns and operations.",
                "knowledge_source": "Threat Actor Research Methodologies",
                "tags": ["osint", "threat_actor", "social_media", "dark_web", "research"]
            }
        ]
        
        return examples
    
    def create_threat_hunting_intel_examples(self) -> List[Dict]:
        """Threat intelligence-driven hunting examples"""
        
        examples = [
            {
                "query": "Design threat hunting hypothesis based on recent APT40 TTPs and marine industry targeting",
                "context": "APT40 targets maritime industries using spear phishing, web shells, and credential harvesting. Recent campaigns show focus on shipping logistics, port management systems, and maritime research. Hunting should focus on industry-specific attack vectors and infrastructure.",
                "expected_response": "APT40 hunting hypothesis: Maritime organizations face increased risk from spear phishing targeting shipping logistics personnel, web shell deployment on public-facing applications, and credential harvesting from maritime research systems. Hunt for: maritime-themed phishing, unusual web application activity, and suspicious access to shipping management systems.",
                "knowledge_source": "APT40 Campaign Analysis",
                "tags": ["threat_hunting", "apt40", "maritime", "hypothesis", "industry_targeting"]
            },
            
            {
                "query": "Create proactive hunting queries for detecting novel ransomware variants based on behavioral patterns",
                "context": "Ransomware evolution requires behavioral detection beyond signature-based approaches. Novel variants may use different encryption algorithms, communication protocols, or deployment methods while maintaining core ransomware behaviors like file encryption, shadow copy deletion, and ransom note deployment.",
                "expected_response": "Novel ransomware hunting: Monitor for: 1) Rapid file extension changes across multiple directories, 2) Shadow copy deletion commands (vssadmin, wmic), 3) Unusual network connections during encryption process, 4) Process creation chains leading to encryption behavior, 5) Registry modifications for persistence, 6) Creation of ransom note files with entropy analysis.",
                "knowledge_source": "Ransomware Behavioral Analysis",
                "tags": ["threat_hunting", "ransomware", "behavioral_detection", "novel_variants", "proactive"]
            }
        ]
        
        return examples
    
    def create_attribution_analysis_examples(self) -> List[Dict]:
        """Threat attribution and campaign tracking examples"""
        
        examples = [
            {
                "query": "Perform attribution analysis for a sophisticated phishing campaign using infrastructure overlaps and TTP correlation",
                "context": "Attribution analysis requires analyzing infrastructure patterns, TTP overlaps, operational timing, language artifacts, and campaign objectives. High-confidence attribution combines multiple independent indicators across infrastructure, techniques, and operational patterns.",
                "expected_response": "Attribution methodology: 1) Infrastructure overlap analysis with known threat actors, 2) TTP correlation using MITRE ATT&CK framework, 3) Operational timing analysis for geographic indicators, 4) Language artifact examination in malware/communications, 5) Campaign objective assessment, 6) Confidence scoring based on indicator overlap and uniqueness.",
                "knowledge_source": "Threat Attribution Methodologies",
                "tags": ["threat_intel", "attribution", "campaign_tracking", "ttp_analysis", "methodology"]
            },
            
            {
                "query": "Track ransomware-as-a-service operations using underground forum monitoring and payment analysis",
                "context": "RaaS operations involve affiliate programs, payment processing, and underground marketing. Tracking requires monitoring dark web forums, analyzing payment flows, identifying affiliate relationships, and mapping service infrastructure across multiple criminal operations.",
                "expected_response": "RaaS tracking: 1) Underground forum monitoring for affiliate recruitment, 2) Payment flow analysis using blockchain analytics, 3) Affiliate relationship mapping through operational patterns, 4) Service infrastructure identification via hosting analysis, 5) Cross-operation correlation for shared resources, 6) Revenue and operational assessment.",
                "knowledge_source": "RaaS Operation Analysis",
                "tags": ["threat_intel", "raas", "underground_forums", "payment_analysis", "tracking"]
            }
        ]
        
        return examples
    
    def create_intelligence_automation_examples(self) -> List[Dict]:
        """Intelligence automation and processing examples"""
        
        examples = [
            {
                "query": "Automate threat intelligence processing using machine learning for IOC scoring and prioritization",
                "context": "Automated intelligence processing uses ML algorithms to score IOC relevance, prioritize threats based on organizational context, and reduce analyst workload. Processing involves feature extraction, confidence scoring, false positive reduction, and contextual relevance assessment.",
                "expected_response": "ML-driven intel automation: 1) Feature extraction from IOC metadata and context, 2) Relevance scoring based on organizational assets and threats, 3) Confidence assessment using multiple intelligence sources, 4) False positive reduction through historical analysis, 5) Automated triage and analyst queue management, 6) Feedback loop for model improvement.",
                "knowledge_source": "Intelligence Automation Frameworks",
                "tags": ["threat_intel", "automation", "machine_learning", "ioc_scoring", "prioritization"]
            },
            
            {
                "query": "Implement automated threat actor tracking using natural language processing of security reports",
                "context": "Automated actor tracking processes unstructured threat reports, extracts TTPs and IOCs, maps to existing actor profiles, and identifies emerging threats. NLP processing handles report standardization, entity extraction, and relationship mapping for comprehensive threat tracking.",
                "expected_response": "NLP threat tracking: 1) Report ingestion and preprocessing for standardization, 2) Named entity recognition for actor, malware, and TTP extraction, 3) Relationship mapping using graph databases, 4) Actor profile correlation and updating, 5) Emerging threat identification through pattern analysis, 6) Automated report generation and dissemination.",
                "knowledge_source": "NLP Threat Intelligence Processing",
                "tags": ["threat_intel", "nlp", "automation", "actor_tracking", "report_processing"]
            }
        ]
        
        return examples
    
    def generate_all_threat_intel_examples(self) -> List[Dict]:
        """Generate comprehensive threat intelligence dataset"""
        
        all_examples = []
        all_examples.extend(self.create_ioc_analysis_examples())
        all_examples.extend(self.create_osint_investigation_examples())
        all_examples.extend(self.create_threat_hunting_intel_examples())
        all_examples.extend(self.create_attribution_analysis_examples())
        all_examples.extend(self.create_intelligence_automation_examples())
        
        # Add metadata to each example
        for i, example in enumerate(all_examples):
            example.update({
                "id": f"threat_intel_rag_{i+1:03d}",
                "created_date": datetime.now().isoformat(),
                "content_hash": hashlib.md5(example["query"].encode()).hexdigest()[:8],
                "retrieval_type": "threat_intelligence_learning",
                "intelligence_type": "tactical_strategic"
            })
        
        return all_examples
    
    def save_threat_intel_dataset(self, output_file: str = "threat_intel_rag_training_data.json"):
        """Save threat intelligence training dataset"""
        
        examples = self.generate_all_threat_intel_examples()
        
        dataset = {
            "dataset_info": {
                "name": "Whis Threat Intelligence RAG Training Data",
                "version": "3.0", 
                "created_date": datetime.now().isoformat(),
                "total_examples": len(examples),
                "intelligence_focus": "tactical_strategic_operational",
                "categories": {
                    "ioc_analysis": len([e for e in examples if "ioc_analysis" in e.get("tags", [])]),
                    "osint_investigation": len([e for e in examples if "osint" in e.get("tags", [])]),
                    "threat_hunting_intel": len([e for e in examples if "threat_hunting" in e.get("tags", [])]),
                    "attribution_analysis": len([e for e in examples if "attribution" in e.get("tags", [])]),
                    "intelligence_automation": len([e for e in examples if "automation" in e.get("tags", [])])
                }
            },
            "examples": examples
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(dataset, f, indent=2, ensure_ascii=False)
        
        print(f"🎯 Generated {len(examples)} THREAT INTEL RAG training examples")
        print(f"💾 Saved to: {output_file}")
        
        return dataset

def main():
    """Generate threat intelligence RAG training data"""
    print("🎯 THREAT INTELLIGENCE RAG TRAINING DATA GENERATOR")
    print("=" * 60)
    
    generator = ThreatIntelRAGGenerator()
    dataset = generator.save_threat_intel_dataset()
    
    print("\n📊 Threat Intel Dataset Statistics:")
    for category, count in dataset["dataset_info"]["categories"].items():
        print(f"  • {category.replace('_', ' ').title()}: {count} examples")
    
    print(f"\n🎯 Total Threat Intel Examples: {dataset['dataset_info']['total_examples']}")
    print("🚀 Ready for threat intelligence training!")
    
    return dataset

if __name__ == "__main__":
    main()