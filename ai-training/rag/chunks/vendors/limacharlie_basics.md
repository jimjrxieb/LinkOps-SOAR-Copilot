# LimaCharlie Endpoint Detection & Response

**LimaCharlie** is a SecOps Cloud Platform providing comprehensive endpoint detection and response (EDR) capabilities with real-time telemetry and automated response actions.

## Core Capabilities

### Real-time Endpoint Telemetry
- Process execution, network connections, file system changes
- Registry modifications, DNS queries, authentication events  
- Memory analysis and behavioral indicators
- Cross-platform support (Windows, macOS, Linux)

### Detection & Response Rules
- YARA signatures for malware detection
- D&R (Detection & Response) rules for behavioral analysis
- Custom rule creation with Sigma rule compatibility
- Integration with MITRE ATT&CK framework

### Artifact Collection
- Memory dumps, process trees, network artifacts
- File system forensics and timeline reconstruction
- Registry snapshots and configuration baselines
- Automated evidence preservation for investigations

### Remote Shell Access
- Secure command execution on endpoints
- File transfer capabilities for analysis
- Live investigation and incident response
- Privilege escalation detection and prevention

## Common Response Actions

### Isolation & Containment
```python
# Isolate endpoint from network
isolate_endpoint(sensor_id, duration_hours=24)

# Kill malicious process
terminate_process(sensor_id, process_id, kill_tree=True)

# Block file hash globally  
deny_hash_globally(file_hash, reason="Malware detected")
```

### Investigation & Analysis
```python
# Collect memory dump
collect_memory_dump(sensor_id, max_size_mb=2048)

# Get process ancestry
get_process_tree(sensor_id, process_id, depth=5)

# Extract network connections
get_network_connections(sensor_id, since_hours=24)
```

### Threat Hunting
```python
# Hunt for specific IOCs
hunt_indicators(ioc_list, sensor_groups=["production"])

# Search for lateral movement
hunt_pattern("network_connection", dst_port=445, protocol="tcp")

# Monitor for persistence mechanisms
monitor_persistence_locations(registry_keys, file_paths)
```

## Integration Architecture

**Your Environment**: LimaCharlie EDR integrated via webhook ingestion with automated SOAR response workflows.

```
LimaCharlie Sensor → Detection Rules → Webhook → WHIS SOAR → Automated Response
                     ↓
               Real-time Telemetry → SIEM (Splunk) → Correlation Engine
```

## Tool Wrappers

Pre-built WHIS integrations for common LimaCharlie operations:

- `lc_isolate_endpoint()` - Network isolation with approval workflows
- `lc_collect_artifacts()` - Automated evidence collection  
- `lc_terminate_process()` - Process termination with logging
- `lc_block_hash()` - Hash blocking across fleet
- `lc_hunt_indicators()` - IOC hunting with reporting

## Detection Use Cases

**Credential Access**: Monitor for LSASS dumps, Kerberoasting, credential harvesting
**Lateral Movement**: Detect Pass-the-Hash, RDP brute force, SMB enumeration  
**Defense Evasion**: Identify process hollowing, DLL injection, AV evasion
**Persistence**: Track scheduled tasks, registry changes, service creation
**Exfiltration**: Monitor large data transfers, DNS tunneling, unusual network activity

All LimaCharlie detections automatically trigger WHIS SOAR playbooks for consistent incident response across your environment.