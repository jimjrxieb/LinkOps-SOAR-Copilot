#!/usr/bin/env python3
"""
Mentor's Validation Prompts - Exact requirements
Pass criteria: ATT&CK T1110, 4625 key fields, FP patterns, thresholds, 4 sections, approval_required
"""

import json
from datetime import datetime

# Mentor's exact validation prompts
TEACHER_PROMPT = """Explain Windows Event **4625**. Return (1) meaning & key fields (**LogonType, AccountName, IpAddress**), (2) common false positives, (3) escalation threshold. Map to **MITRE ATT&CK T1110** and cite sources."""

ASSISTANT_PROMPT = """Assistant mode: we saw repeated 4625s indicating brute force. Return four sections:

1. **detection_outline** (SIEM-agnostic + one Splunk SPL example),
2. **playbook_choice** with **preconditions** & **rollback**,
3. **limacharlie_actions** with **approval_required: true**,
4. **team_update** (Slack-ready). Include citations."""

def format_prompt_for_model(prompt_text, mode="teacher"):
    """Format prompt in Alpaca style for model"""
    if mode == "teacher":
        return f"""Below is an instruction that describes a cybersecurity task. Write a response that appropriately completes the request.

### Instruction:
{prompt_text}

### Response:"""
    else:  # assistant
        return f"""Below is an instruction that describes a cybersecurity task. Write a response that appropriately completes the request.

### Instruction:
{prompt_text}

### Response:"""

def validate_teacher_response(response):
    """Validate teacher response against mentor's criteria"""
    response_lower = response.lower()
    
    criteria = {
        "has_logontype": "logontype" in response_lower,
        "has_accountname": "accountname" in response_lower,
        "has_ipaddress": "ipaddress" in response_lower,
        "maps_to_t1110": "t1110" in response_lower,
        "mentions_false_positives": any(fp in response_lower for fp in [
            "false positive", "service account", "typo", "caps lock", "vacation"
        ]),
        "has_threshold": any(thresh in response_lower for thresh in [
            "threshold", "escalation", "5 failures", "10 failures", "alert"
        ]),
        "cites_sources": any(cite in response_lower for cite in [
            "mitre", "att&ck", "nist", "source"
        ])
    }
    
    passed = sum(criteria.values())
    total = len(criteria)
    
    return {
        "criteria": criteria,
        "score": passed / total,
        "passed": passed >= 6,  # Must pass at least 6/7 criteria
        "details": f"Passed {passed}/{total} criteria"
    }

def validate_assistant_response(response):
    """Validate assistant response against mentor's criteria"""
    response_lower = response.lower()
    
    # Check for 4 required sections
    sections = {
        "detection_outline": "detection" in response_lower and ("outline" in response_lower or "spl" in response_lower),
        "playbook_choice": "playbook" in response_lower and ("choice" in response_lower or "precondition" in response_lower),
        "limacharlie_actions": "limacharlie" in response_lower or "lc" in response_lower,
        "team_update": any(update in response_lower for update in ["slack", "team", "update", "notification"])
    }
    
    other_criteria = {
        "approval_required": "approval" in response_lower and "required" in response_lower and "true" in response_lower,
        "has_splunk_example": "spl" in response_lower or "index=" in response_lower,
        "maps_to_t1110": "t1110" in response_lower,
        "includes_citations": any(cite in response_lower for cite in ["source", "reference", "cite", "mitre"])
    }
    
    all_criteria = {**sections, **other_criteria}
    passed = sum(all_criteria.values())
    total = len(all_criteria)
    
    return {
        "sections": sections,
        "other_criteria": other_criteria,
        "score": passed / total,
        "passed": passed >= 7 and all_criteria["approval_required"],  # Must have approval_required
        "details": f"Passed {passed}/{total} criteria, approval_required: {all_criteria['approval_required']}"
    }

