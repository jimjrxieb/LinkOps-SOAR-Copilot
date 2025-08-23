#!/usr/bin/env python3
"""
Performance Booster for Whis
Generates additional high-quality training data if test performance is low
"""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict

class WhisPerformanceBooster:
    def __init__(self):
        self.additional_data = []
        
    def generate_soar_automation_boost(self) -> List[Dict]:
        """Generate high-quality SOAR automation examples"""
        soar_examples = [
            {
                "instruction": "Create an automated SOAR playbook for phishing email response with LimaCharlie integration",
                "input": "Detected phishing email with malicious attachment targeting finance team - automate containment and investigation",
                "output": """**AUTOMATED PHISHING RESPONSE PLAYBOOK**

**🚨 IMMEDIATE AUTOMATED ACTIONS (0-5 minutes):**

```yaml
# LimaCharlie Automated Response
responses:
  - name: block_sender_domain
    action: network_block
    target: email_sender_domain
    duration: 3600
    approval_required: false
    
  - name: quarantine_attachment_hash
    action: file_quarantine  
    target: attachment_sha256
    scope: organization
    approval_required: false
    
  - name: isolate_recipient_endpoints
    action: host_isolation
    target: recipient_endpoints
    duration: 1800
    approval_required: true
```

**📧 EMAIL ANALYSIS AUTOMATION:**
```spl
index=email_security subject="*" attachment_present=true
| eval risk_score = if(sender_reputation<2, 50, 0) + if(attachment_entropy>7.5, 30, 0) + if(url_count>5, 20, 0)
| where risk_score > 70
| eval action = if(risk_score>90, "quarantine", "flag")
```

**🔍 AUTOMATED INVESTIGATION STEPS:**
1. **Hash Analysis**: Submit to VirusTotal + internal sandbox
2. **Domain Reputation**: Query threat intelligence feeds  
3. **User Behavior**: Analyze recipient click patterns
4. **Network Traffic**: Hunt for C2 communications

**✅ SUCCESS CRITERIA:**
- Malicious attachment quarantined: < 2 minutes
- Sender domain blocked: < 1 minute  
- Affected users identified: < 5 minutes
- Incident ticket created: Automatic""",
                "metadata": {
                    "category": "soar-automation",
                    "difficulty": "advanced", 
                    "quality_score": 0.95
                }
            },
            {
                "instruction": "Design SOAR response for lateral movement detection with automated containment",
                "input": "Suspicious lateral movement detected across 3 systems using compromised service account - need automated response",
                "output": """**LATERAL MOVEMENT CONTAINMENT PLAYBOOK**

**⚡ IMMEDIATE AUTOMATED CONTAINMENT:**

```yaml
# Automated Service Account Response
soar_actions:
  - name: disable_service_account
    action: identity_disable
    target: compromised_service_account
    approval_required: false
    priority: critical
    
  - name: kill_suspicious_processes
    action: process_termination
    target: suspicious_process_list
    scope: affected_hosts
    approval_required: false
    
  - name: network_micro_isolation
    action: network_isolation
    target: affected_hosts
    allow_management_only: true
    approval_required: true
```

**🔍 AUTOMATED DETECTION LOGIC:**
```spl
index=security EventCode IN (4624,4625,4768,4769)
| stats dc(Computer) as host_count, values(Computer) as hosts by Account_Name
| where host_count >= 3 AND NOT Account_Name IN ("SYSTEM", "LOCAL SERVICE")
| eval lateral_movement_score = host_count * 10
| where lateral_movement_score > 25
| eval response_action = "isolate_and_investigate"
```

**📊 AUTOMATED ENRICHMENT:**
- **Timeline Analysis**: Correlate logon events across hosts
- **Privilege Mapping**: Identify account permissions on each system
- **Network Flow**: Analyze inter-host communications  
- **File Activity**: Hunt for suspicious file transfers

**🛡️ AUTOMATED RECOVERY:**
1. **Password Reset**: Force password change for affected account
2. **Ticket Routing**: Escalate to Tier 2 analyst automatically
3. **Evidence Collection**: Preserve memory dumps + logs
4. **Stakeholder Notification**: Alert security team + IT management""",
                "metadata": {
                    "category": "soar-automation",
                    "difficulty": "expert",
                    "quality_score": 0.93
                }
            },
            {
                "instruction": "Create SOAR automation for malware detection with dynamic analysis integration",
                "input": "Unknown binary detected on endpoint - automate malware analysis and response workflow",
                "output": """**AUTOMATED MALWARE ANALYSIS PLAYBOOK**

**🔬 IMMEDIATE AUTOMATED ANALYSIS:**

```yaml
# Dynamic Analysis Pipeline
analysis_workflow:
  - name: file_isolation
    action: quarantine_file
    target: suspicious_binary_hash
    scope: organization
    approval_required: false
    
  - name: sandbox_submission
    action: dynamic_analysis
    targets: [cuckoo_sandbox, joe_sandbox, vmray]
    timeout: 300
    approval_required: false
    
  - name: static_analysis
    action: malware_analysis
    tools: [yara_scan, entropy_check, pe_analysis]
    approval_required: false
```

**🧠 AUTOMATED DECISION LOGIC:**
```python
def malware_verdict(analysis_results):
    risk_score = 0
    
    # Static analysis indicators
    if analysis_results.entropy > 7.0: risk_score += 25
    if analysis_results.packed: risk_score += 20
    if analysis_results.suspicious_imports: risk_score += 15
    
    # Dynamic analysis indicators  
    if analysis_results.network_connections: risk_score += 30
    if analysis_results.registry_modifications: risk_score += 20
    if analysis_results.file_system_changes: risk_score += 15
    
    # Threat intelligence
    if analysis_results.ioc_matches: risk_score += 40
    
    return "malicious" if risk_score >= 75 else "suspicious" if risk_score >= 40 else "benign"
```

**⚡ AUTOMATED RESPONSE ACTIONS:**
- **Score ≥ 75**: Immediate quarantine + network isolation
- **Score 40-74**: Enhanced monitoring + user notification  
- **Score < 40**: Log event + continue monitoring

**📈 AUTOMATED REPORTING:**
- Real-time dashboard updates
- IOC extraction and sharing
- MITRE ATT&CK technique mapping
- Executive summary generation""",
                "metadata": {
                    "category": "soar-automation", 
                    "difficulty": "advanced",
                    "quality_score": 0.91
                }
            }
        ]
        return soar_examples
        
    def generate_incident_response_boost(self) -> List[Dict]:
        """Generate detailed incident response scenarios"""
        ir_examples = [
            {
                "instruction": "Provide step-by-step incident response for ransomware attack on domain controller with specific commands",
                "input": "Ransomware detected on primary domain controller - systems being encrypted rapidly - immediate response needed",
                "output": """**🚨 CRITICAL RANSOMWARE INCIDENT RESPONSE**

**PHASE 1: IMMEDIATE CONTAINMENT (0-15 minutes)**

```bash
# 1. ISOLATE INFECTED DOMAIN CONTROLLER
# On affected DC (if accessible):
netsh advfirewall set allprofiles firewallpolicy blockinbound,blockoutbound
shutdown /s /t 60 /c "Emergency ransomware isolation"

# 2. PREVENT LATERAL SPREAD
# On network infrastructure:
# Block DC IP at core switches/firewalls
# Disable replication ports: 389, 636, 3268, 3269, 88, 53
```

**PHASE 2: ASSESSMENT & FORENSICS (15-60 minutes)**

```powershell
# 3. RAPID DAMAGE ASSESSMENT
Get-ADComputer -Filter * | Test-Connection -Count 1 -Quiet | 
    Where {$_ -eq $false} | Export-CSV affected_systems.csv

# 4. BACKUP VERIFICATION
Get-WBSummary | Select BackupTime, BackupTarget, LastSuccessfulBackupTime

# 5. EVIDENCE PRESERVATION
# Create forensic images of critical systems
dd if=/dev/sda of=/mnt/evidence/dc_memory_dump.img bs=1M
```

**PHASE 3: RECOVERY PLANNING (1-4 hours)**

```bash
# 6. ISOLATE CLEAN BACKUP DC
# Promote secondary DC to primary role
dcpromo /unattend:promote_dc.txt

# 7. RESET ALL PRIVILEGED ACCOUNTS
dsquery user "CN=Users,DC=domain,DC=com" -scope subtree | 
    dsmod user -mustchpwd yes -disabled yes

# 8. NETWORK SEGMENTATION
# Implement micro-segmentation for critical assets
```

**PHASE 4: ERADICATION & RECOVERY (4-24 hours)**

- **Malware Removal**: Use specialized anti-ransomware tools
- **System Restoration**: Restore from known-clean backups  
- **Network Rebuild**: Implement defense-in-depth architecture
- **Monitoring Enhancement**: Deploy additional EDR sensors

**PHASE 5: POST-INCIDENT (24+ hours)**

- **Forensic Analysis**: Full timeline reconstruction
- **Lessons Learned**: Update playbooks and procedures
- **Regulatory Reporting**: Notify required authorities
- **Insurance Claims**: Document all damages and costs""",
                "metadata": {
                    "category": "incident-response",
                    "difficulty": "expert",
                    "quality_score": 0.96
                }
            }
        ]
        return ir_examples
        
    def generate_k8s_security_boost(self) -> List[Dict]:
        """Generate additional Kubernetes security examples"""
        k8s_examples = [
            {
                "instruction": "Create comprehensive Kubernetes cluster hardening checklist with validation commands",
                "input": "Need to audit and harden Kubernetes cluster security across all components",
                "output": """**KUBERNETES CLUSTER SECURITY HARDENING**

**🔐 API SERVER HARDENING:**

```bash
# 1. Verify API server configuration
kubectl get configmap kube-system/kubeadm-config -o yaml | grep -A 20 apiServer

# Required flags validation:
--anonymous-auth=false
--authorization-mode=RBAC,Node
--admission-control-config-file=/etc/kubernetes/admission-config.yaml
--enable-admission-plugins=NodeRestriction,PodSecurityPolicy,LimitRanger
--audit-log-path=/var/log/kube-audit.log
--audit-log-maxage=30
--tls-cert-file=/etc/kubernetes/pki/apiserver.crt
--tls-private-key-file=/etc/kubernetes/pki/apiserver.key
--client-ca-file=/etc/kubernetes/pki/ca.crt
--service-account-key-file=/etc/kubernetes/pki/sa.pub
--service-account-signing-key-file=/etc/kubernetes/pki/sa.key
```

**🔒 KUBELET SECURITY:**

```bash
# 2. Kubelet configuration hardening
# /etc/kubernetes/kubelet/kubelet-config.yaml
authentication:
  anonymous:
    enabled: false
  webhook:
    enabled: true
authorization:
  mode: Webhook
readOnlyPort: 0
protectKernelDefaults: true
makeIPTablesUtilChains: true
eventRecordQPS: 0
```

**🛡️ POD SECURITY STANDARDS:**

```yaml
# 3. Enforce restricted Pod Security Standards
apiVersion: v1
kind: Namespace
metadata:
  name: production
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
```

**🔍 SECURITY AUDIT COMMANDS:**

```bash
# 4. Comprehensive security audit
# Check for privileged containers
kubectl get pods --all-namespaces -o jsonpath='{range .items[*]}{.metadata.namespace}{"\t"}{.metadata.name}{"\t"}{.spec.securityContext.privileged}{"\n"}{end}' | grep true

# Audit service accounts with cluster-admin
kubectl get clusterrolebindings -o json | jq -r '.items[] | select(.roleRef.name=="cluster-admin") | .subjects[]? | select(.kind=="ServiceAccount") | "\(.namespace)/\(.name)"'

# Check for containers running as root
kubectl get pods --all-namespaces -o jsonpath='{range .items[*]}{range .spec.containers[*]}{.securityContext.runAsUser}{"\t"}{.name}{"\n"}{end}{end}' | grep -E "^0|^$"
```

**📊 VALIDATION CHECKLIST:**

- [ ] API server anonymous auth disabled
- [ ] RBAC authorization enabled
- [ ] Pod Security Standards enforced
- [ ] Network policies implemented
- [ ] Container images signed and scanned
- [ ] Secrets encrypted at rest
- [ ] Audit logging enabled
- [ ] Resource quotas configured
- [ ] Node OS hardened (CIS benchmarks)
- [ ] Regular security scanning automated""",
                "metadata": {
                    "category": "k8s-security",
                    "difficulty": "advanced", 
                    "quality_score": 0.94
                }
            }
        ]
        return k8s_examples
        
    def create_performance_boost_dataset(self):
        """Create comprehensive performance boost dataset"""
        print("🚀 CREATING PERFORMANCE BOOST DATASET")
        print("=" * 45)
        
        # Generate examples from each category
        soar_examples = self.generate_soar_automation_boost()
        ir_examples = self.generate_incident_response_boost() 
        k8s_examples = self.generate_k8s_security_boost()
        
        all_examples = soar_examples + ir_examples + k8s_examples
        
        # Convert to Whis training format
        boost_data = []
        for example in all_examples:
            whis_format = {
                "text": f"""Below is an instruction that describes a cybersecurity task, paired with an input that provides further context. Write a response that appropriately completes the request.

### Instruction:
{example['instruction']}

### Input:
{example['input']}

### Response:
{example['output']}""",
                "metadata": {
                    "original_instruction": example['instruction'],
                    "quality_score": example['metadata']['quality_score'],
                    "tags": [
                        "PerformanceBoost",
                        f"Category:{example['metadata']['category']}",
                        f"Difficulty:{example['metadata']['difficulty']}",
                        "HighQuality"
                    ],
                    "category": example['metadata']['category']
                }
            }
            boost_data.append(whis_format)
            
        # Save performance boost dataset
        boost_path = Path("training/processed_data/performance_boost_dataset.json")
        boost_path.parent.mkdir(exist_ok=True)
        
        with open(boost_path, 'w') as f:
            json.dump(boost_data, f, indent=2)
            
        print(f"✅ Performance boost dataset created: {boost_path}")
        print(f"📊 High-quality examples: {len(boost_data)}")
        
        # Create summary
        categories = {}
        for example in boost_data:
            cat = example['metadata']['category']
            categories[cat] = categories.get(cat, 0) + 1
            
        print("\n📈 Category breakdown:")
        for cat, count in categories.items():
            print(f"  - {cat}: {count} examples")
            
        return boost_path, boost_data

def main():
    booster = WhisPerformanceBooster()
    boost_path, boost_data = booster.create_performance_boost_dataset()
    
    return {
        "boost_dataset": str(boost_path),
        "examples_count": len(boost_data),
        "categories": list(set(ex['metadata']['category'] for ex in boost_data))
    }

if __name__ == "__main__":
    main()