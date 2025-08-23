# Enhanced RAG Knowledge Base - Advanced SecOps

## Document Metadata
- **ID**: KB-RAG-ENHANCED-001
- **Title**: Enhanced RAG Knowledge Base for Advanced Security Operations
- **Tags**: RAG, Advanced, Windows Events, MITRE ATT&CK, Splunk, LimaCharlie, IR, Threat Hunting
- **Owner**: whis-team
- **Created**: 2025-08-22
- **Source**: Expert SecOps knowledge compilation
- **Hash**: ragenhanced001

---

## Windows Security Events

### Windows Event ID 4624 - Successful Logon

**Query**: What does Windows Event ID 4624 indicate and what are the key fields?

**Knowledge**: Windows Event 4624 represents successful logon events. Key fields include LogonType (2=interactive, 3=network, 10=RemoteInteractive), Account Name, Source Network Address, and Logon Process. This event is crucial for tracking user authentication activity.

**Response Template**: Event 4624 indicates successful user logon. Key fields: LogonType (2=interactive, 3=network, 10=remote), Account Name, Source IP, Logon Process. Critical for authentication monitoring and baseline establishment.

### Windows Event ID 4648 - Explicit Credential Usage

**Query**: Explain Windows Event ID 4648 and its significance for lateral movement detection

**Knowledge**: Event 4648 occurs when a logon is attempted using explicit credentials (RunAs). This is significant for detecting lateral movement as attackers often use stolen credentials to authenticate to remote systems. Fields include Subject (who initiated), Target Server, and Account Name being used.

**Response Template**: Event 4648 = explicit credential usage (RunAs). Critical for lateral movement detection as attackers use stolen credentials. Monitor Subject vs Account Name discrepancies and cross-network authentication patterns.

### Windows Event ID 4672 - Special Privileges Assigned

**Query**: What is Windows Event ID 4672 and why is it important for privilege escalation monitoring?

**Knowledge**: Event 4672 indicates that special privileges were assigned to a new logon. This event is generated when an account is assigned user rights that are considered sensitive (like SeDebugPrivilege, SeBackupPrivilege). It's crucial for monitoring privilege escalation attempts.

**Response Template**: Event 4672 = special privileges assigned to new logon. Critical for privilege escalation monitoring. Watch for sensitive rights like SeDebugPrivilege, SeBackupPrivilege being assigned to regular user accounts.

## MITRE ATT&CK Techniques

### T1078 - Valid Accounts

**Query**: Explain MITRE ATT&CK technique T1078 and provide detection strategies

**Knowledge**: T1078 (Valid Accounts) involves adversaries using legitimate credentials to maintain access. Subtechniques include T1078.001 (Default Accounts), T1078.002 (Domain Accounts), T1078.003 (Local Accounts), and T1078.004 (Cloud Accounts). Detection focuses on unusual access patterns, privilege usage, and cross-system authentication.

**Response Template**: T1078 Valid Accounts: Adversaries use legitimate credentials. Subtechniques: Default/Domain/Local/Cloud accounts. Detection: Monitor unusual login patterns, privilege escalation, geographic anomalies, and failed-then-successful authentication sequences.

### T1055 - Process Injection

**Query**: What is MITRE ATT&CK T1055 Process Injection and what are common detection methods?

**Knowledge**: T1055 Process Injection allows adversaries to execute code in the address space of legitimate processes. Common techniques include DLL injection, Process Hollowing, and Thread Execution Hijacking. Detection involves monitoring for unusual process behavior, memory modifications, and API calls like CreateRemoteThread, WriteProcessMemory.

**Response Template**: T1055 Process Injection: Execute code in legitimate process space. Techniques: DLL injection, process hollowing, thread hijacking. Detection: Monitor CreateRemoteThread, WriteProcessMemory APIs, unusual child processes, memory anomalies.

### T1059 - Command and Scripting Interpreter

**Query**: Describe MITRE ATT&CK T1059 Command and Scripting Interpreter with detection approaches

**Knowledge**: T1059 involves adversaries using command and scripting interpreters to execute code. Subtechniques include PowerShell (T1059.001), AppleScript (T1059.002), Windows Command Shell (T1059.003), and others. Detection focuses on command-line analysis, script content inspection, and behavioral patterns.

**Response Template**: T1059 Command/Scripting Interpreter: Execute code via interpreters. Key subtechniques: PowerShell, cmd.exe, bash. Detection: Monitor command-line arguments, encoded commands, script execution policies, and unusual interpreter spawning patterns.

## Splunk SIEM Detection Queries

### Brute Force Attack Detection

**Query**: Create a Splunk search to detect potential brute force attacks using Windows Event 4625

**Knowledge**: Brute force attacks generate multiple failed logon events (4625) from the same source. Effective detection requires analyzing failure counts, unique accounts targeted, and source IP patterns within specific time windows.

**SPL Query**:
```spl
index=security EventCode=4625 
| bucket _time span=5m 
| stats count as failures, dc(Account_Name) as unique_accounts by src_ip, _time 
| where failures > 5 AND unique_accounts > 1 
| eval risk_score = failures * unique_accounts
```

### PowerShell Malware Detection

