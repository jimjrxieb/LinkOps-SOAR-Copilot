#!/usr/bin/env python3
"""
🔄 Training Pipeline for WHIS Red vs Blue Loop
Converts attack chains into training data and retrains the model
"""

import json
import logging
import asyncio
import os
import shutil
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import subprocess

# Add API path for imports
import sys
sys.path.append('/home/jimmie/linkops-industries/SOAR-copilot/apps/api')

from attack_chain_analyzer import AttackChain, attack_chain_analyzer
from golden_set import golden_set_manager, GoldenSetExample, EvaluationBucket

logger = logging.getLogger(__name__)

@dataclass
class TrainingExample:
    """Training example generated from attack chain"""
    example_id: str
    attack_chain_id: str
    input_prompt: str
    expected_output: str
    quality_score: float
    source_events: List[str]
    attack_phases: List[str]
    mitre_techniques: List[str]
    created_at: str

class WhisTrainingPipeline:
    """Pipeline for converting red vs blue data into Whis training examples"""
    
    def __init__(self):
        self.training_data_dir = Path("/home/jimmie/linkops-industries/SOAR-copilot/data/training")
        self.model_dir = Path("/home/jimmie/linkops-industries/SOAR-copilot/training")
        self.generated_examples = []
        self.training_batches = []
        
        # Create directories
        self.training_data_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("🔄 Training pipeline initialized")
    
    async def process_attack_chains(self) -> Dict[str, Any]:
        """Process completed attack chains into training data"""
        logger.info("📚 Processing attack chains for training data generation...")
        
        # Get high-value completed chains
        chains = attack_chain_analyzer.get_completed_chains(min_training_value=0.4)
        
        if not chains:
            logger.warning("No high-value attack chains available for training")
            return {"message": "No training data generated", "chains_processed": 0}
        
        logger.info(f"🎯 Processing {len(chains)} attack chains...")
        
        training_examples = []
        
        for chain in chains:
            examples = await self._convert_chain_to_training_examples(chain)
            training_examples.extend(examples)
            logger.info(f"Generated {len(examples)} examples from chain {chain.chain_id}")
        
        # Save training examples
        await self._save_training_examples(training_examples)
        
        # Update Golden Set with best examples
        await self._update_golden_set(training_examples)
        
        return {
            "chains_processed": len(chains),
            "training_examples_generated": len(training_examples),
            "high_quality_examples": len([ex for ex in training_examples if ex.quality_score > 0.7]),
            "examples_added_to_golden_set": len([ex for ex in training_examples if ex.quality_score > 0.8])
        }
    
    async def _convert_chain_to_training_examples(self, chain: AttackChain) -> List[TrainingExample]:
        """Convert a single attack chain into multiple training examples"""
        examples = []
        
        try:
            # Example 1: Initial Access Analysis
            initial_events = [e for e in chain.events if e.attack_phase and "initial_access" in e.attack_phase.value]
            if initial_events:
                example = await self._create_initial_access_example(chain, initial_events[0])
                if example:
                    examples.append(example)
            
            # Example 2: Lateral Movement Detection
            lateral_events = [e for e in chain.events if e.attack_phase and "lateral_movement" in e.attack_phase.value]
            if lateral_events and len(chain.target_hosts) > 1:
                example = await self._create_lateral_movement_example(chain, lateral_events)
                if example:
                    examples.append(example)
            
            # Example 3: Privilege Escalation
            if "privilege_escalation_success" in chain.success_indicators:
                example = await self._create_privilege_escalation_example(chain)
                if example:
                    examples.append(example)
            
            # Example 4: Persistence Detection
            if "persistence_established" in chain.success_indicators:
                example = await self._create_persistence_example(chain)
                if example:
                    examples.append(example)
            
            # Example 5: Full Attack Chain Summary
            if chain.training_value > 0.6:
                example = await self._create_full_chain_example(chain)
                if example:
                    examples.append(example)
            
        except Exception as e:
            logger.error(f"Error converting chain {chain.chain_id} to examples: {e}")
        
        return examples
    
    async def _create_initial_access_example(self, chain: AttackChain, initial_event) -> Optional[TrainingExample]:
        """Create training example for initial access scenario"""
        try:
            # Create realistic input based on the actual attack
            input_data = {
                "search_name": f"Suspicious {initial_event.event_type} Activity",
                "host": initial_event.host,
                "user": initial_event.user,
                "process": initial_event.process,
                "CommandLine": initial_event.command_line,
                "src_ip": chain.attacker_ip if chain.attacker_ip != "unknown" else "192.168.100.50",
                "dest_ip": initial_event.host,
                "timestamp": initial_event.timestamp.isoformat()
            }
            
            # Create expert-level response based on what actually happened
            expected_response = {
                "triage_steps": [
                    f"Investigate initial access via {initial_event.event_type} on {initial_event.host}",
                    f"Analyze process execution: {initial_event.process}",
                    f"Review network connections from {chain.attacker_ip}",
                    "Check for additional compromised accounts or systems",
                    "Correlate with authentication logs for timeline"
                ],
                "containment": [
                    f"Immediately isolate {initial_event.host} from network",
                    f"Block source IP {chain.attacker_ip} at firewall",
                    "Reset potentially compromised user passwords",
                    "Monitor for lateral movement attempts"
                ],
                "remediation": [
                    "Patch vulnerabilities that enabled initial access",
                    "Implement additional access controls",
                    "Deploy enhanced monitoring for similar attacks",
                    "Update incident response procedures based on findings"
                ],
                "mitre": initial_event.mitre_techniques or ["T1078"],
                "spl_query": f'index=* host="{initial_event.host}" | search "{initial_event.process}" OR src_ip="{chain.attacker_ip}"',
                "lc_rule": f"op: and\\nrules:\\n  - op: is\\n    path: event/HOST\\n    value: {initial_event.host}\\n  - op: contains\\n    path: event/COMMAND_LINE\\n    value: {initial_event.process}",
                "validation_steps": [
                    "Confirm successful network isolation",
                    "Verify no additional systems compromised", 
                    "Validate remediation effectiveness"
                ],
                "citations": ["Red vs Blue Lab Attack Data", "MITRE ATT&CK Framework"],
                "confidence": 0.85,
                "grounded": True
            }
            
            # Calculate quality score
            quality_score = 0.8  # High quality - based on real attack
            if len(chain.success_indicators) > 2:
                quality_score += 0.1
            if len(chain.phases_detected) > 3:
                quality_score += 0.1
            
            example = TrainingExample(
                example_id=f"redblue_{chain.chain_id}_initial",
                attack_chain_id=chain.chain_id,
                input_prompt=json.dumps(input_data),
                expected_output=json.dumps(expected_response),
                quality_score=min(quality_score, 1.0),
                source_events=[initial_event.event_id],
                attack_phases=[phase.value for phase in chain.phases_detected],
                mitre_techniques=initial_event.mitre_techniques,
                created_at=datetime.now().isoformat()
            )
            
            return example
            
        except Exception as e:
            logger.error(f"Error creating initial access example: {e}")
            return None
    
    async def _create_lateral_movement_example(self, chain: AttackChain, lateral_events) -> Optional[TrainingExample]:
        """Create training example for lateral movement scenario"""
        try:
            primary_event = lateral_events[0]
            
            input_data = {
                "search_name": "Lateral Movement - Multiple Host Access",
                "host": primary_event.host,
                "user": primary_event.user,
                "process": primary_event.process,
                "CommandLine": primary_event.command_line,
                "src_ip": primary_event.network_info.get("src_ip", ""),
                "dest_ip": primary_event.network_info.get("dest_ip", ""),
                "additional_hosts": chain.target_hosts,
                "timestamp": primary_event.timestamp.isoformat()
            }
            
            expected_response = {
                "triage_steps": [
                    f"Investigate lateral movement across {len(chain.target_hosts)} hosts: {', '.join(chain.target_hosts)}",
                    "Analyze authentication patterns and privilege usage",
                    "Review network connections between compromised systems",
                    "Check for credential reuse or privilege escalation",
                    "Hunt for additional compromised systems"
                ],
                "containment": [
                    f"Network segment all affected hosts: {', '.join(chain.target_hosts)}",
                    "Reset all user credentials involved in the attack",
                    "Block inter-system communication paths used",
                    "Monitor for further lateral movement attempts"
                ],
                "remediation": [
                    "Implement network segmentation controls",
                    "Deploy just-in-time admin access",
                    "Enable credential guard on all systems",
                    "Review and restrict administrative accounts"
                ],
                "mitre": list(set(chain.techniques_used)),
                "spl_query": f'index=* (host="{'" OR host="'.join(chain.target_hosts)}") | search lateral OR movement OR {primary_event.process}',
                "lc_rule": f"op: or\\nrules:\\n" + "\\n".join([f"  - op: is\\n    path: routing/hostname\\n    value: {host}" for host in chain.target_hosts]),
                "validation_steps": [
                    "Confirm all affected systems isolated",
                    "Verify no additional lateral movement",
                    "Validate credential reset effectiveness"
                ],
                "citations": ["Red vs Blue Lab - Multi-Host Attack", "NIST Lateral Movement Guide"],
                "confidence": 0.9,
                "grounded": True
            }
            
            example = TrainingExample(
                example_id=f"redblue_{chain.chain_id}_lateral",
                attack_chain_id=chain.chain_id,
                input_prompt=json.dumps(input_data),
                expected_output=json.dumps(expected_response),
                quality_score=0.9,  # Very high quality - multi-host attack
                source_events=[e.event_id for e in lateral_events],
                attack_phases=[phase.value for phase in chain.phases_detected],
                mitre_techniques=list(set(chain.techniques_used)),
                created_at=datetime.now().isoformat()
            )
            
            return example
            
        except Exception as e:
            logger.error(f"Error creating lateral movement example: {e}")
            return None
    
    async def _create_privilege_escalation_example(self, chain: AttackChain) -> Optional[TrainingExample]:
        """Create training example for privilege escalation scenario"""
        try:
            # Find privilege escalation events
            priv_esc_events = [e for e in chain.events if e.user in ["administrator", "system", "SYSTEM"]]
            
            if not priv_esc_events:
                return None
            
            event = priv_esc_events[0]
            
            input_data = {
                "search_name": "Privilege Escalation - Administrator Access Gained",
                "host": event.host,
                "user": event.user,
                "process": event.process,
                "CommandLine": event.command_line,
                "privilege_level": "administrator",
                "timestamp": event.timestamp.isoformat()
            }
            
            expected_response = {
                "triage_steps": [
                    f"Investigate how {event.user} privileges were escalated on {event.host}",
                    f"Analyze process execution: {event.process}",
                    "Review authentication logs for privilege usage",
                    "Check for exploitation of privilege escalation vulnerabilities",
                    "Hunt for persistence mechanisms established"
                ],
                "containment": [
                    f"Immediately revoke elevated privileges on {event.host}",
                    "Isolate system from network pending investigation",
                    "Reset all administrative passwords",
                    "Monitor for abuse of elevated privileges"
                ],
                "remediation": [
                    "Patch privilege escalation vulnerabilities",
                    "Implement least-privilege access controls",
                    "Deploy privileged access management (PAM)",
                    "Enable additional logging for privilege usage"
                ],
                "mitre": ["T1068", "T1548"] + event.mitre_techniques,
                "spl_query": f'index=* host="{event.host}" user="administrator" OR user="SYSTEM" | search privilege OR escalation',
                "lc_rule": f"op: and\\nrules:\\n  - op: is\\n    path: routing/hostname\\n    value: {event.host}\\n  - op: is\\n    path: event/USER\\n    value: administrator",
                "validation_steps": [
                    "Confirm privilege revocation successful",
                    "Verify no persistent elevated access remains",
                    "Validate vulnerability patches applied"
                ],
                "citations": ["Red vs Blue Lab - Privilege Escalation", "MITRE ATT&CK - Privilege Escalation"],
                "confidence": 0.85,
                "grounded": True
            }
            
            example = TrainingExample(
                example_id=f"redblue_{chain.chain_id}_privesc",
                attack_chain_id=chain.chain_id,
                input_prompt=json.dumps(input_data),
                expected_output=json.dumps(expected_response),
                quality_score=0.85,
                source_events=[event.event_id],
                attack_phases=[phase.value for phase in chain.phases_detected],
                mitre_techniques=event.mitre_techniques,
                created_at=datetime.now().isoformat()
            )
            
            return example
            
        except Exception as e:
            logger.error(f"Error creating privilege escalation example: {e}")
            return None
    
    async def _create_persistence_example(self, chain: AttackChain) -> Optional[TrainingExample]:
        """Create training example for persistence scenario"""
        try:
            # Find persistence-related events
            persistence_events = [e for e in chain.events if "registry" in e.command_line.lower() or "startup" in e.command_line.lower()]
            
            if not persistence_events:
                return None
            
            event = persistence_events[0]
            
            input_data = {
                "search_name": "Persistence Mechanism - Registry Modification",
                "host": event.host,
                "user": event.user,
                "process": event.process,
                "CommandLine": event.command_line,
                "registry_key": event.registry_info.get("key_path", ""),
                "timestamp": event.timestamp.isoformat()
            }
            
            expected_response = {
                "triage_steps": [
                    f"Investigate persistence mechanism on {event.host}",
                    f"Analyze registry modifications: {event.registry_info.get('key_path', 'unknown')}",
                    "Check for additional persistence mechanisms",
                    "Review startup items and scheduled tasks",
                    "Hunt for backdoors and implants"
                ],
                "containment": [
                    "Remove malicious registry entries immediately",
                    "Disable suspicious startup items",
                    "Monitor for re-establishment of persistence",
                    "Block execution of persistent malware"
                ],
                "remediation": [
                    "Implement application whitelisting",
                    "Deploy registry monitoring and protection",
                    "Review and secure startup locations",
                    "Enable Sysmon registry monitoring"
                ],
                "mitre": ["T1547.001", "T1112"] + event.mitre_techniques,
                "spl_query": f'index=* host="{event.host}" | search registry OR startup OR persistence',
                "lc_rule": f"op: and\\nrules:\\n  - op: is\\n    path: routing/hostname\\n    value: {event.host}\\n  - op: contains\\n    path: event/REGISTRY_KEY\\n    value: Run",
                "validation_steps": [
                    "Confirm removal of all persistence mechanisms",
                    "Verify system clean boot without malware",
                    "Validate monitoring improvements deployed"
                ],
                "citations": ["Red vs Blue Lab - Persistence Analysis", "MITRE ATT&CK - Persistence"],
                "confidence": 0.8,
                "grounded": True
            }
            
            example = TrainingExample(
                example_id=f"redblue_{chain.chain_id}_persist",
                attack_chain_id=chain.chain_id,
                input_prompt=json.dumps(input_data),
                expected_output=json.dumps(expected_response),
                quality_score=0.8,
                source_events=[event.event_id],
                attack_phases=[phase.value for phase in chain.phases_detected],
                mitre_techniques=event.mitre_techniques,
                created_at=datetime.now().isoformat()
            )
            
            return example
            
        except Exception as e:
            logger.error(f"Error creating persistence example: {e}")
            return None
    
    async def _create_full_chain_example(self, chain: AttackChain) -> Optional[TrainingExample]:
        """Create comprehensive training example for full attack chain"""
        try:
            # Summarize the entire attack chain
            input_data = {
                "search_name": f"Multi-Stage Attack Campaign - {len(chain.events)} Events",
                "attack_duration": str(chain.end_time - chain.start_time) if chain.end_time else "ongoing",
                "hosts_affected": len(chain.target_hosts),
                "techniques_observed": len(chain.techniques_used),
                "success_indicators": chain.success_indicators,
                "attacker_ip": chain.attacker_ip,
                "target_hosts": chain.target_hosts,
                "attack_phases": [phase.value for phase in chain.phases_detected]
            }
            
            expected_response = {
                "triage_steps": [
                    f"Analyze multi-stage attack affecting {len(chain.target_hosts)} systems",
                    f"Review attack timeline: {chain.start_time} to {chain.end_time}",
                    f"Investigate {len(chain.techniques_used)} MITRE techniques observed",
                    "Correlate events across affected systems",
                    "Assess overall business impact and data at risk"
                ],
                "containment": [
                    f"Network isolate all affected systems: {', '.join(chain.target_hosts)}",
                    f"Block attacker infrastructure: {chain.attacker_ip}",
                    "Reset all potentially compromised credentials",
                    "Monitor for additional infrastructure or persistence",
                    "Engage incident response team for campaign-level response"
                ],
                "remediation": [
                    "Conduct comprehensive security assessment",
                    "Deploy advanced threat hunting capabilities",
                    "Implement network segmentation improvements",
                    "Update security controls based on attack patterns",
                    "Develop organization-specific threat intelligence"
                ],
                "mitre": chain.techniques_used,
                "spl_query": f'index=* (host="{'" OR host="'.join(chain.target_hosts)}") | search campaign OR {chain.attacker_ip}',
                "lc_rule": "op: or\\nrules:\\n" + "\\n".join([f"  - op: is\\n    path: routing/hostname\\n    value: {host}" for host in chain.target_hosts]),
                "validation_steps": [
                    "Confirm complete eradication across all systems",
                    "Verify no remaining attacker infrastructure",
                    "Validate security improvements effectiveness",
                    "Document lessons learned for future prevention"
                ],
                "citations": [f"Red vs Blue Lab - Attack Chain {chain.chain_id}", "NIST Incident Response Framework"],
                "confidence": 0.95,
                "grounded": True
            }
            
            example = TrainingExample(
                example_id=f"redblue_{chain.chain_id}_full",
                attack_chain_id=chain.chain_id,
                input_prompt=json.dumps(input_data),
                expected_output=json.dumps(expected_response),
                quality_score=chain.training_value,  # Use chain's calculated value
                source_events=[e.event_id for e in chain.events],
                attack_phases=[phase.value for phase in chain.phases_detected],
                mitre_techniques=chain.techniques_used,
                created_at=datetime.now().isoformat()
            )
            
            return example
            
        except Exception as e:
            logger.error(f"Error creating full chain example: {e}")
            return None
    
    async def _save_training_examples(self, examples: List[TrainingExample]):
        """Save training examples to files"""
        batch_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        batch_dir = self.training_data_dir / f"batch_{batch_timestamp}"
        batch_dir.mkdir(exist_ok=True)
        
        # Save individual examples
        for example in examples:
            example_file = batch_dir / f"{example.example_id}.json"
            with open(example_file, 'w') as f:
                json.dump({
                    "example_id": example.example_id,
                    "attack_chain_id": example.attack_chain_id,
                    "input": json.loads(example.input_prompt),
                    "output": json.loads(example.expected_output),
                    "quality_score": example.quality_score,
                    "source_events": example.source_events,
                    "attack_phases": example.attack_phases,
                    "mitre_techniques": example.mitre_techniques,
                    "created_at": example.created_at
                }, f, indent=2)
        
        # Save batch summary
        batch_summary = {
            "batch_id": batch_timestamp,
            "total_examples": len(examples),
            "average_quality": sum(ex.quality_score for ex in examples) / len(examples),
            "examples": [ex.example_id for ex in examples],
            "created_at": datetime.now().isoformat()
        }
        
        with open(batch_dir / "batch_summary.json", 'w') as f:
            json.dump(batch_summary, f, indent=2)
        
        logger.info(f"💾 Saved {len(examples)} training examples to {batch_dir}")
        
        self.training_batches.append(batch_summary)
    
    async def _update_golden_set(self, examples: List[TrainingExample]):
        """Add high-quality examples to Golden Set"""
        high_quality_examples = [ex for ex in examples if ex.quality_score > 0.8]
        
        for example in high_quality_examples:
            try:
                input_data = json.loads(example.input_prompt)
                output_data = json.loads(example.expected_output)
                
                # Determine bucket based on complexity
                if len(example.attack_phases) > 3 and example.quality_score > 0.9:
                    bucket = EvaluationBucket.TEACHER
                else:
                    bucket = EvaluationBucket.ASSISTANT
                
                golden_example = GoldenSetExample(
                    id=example.example_id,
                    bucket=bucket,
                    input_event=input_data,
                    expected_output=output_data,
                    evaluation_criteria={
                        "completeness": "Must provide comprehensive analysis based on real attack data",
                        "accuracy": f"Must correctly identify MITRE techniques: {example.mitre_techniques}",
                        "actionability": "Must provide specific containment and remediation steps",
                        "grounding": "Must be grounded with high confidence based on lab data"
                    },
                    created_at=example.created_at,
                    tags=["red_vs_blue", "lab_data"] + example.attack_phases
                )
                
                golden_set_manager.add_example(golden_example)
                logger.info(f"📚 Added example {example.example_id} to Golden Set ({bucket.value})")
                
            except Exception as e:
                logger.error(f"Error adding example {example.example_id} to Golden Set: {e}")
    
    async def prepare_retraining_data(self) -> Dict[str, Any]:
        """Prepare all training data for model retraining"""
        logger.info("🔄 Preparing data for model retraining...")
        
        all_examples = []
        
        # Collect all training examples from batches
        for batch_dir in self.training_data_dir.iterdir():
            if batch_dir.is_dir() and batch_dir.name.startswith("batch_"):
                for example_file in batch_dir.glob("*.json"):
                    if example_file.name != "batch_summary.json":
                        with open(example_file, 'r') as f:
                            example_data = json.load(f)
                            all_examples.append(example_data)
        
        if not all_examples:
            return {"message": "No training examples available", "status": "no_data"}
        
        # Filter by quality
        high_quality_examples = [ex for ex in all_examples if ex.get("quality_score", 0) > 0.6]
        
        # Convert to training format
        training_data = []
        for example in high_quality_examples:
            # Format for CodeLlama fine-tuning
            training_entry = {
                "instruction": f"You are a SecOps copilot. A security event occurred: {example['input'].get('search_name', 'Security Event')}",
                "input": json.dumps(example['input'], indent=2),
                "output": json.dumps(example['output'], indent=2)
            }
            training_data.append(training_entry)
        
        # Save training dataset
        training_file = self.training_data_dir / "whis_retraining_dataset.json"
        with open(training_file, 'w') as f:
            json.dump(training_data, f, indent=2)
        
        logger.info(f"💾 Prepared {len(training_data)} examples for retraining")
        
        return {
            "status": "ready",
            "total_examples": len(training_data),
            "training_file": str(training_file),
            "average_quality": sum(ex.get("quality_score", 0) for ex in high_quality_examples) / len(high_quality_examples),
            "unique_techniques": len(set().union(*[ex.get("mitre_techniques", []) for ex in high_quality_examples])),
            "attack_phases_covered": len(set().union(*[ex.get("attack_phases", []) for ex in high_quality_examples]))
        }
    
    async def trigger_retraining(self) -> Dict[str, Any]:
        """Trigger model retraining with new red vs blue data"""
        logger.info("🚀 Starting model retraining with red vs blue data...")
        
        try:
            # Prepare training data
            prep_result = await self.prepare_retraining_data()
            
            if prep_result.get("status") != "ready":
                return prep_result
            
            # Copy new data to training directory
            source_file = Path(prep_result["training_file"])
            dest_file = self.model_dir / "red_blue_training_data.json"
            shutil.copy(source_file, dest_file)
            
            # Create retraining script
            retrain_script = self.model_dir / "retrain_with_red_blue.py"
            
            script_content = f'''#!/usr/bin/env python3
"""
🔄 Whis Model Retraining with Red vs Blue Data
"""

import json
from datasets import Dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer, 
    TrainingArguments,
    DataCollatorForLanguageModeling
)
from peft import LoraConfig, get_peft_model, TaskType
from trl import SFTTrainer
import torch

def main():
    print("🔄 Starting Whis model retraining with red vs blue data...")
    
    # Load new training data
    with open("red_blue_training_data.json", "r") as f:
        training_data = json.load(f)
    
    print(f"📚 Loaded {{len(training_data)}} new training examples")
    
    # Load base model and tokenizer
    model_name = "codellama/CodeLlama-7b-Instruct-hf"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    tokenizer.pad_token = tokenizer.eos_token
    
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.bfloat16,
        device_map="auto",
        trust_remote_code=True
    )
    
    # Load existing LoRA if it exists
    try:
        from peft import PeftModel
        model = PeftModel.from_pretrained(model, "./whis-mega-model")
        print("✅ Loaded existing Whis model for continued training")
    except:
        print("🆕 Starting fresh LoRA training")
        # Configure LoRA
        lora_config = LoraConfig(
            r=16,
            lora_alpha=32,
            target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
            lora_dropout=0.1,
            bias="none",
            task_type=TaskType.CAUSAL_LM
        )
        model = get_peft_model(model, lora_config)
    
    # Prepare dataset
    def format_prompt(example):
        prompt = f\"\"\"Below is an instruction that describes a cybersecurity task, paired with an input that provides further context. Write a response that appropriately completes the request.

### Instruction:
{{example['instruction']}}

### Input:
{{example['input']}}

### Response:
{{example['output']}}\"\"\"
        return {{"text": prompt}}
    
    dataset = Dataset.from_list(training_data)
    dataset = dataset.map(format_prompt)
    
    # Training arguments
    training_args = TrainingArguments(
        output_dir="./whis-mega-model-v2",
        per_device_train_batch_size=1,
        gradient_accumulation_steps=4,
        num_train_epochs=3,
        learning_rate=2e-4,
        logging_steps=10,
        save_steps=50,
        save_strategy="steps",
        optim="adamw_torch",
        lr_scheduler_type="cosine",
        warmup_steps=10,
        bf16=True,
        dataloader_drop_last=True,
        run_name="whis-red-blue-retrain"
    )
    
    # Trainer
    trainer = SFTTrainer(
        model=model,
        train_dataset=dataset,
        tokenizer=tokenizer,
        args=training_args,
        max_seq_length=2048,
        dataset_text_field="text",
        data_collator=DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)
    )
    
    # Train
    print("🚀 Starting training...")
    trainer.train()
    
    # Save model
    trainer.save_model("./whis-mega-model-v2")
    print("✅ Model saved to ./whis-mega-model-v2")
    
    # Update symlink to new model
    import os
    if os.path.exists("./whis-mega-model"):
        os.remove("./whis-mega-model")
    os.symlink("./whis-mega-model-v2", "./whis-mega-model")
    
    print("🎉 Retraining complete! New model is ready for deployment.")

if __name__ == "__main__":
    main()
'''
            
            with open(retrain_script, 'w') as f:
                f.write(script_content)
            
            retrain_script.chmod(0o755)
            
            logger.info("🎯 Retraining preparation complete")
            
            return {
                "status": "prepared",
                "message": "Retraining setup complete - run retrain_with_red_blue.py to start",
                "training_examples": prep_result["total_examples"],
                "script_location": str(retrain_script),
                "data_location": str(dest_file),
                "next_steps": [
                    f"cd {self.model_dir}",
                    "python retrain_with_red_blue.py",
                    "Wait for training completion",
                    "Test new model with quality gates",
                    "Deploy if quality gates pass"
                ]
            }
            
        except Exception as e:
            logger.error(f"Error preparing retraining: {e}")
            return {"status": "error", "error": str(e)}
    
    def get_training_statistics(self) -> Dict[str, Any]:
        """Get statistics about generated training data"""
        total_examples = len(self.generated_examples)
        
        if total_examples == 0:
            return {"message": "No training examples generated yet"}
        
        quality_distribution = {
            "high_quality": len([ex for ex in self.generated_examples if ex.quality_score > 0.8]),
            "medium_quality": len([ex for ex in self.generated_examples if 0.6 <= ex.quality_score <= 0.8]),
            "low_quality": len([ex for ex in self.generated_examples if ex.quality_score < 0.6])
        }
        
        attack_phases_covered = set()
        techniques_covered = set()
        
        for example in self.generated_examples:
            attack_phases_covered.update(example.attack_phases)
            techniques_covered.update(example.mitre_techniques)
        
        return {
            "total_examples": total_examples,
            "quality_distribution": quality_distribution,
            "average_quality": sum(ex.quality_score for ex in self.generated_examples) / total_examples,
            "attack_phases_covered": list(attack_phases_covered),
            "mitre_techniques_covered": list(techniques_covered),
            "training_batches": len(self.training_batches)
        }

# Global training pipeline
training_pipeline = WhisTrainingPipeline()