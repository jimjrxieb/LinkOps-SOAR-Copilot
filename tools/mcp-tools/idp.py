#!/usr/bin/env python3
"""
🔐 IDP (Identity Provider) MCP Tool Wrappers  
=============================================
TAG: MCP-TOOLS-IDP
Purpose: Secure wrappers for identity operations (Azure AD, Okta, etc.) with guardrails
Security: All identity changes require explicit approvals and audit logging
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from uuid import uuid4

from pydantic import BaseModel, Field, validator

logger = logging.getLogger(__name__)

# ==============================================================================
# Import base tool framework from EDR
# ==============================================================================

from .edr import EDRToolBase, ToolResult

# ==============================================================================
# IDP User Management Tool
# ==============================================================================

class IDPDisableUser(EDRToolBase):
    """Disable user account with safety checks"""
    
    def __init__(self, tenant_id: str = None, client_id: str = None, api_key: str = None):
        super().__init__()
        self.tenant_id = tenant_id or "mock-tenant"
        self.client_id = client_id or "mock-client"
        self.api_key = api_key or "MOCK_API_KEY"
        self.tool_name = "idp.disable_user"
    
    async def _check_preconditions(self, action: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Check preconditions for user disable"""
        passed_checks = []
        failed_checks = []
        
        # Required fields
        user_id = args.get("user_id")
        if not user_id:
            failed_checks.append("User ID required")
        else:
            passed_checks.append("User ID provided")
        
        # Service account protection
        if self._is_service_account(user_id):
            if not args.get("service_account_override"):
                failed_checks.append("Cannot disable service account without override")
            else:
                passed_checks.append("Service account override provided")
        else:
            passed_checks.append("Not a service account")
        
        # Admin account protection
        if self._is_admin_account(user_id):
            if not args.get("admin_override"):
                failed_checks.append("Admin account disable requires override")
            else:
                passed_checks.append("Admin override provided")
        else:
            passed_checks.append("Not an admin account")
        
        # Break-glass protection
        if user_id.lower() in ["emergency", "breakglass", "admin"]:
            failed_checks.append("Cannot disable break-glass account")
        
        return {
            "passed": len(failed_checks) == 0,
            "failed": failed_checks,
            "passed_checks": passed_checks
        }
    
    async def _dry_run(self, action: str, args: Dict[str, Any]) -> str:
        user_id = args.get("user_id")
        reason = args.get("reason", "Security automated response")
        
        plan = f"""
USER DISABLE PLAN for {user_id}:
1. Validate user exists in identity provider
2. Check current user status and group memberships
3. Set account status to DISABLED
4. Revoke active authentication tokens
5. Remove from security groups (optional)
6. Send notification to user's manager
7. Log disable action with reason: {reason}
8. Rollback available: Re-enable account

BLAST RADIUS: 1 user account
REVERSIBLE: Yes (enable_user action)
NOTIFICATIONS: User's manager, Security team
COMPLIANCE: Audit log entry created
        """.strip()
        
        return plan
    
    async def _execute_action(self, action: str, args: Dict[str, Any], timeout: int) -> Dict[str, Any]:
        """Execute user disable via identity provider API"""
        user_id = args["user_id"]
        reason = args.get("reason", "Automated security response")
        
        logger.info(f"🔒 Disabling user account: {user_id}")
        
        # Simulate API calls
        await asyncio.sleep(1)  # User lookup
        await asyncio.sleep(1)  # Disable account
        await asyncio.sleep(0.5)  # Token revocation
        
        # Mock successful disable
        return {
            "status": "success",
            "output": {
                "user_id": user_id,
                "account_status": "disabled",
                "disabled_at": datetime.now().isoformat(),
                "disabled_by": "whis_automation",
                "reason": reason,
                "tokens_revoked": 3,  # Mock token count
                "groups_removed": [],  # Mock - usually empty for disable
                "manager_notified": True,
                "backup_method_disabled": True
            },
            "rollback_available": True,
            "rollback_data": {
                "action": "enable_user",
                "user_id": user_id,
                "original_state": "enabled",
                "restore_groups": []  # Would contain original groups
            }
        }
    
    async def _verify_postconditions(self, action: str, args: Dict[str, Any], output: Dict[str, Any]) -> bool:
        """Verify user account is disabled"""
        user_id = args["user_id"]
        
        logger.info(f"🔍 Verifying user {user_id} is disabled")
        await asyncio.sleep(0.5)
        
        # Mock verification - account status is disabled
        return output.get("account_status") == "disabled"
    
    def _requires_approval(self, action: str, args: Dict[str, Any]) -> bool:
        """User disabling generally requires approval"""
        user_id = args.get("user_id", "")
        
        # Always require approval except for automated emergency responses
        return not args.get("emergency_disable", False)
    
    def _is_service_account(self, user_id: str) -> bool:
        """Check if user is a service account"""
        service_patterns = ["svc-", "service-", "sa-", "system-", "app-"]
        return any(user_id.lower().startswith(pattern) for pattern in service_patterns)
    
    def _is_admin_account(self, user_id: str) -> bool:
        """Check if user is an admin account"""
        admin_patterns = ["admin", "administrator", "root", "superuser"]
        return any(pattern in user_id.lower() for pattern in admin_patterns)
    
    def _get_privilege_scope(self, action: str, args: Dict[str, Any]) -> str:
        return f"user_disable:{args.get('user_id', 'unknown')}"

