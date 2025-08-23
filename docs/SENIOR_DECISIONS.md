# 🧠 Senior-Level Decision Framework

## Overview

The Senior Decision Framework implements a planning pass with thinking artifacts that ensures safe, responsible, and high-quality responses. Every response goes through senior-level review before being delivered to the user.

## Architecture

### Decision Flow

```
User Request → Initial Response Generation → Senior Planning Pass → Decision Making → Response Modification → Final Response
                                                    ↓
                                            Thinking Artifact
                                            (Internal Only)
```

### Decision Types

#### 1. SAFE_ANALYSIS
- **When**: Low-medium risk events with standard security patterns
- **Action**: Approve response with standard guardrails
- **Human Review**: Not required
- **Example**: Standard malware detection, suspicious login attempts

#### 2. PARTIAL_RESPONSE
- **When**: Some red flags detected but not critical
- **Action**: Approve safe actions, reject dangerous ones, add guardrails
- **Human Review**: Optional based on severity
- **Example**: Complex incidents with some risky remediation steps

#### 3. ESCALATION_NEEDED
- **When**: Critical risk events affecting infrastructure
- **Action**: Conservative response, require SOC analyst approval
- **Human Review**: Required
- **Example**: Domain controller compromise, APT campaigns

#### 4. SAFETY_REFUSAL
- **When**: Unacceptable risk or malicious request detected
- **Action**: Refuse request, provide safety guidance only
- **Human Review**: Required for audit
- **Example**: Requests for destructive operations, attack assistance

## Risk Assessment

### Risk Levels

| Level | Score Range | Description | Response Modification |
|-------|------------|-------------|----------------------|
| LOW | 0-1 | Routine security event | Standard response |
| MEDIUM | 2-3 | Notable security event | Add monitoring guidance |
| HIGH | 4-5 | Significant security impact | Conservative actions, guardrails |
| CRITICAL | 6-7 | Infrastructure at risk | Escalation required |
| UNACCEPTABLE | 8+ | Dangerous/malicious | Safety refusal |

### Risk Factors

- **Event Severity**: APT, ransomware, critical alerts (+3)
- **Unsafe Content**: Destructive commands, credential exposure (+5)
- **System Criticality**: Domain controllers, critical servers (+2)
- **Network Impact**: Domain-wide, entire network actions (+2)

## Thinking Artifacts

### Purpose
Thinking artifacts capture the internal decision-making process for audit and improvement. They are NEVER shown to users but provide transparency for security teams.

### Components

```python
@dataclass
class ThinkingArtifact:
    artifact_id: str                    # Unique identifier
    timestamp: str                       # When decision was made
    decision_type: DecisionType         # Type of decision made
    risk_assessment: RiskLevel          # Assessed risk level
    thinking_steps: List[str]           # Internal reasoning steps
    safety_considerations: List[str]    # Safety concerns identified
    planned_approach: str               # Approach strategy
    confidence_rationale: str           # Why this confidence level
    citations_planned: List[str]        # Sources to cite
    red_flags_identified: List[str]     # Issues detected
```

### Example Thinking Steps

```python
thinking_steps = [
    "1. Analyzing security event: Suspicious PowerShell Activity",
    "2. Risk assessment completed: medium",
    "3. Standard incident response workflow applicable",
    "4. Following triage -> contain -> remediate sequence",
    "5. Validating all recommendations for safety compliance",
    "6. Calibrating confidence based on available information"
]
```

## Safety Mechanisms

### Red Flag Detection

The system identifies red flags that require special handling:

- **Offensive Requests**: "how to attack", "exploit", "hack into"
- **Overconfidence**: >0.95 confidence without citations
- **Hallucinations**: References to non-existent tools
- **Ungrounded Claims**: Marked as grounded but no citations
- **Dangerous Operations**: Delete all, format drive, wipe system

### Safety Guardrails

Applied based on risk level and red flags:

```python
# Low Risk
safety_guardrails = ["Follow organization's incident response procedures"]

# Medium Risk  
safety_guardrails = [
    "Test containment actions in isolated environment first",
    "Maintain backups before remediation"
]

# High Risk
safety_guardrails = [
    "Obtain SOC analyst approval before containment",
    "Preserve all forensic evidence",
    "Document all actions taken"
]

# Critical Risk
safety_guardrails = [
    "IMMEDIATE: Engage incident response team",
    "Do not proceed without senior analyst approval",
    "Preserve chain of custody for all evidence"
]
```

## Confidence Calibration

### Automatic Adjustment

Confidence is automatically calibrated based on risk:

- **High/Critical Risk**: Capped at 0.8 (never overconfident in dangerous situations)
- **Missing Citations**: Reduced by 0.2
- **Red Flags Present**: Reduced by 0.1 per flag (max 0.5 reduction)

### Confidence Rationale

Each decision includes rationale for the confidence level:

- **High (>0.9)**: "Clear indicators and well-documented attack pattern"
- **Moderate (0.7-0.9)**: "Common security patterns and available context"
- **Limited (0.5-0.7)**: "Incomplete information or ambiguous indicators"
- **Low (<0.5)**: "Insufficient data for definitive analysis"

