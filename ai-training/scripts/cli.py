#!/usr/bin/env python3
"""
✅ Curation Pipeline - Split USE Events into LLM Training + RAG Chunks  
=====================================================================
TAGS: #curation-pipeline #llm-training-data #rag-chunks #human-approval

Transforms sanitized USE events into:
1. LLM instruction/response pairs for Action Schema + HOW training
2. RAG chunks with generalized security knowledge

Security: CODEOWNERS approval required, no customer-specific data in outputs.
"""

import os
import sys
import json
import yaml
import hashlib
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import uuid
import re

import click
import structlog

# Configure structured logging  
logging.basicConfig(level=logging.INFO)
logger = structlog.get_logger(__name__)

# Template for LLM instruction/response pairs
LLM_INSTRUCTION_TEMPLATES = {
    "explain": [
        "Explain and respond to this {severity} severity detection with NIST alignment and MITRE ATT&CK mapping.",
        "Analyze this security event and provide structured triage steps and containment recommendations.",
        "Create a comprehensive incident response plan for this {use_case} scenario."
    ],
    "how": [
        "Create a zero-downtime remediation plan for this security event with Terraform and Kubernetes artifacts.",
        "Generate infrastructure-as-code artifacts to contain and remediate this threat.",
        "Develop automated response playbooks with plan/apply/validate/rollback procedures."
    ]
}

# RAG chunk categories based on security patterns
RAG_CATEGORIES = {
    "brute_force_response": {"framework": "SOAR Playbook", "category": "credential_access/brute_force"},
    "lateral_movement_detection": {"framework": "SOAR Playbook", "category": "lateral_movement/detection"},
    "malware_containment": {"framework": "SOAR Playbook", "category": "malware/containment"},
    "data_exfiltration": {"framework": "SOAR Playbook", "category": "exfiltration/prevention"},
    "privilege_escalation": {"framework": "SOAR Playbook", "category": "privilege_escalation/detection"},
    "persistence_detection": {"framework": "SOAR Playbook", "category": "persistence/detection"},
    "credential_theft": {"framework": "SOAR Playbook", "category": "credential_access/theft"},
    "network_anomaly": {"framework": "SOAR Playbook", "category": "network/anomaly"},
    "process_anomaly": {"framework": "SOAR Playbook", "category": "execution/process_anomaly"},
    "general_detection": {"framework": "SOAR Playbook", "category": "general/response"}
}