# ==============================================================================
# IDP Token Revocation Tool
# ==============================================================================

class IDPRevokeTokens(EDRToolBase):
    """Revoke user authentication tokens"""
    
    def __init__(self, tenant_id: str = None, client_id: str = None, api_key: str = None):
        super().__init__()
        self.tenant_id = tenant_id or "mock-tenant"
        self.client_id = client_id or "mock-client" 
        self.api_key = api_key or "MOCK_API_KEY"
        self.tool_name = "idp.revoke_tokens"
    
    async def _check_preconditions(self, action: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Check preconditions for token revocation"""
        passed_checks = []
        failed_checks = []
        
        # Required fields
        user_id = args.get("user_id")
        if not user_id:
            failed_checks.append("User ID required")
        else:
            passed_checks.append("User ID provided")
        
        # Token types validation
        token_types = args.get("token_types", ["access_token", "refresh_token"])
        valid_types = ["access_token", "refresh_token", "id_token", "all"]
        invalid_types = [t for t in token_types if t not in valid_types]
        
        if invalid_types:
            failed_checks.append(f"Invalid token types: {invalid_types}")
        else:
            passed_checks.append("Valid token types specified")
        
        return {
            "passed": len(failed_checks) == 0,
            "failed": failed_checks,
            "passed_checks": passed_checks
        }
    
    async def _dry_run(self, action: str, args: Dict[str, Any]) -> str:
        user_id = args.get("user_id")
        token_types = args.get("token_types", ["access_token", "refresh_token"])
        
        plan = f"""
TOKEN REVOCATION PLAN for {user_id}:
1. Enumerate active tokens for user
2. Revoke token types: {', '.join(token_types)}
3. Invalidate sessions across all applications
4. Force re-authentication on next access
5. Update token revocation list (TRL)
6. Notify affected applications
7. Log revocation event

TOKEN TYPES TO REVOKE: {', '.join(token_types)}
BLAST RADIUS: All active sessions for 1 user
REVERSIBLE: No (tokens cannot be un-revoked)
EFFECT: User forced to re-authenticate immediately
        """.strip()
        
        return plan
    
    async def _execute_action(self, action: str, args: Dict[str, Any], timeout: int) -> Dict[str, Any]:
        """Execute token revocation via identity provider"""
        user_id = args["user_id"]
        token_types = args.get("token_types", ["access_token", "refresh_token"])
        
        logger.info(f"🔑 Revoking tokens for user: {user_id} (types: {token_types})")
        
        # Simulate API calls
        await asyncio.sleep(1)  # Enumerate tokens
        await asyncio.sleep(1)  # Revoke tokens
        await asyncio.sleep(0.5)  # Update TRL
        
        # Count revoked tokens (mock)
        token_counts = {
            "access_token": 5,
            "refresh_token": 3,
            "id_token": 2,
            "all": 15
        }
        
        total_revoked = sum(token_counts.get(t, 0) for t in token_types)
        
        return {
            "status": "success",
            "output": {
                "user_id": user_id,
                "token_types_revoked": token_types,
                "total_tokens_revoked": total_revoked,
                "revoked_at": datetime.now().isoformat(),
                "revoked_by": "whis_automation",
                "sessions_invalidated": total_revoked,
                "applications_notified": ["office365", "sharepoint", "teams", "azure_portal"],
                "trl_updated": True
            },
            "rollback_available": False,  # Tokens cannot be un-revoked
            "rollback_data": None
        }
    
    async def _verify_postconditions(self, action: str, args: Dict[str, Any], output: Dict[str, Any]) -> bool:
        """Verify tokens were revoked"""
        user_id = args["user_id"]
        
        logger.info(f"🔍 Verifying tokens revoked for {user_id}")
        await asyncio.sleep(0.5)
        
        # Mock verification - tokens revoked successfully
        return output.get("total_tokens_revoked", 0) > 0
    
    def _requires_approval(self, action: str, args: Dict[str, Any]) -> bool:
        """Token revocation for service accounts requires approval"""
        user_id = args.get("user_id", "")
        return self._is_service_account(user_id)
    
    def _is_service_account(self, user_id: str) -> bool:
        """Check if user is a service account"""
        service_patterns = ["svc-", "service-", "sa-", "system-", "app-"]
        return any(user_id.lower().startswith(pattern) for pattern in service_patterns)
    
    def _get_privilege_scope(self, action: str, args: Dict[str, Any]) -> str:
        return f"token_revoke:{args.get('user_id', 'unknown')}"

# ==============================================================================
# IDP User Lookup Tool
# ==============================================================================

class IDPGetUserDetails(EDRToolBase):
    """Get user details and status (read-only)"""
    
    def __init__(self, tenant_id: str = None, client_id: str = None, api_key: str = None):
        super().__init__()
        self.tenant_id = tenant_id or "mock-tenant"
        self.client_id = client_id or "mock-client"
        self.api_key = api_key or "MOCK_API_KEY"
        self.tool_name = "idp.get_user_details"
    
    async def _check_preconditions(self, action: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Check preconditions for user lookup"""
        passed_checks = []
        failed_checks = []
        
        # Required fields
        user_id = args.get("user_id")
        if not user_id:
            failed_checks.append("User ID required")
        else:
            passed_checks.append("User ID provided")
        
        return {
            "passed": len(failed_checks) == 0,
            "failed": failed_checks,
            "passed_checks": passed_checks
        }
    
    async def _dry_run(self, action: str, args: Dict[str, Any]) -> str:
        user_id = args.get("user_id")
        include_activity = args.get("include_recent_activity", False)
        
        plan = f"""
USER LOOKUP PLAN for {user_id}:
1. Query user profile from identity provider
2. Get account status and properties
3. List group memberships and roles
4. Check last sign-in time
{'5. Get recent activity logs (optional)' if include_activity else ''}
6. Return user information

OPERATION TYPE: Read-only
BLAST RADIUS: None (information gathering only)
PRIVACY: Respects data governance policies
        """.strip()
        
        return plan
    
    async def _execute_action(self, action: str, args: Dict[str, Any], timeout: int) -> Dict[str, Any]:
        """Execute user lookup via identity provider"""
        user_id = args["user_id"]
        include_activity = args.get("include_recent_activity", False)
        
        logger.info(f"👤 Looking up user details: {user_id}")
        
        # Simulate API calls
        await asyncio.sleep(0.5)  # User profile lookup
        if include_activity:
            await asyncio.sleep(1)  # Activity logs
        
        # Mock user details
        user_details = {
            "user_id": user_id,
            "display_name": f"User {user_id}",
            "email": f"{user_id}@company.com",
            "account_enabled": True,
            "account_type": "Member",
            "created_date": "2022-01-15T10:30:00Z",
            "last_sign_in": "2024-08-24T14:22:00Z",
            "sign_in_count": 1247,
            "groups": ["Security-Team", "IT-Staff", "All-Users"],
            "roles": ["User", "Security Reader"],
            "department": "Information Technology",
            "manager": "manager@company.com",
            "mfa_enabled": True,
            "risk_level": "low"
        }
        
        if include_activity:
            user_details["recent_activity"] = [
                {
                    "timestamp": "2024-08-24T14:22:00Z",
                    "activity": "Sign-in",
                    "application": "Azure Portal",
                    "ip_address": "10.0.1.100",
                    "location": "New York, US"
                },
                {
                    "timestamp": "2024-08-24T09:15:00Z", 
                    "activity": "Password change",
                    "application": "Self-Service Password Reset",
                    "ip_address": "10.0.1.100",
                    "location": "New York, US"
                }
            ]
        
        return {
            "status": "success",
            "output": user_details,
            "rollback_available": False,  # Read-only operation
            "rollback_data": None
        }
    
    async def _verify_postconditions(self, action: str, args: Dict[str, Any], output: Dict[str, Any]) -> bool:
        """Verify user lookup succeeded"""
        return "user_id" in output and output["user_id"] == args.get("user_id")
    
    def _requires_approval(self, action: str, args: Dict[str, Any]) -> bool:
        """Read-only operations generally don't require approval"""
        return False  # Unless querying sensitive admin accounts
    
    def _get_privilege_scope(self, action: str, args: Dict[str, Any]) -> str:
        return f"user_read:{args.get('user_id', 'unknown')}"

# ==============================================================================
# IDP User Status Check Tool  
# ==============================================================================

class IDPGetUserStatus(EDRToolBase):
    """Get user status (minimal read-only)"""
    
    def __init__(self, tenant_id: str = None, client_id: str = None, api_key: str = None):
        super().__init__()
        self.tenant_id = tenant_id or "mock-tenant"
        self.client_id = client_id or "mock-client"
        self.api_key = api_key or "MOCK_API_KEY" 
        self.tool_name = "idp.get_user_status"
    
    async def _check_preconditions(self, action: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Check preconditions for user status check"""
        passed_checks = []
        failed_checks = []
        
        user_id = args.get("user_id")
        if not user_id:
            failed_checks.append("User ID required")
        else:
            passed_checks.append("User ID provided")
        
        return {
            "passed": len(failed_checks) == 0,
            "failed": failed_checks,
            "passed_checks": passed_checks
        }
    
    async def _dry_run(self, action: str, args: Dict[str, Any]) -> str:
        user_id = args.get("user_id")
        
        plan = f"""
USER STATUS CHECK for {user_id}:
1. Query basic user status from identity provider
2. Check if account is enabled/disabled
3. Get last authentication timestamp
4. Return minimal status information

OPERATION TYPE: Read-only (minimal data)
BLAST RADIUS: None
PURPOSE: Status verification for automation decisions
        """.strip()
        
        return plan
    
    async def _execute_action(self, action: str, args: Dict[str, Any], timeout: int) -> Dict[str, Any]:
        """Execute minimal user status check"""
        user_id = args["user_id"]
        
        logger.info(f"📊 Checking user status: {user_id}")
        
        await asyncio.sleep(0.2)  # Quick status check
        
        return {
            "status": "success",
            "output": {
                "user_id": user_id,
                "account_enabled": True,
                "last_sign_in": "2024-08-24T14:22:00Z",
                "days_since_last_sign_in": 0,
                "account_locked": False,
                "password_expired": False,
                "mfa_enabled": True,
                "risk_state": "low"
            },
            "rollback_available": False,
            "rollback_data": None
        }
    
    async def _verify_postconditions(self, action: str, args: Dict[str, Any], output: Dict[str, Any]) -> bool:
        """Verify status check succeeded"""
        return "account_enabled" in output
    
    def _requires_approval(self, action: str, args: Dict[str, Any]) -> bool:
        return False  # Read-only status check
    
    def _get_privilege_scope(self, action: str, args: Dict[str, Any]) -> str:
        return f"user_status:{args.get('user_id', 'unknown')}"

# ==============================================================================
# Factory Functions and Registry  
# ==============================================================================

IDP_TOOLS = {
    "disable_user": IDPDisableUser,
    "revoke_tokens": IDPRevokeTokens,
    "get_user_details": IDPGetUserDetails,
    "get_user_status": IDPGetUserStatus
}

async def create_idp_tool(tool_name: str, **config) -> EDRToolBase:
    """Factory function to create IDP tools"""
    if tool_name not in IDP_TOOLS:
        raise ValueError(f"Unknown IDP tool: {tool_name}. Available: {list(IDP_TOOLS.keys())}")
    
    tool_class = IDP_TOOLS[tool_name]
    return tool_class(**config)

async def execute_idp_action(
    tool_name: str,
    args: Dict[str, Any],
    dry_run: bool = True,
    approval_token: Optional[str] = None,
    **config
) -> ToolResult:
    """Execute an IDP action with full guardrails"""
    tool = await create_idp_tool(tool_name, **config)
    return await tool.execute(
        action=tool_name,
        args=args,
        dry_run=dry_run,
        approval_token=approval_token
    )

# ==============================================================================
# Testing and Validation
# ==============================================================================

async def test_idp_tools():
    """Test all IDP tools with mock data"""
    test_cases = [
        {
            "tool": "get_user_status",
            "args": {
                "user_id": "john.doe"
            }
        },
        {
            "tool": "get_user_details", 
            "args": {
                "user_id": "john.doe",
                "include_recent_activity": True
            }
        },
        {
            "tool": "disable_user",
            "args": {
                "user_id": "suspected.user",
                "reason": "Suspected compromise - automated response",
                "emergency_disable": False
            }
        },
        {
            "tool": "revoke_tokens",
            "args": {
                "user_id": "suspected.user",
                "token_types": ["access_token", "refresh_token"]
            }
        }
    ]
    
    print("🧪 Testing IDP tools...")
    for test_case in test_cases:
        print(f"\n🔧 Testing {test_case['tool']}...")
        
        # Test dry-run first
        result = await execute_idp_action(
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
    asyncio.run(test_idp_tools())