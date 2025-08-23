#!/usr/bin/env python3
"""
Final RAG to Training Converter
Properly extracts all scenarios and creates training examples
"""

import json
import re
import hashlib
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

class FinalRAGConverter:
    def __init__(self):
        self.sanitized_dir = Path("sanitized_rag_data")
        self.output_dir = Path("../../llm/data")
        
    def load_all_sanitized_text(self) -> str:
        """Load and combine all sanitized text chunks"""
        sanitized_files = list(self.sanitized_dir.glob("sanitized_chunks_*.jsonl"))
        if not sanitized_files:
            raise FileNotFoundError("No sanitized RAG chunks found")
        
        latest_file = max(sanitized_files, key=lambda x: x.stat().st_mtime)
        print(f"📖 Loading sanitized chunks: {latest_file}")
        
        all_text = ""
        chunk_count = 0
        
        with open(latest_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    chunk = json.loads(line)
                    text = chunk.get('text', '')
                    all_text += "\n" + text
                    chunk_count += 1
        
        print(f"  ✅ Combined {chunk_count} chunks into {len(all_text)} characters")
        return all_text
    
    def extract_all_scenarios(self, text: str) -> List[Dict]:
        """Extract all scenarios from combined text"""
        print("🔍 Extracting scenarios from combined text...")
        
        scenarios = []
        scenario_pattern = r'# Scenario: ([^#\n]+)'
        scenario_matches = list(re.finditer(scenario_pattern, text))
        
        print(f"  🎯 Found {len(scenario_matches)} scenarios")
        
        for i, match in enumerate(scenario_matches):
            scenario_title = match.group(1).strip().strip('"')
            start_pos = match.start()
            end_pos = scenario_matches[i + 1].start() if i + 1 < len(scenario_matches) else len(text)
            
            scenario_content = text[start_pos:end_pos]
            
            # Extract key sections using more flexible patterns
            problem = self.extract_section(scenario_content, r'\*\*Problem\*\*:\s*(.*?)(?=\*\*[A-Z])', multiline=True)
            practices = self.extract_section(scenario_content, r'\*\*DevSecOps Practice\*\*:\s*(.*?)(?=\*\*[A-Z])', multiline=True)
            costs = self.extract_section(scenario_content, r'\*\*(?:Cost Analysis|Financial Analysis|Economics)\*\*:\s*(.*?)(?=\*\*[A-Z])', multiline=True)
            implementation = self.extract_section(scenario_content, r'\*\*(?:Actionable Implementation|Implementation|Strategic Implementation)\*\*:\s*(.*?)(?=\*\*[A-Z])', multiline=True)
            communication = self.extract_section(scenario_content, r'\*\*(?:Executive Communication|Business Communication)\*\*:\s*(.*?)(?=\*\*[A-Z]|---)', multiline=True)
            
            if problem:  # Only process if we have a problem statement
                scenarios.append({
                    'title': scenario_title,
                    'problem': problem.strip(),
                    'practices': practices.strip() if practices else '',
                    'costs': costs.strip() if costs else '',
                    'implementation': implementation.strip() if implementation else '',
                    'communication': communication.strip() if communication else '',
                    'full_content': scenario_content[:1000]  # Truncate for debugging
                })
        
        print(f"  ✅ Successfully extracted {len(scenarios)} scenarios with problem statements")
        return scenarios
    
    def extract_section(self, text: str, pattern: str, multiline: bool = False) -> str:
        """Extract a section using regex pattern"""
        flags = re.DOTALL if multiline else 0
        match = re.search(pattern, text, flags)
        if match:
            result = match.group(1).strip()
            # Clean up the result
            result = re.sub(r'\n\s*\n', '\n', result)  # Remove multiple newlines
            result = re.sub(r'\s+', ' ', result)  # Normalize whitespace
            return result
        return ""
    
    def create_training_example(self, scenario: Dict) -> Dict:
        """Create a training example from a scenario"""
        
        # Create instruction based on scenario
        problem_snippet = scenario['problem'][:150] if scenario['problem'] else scenario['title']
        
        # Choose instruction format based on scenario type
        title_lower = scenario['title'].lower()
        
        if "patch" in title_lower and "downtime" in title_lower:
            instruction = "How do you handle a CIO who refuses to patch critical servers due to downtime concerns?"
        elif "mfa" in title_lower and ("executive" in title_lower or "disruptive" in title_lower):
            instruction = "Security team says 'Enable MFA', but executives push back on usability. What's your senior-level approach?"
        elif "budget" in title_lower and ("edr" in title_lower or "xdr" in title_lower):
            instruction = "CFO says 'We don't have budget for EDR'. How do you justify the investment?"
        elif "container" in title_lower and ("slow" in title_lower or "complex" in title_lower):
            instruction = "Development team resists container security scanning claiming it slows CI/CD pipelines. How do you address this?"
        elif "zero trust" in title_lower:
            instruction = "How do you justify Zero Trust implementation when network team says it's too disruptive?"
        elif "compliance" in title_lower and "automation" in title_lower:
            instruction = "Compliance team manually generates reports taking 200+ hours per quarter. How do you build ROI case for automation?"
        elif "cloud migration" in title_lower:
            instruction = "Cloud migration team wants to move fast but security team demands comprehensive controls. How do you balance speed vs security?"
        elif "api security" in title_lower:
            instruction = "API security gaps identified but development team says implementing OAuth 2.0 will delay product launch by 3 months. What's your recommendation?"
        elif "saas" in title_lower and "shadow it" in title_lower:
            instruction = "200+ SaaS applications discovered through shadow IT. How do you manage this security and cost risk?"
        elif "supply chain" in title_lower:
            instruction = "Supply chain attack concerns after SolarWinds. How do you protect 2000+ third-party software components cost-effectively?"
        elif "msp" in title_lower:
            instruction = "MSP security concerns with 8 managed service providers having privileged access. How do you reduce this extended enterprise risk?"
        elif "gdpr" in title_lower and "data subject" in title_lower:
            instruction = "GDPR compliance requires processing 500+ data subject requests monthly at 8 hours each. How do you automate this cost-effectively?"
        elif "insurance" in title_lower:
            instruction = "Cyber insurance premiums increased 300% to $500K. How do you optimize this through security control investments?"
        elif "tool" in title_lower and ("sprawl" in title_lower or "consolidation" in title_lower):
            instruction = "25+ security tools creating $800K licensing costs with poor integration. How do you build case for consolidation?"
        else:
            instruction = f"How would you handle this DevSecOps challenge: {scenario['title']}"
        
        # Extract cost figures for guidance
        cost_info = ""
        if scenario['costs']:
            cost_matches = re.findall(r'\$[0-9.,]+[KMB]?', scenario['costs'])
            if cost_matches:
                cost_info = f"Financial impact: {', '.join(cost_matches[:3])}. "
        
        # Create structured response
        triage_steps = [
            "Assess business impact and stakeholder concerns",
            "Quantify current risk exposure and costs",
            "Evaluate implementation options and trade-offs"
        ]
        
        containment_steps = [
            "Implement immediate risk mitigation measures",
            "Deploy interim security controls where feasible",
            "Coordinate with business stakeholders on timeline"
        ]
        
        remediation_steps = [
            "Execute phased implementation plan with measurable milestones",
            "Deploy automated controls and continuous monitoring",
            "Establish governance framework and ongoing measurement"
        ]
        
        # Extract specific steps from implementation if available
        if scenario['implementation']:
            impl_lines = [line.strip() for line in scenario['implementation'].split('\n') if line.strip()]
            numbered_items = [line for line in impl_lines if re.match(r'^\d+\.', line)]
            
            if len(numbered_items) >= 3:
                remediation_steps = []
                for item in numbered_items[:3]:
                    clean_item = re.sub(r'^\d+\.\s*\*\*[^:]*\*\*:\s*', '', item)
                    clean_item = re.sub(r'^\d+\.\s*', '', clean_item)
                    if clean_item:
                        remediation_steps.append(clean_item[:100])  # Truncate long items
        
        # Determine MITRE techniques
        mitre_techniques = ["T1190 - Exploit Public-Facing Application"]  # Default
        
        if "patch" in title_lower:
            mitre_techniques = ["T1190 - Exploit Public-Facing Application"]
        elif "mfa" in title_lower or "account" in title_lower:
            mitre_techniques = ["T1078 - Valid Accounts", "T1110 - Brute Force"]
        elif "edr" in title_lower or "endpoint" in title_lower:
            mitre_techniques = ["T1055 - Process Injection", "T1083 - File and Directory Discovery"]
        elif "container" in title_lower:
            mitre_techniques = ["T1610 - Deploy Container"]
        elif "zero trust" in title_lower:
            mitre_techniques = ["T1021 - Remote Services", "T1570 - Lateral Tool Transfer"]
        elif "api" in title_lower:
            mitre_techniques = ["T1190 - Exploit Public-Facing Application"]
        elif "supply chain" in title_lower:
            mitre_techniques = ["T1195 - Supply Chain Compromise"]
        elif "vendor" in title_lower or "msp" in title_lower:
            mitre_techniques = ["T1199 - Trusted Relationship"]
        elif "data" in title_lower and ("loss" in title_lower or "gdpr" in title_lower):
            mitre_techniques = ["T1041 - Exfiltration Over C2 Channel"]
        
        # Create guidance
        guidance = f"Business-focused approach to {scenario['title'].lower()}. {cost_info}Balance security requirements with operational constraints using risk-based prioritization and measurable ROI. Focus on stakeholder communication and phased implementation."
        
        # Create response in Action Schema format
        response = {
            "triage_steps": triage_steps,
            "containment": containment_steps,
            "remediation": remediation_steps,
            "mitre": mitre_techniques,
            "guidance": guidance,
            "citations": ["Industry Cost-Benefit Analysis", "DevSecOps Economics Framework"],
            "confidence": 0.88
        }
        
        return {
            "instruction": instruction,
            "input": "",
            "output": json.dumps(response, separators=(',', ':')),
            "metadata": {
                "category": "senior_devsecops_rag",
                "source": "sanitized_rag_final",
                "original_title": scenario['title']
            }
        }
    
    def create_comprehensive_dataset(self):
        """Create the final comprehensive training dataset"""
        print("🚀 FINAL RAG TO TRAINING CONVERTER")
        print("=" * 60)
        
        # Load all sanitized text
        all_text = self.load_all_sanitized_text()
        
        # Extract all scenarios
        scenarios = self.extract_all_scenarios(all_text)
        
        # Create training examples
        print("🔄 Creating training examples...")
        training_examples = []
        
        for scenario in scenarios:
            example = self.create_training_example(scenario)
            training_examples.append(example)
        
        print(f"  ✅ Created {len(training_examples)} training examples from RAG scenarios")
        
        # Load existing training data
        existing_examples = []
        existing_files = [
            "devsecops_senior_scenarios.jsonl",
            "security_interview_questions.jsonl"
        ]
        
        for file_name in existing_files:
            file_path = self.output_dir / file_name
            if file_path.exists():
                print(f"📚 Loading existing training data: {file_name}")
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            existing_examples.append(json.loads(line))
        
        # Combine and deduplicate
        all_examples = existing_examples + training_examples
        
        # Simple deduplication by instruction
        seen_instructions = set()
        unique_examples = []
        
        for example in all_examples:
            instruction = example.get('instruction', '')
            if instruction not in seen_instructions:
                seen_instructions.add(instruction)
                unique_examples.append(example)
        
        duplicates_removed = len(all_examples) - len(unique_examples)
        
        print(f"\n📊 DATASET SUMMARY:")
        print(f"  📖 Existing examples: {len(existing_examples)}")
        print(f"  🧠 RAG-derived examples: {len(training_examples)}")
        print(f"  🔄 Total before dedup: {len(all_examples)}")
        print(f"  ❌ Duplicates removed: {duplicates_removed}")
        print(f"  ✅ Final unique examples: {len(unique_examples)}")
        
        # Save the comprehensive dataset
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.output_dir / f"whis_comprehensive_training_{timestamp}.jsonl"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            for example in unique_examples:
                f.write(json.dumps(example, ensure_ascii=False, separators=(',', ':')) + '\n')
        
        # Create latest symlink
        latest_file = self.output_dir / "whis_comprehensive_training_latest.jsonl"
        if latest_file.exists() or latest_file.is_symlink():
            latest_file.unlink()
        latest_file.symlink_to(output_file.name)
        
        print(f"\n✅ COMPREHENSIVE TRAINING DATASET CREATED")
        print(f"📁 Output file: {output_file}")
        print(f"🔗 Latest link: {latest_file}")
        print(f"\n🎯 Ready for Whis model training with {len(unique_examples)} examples!")
        
        return output_file

def main():
    converter = FinalRAGConverter()
    output_file = converter.create_comprehensive_dataset()
    
    print(f"\n🚀 Next step: Train Whis model with {output_file}")

if __name__ == "__main__":
    main()