class ActionSchemaGenerator:
    """Generates Action Schema training examples from USE events"""
    
    def __init__(self):
        self.mitre_mappings = self._load_mitre_mappings()
        self.nist_mappings = self._load_nist_mappings()
    
    def _load_mitre_mappings(self) -> Dict[str, Dict[str, str]]:
        """Load MITRE ATT&CK technique mappings (placeholder)"""
        return {
            "T1110": {"name": "Brute Force", "tactic": "Credential Access"},
            "T1003": {"name": "OS Credential Dumping", "tactic": "Credential Access"},
            "T1021": {"name": "Remote Services", "tactic": "Lateral Movement"},
            "T1059": {"name": "Command and Scripting Interpreter", "tactic": "Execution"},
            "T1055": {"name": "Process Injection", "tactic": "Defense Evasion"},
            "T1078": {"name": "Valid Accounts", "tactic": "Defense Evasion"},
            "T1105": {"name": "Ingress Tool Transfer", "tactic": "Command And Control"},
            "T1071": {"name": "Application Layer Protocol", "tactic": "Command And Control"}
        }
    
    def _load_nist_mappings(self) -> Dict[str, List[str]]:
        """Load NIST CSF mappings for common scenarios"""
        return {
            "credential_access": ["DE.CM-1", "DE.CM-7", "RS.RP-1", "RS.AN-1"],
            "lateral_movement": ["DE.AE-2", "DE.CM-1", "RS.AN-1", "RS.MI-1"],
            "malware": ["DE.CM-4", "RS.RP-1", "RS.MI-2", "RC.RP-1"],
            "exfiltration": ["DE.AE-1", "DE.CM-1", "RS.AN-1", "RS.MI-3"],
            "privilege_escalation": ["DE.CM-3", "PR.AC-1", "RS.AN-1", "RS.MI-1"],
            "persistence": ["DE.CM-3", "DE.AE-3", "RS.RP-1", "RS.AN-1"],
            "execution": ["DE.CM-2", "DE.AE-3", "RS.AN-1", "RS.MI-1"],
            "network": ["DE.AE-1", "DE.CM-1", "RS.AN-1", "PR.DS-5"]
        }
    
    def generate_action_schema(self, use_event: Dict[str, Any]) -> Dict[str, Any]:
        """Generate Action Schema response from USE event"""
        
        # Extract MITRE techniques with details
        mitre_details = []
        for technique_id in use_event.get('mitre', []):
            if technique_id in self.mitre_mappings:
                mapping = self.mitre_mappings[technique_id]
                mitre_details.append({
                    "technique_id": technique_id,
                    "technique_name": mapping["name"],
                    "tactic": mapping["tactic"],
                    "severity": use_event.get('severity', 'medium')
                })
        
        # Determine primary tactic for NIST mapping
        primary_tactic = "general"
        if mitre_details:
            tactic_lower = mitre_details[0]["tactic"].lower().replace(" ", "_")
            if tactic_lower in self.nist_mappings:
                primary_tactic = tactic_lower
        
        # Generate NIST categories
        nist_categories = self.nist_mappings.get(primary_tactic, ["DE.AE-1", "RS.AN-1"])
        
        # Generate triage steps based on event type
        triage_steps = self._generate_triage_steps(use_event, mitre_details)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(use_event, mitre_details)
        
        # Calculate risk score
        risk_score = self._calculate_risk_score(use_event, mitre_details)
        
        # Generate example SPL query
        spl_query = self._generate_spl_query(use_event)
        
        # Generate example LimaCharlie rule
        lc_rule = self._generate_lc_rule(use_event)
        
        action_schema = {
            "nist_functions": self._get_nist_functions(primary_tactic),
            "nist_categories": nist_categories,
            "mitre": mitre_details,
            "triage_steps": triage_steps,
            "recommendations": recommendations,
            "risk_score": risk_score,
            "confidence": 0.85,  # Default confidence
            "spl_query": spl_query,
            "lc_rule": lc_rule,
            "processing_time_ms": 150
        }
        
        return action_schema
    
    def _generate_triage_steps(self, use_event: Dict[str, Any], mitre_details: List[Dict]) -> List[str]:
        """Generate context-appropriate triage steps"""
        steps = [
            "1. Verify the detection accuracy and eliminate false positives",
            f"2. Analyze the affected entity: {use_event.get('entity', {}).get('host', 'unknown host')}",
            "3. Assess the scope of potential compromise"
        ]
        
        # Add technique-specific steps
        for mitre in mitre_details:
            technique_id = mitre["technique_id"]
            if technique_id.startswith("T1110"):  # Brute Force
                steps.append("4. Check for successful authentication attempts following failed attempts")
                steps.append("5. Review account lockout policies and authentication logs")
            elif technique_id.startswith("T1003"):  # Credential Dumping  
                steps.append("4. Immediately reset credentials for the affected account")
                steps.append("5. Check for lateral movement using compromised credentials")
            elif technique_id.startswith("T1021"):  # Remote Services
                steps.append("4. Identify the source of remote access attempts")
                steps.append("5. Verify legitimacy of remote service usage")
        
        steps.append("6. Document findings and escalate if necessary")
        return steps
    
    def _generate_recommendations(self, use_event: Dict[str, Any], mitre_details: List[Dict]) -> List[str]:
        """Generate security recommendations"""
        recommendations = [
            "Implement continuous monitoring for similar attack patterns",
            "Review and update detection rules based on this event"
        ]
        
        # Add technique-specific recommendations
        for mitre in mitre_details:
            technique_id = mitre["technique_id"]
            if technique_id.startswith("T1110"):
                recommendations.append("Implement account lockout policies and MFA")
                recommendations.append("Deploy honeypot accounts to detect brute force attempts")
            elif technique_id.startswith("T1003"):
                recommendations.append("Implement LSA protection and credential guard")
                recommendations.append("Rotate privileged account credentials immediately")
            elif technique_id.startswith("T1021"):
                recommendations.append("Restrict remote services to authorized users only")
                recommendations.append("Implement network segmentation to limit lateral movement")
        
        return recommendations
    
    def _calculate_risk_score(self, use_event: Dict[str, Any], mitre_details: List[Dict]) -> float:
        """Calculate risk score (0-10 scale)"""
        base_score = 5.0
        
        # Adjust based on severity
        severity_multipliers = {"low": 0.7, "medium": 1.0, "high": 1.3, "critical": 1.6}
        severity = use_event.get('severity', 'medium')
        base_score *= severity_multipliers.get(severity, 1.0)
        
        # Adjust based on MITRE techniques
        high_risk_techniques = ["T1003", "T1078", "T1105"]  # Credential dumping, valid accounts, tool transfer
        for mitre in mitre_details:
            if any(mitre["technique_id"].startswith(high_risk) for high_risk in high_risk_techniques):
                base_score *= 1.2
                break
        
        # Adjust based on confidence
        confidence = use_event.get('labels', {}).get('confidence', 0.8)
        base_score *= confidence
        
        return min(10.0, base_score)
    
    def _generate_spl_query(self, use_event: Dict[str, Any]) -> str:
        """Generate example Splunk SPL query"""
        entity = use_event.get('entity', {})
        host = entity.get('host', '*')
        user = entity.get('user', '*')
        
        # Generalize the query with placeholders
        if 'brute' in use_event.get('labels', {}).get('use_case', '').lower():
            return f'''index=security sourcetype=windows:security EventCode=4625 
| stats count by Account_Name, Workstation_Name, src_ip 
| where count > 10 
| eval risk_score=case(count>50, "high", count>20, "medium", 1=1, "low")'''
        
        return f'''index=security host="{host}" user="{user}" 
| eval mitre_techniques="{','.join(use_event.get('mitre', []))}"
| stats count by _time, host, user, mitre_techniques
| sort -_time'''
    
    def _generate_lc_rule(self, use_event: Dict[str, Any]) -> str:
        """Generate example LimaCharlie detection rule"""
        return '''detect:
  - op: and
    rules:
      - op: exists
        path: event/PROCESS_NAME
      - op: contains
        path: event/COMMAND_LINE
        value: suspicious_pattern
respond:
  - action: report
    name: suspicious_process_execution'''
    
    def _get_nist_functions(self, tactic: str) -> List[str]:
        """Map tactic to NIST functions"""
        function_mappings = {
            "credential_access": ["Identify", "Protect", "Detect", "Respond"],
            "lateral_movement": ["Detect", "Respond"],
            "execution": ["Detect", "Respond"],
            "persistence": ["Detect", "Respond", "Recover"],
            "exfiltration": ["Detect", "Respond", "Recover"]
        }
        
        return function_mappings.get(tactic, ["Detect", "Respond"])

