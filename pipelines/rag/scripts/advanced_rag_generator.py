#!/usr/bin/env python3
"""
Advanced RAG Training Data Generator
Creates specialized SecOps scenarios for Whis training
"""

import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict

class AdvancedRAGGenerator:
    """Generate advanced SecOps training examples"""
    
    def __init__(self):
        self.examples = []
        
    def create_advanced_windows_events(self) -> List[Dict]:
        """Advanced Windows Event correlation examples"""
        
        examples = [
            {
                "query": "Correlate Windows Event 4740 account lockout with preceding 4625 failures for brute force detection",
                "context": "Event 4740 (Account Locked Out) combined with multiple 4625 events indicates successful brute force detection by account lockout policies. Key correlation fields include Account Name, Source Workstation, and Caller Computer Name. Time correlation should be within policy lockout threshold window.",
                "expected_response": "Correlation: Event 4625 → 4740 sequence indicates lockout-triggered brute force detection. Monitor: Account Name match, Source IP consistency, failure count vs lockout threshold, time window correlation. High confidence indicator when 4625 count exceeds lockout policy within time window followed by 4740.",
                "knowledge_source": "Windows Security Log Correlation",
                "tags": ["windows", "correlation", "brute_force", "event_4740", "event_4625", "teacher_mode"]
            },
            
            {
                "query": "Analyze Windows Event 4768 TGT requests for Kerberoasting attack patterns",
                "context": "Event 4768 (TGT Request) can indicate Kerberoasting when combined with specific encryption types. RC4 encryption (0x17) in TGT requests, especially for service accounts, suggests potential Kerberoasting. Monitor for unusual TGT request patterns, service account targeting, and encryption downgrade attacks.",
                "expected_response": "Event 4768 Kerberoasting indicators: RC4 encryption (0x17) requests, service account targeting, unusual request volume, source IP patterns. Detection: Filter for RC4 TGT requests to service accounts, baseline normal authentication patterns, alert on encryption downgrade attempts.",
                "knowledge_source": "Kerberos Attack Detection",
                "tags": ["windows", "kerberos", "kerberoasting", "event_4768", "encryption", "detection"]
            },
            
            {
                "query": "Detect Windows Event 4688 process creation chains for living-off-the-land attacks",
                "context": "Event 4688 process creation can reveal attack chains using legitimate Windows utilities. Monitor for suspicious parent-child relationships like cmd.exe → powershell.exe → certutil.exe or wmiprvse.exe spawning unusual processes. Process command lines and execution sequences are critical for detection.",
                "expected_response": "Event 4688 LOLBAS detection: Monitor process chains cmd→powershell→certutil, wmiprvse spawning shells, rundll32 with unusual DLLs. Key fields: Parent Process, Process Command Line, Creator Process. Baseline normal administrative activity vs suspicious sequences.",
                "knowledge_source": "Living-off-the-Land Binary Detection",
                "tags": ["windows", "process_creation", "lolbas", "event_4688", "attack_chain"]
            }
        ]
        
        return examples
    
    def create_advanced_mitre_techniques(self) -> List[Dict]:
        """Advanced MITRE ATT&CK correlation examples"""
        
        examples = [
            {
                "query": "Map credential dumping techniques T1003 variants to detection strategies across multiple data sources",
                "context": "T1003 Credential Dumping has multiple subtechniques: T1003.001 (LSASS Memory), T1003.002 (Security Account Manager), T1003.003 (NTDS), T1003.004 (LSA Secrets), T1003.005 (Cached Credentials), T1003.006 (DCSync), T1003.008 (Windows Credential Manager). Each requires different detection approaches across EDR, Windows logs, and network monitoring.",
                "expected_response": "T1003 detection matrix: LSASS access (Sysmon 10, Process Access), SAM/NTDS file access (4663), DCSync (4662 with replication rights), credential manager access (Registry/API calls). Multi-source correlation: EDR process monitoring + Windows security logs + network traffic analysis for comprehensive coverage.",
                "knowledge_source": "MITRE ATT&CK T1003 Detection Guide",
                "tags": ["mitre_attack", "T1003", "credential_dumping", "multi_source", "correlation"]
            },
            
            {
                "query": "Design detection for T1574 DLL Hijacking across different Windows versions and attack vectors",
                "context": "T1574 DLL Hijacking varies by Windows version and application vulnerability. Common vectors include phantom DLL loading, DLL search order exploitation, and DLL replacement. Detection requires monitoring DLL loads from unusual locations, unsigned DLLs in system directories, and application-specific DLL load patterns.",
                "expected_response": "T1574 DLL Hijacking detection: Monitor Sysmon Event 7 (Image/DLL Load) for unsigned DLLs in system paths, unusual load locations, phantom DLLs. Key indicators: DLL loads from temp/user directories, unsigned libraries in system folders, application spawning from unusual locations. Baseline per-application DLL patterns.",
                "knowledge_source": "DLL Hijacking Detection Strategies",
                "tags": ["mitre_attack", "T1574", "dll_hijacking", "sysmon", "application_security"]
            },
            
            {
                "query": "Correlate T1055 Process Injection with T1036 Masquerading for advanced evasion detection",
                "context": "Advanced attackers combine T1055 Process Injection with T1036 Masquerading to evade detection. This involves injecting malicious code into legitimate processes while masquerading process names, file paths, or metadata. Detection requires behavioral analysis, memory inspection, and process hollowing indicators.",
                "expected_response": "T1055+T1036 correlation: Process injection into masqueraded processes creates detection blind spots. Monitor: Process name vs file path mismatches, unsigned code in signed processes, hollow process indicators, memory allocation patterns. Cross-reference process metadata with behavioral analysis for evasion detection.",
                "knowledge_source": "Advanced Evasion Technique Correlation",
                "tags": ["mitre_attack", "T1055", "T1036", "evasion", "correlation", "behavioral_analysis"]
            }
        ]
        
        return examples
    
    def create_advanced_splunk_queries(self) -> List[Dict]:
        """Advanced Splunk correlation and hunting queries"""
        
        examples = [
            {
                "query": "Create a Splunk search for detecting credential stuffing across multiple applications using statistical analysis",
                "context": "Credential stuffing attacks target multiple applications with stolen credentials. Detection requires analyzing login patterns across different services, identifying shared source IPs, timing correlations, and success/failure ratios that indicate automated credential testing.",
                "expected_response": "| multisearch [search index=app1_logs failed_login] [search index=app2_logs authentication_failure] | eval source_type=case(index=\"app1_logs\",\"app1\",index=\"app2_logs\",\"app2\") | stats dc(source_type) as app_count, count as attempts by src_ip,user | where app_count>1 AND attempts>10 | eval credential_stuffing_score=app_count*attempts",
                "knowledge_source": "Multi-Application Security Correlation",
                "tags": ["splunk", "credential_stuffing", "correlation", "statistical_analysis", "assistant_mode"]
            },
            
            {
                "query": "Write a Splunk search to detect data exfiltration using DNS tunneling with entropy analysis",
                "context": "DNS tunneling for data exfiltration creates high-entropy DNS queries with unusual subdomain patterns. Detection involves analyzing DNS query entropy, subdomain length distributions, query frequency, and domain reputation. Statistical baselines help identify anomalous DNS behavior.",
                "expected_response": "index=dns_logs | eval subdomain_entropy=entropy(query) | eval subdomain_length=len(query) | stats avg(subdomain_entropy) as avg_entropy, max(subdomain_length) as max_length, count as query_count by src_ip,domain | where avg_entropy>3.5 AND max_length>50 AND query_count>100 | eval exfil_score=avg_entropy*max_length",
                "knowledge_source": "DNS Tunneling Detection Techniques",
                "tags": ["splunk", "dns_tunneling", "entropy_analysis", "data_exfiltration", "statistical"]
            },
            
            {
                "query": "Build a Splunk correlation search for detecting insider threat indicators using behavioral analytics",
                "context": "Insider threat detection requires analyzing user behavior patterns including access times, data volume, privileged escalation, and unusual resource access. Behavioral baselines and anomaly detection help identify potential insider threats through deviation analysis.",
                "expected_response": "| multisearch [search index=file_access] [search index=privilege_escalation] [search index=network_traffic] | stats sum(data_bytes) as total_data, dc(resource) as unique_resources, dc(privilege_level) as escalation_count by user,hour | eventstats avg(total_data) as avg_data_baseline by user | eval anomaly_score=if(total_data>avg_data_baseline*3,3,1) | where anomaly_score>2",
                "knowledge_source": "Insider Threat Behavioral Analytics",
                "tags": ["splunk", "insider_threat", "behavioral_analytics", "anomaly_detection", "user_behavior"]
            }
        ]
        
        return examples
    
    def create_advanced_limacharlie_rules(self) -> List[Dict]:
        """Advanced LimaCharlie D&R rules for complex threats"""
        
        examples = [
            {
                "query": "Create a LimaCharlie rule to detect advanced persistent threat (APT) lateral movement using WMI",
                "context": "APT groups often use WMI for lateral movement and remote execution. Detection requires monitoring WMI process creation, authentication events, and command execution patterns. LimaCharlie can detect WMI-based lateral movement through process lineage and network correlation.",
                "expected_response": "detect:\\n  event: NEW_PROCESS\\n  op: and\\n  rules:\\n    - op: is\\n      path: event/PARENT/PROCESS_NAME\\n      value: \"wmiprvse.exe\"\\n    - op: contains\\n      path: event/COMMAND_LINE\\n      value: \"process call create\"\\n    - op: not\\n      path: event/PROCESS_PATH\\n      re: \"^C:\\\\\\\\Windows\\\\\\\\(System32|SysWOW64)\\\\\\\\\"\\nrespond:\\n  - action: report\\n    name: apt_wmi_lateral_movement\\n  - action: isolation\\n    duration: 1800",
                "knowledge_source": "APT Lateral Movement Detection",
                "tags": ["limacharlie", "apt", "lateral_movement", "wmi", "process_monitoring"]
            },
            
            {
                "query": "Design a LimaCharlie rule for detecting fileless malware using memory injection techniques",
                "context": "Fileless malware uses memory injection to avoid disk-based detection. LimaCharlie can monitor memory allocations, process hollowing, and reflective DLL loading. Detection focuses on unusual memory patterns, process behavior changes, and injection indicators.",
                "expected_response": "detect:\\n  event: MEMORY_ALLOC\\n  op: and\\n  rules:\\n    - op: is\\n      path: event/MEMORY_TYPE\\n      value: \"PAGE_EXECUTE_READWRITE\"\\n    - op: is\\n      path: event/ALLOCATION_TYPE\\n      value: \"MEM_COMMIT\"\\n    - op: \">\"\\n      path: event/MEMORY_SIZE\\n      value: 1048576\\nrespond:\\n  - action: memory_dump\\n    pid: \"<<routing/parent/pid>>\"\\n  - action: report\\n    name: fileless_memory_injection",
                "knowledge_source": "Fileless Malware Detection Techniques",
                "tags": ["limacharlie", "fileless_malware", "memory_injection", "process_hollowing", "response"]
            }
        ]
        
        return examples
    
    def create_advanced_incident_response(self) -> List[Dict]:
        """Advanced incident response scenarios"""
        
        examples = [
            {
                "query": "Design incident response procedures for a zero-day exploitation targeting cloud infrastructure",
                "context": "Zero-day exploits in cloud environments require rapid containment across multiple cloud services, identity systems, and hybrid infrastructure. Response involves cloud-specific isolation, API security analysis, and coordinated response across on-premises and cloud resources.",
                "expected_response": "Zero-day cloud IR: 1) Immediate API key rotation and MFA enforcement, 2) Cloud resource isolation via security groups/NACLs, 3) Enable detailed cloud logging and forensic imaging, 4) Coordinate with cloud provider security teams, 5) Implement emergency access controls, 6) Begin parallel on-premises investigation for lateral movement",
                "knowledge_source": "Cloud Security Incident Response",
                "tags": ["incident_response", "zero_day", "cloud_security", "containment", "coordination"]
            },
            
            {
                "query": "Outline response procedures for a supply chain compromise affecting critical infrastructure",
                "context": "Supply chain attacks targeting critical infrastructure require coordinated response across multiple organizations, regulatory compliance, and potential national security considerations. Response involves vendor coordination, impact assessment, and infrastructure protection measures.",
                "expected_response": "Supply chain IR: 1) Immediate vendor communication and compromise verification, 2) Asset inventory of affected components across infrastructure, 3) Coordinate with sector ISAC and regulatory bodies, 4) Implement compensating controls for compromised components, 5) Begin forensic analysis of supply chain artifacts, 6) Activate business continuity plans for critical services",
                "knowledge_source": "Supply Chain Security Response",
                "tags": ["incident_response", "supply_chain", "critical_infrastructure", "coordination", "compliance"]
            }
        ]
        
        return examples
    
    def create_advanced_threat_hunting(self) -> List[Dict]:
        """Advanced threat hunting methodologies"""
        
        examples = [
            {
                "query": "Design a threat hunting campaign for detecting state-sponsored APT activity using behavioral analytics",
                "context": "State-sponsored APTs use sophisticated techniques requiring advanced hunting methodologies. Hunting focuses on long-term persistence, data staging, covert channels, and operational patterns. Behavioral analytics help identify subtle indicators of advanced threats.",
                "expected_response": "APT hunting methodology: 1) Baseline normal administrative behavior and establish user behavior analytics, 2) Hunt for long-term persistence mechanisms across multiple systems, 3) Analyze network flows for covert channels and data staging, 4) Correlate logon patterns with geopolitical events, 5) Search for supply chain indicators and zero-day exploitation artifacts, 6) Use stack ranking to identify statistical outliers",
                "knowledge_source": "Advanced Persistent Threat Hunting",
                "tags": ["threat_hunting", "apt", "state_sponsored", "behavioral_analytics", "methodology"]
            },
            
            {
                "query": "Develop hunting techniques for detecting insider threats using machine learning approaches",
                "context": "Insider threat hunting requires analyzing user behavior patterns, access anomalies, and psychological indicators. Machine learning helps identify subtle behavioral changes and anomalous access patterns that traditional rule-based detection might miss.",
                "expected_response": "ML-based insider hunting: 1) Create user behavior baselines using unsupervised clustering, 2) Implement anomaly detection for access patterns and data movement, 3) Analyze emotional sentiment in communications for psychological indicators, 4) Use time-series analysis for behavioral drift detection, 5) Correlate HR events with security behavior changes, 6) Implement peer group analysis for comparative behavioral assessment",
                "knowledge_source": "Machine Learning Threat Hunting",
                "tags": ["threat_hunting", "insider_threat", "machine_learning", "behavioral_analysis", "anomaly_detection"]
            }
        ]
        
        return examples
    
    def generate_all_advanced_examples(self) -> List[Dict]:
        """Generate comprehensive advanced training dataset"""
        
        all_examples = []
        all_examples.extend(self.create_advanced_windows_events())
        all_examples.extend(self.create_advanced_mitre_techniques())
        all_examples.extend(self.create_advanced_splunk_queries())
        all_examples.extend(self.create_advanced_limacharlie_rules())
        all_examples.extend(self.create_advanced_incident_response())
        all_examples.extend(self.create_advanced_threat_hunting())
        
        # Add metadata to each example
        for i, example in enumerate(all_examples):
            example.update({
                "id": f"advanced_rag_{i+1:03d}",
                "created_date": datetime.now().isoformat(),
                "content_hash": hashlib.md5(example["query"].encode()).hexdigest()[:8],
                "retrieval_type": "advanced_supervised_learning",
                "complexity_level": "advanced"
            })
        
        return all_examples
    
    def save_advanced_dataset(self, output_file: str = "advanced_rag_training_data.json"):
        """Save advanced RAG training dataset"""
        
        examples = self.generate_all_advanced_examples()
        
        dataset = {
            "dataset_info": {
                "name": "Whis Advanced RAG Training Data", 
                "version": "2.0",
                "created_date": datetime.now().isoformat(),
                "total_examples": len(examples),
                "complexity_level": "advanced",
                "categories": {
                    "advanced_windows_events": len([e for e in examples if "windows" in e.get("tags", [])]),
                    "advanced_mitre_attack": len([e for e in examples if "mitre_attack" in e.get("tags", [])]),
                    "advanced_splunk_queries": len([e for e in examples if "splunk" in e.get("tags", [])]),
                    "advanced_limacharlie_rules": len([e for e in examples if "limacharlie" in e.get("tags", [])]),
                    "advanced_incident_response": len([e for e in examples if "incident_response" in e.get("tags", [])]),
                    "advanced_threat_hunting": len([e for e in examples if "threat_hunting" in e.get("tags", [])])
                }
            },
            "examples": examples
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(dataset, f, indent=2, ensure_ascii=False)
        
        print(f"🔥 Generated {len(examples)} ADVANCED RAG training examples")
        print(f"💾 Saved to: {output_file}")
        
        return dataset

def main():
    """Generate advanced RAG training data"""
    print("🔥 ADVANCED RAG TRAINING DATA GENERATOR")
    print("=" * 50)
    
    generator = AdvancedRAGGenerator()
    dataset = generator.save_advanced_dataset()
    
    print("\n📊 Advanced Dataset Statistics:")
    for category, count in dataset["dataset_info"]["categories"].items():
        print(f"  • {category.replace('_', ' ').title()}: {count} examples")
    
    print(f"\n🎯 Total Advanced Examples: {dataset['dataset_info']['total_examples']}")
    print("🚀 Ready for advanced SecOps training!")
    
    return dataset

if __name__ == "__main__":
    main()