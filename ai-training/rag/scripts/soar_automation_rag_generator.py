#!/usr/bin/env python3
"""
SOAR Automation RAG Training Data Generator
Creates specialized SOAR playbook and automation examples for Whis
"""

import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict

class SOARAutomationRAGGenerator:
    """Generate SOAR automation training examples"""
    
    def __init__(self):
        self.examples = []
        
    def create_playbook_automation_examples(self) -> List[Dict]:
        """SOAR playbook automation examples"""
        
        examples = [
            {
                "query": "Design automated SOAR playbook for phishing email response with human approval gates",
                "context": "Phishing response requires automated investigation, evidence collection, and containment actions while maintaining human oversight for critical decisions. Playbook should handle email analysis, URL/attachment inspection, user notification, and potential account compromise response.",
                "expected_response": "Phishing SOAR playbook: 1) **Auto-investigation**: Extract URLs/attachments, sandbox analysis, reputation checks, 2) **Evidence collection**: Email headers, recipient list, click tracking, 3) **Human approval**: Block sender/domain decision, 4) **Auto-containment**: Email deletion, user notification, 5) **Escalation**: Account compromise investigation if clicked, 6) **Documentation**: Incident record and IOC updates.",
                "knowledge_source": "SOAR Phishing Response Playbooks",
                "tags": ["soar", "playbook", "phishing", "automation", "approval_gates", "assistant_mode"]
            },
            
            {
                "query": "Create SOAR automation for malware incident response with LimaCharlie EDR integration",
                "context": "Malware incidents require rapid host isolation, evidence preservation, and artifact collection. SOAR automation should integrate with LimaCharlie for endpoint control, coordinate with SIEM for log analysis, and maintain chain of custody for forensic evidence.",
                "expected_response": "Malware SOAR automation: 1) **LimaCharlie isolation**: Network isolation command with approval_required: true, 2) **Evidence preservation**: Memory dump and disk imaging via EDR, 3) **SIEM correlation**: Query for lateral movement indicators, 4) **Artifact collection**: Process tree, network connections, file modifications, 5) **Threat intel**: IOC submission and correlation, 6) **Notification**: Security team and affected user communication.",
                "knowledge_source": "EDR-SOAR Integration Patterns",
                "tags": ["soar", "malware", "limacharlie", "edr_integration", "automation", "forensics"]
            },
            
            {
                "query": "Build SOAR workflow for insider threat detection with behavioral analysis and case management",
                "context": "Insider threat response requires sensitive handling, evidence preservation, and coordinated response with HR and legal teams. Automation should support behavioral analysis correlation, discrete monitoring, and appropriate escalation procedures.",
                "expected_response": "Insider threat SOAR: 1) **Behavioral correlation**: User activity analysis across multiple systems, 2) **Discrete monitoring**: Enhanced logging without user notification, 3) **Evidence preservation**: Audit trail collection and secure storage, 4) **Risk assessment**: Automated scoring with human review, 5) **Escalation coordination**: HR/Legal notification with approval gates, 6) **Case management**: Secure documentation and timeline tracking.",
                "knowledge_source": "Insider Threat Response Procedures",
                "tags": ["soar", "insider_threat", "behavioral_analysis", "case_management", "coordination"]
            }
        ]
        
        return examples
    
    def create_integration_examples(self) -> List[Dict]:
        """SOAR integration and orchestration examples"""
        
        examples = [
            {
                "query": "Orchestrate multi-tool response for advanced persistent threat using SOAR automation",
                "context": "APT response requires coordination across EDR, SIEM, threat intelligence, and network security tools. SOAR orchestration should automate data collection, correlation analysis, and coordinated containment while maintaining human oversight for strategic decisions.",
                "expected_response": "APT SOAR orchestration: 1) **Multi-tool data collection**: EDR telemetry, SIEM logs, network flows, threat intel feeds, 2) **Automated correlation**: Timeline reconstruction and IOC pivoting, 3) **Threat assessment**: Automated scoring with analyst review, 4) **Coordinated containment**: Network segmentation, host isolation, account suspension with approval gates, 5) **Intelligence sharing**: IOC distribution and threat reporting, 6) **Recovery coordination**: System restoration and monitoring enhancement.",
                "knowledge_source": "Advanced Threat Response Orchestration",
                "tags": ["soar", "apt", "orchestration", "multi_tool", "coordination", "containment"]
            },
            
            {
                "query": "Automate cloud security incident response using SOAR with AWS/Azure API integration",
                "context": "Cloud security incidents require rapid resource isolation, identity management, and compliance reporting. SOAR automation should integrate with cloud APIs for resource control, identity management, and audit trail preservation while maintaining regulatory compliance.",
                "expected_response": "Cloud SOAR automation: 1) **Resource isolation**: Automated security group modification and instance quarantine, 2) **Identity management**: Account suspension and MFA enforcement via API, 3) **Audit preservation**: CloudTrail/Activity log collection and secure storage, 4) **Compliance reporting**: Automated incident documentation for regulatory requirements, 5) **Recovery orchestration**: Resource restoration with enhanced monitoring, 6) **Notification**: Stakeholder communication and regulatory reporting.",
                "knowledge_source": "Cloud Security Automation Patterns",
                "tags": ["soar", "cloud_security", "aws", "azure", "api_integration", "compliance"]
            }
        ]
        
        return examples
    
    def create_workflow_examples(self) -> List[Dict]:
        """SOAR workflow and decision logic examples"""
        
        examples = [
            {
                "query": "Design SOAR decision tree for automated triage of security alerts with escalation logic",
                "context": "Alert triage requires automated severity assessment, false positive filtering, and appropriate escalation based on threat indicators and business context. Decision logic should balance automation efficiency with analyst oversight.",
                "expected_response": "SOAR triage decision tree: 1) **Severity assessment**: Automated scoring based on IOC reputation, asset criticality, attack progression, 2) **False positive filtering**: Historical pattern matching and whitelist checking, 3) **Escalation logic**: High severity → immediate analyst, Medium → queue with SLA, Low → automated response, 4) **Context enrichment**: Asset importance, user privilege level, network segment, 5) **Approval gates**: Critical asset impacts require human authorization, 6) **SLA management**: Automated escalation for delayed responses.",
                "knowledge_source": "SOAR Triage and Escalation Patterns",
                "tags": ["soar", "triage", "decision_tree", "escalation", "automation", "sla_management"]
            },
            
            {
                "query": "Create SOAR communication workflow for incident notification and stakeholder updates",
                "context": "Incident communication requires automated stakeholder notification, status updates, and regulatory reporting based on incident severity and impact. Communication should be tailored to audience and maintain appropriate information security.",
                "expected_response": "SOAR communication workflow: 1) **Stakeholder mapping**: Automated notification based on incident type and severity, 2) **Template selection**: Incident-specific communication templates with approval workflows, 3) **Channel coordination**: Email, Slack, SMS based on urgency and recipient, 4) **Status automation**: Regular updates during incident lifecycle, 5) **Regulatory coordination**: Automated compliance reporting for qualifying incidents, 6) **Documentation**: Communication log for incident record.",
                "knowledge_source": "Incident Communication Automation",
                "tags": ["soar", "communication", "notification", "stakeholder", "regulatory", "documentation"]
            }
        ]
        
        return examples
    
    def create_compliance_automation_examples(self) -> List[Dict]:
        """SOAR compliance and reporting automation examples"""
        
        examples = [
            {
                "query": "Automate GDPR breach notification using SOAR with regulatory compliance workflows",
                "context": "GDPR compliance requires automated assessment of personal data impact, 72-hour notification timelines, and documented response procedures. SOAR should handle impact assessment, notification generation, and compliance documentation.",
                "expected_response": "GDPR SOAR automation: 1) **Impact assessment**: Automated PII detection and affected record counting, 2) **Timeline management**: 72-hour notification countdown with automated reminders, 3) **Notification generation**: Templated regulatory filing with approval workflow, 4) **Documentation**: Comprehensive incident record for audit compliance, 5) **Stakeholder notification**: Data controller and affected individual communication, 6) **Recovery tracking**: Remediation progress and effectiveness monitoring.",
                "knowledge_source": "GDPR Compliance Automation",
                "tags": ["soar", "gdpr", "compliance", "breach_notification", "regulatory", "automation"]
            },
            
            {
                "query": "Build SOAR workflow for SOX compliance incident handling with audit trail preservation",
                "context": "SOX compliance incidents involving financial systems require automated evidence preservation, access controls, and audit documentation. SOAR should ensure proper chain of custody and regulatory reporting requirements.",
                "expected_response": "SOX SOAR compliance: 1) **Evidence preservation**: Automated log collection and chain of custody documentation, 2) **Access control**: Emergency financial system isolation with audit logging, 3) **Compliance assessment**: Automated control impact analysis and risk scoring, 4) **Audit documentation**: Templated incident reports with required compliance fields, 5) **Escalation procedures**: Automated notification to compliance and audit teams, 6) **Recovery validation**: Control testing and effectiveness verification.",
                "knowledge_source": "SOX Compliance Incident Response",
                "tags": ["soar", "sox", "compliance", "financial_systems", "audit_trail", "documentation"]
            }
        ]
        
        return examples
    
    def generate_all_soar_examples(self) -> List[Dict]:
        """Generate comprehensive SOAR automation dataset"""
        
        all_examples = []
        all_examples.extend(self.create_playbook_automation_examples())
        all_examples.extend(self.create_integration_examples())
        all_examples.extend(self.create_workflow_examples())
        all_examples.extend(self.create_compliance_automation_examples())
        
        # Add metadata to each example
        for i, example in enumerate(all_examples):
            example.update({
                "id": f"soar_automation_rag_{i+1:03d}",
                "created_date": datetime.now().isoformat(),
                "content_hash": hashlib.md5(example["query"].encode()).hexdigest()[:8],
                "retrieval_type": "soar_automation_learning",
                "automation_type": "orchestration_workflow"
            })
        
        return all_examples
    
    def save_soar_dataset(self, output_file: str = "soar_automation_rag_training_data.json"):
        """Save SOAR automation training dataset"""
        
        examples = self.generate_all_soar_examples()
        
        dataset = {
            "dataset_info": {
                "name": "Whis SOAR Automation RAG Training Data",
                "version": "5.0",
                "created_date": datetime.now().isoformat(),
                "total_examples": len(examples),
                "automation_focus": "orchestration_workflow_compliance",
                "categories": {
                    "playbook_automation": len([e for e in examples if "playbook" in e.get("tags", [])]),
                    "tool_integration": len([e for e in examples if "integration" in e.get("tags", [])]),
                    "workflow_logic": len([e for e in examples if "workflow" in e.get("tags", [])]),
                    "compliance_automation": len([e for e in examples if "compliance" in e.get("tags", [])])
                }
            },
            "examples": examples
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(dataset, f, indent=2, ensure_ascii=False)
        
        print(f"⚙️ Generated {len(examples)} SOAR AUTOMATION RAG training examples")
        print(f"💾 Saved to: {output_file}")
        
        return dataset

def main():
    """Generate SOAR automation RAG training data"""
    print("⚙️ SOAR AUTOMATION RAG TRAINING DATA GENERATOR")
    print("=" * 60)
    
    generator = SOARAutomationRAGGenerator()
    dataset = generator.save_soar_dataset()
    
    print("\\n📊 SOAR Automation Dataset Statistics:")
    for category, count in dataset["dataset_info"]["categories"].items():
        print(f"  • {category.replace('_', ' ').title()}: {count} examples")
    
    print(f"\\n⚙️ Total SOAR Automation Examples: {dataset['dataset_info']['total_examples']}")
    print("🚀 Ready for SOAR automation training!")
    
    return dataset

if __name__ == "__main__":
    main()