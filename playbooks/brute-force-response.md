# Brute Force Response Playbook

**Playbook ID**: PB-AUTH-001  
**MITRE Mapping**: T1110 (Brute Force)  
**Severity**: Medium to High  
**Estimated Duration**: 15-30 minutes  

## Trigger Conditions
- Multiple 4625 events (>5 in 5 minutes)
- Failed authentication across multiple accounts
- Geographic anomalies in logon attempts
- Whis Assistant recommendation

## Initial Assessment (2-3 minutes)

### 🔍 Immediate Checks
1. **Source IP Analysis**
   ```
   LimaCharlie Query: 
   SELECT * FROM processes WHERE net_conn_remote_ip = 'SUSPICIOUS_IP'
   ```

2. **Account Impact Assessment**
   ```
   Splunk Query:
   index=security EventCode=4625 src_ip="SUSPICIOUS_IP" 
   | stats dc(user) as unique_accounts, count by src_ip
   ```

3. **Success/Failure Ratio**
   - Check for any successful logons (4624) from same source
   - Verify if attack was successful

### 📊 Risk Factors
- [ ] Privileged accounts targeted
- [ ] External IP source  
- [ ] Outside business hours
- [ ] High volume (>20 attempts)
- [ ] Multiple systems affected

## Containment Actions (5-10 minutes)

### 🚫 Immediate Containment
1. **IP Address Blocking**
   - Firewall rule implementation
   - Proxy/WAF blocking
   - Document block reason and duration

2. **Account Protection** (if confirmed targeting)
   - Temporary account lockout
   - Force password reset on affected accounts
   - Notify account owners

### 🔐 LimaCharlie Actions
```yaml
# LC Isolation Rule
- action: isolate
  conditions:
    - net_conn_remote_ip: "SUSPICIOUS_IP"
  duration: 3600  # 1 hour
  reason: "Brute force attack containment"
```

## Investigation Phase (10-15 minutes)

### 🕵️ Detailed Analysis
1. **Timeline Construction**
   - First/last attempt timestamps
   - Pattern analysis (consistent intervals?)
   - Tool signature identification

2. **Lateral Movement Check**
   ```
   Splunk Query:
   index=security (EventCode=4624 OR EventCode=4648) src_ip="SUSPICIOUS_IP"
   | eval success_after_attempts="true"
   ```

3. **Threat Intelligence**
   - IP reputation check (VirusTotal, AbuseIPDB)
   - Known attack campaigns
   - IOC correlation

### 📝 Evidence Collection
- Network flow data
- Authentication logs
- System process information
- User agent strings (if web-based)

## Communication (Parallel Task)

### 🚨 Stakeholder Notification
1. **Immediate (via Slack)**
   ```
   🛡️ SECURITY ALERT: Brute Force Attack Detected
   Source: {source_ip}
   Targets: {affected_accounts}
   Status: Contained
   Analyst: {analyst_name}
   Tracking: {incident_id}
   ```

2. **Affected Users**
   - Email notification of suspicious activity
   - Password reset instructions
   - Security awareness reminder

## Resolution Actions

### ✅ Short-term
- [ ] IP blocking confirmed effective
- [ ] Affected accounts secured
- [ ] Attack activity ceased
- [ ] Documentation completed

### 🔧 Long-term  
- [ ] Detection rule tuning
- [ ] Threshold adjustment based on false positives
- [ ] Process improvement recommendations
- [ ] User security training

## Whis Integration Points

### 🎓 Teacher Mode Outputs
- False positive analysis for threshold tuning
- ATT&CK technique correlation
- Best practice recommendations

### 🤖 Assistant Mode Actions
- Automated IP reputation checks
- Suggested containment actions
- Playbook routing recommendations
- Draft stakeholder communications

## Approval Gates

### 🚦 Human Approval Required
- [ ] IP blocking (if affects business operations)
- [ ] Account lockouts (if affects critical users)
- [ ] Network isolation (if affects shared resources)

### ⚡ Auto-approved Actions
- [ ] Log collection and analysis
- [ ] Threat intelligence queries
- [ ] Internal team notifications

## Success Metrics

### 📈 Effectiveness Measures
- Time to detection: <5 minutes
- Time to containment: <10 minutes  
- False positive rate: <10%
- Stakeholder notification: <15 minutes

## Post-Incident Review

### 📚 Lessons Learned
1. What worked well in detection/response?
2. Were thresholds appropriate?
3. Any false positives to address?
4. Process improvements needed?

### 🔄 Continuous Improvement
- Update detection rules based on new patterns
- Refine playbook based on execution experience
- Share intelligence with security community
- Train team on new techniques discovered

---

**Last Updated**: {current_date}  
**Next Review**: Quarterly  
**Playbook Owner**: SOC Team Lead  
**Whis Integration**: Full (Teacher + Assistant modes)