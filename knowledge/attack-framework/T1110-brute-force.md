# MITRE ATT&CK T1110: Brute Force

## Overview
Adversaries may use brute force techniques to gain access to accounts when passwords are unknown or when password hashes are obtained.

## Sub-Techniques
- **T1110.001**: Password Guessing
- **T1110.002**: Password Cracking  
- **T1110.003**: Password Spraying
- **T1110.004**: Credential Stuffing

## Detection: Windows Event 4625 (Failed Logon)

### Key Indicators
- Multiple failed logon attempts from same source
- Failed logons across multiple accounts from same IP
- Failed logons outside normal business hours
- Unusual logon types (Network logon type 3)

### Event Analysis
```xml
Event ID: 4625
Security ID: NULL SID
Account Name: admin
Account Domain: DOMAIN
Failure Reason: Unknown user name or bad password
Status: 0xc000006d
Sub Status: 0xc000006a
Logon Type: 3
Process Name: -
```

## False Positives

### Common Scenarios
1. **Service Account Issues**
   - Expired passwords on service accounts
   - Misconfigured scheduled tasks
   - Application connection failures

2. **User Behavior**
   - Users returning from vacation with forgotten passwords
   - Password policy changes requiring resets
   - Caps lock enabled during logon

3. **Network Issues**
   - Time synchronization problems
   - Domain controller connectivity issues
   - Cached credential validation failures

### Filtering Recommendations
```
index=security EventCode=4625
| stats count by src_ip, user, _time
| where count > 5
| eval timeframe="5min"
| where _time > relative_time(now(), "-5m")
```

## Detection Tuning

### Recommended Thresholds
- **Initial Alert**: >5 failures in 5 minutes from same IP
- **Escalation**: >10 failures in 1 minute 
- **Critical**: >20 failures across multiple accounts

### Exclusions
- Known service account IPs
- Administrative workstations (with monitoring)
- Test environments (separate alerting)

## Response Playbooks

### Immediate Actions
1. **Account Lockdown** (if confirmed malicious)
2. **IP Blocking** at firewall/proxy
3. **User Notification** for legitimate account owners

### Investigation Steps
1. Review source IP reputation
2. Check for successful logons from same source
3. Correlate with other authentication events
4. Review account permissions and usage patterns

## Best Practices

### Prevention
- Implement account lockout policies
- Use multi-factor authentication
- Deploy CAPTCHA for web applications
- Monitor privileged account usage

### Detection Enhancement
- Correlate with geolocation data
- Monitor authentication across multiple systems
- Track successful logons after failed attempts
- Implement behavioral analytics

## References
- [MITRE ATT&CK T1110](https://attack.mitre.org/techniques/T1110/)
- [NIST SP 800-53 IA-5](https://csrc.nist.gov/Projects/risk-management/sp800-53-controls/release-search#!/control?version=5.1&number=IA-5)
- [CIS Control 16: Account Monitoring](https://www.cisecurity.org/controls/account-monitoring-and-control)

## Whis Training Notes

### For SOC Analysts
- Always verify source IP legitimacy before escalation
- Consider business context (time, geography, user role)
- Document patterns for threshold tuning
- Escalate privilege account targeting immediately

### Common Mistakes
- Alerting on single failed logons
- Not excluding known service account sources
- Missing successful logons after failed attempts
- Over-aggressive IP blocking without investigation