def run_mentor_validation(model_generate_func):
    """Run mentor's validation with provided model function"""
    print("🎓 Running Mentor's Validation Criteria")
    print("=" * 60)
    
    results = {
        "validation_timestamp": datetime.now().isoformat(),
        "teacher_test": {},
        "assistant_test": {},
        "overall_pass": False
    }
    
    # Test Teacher Mode
    print("\n🎯 TEACHER TEST:")
    print("Expected: LogonType, AccountName, IpAddress, FP patterns, T1110 mapping")
    
    teacher_formatted = format_prompt_for_model(TEACHER_PROMPT, "teacher")
    teacher_response = model_generate_func(teacher_formatted)
    teacher_validation = validate_teacher_response(teacher_response)
    
    results["teacher_test"] = {
        "prompt": TEACHER_PROMPT,
        "response": teacher_response,
        "validation": teacher_validation
    }
    
    print(f"📊 Teacher Score: {teacher_validation['score']:.2f}")
    print(f"✅ Teacher Pass: {teacher_validation['passed']}")
    print(f"📝 Details: {teacher_validation['details']}")
    
    # Test Assistant Mode
    print("\n🤖 ASSISTANT TEST:")
    print("Expected: 4 sections + approval_required: true + T1110 mapping")
    
    assistant_formatted = format_prompt_for_model(ASSISTANT_PROMPT, "assistant")
    assistant_response = model_generate_func(assistant_formatted)
    assistant_validation = validate_assistant_response(assistant_response)
    
    results["assistant_test"] = {
        "prompt": ASSISTANT_PROMPT,
        "response": assistant_response,
        "validation": assistant_validation
    }
    
    print(f"📊 Assistant Score: {assistant_validation['score']:.2f}")
    print(f"✅ Assistant Pass: {assistant_validation['passed']}")
    print(f"📝 Details: {assistant_validation['details']}")
    
    # Overall result
    overall_pass = teacher_validation["passed"] and assistant_validation["passed"]
    results["overall_pass"] = overall_pass
    
    print(f"\n🎯 OVERALL RESULT:")
    print(f"{'🎉 PASS' if overall_pass else '❌ NEEDS IMPROVEMENT'}")
    
    if overall_pass:
        print("✅ Ready for mentor demonstration!")
    else:
        print("🔄 Consider additional training or prompt tuning")
    
    return results

def save_validation_results(results, filename="mentor_validation_results.json"):
    """Save validation results"""
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"💾 Results saved to: {filename}")

# Test functions for demonstration
def demo_validation():
    """Demo validation with mock responses"""
    def mock_teacher_response(prompt):
        return """**Windows Event 4625: Failed Logon Analysis**

**(1) Meaning & Key Fields:**
Event 4625 indicates authentication failure. Key fields:
- **LogonType**: Authentication method (2=Interactive, 3=Network, 4=Batch)  
- **AccountName**: Target account attempting authentication
- **IpAddress**: Source IP address of authentication attempt

**(2) Common False Positives:**
- Service account password expiration
- Users returning from vacation with forgotten passwords
- Caps Lock enabled during authentication
- Time synchronization issues between domain controllers

**(3) Escalation Threshold:**
- Alert on >5 failures per user per 5 minutes
- Escalate >10 failures from single IP in 1 minute
- Critical: >20 failures across multiple accounts

**MITRE ATT&CK Mapping:**
Maps to **T1110 (Brute Force)** - adversaries attempting to gain access through repeated authentication attempts.

**Sources:** MITRE ATT&CK Framework, NIST SP 800-53"""
    
    def mock_assistant_response(prompt):
        return """**1. detection_outline:**
SIEM-agnostic: Monitor authentication failures >5 per source in 5min window
Splunk SPL: `index=security EventCode=4625 | stats count by src_ip | where count > 5`

**2. playbook_choice:**
Playbook: PB-AUTH-001 (Brute Force Response)
Preconditions: External IP source, >10 failures
Rollback: Remove IP blocks after 24h if no further activity

**3. limacharlie_actions:**
```yaml
- action: isolate_host
  approval_required: true
  duration: 3600
- action: block_ip
  approval_required: true
  scope: organization
```

**4. team_update:**
🚨 **SECURITY ALERT**: Brute force detected from 203.0.113.100
📊 15 failed logons targeting admin accounts  
🎯 Containment actions pending approval
👤 Analyst: {{username}}
🔗 Incident: INC-{{timestamp}}

**Citations:** MITRE ATT&CK T1110, Windows Security Event Reference"""
    
    # Run validation with mock functions
    if mock_teacher_response.__name__ == "mock_teacher_response":
        print("🧪 Running demo validation with mock responses...")
        
        teacher_val = validate_teacher_response(mock_teacher_response(""))
        assistant_val = validate_assistant_response(mock_assistant_response(""))
        
        print(f"📚 Teacher validation: {teacher_val['passed']} ({teacher_val['score']:.2f})")
        print(f"🤖 Assistant validation: {assistant_val['passed']} ({assistant_val['score']:.2f})")

if __name__ == "__main__":
    demo_validation()