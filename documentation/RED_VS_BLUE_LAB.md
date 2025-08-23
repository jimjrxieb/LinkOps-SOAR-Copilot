# 🔥 WHIS Red vs Blue Lab Guide

## Overview

The WHIS Red vs Blue Lab is a cloud-based vulnerable environment where:
- **Red Team** (your coworker) attacks the vulnerable Windows VM
- **Blue Team** (you) monitors with Sysmon, Splunk, and LimaCharlie  
- **Whis AI** analyzes security events and provides SOAR recommendations
- **Training Loop** improves Whis based on real attack patterns

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Red Team      │    │  Vulnerable VM   │    │   Blue Team     │
│   Attacker      │───▶│  Windows 2019    │───▶│   Monitoring    │
│                 │    │  - Weak passwords│    │   - Sysmon      │
└─────────────────┘    │  - Open services │    │   - Splunk      │
                       │  - Vuln software │    │   - LimaCharlie │
                       └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │   Whis SOAR      │
                       │   - Event Analysis│
                       │   - Response Recs│  
                       │   - Training Loop│
                       └──────────────────┘
```

## Lab Components

### Vulnerable Windows VM
- **OS**: Windows Server 2019
- **IP**: Public IP for red team access + Private IP for monitoring
- **Credentials**: Auto-generated (output from Terraform)
- **Services**: RDP, SMB, WinRM (all intentionally vulnerable)
- **Software**: Vulnerable web app, file shares with dummy secrets

### Monitoring Stack
- **Sysmon**: Process, network, and file monitoring with SwiftOnSecurity config
- **Splunk Universal Forwarder**: Ships logs to HEC endpoint
- **LimaCharlie**: EDR sensor with webhook integration
- **Health Monitoring**: Automated status checks every 5 minutes

### Network Security
- **Vulnerable Subnet**: 10.10.1.0/24 (intentionally weak NSG rules)
- **Monitoring Subnet**: 10.10.2.0/24 (secure access for SOC)
- **Public Access**: RDP allowed from red team IP only

## Deployment Guide

### Prerequisites

1. **Azure CLI**: `az login` and active subscription
2. **Terraform**: v1.0+ installed and in PATH
3. **Access**: Splunk HEC token and LimaCharlie install key

### Quick Start

```bash
# 1. Clone and navigate
cd infrastructure

# 2. Configure variables
cp terraform/terraform.tfvars.example terraform/terraform.tfvars
# Edit terraform.tfvars with your IPs and tokens

# 3. Deploy lab
./deploy.sh

# 4. Get connection info
cat connection_info.txt
```

### Required Configuration

Update `terraform/terraform.tfvars`:

```hcl
# Network Access (CRITICAL - UPDATE THESE!)
attacker_ip = "RED_TEAM_IP/32"    # Your coworker's IP
soc_ip      = "BLUE_TEAM_IP/32"   # Your monitoring IP

# Monitoring Integration  
splunk_hec_token = "abcd1234-ef56-7890-..."  # From Splunk
lc_install_key   = "12345678-90ab-cdef-..."   # From LimaCharlie
```

## Attack Scenarios

### Basic Red Team Targets

#### 1. RDP Brute Force
```bash
# Target: Public IP:3389
# Method: Weak admin password
# Blue Team: Watch for EventID 4625 (failed logon)
# Whis: Should detect brute force pattern and recommend lockdown
```

#### 2. SMB File Share Enumeration
```bash
# Target: \\VM_IP\VulnShare
# Method: Anonymous access to sensitive files
# Blue Team: Sysmon Process Creation + Network events
# Whis: Should recommend SMB hardening and access controls
```

#### 3. WinRM Lateral Movement  
```bash
# Target: VM_IP:5985 (HTTP WinRM)
# Method: Basic auth with weak credentials
# Blue Team: WinRM service logs + Sysmon
# Whis: Should detect lateral movement and recommend WinRM security
```

#### 4. Web Application Attacks
```bash
# Target: http://VM_IP/vulnapp/
# Method: SQL injection, XSS, directory traversal
# Blue Team: IIS logs + Sysmon process creation
# Whis: Should recommend web app security measures
```

### Advanced Scenarios (Configure with `lab_scenario` variable)

#### APT Campaign Simulation
- Multi-stage attack with persistence
- Credential harvesting with Mimikatz-style tools
- Command & control communication
- Data exfiltration attempts

#### Ransomware Simulation  
- File encryption patterns
- Shadow copy deletion
- Network spreading attempts
- Backup destruction simulation

## Blue Team Monitoring

### Sysmon Events to Watch

| Event ID | Description | Red Team Activity |
|----------|-------------|-------------------|
| 1 | Process Creation | Tool execution, shell commands |
| 3 | Network Connection | C2 communication, data exfil |
| 7 | Image/DLL Loaded | DLL injection, process hollowing |
| 8 | CreateRemoteThread | Process injection techniques |
| 10 | Process Access | Credential dumping, LSASS access |
| 11 | File Creation | Dropped files, persistence |

### Splunk Searches

```spl
# Detect suspicious process execution
index=sysmon EventCode=1 
| search (Image="*powershell*" OR Image="*cmd.exe*") 
| stats count by Computer, User, Image, CommandLine

# Network connections to external IPs
index=sysmon EventCode=3 DestinationIsIpv6=false
| search NOT (DestinationIp="10.*" OR DestinationIp="192.168.*")
| stats count by Computer, SourceIp, DestinationIp, DestinationPort

