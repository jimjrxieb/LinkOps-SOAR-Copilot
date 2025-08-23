#!/usr/bin/env python3
"""
Improved RAG to Training Data Converter
Extracts specific scenarios and creates high-quality training examples
"""

import json
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

class ImprovedRAGConverter:
    def __init__(self):
        self.sanitized_dir = Path("sanitized_rag_data")
        self.output_dir = Path("../../llm/data")
        
    def extract_scenario_from_text(self, text: str) -> List[Dict]:
        """Extract individual scenarios from text chunks"""
        scenarios = []
        
        # Split by scenario headers
        scenario_pattern = r'# Scenario: ([^#\n]+)'
        scenario_matches = list(re.finditer(scenario_pattern, text))
        
        for i, match in enumerate(scenario_matches):
            scenario_title = match.group(1).strip().strip('"')
            start_pos = match.start()
            end_pos = scenario_matches[i + 1].start() if i + 1 < len(scenario_matches) else len(text)
            
            scenario_content = text[start_pos:end_pos]
            
            # Extract key sections
            problem = self.extract_section(scenario_content, r'\*\*Problem\*\*:(.*?)(?=\*\*|$)', multiline=True)
            practices = self.extract_section(scenario_content, r'\*\*DevSecOps Practice\*\*:(.*?)(?=\*\*|$)', multiline=True)
            costs = self.extract_section(scenario_content, r'\*\*Cost Analysis\*\*:(.*?)(?=\*\*|$)', multiline=True)
            implementation = self.extract_section(scenario_content, r'\*\*Actionable Implementation\*\*:(.*?)(?=\*\*|$)', multiline=True)
            communication = self.extract_section(scenario_content, r'\*\*Executive Communication\*\*:(.*?)(?=\*\*|$)', multiline=True)
            
            if problem and costs:  # Only process if we have core sections
                scenarios.append({
                    'title': scenario_title,
                    'problem': problem.strip(),
                    'practices': practices.strip() if practices else '',
                    'costs': costs.strip(),
                    'implementation': implementation.strip() if implementation else '',
                    'communication': communication.strip() if communication else '',
                    'full_content': scenario_content
                })
        
        return scenarios
    
    def extract_section(self, text: str, pattern: str, multiline: bool = False) -> str:
        """Extract a section using regex pattern"""
        flags = re.DOTALL | re.MULTILINE if multiline else 0
        match = re.search(pattern, text, flags)
        return match.group(1).strip() if match else ""
    
    def create_training_example(self, scenario: Dict, category: str) -> Dict:
        """Create a training example from a scenario"""
        
        # Create instruction based on the scenario title and problem
        if "patch" in scenario['title'].lower():
            instruction = f"How do you handle patch management when {scenario['problem'][:100]}...?"
        elif "mfa" in scenario['title'].lower():
            instruction = f"How would you implement MFA when facing this challenge: {scenario['problem'][:100]}...?"
        elif "budget" in scenario['title'].lower() or "cost" in scenario['title'].lower():
            instruction = f"How do you justify security investments in this situation: {scenario['problem'][:100]}...?"
        elif "compliance" in scenario['title'].lower():
            instruction = f"How would you handle compliance requirements when {scenario['problem'][:100]}...?"
        elif "zero trust" in scenario['title'].lower():
            instruction = f"How would you implement Zero Trust when {scenario['problem'][:100]}...?"
        else:
            instruction = f"How would you handle this DevSecOps challenge: {scenario['title']}"
        
        # Extract specific steps from implementation
        triage_steps = []
        containment_steps = []
        remediation_steps = []
        
        if scenario['implementation']:
            impl_lines = scenario['implementation'].split('\n')
            for line in impl_lines:
                if line.strip() and ('1.' in line or '2.' in line or '3.' in line):
                    if 'assess' in line.lower() or 'evaluate' in line.lower() or 'identify' in line.lower():
                        triage_steps.append(line.split(':', 1)[-1].strip().strip('*').strip())
                    elif 'immediate' in line.lower() or 'emergency' in line.lower() or 'temporary' in line.lower():
                        containment_steps.append(line.split(':', 1)[-1].strip().strip('*').strip())
                    else:
                        remediation_steps.append(line.split(':', 1)[-1].strip().strip('*').strip())
        
        # Ensure we have at least basic steps
        if not triage_steps:
            triage_steps = [
                "Assess current security posture and business impact",
                "Identify stakeholder concerns and constraints",
                "Evaluate cost-benefit analysis and ROI potential"
            ]
        
        if not containment_steps:
            containment_steps = [
                "Implement immediate risk mitigation measures",
                "Deploy temporary security controls where feasible",
                "Coordinate with business stakeholders on timeline"
            ]
        
        if not remediation_steps:
            remediation_steps = [
                "Execute comprehensive implementation plan with phased approach",
                "Deploy automated controls and continuous monitoring",
                "Establish ongoing governance and measurement framework"
            ]
        
        # Create guidance from the scenario content
        guidance = f"Address {scenario['title'].lower()} with business-focused approach. "
        
        if scenario['costs']:
            cost_match = re.search(r'\$([0-9.]+[KM]?)', scenario['costs'])
            if cost_match:
                guidance += f"Consider financial impact: {cost_match.group(0)}. "
        
        guidance += "Balance security requirements with operational needs and cost constraints. Use risk-based prioritization and measurable ROI."
        
        # Determine MITRE techniques based on scenario type
        mitre_techniques = []
        if "patch" in scenario['title'].lower():
            mitre_techniques = ["T1190 - Exploit Public-Facing Application"]
        elif "mfa" in scenario['title'].lower():
            mitre_techniques = ["T1078 - Valid Accounts", "T1110 - Brute Force"]
        elif "edr" in scenario['title'].lower():
            mitre_techniques = ["T1055 - Process Injection", "T1083 - File and Directory Discovery"]
        elif "zero trust" in scenario['title'].lower():
            mitre_techniques = ["T1021 - Remote Services", "T1570 - Lateral Tool Transfer"]
        elif "container" in scenario['title'].lower():
            mitre_techniques = ["T1610 - Deploy Container"]
        else:
            mitre_techniques = ["T1562 - Impair Defenses"]
        
        # Create response in Action Schema format
        response = {
            "triage_steps": triage_steps[:3],  # Limit to 3 steps
            "containment": containment_steps[:3],
            "remediation": remediation_steps[:3],
            "mitre": mitre_techniques,
            "guidance": guidance,
            "citations": ["Industry Cost-Benefit Analysis", "DevSecOps Best Practices"],
            "confidence": 0.88
        }
        
        return {
            "instruction": instruction,
            "input": "",
            "output": json.dumps(response, separators=(',', ':')),
            "metadata": {
                "category": "senior_devsecops",
                "source": "sanitized_rag_enhanced",
                "scenario_type": category,
                "original_title": scenario['title']
            }
        }
    
    def process_sanitized_chunks(self) -> List[Dict]:
        """Process all sanitized chunks into training examples"""
        print("🔄 Processing sanitized RAG chunks into training examples...")
        
        # Find the latest sanitized file
        sanitized_files = list(self.sanitized_dir.glob("sanitized_chunks_*.jsonl"))
        if not sanitized_files:
            raise FileNotFoundError("No sanitized RAG chunks found")
        
        latest_file = max(sanitized_files, key=lambda x: x.stat().st_mtime)
        print(f"📖 Loading sanitized chunks: {latest_file}")
        
        training_examples = []
        
        with open(latest_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    chunk = json.loads(line)
                    text = chunk.get('text', '')
                    
                    # Extract scenarios from this chunk
                    scenarios = self.extract_scenario_from_text(text)
                    
                    # Determine category from title
                    title = chunk.get('title', '').lower()
                    if 'devsecops' in title:
                        category = 'devsecops_economics'
                    elif 'cloud' in title:
                        category = 'cloud_security'
                    elif 'incident' in title:
                        category = 'incident_response'
                    elif 'compliance' in title:
                        category = 'compliance_automation'
                    elif 'vendor' in title:
                        category = 'vendor_risk'
                    else:
                        category = 'general_security'
                    
                    # Create training examples from scenarios
                    for scenario in scenarios:
                        example = self.create_training_example(scenario, category)
                        training_examples.append(example)
        
        print(f"  ✅ Created {len(training_examples)} training examples from sanitized RAG")
        return training_examples
    
    def save_enhanced_training_data(self, training_examples: List[Dict]):
        """Save enhanced training data"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Load existing training data and combine
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
        
        # Combine all examples
        all_examples = existing_examples + training_examples
        
        print(f"📊 Total training examples: {len(all_examples)}")
        print(f"  📖 Existing: {len(existing_examples)}")
        print(f"  🧠 RAG-derived: {len(training_examples)}")
        
        # Save combined dataset
        output_file = self.output_dir / f"whis_mega_enhanced_training_{timestamp}.jsonl"
        with open(output_file, 'w', encoding='utf-8') as f:
            for example in all_examples:
                f.write(json.dumps(example, ensure_ascii=False, separators=(',', ':')) + '\n')
        
        # Create latest symlink
        latest_file = self.output_dir / "whis_mega_enhanced_training_latest.jsonl"
        if latest_file.exists() or latest_file.is_symlink():
            latest_file.unlink()
        latest_file.symlink_to(output_file.name)
        
        print(f"\n✅ ENHANCED TRAINING DATA CREATED")
        print(f"📁 Output file: {output_file}")
        print(f"🔗 Latest link: {latest_file}")
        
        return output_file

def main():
    print("🚀 IMPROVED RAG TO TRAINING CONVERTER")
    print("=" * 50)
    
    converter = ImprovedRAGConverter()
    training_examples = converter.process_sanitized_chunks()
    output_file = converter.save_enhanced_training_data(training_examples)
    
    print(f"\n🎯 Ready for Whis model training!")
    print(f"   Use: {output_file}")

if __name__ == "__main__":
    main()