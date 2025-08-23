#!/usr/bin/env python3
"""
Debug RAG scenario extraction
"""

import json
import re
from pathlib import Path

def debug_scenarios():
    sanitized_dir = Path("sanitized_rag_data")
    sanitized_files = list(sanitized_dir.glob("sanitized_chunks_*.jsonl"))
    latest_file = max(sanitized_files, key=lambda x: x.stat().st_mtime)
    
    print(f"🔍 Debugging scenarios in: {latest_file}")
    
    all_text = ""
    chunk_count = 0
    
    with open(latest_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                chunk = json.loads(line)
                text = chunk.get('text', '')
                all_text += "\n" + text
                chunk_count += 1
                
                # Check for scenario patterns in individual chunks
                scenario_pattern = r'# Scenario: ([^#\n]+)'
                matches = list(re.finditer(scenario_pattern, text))
                
                if matches:
                    print(f"\n📄 Chunk {chunk_count}: Found {len(matches)} scenarios")
                    for match in matches:
                        print(f"  - {match.group(1).strip()}")
                        
                        # Show some context
                        start = max(0, match.start() - 50)
                        end = min(len(text), match.end() + 200)
                        context = text[start:end].replace('\n', ' ')
                        print(f"    Context: {context[:100]}...")
    
    # Now check all text combined
    print(f"\n🔍 Total chunks processed: {chunk_count}")
    print(f"📊 Total text length: {len(all_text)}")
    
    # Find all scenarios in combined text
    scenario_pattern = r'# Scenario: ([^#\n]+)'
    all_scenarios = list(re.finditer(scenario_pattern, all_text))
    
    print(f"🎯 Total scenarios found in combined text: {len(all_scenarios)}")
    
    for i, match in enumerate(all_scenarios[:5]):  # Show first 5
        print(f"{i+1}. {match.group(1).strip()}")
        
        # Extract problem section for this scenario
        start_pos = match.start()
        end_pos = all_scenarios[i + 1].start() if i + 1 < len(all_scenarios) else len(all_text)
        scenario_content = all_text[start_pos:end_pos]
        
        problem_match = re.search(r'\*\*Problem\*\*:(.*?)(?=\*\*|$)', scenario_content, re.DOTALL)
        if problem_match:
            problem = problem_match.group(1).strip()[:100]
            print(f"   Problem: {problem}...")
        else:
            print("   Problem: Not found")
    
    return len(all_scenarios)

if __name__ == "__main__":
    debug_scenarios()