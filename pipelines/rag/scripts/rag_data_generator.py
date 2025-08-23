#!/usr/bin/env python3
"""
Enhanced RAG Training Data Generator
Creates supervised learning examples for Whis knowledge retrieval
"""

import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict

class RAGDataGenerator:
    """Generate supervised RAG training examples"""
    
    def __init__(self):
        self.examples = []
        
    def create_windows_events_data(self) -> List[Dict]:
        """Windows Event ID training examples"""
        
        examples = [
            {
                "query": "What does Windows Event ID 4624 indicate and what are the key fields?",
                "context": "Windows Event 4624 represents successful logon events. Key fields include LogonType (2=interactive, 3=network, 10=RemoteInteractive), Account Name, Source Network Address, and Logon Process. This event is crucial for tracking user authentication activity.",
                "expected_response": "Event 4624 indicates successful user logon. Key fields: LogonType (2=interactive, 3=network, 10=remote), Account Name, Source IP, Logon Process. Critical for authentication monitoring and baseline establishment.",
                "knowledge_source": "Windows Security Event Reference",
                "tags": ["windows", "authentication", "event_4624", "teacher_mode"]
            },
            
            {
                "query": "Explain Windows Event ID 4648 and its significance for lateral movement detection",
                "context": "Event 4648 occurs when a logon is attempted using explicit credentials (RunAs). This is significant for detecting lateral movement as attackers often use stolen credentials to authenticate to remote systems. Fields include Subject (who initiated), Target Server, and Account Name being used.",
                "expected_response": "Event 4648 = explicit credential usage (RunAs). Critical for lateral movement detection as attackers use stolen credentials. Monitor Subject vs Account Name discrepancies and cross-network authentication patterns.",
                "knowledge_source": "MITRE ATT&CK T1021",
                "tags": ["windows", "lateral_movement", "event_4648", "detection"]
            },
            
            {
                "query": "What is Windows Event ID 4672 and why is it important for privilege escalation monitoring?",
                "context": "Event 4672 indicates that special privileges were assigned to a new logon. This event is generated when an account is assigned user rights that are considered sensitive (like SeDebugPrivilege, SeBackupPrivilege). It's crucial for monitoring privilege escalation attempts.",
                "expected_response": "Event 4672 = special privileges assigned to new logon. Critical for privilege escalation monitoring. Watch for sensitive rights like SeDebugPrivilege, SeBackupPrivilege being assigned to regular user accounts.",
                "knowledge_source": "Windows Security Monitoring Guide",
                "tags": ["windows", "privilege_escalation", "event_4672", "monitoring"]
            }
        ]
        
        return examples
    
    def create_mitre_attack_data(self) -> List[Dict]:
        """MITRE ATT&CK technique training examples"""
        
        examples = [
            {
                "query": "Explain MITRE ATT&CK technique T1078 and provide detection strategies",
                "context": "T1078 (Valid Accounts) involves adversaries using legitimate credentials to maintain access. Subtechniques include T1078.001 (Default Accounts), T1078.002 (Domain Accounts), T1078.003 (Local Accounts), and T1078.004 (Cloud Accounts). Detection focuses on unusual access patterns, privilege usage, and cross-system authentication.",
                "expected_response": "T1078 Valid Accounts: Adversaries use legitimate credentials. Subtechniques: Default/Domain/Local/Cloud accounts. Detection: Monitor unusual login patterns, privilege escalation, geographic anomalies, and failed-then-successful authentication sequences.",
                "knowledge_source": "MITRE ATT&CK Framework",
                "tags": ["mitre_attack", "T1078", "valid_accounts", "detection"]
            },
            
            {
                "query": "What is MITRE ATT&CK T1055 Process Injection and what are common detection methods?",
                "context": "T1055 Process Injection allows adversaries to execute code in the address space of legitimate processes. Common techniques include DLL injection, Process Hollowing, and Thread Execution Hijacking. Detection involves monitoring for unusual process behavior, memory modifications, and API calls like CreateRemoteThread, WriteProcessMemory.",
                "expected_response": "T1055 Process Injection: Execute code in legitimate process space. Techniques: DLL injection, process hollowing, thread hijacking. Detection: Monitor CreateRemoteThread, WriteProcessMemory APIs, unusual child processes, memory anomalies.",
                "knowledge_source": "MITRE ATT&CK Framework",
                "tags": ["mitre_attack", "T1055", "process_injection", "edr"]
            },
            
            {
                "query": "Describe MITRE ATT&CK T1059 Command and Scripting Interpreter with detection approaches",
                "context": "T1059 involves adversaries using command and scripting interpreters to execute code. Subtechniques include PowerShell (T1059.001), AppleScript (T1059.002), Windows Command Shell (T1059.003), and others. Detection focuses on command-line analysis, script content inspection, and behavioral patterns.",
                "expected_response": "T1059 Command/Scripting Interpreter: Execute code via interpreters. Key subtechniques: PowerShell, cmd.exe, bash. Detection: Monitor command-line arguments, encoded commands, script execution policies, and unusual interpreter spawning patterns.",
                "knowledge_source": "MITRE ATT&CK Framework", 
                "tags": ["mitre_attack", "T1059", "command_line", "powershell"]
            }
        ]
        
        return examples
    
    def create_splunk_siem_data(self) -> List[Dict]:
        """Splunk SIEM query and detection examples"""
        
        examples = [
            {
                "query": "Create a Splunk search to detect potential brute force attacks using Windows Event 4625",
                "context": "Brute force attacks generate multiple failed logon events (4625) from the same source. Effective detection requires analyzing failure counts, unique accounts targeted, and source IP patterns within specific time windows.",
                "expected_response": "index=security EventCode=4625 | bucket _time span=5m | stats count as failures, dc(Account_Name) as unique_accounts by src_ip, _time | where failures > 5 AND unique_accounts > 1 | eval risk_score = failures * unique_accounts",
                "knowledge_source": "Splunk ES Documentation",
                "tags": ["splunk", "spl", "brute_force", "detection", "assistant_mode"]
            },
            
            {
                "query": "Write a Splunk query to identify suspicious PowerShell execution patterns",
                "context": "Malicious PowerShell often uses encoded commands, download functions, and execution policy bypasses. Detection should look for these patterns in PowerShell event logs (EventCode 4104, 4103) and analyze command content.",
                "expected_response": "index=security sourcetype=\"WinEventLog:Microsoft-Windows-PowerShell/Operational\" | search EventCode=4104 OR EventCode=4103 | regex Message=\"(?i)(encodedcommand|downloadstring|invoke-expression|bypass)\" | stats count by Computer, User, Message | where count > 1",
                "knowledge_source": "PowerShell Security Best Practices",
                "tags": ["splunk", "powershell", "malware", "detection"]
            },
            
            {
                "query": "How do you create a Splunk correlation search for lateral movement detection?",
                "context": "Lateral movement involves authentication across multiple systems in short time periods. Detection should correlate successful logons (4624) across different hosts from the same user account within suspicious timeframes.",
                "expected_response": "index=security EventCode=4624 | eval src_category=case(cidrmatch(\"192.168.0.0/16\",src_ip),\"internal\", 1=1,\"external\") | where src_category=\"internal\" | stats dc(dest_host) as unique_hosts, values(dest_host) as hosts by user, _time | where unique_hosts > 3",
                "knowledge_source": "Splunk Security Use Cases",
                "tags": ["splunk", "lateral_movement", "correlation", "advanced"]
            }
        ]
        
        return examples
    
    def create_limacharlie_edr_data(self) -> List[Dict]:
        """LimaCharlie EDR Detection & Response examples"""
        
        examples = [
            {
                "query": "Create a LimaCharlie D&R rule to detect suspicious process creation patterns",
                "context": "LimaCharlie D&R rules use YAML format to define detection logic and response actions. Process creation monitoring should focus on unusual parent-child relationships, command-line arguments, and execution from suspicious locations.",
                "expected_response": "detect:\n  event: NEW_PROCESS\n  op: and\n  rules:\n    - op: contains\n      path: event/COMMAND_LINE\n      value: \"powershell\"\n    - op: contains\n      path: event/COMMAND_LINE\n      value: \"-EncodedCommand\"\nrespond:\n  - action: report\n    name: suspicious_powershell_encoded",
                "knowledge_source": "LimaCharlie Documentation",
                "tags": ["limacharlie", "edr", "detection_rule", "assistant_mode"]
            },
            
            {
                "query": "Write a LimaCharlie rule for detecting file-less malware execution",
                "context": "File-less malware often uses legitimate system processes and injects code into memory. Detection should monitor for unusual memory allocations, process hollowing, and execution from unexpected locations or contexts.",
                "expected_response": "detect:\n  event: MEMORY_ALLOC\n  op: and\n  rules:\n    - op: is\n      path: event/MEMORY_TYPE\n      value: \"PAGE_EXECUTE_READWRITE\"\n    - op: not\n      path: event/PROCESS_PATH\n      re: \"^C:\\\\\\\\Windows\\\\\\\\(System32|SysWOW64)\\\\\\\\.+\\.exe$\"\nrespond:\n  - action: isolation\n    duration: 3600\n  - action: report\n    name: potential_process_injection",
                "knowledge_source": "LimaCharlie EDR Best Practices",
                "tags": ["limacharlie", "fileless_malware", "memory_analysis", "response"]
            }
        ]
        
        return examples
    
    def create_incident_response_data(self) -> List[Dict]:
        """Incident Response playbook examples"""
        
        examples = [
            {
                "query": "Outline the immediate response steps for a confirmed ransomware incident",
                "context": "Ransomware incidents require rapid containment to prevent spread. Initial response focuses on isolation, impact assessment, and evidence preservation while coordinating with stakeholders.",
                "expected_response": "Immediate steps: 1) Isolate affected systems (network isolation, not power-off), 2) Assess scope via EDR/SIEM queries, 3) Preserve memory dumps and logs, 4) Notify incident commander and legal team, 5) Begin asset inventory of impacted systems, 6) Implement backup assessment and recovery planning",
                "knowledge_source": "NIST Incident Response Guide",
                "tags": ["incident_response", "ransomware", "containment", "playbook"]
            },
            
            {
                "query": "What are the key steps in investigating a data exfiltration incident?",
                "context": "Data exfiltration investigations require analyzing network traffic, user behavior, and access patterns to determine what data was accessed and how it was transmitted. Timeline reconstruction is critical.",
                "expected_response": "Investigation steps: 1) Identify data access patterns via logs, 2) Analyze network traffic for unusual outbound connections, 3) Check for data staging activities (compression, encryption), 4) Review user authentication and privilege usage, 5) Examine email/cloud storage for data transfers, 6) Reconstruct timeline with correlation analysis",
                "knowledge_source": "Data Breach Investigation Handbook",
                "tags": ["incident_response", "data_exfiltration", "investigation", "forensics"]
            }
        ]
        
        return examples
    
    def create_threat_hunting_data(self) -> List[Dict]:
        """Threat hunting hypothesis and methodology examples"""
        
        examples = [
            {
                "query": "Design a threat hunting hypothesis for detecting living-off-the-land attacks",
                "context": "Living-off-the-land attacks use legitimate system tools for malicious purposes. Hunting should focus on unusual usage patterns of built-in utilities like certutil, bitsadmin, regsvr32, and others in unexpected contexts.",
                "expected_response": "Hypothesis: Adversaries abuse legitimate Windows utilities for malicious purposes. Hunt for: certutil downloading files, bitsadmin transfers, regsvr32 with unusual arguments, rundll32 executing from temp directories, and wmic lateral movement. Baseline normal usage first.",
                "knowledge_source": "MITRE ATT&CK Living Off The Land",
                "tags": ["threat_hunting", "living_off_land", "hypothesis", "baseline"]
            },
            
            {
                "query": "What threat hunting approach would you use to find persistent backdoors?",
                "context": "Persistent backdoors establish long-term access through various mechanisms including registry modifications, scheduled tasks, services, and startup folder modifications. Hunting requires systematic enumeration of persistence mechanisms.",
                "expected_response": "Approach: 1) Hunt for unusual registry Run keys, 2) Enumerate suspicious scheduled tasks and services, 3) Check startup folders and WMI event subscriptions, 4) Analyze DLL hijacking opportunities, 5) Look for COM object hijacking, 6) Cross-reference with process execution timeline",
                "knowledge_source": "Windows Persistence Techniques",
                "tags": ["threat_hunting", "persistence", "backdoors", "enumeration"]
            }
        ]
        
        return examples
    
    def generate_all_examples(self) -> List[Dict]:
        """Generate comprehensive RAG training dataset"""
        
        all_examples = []
        all_examples.extend(self.create_windows_events_data())
        all_examples.extend(self.create_mitre_attack_data())
        all_examples.extend(self.create_splunk_siem_data())
        all_examples.extend(self.create_limacharlie_edr_data())
        all_examples.extend(self.create_incident_response_data())
        all_examples.extend(self.create_threat_hunting_data())
        
        # Add metadata to each example
        for i, example in enumerate(all_examples):
            example.update({
                "id": f"rag_example_{i+1:03d}",
                "created_date": datetime.now().isoformat(),
                "content_hash": hashlib.md5(example["query"].encode()).hexdigest()[:8],
                "retrieval_type": "supervised_learning"
            })
        
        return all_examples
    
    def save_rag_dataset(self, output_file: str = "enhanced_rag_training_data.json"):
        """Save RAG training dataset"""
        
        examples = self.generate_all_examples()
        
        dataset = {
            "dataset_info": {
                "name": "Whis Enhanced RAG Training Data",
                "version": "1.0",
                "created_date": datetime.now().isoformat(),
                "total_examples": len(examples),
                "categories": {
                    "windows_events": len([e for e in examples if "windows" in e.get("tags", [])]),
                    "mitre_attack": len([e for e in examples if "mitre_attack" in e.get("tags", [])]),
                    "splunk_siem": len([e for e in examples if "splunk" in e.get("tags", [])]),
                    "limacharlie_edr": len([e for e in examples if "limacharlie" in e.get("tags", [])]),
                    "incident_response": len([e for e in examples if "incident_response" in e.get("tags", [])]),
                    "threat_hunting": len([e for e in examples if "threat_hunting" in e.get("tags", [])])
                }
            },
            "examples": examples
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(dataset, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Generated {len(examples)} RAG training examples")
        print(f"💾 Saved to: {output_file}")
        
        return dataset

def main():
    """Generate enhanced RAG training data"""
    print("🔍 ENHANCED RAG TRAINING DATA GENERATOR")
    print("=" * 50)
    
    generator = RAGDataGenerator()
    dataset = generator.save_rag_dataset()
    
    print("\n📊 Dataset Statistics:")
    for category, count in dataset["dataset_info"]["categories"].items():
        print(f"  • {category.replace('_', ' ').title()}: {count} examples")
    
    print(f"\n🎯 Total Examples: {dataset['dataset_info']['total_examples']}")
    print("🚀 Ready for RAG system integration!")
    
    return dataset

if __name__ == "__main__":
    main()