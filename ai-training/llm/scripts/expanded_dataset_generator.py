#!/usr/bin/env python3
"""
Expanded Cybersecurity Dataset Generator
Following mentor's requirements: 100+ examples for 4625/T1110 + LC Replay
"""

import json
import os
from datetime import datetime
from typing import Dict, List

class ExpandedDatasetGenerator:
    """Generate comprehensive dataset following mentor's specifications"""
    
    def __init__(self):
        self.examples = []
    
    def generate_4625_teacher_examples(self) -> List[Dict]:
        """Generate teacher examples for Windows 4625 events"""
        examples = []
        
        # Basic 4625 explanation variations
        base_scenarios = [
            {
                "context": "Multiple failed logons from external IP",
                "details": "EventCode 4625, LogonType 3, 15 failures in 2 minutes"
            },
            {
                "context": "Service account authentication failures", 
                "details": "EventCode 4625, LogonType 4, expired password"
            },
            {
                "context": "Interactive logon failures during off-hours",
                "details": "EventCode 4625, LogonType 2, weekend activity"
            },
            {
                "context": "Network logon failures with geographic anomaly",
                "details": "EventCode 4625, LogonType 3, source from different country"
            }
        ]
        
        for i, scenario in enumerate(base_scenarios):
            examples.append({
                "instruction": f"Explain Windows Event 4625 (Failed Logon) analysis for this security scenario. Include key fields, false positive patterns, and ATT&CK mapping.",
                "input": f"{scenario['context']}: {scenario['details']}",
                "output": self._generate_4625_explanation(scenario),
                "tags": ["Windows:4625", "ATTACK:T1110", "Teacher", "Authentication"]
            })
            
            # Generate variations focusing on different aspects
            examples.extend([
                {
                    "instruction": f"Focus on false positive analysis for this 4625 event pattern.",
                    "input": f"Security analysts seeing alerts for: {scenario['details']}",
                    "output": self._generate_fp_analysis(scenario),
                    "tags": ["Windows:4625", "FalsePositive", "Teacher", "Tuning"]
                },
                {
                    "instruction": f"Provide escalation thresholds and detection tuning for this logon failure pattern.",
                    "input": f"SOC needs detection rules for: {scenario['context']}",
                    "output": self._generate_escalation_guidance(scenario),
                    "tags": ["Windows:4625", "DetectionTuning", "Teacher", "SOC"]
                }
            ])
        
        return examples
    
    def generate_4625_assistant_examples(self) -> List[Dict]:
        """Generate assistant examples for 4625 response actions"""
        examples = []
        
        scenarios = [
            {
                "incident": "Confirmed brute force attack from 192.168.1.100",
                "severity": "High",
                "accounts": "admin, svcAccount, testuser"
            },
            {
                "incident": "Possible credential stuffing against web application",
                "severity": "Medium", 
                "accounts": "multiple user accounts"
            },
            {
                "incident": "Service account lockout causing application failures",
                "severity": "Medium",
                "accounts": "svc-webapp, svc-db"
            }
        ]
        
        for scenario in scenarios:
            examples.append({
                "instruction": f"Propose comprehensive response actions for this authentication security incident. Include SIEM queries, playbook selection, LimaCharlie actions, and stakeholder communication.",
                "input": f"Incident: {scenario['incident']}. Severity: {scenario['severity']}. Affected accounts: {scenario['accounts']}",
                "output": self._generate_assistant_response(scenario),
                "tags": ["Windows:4625", "ATTACK:T1110", "Assistant", "SOAR:playbook", "Response"]
            })
        
        return examples
    
    def generate_t1110_variations(self) -> List[Dict]:
        """Generate T1110 (Brute Force) technique variations"""
        examples = []
        
        sub_techniques = {
            "T1110.001": {
                "name": "Password Guessing",
                "description": "Common password attempts against known accounts"
            },
            "T1110.002": {
                "name": "Password Cracking", 
                "description": "Offline password hash cracking"
            },
            "T1110.003": {
                "name": "Password Spraying",
                "description": "Low-volume password attempts across many accounts"
            },
            "T1110.004": {
                "name": "Credential Stuffing",
                "description": "Using leaked credentials across multiple services"
            }
        }
        
        for tid, technique in sub_techniques.items():
            examples.extend([
                {
                    "instruction": f"Explain MITRE ATT&CK sub-technique {tid} ({technique['name']}) with detection strategies and response procedures.",
                    "input": f"SOC analyst needs to understand {technique['description'].lower()}",
                    "output": self._generate_subtechnique_explanation(tid, technique),
                    "tags": [f"ATTACK:{tid}", "Teacher", "MITRE"]
                },
                {
                    "instruction": f"Create detection rules and hunting queries for {tid} ({technique['name']}).",
                    "input": f"Need to detect {technique['description'].lower()} in enterprise environment",
                    "output": self._generate_detection_rules(tid, technique),
                    "tags": [f"ATTACK:{tid}", "DetectionRules", "Hunting"]
                }
            ])
        
        return examples
    
    def generate_limacharlie_examples(self) -> List[Dict]:
        """Generate LimaCharlie D&R and Replay examples"""
        examples = []
        
        lc_scenarios = [
            {
                "type": "D&R Rule",
                "purpose": "Detect suspicious authentication patterns",
                "event_type": "NEW_PROCESS"
            },
            {
                "type": "Replay Analysis",
                "purpose": "Investigate failed logon timeline",
                "event_type": "NETWORK_SUMMARY"
            },
            {
                "type": "Response Action",
                "purpose": "Automated containment for confirmed brute force",
                "event_type": "ISOLATION"
            }
        ]
        
        for scenario in lc_scenarios:
            examples.extend([
                {
                    "instruction": f"Explain LimaCharlie {scenario['type']} for authentication security monitoring.",
                    "input": f"Need to {scenario['purpose'].lower()} using LimaCharlie capabilities",
                    "output": self._generate_lc_explanation(scenario),
                    "tags": ["LimaCharlie", "Teacher", "EDR", scenario["type"].replace(" ", "")]
                },
                {
                    "instruction": f"Create LimaCharlie {scenario['type']} configuration with approval workflow.",
                    "input": f"SOC needs automated {scenario['purpose'].lower()} with human oversight",
                    "output": self._generate_lc_config(scenario),
                    "tags": ["LimaCharlie", "Assistant", "Configuration", "Approval"]
                }
            ])
        
        return examples
    
    def generate_splunk_examples(self) -> List[Dict]:
        """Generate Splunk ES investigation examples"""
        examples = []
        
        splunk_use_cases = [
            {
                "scenario": "Authentication failure correlation",
                "data_model": "Authentication",
                "goal": "Identify brute force patterns"
            },
            {
                "scenario": "Notable event investigation",
                "data_model": "Risk", 
                "goal": "Escalate high-confidence incidents"
            },
            {
                "scenario": "Threat hunting dashboard",
                "data_model": "Network_Sessions",
                "goal": "Proactive authentication anomaly detection"
            }
        ]
        
        for use_case in splunk_use_cases:
            examples.extend([
                {
                    "instruction": f"Explain Splunk ES investigation workflow for {use_case['scenario']}.",
                    "input": f"Security analyst investigating {use_case['goal'].lower()} using {use_case['data_model']} data model",
                    "output": self._generate_splunk_workflow(use_case),
                    "tags": ["Splunk", "Teacher", "Investigation", use_case["data_model"]]
                },
                {
                    "instruction": f"Create Splunk search and correlation rule for {use_case['scenario']}.",
                    "input": f"Need automated detection for {use_case['goal'].lower()}",
                    "output": self._generate_splunk_search(use_case),
                    "tags": ["Splunk", "DetectionRules", "Correlation", use_case["data_model"]]
                }
            ])
        
        return examples
    
    def _generate_4625_explanation(self, scenario: Dict) -> str:
        return f"""**Windows Event 4625: Failed Logon Analysis**

**Event Overview:**
{scenario['context']} - {scenario['details']}

**Key Fields Analysis:**
- **LogonType**: Indicates authentication method (2=Interactive, 3=Network, 4=Batch, 5=Service)
- **FailureReason**: 0xC000006D (bad username/password), 0xC000006A (wrong password), 0xC000006E (account restriction)
- **IpAddress**: Source of authentication attempt (key for geographic analysis)
- **WorkstationName**: Client system making the request

**ATT&CK Mapping:**
- **Primary**: T1110 (Brute Force)
- **Sub-techniques**: T1110.001 (Password Guessing), T1110.003 (Password Spraying)

**False Positive Patterns:**
- Service account password expiration causing batch job failures
- Users returning from vacation with forgotten passwords
- Time synchronization issues between domain controllers
- Legitimate applications with retry mechanisms

**Escalation Thresholds:**
- **Low**: 3-5 failures per user per hour
- **Medium**: 10+ failures from single IP in 5 minutes  
- **High**: 20+ failures across multiple accounts
- **Critical**: Successful logon after failed attempts from external IP

**Investigation Steps:**
1. Verify source IP legitimacy and geolocation
2. Check for successful 4624 events from same source
3. Correlate with network traffic and process execution
4. Review account usage patterns and privileges"""

    def _generate_fp_analysis(self, scenario: Dict) -> str:
        return f"""**False Positive Analysis: Event 4625**

**Scenario Context:** {scenario['context']}

**Common False Positive Sources:**

**1. Service Account Issues:**
- Password expiration on scheduled tasks
- Service startup failures after password changes
- Cluster service account synchronization delays

**2. Application Behavior:**
- Web applications with connection pooling
- Database connection retry mechanisms
- Load balancer health checks with authentication

**3. User Behavior:**
- Password policy changes requiring resets
- Caps Lock enabled during authentication
- Copy/paste errors with special characters
- VPN client automatic reconnection attempts

**4. Infrastructure Issues:**
- Time skew between client and domain controller
- Network latency causing timeout failures
- DNS resolution failures for authentication servers

**Filtering Recommendations:**
```spl
index=security EventCode=4625
| eval is_service_account=if(match(Account_Name, "^svc-|^service-"), 1, 0)
| eval is_machine_account=if(like(Account_Name, "%$"), 1, 0)  
| eval failure_reason=case(
    Status="0xC000006D", "Bad username or password",
    Status="0xC000006A", "Wrong password", 
    Status="0xC000006E", "Account restriction")
| where is_service_account=0 AND is_machine_account=0
| stats count by Account_Name, Computer_Name, failure_reason
| where count > 3
```

**Tuning Strategy:**
- Whitelist known service account sources
- Implement time-based thresholds (higher during business hours)
- Use account type classification for risk scoring"""

    def _generate_escalation_guidance(self, scenario: Dict) -> str:
        return f"""**Escalation Thresholds: Authentication Failures**

**Scenario:** {scenario['context']}

**Detection Thresholds:**

**Tier 1 - Informational (No Action):**
- 1-2 failures per user per hour
- Known service account sources
- During maintenance windows

**Tier 2 - Low Priority Investigation:**
- 3-5 failures per user per hour
- New geographic locations for known users
- Outside business hours for standard accounts

**Tier 3 - Medium Priority Response:**
- 6-10 failures per user in 5 minutes
- Multiple accounts from single external IP
- Privileged account targeting

**Tier 4 - High Priority Incident:**
- 11+ failures per user in 5 minutes
- 5+ different accounts from single source
- Successful logon after multiple failures
- Administrative account compromise indicators

**Tier 5 - Critical Security Incident:**
- 20+ accounts targeted from single source
- Privileged account successful authentication after failures
- Pattern matching known attack campaigns
- Concurrent with other suspicious activities

**Automated Response Actions:**
- **Low**: Log and monitor
- **Medium**: Alert SOC team
- **High**: Block source IP, alert CISO
- **Critical**: Isolate systems, activate incident response

**Detection Tuning:**
```spl
| eval risk_score=case(
    account_type="admin", failure_count * 3,
    source_external=1, failure_count * 2,
    business_hours=0, failure_count * 1.5,
    1=1, failure_count)
| eval alert_level=case(
    risk_score > 50, "Critical",
    risk_score > 25, "High", 
    risk_score > 10, "Medium",
    1=1, "Low")
```"""

    def _generate_assistant_response(self, scenario: Dict) -> str:
        return f"""**SOAR Response Plan: Authentication Incident**

**Incident Assessment:**
{scenario['incident']} (Severity: {scenario['severity']})
Affected accounts: {scenario['accounts']}

**Detection Outline:**
```spl
index=security EventCode=4625 
| eval incident_id="INC-$(now())"
| stats count, dc(Account_Name) as unique_accounts by src_ip
| where count > 10 OR unique_accounts > 5
| eval severity="{scenario['severity']}"
```

**Playbook Selection:**
- **Primary**: PB-AUTH-001 (Brute Force Response)
- **Secondary**: PB-ACCOUNT-002 (Account Compromise Investigation)
- **Estimated Duration**: 15-30 minutes

**LimaCharlie Actions (Approval Required):**
```yaml
response_actions:
  - action: isolate_host
    target: source_systems
    duration: 3600
    approval_required: true
    justification: "Confirmed brute force attack"
    
  - action: block_network
    target: source_ip_ranges  
    duration: 7200
    approval_required: true
    justification: "External attack source"

  - action: monitor_accounts
    target: affected_accounts
    duration: 86400
    approval_required: false
    justification: "Enhanced monitoring"
```

**Stakeholder Communication:**

**Slack Update:**
```
🛡️ SECURITY INCIDENT: {scenario['incident']}
📊 Severity: {scenario['severity']}
👥 Affected: {scenario['accounts']}
🎯 Playbook: PB-AUTH-001 activated
⏰ ETA: 30 minutes
👤 Analyst: {{analyst_name}}
🔗 Incident: INC-{{timestamp}}

Next Update: 15 minutes
```

**Email Notification:**
- **To**: CISO, IT Security Team, Affected Account Owners
- **Subject**: Security Incident - Authentication Attack Detected
- **Priority**: {scenario['severity']}

**Approval Required Actions:**
1. ✅ Network isolation of source systems
2. ✅ IP blocking at firewall level
3. ⚠️ Account lockdown (business impact assessment needed)

**Timeline:**
- T+0: Incident detected and assessed
- T+5: Immediate containment actions
- T+15: Stakeholder notification complete
- T+30: Full response plan executed"""

    def _generate_subtechnique_explanation(self, tid: str, technique: Dict) -> str:
        return f"""**MITRE ATT&CK {tid}: {technique['name']}**

**Technique Description:**
{technique['description']}

**Common Attack Patterns:**
- Automated credential testing tools (Hydra, Medusa, Burp Intruder)
- Custom scripts with password lists
- Cloud-based distributed attacks
- Mobile app credential validation bypass

**Detection Strategies:**

**Behavioral Indicators:**
- Consistent timing patterns between attempts
- Sequential account targeting
- Use of common password lists
- Low success rate with high volume

**Technical Indicators:**
- Multiple 4625 events with varied account names
- Consistent source IP or user agent patterns
- Network traffic patterns (timing, frequency)
- Process execution anomalies

**Detection Rules:**
```spl
index=security EventCode=4625
| bucket _time span=5m
| stats dc(Account_Name) as unique_accounts, count as attempts by src_ip, _time
| where unique_accounts > 5 AND attempts > 20
| eval technique_id="{tid}"
| eval confidence=case(
    attempts > 100, "High",
    attempts > 50, "Medium", 
    1=1, "Low")
```

**Response Procedures:**

**Immediate (0-5 minutes):**
1. Block source IP at perimeter
2. Monitor for successful authentications
3. Alert security team

**Short-term (5-30 minutes):**
1. Analyze attack patterns and scope
2. Check for credential compromise
3. Implement additional monitoring

**Long-term (30+ minutes):**
1. Password policy review
2. Account lockout tuning
3. User awareness training

**Mitigation Controls:**
- Multi-factor authentication implementation
- Account lockout policies
- IP-based access controls
- Behavioral analytics deployment"""

    def _generate_detection_rules(self, tid: str, technique: Dict) -> str:
        return f"""**Detection Rules: {tid} ({technique['name']})**

**Splunk Detection Rule:**
```spl
index=security sourcetype=WinEventLog:Security EventCode=4625
| eval attack_technique="{tid}"
| bucket _time span=5m
| stats 
    count as failure_count,
    dc(Account_Name) as unique_accounts,
    values(Account_Name) as targeted_accounts,
    dc(Computer_Name) as unique_hosts
    by src_ip, _time
| where failure_count > 15 AND unique_accounts > 3
| eval severity=case(
    failure_count > 100, "Critical",
    failure_count > 50, "High",
    failure_count > 25, "Medium",
    1=1, "Low")
| eval description="{technique['description']}"
| table _time, src_ip, failure_count, unique_accounts, severity, description
```

**Sigma Rule:**
```yaml
title: {technique['name']} Detection
id: {tid.lower()}-detection-rule
status: experimental
description: Detects {technique['description'].lower()}
logsource:
    category: authentication
    product: windows
detection:
    selection:
        EventID: 4625
    timeframe: 5m
    condition: 
        - selection | count() > 15
        - selection | count(Account_Name) > 3
falsepositives:
    - Service account authentication issues
    - Password policy changes
    - Network connectivity problems
level: medium
tags:
    - attack.{tid.lower()}
    - attack.credential_access
```

**LimaCharlie D&R Rule:**
```yaml
detect:
    event: LOG
    op: and
    rules:
        - op: is
          path: event/EVENT/System/EventID
          value: 4625
        - op: exists  
          path: event/EVENT/EventData/IpAddress

respond:
    - action: report
      name: {tid.lower()}_bruteforce
      metadata:
        technique: "{tid}"
        description: "{technique['description']}"
    
    - action: extension_request
      extension: logging
      request: track_ip
      params:
        ip: "{{ .event.EVENT.EventData.IpAddress }}"
        duration: 3600
```

**Hunting Queries:**

**PowerShell (Active Directory):**
```powershell
# Hunt for {technique['name']} patterns
Get-WinEvent -FilterHashtable @{{LogName='Security';ID=4625}} -MaxEvents 1000 |
Where-Object {{$_.TimeCreated -gt (Get-Date).AddHours(-1)}} |
Group-Object {{$_.Properties[19].Value}} |
Where-Object {{$_.Count -gt 10}} |
Select-Object Name, Count, @{{n='Accounts';e={{$_.Group.Properties[5].Value | Sort-Object -Unique}}}}
```

**KQL (Sentinel):**
```kql
SecurityEvent
| where TimeGenerated > ago(1h)
| where EventID == 4625
| extend SourceIP = IpAddress
| summarize 
    FailureCount = count(),
    UniqueAccounts = dcount(Account),
    AccountList = make_set(Account)
    by SourceIP, bin(TimeGenerated, 5m)
| where FailureCount > 15 and UniqueAccounts > 3
| extend TechniqueID = "{tid}"
```"""

    def _generate_lc_explanation(self, scenario: Dict) -> str:
        return f"""**LimaCharlie {scenario['type']}: Authentication Security**

**Purpose:** {scenario['purpose']}

**LimaCharlie Capabilities Overview:**

**Detection & Response (D&R):**
- Real-time event processing and correlation
- Custom detection rules with flexible response actions
- Integration with external systems and threat intelligence
- Approval workflows for high-impact responses

**Replay & Investigation:**
- Historical event reconstruction and timeline analysis
- Full system state capture at time of incidents
- Interactive investigation with filtering and correlation
- Export capabilities for forensic analysis

**Response Orchestration:**
- Automated containment and isolation actions
- Custom response scripts and integrations
- Human approval gates for critical decisions
- Audit logging of all response activities

**Configuration Example:**

**D&R Rule Structure:**
```yaml
rules:
  - name: authentication_monitoring
    detect:
      event: {scenario['event_type']}
      op: and
      rules:
        - op: contains
          path: event/EVENT_TYPE
          value: authentication_failure
    respond:
      - action: report
        name: auth_failure_detected
      - action: extension_request
        extension: chronicle
        request: enrich_event
```

**Key Benefits:**
- **Real-time Processing**: Sub-second detection and response
- **Cloud-native Architecture**: Scalable and resilient
- **API-first Design**: Easy integration with SOAR platforms
- **Comprehensive Logging**: Full audit trail for compliance

**Integration Points:**
- **SIEM**: Send enriched events to Splunk/Sentinel
- **SOAR**: Trigger playbooks and orchestrate responses
- **Threat Intelligence**: Correlate with IOCs and campaigns
- **Communication**: Slack/Teams notifications with context

**Best Practices:**
1. Start with detection-only rules before enabling responses
2. Use approval workflows for high-impact actions
3. Implement proper logging and monitoring of the platform itself
4. Regular rule testing and validation"""

    def _generate_lc_config(self, scenario: Dict) -> str:
        return f"""**LimaCharlie Configuration: {scenario['type']}**

**Objective:** {scenario['purpose']} with human oversight

**Complete D&R Rule:**
```yaml
rules:
  - name: auth_security_{scenario['type'].lower().replace(' ', '_')}
    detect:
      event: LOG
      op: and  
      rules:
        - op: is
          path: event/EVENT/System/EventID
          value: 4625
        - op: exists
          path: event/EVENT/EventData/IpAddress
        - op: not
          path: event/EVENT/EventData/IpAddress
          value: "127.0.0.1"
    
    respond:
      # Phase 1: Immediate reporting
      - action: report
        name: failed_authentication
        metadata:
          severity: medium
          category: authentication
          technique: T1110
          
      # Phase 2: Automated analysis
      - action: extension_request
        extension: threat_intel
        request: check_ip_reputation
        params:
          ip: "{{ .event.EVENT.EventData.IpAddress }}"
          
      # Phase 3: Conditional response (approval required)
      - action: task_create
        name: evaluate_blocking_action
        params:
          description: "Review failed authentication from {{ .event.EVENT.EventData.IpAddress }}"
          severity: medium
          auto_approve: false
          escalate_after: 300  # 5 minutes
```

**Approval Workflow Integration:**
```yaml
approval_config:
  - rule_name: auth_security_response
    actions_requiring_approval:
      - isolation
      - network_block
      - account_disable
    
    approval_matrix:
      - severity: low
        approvers: ["soc_analyst", "security_lead"]
        timeout: 1800  # 30 minutes
      - severity: medium  
        approvers: ["security_lead", "ciso"]
        timeout: 900   # 15 minutes
      - severity: high
        approvers: ["ciso", "it_director"]
        timeout: 300   # 5 minutes

    notification_channels:
      - type: slack
        channel: "#security-alerts"
        template: |
          🛡️ **Approval Required**: {{ .rule_name }}
          📊 **Severity**: {{ .severity }}
          🎯 **Action**: {{ .requested_action }}
          💬 **Context**: {{ .event_summary }}
          ⏰ **Timeout**: {{ .approval_timeout }}
```

**Response Action Templates:**
```yaml
response_templates:
  isolation:
    action: isolate_host
    params:
      duration: 3600  # 1 hour default
      reason: "Authentication security incident"
      allow_list: ["management_subnet"]
      
  ip_blocking:
    action: network_isolation  
    params:
      target_type: "ip_address"
      duration: 7200  # 2 hours default
      scope: "organization_wide"
      
  account_monitoring:
    action: extension_request
    extension: user_behavior_analytics
    request: enhanced_monitoring
    params:
      duration: 86400  # 24 hours
      alert_threshold: "low"
```

**Deployment Steps:**
1. **Test Phase**: Deploy rule with report-only actions
2. **Validation**: Verify detection accuracy over 24-48 hours  
3. **Gradual Rollout**: Enable automated responses for low-risk actions
4. **Full Deployment**: Activate approval workflow for high-impact responses

**Monitoring and Metrics:**
- Rule trigger frequency and accuracy
- Approval response times
- False positive rates
- Response effectiveness metrics"""

    def _generate_splunk_workflow(self, use_case: Dict) -> str:
        return f"""**Splunk ES Investigation Workflow: {use_case['scenario']}**

**Objective:** {use_case['goal']} using {use_case['data_model']} data model

**Investigation Phases:**

**Phase 1: Initial Assessment (2-3 minutes)**
```spl
| datamodel {use_case['data_model']} {use_case['data_model']} search
| search earliest=-1h
| stats count by src, dest, user
| sort - count
| head 20
```

**Phase 2: Pattern Analysis (5-10 minutes)**  
```spl
| datamodel {use_case['data_model']} {use_case['data_model']} search
| bucket _time span=5m
| stats 
    count as events,
    dc(user) as unique_users,
    dc(src) as unique_sources
    by _time, action
| eval pattern_score = events * unique_users * unique_sources
| sort - pattern_score
```

**Phase 3: Risk Correlation (5-10 minutes)**
```spl
| datamodel Risk All_Risk search 
| search risk_object_type="user" OR risk_object_type="system"
| join risk_object 
    [| datamodel {use_case['data_model']} {use_case['data_model']} search 
     | eval risk_object=coalesce(src, user, dest)]
| stats sum(risk_score) as total_risk by risk_object
| where total_risk > 50
```

**Phase 4: Timeline Reconstruction (10-15 minutes)**
```spl
| datamodel {use_case['data_model']} {use_case['data_model']} search
| search user="$target_user$" OR src="$target_host$"
| eval event_category=case(
    action="failure", "Authentication Failure",
    action="success", "Authentication Success", 
    1=1, "Other")
| table _time, user, src, dest, action, event_category
| sort _time
```

**Notable Event Creation:**
```spl
| eval notable_title="{use_case['scenario']} - " + user
| eval notable_description="Investigation of " + "{use_case['goal'].lower()}"
| eval urgency=case(
    total_risk > 80, "high",
    total_risk > 40, "medium",
    1=1, "low")
| eval security_domain="authentication"
| sendalert notable param.title="$notable_title$" param.description="$notable_description$"
```

**Investigation Checklist:**
- [ ] Verify user account legitimacy and current status
- [ ] Check for successful authentications from same source
- [ ] Correlate with network traffic and endpoint activity
- [ ] Review historical authentication patterns for baseline
- [ ] Check threat intelligence feeds for known bad IPs
- [ ] Validate business justification for access patterns

**Documentation Template:**
```
Investigation: {use_case['scenario']}
Date/Time: {{ current_timestamp }}
Analyst: {{ analyst_name }}

Summary:
- Scope: {{ investigation_scope }}
- Findings: {{ key_findings }}
- Risk Level: {{ assessed_risk }}

Actions Taken:
- {{ actions_performed }}

Recommendations:
- {{ security_recommendations }}

Follow-up Required:
- {{ follow_up_tasks }}
```

**Integration Points:**
- **SOAR Platform**: Auto-create investigation tasks
- **Threat Intelligence**: Enrich with external IOCs
- **Communication**: Stakeholder notification workflows
- **Documentation**: Case management system integration"""

    def _generate_splunk_search(self, use_case: Dict) -> str:
        return f"""**Splunk Detection Search: {use_case['scenario']}**

**Primary Detection Search:**
```spl
| datamodel {use_case['data_model']} {use_case['data_model']} search
| search earliest=-1h latest=now
| eval scenario="{use_case['scenario']}"
| eval goal="{use_case['goal']}"

# Core detection logic
| bucket _time span=5m
| stats 
    count as event_count,
    dc(user) as unique_users,
    dc(src) as unique_sources,
    values(action) as actions,
    values(app) as applications
    by _time, src

# Apply detection thresholds
| where event_count > 15 AND unique_users > 3

# Risk scoring
| eval base_risk = case(
    event_count > 100, 80,
    event_count > 50, 60, 
    event_count > 25, 40,
    1=1, 20)
    
| eval user_risk = case(
    unique_users > 10, 30,
    unique_users > 5, 20,
    unique_users > 3, 10,
    1=1, 5)
    
| eval total_risk = base_risk + user_risk

# Categorize findings
| eval alert_category = case(
    total_risk > 90, "Critical",
    total_risk > 70, "High", 
    total_risk > 50, "Medium",
    1=1, "Low")

# Output formatting
| eval detection_time = strftime(_time, "%Y-%m-%d %H:%M:%S")
| table detection_time, src, event_count, unique_users, total_risk, alert_category, actions
| sort - total_risk
```

**Correlation Rule (savedsearches.conf):**
```conf
[{use_case['scenario'].replace(' ', '_')}_detection]
search = | datamodel {use_case['data_model']} {use_case['data_model']} search earliest=-1h | bucket _time span=5m | stats count as events, dc(user) as users by _time, src | where events > 15 AND users > 3 | eval risk_score = events * users | where risk_score > 50
dispatch.earliest_time = rt-1h
dispatch.latest_time = rt
cron_schedule = */5 * * * *
enableSched = 1
alert.track = 1
alert.digest_mode = 1
action.email = 1
action.email.to = security-team@company.com
action.email.subject = {use_case['scenario']} Alert
action.notable = 1
action.notable.param.security_domain = authentication
action.notable.param.severity = medium
action.correlationsearch.enabled = 1
```

**Dashboard Panel:**
```xml
<panel>
  <title>{use_case['scenario']} Monitoring</title>
  <chart>
    <search>
      <query>
        | datamodel {use_case['data_model']} {use_case['data_model']} search 
        | timechart span=1h count by action
        | eval goal = "{use_case['goal']}"
      </query>
      <earliest>-24h@h</earliest>
      <latest>now</latest>
      <refresh>5m</refresh>
    </search>
    <option name="charting.chart">column</option>
    <option name="charting.axisTitleX.text">Time</option>
    <option name="charting.axisTitleY.text">Event Count</option>
  </chart>
</panel>
```

**Threat Hunting Search:**
```spl
# Hunt for {use_case['goal'].lower()}
| datamodel {use_case['data_model']} {use_case['data_model']} search earliest=-7d
| eval hunt_scenario = "{use_case['scenario']}"

# Look for subtle patterns
| bucket _time span=1h  
| stats 
    avg(eval(if(action="failure", 1, 0))) as failure_rate,
    count as total_events,
    dc(user) as user_variety
    by src, _time

# Identify low-and-slow attacks  
| where failure_rate > 0.3 AND failure_rate < 0.8
| where total_events > 5 AND total_events < 50
| where user_variety > 2

# Calculate suspicion score
| eval suspicion_score = (failure_rate * 50) + (user_variety * 10) + (total_events / 2)
| where suspicion_score > 30

| sort - suspicion_score
| head 20
```

**Automated Response Integration:**
```spl
# Response trigger search  
<base_search>
| where alert_category IN ("High", "Critical")
| eval response_required = "true"
| eval soar_payload = "{"
    + "\"src_ip\":\"" + src + "\","
    + "\"event_count\":" + tostring(event_count) + ","
    + "\"risk_score\":" + tostring(total_risk) + ","
    + "\"scenario\":\"" + scenario + "\""
    + "}"
| map search="| rest /services/data/inputs/http | where title=\\"soar_webhook\\" | eval response=soar_payload"
```"""

    def generate_all_examples(self) -> List[Dict]:
        """Generate all training examples"""
        print("🔄 Generating expanded cybersecurity dataset...")
        
        all_examples = []
        
        # Generate examples by category
        categories = [
            ("4625 Teacher", self.generate_4625_teacher_examples),
            ("4625 Assistant", self.generate_4625_assistant_examples), 
            ("T1110 Variations", self.generate_t1110_variations),
            ("LimaCharlie", self.generate_limacharlie_examples),
            ("Splunk ES", self.generate_splunk_examples)
        ]
        
        for category_name, generator_func in categories:
            examples = generator_func()
            all_examples.extend(examples)
            print(f"  ✅ {category_name}: {len(examples)} examples")
        
        print(f"\n📊 Total examples generated: {len(all_examples)}")
        return all_examples
    
    def save_dataset(self, examples: List[Dict], filename: str = None):
        """Save dataset to file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S") 
            filename = f"training_data/expanded_cybersec_dataset_{timestamp}.json"
        
        # Ensure training_data directory exists
        os.makedirs("training_data", exist_ok=True)
        
        # Format for training
        formatted_data = {
            "metadata": {
                "generation_date": datetime.now().isoformat(),
                "total_examples": len(examples),
                "categories": {},
                "mentor_requirements": {
                    "target_examples": "100+",
                    "focus": "4625/T1110 + LC Replay",
                    "format": "instruction-tuning pairs with rationales"
                }
            },
            "examples": examples
        }
        
        # Count by category
        for example in examples:
            tags = example.get("tags", [])
            for tag in tags:
                if tag not in formatted_data["metadata"]["categories"]:
                    formatted_data["metadata"]["categories"][tag] = 0
                formatted_data["metadata"]["categories"][tag] += 1
        
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(formatted_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Dataset saved: {filename}")
        return filename

def main():
    """Generate expanded dataset following mentor's requirements"""
    generator = ExpandedDatasetGenerator()
    examples = generator.generate_all_examples()
    
    if len(examples) >= 100:
        print(f"✅ Target achieved: {len(examples)} examples (100+ required)")
    else:
        print(f"⚠️ Below target: {len(examples)} examples (need 100+)")
    
    filename = generator.save_dataset(examples)
    
    print("\n🎯 Expanded Dataset Summary:")
    print(f"📁 File: {filename}")
    print(f"📊 Examples: {len(examples)}")
    print("🛡️ Ready for robust Whis training!")
    
    return filename

if __name__ == "__main__":
    main()