#!/usr/bin/env python3
"""
📊 SIEM MCP Tool Wrappers
========================
TAG: MCP-TOOLS-SIEM  
Purpose: Secure wrappers for SIEM operations (Splunk searches, etc.) with guardrails
Security: Read-only operations with query validation and rate limiting
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from uuid import uuid4
import hashlib

from pydantic import BaseModel, Field, validator

logger = logging.getLogger(__name__)

# ==============================================================================
# Import base tool framework
# ==============================================================================

from .edr import EDRToolBase, ToolResult

# ==============================================================================
# SIEM Saved Search Tool
# ==============================================================================

class SIEMSavedSearch(EDRToolBase):
    """Execute saved searches in SIEM with safety controls"""
    
    def __init__(self, splunk_api: str = None, auth_token: str = None):
        super().__init__()
        self.splunk_api = splunk_api or "https://splunk.company.com:8089"
        self.auth_token = auth_token or "MOCK_AUTH_TOKEN"
        self.tool_name = "siem.saved_search"
        
        # Query templates for common investigations
        self.query_templates = {
            "brute_force_context": {
                "spl": 'index=* src={source_ip} user={user} (EventCode=4625 OR EventCode=4624) | stats count by _time user src | where count > 5',
                "description": "Authentication failures and successes from source IP",
                "max_results": 1000
            },
            "lateral_movement": {
                "spl": 'index=* user={user} (EventCode=4624 OR EventCode=4648) | eval logon_type=case(EventCode=4624,"Interactive",EventCode=4648,"Explicit") | stats count by dest user logon_type',
                "description": "User logon activity across multiple hosts",
                "max_results": 500
            },
            "powershell_activity": {
                "spl": 'index=* (powershell.exe OR pwsh.exe) host={host} | stats count by CommandLine user | where count > 1',
                "description": "PowerShell command execution on host",
                "max_results": 200
            },
            "c2_beacon": {
                "spl": 'index=* (src={ip_list} OR dest={ip_list}) | stats count by src dest bytes_out bytes_in | where count > 10',
                "description": "Network communication with suspected C2 IPs",
                "max_results": 500
            },
            "host_context": {
                "spl": 'index=* host={host} | head 100 | stats count by sourcetype EventCode user',
                "description": "General activity context for host",
                "max_results": 100
            }
        }
    
    async def _check_preconditions(self, action: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Check preconditions for SIEM search"""
        passed_checks = []
        failed_checks = []
        
        # Query validation
        query_template = args.get("query_template")
        custom_query = args.get("custom_query")
        
        if not query_template and not custom_query:
            failed_checks.append("Either query_template or custom_query required")
        elif query_template and query_template not in self.query_templates:
            failed_checks.append(f"Unknown query template: {query_template}. Available: {list(self.query_templates.keys())}")
        else:
            passed_checks.append("Query source validated")
        
        # Custom query safety checks
        if custom_query:
            safety_issues = self._validate_custom_query(custom_query)
            if safety_issues:
                failed_checks.extend(safety_issues)
            else:
                passed_checks.append("Custom query safety checks passed")
        
        # Timeframe validation
        timeframe = args.get("timeframe", "4h")
        if not self._is_valid_timeframe(timeframe):
            failed_checks.append(f"Invalid timeframe: {timeframe}")
        else:
            passed_checks.append("Valid timeframe provided")
        
        # Rate limiting check
        if not self._check_rate_limit():
            failed_checks.append("Rate limit exceeded - too many recent searches")
        else:
            passed_checks.append("Rate limit check passed")
        
        return {
            "passed": len(failed_checks) == 0,
            "failed": failed_checks,
            "passed_checks": passed_checks
        }
    
    async def _dry_run(self, action: str, args: Dict[str, Any]) -> str:
        query_template = args.get("query_template")
        custom_query = args.get("custom_query")
        timeframe = args.get("timeframe", "4h")
        
        if query_template:
            template_info = self.query_templates[query_template]
            query = template_info["spl"]
            description = template_info["description"]
            max_results = template_info["max_results"]
        else:
            query = custom_query
            description = "Custom SIEM search"
            max_results = args.get("max_results", 1000)
        
        # Substitute parameters
        substituted_query = self._substitute_query_params(query, args)
        
        plan = f"""
SIEM SEARCH PLAN:
Description: {description}
Timeframe: {timeframe} (earliest=-{timeframe})

Query to execute:
{substituted_query}

Execution details:
1. Connect to Splunk API
2. Submit search job with timeframe
3. Wait for job completion (max 5 minutes)
4. Retrieve results (max {max_results} events)
5. Format and return results
6. Log search execution for audit

OPERATION TYPE: Read-only
BLAST RADIUS: None (information gathering only)
PERFORMANCE IMPACT: Low (pre-approved search patterns)
        """.strip()
        
        return plan
    
    async def _execute_action(self, action: str, args: Dict[str, Any], timeout: int) -> Dict[str, Any]:
        """Execute SIEM search via Splunk API"""
        query_template = args.get("query_template")
        custom_query = args.get("custom_query")
        timeframe = args.get("timeframe", "4h")
        
        if query_template:
            template_info = self.query_templates[query_template]
            query = template_info["spl"]
            max_results = template_info.get("max_results", 1000)
        else:
            query = custom_query
            max_results = args.get("max_results", 1000)
        
        # Substitute parameters
        final_query = self._substitute_query_params(query, args)
        
        logger.info(f"🔍 Executing SIEM search: {query_template or 'custom'}")
        
        # Simulate Splunk search
        search_id = f"search_{int(time.time())}"
        await asyncio.sleep(2)  # Search execution time
        
        # Mock search results based on template
        results = self._generate_mock_results(query_template or "custom", args)
        
        return {
            "status": "success",
            "output": {
                "search_id": search_id,
                "query_template": query_template,
                "executed_query": final_query,
                "timeframe": timeframe,
                "results": results,
                "result_count": len(results),
                "max_results": max_results,
                "execution_time_seconds": 2.1,
                "search_started": datetime.now().isoformat(),
                "search_completed": datetime.now().isoformat(),
                "truncated": len(results) >= max_results
            },
            "rollback_available": False,  # Read-only operation
            "rollback_data": None
        }
    
    async def _verify_postconditions(self, action: str, args: Dict[str, Any], output: Dict[str, Any]) -> bool:
        """Verify search executed successfully"""
        return (
            "results" in output and 
            "result_count" in output and
            output["result_count"] >= 0
        )
    
    def _requires_approval(self, action: str, args: Dict[str, Any]) -> bool:
        """SIEM searches generally don't require approval (read-only)"""
        # Only require approval for custom queries that might be resource-intensive
        custom_query = args.get("custom_query")
        if custom_query:
            # Check for potentially expensive operations
            expensive_patterns = ["inputlookup", "rest", "dbxquery", "join", "subsearch"]
            return any(pattern in custom_query.lower() for pattern in expensive_patterns)
        return False
    
    def _validate_custom_query(self, query: str) -> List[str]:
        """Validate custom query for safety"""
        issues = []
        query_lower = query.lower()
        
        # Dangerous commands
        dangerous_commands = [
            "outputlookup",  # Write operations
            "delete",        # Data deletion
            "| rest",        # System REST API access  
            "| dbxquery",    # Database queries
            "sendalert"      # External alerting
        ]
        
        for cmd in dangerous_commands:
            if cmd in query_lower:
                issues.append(f"Dangerous command not allowed: {cmd}")
        
        # Query complexity limits
        if query_lower.count("join") > 2:
            issues.append("Too many join operations (max 2)")
        
        if query_lower.count("subsearch") > 1:
            issues.append("Too many subsearch operations (max 1)")
        
        # Time range requirements
        if "earliest" not in query_lower and "timeframe" not in query_lower:
            issues.append("Query must include time constraints")
        
        return issues
    
    def _is_valid_timeframe(self, timeframe: str) -> bool:
        """Validate timeframe format"""
        valid_formats = [
            "15m", "30m", "1h", "2h", "4h", "8h", "12h", "24h", 
            "2d", "3d", "7d", "30d"
        ]
        return timeframe in valid_formats
    
    def _check_rate_limit(self) -> bool:
        """Check if we're within rate limits for searches"""
        # Mock rate limiting - in real implementation would check recent search history
        return True  # Allow for now
    
    def _substitute_query_params(self, query: str, args: Dict[str, Any]) -> str:
        """Substitute parameters in query template"""
        substitutions = {
            "{host}": args.get("host", "unknown"),
            "{user}": args.get("user", "unknown"),
            "{source_ip}": args.get("source_ip", "unknown"),
            "{ip_list}": " OR ".join(args.get("ip_addresses", ["unknown"])),
            "{timeframe}": args.get("timeframe", "4h")
        }
        
        final_query = query
        for placeholder, value in substitutions.items():
            final_query = final_query.replace(placeholder, str(value))
        
        return final_query
    
    def _generate_mock_results(self, query_type: str, args: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate mock search results based on query type"""
        if query_type == "brute_force_context":
            return [
                {
                    "_time": "2024-08-24T14:22:00Z",
                    "user": args.get("user", "testuser"),
                    "src": args.get("source_ip", "192.168.1.100"),
                    "EventCode": "4625",
                    "count": 25
                },
                {
                    "_time": "2024-08-24T14:25:00Z", 
                    "user": args.get("user", "testuser"),
                    "src": args.get("source_ip", "192.168.1.100"),
                    "EventCode": "4624",
                    "count": 1
                }
            ]
        elif query_type == "powershell_activity":
            return [
                {
                    "_time": "2024-08-24T14:20:00Z",
                    "host": args.get("host", "workstation-01"),
                    "CommandLine": "powershell.exe -NoProfile -Command IEX",
                    "user": "DOMAIN\\testuser",
                    "count": 3
                }
            ]
        elif query_type == "host_context":
            return [
                {
                    "sourcetype": "WinEventLog:Security",
                    "EventCode": "4624",
                    "user": "testuser",
                    "count": 15
                },
                {
                    "sourcetype": "WinEventLog:System", 
                    "EventCode": "7045",
                    "user": "SYSTEM",
                    "count": 2
                }
            ]
        else:
            return [
                {
                    "_time": "2024-08-24T14:22:00Z",
                    "message": "Mock search result",
                    "host": args.get("host", "unknown"),
                    "count": 1
                }
            ]
    
    def _get_privilege_scope(self, action: str, args: Dict[str, Any]) -> str:
        query_template = args.get("query_template", "custom")
        return f"siem_search:{query_template}"

# ==============================================================================
# SIEM Context Gathering Tool
# ==============================================================================

class SIEMGatherContext(EDRToolBase):
    """Gather contextual information around security events"""
    
    def __init__(self, splunk_api: str = None, auth_token: str = None):
        super().__init__()
        self.splunk_api = splunk_api or "https://splunk.company.com:8089"
        self.auth_token = auth_token or "MOCK_AUTH_TOKEN"
        self.tool_name = "siem.gather_context"
    
    async def _check_preconditions(self, action: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Check preconditions for context gathering"""
        passed_checks = []
        failed_checks = []
        
        # Required fields
        fields = args.get("fields", [])
        if not fields:
            failed_checks.append("At least one field required for context gathering")
        else:
            passed_checks.append(f"Context fields provided: {', '.join(fields)}")
        
        # Timeframe validation
        timeframe = args.get("timeframe", "24h") 
        if not self._is_valid_timeframe(timeframe):
            failed_checks.append(f"Invalid timeframe: {timeframe}")
        else:
            passed_checks.append("Valid timeframe provided")
        
        return {
            "passed": len(failed_checks) == 0,
            "failed": failed_checks,
            "passed_checks": passed_checks
        }
    
    async def _dry_run(self, action: str, args: Dict[str, Any]) -> str:
        fields = args.get("fields", [])
        timeframe = args.get("timeframe", "24h")
        
        plan = f"""
CONTEXT GATHERING PLAN:
Fields to analyze: {', '.join(fields)}
Timeframe: Last {timeframe}

Context searches to perform:
1. Event frequency analysis for each field
2. Timeline of related events
3. Associated users and hosts
4. Network connections and traffic patterns
5. Process execution context
6. Authentication events correlation

OPERATION TYPE: Read-only analysis
BLAST RADIUS: None (information gathering)
MULTIPLE SEARCHES: Yes (one per context area)
        """.strip()
        
        return plan
    
    async def _execute_action(self, action: str, args: Dict[str, Any], timeout: int) -> Dict[str, Any]:
        """Execute context gathering via multiple SIEM searches"""
        fields = args["fields"]
        timeframe = args.get("timeframe", "24h")
        
        logger.info(f"📈 Gathering context for fields: {', '.join(fields)}")
        
        # Simulate multiple context searches
        await asyncio.sleep(3)  # Multiple search execution time
        
        # Generate context results
        context_results = {}
        for field in fields:
            if field == "asset.host":
                context_results[field] = {
                    "event_count": 1247,
                    "unique_users": 3,
                    "unique_processes": 15,
                    "network_connections": 42,
                    "authentication_events": 28,
                    "timeline": [
                        {"time": "2024-08-24T14:00:00Z", "event": "User logon", "count": 1},
                        {"time": "2024-08-24T14:20:00Z", "event": "Process execution", "count": 5},
                        {"time": "2024-08-24T14:22:00Z", "event": "Network connection", "count": 10}
                    ]
                }
            elif field == "asset.user":
                context_results[field] = {
                    "event_count": 543,
                    "unique_hosts": 2,
                    "failed_logons": 0,
                    "successful_logons": 15,
                    "privilege_escalations": 1,
                    "timeline": [
                        {"time": "2024-08-24T09:00:00Z", "event": "First logon today", "count": 1},
                        {"time": "2024-08-24T14:22:00Z", "event": "Current session", "count": 1}
                    ]
                }
        
        # Calculate aggregate context score
        total_events = sum(ctx.get("event_count", 0) for ctx in context_results.values())
        
        return {
            "status": "success",
            "output": {
                "fields": fields,
                "timeframe": timeframe,
                "context_results": context_results,
                "total_events_analyzed": total_events,
                "searches_executed": len(fields) * 3,  # Multiple searches per field
                "context_score": min(total_events / 100, 10.0),  # Normalized context score
                "analysis_completed": datetime.now().isoformat(),
                "recommendations": [
                    "Normal activity patterns observed",
                    "No obvious anomalies detected",
                    "Continue monitoring for changes"
                ]
            },
            "rollback_available": False,
            "rollback_data": None
        }
    
    async def _verify_postconditions(self, action: str, args: Dict[str, Any], output: Dict[str, Any]) -> bool:
        """Verify context gathering succeeded"""
        expected_fields = set(args.get("fields", []))
        actual_fields = set(output.get("context_results", {}).keys())
        return expected_fields.issubset(actual_fields)
    
    def _requires_approval(self, action: str, args: Dict[str, Any]) -> bool:
        return False  # Read-only context gathering
    
    def _is_valid_timeframe(self, timeframe: str) -> bool:
        """Validate timeframe format"""
        valid_formats = ["1h", "4h", "8h", "24h", "2d", "3d", "7d"]
        return timeframe in valid_formats
    
    def _get_privilege_scope(self, action: str, args: Dict[str, Any]) -> str:
        field_count = len(args.get("fields", []))
        return f"context_gather:{field_count}_fields"

# ==============================================================================
# Factory Functions and Registry
# ==============================================================================

SIEM_TOOLS = {
    "saved_search": SIEMSavedSearch,
    "gather_context": SIEMGatherContext
}

async def create_siem_tool(tool_name: str, **config) -> EDRToolBase:
    """Factory function to create SIEM tools"""
    if tool_name not in SIEM_TOOLS:
        raise ValueError(f"Unknown SIEM tool: {tool_name}. Available: {list(SIEM_TOOLS.keys())}")
    
    tool_class = SIEM_TOOLS[tool_name]
    return tool_class(**config)

async def execute_siem_action(
    tool_name: str,
    args: Dict[str, Any],
    dry_run: bool = True,
    approval_token: Optional[str] = None,
    **config
) -> ToolResult:
    """Execute a SIEM action with full guardrails"""
    tool = await create_siem_tool(tool_name, **config)
    return await tool.execute(
        action=tool_name,
        args=args,
        dry_run=dry_run,
        approval_token=approval_token
    )

# ==============================================================================
# Testing and Validation
# ==============================================================================

async def test_siem_tools():
    """Test all SIEM tools with mock data"""
    test_cases = [
        {
            "tool": "saved_search",
            "args": {
                "query_template": "brute_force_context",
                "user": "testuser",
                "source_ip": "192.168.1.100",
                "timeframe": "4h"
            }
        },
        {
            "tool": "saved_search",
            "args": {
                "query_template": "powershell_activity",
                "host": "workstation-01",
                "timeframe": "2h"
            }
        },
        {
            "tool": "gather_context",
            "args": {
                "fields": ["asset.host", "asset.user"],
                "timeframe": "24h"
            }
        }
    ]
    
    print("🧪 Testing SIEM tools...")
    for test_case in test_cases:
        print(f"\n🔧 Testing {test_case['tool']}...")
        
        # Test dry-run first
        result = await execute_siem_action(
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
    asyncio.run(test_siem_tools())