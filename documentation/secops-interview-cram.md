# SecOps Interview Cram Guide - RAG Knowledge Base

## Document Metadata
- **ID**: KB-SECOPS-CRAM-001
- **Title**: SecOps Interview Cram Guide for Experienced Professionals
- **Tags**: SecOps, Interview, SIEM, SOAR, MITRE, Detection, Response
- **Owner**: whis-team
- **Created**: 2025-08-22
- **Source**: Expert SecOps knowledge compilation
- **Hash**: secops001

---

## 1. Core Security Pillars

### CIA Triad
**Confidentiality**: Protecting data from unauthorized access
- Encryption at rest and in transit
- Access controls and authentication
- Data classification and handling

**Integrity**: Ensuring data accuracy and preventing unauthorized modification
- Digital signatures and checksums
- Version control and audit trails
- Input validation and sanitization

**Availability**: Ensuring systems and data are accessible when needed
- Redundancy and failover mechanisms
- Load balancing and performance monitoring
- Disaster recovery and business continuity

### Defense in Depth
**Network Layer**: Firewalls, IPS, network segmentation
**Endpoint Layer**: EDR, antivirus, device controls
**Application Layer**: WAF, code analysis, secure coding
**Identity Layer**: MFA, privilege management, access reviews
**Data Layer**: Encryption, DLP, classification
**Physical Layer**: Access controls, environmental security

### Zero Trust Architecture
**Core Principles**:
- Never trust, always verify
- Assume breach mentality
- Least privilege access
- Continuous verification

**Implementation**:
- Multi-factor authentication everywhere
- Micro-segmentation of networks
- Identity-based access controls
- Real-time monitoring and analytics

### Kill Chain & MITRE ATT&CK
**Cyber Kill Chain Phases**:
1. Reconnaissance
2. Weaponization
3. Delivery
4. Exploitation
5. Installation
6. Command & Control
7. Actions on Objectives

**MITRE ATT&CK Integration**:
- Map detections to specific techniques
- Understand adversary behavior patterns
- Develop targeted countermeasures
- Measure security coverage gaps

---

## 2. Day-to-Day SecOps Responsibilities

### Monitoring Operations
**SIEM Dashboard Management**:
- Monitor real-time security events
- Triage alerts by severity and impact
- Correlate events across multiple sources
- Maintain situational awareness

**Key Metrics to Track**:
- Alert volume and trends
- False positive rates
- Mean time to detection (MTTD)
- Mean time to response (MTTR)
- Incident escalation rates

### Detection Engineering
**Alert Tuning Process**:
1. Analyze false positive patterns
2. Refine detection logic
3. Adjust thresholds and timeframes
4. Test with historical data
5. Document changes and rationale

**Detection Development**:
- Create custom rules for emerging threats
- Map detections to MITRE ATT&CK techniques
- Implement behavioral analytics
- Validate detection effectiveness

### Incident Response
**Standard IR Process**:
1. **Preparation**: Playbooks, tools, training
2. **Identification**: Alert triage and validation
3. **Containment**: Immediate threat isolation
4. **Eradication**: Remove threat from environment
5. **Recovery**: Restore normal operations
6. **Lessons Learned**: Improve processes

### Threat Hunting
**Hunting Methodologies**:
- Hypothesis-driven hunting
- Intelligence-driven hunting
- Baseline deviation hunting
- Crown jewel analysis

**Common Hunt Techniques**:
- PowerShell command analysis
- Network traffic anomalies
- Process execution patterns
- Registry and file system changes

---

## 3. Common SIEM/SOAR Workflows

### Windows Authentication Monitoring
**Event ID 4625 (Failed Logons)**:
```
Detection Logic:
- Monitor for >5 failures per source IP in 5 minutes
- Alert on >10 failures from external IPs
- Track unique account targeting patterns

Response Actions:
- Block source IP at firewall
- Lock targeted accounts temporarily
- Alert security team and account owners
- Investigate for successful authentications
```

