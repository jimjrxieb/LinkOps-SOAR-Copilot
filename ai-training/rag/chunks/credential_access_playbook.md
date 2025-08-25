# Credential Access Response Playbook

## Credential Dumping (T1003)

**Critical Priority Actions:**
1. **Immediate Isolation**: Network isolate affected domain controllers
2. **Password Reset**: Force password reset for all privileged accounts
3. **Kerberos Ticket Invalidation**: Clear all Kerberos tickets domain-wide
4. **Memory Analysis**: Capture memory dumps before system reboot

**Detection Indicators:**
- LSASS process memory access (Mimikatz, ProcDump)
- Unusual ntds.dit file access patterns
- SAM registry hive extraction attempts
- PowerShell credential access modules (Invoke-Mimikatz)

**Investigation Framework:**
- Review Security Event Logs for Event ID 4656 (handle to object requested)
- Analyze process creation events for credential access tools
- Check for DCSync attack patterns (Event ID 4662)
- Review network authentication patterns for Pass-the-Hash attempts

**Containment Measures:**
- Enable Credential Guard on all endpoints
- Implement LAPS for local administrator passwords
- Deploy privileged access workstations (PAWs)
- Configure just-in-time administration access

**Recovery Protocol:**
- Rebuild affected domain controllers from known-good backups
- Reset krbtgt account password twice (24-hour interval)
- Implement enhanced privileged account monitoring
- Deploy Windows Defender Credential Guard