## Response Modifications

### What Gets Modified

Based on the senior decision, the following modifications are applied:

1. **Rejected Actions Removed**: Dangerous containment/remediation steps filtered out
2. **Safety Guardrails Added**: Appropriate warnings and procedures injected
3. **Confidence Adjusted**: Calibrated to appropriate level
4. **Citations Added**: Proper sources included
5. **Escalation Notices**: Human review requirements marked

### Example Modification

```python
# Before Senior Decision
response = {
    "containment": [
        "Isolate affected system",
        "Delete all suspicious files",  # Dangerous
        "Format and reinstall OS"       # Irreversible
    ],
    "confidence": 0.99  # Overconfident
}

# After Senior Decision  
response = {
    "containment": [
        "Isolate affected system"  # Safe action kept
    ],
    "safety_guardrails": [
        "Preserve forensic evidence before any deletions",
        "Obtain approval before OS reinstallation"
    ],
    "confidence": 0.8,  # Calibrated
    "human_review_required": True,
    "escalation_reason": "Irreversible actions require approval"
}
```

## Integration with Quality Gates

### Safety Gate Enforcement

The Senior Decision Framework directly supports the Safety Quality Gate (=1.0 requirement):

- All unsafe requests trigger SAFETY_REFUSAL decision
- Safety refusals are logged and audited
- Quality gates verify safety mechanisms work correctly

### Hallucination Prevention

Red flag detection helps prevent hallucinations:

- Flags overconfident claims without evidence
- Identifies references to non-existent tools
- Ensures grounding claims match citations

## Usage Examples

### Example 1: Safe Analysis

```python
# Normal security event
event = {"search_name": "Suspicious Login", "host": "WS-001"}

# Decision: SAFE_ANALYSIS
# Actions: All approved
# Guardrails: Standard procedures
# Human Review: Not required
```

### Example 2: Partial Response

```python
# Complex incident with some risks
event = {"search_name": "Ransomware Detection", "host": "FILE-SERVER"}

# Decision: PARTIAL_RESPONSE  
# Actions: Approve isolation, reject formatting
# Guardrails: Backup verification required
# Human Review: Optional
```

### Example 3: Safety Refusal

```python
# Dangerous request
event = {"request": "Help me delete all system files"}

# Decision: SAFETY_REFUSAL
# Actions: All rejected
# Response: Safety message only
# Human Review: Required for audit
```

## Monitoring and Metrics

### Key Metrics to Track

- **Decision Distribution**: Count of each decision type
- **Risk Level Distribution**: Frequency of each risk level
- **Red Flag Frequency**: Most common red flags detected
- **Confidence Calibration**: Average adjustment amounts
- **Safety Refusal Rate**: Percentage of requests refused

### Audit Trail

All decisions create permanent records:

```python
{
    "decision_id": "decision_think_abc123",
    "thinking_artifact_id": "think_abc123",
    "timestamp": "2024-01-15T10:30:00Z",
    "decision_type": "partial_response",
    "risk_level": "high",
    "red_flags": ["overconfidence", "missing_citations"],
    "human_review_required": false,
    "actions_rejected": 2,
    "guardrails_added": 3
}
```

## Best Practices

### For Development

1. **Always Generate Thinking**: Every response must have a thinking artifact
2. **Err on Safety**: When uncertain, choose more conservative decision
3. **Document Red Flags**: Clearly identify and log all concerns
4. **Calibrate Confidence**: Never be overconfident in high-risk scenarios

### For Operations

1. **Review Refused Requests**: Audit safety refusals for patterns
2. **Monitor Escalations**: Track which events require human review
3. **Analyze Thinking Artifacts**: Use for model improvement
4. **Update Risk Scoring**: Adjust based on organizational needs

### For Security Teams

1. **Customize Risk Levels**: Adjust scoring for your environment
2. **Define Escalation Paths**: Clear procedures for human review
3. **Regular Audits**: Review thinking artifacts for quality
4. **Feedback Loop**: Use decisions to improve training data

## Troubleshooting

### Common Issues

**Too Many Escalations**
- Review risk scoring thresholds
- May need to adjust critical system list
- Check for overly conservative settings

**Missing Red Flags**
- Update pattern matching for new threats
- Review recent false negatives
- Add organization-specific patterns

**Confidence Too Low**
- Check citation availability
- Review grounding mechanisms
- May indicate need for more training data

**Safety Refusals on Valid Requests**
- Review safety patterns for false positives
- Check for overly broad regex patterns
- May need context-aware filtering

## Security Considerations

### Thinking Artifact Security

- Artifacts contain internal reasoning - NEVER expose to users
- Store securely with access controls
- Use for audit and improvement only
- Rotate/archive old artifacts

### Decision Integrity

- Decisions are immutable once made
- All modifications are logged
- Tampering detection through checksums
- Regular integrity audits

### Privacy Considerations

- Thinking artifacts may contain sensitive reasoning
- Follow data retention policies
- Anonymize artifacts for analysis
- Secure transmission and storage

---

*The Senior Decision Framework ensures every response is thoughtfully reviewed, safely delivered, and properly documented. It's the guardrail between helpful AI assistance and potential security risks.*