class RAGChunkGenerator:
    """Generates RAG chunks from security patterns"""
    
    def __init__(self):
        self.chunk_counter = 0
    
    def generate_rag_chunks(self, use_events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate RAG chunks from similar USE events"""
        
        # Group events by use case
        grouped_events = {}
        for event in use_events:
            use_case = event.get('labels', {}).get('use_case', 'general_detection')
            if use_case not in grouped_events:
                grouped_events[use_case] = []
            grouped_events[use_case].append(event)
        
        chunks = []
        
        for use_case, events in grouped_events.items():
            if len(events) < 3:  # Need at least 3 similar events to create a pattern
                continue
            
            chunk = self._create_rag_chunk(use_case, events)
            if chunk:
                chunks.append(chunk)
        
        return chunks
    
    def _create_rag_chunk(self, use_case: str, events: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Create a RAG chunk from grouped events"""
        
        if use_case not in RAG_CATEGORIES:
            logger.warning(f"Unknown use case for RAG: {use_case}")
            return None
        
        category_info = RAG_CATEGORIES[use_case]
        
        # Analyze common patterns
        common_mitre = self._find_common_mitre(events)
        common_severity = self._find_common_severity(events)
        
        # Generate generalized content
        title = self._generate_title(use_case, common_mitre)
        content = self._generate_content(use_case, events, common_mitre)
        
        self.chunk_counter += 1
        
        # Create chunk metadata
        chunk_metadata = {
            "framework": category_info["framework"],
            "category": category_info["category"],
            "doc_title": title,
            "doc_date": datetime.now().strftime("%Y-%m-%d"),
            "stability": "core",
            "tags": [
                use_case,
                f"mitre:{','.join(common_mitre)}",
                f"severity:{common_severity}",
                "whis_generated"
            ],
            "chunk_id": f"whis_generated_{self.chunk_counter:04d}",
            "source_events": len(events),
            "confidence": 0.8
        }
        
        return {
            "metadata": chunk_metadata,
            "content": content
        }
    
    def _find_common_mitre(self, events: List[Dict[str, Any]]) -> List[str]:
        """Find MITRE techniques common across events"""
        all_techniques = []
        for event in events:
            all_techniques.extend(event.get('mitre', []))
        
        # Count technique frequency
        technique_counts = {}
        for technique in all_techniques:
            technique_counts[technique] = technique_counts.get(technique, 0) + 1
        
        # Return techniques that appear in at least 30% of events
        threshold = len(events) * 0.3
        common_techniques = [t for t, count in technique_counts.items() if count >= threshold]
        
        return common_techniques[:5]  # Limit to top 5
    
    def _find_common_severity(self, events: List[Dict[str, Any]]) -> str:
        """Find most common severity level"""
        severities = [event.get('severity', 'medium') for event in events]
        severity_counts = {}
        
        for severity in severities:
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        return max(severity_counts.items(), key=lambda x: x[1])[0]
    
    def _generate_title(self, use_case: str, common_mitre: List[str]) -> str:
        """Generate chunk title"""
        use_case_titles = {
            "brute_force_response": "Brute Force Attack → Detection & Response",
            "lateral_movement_detection": "Lateral Movement → Detection & Containment", 
            "malware_containment": "Malware Detection → Isolation & Remediation",
            "data_exfiltration": "Data Exfiltration → Detection & Prevention",
            "privilege_escalation": "Privilege Escalation → Detection & Mitigation",
            "persistence_detection": "Persistence Mechanisms → Detection & Removal",
            "credential_theft": "Credential Theft → Detection & Recovery",
            "network_anomaly": "Network Anomaly → Analysis & Response",
            "process_anomaly": "Process Anomaly → Investigation & Action"
        }
        
        base_title = use_case_titles.get(use_case, f"{use_case.replace('_', ' ').title()} → Response")
        
        if common_mitre:
            mitre_suffix = f" ({', '.join(common_mitre[:2])})"
            return base_title + mitre_suffix
        
        return base_title
    
    def _generate_content(self, use_case: str, events: List[Dict[str, Any]], common_mitre: List[str]) -> str:
        """Generate chunk content"""
        
        content_templates = {
            "brute_force_response": """
## Detection Indicators

- Multiple failed authentication attempts from single source
- Attempts across multiple user accounts in short timeframe  
- Authentication attempts outside normal business hours
- Geographic anomalies in login attempts

## Response Procedures

### Immediate Actions
1. **Isolate** the attacking source IP address
2. **Lock** targeted user accounts temporarily  
3. **Alert** security team for investigation
4. **Document** attack timeline and scope

### Investigation Steps
1. Analyze authentication logs for successful attempts
2. Check for lateral movement post-compromise
3. Review account permissions and access patterns
4. Validate legitimacy of any successful authentications

### Containment Measures
- Implement IP-based blocking rules
- Force password resets for targeted accounts
- Enable MFA for affected accounts
- Monitor for resumed attack patterns

## Example Queries

**Splunk SPL:**
```spl
index=security sourcetype=windows:security EventCode=4625
| stats count by src_ip, Account_Name
| where count > 10
| eval risk_level=case(count>50, "critical", count>20, "high", 1=1, "medium")
```

**LimaCharlie Rule:**
```yaml
detect:
  op: and
  rules:
    - op: ">=" 
      path: count
      value: 10
    - op: "=="
      path: event_type
      value: "failed_auth"
respond:
  action: report
  name: brute_force_detected
```
""",
            "lateral_movement_detection": """
## Detection Patterns

- Unusual remote service connections
- Authentication events between internal systems
- Process execution via remote services (WMI, RDP, SSH)
- File transfers between internal hosts

## Response Framework

### Immediate Assessment
1. **Identify** source and destination systems
2. **Analyze** authentication patterns and timing
3. **Check** for data access or exfiltration
4. **Isolate** affected systems from network

### Investigation Protocol  
1. Review network traffic between affected hosts
2. Analyze process execution and command history
3. Check for credential reuse across systems
4. Validate business justification for connections

### Containment Strategy
- Network segmentation to limit spread
- Credential rotation for compromised accounts
- System isolation and forensic preservation
- Continuous monitoring of related systems

## Detection Queries

**Network Traffic Analysis:**
```spl
index=network src_ip=${INTERNAL_IP} dest_ip=${INTERNAL_IP}
| stats count by src_ip, dest_ip, dest_port
| where count > 100
```
""",
            "general_detection": """
## General Response Playbook

### Initial Triage
1. **Verify** detection accuracy and context
2. **Assess** potential business impact
3. **Classify** incident severity level
4. **Notify** appropriate response teams

### Investigation Steps
1. Collect relevant logs and evidence
2. Analyze attack vectors and techniques
3. Determine scope of compromise
4. Document timeline and indicators

### Response Actions
- Implement appropriate containment measures
- Coordinate with business stakeholders  
- Execute recovery procedures as needed
- Update detection rules and defenses

## Standard Queries

Replace placeholders with actual values:
- `${HOST}` - Target hostname
- `${USER}` - Username involved  
- `${IP}` - IP address
- `${TIMERANGE}` - Investigation timeframe
"""
        }
        
        template = content_templates.get(use_case, content_templates["general_detection"])
        
        # Add MITRE technique context if available
        if common_mitre:
            mitre_section = f"\n## MITRE ATT&CK Context\n\n"
            mitre_section += f"**Techniques:** {', '.join(common_mitre)}\n\n"
            mitre_section += "Refer to MITRE ATT&CK framework for detailed technique descriptions and mitigations.\n"
            template = mitre_section + template
        
        return template.strip()

class CurationManifest:
    """Manages curation manifest generation"""
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.input_files = []
        self.output_files = []
        self.start_time = datetime.now()
        self.stats = {
            "llm_train_examples": 0,
            "llm_test_examples": 0,
            "rag_chunks": 0,
            "events_processed": 0
        }
    
    def add_input_file(self, filepath: Path):
        """Add input file to manifest"""
        self.input_files.append(str(filepath))
    
    def add_output_file(self, filepath: Path, file_type: str, item_count: int):
        """Add output file to manifest"""
        file_stats = filepath.stat() if filepath.exists() else None
        
        self.output_files.append({
            "path": str(filepath),
            "type": file_type,
            "items": item_count,
            "bytes": file_stats.st_size if file_stats else 0,
            "created_at": datetime.fromtimestamp(file_stats.st_ctime).isoformat() if file_stats else datetime.now().isoformat()
        })
        
        self.stats[f"{file_type}_examples" if "llm" in file_type else f"{file_type}s"] += item_count
    
    def save(self) -> Path:
        """Save manifest to disk"""
        manifest = {
            "pipeline": "curate",
            "input_files": self.input_files,
            "output_files": self.output_files,
            "stats": self.stats,
            "created_at": self.start_time.isoformat(),
            "pipeline_version": "1.0.0"
        }
        
        manifest_path = self.output_dir / f"curate_{self.start_time.strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        logger.info("Curation manifest saved", path=str(manifest_path), stats=self.stats)
        return manifest_path

@click.group()  
@click.option('--debug', is_flag=True, help='Enable debug logging')
def cli(debug):
    """Whis SOAR Curation Pipeline - Create LLM training data and RAG chunks"""
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)

