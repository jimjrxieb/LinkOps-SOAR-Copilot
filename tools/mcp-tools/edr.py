#!/usr/bin/env python3
"""
🛡️ EDR (Endpoint Detection & Response) MCP Tool Wrappers
========================================================
TAG: MCP-TOOLS-EDR
Purpose: Secure wrappers for LimaCharlie EDR operations with full guardrails
Security: All actions require preconditions, dry-run capability, and audit logging
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from uuid import uuid4

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# ==============================================================================
# Base Tool Framework with Guardrails
# ==============================================================================

class ToolPrecondition(BaseModel):
    """Tool precondition check"""
    name: str
    condition: str
    error_message: str

class ToolResult(BaseModel):
    """Standardized tool execution result"""
    tool_name: str
    action: str
    status: str  # success | failed | blocked | dry_run
    execution_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    
    # Execution details
    dry_run_result: Optional[str] = None
    output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    
    # Security and audit
    preconditions_passed: List[str] = []
    postconditions_verified: bool = False
    approval_token: Optional[str] = None
    audit_fields: Dict[str, Any] = {}
    
    # Rollback capability
    rollback_available: bool = False
    rollback_data: Optional[Dict[str, Any]] = None

class EDRToolBase:
    """Base class for EDR tools with security guardrails"""
    
    def __init__(self, lc_api_key: str = None, org_id: str = None):
        self.lc_api_key = lc_api_key or "MOCK_API_KEY"
        self.org_id = org_id or "mock-org"
        self.tool_name = "edr_base"
        
    async def execute(
        self,
        action: str,
        args: Dict[str, Any],
        dry_run: bool = True,
        approval_token: Optional[str] = None,
        timeout_seconds: int = 300
    ) -> ToolResult:
        """Execute tool action with full guardrails"""
        execution_id = str(uuid4())
        start_time = datetime.now()
        
        result = ToolResult(
            tool_name=self.tool_name,
            action=action,
            status="pending",
            execution_id=execution_id,
            start_time=start_time
        )
        
        try:
            # Step 1: Validate preconditions
            logger.info(f"[{execution_id}] 🔍 Validating preconditions for {self.tool_name}.{action}")
            precondition_result = await self._check_preconditions(action, args)
            
            if not precondition_result["passed"]:
                result.status = "blocked"
                result.error = f"Preconditions failed: {precondition_result['failed']}"
                result.end_time = datetime.now()
                return result
            
            result.preconditions_passed = precondition_result["passed_checks"]
            
            # Step 2: Execute or dry-run
            if dry_run:
                logger.info(f"[{execution_id}] 🔄 Dry-run mode: {self.tool_name}.{action}")
                dry_run_result = await self._dry_run(action, args)
                result.status = "dry_run"
                result.dry_run_result = dry_run_result
            else:
                # Check approval for non-dry-run
                if self._requires_approval(action, args) and not approval_token:
                    result.status = "blocked"
                    result.error = "Action requires approval token"
                    result.end_time = datetime.now()
                    return result
                
                logger.info(f"[{execution_id}] ⚡ Executing: {self.tool_name}.{action}")
                execution_result = await self._execute_action(action, args, timeout_seconds)
                
                result.status = execution_result["status"]
                result.output = execution_result.get("output")
                result.error = execution_result.get("error")
                result.rollback_available = execution_result.get("rollback_available", False)
                result.rollback_data = execution_result.get("rollback_data")
                
                # Step 3: Verify postconditions (if execution succeeded)
                if result.status == "success":
                    postcondition_result = await self._verify_postconditions(action, args, result.output)
                    result.postconditions_verified = postcondition_result
                    
                    if not postcondition_result:
                        logger.warning(f"[{execution_id}] ⚠️ Postcondition verification failed")
                        # Could trigger rollback here
            
            result.end_time = datetime.now()
            result.audit_fields = self._generate_audit_fields(action, args, result)
            
            logger.info(f"[{execution_id}] ✅ {self.tool_name}.{action} completed: {result.status}")
            return result
            
        except Exception as e:
            logger.error(f"[{execution_id}] ❌ {self.tool_name}.{action} failed: {e}")
            result.status = "failed"
            result.error = str(e)
            result.end_time = datetime.now()
            return result
    
    async def _check_preconditions(self, action: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Check preconditions - override in subclasses"""
        return {"passed": True, "failed": [], "passed_checks": []}
    
    async def _dry_run(self, action: str, args: Dict[str, Any]) -> str:
        """Generate dry-run plan - override in subclasses"""
        return f"Would execute {self.tool_name}.{action} with args: {args}"
    
    async def _execute_action(self, action: str, args: Dict[str, Any], timeout: int) -> Dict[str, Any]:
        """Execute the actual action - override in subclasses"""
        return {"status": "success", "output": {"message": "Mock execution"}}
    
    async def _verify_postconditions(self, action: str, args: Dict[str, Any], output: Dict[str, Any]) -> bool:
        """Verify postconditions - override in subclasses"""
        return True
    
    def _requires_approval(self, action: str, args: Dict[str, Any]) -> bool:
        """Check if action requires approval - override in subclasses"""
        return action in ["isolate_host", "kill_process", "block_hash"]
    
    def _generate_audit_fields(self, action: str, args: Dict[str, Any], result: ToolResult) -> Dict[str, Any]:
        """Generate audit fields"""
        return {
            "user": "whis_automation",
            "source_ip": "127.0.0.1", 
            "action_args": args,
            "execution_duration_ms": int((result.end_time - result.start_time).total_seconds() * 1000) if result.end_time else 0,
            "least_privilege_scope": self._get_privilege_scope(action, args)
        }
    
    def _get_privilege_scope(self, action: str, args: Dict[str, Any]) -> str:
        """Get the privilege scope for this action"""
        return "single_host"  # Default scope

