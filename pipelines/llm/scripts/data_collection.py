"""
Cybersecurity Knowledge Data Collection Pipeline
Automated collection and curation of training data for Whis LLM
"""

import asyncio
import aiohttp
import json
import os
import re
import pandas as pd
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import hashlib
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TrainingExample:
    """Structured training example for cybersecurity LLM"""
    instruction: str
    input: str
    output: str
    category: str
    source: str
    quality_score: float
    metadata: Dict

class CybersecDataCollector:
    """Collects and curates cybersecurity training data from multiple sources"""
    
    def __init__(self, output_dir: str = "./training_data"):
        self.output_dir = output_dir
        self.session = None
        self.collected_data = {
            "attack_techniques": [],
            "detection_rules": [],
            "incident_response": [],
            "cloud_security": [],
            "vulnerability_analysis": [],
            "compliance_frameworks": [],
            "soar_automation": [],
            "threat_intelligence": []
        }
        
        os.makedirs(output_dir, exist_ok=True)
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def collect_mitre_attack_data(self) -> List[TrainingExample]:
        """Collect MITRE ATT&CK framework data"""
        logger.info("🎯 Collecting MITRE ATT&CK data...")
        
        examples = []
        
        # ATT&CK techniques with detailed explanations
        attack_techniques = {
            "T1110": {
                "name": "Brute Force",
                "description": "Adversaries may use brute force techniques to gain access to accounts",
                "detection": "Monitor for multiple failed authentication attempts",
                "mitigation": "Implement account lockout policies and MFA"
            },
            "T1566": {
                "name": "Phishing",
                "description": "Adversaries may send phishing messages to gain access to victim systems",
                "detection": "Monitor email attachments and suspicious links",
                "mitigation": "User training and email security controls"
            },
            "T1055": {
                "name": "Process Injection",
                "description": "Adversaries may inject code into processes to evade defenses",
                "detection": "Monitor for process creation and memory modification",
                "mitigation": "Application isolation and endpoint protection"
            },
            "T1021": {
                "name": "Remote Services",
                "description": "Adversaries may use valid accounts to log into remote services",
                "detection": "Monitor for unusual logon patterns and geographic anomalies",
                "mitigation": "Network segmentation and privileged access management"
            },
            "T1059": {
                "name": "Command and Scripting Interpreter",
                "description": "Adversaries may abuse command interpreters to execute commands",
                "detection": "Monitor command-line activity and script execution",
                "mitigation": "Application controls and PowerShell logging"
            }
        }
        
        for tid, technique in attack_techniques.items():
            # Create comprehensive training examples for each technique
            examples.append(TrainingExample(
                instruction=f"Explain MITRE ATT&CK technique {tid} ({technique['name']}) and provide comprehensive detection and response guidance.",
                input=f"Security analyst needs to understand {technique['name']} attacks and how to detect them.",
                output=self._generate_attack_explanation(tid, technique),
                category="attack_techniques",
                source="mitre_attack",
                quality_score=0.95,
                metadata={"technique_id": tid, "tactic": "various"}
            ))
            
            # Create detection rule examples
            examples.append(TrainingExample(
                instruction=f"Create detection rules for MITRE ATT&CK technique {tid} ({technique['name']}).",
                input=f"Need to detect {technique['name']} attacks in SIEM environment.",
                output=self._generate_detection_rules(tid, technique),
                category="detection_rules", 
                source="mitre_attack",
                quality_score=0.9,
                metadata={"technique_id": tid, "rule_type": "siem"}
            ))
        
        logger.info(f"✅ Generated {len(examples)} MITRE ATT&CK examples")
        return examples
    
    def _generate_attack_explanation(self, tid: str, technique: Dict) -> str:
        """Generate comprehensive ATT&CK technique explanation"""
        return f"""**MITRE ATT&CK {tid}: {technique['name']}**

**Description:**
{technique['description']}

**Detection Strategy:**
{technique['detection']}

**Key Indicators:**
- Unusual process behavior
- Suspicious network connections
- Anomalous authentication patterns
- Unexpected file modifications

**Response Actions:**
1. **Immediate**: Isolate affected systems
2. **Investigation**: Analyze attack timeline and scope
3. **Containment**: Block malicious IPs and processes
4. **Recovery**: Restore from clean backups if needed

**Mitigation:**
{technique['mitigation']}

**Hunting Queries:**
```spl
index=security technique_id="{tid}"
| stats count by src_ip, dest_host, process_name
| where count > threshold
```

**References:**
- MITRE ATT&CK: https://attack.mitre.org/techniques/{tid}/
- NIST SP 800-53 controls
- CIS Critical Security Controls"""

    def _generate_detection_rules(self, tid: str, technique: Dict) -> str:
        """Generate detection rules for ATT&CK technique"""
        return f"""**Detection Rules for {tid}: {technique['name']}**

**Splunk Detection:**
```spl
index=security sourcetype=WinEventLog:Security
| eval technique_id="{tid}"
| search EventCode=4624 OR EventCode=4625
| stats count by src_ip, user, technique_id
| where count > 5
| eval severity=case(count > 20, "High", count > 10, "Medium", 1=1, "Low")
```

**LimaCharlie D&R Rule:**
```yaml
detect:
  event: NEW_PROCESS
  op: and
  rules:
    - op: contains
      path: event/COMMAND_LINE
      value: suspicious_pattern
      case_sensitive: false

respond:
  - action: report
    name: {tid.lower()}_detection
  - action: isolation
    duration: 3600
    reason: Potential {technique['name']} detected
```

**Sigma Rule:**
```yaml
title: {technique['name']} Detection
id: {hashlib.md5(tid.encode()).hexdigest()[:8]}-{hashlib.md5(technique['name'].encode()).hexdigest()[:4]}-4{hashlib.md5('sigma'.encode()).hexdigest()[:3]}-{hashlib.md5('rule'.encode()).hexdigest()[:4]}-{hashlib.md5('whis'.encode()).hexdigest()[:12]}
status: experimental
description: Detects potential {technique['name']} activity
logsource:
  category: process_creation
  product: windows
detection:
  selection:
    Image|endswith: '.exe'
    CommandLine|contains: 'suspicious'
  condition: selection
falsepositives:
  - Legitimate administrative activity
level: medium
tags:
  - attack.{tid.lower()}
```

**Tuning Guidance:**
- Adjust thresholds based on environment baseline
- Whitelist known legitimate processes
- Correlate with threat intelligence feeds"""

    async def collect_cloud_security_data(self) -> List[TrainingExample]:
        """Collect cloud security and CKS/CCSP knowledge"""
        logger.info("☁️ Collecting cloud security data...")
        
        examples = []
        
        # Kubernetes Security (CKS)
        k8s_topics = {
            "pod_security_standards": {
                "description": "Pod Security Standards enforce security policies",
                "example": "Implement restricted PSS to prevent privileged containers"
            },
            "network_policies": {
                "description": "Control network traffic between pods", 
                "example": "Create deny-all default policy with explicit allow rules"
            },
            "rbac": {
                "description": "Role-Based Access Control for Kubernetes resources",
                "example": "Implement least privilege access with specific role bindings"
            },
            "secrets_management": {
                "description": "Secure handling of sensitive data in Kubernetes",
                "example": "Use external secret managers and encryption at rest"
            },
            "runtime_security": {
                "description": "Monitor and protect running containers",
                "example": "Deploy Falco for runtime threat detection"
            }
        }
        
        for topic, info in k8s_topics.items():
            examples.append(TrainingExample(
                instruction=f"Explain Kubernetes {topic.replace('_', ' ')} security best practices for CKS certification.",
                input=f"DevSecOps team needs to implement {info['description'].lower()}.",
                output=self._generate_k8s_security_guidance(topic, info),
                category="cloud_security",
                source="cks_knowledge",
                quality_score=0.92,
                metadata={"certification": "CKS", "topic": topic}
            ))
        
        # Cloud Security (CCSP)
        cloud_domains = {
            "data_classification": "Identify and classify data based on sensitivity",
            "identity_access_management": "Implement strong IAM controls in cloud",
            "encryption": "Protect data in transit and at rest",
            "security_monitoring": "Continuous monitoring of cloud environments",
            "incident_response": "Cloud-specific incident response procedures"
        }
        
        for domain, description in cloud_domains.items():
            examples.append(TrainingExample(
                instruction=f"Explain {domain.replace('_', ' ')} best practices for CCSP certification.",
                input=f"Cloud security team needs guidance on {description.lower()}.",
                output=self._generate_ccsp_guidance(domain, description),
                category="cloud_security",
                source="ccsp_knowledge",
                quality_score=0.9,
                metadata={"certification": "CCSP", "domain": domain}
            ))
        
        logger.info(f"✅ Generated {len(examples)} cloud security examples")
        return examples
    
    def _generate_k8s_security_guidance(self, topic: str, info: Dict) -> str:
        """Generate Kubernetes security guidance"""
        configs = {
            "pod_security_standards": """**Kubernetes Pod Security Standards (CKS)**

**Restricted Profile Configuration:**
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: secure-namespace
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
spec: {}
```

**Secure Pod Configuration:**
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: secure-pod
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    runAsGroup: 1000
    fsGroup: 1000
    seccompProfile:
      type: RuntimeDefault
  containers:
  - name: app
    image: nginx:alpine
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      capabilities:
        drop:
        - ALL
    resources:
      limits:
        memory: "256Mi"
        cpu: "200m"
```

**Implementation Steps:**
1. Enable Pod Security admission controller
2. Configure namespace labels for enforcement
3. Test policies in warn/audit mode first
4. Gradually enforce across environments""",

            "network_policies": """**Kubernetes Network Policies (CKS)**

**Default Deny-All Policy:**
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: production
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
```

**Selective Allow Policy:**
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: web-to-api
spec:
  podSelector:
    matchLabels:
      app: api
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: web
    ports:
    - protocol: TCP
      port: 8080
```

**Best Practices:**
- Implement zero-trust networking
- Use label selectors for granular control
- Test policies in non-production first
- Monitor network flows for compliance"""
        }
        
        return configs.get(topic, f"**{topic.replace('_', ' ').title()} Security**\n\n{info['description']}\n\nExample: {info['example']}")
    
    def _generate_ccsp_guidance(self, domain: str, description: str) -> str:
        """Generate CCSP certification guidance"""
        return f"""**CCSP Domain: {domain.replace('_', ' ').title()}**

**Overview:**
{description}

**Key Concepts:**
- Shared responsibility model
- Cloud service models (IaaS, PaaS, SaaS)
- Compliance and regulatory requirements
- Risk management frameworks

**Implementation Guidelines:**
1. **Assessment**: Evaluate current cloud security posture
2. **Design**: Implement security controls based on requirements
3. **Deploy**: Roll out security measures with proper testing
4. **Monitor**: Continuous monitoring and improvement

**Best Practices:**
- Follow cloud provider security recommendations
- Implement defense in depth strategies
- Regular security assessments and audits
- Staff training and awareness programs

**Common Challenges:**
- Multi-cloud complexity
- Shared responsibility confusion
- Compliance across jurisdictions
- Skills and resource gaps"""

    async def collect_soar_data(self) -> List[TrainingExample]:
        """Collect SOAR automation and playbook data"""
        logger.info("🤖 Collecting SOAR automation data...")
        
        examples = []
        
        # SOAR playbook examples
        playbooks = {
            "phishing_investigation": {
                "trigger": "User reports suspicious email",
                "steps": ["Email analysis", "URL/attachment scanning", "User impact assessment", "Response actions"]
            },
            "malware_containment": {
                "trigger": "Endpoint detection alert",
                "steps": ["Isolate endpoint", "Collect forensics", "Analyze malware", "Remediate systems"]
            },
            "data_breach_response": {
                "trigger": "Data exfiltration detected",
                "steps": ["Assess scope", "Contain breach", "Notify stakeholders", "Forensic analysis"]
            }
        }
        
        for playbook_name, details in playbooks.items():
            examples.append(TrainingExample(
                instruction=f"Create a comprehensive SOAR playbook for {playbook_name.replace('_', ' ')}.",
                input=f"Security team needs automated response for: {details['trigger']}",
                output=self._generate_soar_playbook(playbook_name, details),
                category="soar_automation",
                source="soar_playbooks",
                quality_score=0.93,
                metadata={"playbook_type": playbook_name, "automation_level": "high"}
            ))
        
        logger.info(f"✅ Generated {len(examples)} SOAR examples")
        return examples
    
    def _generate_soar_playbook(self, name: str, details: Dict) -> str:
        """Generate SOAR playbook documentation"""
        return f"""**SOAR Playbook: {name.replace('_', ' ').title()}**

**Trigger Condition:**
{details['trigger']}

**Playbook Steps:**
{chr(10).join(f"{i+1}. {step}" for i, step in enumerate(details['steps']))}

**Automation Workflow:**
```python
# SOAR Playbook Implementation
class {name.title().replace('_', '')}Playbook:
    def __init__(self):
        self.name = "{name}"
        self.severity_threshold = "medium"
        self.auto_approve = False
    
    async def execute(self, incident):
        # Step 1: Initial assessment
        assessment = await self.assess_incident(incident)
        
        # Step 2: Automated actions
        if assessment.confidence > 0.8:
            await self.execute_immediate_actions(incident)
        
        # Step 3: Human approval for critical actions
        if assessment.requires_approval:
            approval = await self.request_approval(incident, assessment)
            if approval.approved:
                await self.execute_approved_actions(incident, approval.actions)
        
        # Step 4: Documentation and learning
        await self.document_incident(incident, assessment)
        return assessment
    
    async def assess_incident(self, incident):
        # Implement assessment logic
        pass
```

**Integration Points:**
- SIEM: Receive alerts and enrich with context
- EDR: Execute containment actions
- Threat Intelligence: Correlate with known threats
- Communication: Notify stakeholders

**Approval Gates:**
- High-impact actions require human approval
- Low-risk actions can be auto-executed
- All actions are logged and auditable

**Success Metrics:**
- Mean time to detection (MTTD)
- Mean time to response (MTTR)
- False positive reduction
- Analyst productivity improvement"""

    async def collect_all_data(self) -> Dict[str, List[TrainingExample]]:
        """Collect data from all sources"""
        logger.info("📊 Starting comprehensive data collection...")
        
        # Collect from all sources
        attack_data = await self.collect_mitre_attack_data()
        cloud_data = await self.collect_cloud_security_data()
        soar_data = await self.collect_soar_data()
        
        # Organize by category
        all_examples = attack_data + cloud_data + soar_data
        
        for example in all_examples:
            self.collected_data[example.category].append(example)
        
        # Save collected data
        await self.save_training_data()
        
        logger.info(f"✅ Collection complete: {len(all_examples)} total examples")
        return self.collected_data
    
    async def save_training_data(self):
        """Save collected data to files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save as JSON for processing
        json_file = f"{self.output_dir}/cybersec_training_data_{timestamp}.json"
        
        serializable_data = {}
        for category, examples in self.collected_data.items():
            serializable_data[category] = [
                {
                    "instruction": ex.instruction,
                    "input": ex.input,
                    "output": ex.output,
                    "category": ex.category,
                    "source": ex.source,
                    "quality_score": ex.quality_score,
                    "metadata": ex.metadata
                }
                for ex in examples
            ]
        
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(serializable_data, f, indent=2, ensure_ascii=False)
        
        # Save as CSV for analysis
        csv_file = f"{self.output_dir}/cybersec_training_data_{timestamp}.csv"
        
        rows = []
        for category, examples in self.collected_data.items():
            for ex in examples:
                rows.append({
                    "instruction": ex.instruction,
                    "input": ex.input,
                    "output": ex.output,
                    "category": ex.category,
                    "source": ex.source,
                    "quality_score": ex.quality_score,
                    "word_count": len(ex.output.split()),
                    "has_code": "```" in ex.output
                })
        
        df = pd.DataFrame(rows)
        df.to_csv(csv_file, index=False)
        
        # Generate summary statistics
        summary = {
            "collection_date": datetime.now().isoformat(),
            "total_examples": len(rows),
            "categories": {cat: len(examples) for cat, examples in self.collected_data.items()},
            "avg_quality_score": float(df["quality_score"].mean()),
            "avg_word_count": float(df["word_count"].mean()),
            "examples_with_code": int(df["has_code"].sum())
        }
        
        summary_file = f"{self.output_dir}/collection_summary_{timestamp}.json"
        with open(summary_file, "w") as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"💾 Data saved:")
        logger.info(f"  📁 JSON: {json_file}")
        logger.info(f"  📊 CSV: {csv_file}")
        logger.info(f"  📈 Summary: {summary_file}")

async def main():
    """Main data collection pipeline"""
    async with CybersecDataCollector() as collector:
        data = await collector.collect_all_data()
        
        print("\n🎯 Data Collection Summary:")
        print("=" * 50)
        total = 0
        for category, examples in data.items():
            count = len(examples)
            total += count
            print(f"  {category.replace('_', ' ').title()}: {count} examples")
        
        print(f"\n📊 Total Examples: {total}")
        print("✅ Data collection complete!")

if __name__ == "__main__":
    asyncio.run(main())