# File creation in system directories
index=sysmon EventCode=11
| search TargetFilename="C:\\Windows\\System32\\*" OR TargetFilename="C:\\Windows\\Temp\\*"
| stats count by Computer, TargetFilename, Image
```

### LimaCharlie Detection Rules

```yaml
# Process injection detection
detection:
  op: and
  rules:
    - op: is
      path: event/PROCESS_NAME
      value: suspicious.exe
    - op: is  
      path: event/COMMAND_LINE
      value: "*CreateRemoteThread*"

response:
  - action: report
    name: process_injection_detected
```

## Whis Integration

### Event Flow

```
Security Event → Sysmon/LC → Splunk HEC → Whis Webhook → Analysis → Response Recommendations
```

### Webhook Configuration

```json
{
  "splunk_hec_url": "https://VM_IP:8088/services/collector/event",
  "splunk_hec_token": "YOUR_TOKEN",  
  "whis_api_url": "http://YOUR_WHIS_API:8001",
  "lc_webhook_url": "http://YOUR_WHIS_API:8001/webhooks/limacharlie"
}
```

### Expected Whis Responses

For each attack, Whis should provide:
- **Triage Steps**: Immediate investigation actions
- **Containment**: Isolation and blocking measures
- **Remediation**: Long-term security improvements
- **MITRE Mapping**: Relevant ATT&CK techniques
- **Splunk Queries**: Investigation searches
- **LimaCharlie Rules**: Detection improvements

## Training Loop

### 1. Attack Execution
Red team performs attack on vulnerable VM

### 2. Detection & Analysis
- Sysmon captures telemetry
- LimaCharlie detects behaviors  
- Splunk centralizes logs
- Whis analyzes events

### 3. Response Evaluation
- Review Whis recommendations
- Test suggested containment
- Validate remediation steps
- Assess response quality

### 4. Model Improvement
- Add successful scenarios to Golden Set
- Update training data with new patterns
- Retrain model on improved dataset
- Deploy updated model

### 5. Repeat Cycle
- Red team adapts tactics
- Blue team improves detection
- Whis learns from feedback
- Continuous improvement loop

## Security Considerations

### Lab Isolation ⚠️

**CRITICAL**: This VM is intentionally vulnerable!

- **Never connect to production networks**
- **Use isolated lab environment only**
- **Destroy when testing complete**
- **Monitor for unintended access**

### Network Segmentation

```
Production Network: 192.168.0.0/16 (ISOLATED)
Lab Network:       10.10.0.0/16    (VULNERABLE)
```

### Access Controls

- Red team: RDP only from specified IP
- Blue team: Splunk web UI from specified IP  
- No internet access from vulnerable VM
- Monitoring traffic allowed within lab network

## Troubleshooting

### Common Issues

**VM Not Accessible**
```bash
# Check NSG rules allow your IP
az network nsg rule show --resource-group whis-redvsblue-lab --nsg-name whis-lab-vulnerable-nsg --name AllowRDP

# Verify VM is running
az vm show --resource-group whis-redvsblue-lab --name whis-lab-vuln-vm --show-details
```

**Sysmon Not Logging**
```powershell
# Check Sysmon service
Get-Service Sysmon64

# Verify event log
Get-WinEvent -LogName "Microsoft-Windows-Sysmon/Operational" -MaxEvents 10
```

**Splunk Not Receiving Data**
```bash
# Test HEC endpoint
curl -k "https://VM_IP:8088/services/collector/event" \
  -H "Authorization: Splunk YOUR_TOKEN" \
  -d '{"event": "test"}'
```

**LimaCharlie Sensor Issues**
```powershell
# Check LC sensor status
Get-Process lc_sensor

# Review installation logs
Get-Content "C:\Program Files\LimaCharlie\logs\sensor.log"
```

## Metrics & KPIs

### Red Team Success Metrics
- Time to initial access
- Privilege escalation achieved
- Lateral movement success
- Data exfiltration completed
- Persistence established

### Blue Team Detection Metrics  
- Mean time to detection (MTTD)
- Alert accuracy (true positive rate)
- Investigation completeness
- Response time to containment
- False positive rate

### Whis AI Performance
- Response relevance score
- Containment effectiveness
- MITRE technique accuracy
- Splunk query success rate
- Golden Set evaluation scores

## Advanced Configurations

### Multi-VM Scenarios

Deploy additional VMs for complex attacks:

```hcl
additional_vulnerable_vms = 2
lab_scenario = "lateral_movement"
```

### Custom Vulnerable Software

Add organization-specific vulnerable applications:
- Internal web apps
- Custom database systems
- Legacy software stacks
- Industry-specific tools

### Purple Team Exercises

Combine red/blue activities:
1. **Plan**: Define attack scenario and detection objectives  
2. **Execute**: Red team attacks while blue team detects
3. **Analyze**: Review detection gaps and response quality
4. **Improve**: Update detections and train Whis
5. **Document**: Capture lessons learned

## Cleanup

### Destroy Lab Environment

```bash
cd infrastructure/terraform
terraform destroy
```

### Verify Cleanup

```bash
# Check resource group is deleted
az group show --name whis-redvsblue-lab
# Should return error: ResourceGroupNotFound
```

---

**🔥 Ready for battle! May the best team win, and may Whis learn from every engagement!**

*Remember: This is about improving our collective security posture through adversarial training. The real winner is better cybersecurity for everyone.*