# ==============================================================================
# EDR Host Isolation Tool
# ==============================================================================

class EDRIsolateHost(EDRToolBase):
    """Isolate host from network with safety checks"""
    
    def __init__(self, lc_api_key: str = None, org_id: str = None):
        super().__init__(lc_api_key, org_id)
        self.tool_name = "edr.isolate_host"
    
    async def _check_preconditions(self, action: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Check preconditions for host isolation"""
        passed_checks = []
        failed_checks = []
        
        # Required fields
        if not args.get("host"):
            failed_checks.append("Host identifier required")
        else:
            passed_checks.append("Host identifier provided")
        
        # Asset class restrictions
        asset_class = args.get("asset_class", "workstation")
        if asset_class in ["domain_controller", "database"] and not args.get("approval_granted"):
            failed_checks.append(f"Asset class {asset_class} requires approval")
        else:
            passed_checks.append("Asset class check passed")
        
        # Business hours check for critical assets
        criticality = args.get("criticality", "medium")
        if criticality == "critical" and not self._is_business_hours():
            if not args.get("emergency", False):
                failed_checks.append("Critical asset isolation outside business hours requires emergency flag")
        
        if not failed_checks:
            passed_checks.append("Business hours check passed")
        
        return {
            "passed": len(failed_checks) == 0,
            "failed": failed_checks,
            "passed_checks": passed_checks
        }
    
    async def _dry_run(self, action: str, args: Dict[str, Any]) -> str:
        isolation_type = args.get("isolation_type", "network")
        host = args.get("host")
        
        plan = f"""
ISOLATION PLAN for {host}:
1. Identify host in LimaCharlie (sensor lookup)
2. Set isolation mode: {isolation_type}
3. Verify network connectivity severed
4. Maintain management channel: {args.get('allow_management', True)}
5. Log isolation event with correlation ID
6. Rollback available: restore network connectivity

BLAST RADIUS: 1 host
REVERSIBLE: Yes (restore_network action available)
DURATION: Until manually restored
        """.strip()
        
        return plan
    
    async def _execute_action(self, action: str, args: Dict[str, Any], timeout: int) -> Dict[str, Any]:
        """Execute host isolation via LimaCharlie API"""
        host = args["host"]
        isolation_type = args.get("isolation_type", "network")
        
        # Mock LimaCharlie API call
        logger.info(f"🔒 Isolating host {host} (type: {isolation_type})")
        
        # Simulate API call delay
        await asyncio.sleep(2)
        
        # Mock successful isolation
        return {
            "status": "success",
            "output": {
                "host": host,
                "isolation_status": "isolated",
                "isolation_type": isolation_type,
                "sensor_id": f"sensor_{host}",
                "isolated_at": datetime.now().isoformat(),
                "management_channel": args.get("allow_management", True)
            },
            "rollback_available": True,
            "rollback_data": {
                "action": "restore_network",
                "host": host,
                "original_state": "connected"
            }
        }
    
    async def _verify_postconditions(self, action: str, args: Dict[str, Any], output: Dict[str, Any]) -> bool:
        """Verify host is actually isolated"""
        host = args["host"]
        
        # Mock verification - in real implementation, would check LC sensor status
        logger.info(f"🔍 Verifying isolation status for {host}")
        await asyncio.sleep(1)
        
        # Simulate successful verification
        return output.get("isolation_status") == "isolated"
    
    def _requires_approval(self, action: str, args: Dict[str, Any]) -> bool:
        """Host isolation requires approval for critical assets"""
        criticality = args.get("criticality", "medium")
        asset_class = args.get("asset_class", "workstation")
        
        return (
            criticality in ["high", "critical"] or
            asset_class in ["server", "domain_controller", "database"] or
            not self._is_business_hours()
        )
    
    def _get_privilege_scope(self, action: str, args: Dict[str, Any]) -> str:
        return f"host_isolation:{args.get('host', 'unknown')}"
    
    def _is_business_hours(self) -> bool:
        """Check if current time is within business hours (9 AM - 5 PM EST, weekdays)"""
        now = datetime.now()
        return (
            now.weekday() < 5 and  # Monday = 0, Friday = 4
            9 <= now.hour < 17
        )

# ==============================================================================
# EDR Process Termination Tool
# ==============================================================================

class EDRKillProcess(EDRToolBase):
    """Kill malicious processes with safety checks"""
    
    def __init__(self, lc_api_key: str = None, org_id: str = None):
        super().__init__(lc_api_key, org_id)
        self.tool_name = "edr.kill_process"
    
    async def _check_preconditions(self, action: str, args: Dict[str, Any]) -> Dict[str, Any]:
        passed_checks = []
        failed_checks = []
        
        # Required fields
        if not args.get("host"):
            failed_checks.append("Host identifier required")
        else:
            passed_checks.append("Host identifier provided")
        
        # Process identification
        if not (args.get("process_name") or args.get("process_id")):
            failed_checks.append("Process name or PID required")
        else:
            passed_checks.append("Process identification provided")
        
        # Critical process protection
        process_name = args.get("process_name", "")
        if process_name.lower() in ["winlogon.exe", "csrss.exe", "smss.exe", "services.exe"]:
            failed_checks.append(f"Cannot kill critical system process: {process_name}")
        else:
            passed_checks.append("Not a protected system process")
        
        return {
            "passed": len(failed_checks) == 0,
            "failed": failed_checks,
            "passed_checks": passed_checks
        }
    
    async def _dry_run(self, action: str, args: Dict[str, Any]) -> str:
        host = args.get("host")
        process_name = args.get("process_name")
        process_id = args.get("process_id")
        
        plan = f"""
PROCESS TERMINATION PLAN:
1. Identify process on {host}:
   - Name: {process_name or 'N/A'}
   - PID: {process_id or 'N/A'}
2. Verify process is not critical system process
3. Send SIGTERM to process (graceful)
4. If not terminated in 5s, send SIGKILL (forceful)
5. Verify process termination
6. Log termination event

BLAST RADIUS: 1 process on 1 host
REVERSIBLE: No (process cannot be un-killed)
RISK: Low (single process termination)
        """.strip()
        
        return plan
    
    async def _execute_action(self, action: str, args: Dict[str, Any], timeout: int) -> Dict[str, Any]:
        """Execute process termination via LimaCharlie"""
        host = args["host"]
        process_name = args.get("process_name")
        process_id = args.get("process_id")
        
        logger.info(f"⚡ Killing process {process_name or process_id} on {host}")
        
        # Simulate API call
        await asyncio.sleep(1)
        
        return {
            "status": "success",
            "output": {
                "host": host,
                "process_name": process_name,
                "process_id": process_id,
                "termination_method": "SIGKILL",
                "terminated_at": datetime.now().isoformat(),
                "exit_code": -9
            },
            "rollback_available": False,  # Cannot undo process termination
            "rollback_data": None
        }
    
    async def _verify_postconditions(self, action: str, args: Dict[str, Any], output: Dict[str, Any]) -> bool:
        """Verify process was terminated"""
        host = args["host"]
        process_id = output.get("process_id")
        
        logger.info(f"🔍 Verifying process {process_id} terminated on {host}")
        await asyncio.sleep(0.5)
        
        # Mock verification - process no longer running
        return True
    
    def _requires_approval(self, action: str, args: Dict[str, Any]) -> bool:
        """Process killing generally allowed, but check for critical processes"""
        process_name = args.get("process_name", "").lower()
        
        # Critical process patterns require approval
        critical_patterns = ["svchost", "explorer", "winlogon", "lsass"]
        return any(pattern in process_name for pattern in critical_patterns)

# ==============================================================================
# EDR Hash Blocking Tool
# ==============================================================================

class EDRBlockHash(EDRToolBase):
    """Block file hash across organization"""
    
    def __init__(self, lc_api_key: str = None, org_id: str = None):
        super().__init__(lc_api_key, org_id)
        self.tool_name = "edr.block_hash"
    
    async def _check_preconditions(self, action: str, args: Dict[str, Any]) -> Dict[str, Any]:
        passed_checks = []
        failed_checks = []
        
        # Required fields
        hash_value = args.get("hash")
        if not hash_value:
            failed_checks.append("File hash required")
        elif len(hash_value) not in [32, 40, 64]:  # MD5, SHA1, SHA256
            failed_checks.append("Invalid hash format")
        else:
            passed_checks.append("Valid hash format provided")
        
        # Scope validation
        scope = args.get("scope", "organization")
        if scope not in ["organization", "group", "sensor"]:
            failed_checks.append("Invalid scope - must be organization, group, or sensor")
        else:
            passed_checks.append("Valid scope provided")
        
        return {
            "passed": len(failed_checks) == 0,
            "failed": failed_checks,
            "passed_checks": passed_checks
        }
    
    async def _dry_run(self, action: str, args: Dict[str, Any]) -> str:
        hash_value = args.get("hash")
        hash_type = args.get("hash_type", "sha256")
        scope = args.get("scope", "organization")
        
        plan = f"""
HASH BLOCKING PLAN:
1. Add {hash_type.upper()} hash to blocklist: {hash_value[:16]}...
2. Scope: {scope}
3. Distribution: Push to all sensors in scope (~5 minutes)
4. Effect: Block execution + file creation with this hash
5. Quarantine: Move existing files with hash to quarantine
6. Rollback available: Remove hash from blocklist

BLAST RADIUS: All hosts in {scope}
REVERSIBLE: Yes (unblock_hash action)
PROPAGATION: ~5 minutes to all sensors
        """.strip()
        
        return plan
    
    async def _execute_action(self, action: str, args: Dict[str, Any], timeout: int) -> Dict[str, Any]:
        """Execute hash blocking via LimaCharlie"""
        hash_value = args["hash"]
        scope = args.get("scope", "organization")
        
        logger.info(f"🚫 Blocking hash {hash_value[:16]}... across {scope}")
        
        # Simulate API call
        await asyncio.sleep(2)
        
        return {
            "status": "success",
            "output": {
                "hash": hash_value,
                "hash_type": args.get("hash_type", "sha256"),
                "scope": scope,
                "blocked_at": datetime.now().isoformat(),
                "rule_id": f"block_{hash_value[:8]}",
                "sensors_updated": 150,  # Mock sensor count
                "quarantined_files": 3   # Mock files quarantined
            },
            "rollback_available": True,
            "rollback_data": {
                "action": "unblock_hash",
                "hash": hash_value,
                "rule_id": f"block_{hash_value[:8]}"
            }
        }
    
    async def _verify_postconditions(self, action: str, args: Dict[str, Any], output: Dict[str, Any]) -> bool:
        """Verify hash is blocked"""
        hash_value = args["hash"]
        
        logger.info(f"🔍 Verifying hash {hash_value[:16]}... is blocked")
        await asyncio.sleep(1)
        
        # Mock verification - hash is in blocklist
        return output.get("sensors_updated", 0) > 0
    
    def _requires_approval(self, action: str, args: Dict[str, Any]) -> bool:
        """Hash blocking across organization requires approval"""
        scope = args.get("scope", "organization")
        return scope == "organization"
    
    def _get_privilege_scope(self, action: str, args: Dict[str, Any]) -> str:
        return f"hash_block:{args.get('scope', 'organization')}"

# ==============================================================================
# EDR Artifact Collection Tool
# ==============================================================================

class EDRCollectArtifacts(EDRToolBase):
    """Collect forensic artifacts from endpoints"""
    
    def __init__(self, lc_api_key: str = None, org_id: str = None):
        super().__init__(lc_api_key, org_id)
        self.tool_name = "edr.collect_artifacts"
    
    async def _check_preconditions(self, action: str, args: Dict[str, Any]) -> Dict[str, Any]:
        passed_checks = []
        failed_checks = []
        
        # Required fields
        if not args.get("host"):
            failed_checks.append("Host identifier required")
        else:
            passed_checks.append("Host identifier provided")
        
        # Artifact types validation
        artifacts = args.get("artifacts", [])
        if not artifacts:
            failed_checks.append("At least one artifact type required")
        else:
            valid_artifacts = [
                "memory_dump", "process_list", "network_connections", 
                "file_system_timeline", "registry_snapshot", "event_logs"
            ]
            invalid = [a for a in artifacts if a not in valid_artifacts]
            if invalid:
                failed_checks.append(f"Invalid artifact types: {invalid}")
            else:
                passed_checks.append("Valid artifact types specified")
        
        return {
            "passed": len(failed_checks) == 0,
            "failed": failed_checks,
            "passed_checks": passed_checks
        }
    
    async def _dry_run(self, action: str, args: Dict[str, Any]) -> str:
        host = args.get("host")
        artifacts = args.get("artifacts", [])
        
        plan = f"""
ARTIFACT COLLECTION PLAN for {host}:

Artifacts to collect: {', '.join(artifacts)}

Collection steps:
1. Memory dump: ~2-8GB, 5-15 minutes
2. Process list: ~1MB, 30 seconds
3. Network connections: ~100KB, 10 seconds
4. File system timeline: ~10-100MB, 2-5 minutes
5. Registry snapshot: ~50-200MB, 3-8 minutes
6. Event logs: ~100MB-1GB, 1-3 minutes

Total estimated time: 15-45 minutes
Total estimated size: 2-10GB
Storage location: Secure evidence store
Retention: 90 days (configurable)

BLAST RADIUS: 1 host (read-only collection)
PERFORMANCE IMPACT: Low-Medium during collection
        """.strip()
        
        return plan
    
    async def _execute_action(self, action: str, args: Dict[str, Any], timeout: int) -> Dict[str, Any]:
        """Execute artifact collection"""
        host = args["host"]
        artifacts = args.get("artifacts", [])
        
        logger.info(f"📦 Collecting artifacts {artifacts} from {host}")
        
        # Simulate collection time based on artifact types
        collection_time = len(artifacts) * 2  # 2 seconds per artifact type (mock)
        await asyncio.sleep(min(collection_time, 10))  # Cap at 10 seconds for testing
        
        collected_artifacts = []
        for artifact in artifacts:
            collected_artifacts.append({
                "type": artifact,
                "size_bytes": 1024 * 1024 * (10 if artifact == "memory_dump" else 1),  # Mock sizes
                "collection_time": datetime.now().isoformat(),
                "storage_path": f"/evidence/{host}/{artifact}_{int(time.time())}.zip",
                "checksum": f"sha256:{artifact[:8]}{'0' * 56}"  # Mock checksum
            })
        
        return {
            "status": "success",
            "output": {
                "host": host,
                "artifacts": collected_artifacts,
                "total_size_bytes": sum(a["size_bytes"] for a in collected_artifacts),
                "collection_duration_seconds": collection_time,
                "evidence_bag_id": f"evidence_{host}_{int(time.time())}",
                "chain_of_custody": {
                    "collected_by": "whis_automation",
                    "collected_at": datetime.now().isoformat(),
                    "witness": "system_audit_log"
                }
            },
            "rollback_available": False,  # Evidence collection cannot be undone
            "rollback_data": None
        }
    
    async def _verify_postconditions(self, action: str, args: Dict[str, Any], output: Dict[str, Any]) -> bool:
        """Verify artifacts were collected successfully"""
        artifacts = output.get("artifacts", [])
        expected_count = len(args.get("artifacts", []))
        
        logger.info(f"🔍 Verifying {len(artifacts)} artifacts collected (expected: {expected_count})")
        
        return len(artifacts) == expected_count
    
    def _requires_approval(self, action: str, args: Dict[str, Any]) -> bool:
        """Memory dumps from critical systems require approval"""
        artifacts = args.get("artifacts", [])
        asset_class = args.get("asset_class", "workstation")
        
        return (
            "memory_dump" in artifacts and 
            asset_class in ["domain_controller", "database"]
        )

# ==============================================================================
# Factory Functions and Registry
# ==============================================================================

# Tool registry for easy instantiation
EDR_TOOLS = {
    "isolate_host": EDRIsolateHost,
    "kill_process": EDRKillProcess,
    "block_hash": EDRBlockHash,
    "collect_artifacts": EDRCollectArtifacts
}

async def create_edr_tool(tool_name: str, **config) -> EDRToolBase:
    """Factory function to create EDR tools"""
    if tool_name not in EDR_TOOLS:
        raise ValueError(f"Unknown EDR tool: {tool_name}. Available: {list(EDR_TOOLS.keys())}")
    
    tool_class = EDR_TOOLS[tool_name]
    return tool_class(**config)

async def execute_edr_action(
    tool_name: str,
    args: Dict[str, Any],
    dry_run: bool = True,
    approval_token: Optional[str] = None,
    **config
) -> ToolResult:
    """Execute an EDR action with full guardrails"""
    tool = await create_edr_tool(tool_name, **config)
    return await tool.execute(
        action=tool_name,
        args=args,
        dry_run=dry_run,
        approval_token=approval_token
    )

# ==============================================================================
# Testing and Validation
# ==============================================================================

async def test_edr_tools():
    """Test all EDR tools with mock data"""
    test_cases = [
        {
            "tool": "isolate_host",
            "args": {
                "host": "test-workstation-01",
                "asset_class": "workstation",
                "isolation_type": "network",
                "emergency": False
            }
        },
        {
            "tool": "kill_process",
            "args": {
                "host": "test-workstation-01",
                "process_name": "malicious.exe",
                "process_id": 1234
            }
        },
        {
            "tool": "block_hash",
            "args": {
                "hash": "d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2",
                "hash_type": "sha256",
                "scope": "organization"
            }
        },
        {
            "tool": "collect_artifacts",
            "args": {
                "host": "test-workstation-01",
                "artifacts": ["process_list", "network_connections"]
            }
        }
    ]
    
    print("🧪 Testing EDR tools...")
    for test_case in test_cases:
        print(f"\n🔧 Testing {test_case['tool']}...")
        
        # Test dry-run first
        result = await execute_edr_action(
            tool_name=test_case["tool"],
            args=test_case["args"],
            dry_run=True
        )
        
        print(f"Status: {result.status}")
        if result.dry_run_result:
            print(f"Dry-run plan:\n{result.dry_run_result}")
        
        print(f"Preconditions passed: {len(result.preconditions_passed)}")
        if result.error:
            print(f"Error: {result.error}")

if __name__ == "__main__":
    asyncio.run(test_edr_tools())