**Event ID 4624 (Successful Logons)**:
```
Detection Logic:
- Unusual logon times or locations
- Service account interactive logons
- Privileged account usage patterns
- Logon type anomalies

Response Actions:
- Verify legitimacy with account owner
- Check for concurrent suspicious activities
- Monitor for lateral movement indicators
- Document in case management system
```

### PowerShell Monitoring
**Suspicious PowerShell Indicators**:
- EncodedCommand usage
- DownloadString functions
- Base64 encoded payloads
- PowerShell execution policy bypasses
- Invoke-Expression patterns

**Detection Query Example**:
```spl
index=security sourcetype=WinEventLog:Microsoft-Windows-PowerShell/Operational
| search EventCode=4104 OR EventCode=4103
| regex Message="(?i)(encodedcommand|downloadstring|invoke-expression)"
| stats count by Computer, User, Message
| where count > 1
```

### Lateral Movement Detection
**Key Indicators**:
- Event ID 4672 (Special privileges assigned)
- Event ID 4648 (Logon with explicit credentials)
- Unusual admin account usage
- Cross-network authentication patterns

**Detection Strategy**:
```spl
index=security (EventCode=4624 OR EventCode=4648)
| eval src_category=case(
    cidrmatch("10.0.0.0/8", src_ip), "internal",
    cidrmatch("192.168.0.0/16", src_ip), "internal",
    1=1, "external")
| where src_category="internal"
| stats dc(dest_host) as unique_hosts by user, src_ip
| where unique_hosts > 5
```

### Phishing Response Workflow
**Automated Phishing Triage**:
1. Extract email metadata and attachments
2. Analyze URLs and domains
3. Check threat intelligence feeds
4. Scan attachments for malware
5. Assess user interaction (clicked/downloaded)
6. Determine response actions

**Response Actions**:
- Quarantine suspicious emails
- Block malicious URLs/domains
- Reset user credentials if compromised
- Isolate affected endpoints
- Notify security awareness team

---

## 4. Threat Intelligence & Frameworks

### MITRE ATT&CK Framework
**Common Techniques for SecOps**:
- **T1110**: Brute Force (Password attacks)
- **T1566**: Phishing (Email-based attacks)
- **T1055**: Process Injection (Evasion technique)
- **T1059**: Command and Scripting Interpreter
- **T1021**: Remote Services (Lateral movement)

**ATT&CK Integration Best Practices**:
- Map all detections to specific techniques
- Track coverage across the ATT&CK matrix
- Use for threat hunting prioritization
- Communicate threats in ATT&CK language

### NIST Cybersecurity Framework
**Five Core Functions**:

**Identify (ID)**:
- Asset management and inventory
- Business environment understanding
- Governance and risk assessment
- Risk management strategy

**Protect (PR)**:
- Identity management and access control
- Awareness and training programs
- Data security and privacy protection
- Information protection processes

**Detect (DE)**:
- Anomalies and events monitoring
- Security continuous monitoring
- Detection processes and procedures

**Respond (RS)**:
- Response planning and procedures
- Communications and coordination
- Analysis and mitigation activities
- Improvements based on lessons learned

**Recover (RC)**:
- Recovery planning and procedures
- Improvements and communications

### Indicators of Compromise vs. Attack
**IoCs (Indicators of Compromise)**:
- File hashes (MD5, SHA1, SHA256)
- IP addresses and domains
- Registry keys and file paths
- Network signatures

**IoAs (Indicators of Attack)**:
- Behavioral patterns and techniques
- Process execution anomalies
- Network communication patterns
- User behavior deviations

---

## 5. Security Tools and Technologies

### SIEM Platforms
**Splunk**:
- SPL (Search Processing Language)
- Data models and pivot tables
- Dashboards and visualizations
- Alert correlation and workflow

**Microsoft Sentinel**:
- KQL (Kusto Query Language)
- Logic Apps for automation
- SOAR integration capabilities
- Azure ecosystem integration

### EDR/XDR Solutions
**CrowdStrike Falcon**:
- Real-time endpoint monitoring
- Behavioral analysis and ML
- Threat hunting capabilities
- Incident response tools

