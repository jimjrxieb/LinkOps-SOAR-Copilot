# Lateral Movement Response Playbook

## WMI-Based Lateral Movement (T1047)

**Immediate Actions:**
1. **Network Isolation**: Isolate affected systems from network segments
2. **Account Analysis**: Review service account permissions and usage patterns
3. **Process Analysis**: Examine WMI command history and parent processes
4. **Endpoint Forensics**: Collect memory dumps from source and destination hosts

**Investigation Steps:**
- Query Windows Event Logs for Event ID 4648 (explicit logon attempts)
- Review WMI Event Logs (Microsoft-Windows-WMI-Activity/Operational)
- Check for unusual process spawning from wmiprvse.exe
- Analyze network traffic for WMI-related communications (port 135, dynamic RPC ports)

**Containment Actions:**
- Disable compromised service accounts
- Block WMI access between network segments
- Deploy additional monitoring on critical servers
- Reset credentials for potentially compromised accounts

**Recovery Steps:**
- Rebuild compromised systems from known-good backups
- Implement enhanced WMI monitoring and logging
- Review and update service account permissions
- Deploy additional network segmentation controls

## Detection Patterns:**
- Unusual WMI process execution patterns
- Service account usage outside normal hours
- Cross-segment WMI communications
- Abnormal process parent-child relationships involving wmiprvse.exe