**Query**: Write a Splunk query to identify suspicious PowerShell execution patterns

**Knowledge**: Malicious PowerShell often uses encoded commands, download functions, and execution policy bypasses. Detection should look for these patterns in PowerShell event logs (EventCode 4104, 4103) and analyze command content.

**SPL Query**:
```spl
index=security sourcetype="WinEventLog:Microsoft-Windows-PowerShell/Operational" 
| search EventCode=4104 OR EventCode=4103 
| regex Message="(?i)(encodedcommand|downloadstring|invoke-expression|bypass)" 
| stats count by Computer, User, Message 
| where count > 1
```

### Lateral Movement Correlation

**Query**: How do you create a Splunk correlation search for lateral movement detection?

**Knowledge**: Lateral movement involves authentication across multiple systems in short time periods. Detection should correlate successful logons (4624) across different hosts from the same user account within suspicious timeframes.

**SPL Query**:
```spl
index=security EventCode=4624 
| eval src_category=case(cidrmatch("192.168.0.0/16",src_ip),"internal", 1=1,"external") 
| where src_category="internal" 
| stats dc(dest_host) as unique_hosts, values(dest_host) as hosts by user, _time 
| where unique_hosts > 3
```

## LimaCharlie EDR Detection Rules

### Suspicious Process Creation Detection

**Query**: Create a LimaCharlie D&R rule to detect suspicious process creation patterns

**Knowledge**: LimaCharlie D&R rules use YAML format to define detection logic and response actions. Process creation monitoring should focus on unusual parent-child relationships, command-line arguments, and execution from suspicious locations.

**D&R Rule**:
```yaml
detect:
  event: NEW_PROCESS
  op: and
  rules:
    - op: contains
      path: event/COMMAND_LINE
      value: "powershell"
    - op: contains
      path: event/COMMAND_LINE
      value: "-EncodedCommand"
respond:
  - action: report
    name: suspicious_powershell_encoded
```

### Fileless Malware Detection

**Query**: Write a LimaCharlie rule for detecting file-less malware execution

**Knowledge**: File-less malware often uses legitimate system processes and injects code into memory. Detection should monitor for unusual memory allocations, process hollowing, and execution from unexpected locations or contexts.

**D&R Rule**:
```yaml
detect:
  event: MEMORY_ALLOC
  op: and
  rules:
    - op: is
      path: event/MEMORY_TYPE
      value: "PAGE_EXECUTE_READWRITE"
    - op: not
      path: event/PROCESS_PATH
      re: "^C:\\\\Windows\\\\(System32|SysWOW64)\\\\.+\\.exe$"
respond:
  - action: isolation
    duration: 3600
  - action: report
    name: potential_process_injection
```

## Incident Response Procedures

### Ransomware Response Protocol

**Query**: Outline the immediate response steps for a confirmed ransomware incident

**Knowledge**: Ransomware incidents require rapid containment to prevent spread. Initial response focuses on isolation, impact assessment, and evidence preservation while coordinating with stakeholders.

**Response Steps**: 
1. Isolate affected systems (network isolation, not power-off)
2. Assess scope via EDR/SIEM queries
3. Preserve memory dumps and logs
4. Notify incident commander and legal team
5. Begin asset inventory of impacted systems
6. Implement backup assessment and recovery planning

### Data Exfiltration Investigation

**Query**: What are the key steps in investigating a data exfiltration incident?

**Knowledge**: Data exfiltration investigations require analyzing network traffic, user behavior, and access patterns to determine what data was accessed and how it was transmitted. Timeline reconstruction is critical.

**Investigation Steps**: 
1. Identify data access patterns via logs
2. Analyze network traffic for unusual outbound connections
3. Check for data staging activities (compression, encryption)
4. Review user authentication and privilege usage
5. Examine email/cloud storage for data transfers
6. Reconstruct timeline with correlation analysis

## Threat Hunting Methodologies

### Living-off-the-Land Detection

**Query**: Design a threat hunting hypothesis for detecting living-off-the-land attacks

**Knowledge**: Living-off-the-land attacks use legitimate system tools for malicious purposes. Hunting should focus on unusual usage patterns of built-in utilities like certutil, bitsadmin, regsvr32, and others in unexpected contexts.

**Hunting Hypothesis**: Adversaries abuse legitimate Windows utilities for malicious purposes. Hunt for: certutil downloading files, bitsadmin transfers, regsvr32 with unusual arguments, rundll32 executing from temp directories, and wmic lateral movement. Baseline normal usage first.

### Persistent Backdoor Detection

**Query**: What threat hunting approach would you use to find persistent backdoors?

**Knowledge**: Persistent backdoors establish long-term access through various mechanisms including registry modifications, scheduled tasks, services, and startup folder modifications. Hunting requires systematic enumeration of persistence mechanisms.

**Hunting Approach**: 
1. Hunt for unusual registry Run keys
2. Enumerate suspicious scheduled tasks and services
3. Check startup folders and WMI event subscriptions
4. Analyze DLL hijacking opportunities
5. Look for COM object hijacking
6. Cross-reference with process execution timeline

---

This enhanced knowledge base provides comprehensive coverage of advanced SecOps topics with practical implementation examples for both Teacher and Assistant modes.