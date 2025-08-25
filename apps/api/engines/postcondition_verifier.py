#!/usr/bin/env python3
"""
✅ Postcondition Verification System
=====================================
TAG: POSTCONDITION-VERIFICATION
Purpose: Verify that automated actions achieved expected outcomes
Security: Critical for preventing false positives and ensuring effectiveness
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# ==============================================================================
# Verification Status Enums
# ==============================================================================

class VerificationStatus(str, Enum):
    """Status of postcondition verification"""
    PENDING = "pending"
    VERIFYING = "verifying"
    PASSED = "passed"
    FAILED = "failed"
    PARTIAL = "partial"
    TIMEOUT = "timeout"
    ERROR = "error"

class VerificationAction(str, Enum):
    """Action to take based on verification result"""
    CONTINUE = "continue"
    RETRY = "retry"
    ROLLBACK = "rollback"
    ESCALATE = "escalate"
    IGNORE = "ignore"

# ==============================================================================
# Verification Models
# ==============================================================================

class PostconditionCheck(BaseModel):
    """Individual postcondition check"""
    name: str
    description: str
    check_type: str  # query, api_call, metric, state_check
    target: str  # What to check (host, user, process, etc.)
    expected_value: Any
    timeout_seconds: int = 60
    retry_count: int = 3
    retry_delay_seconds: int = 10

class VerificationResult(BaseModel):
    """Result of a postcondition verification"""
    check_name: str
    status: VerificationStatus
    actual_value: Optional[Any] = None
    expected_value: Any
    message: str
    timestamp: datetime = Field(default_factory=datetime.now)
    attempts: int = 1
    duration_seconds: float = 0

class VerificationReport(BaseModel):
    """Complete verification report for an action"""
    action_id: str
    tool_name: str
    checks_total: int
    checks_passed: int
    checks_failed: int
    overall_status: VerificationStatus
    results: List[VerificationResult]
    recommended_action: VerificationAction
    can_rollback: bool
    verification_time_seconds: float

# ==============================================================================
# Postcondition Verifier
# ==============================================================================

class PostconditionVerifier:
    """Verify postconditions after action execution"""
    
    def __init__(self, siem_client=None, edr_client=None, idp_client=None):
        self.siem_client = siem_client
        self.edr_client = edr_client
        self.idp_client = idp_client
        
        # Verification methods by tool
        self.verification_methods = {
            "edr.isolate_host": self._verify_host_isolation,
            "edr.kill_process": self._verify_process_termination,
            "edr.block_hash": self._verify_hash_blocked,
            "idp.disable_user": self._verify_user_disabled,
            "idp.revoke_tokens": self._verify_tokens_revoked,
            "net.block_ip": self._verify_ip_blocked,
            "net.block_domains": self._verify_domains_blocked,
            "net.rate_limit_ip": self._verify_rate_limit_active
        }
    
    async def verify_action(
        self,
        tool_name: str,
        action_args: Dict[str, Any],
        action_output: Dict[str, Any],
        runbook_postconditions: List[str]
    ) -> VerificationReport:
        """Verify postconditions for a completed action"""
        
        start_time = datetime.now()
        action_id = action_output.get("execution_id", "unknown")
        
        logger.info(f"🔍 Starting postcondition verification for {tool_name} (action: {action_id})")
        
        # Get verification method
        verify_method = self.verification_methods.get(tool_name)
        if not verify_method:
            logger.warning(f"No verification method for {tool_name} - skipping")
            return VerificationReport(
                action_id=action_id,
                tool_name=tool_name,
                checks_total=0,
                checks_passed=0,
                checks_failed=0,
                overall_status=VerificationStatus.PASSED,
                results=[],
                recommended_action=VerificationAction.CONTINUE,
                can_rollback=False,
                verification_time_seconds=0
            )
        
        # Execute verification
        results = await verify_method(action_args, action_output, runbook_postconditions)
        
        # Calculate summary
        checks_passed = sum(1 for r in results if r.status == VerificationStatus.PASSED)
        checks_failed = sum(1 for r in results if r.status == VerificationStatus.FAILED)
        checks_total = len(results)
        
        # Determine overall status
        if checks_failed == 0:
            overall_status = VerificationStatus.PASSED
            recommended_action = VerificationAction.CONTINUE
        elif checks_passed > 0:
            overall_status = VerificationStatus.PARTIAL
            recommended_action = VerificationAction.RETRY
        else:
            overall_status = VerificationStatus.FAILED
            recommended_action = VerificationAction.ROLLBACK
        
        verification_time = (datetime.now() - start_time).total_seconds()
        
        report = VerificationReport(
            action_id=action_id,
            tool_name=tool_name,
            checks_total=checks_total,
            checks_passed=checks_passed,
            checks_failed=checks_failed,
            overall_status=overall_status,
            results=results,
            recommended_action=recommended_action,
            can_rollback=action_output.get("rollback_available", False),
            verification_time_seconds=verification_time
        )
        
        logger.info(
            f"✅ Verification complete for {tool_name}: "
            f"{checks_passed}/{checks_total} passed, status: {overall_status}"
        )
        
        return report
    
    # ==============================================================================
    # Tool-Specific Verification Methods
    # ==============================================================================
    
    async def _verify_host_isolation(
        self,
        args: Dict[str, Any],
        output: Dict[str, Any],
        postconditions: List[str]
    ) -> List[VerificationResult]:
        """Verify host isolation was successful"""
        results = []
        host = args.get("host")
        
        # Check 1: EDR reports host as isolated
        logger.info(f"Checking EDR isolation status for {host}")
        edr_check = await self._check_edr_isolation_status(host)
        results.append(VerificationResult(
            check_name="edr_isolation_status",
            status=VerificationStatus.PASSED if edr_check else VerificationStatus.FAILED,
            actual_value="isolated" if edr_check else "not_isolated",
            expected_value="isolated",
            message=f"EDR isolation status for {host}"
        ))
        
        # Check 2: No new network connections from host
        logger.info(f"Checking network activity from {host}")
        net_check = await self._check_no_network_activity(host)
        results.append(VerificationResult(
            check_name="network_activity_ceased",
            status=VerificationStatus.PASSED if net_check else VerificationStatus.FAILED,
            actual_value="no_activity" if net_check else "activity_detected",
            expected_value="no_activity",
            message=f"Network activity check for {host}"
        ))
        
        # Check 3: Management channel still active (if required)
        if output.get("management_channel"):
            mgmt_check = await self._check_management_channel(host)
            results.append(VerificationResult(
                check_name="management_channel_active",
                status=VerificationStatus.PASSED if mgmt_check else VerificationStatus.FAILED,
                actual_value="active" if mgmt_check else "inactive",
                expected_value="active",
                message=f"Management channel for {host}"
            ))
        
        return results
    
    async def _verify_process_termination(
        self,
        args: Dict[str, Any],
        output: Dict[str, Any],
        postconditions: List[str]
    ) -> List[VerificationResult]:
        """Verify process was terminated"""
        results = []
        host = args.get("host")
        process_name = args.get("process_name")
        process_id = args.get("process_id")
        
        # Check: Process no longer running
        logger.info(f"Checking if process {process_name or process_id} terminated on {host}")
        process_check = await self._check_process_not_running(host, process_name, process_id)
        results.append(VerificationResult(
            check_name="process_terminated",
            status=VerificationStatus.PASSED if process_check else VerificationStatus.FAILED,
            actual_value="terminated" if process_check else "still_running",
            expected_value="terminated",
            message=f"Process {process_name or process_id} on {host}"
        ))
        
        # Check: No child processes spawned
        if process_id:
            child_check = await self._check_no_child_processes(host, process_id)
            results.append(VerificationResult(
                check_name="no_child_processes",
                status=VerificationStatus.PASSED if child_check else VerificationStatus.FAILED,
                actual_value="no_children" if child_check else "children_found",
                expected_value="no_children",
                message=f"Child processes of {process_id}"
            ))
        
        return results
    
    async def _verify_hash_blocked(
        self,
        args: Dict[str, Any],
        output: Dict[str, Any],
        postconditions: List[str]
    ) -> List[VerificationResult]:
        """Verify hash is blocked across organization"""
        results = []
        hash_value = args.get("hash")
        
        # Check: Hash in EDR blocklist
        logger.info(f"Checking if hash {hash_value[:16]}... is in blocklist")
        blocklist_check = await self._check_hash_in_blocklist(hash_value)
        results.append(VerificationResult(
            check_name="hash_in_blocklist",
            status=VerificationStatus.PASSED if blocklist_check else VerificationStatus.FAILED,
            actual_value="blocked" if blocklist_check else "not_blocked",
            expected_value="blocked",
            message=f"Hash {hash_value[:16]}... in blocklist"
        ))
        
        # Check: No new executions with this hash
        exec_check = await self._check_no_hash_executions(hash_value)
        results.append(VerificationResult(
            check_name="no_new_executions",
            status=VerificationStatus.PASSED if exec_check else VerificationStatus.FAILED,
            actual_value="no_executions" if exec_check else "executions_detected",
            expected_value="no_executions",
            message=f"Executions with hash {hash_value[:16]}..."
        ))
        
        return results
    
    async def _verify_user_disabled(
        self,
        args: Dict[str, Any],
        output: Dict[str, Any],
        postconditions: List[str]
    ) -> List[VerificationResult]:
        """Verify user account is disabled"""
        results = []
        user_id = args.get("user_id")
        
        # Check: Account status is disabled
        logger.info(f"Checking if user {user_id} is disabled")
        status_check = await self._check_user_account_status(user_id)
        results.append(VerificationResult(
            check_name="account_disabled",
            status=VerificationStatus.PASSED if status_check == "disabled" else VerificationStatus.FAILED,
            actual_value=status_check,
            expected_value="disabled",
            message=f"Account status for {user_id}"
        ))
        
        # Check: No active sessions
        session_check = await self._check_no_active_sessions(user_id)
        results.append(VerificationResult(
            check_name="no_active_sessions",
            status=VerificationStatus.PASSED if session_check else VerificationStatus.FAILED,
            actual_value="no_sessions" if session_check else "sessions_active",
            expected_value="no_sessions",
            message=f"Active sessions for {user_id}"
        ))
        
        # Check: Authentication failures increased (user trying to login)
        auth_check = await self._check_auth_failures_increased(user_id)
        # This is informational - not a failure if no attempts
        results.append(VerificationResult(
            check_name="auth_attempts_blocked",
            status=VerificationStatus.PASSED,
            actual_value="attempts_blocked" if auth_check else "no_attempts",
            expected_value="attempts_blocked_or_none",
            message=f"Authentication attempts for {user_id}"
        ))
        
        return results
    
    async def _verify_tokens_revoked(
        self,
        args: Dict[str, Any],
        output: Dict[str, Any],
        postconditions: List[str]
    ) -> List[VerificationResult]:
        """Verify tokens were revoked"""
        results = []
        user_id = args.get("user_id")
        
        # Check: No valid tokens exist
        logger.info(f"Checking if tokens revoked for {user_id}")
        token_check = await self._check_no_valid_tokens(user_id)
        results.append(VerificationResult(
            check_name="tokens_revoked",
            status=VerificationStatus.PASSED if token_check else VerificationStatus.FAILED,
            actual_value="all_revoked" if token_check else "tokens_still_valid",
            expected_value="all_revoked",
            message=f"Token status for {user_id}"
        ))
        
        # Check: Recent API calls failing with auth errors
        api_check = await self._check_api_auth_failures(user_id)
        results.append(VerificationResult(
            check_name="api_access_denied",
            status=VerificationStatus.PASSED if api_check else VerificationStatus.PARTIAL,
            actual_value="access_denied" if api_check else "no_api_attempts",
            expected_value="access_denied_or_none",
            message=f"API access for {user_id}"
        ))
        
        return results
    
    async def _verify_ip_blocked(
        self,
        args: Dict[str, Any],
        output: Dict[str, Any],
        postconditions: List[str]
    ) -> List[VerificationResult]:
        """Verify IP is blocked at firewall"""
        results = []
        ip_address = args.get("ip_address")
        
        # Check: Firewall rule active
        logger.info(f"Checking if IP {ip_address} is blocked")
        fw_check = await self._check_firewall_rule_active(ip_address)
        results.append(VerificationResult(
            check_name="firewall_rule_active",
            status=VerificationStatus.PASSED if fw_check else VerificationStatus.FAILED,
            actual_value="blocked" if fw_check else "not_blocked",
            expected_value="blocked",
            message=f"Firewall rule for {ip_address}"
        ))
        
        # Check: No traffic from/to IP
        traffic_check = await self._check_no_ip_traffic(ip_address)
        results.append(VerificationResult(
            check_name="traffic_blocked",
            status=VerificationStatus.PASSED if traffic_check else VerificationStatus.FAILED,
            actual_value="no_traffic" if traffic_check else "traffic_detected",
            expected_value="no_traffic",
            message=f"Traffic to/from {ip_address}"
        ))
        
        return results
    
    async def _verify_domains_blocked(
        self,
        args: Dict[str, Any],
        output: Dict[str, Any],
        postconditions: List[str]
    ) -> List[VerificationResult]:
        """Verify domains are blocked"""
        results = []
        domains = args.get("domains", [])
        
        for domain in domains:
            # Check: DNS resolution fails
            logger.info(f"Checking if domain {domain} is blocked")
            dns_check = await self._check_dns_blocked(domain)
            results.append(VerificationResult(
                check_name=f"dns_blocked_{domain}",
                status=VerificationStatus.PASSED if dns_check else VerificationStatus.FAILED,
                actual_value="blocked" if dns_check else "resolving",
                expected_value="blocked",
                message=f"DNS resolution for {domain}"
            ))
        
        # Check: Web filter active
        webfilter_check = await self._check_webfilter_active(domains)
        results.append(VerificationResult(
            check_name="webfilter_rules_active",
            status=VerificationStatus.PASSED if webfilter_check else VerificationStatus.FAILED,
            actual_value="active" if webfilter_check else "inactive",
            expected_value="active",
            message=f"Web filter for {len(domains)} domains"
        ))
        
        return results
    
    async def _verify_rate_limit_active(
        self,
        args: Dict[str, Any],
        output: Dict[str, Any],
        postconditions: List[str]
    ) -> List[VerificationResult]:
        """Verify rate limiting is active"""
        results = []
        ip_address = args.get("ip_address")
        rate_limit = args.get("rate_limit")
        
        # Check: Rate limit rule active
        logger.info(f"Checking if rate limit active for {ip_address}")
        rl_check = await self._check_rate_limit_rule(ip_address)
        results.append(VerificationResult(
            check_name="rate_limit_active",
            status=VerificationStatus.PASSED if rl_check else VerificationStatus.FAILED,
            actual_value="active" if rl_check else "inactive",
            expected_value="active",
            message=f"Rate limit for {ip_address}: {rate_limit}"
        ))
        
        # Check: Traffic rate reduced
        rate_check = await self._check_traffic_rate_reduced(ip_address)
        results.append(VerificationResult(
            check_name="traffic_rate_reduced",
            status=VerificationStatus.PASSED if rate_check else VerificationStatus.PARTIAL,
            actual_value="reduced" if rate_check else "unchanged",
            expected_value="reduced",
            message=f"Traffic rate from {ip_address}"
        ))
        
        return results
    
    # ==============================================================================
    # Mock Verification Helper Methods (replace with real API calls)
    # ==============================================================================
    
    async def _check_edr_isolation_status(self, host: str) -> bool:
        """Check if host is isolated in EDR"""
        await asyncio.sleep(0.5)  # Simulate API call
        return True  # Mock - host is isolated
    
    async def _check_no_network_activity(self, host: str) -> bool:
        """Check for network activity from host"""
        await asyncio.sleep(0.5)
        return True  # Mock - no activity
    
    async def _check_management_channel(self, host: str) -> bool:
        """Check if management channel is active"""
        await asyncio.sleep(0.2)
        return True  # Mock - channel active
    
    async def _check_process_not_running(self, host: str, process_name: str, process_id: int) -> bool:
        """Check if process is not running"""
        await asyncio.sleep(0.3)
        return True  # Mock - process terminated
    
    async def _check_no_child_processes(self, host: str, parent_pid: int) -> bool:
        """Check for child processes"""
        await asyncio.sleep(0.2)
        return True  # Mock - no children
    
    async def _check_hash_in_blocklist(self, hash_value: str) -> bool:
        """Check if hash is in blocklist"""
        await asyncio.sleep(0.3)
        return True  # Mock - hash blocked
    
    async def _check_no_hash_executions(self, hash_value: str) -> bool:
        """Check for executions with hash"""
        await asyncio.sleep(0.5)
        return True  # Mock - no executions
    
    async def _check_user_account_status(self, user_id: str) -> str:
        """Check user account status"""
        await asyncio.sleep(0.3)
        return "disabled"  # Mock - account disabled
    
    async def _check_no_active_sessions(self, user_id: str) -> bool:
        """Check for active user sessions"""
        await asyncio.sleep(0.3)
        return True  # Mock - no sessions
    
    async def _check_auth_failures_increased(self, user_id: str) -> bool:
        """Check if auth failures increased"""
        await asyncio.sleep(0.2)
        return False  # Mock - no recent attempts
    
    async def _check_no_valid_tokens(self, user_id: str) -> bool:
        """Check if tokens are revoked"""
        await asyncio.sleep(0.3)
        return True  # Mock - tokens revoked
    
    async def _check_api_auth_failures(self, user_id: str) -> bool:
        """Check for API auth failures"""
        await asyncio.sleep(0.2)
        return False  # Mock - no API attempts
    
    async def _check_firewall_rule_active(self, ip_address: str) -> bool:
        """Check if firewall rule is active"""
        await asyncio.sleep(0.3)
        return True  # Mock - rule active
    
    async def _check_no_ip_traffic(self, ip_address: str) -> bool:
        """Check for traffic to/from IP"""
        await asyncio.sleep(0.5)
        return True  # Mock - no traffic
    
    async def _check_dns_blocked(self, domain: str) -> bool:
        """Check if DNS is blocked for domain"""
        await asyncio.sleep(0.2)
        return True  # Mock - DNS blocked
    
    async def _check_webfilter_active(self, domains: List[str]) -> bool:
        """Check if web filter is active"""
        await asyncio.sleep(0.3)
        return True  # Mock - filter active
    
    async def _check_rate_limit_rule(self, ip_address: str) -> bool:
        """Check if rate limit rule is active"""
        await asyncio.sleep(0.2)
        return True  # Mock - rule active
    
    async def _check_traffic_rate_reduced(self, ip_address: str) -> bool:
        """Check if traffic rate is reduced"""
        await asyncio.sleep(0.3)
        return True  # Mock - rate reduced

# ==============================================================================
# Factory Function
# ==============================================================================

def create_postcondition_verifier(**config) -> PostconditionVerifier:
    """Create postcondition verifier instance"""
    return PostconditionVerifier(**config)

# ==============================================================================
# Testing
# ==============================================================================

async def test_postcondition_verification():
    """Test postcondition verification"""
    verifier = create_postcondition_verifier()
    
    # Test host isolation verification
    print("🧪 Testing host isolation verification...")
    report = await verifier.verify_action(
        tool_name="edr.isolate_host",
        action_args={"host": "workstation-01"},
        action_output={
            "execution_id": "test-123",
            "isolation_status": "isolated",
            "management_channel": True,
            "rollback_available": True
        },
        runbook_postconditions=["host_isolated", "c2_communication_blocked"]
    )
    
    print(f"Overall status: {report.overall_status}")
    print(f"Checks passed: {report.checks_passed}/{report.checks_total}")
    print(f"Recommended action: {report.recommended_action}")
    
    for result in report.results:
        print(f"  - {result.check_name}: {result.status} ({result.message})")

if __name__ == "__main__":
    asyncio.run(test_postcondition_verification())