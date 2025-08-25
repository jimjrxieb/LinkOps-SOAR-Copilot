# PowerShell Empire Response Playbook

## PowerShell Empire Detection & Response (T1059.001)

**Immediate Response:**
1. **Process Termination**: Kill malicious PowerShell processes immediately
2. **Network Blocking**: Block C2 communications to external IPs
3. **Script Analysis**: Capture and analyze PowerShell command history
4. **User Isolation**: Disable affected user accounts pending investigation

**Empire Indicators:**
- Base64 encoded PowerShell commands
- Empire-specific user agents in HTTP traffic
- PowerShell execution with hidden windows (-WindowStyle Hidden)
- Unusual PowerShell module loading patterns
- Persistence via registry run keys or scheduled tasks

**Investigation Steps:**
- Review PowerShell operational logs (Event ID 4103, 4104)
- Analyze PowerShell command history (%APPDATA%\Microsoft\Windows\PowerShell\PSReadLine\)
- Check for Empire stager artifacts in temporary directories
- Review network connections for C2 beacon patterns

**Containment Actions:**
- Implement PowerShell constrained language mode
- Enable PowerShell script block logging
- Deploy application whitelisting for PowerShell scripts
- Block known Empire C2 infrastructure

**Eradication Steps:**
- Remove Empire agent persistence mechanisms
- Clear PowerShell command history and logs
- Update antivirus signatures for Empire variants
- Patch vulnerabilities used for initial access

**Recovery Actions:**
- Rebuild compromised systems from clean images
- Implement enhanced PowerShell monitoring
- Deploy advanced threat protection solutions
- Conduct user awareness training on phishing