**LimaCharlie**:
- Cloud-native security platform
- D&R (Detection & Response) rules
- Real-time event streaming
- API-first architecture

### SOAR Platforms
**Splunk SOAR (Phantom)**:
- Playbook automation
- Case management
- Integration ecosystem
- Custom app development

**Cortex XSOAR**:
- Incident orchestration
- Threat intelligence integration
- Collaborative investigations
- Automated response actions

---

## 6. Senior-Level Concepts

### Security Metrics and KPIs
**Detection Metrics**:
- Mean Time to Detection (MTTD)
- Mean Time to Response (MTTR)
- Alert fatigue indicators
- Coverage mapping

**Operational Metrics**:
- False positive rates
- Escalation accuracy
- Analyst productivity
- Incident classification accuracy

### Cloud Security Operations
**AWS Security Monitoring**:
- CloudTrail for API logging
- GuardDuty for threat detection
- Config for compliance monitoring
- VPC Flow Logs for network analysis

**Azure Security Operations**:
- Activity Logs for resource changes
- Security Center for posture management
- Sentinel for SIEM capabilities
- Network Watcher for traffic analysis

### Compliance Integration
**Common Frameworks**:
- **PCI-DSS**: Payment card security
- **HIPAA**: Healthcare data protection
- **SOC 2**: Service organization controls
- **ISO 27001**: Information security management

**Compliance Automation**:
- Continuous compliance monitoring
- Automated evidence collection
- Risk assessment integration
- Audit trail maintenance

---

## 7. Interview Sound Bites and Talking Points

### Professional Responses
**On Alert Triage**: 
"My approach to alerts is always triage first — severity, scope, and potential impact. I use a risk-based prioritization framework that considers business context and threat landscape."

**On False Positives**: 
"Reducing false positives is key. Otherwise analysts drown in noise. I focus on tuning detection logic, improving data quality, and implementing behavioral baselines."

**On MITRE ATT&CK**: 
"Every detection I write, I map to MITRE ATT&CK to ensure coverage. This helps with threat hunting prioritization and communicating risk to leadership."

**On Automation**: 
"I see SOAR as the force multiplier — humans decide, automation executes. The key is designing playbooks that enhance analyst capabilities rather than replace human judgment."

### Technical Depth Examples
**Splunk Detection Query**:
```spl
index=security sourcetype=WinEventLog:Security EventCode=4625
| bucket _time span=5m
| stats count as failure_count, dc(Account_Name) as unique_accounts by src_ip, _time
| where failure_count > 5 AND unique_accounts > 1
| eval risk_score = failure_count * unique_accounts
| where risk_score > 25
```

**LimaCharlie D&R Rule**:
```yaml
detect:
  event: NEW_PROCESS
  op: and
  rules:
    - op: contains
      path: event/COMMAND_LINE
      value: "-EncodedCommand"
    - op: contains
      path: event/COMMAND_LINE
      value: "powershell"
respond:
  - action: report
    name: suspicious_powershell_encoded
  - action: isolation
    duration: 3600
```

---

## 8. Practical Scenarios and Responses

### Scenario: Suspected Data Exfiltration
**Investigation Steps**:
1. Identify unusual outbound network traffic patterns
2. Correlate with user behavior and access patterns
3. Check for data staging and compression activities
4. Review privileged account usage
5. Analyze timeline of events

**Response Actions**:
1. Contain potentially compromised accounts
2. Block suspicious network destinations
3. Preserve forensic evidence
4. Notify legal and compliance teams
5. Initiate incident response procedures

### Scenario: Advanced Persistent Threat (APT)
**Detection Indicators**:
- Long-term persistence mechanisms
- Low-and-slow data exfiltration
- Living-off-the-land techniques
- Command and control communications

**Response Strategy**:
1. Maintain operational security during investigation
2. Map full extent of compromise
3. Coordinate with threat intelligence teams
4. Plan simultaneous remediation actions
5. Implement enhanced monitoring

---

This knowledge base provides comprehensive coverage of SecOps interview topics with specific examples, technical details, and practical scenarios that demonstrate senior-level understanding.