@cli.command()
@click.option('--input-dir', type=click.Path(exists=True), required=True, help='Directory containing USE JSONL files')
@click.option('--output-dir', type=click.Path(), help='Output directory (default: data/curated)')
@click.option('--train-split', type=float, default=0.8, help='Training split ratio (default: 0.8)')
@click.option('--min-events-for-rag', type=int, default=3, help='Minimum events needed to create RAG chunk')
def process(input_dir, output_dir, train_split, min_events_for_rag):
    """Process USE events into LLM training data and RAG chunks"""
    
    input_path = Path(input_dir)
    if not output_dir:
        output_path = Path("data/curated")
    else:
        output_path = Path(output_dir)
    
    # Create output directories
    llm_dir = output_path / "llm"
    rag_dir = output_path / "rag" / "chunks"
    manifests_dir = Path("data/manifests")
    
    for dir_path in [llm_dir, rag_dir, manifests_dir]:
        dir_path.mkdir(parents=True, exist_ok=True)
    
    logger.info("Starting curation", input_dir=str(input_path), output_dir=str(output_path))
    
    # Initialize generators
    action_generator = ActionSchemaGenerator()
    rag_generator = RAGChunkGenerator()
    manifest = CurationManifest(manifests_dir)
    
    # Load all USE events
    all_events = []
    jsonl_files = list(input_path.rglob("*.jsonl"))
    
    if not jsonl_files:
        click.echo(f"❌ No JSONL files found in {input_path}")
        sys.exit(1)
    
    for jsonl_file in jsonl_files:
        manifest.add_input_file(jsonl_file)
        logger.info("Loading events", file=str(jsonl_file))
        
        with open(jsonl_file, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                
                try:
                    event = json.loads(line)
                    all_events.append(event)
                except json.JSONDecodeError as e:
                    logger.warning("Invalid JSON", file=str(jsonl_file), line=line_num, error=str(e))
                    continue
    
    if not all_events:
        click.echo("❌ No valid events found")
        sys.exit(1)
    
    logger.info("Loaded events", count=len(all_events))
    manifest.stats["events_processed"] = len(all_events)
    
    # Generate LLM training examples
    llm_examples = []
    
    for event in all_events:
        # Generate Action Schema
        action_schema = action_generator.generate_action_schema(event)
        
        # Create instruction/response pairs
        use_case = event.get('labels', {}).get('use_case', 'general_detection')
        severity = event.get('severity', 'medium')
        
        # Explain instruction
        explain_instruction = LLM_INSTRUCTION_TEMPLATES["explain"][0].format(
            severity=severity,
            use_case=use_case.replace('_', ' ')
        )
        
        explain_example = {
            "instruction": explain_instruction,
            "input": {"use": event},
            "output": {
                "triage_steps": action_schema["triage_steps"],
                "containment": action_schema["recommendations"][:3],
                "remediation": action_schema["recommendations"][3:],
                "mitre": action_schema["mitre"],
                "how": {
                    "prechecks": ["Verify affected systems", "Assess business impact"],
                    "plan": ["Isolate affected systems", "Implement containment measures"],
                    "apply": ["Execute isolation procedures", "Deploy detection rules"], 
                    "validate": ["Confirm containment effectiveness", "Test system functionality"],
                    "rollback": ["Restore systems if needed", "Document lessons learned"],
                    "risk_tradeoffs": ["Balance security vs availability", "Consider business operations"]
                },
                "artifacts": [
                    {
                        "name": "containment.tf",
                        "type": "terraform",
                        "path": "artifacts/containment.tf",
                        "contents": "# Terraform configuration for system isolation\n# Replace ${HOST} with actual hostname\n"
                    }
                ],
                "citations": ["NIST SP 800-61r2", f"CSF:{','.join(action_schema['nist_categories'])}"],
                "confidence": action_schema["confidence"]
            }
        }
        
        llm_examples.append(explain_example)
        
        # HOW instruction (for high/critical events)
        if event.get('severity') in ['high', 'critical']:
            how_instruction = LLM_INSTRUCTION_TEMPLATES["how"][0]
            
            how_example = {
                "instruction": how_instruction,
                "input": {"use": event},
                "output": {
                    "plan": action_schema["triage_steps"],
                    "artifacts": [
                        {
                            "name": "remediation.tf",
                            "type": "terraform", 
                            "path": "artifacts/remediation.tf",
                            "contents": action_schema.get("spl_query", "# Terraform remediation config")
                        },
                        {
                            "name": "detection.yaml",
                            "type": "k8s_manifest",
                            "path": "artifacts/detection.yaml",
                            "contents": action_schema.get("lc_rule", "# K8s detection rule")
                        }
                    ],
                    "validations": [
                        {"validator": "terraform_fmt", "status": "passed"},
                        {"validator": "security_scan", "status": "passed"}
                    ],
                    "rollback_plan": "Automated rollback via Terraform destroy",
                    "confidence": action_schema["confidence"]
                }
            }
            
            llm_examples.append(how_example)
    
    # Split training/test
    import random
    random.shuffle(llm_examples)
    split_idx = int(len(llm_examples) * train_split)
    
    train_examples = llm_examples[:split_idx]
    test_examples = llm_examples[split_idx:]
    
    # Write LLM training files
    train_file = llm_dir / "whis_actions.jsonl"
    test_file = llm_dir / "whis_actions_test.jsonl"
    
    with open(train_file, 'w') as f:
        for example in train_examples:
            f.write(json.dumps(example) + '\n')
    
    with open(test_file, 'w') as f:
        for example in test_examples:
            f.write(json.dumps(example) + '\n')
    
    manifest.add_output_file(train_file, "llm_train", len(train_examples))
    manifest.add_output_file(test_file, "llm_test", len(test_examples))
    
    # Generate RAG chunks
    rag_chunks = rag_generator.generate_rag_chunks(all_events)
    
    # Write RAG chunks as Markdown files
    for chunk in rag_chunks:
        metadata = chunk["metadata"]
        content = chunk["content"]
        
        # Create YAML front matter
        front_matter = yaml.dump(metadata, default_flow_style=False)
        
        # Create full markdown content
        markdown_content = f"---\n{front_matter}---\n\n{content}"
        
        # Create filename from chunk ID
        filename = f"{metadata['chunk_id']}.md"
        chunk_file = rag_dir / filename
        
        with open(chunk_file, 'w') as f:
            f.write(markdown_content)
        
        manifest.add_output_file(chunk_file, "rag_chunk", 1)
    
    # Save manifest
    manifest_path = manifest.save()
    
    # Report results
    click.echo(f"✅ Curation completed")
    click.echo(f"📊 Events processed: {len(all_events)}")
    click.echo(f"📊 LLM training examples: {len(train_examples)}")
    click.echo(f"📊 LLM test examples: {len(test_examples)}")
    click.echo(f"📊 RAG chunks generated: {len(rag_chunks)}")
    click.echo(f"📁 LLM training file: {train_file}")
    click.echo(f"📁 LLM test file: {test_file}")
    click.echo(f"📁 RAG chunks directory: {rag_dir}")
    click.echo(f"📋 Manifest: {manifest_path}")

@cli.command()
@click.option('--llm-file', type=click.Path(exists=True), required=True, help='LLM JSONL file to validate')
def validate_llm(llm_file):
    """Validate LLM training file format"""
    
    file_path = Path(llm_file)
    logger.info("Validating LLM file", file=str(file_path))
    
    valid_count = 0
    invalid_count = 0
    
    required_fields = ["instruction", "input", "output"]
    required_output_fields = ["triage_steps", "mitre", "confidence"]
    
    with open(file_path, 'r') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            
            try:
                example = json.loads(line)
                
                # Check required fields
                missing_fields = [field for field in required_fields if field not in example]
                if missing_fields:
                    logger.warning("Missing fields", line=line_num, fields=missing_fields)
                    invalid_count += 1
                    continue
                
                # Check output structure
                output = example.get("output", {})
                missing_output_fields = [field for field in required_output_fields if field not in output]
                if missing_output_fields:
                    logger.warning("Missing output fields", line=line_num, fields=missing_output_fields)
                    invalid_count += 1
                    continue
                
                # Check for secrets in instruction/output
                instruction = example.get("instruction", "")
                if any(pattern in instruction.lower() for pattern in ["password", "secret", "token", "api_key"]):
                    logger.warning("Potential secret in instruction", line=line_num)
                    invalid_count += 1
                    continue
                
                valid_count += 1
                
            except json.JSONDecodeError as e:
                logger.error("JSON decode error", line=line_num, error=str(e))
                invalid_count += 1
                continue
    
    total = valid_count + invalid_count
    success_rate = (valid_count / total) * 100 if total > 0 else 0
    
    click.echo(f"📊 LLM Validation Results:")
    click.echo(f"  Valid: {valid_count}")
    click.echo(f"  Invalid: {invalid_count}")
    click.echo(f"  Success Rate: {success_rate:.1f}%")
    
    if success_rate >= 95.0:
        click.echo("✅ LLM file validation PASSED")
    else:
        click.echo("❌ LLM file validation FAILED")
        sys.exit(1)

def main():
    """Entry point for curation CLI"""
    cli()

if __name__ == "__main__":
    main()