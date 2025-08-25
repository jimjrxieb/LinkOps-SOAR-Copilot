#!/usr/bin/env python3
"""
🌐 Network Security MCP Tool Wrappers
====================================
TAG: MCP-TOOLS-NETWORK
Purpose: Secure wrappers for network security operations (firewall, DNS, etc.) with guardrails
Security: All network changes require blast radius analysis and rollback capability
"""

import asyncio
import json
import logging
import ipaddress
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from uuid import uuid4

from pydantic import BaseModel, Field, validator

logger = logging.getLogger(__name__)

# ==============================================================================
# Import base tool framework
# ==============================================================================

from .edr import EDRToolBase, ToolResult

# ==============================================================================
# Network IP Blocking Tool
# ==============================================================================

class NetworkBlockIP(EDRToolBase):
    """Block IP addresses at firewall with safety checks"""
    
    def __init__(self, firewall_api: str = None, api_key: str = None):
        super().__init__()
        self.firewall_api = firewall_api or "https://firewall.company.com/api"
        self.api_key = api_key or "MOCK_API_KEY"
        self.tool_name = "net.block_ip"
    
    async def _check_preconditions(self, action: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Check preconditions for IP blocking"""
        passed_checks = []
        failed_checks = []
        
        # Required fields
        ip_address = args.get("ip_address")
        if not ip_address:
            failed_checks.append("IP address required")
        else:
            # Validate IP format
            try:
                ipaddress.ip_address(ip_address)
                passed_checks.append("Valid IP address format")
            except ValueError:
                failed_checks.append(f"Invalid IP address format: {ip_address}")
        
        # Whitelist protection
        if self._is_internal_ip(ip_address):
            if not args.get("internal_ip_override"):
                failed_checks.append("Cannot block internal IP without override")
            else:
                passed_checks.append("Internal IP override provided")
        else:
            passed_checks.append("External IP - safe to block")
        
        # Critical service protection
        if self._is_critical_service_ip(ip_address):
            failed_checks.append("Cannot block critical service IP")
        else:
            passed_checks.append("Not a critical service IP")
        
        # Duration validation
        duration = args.get("duration", "1h")
        if not self._is_valid_duration(duration):
            failed_checks.append(f"Invalid duration format: {duration}")
        else:
            passed_checks.append("Valid duration format")
        
        return {
            "passed": len(failed_checks) == 0,
            "failed": failed_checks,
            "passed_checks": passed_checks
        }
    
    async def _dry_run(self, action: str, args: Dict[str, Any]) -> str:
        ip_address = args.get("ip_address")
        duration = args.get("duration", "1h")
        reason = args.get("reason", "C2 beacon activity detected")
        
        plan = f"""
IP BLOCKING PLAN for {ip_address}:
1. Validate IP is not in whitelist or critical services
2. Create firewall rule: DENY {ip_address}/32 ANY ANY
3. Apply rule to perimeter firewalls (ingress/egress)
4. Duration: {duration} (auto-expire)
5. Reason: {reason}
6. Log block action with correlation ID
7. Rollback available: Remove firewall rule

BLAST RADIUS: All traffic to/from {ip_address}
REVERSIBLE: Yes (unblock_ip action)
AUTO-EXPIRE: After {duration}
AFFECTED FIREWALLS: Perimeter, internal segmentation
        """.strip()
        
        return plan
    
    async def _execute_action(self, action: str, args: Dict[str, Any], timeout: int) -> Dict[str, Any]:
        """Execute IP blocking via firewall API"""
        ip_address = args["ip_address"]
        duration = args.get("duration", "1h")
        reason = args.get("reason", "Automated security response")
        
        logger.info(f"🚫 Blocking IP address: {ip_address} for {duration}")
        
        # Simulate firewall API calls
        await asyncio.sleep(1)  # Create rule
        await asyncio.sleep(1)  # Deploy to firewalls
        
        # Parse duration
        duration_seconds = self._parse_duration(duration)
        expire_time = datetime.now() + timedelta(seconds=duration_seconds)
        
        return {
            "status": "success",
            "output": {
                "ip_address": ip_address,
                "rule_id": f"block_{ip_address.replace('.', '_')}_{int(time.time())}",
                "blocked_at": datetime.now().isoformat(),
                "expires_at": expire_time.isoformat(),
                "duration": duration,
                "reason": reason,
                "firewalls_updated": ["perimeter-fw-01", "perimeter-fw-02", "internal-fw-01"],
                "rule_priority": 100,  # High priority for security blocks
                "traffic_blocked": 0   # Will increment over time
            },
            "rollback_available": True,
            "rollback_data": {
                "action": "unblock_ip",
                "ip_address": ip_address,
                "rule_id": f"block_{ip_address.replace('.', '_')}_{int(time.time())}"
            }
        }
    
    async def _verify_postconditions(self, action: str, args: Dict[str, Any], output: Dict[str, Any]) -> bool:
        """Verify IP is blocked"""
        ip_address = args["ip_address"]
        rule_id = output.get("rule_id")
        
        logger.info(f"🔍 Verifying IP {ip_address} is blocked (rule: {rule_id})")
        await asyncio.sleep(1)
        
        # Mock verification - rule is active
        return output.get("firewalls_updated", []) and len(output["firewalls_updated"]) > 0
    
    def _requires_approval(self, action: str, args: Dict[str, Any]) -> bool:
        """IP blocking requires approval for internal ranges"""
        ip_address = args.get("ip_address")
        return self._is_internal_ip(ip_address)
    
    def _is_internal_ip(self, ip_address: str) -> bool:
        """Check if IP is in internal ranges"""
        try:
            ip = ipaddress.ip_address(ip_address)
            internal_ranges = [
                ipaddress.ip_network("10.0.0.0/8"),
                ipaddress.ip_network("172.16.0.0/12"),
                ipaddress.ip_network("192.168.0.0/16"),
                ipaddress.ip_network("127.0.0.0/8")
            ]
            return any(ip in network for network in internal_ranges)
        except ValueError:
            return False
    
    def _is_critical_service_ip(self, ip_address: str) -> bool:
        """Check if IP belongs to critical services"""
        # Mock critical service IPs
        critical_ips = [
            "8.8.8.8",  # DNS
            "1.1.1.1",  # DNS
            "10.0.1.5", # Domain controller
            "10.0.1.10" # Exchange server
        ]
        return ip_address in critical_ips
    
    def _is_valid_duration(self, duration: str) -> bool:
        """Validate duration format"""
        try:
            self._parse_duration(duration)
            return True
        except ValueError:
            return False
    
    def _parse_duration(self, duration: str) -> int:
        """Parse duration string to seconds"""
        duration = duration.lower()
        if duration.endswith('s'):
            return int(duration[:-1])
        elif duration.endswith('m'):
            return int(duration[:-1]) * 60
        elif duration.endswith('h'):
            return int(duration[:-1]) * 3600
        elif duration.endswith('d'):
            return int(duration[:-1]) * 86400
        else:
            raise ValueError(f"Invalid duration format: {duration}")
    
    def _get_privilege_scope(self, action: str, args: Dict[str, Any]) -> str:
        return f"ip_block:{args.get('ip_address', 'unknown')}"

# ==============================================================================
# Network Domain Blocking Tool
# ==============================================================================

class NetworkBlockDomains(EDRToolBase):
    """Block domains at DNS/web filter level"""
    
    def __init__(self, dns_api: str = None, web_filter_api: str = None, api_key: str = None):
        super().__init__()
        self.dns_api = dns_api or "https://dns.company.com/api"
        self.web_filter_api = web_filter_api or "https://webfilter.company.com/api"
        self.api_key = api_key or "MOCK_API_KEY"
        self.tool_name = "net.block_domains"
    
    async def _check_preconditions(self, action: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Check preconditions for domain blocking"""
        passed_checks = []
        failed_checks = []
        
        # Required fields
        domains = args.get("domains", [])
        if not domains:
            failed_checks.append("At least one domain required")
        elif isinstance(domains, str):
            domains = [domains]
            args["domains"] = domains  # Normalize to list
        
        if domains:
            passed_checks.append(f"Domain list provided ({len(domains)} domains)")
        
        # Validate domain formats
        invalid_domains = []
        for domain in domains:
            if not self._is_valid_domain(domain):
                invalid_domains.append(domain)
        
        if invalid_domains:
            failed_checks.append(f"Invalid domain formats: {invalid_domains}")
        else:
            passed_checks.append("All domains have valid format")
        
        # Whitelist protection
        critical_domains = self._get_critical_domains()
        blocked_critical = [d for d in domains if d in critical_domains]
        
        if blocked_critical:
            failed_checks.append(f"Cannot block critical domains: {blocked_critical}")
        else:
            passed_checks.append("No critical domains in block list")
        
        return {
            "passed": len(failed_checks) == 0,
            "failed": failed_checks,
            "passed_checks": passed_checks
        }
    
    async def _dry_run(self, action: str, args: Dict[str, Any]) -> str:
        domains = args.get("domains", [])
        duration = args.get("duration", "24h")
        
        plan = f"""
DOMAIN BLOCKING PLAN:
Domains to block: {', '.join(domains)}

1. Add domains to DNS sinkhole
2. Configure web filter rules
3. Update threat intelligence feeds
4. Duration: {duration} (auto-expire)
5. Block at multiple layers:
   - DNS resolution (return NXDOMAIN)
   - Web proxy (HTTP/HTTPS blocking)
   - Threat intel feeds
6. Log block events
7. Rollback available: Remove from block lists

BLAST RADIUS: All DNS/web requests to these domains
REVERSIBLE: Yes (unblock_domains action)
LAYERS: DNS, Web Filter, Threat Intel
        """.strip()
        
        return plan
    
    async def _execute_action(self, action: str, args: Dict[str, Any], timeout: int) -> Dict[str, Any]:
        """Execute domain blocking"""
        domains = args["domains"]
        duration = args.get("duration", "24h")
        reason = args.get("reason", "C2 domain detected")
        
        logger.info(f"🚫 Blocking domains: {', '.join(domains)}")
        
        # Simulate API calls
        await asyncio.sleep(1)  # DNS sinkhole
        await asyncio.sleep(1)  # Web filter
        await asyncio.sleep(0.5)  # Threat intel
        
        duration_seconds = self._parse_duration(duration)
        expire_time = datetime.now() + timedelta(seconds=duration_seconds)
        
        return {
            "status": "success",
            "output": {
                "domains": domains,
                "blocked_count": len(domains),
                "blocked_at": datetime.now().isoformat(),
                "expires_at": expire_time.isoformat(),
                "duration": duration,
                "reason": reason,
                "dns_rules_created": len(domains),
                "webfilter_rules_created": len(domains),
                "threat_intel_updated": True,
                "block_methods": ["dns_sinkhole", "web_filter", "threat_intel"]
            },
            "rollback_available": True,
            "rollback_data": {
                "action": "unblock_domains",
                "domains": domains,
                "rule_ids": [f"block_{d.replace('.', '_')}" for d in domains]
            }
        }
    
    async def _verify_postconditions(self, action: str, args: Dict[str, Any], output: Dict[str, Any]) -> bool:
        """Verify domains are blocked"""
        domains = args["domains"]
        
        logger.info(f"🔍 Verifying {len(domains)} domains are blocked")
        await asyncio.sleep(1)
        
        return output.get("dns_rules_created", 0) == len(domains)
    
    def _requires_approval(self, action: str, args: Dict[str, Any]) -> bool:
        """Domain blocking generally allowed for external domains"""
        domains = args.get("domains", [])
        
        # Check if any domain is internal company domain
        company_domains = ["company.com", "internal.company.com"]
        return any(any(cd in domain for cd in company_domains) for domain in domains)
    
    def _is_valid_domain(self, domain: str) -> bool:
        """Basic domain format validation"""
        import re
        domain_regex = re.compile(
            r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
        )
        return bool(domain_regex.match(domain))
    
    def _get_critical_domains(self) -> List[str]:
        """Get list of critical domains that should never be blocked"""
        return [
            "company.com",
            "microsoft.com", 
            "office.com",
            "azure.com",
            "github.com",
            "stackoverflow.com"
        ]
    
    def _parse_duration(self, duration: str) -> int:
        """Parse duration string to seconds"""
        duration = duration.lower()
        if duration.endswith('s'):
            return int(duration[:-1])
        elif duration.endswith('m'):
            return int(duration[:-1]) * 60
        elif duration.endswith('h'):
            return int(duration[:-1]) * 3600
        elif duration.endswith('d'):
            return int(duration[:-1]) * 86400
        else:
            raise ValueError(f"Invalid duration format: {duration}")
    
    def _get_privilege_scope(self, action: str, args: Dict[str, Any]) -> str:
        domain_count = len(args.get("domains", []))
        return f"domain_block:{domain_count}_domains"

# ==============================================================================
# Network Rate Limiting Tool
# ==============================================================================

class NetworkRateLimit(EDRToolBase):
    """Apply rate limiting to IP addresses"""
    
    def __init__(self, firewall_api: str = None, api_key: str = None):
        super().__init__()
        self.firewall_api = firewall_api or "https://firewall.company.com/api"
        self.api_key = api_key or "MOCK_API_KEY"
        self.tool_name = "net.rate_limit_ip"
    
    async def _check_preconditions(self, action: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Check preconditions for rate limiting"""
        passed_checks = []
        failed_checks = []
        
        # Required fields
        ip_address = args.get("ip_address")
        if not ip_address:
            failed_checks.append("IP address required")
        else:
            try:
                ipaddress.ip_address(ip_address)
                passed_checks.append("Valid IP address format")
            except ValueError:
                failed_checks.append(f"Invalid IP address format: {ip_address}")
        
        # Rate limit validation
        rate_limit = args.get("rate_limit", "1_per_minute")
        if not self._is_valid_rate_limit(rate_limit):
            failed_checks.append(f"Invalid rate limit format: {rate_limit}")
        else:
            passed_checks.append("Valid rate limit format")
        
        return {
            "passed": len(failed_checks) == 0,
            "failed": failed_checks,
            "passed_checks": passed_checks
        }
    
    async def _dry_run(self, action: str, args: Dict[str, Any]) -> str:
        ip_address = args.get("ip_address")
        rate_limit = args.get("rate_limit", "1_per_minute")
        duration = args.get("duration", "1h")
        
        plan = f"""
RATE LIMITING PLAN for {ip_address}:
1. Create rate limiting rule: {rate_limit}
2. Apply to connections from {ip_address}
3. Action on exceed: DROP (drop excess packets)
4. Duration: {duration}
5. Log rate limit events
6. Rollback available: Remove rate limiting rule

EFFECT: Slow down traffic from {ip_address}
BLAST RADIUS: Single IP address
REVERSIBLE: Yes (remove_rate_limit action)
LESS DISRUPTIVE: Than full IP blocking
        """.strip()
        
        return plan
    
    async def _execute_action(self, action: str, args: Dict[str, Any], timeout: int) -> Dict[str, Any]:
        """Execute rate limiting"""
        ip_address = args["ip_address"]
        rate_limit = args.get("rate_limit", "1_per_minute")
        duration = args.get("duration", "1h")
        
        logger.info(f"⏱️ Rate limiting IP {ip_address}: {rate_limit}")
        
        await asyncio.sleep(1)  # Apply rate limit rule
        
        duration_seconds = self._parse_duration(duration)
        expire_time = datetime.now() + timedelta(seconds=duration_seconds)
        
        return {
            "status": "success",
            "output": {
                "ip_address": ip_address,
                "rate_limit": rate_limit,
                "rule_id": f"ratelimit_{ip_address.replace('.', '_')}_{int(time.time())}",
                "applied_at": datetime.now().isoformat(),
                "expires_at": expire_time.isoformat(),
                "duration": duration,
                "action_on_exceed": "drop",
                "current_rate": "0_per_minute"  # Will update as traffic flows
            },
            "rollback_available": True,
            "rollback_data": {
                "action": "remove_rate_limit",
                "ip_address": ip_address,
                "rule_id": f"ratelimit_{ip_address.replace('.', '_')}_{int(time.time())}"
            }
        }
    
    async def _verify_postconditions(self, action: str, args: Dict[str, Any], output: Dict[str, Any]) -> bool:
        """Verify rate limit is active"""
        rule_id = output.get("rule_id")
        
        logger.info(f"🔍 Verifying rate limit rule active: {rule_id}")
        await asyncio.sleep(0.5)
        
        return bool(rule_id)
    
    def _requires_approval(self, action: str, args: Dict[str, Any]) -> bool:
        """Rate limiting generally allowed"""
        return False  # Less disruptive than blocking
    
    def _is_valid_rate_limit(self, rate_limit: str) -> bool:
        """Validate rate limit format"""
        valid_formats = [
            "1_per_second", "5_per_second", "10_per_second",
            "1_per_minute", "5_per_minute", "10_per_minute",
            "1_per_hour", "10_per_hour", "100_per_hour"
        ]
        return rate_limit in valid_formats
    
    def _parse_duration(self, duration: str) -> int:
        """Parse duration string to seconds"""
        duration = duration.lower()
        if duration.endswith('m'):
            return int(duration[:-1]) * 60
        elif duration.endswith('h'):
            return int(duration[:-1]) * 3600
        elif duration.endswith('d'):
            return int(duration[:-1]) * 86400
        else:
            return 3600  # Default 1 hour
    
    def _get_privilege_scope(self, action: str, args: Dict[str, Any]) -> str:
        return f"rate_limit:{args.get('ip_address', 'unknown')}"

# ==============================================================================
# Factory Functions and Registry
# ==============================================================================

NETWORK_TOOLS = {
    "block_ip": NetworkBlockIP,
    "block_domains": NetworkBlockDomains,
    "rate_limit_ip": NetworkRateLimit
}

async def create_network_tool(tool_name: str, **config) -> EDRToolBase:
    """Factory function to create network tools"""
    if tool_name not in NETWORK_TOOLS:
        raise ValueError(f"Unknown network tool: {tool_name}. Available: {list(NETWORK_TOOLS.keys())}")
    
    tool_class = NETWORK_TOOLS[tool_name]
    return tool_class(**config)

async def execute_network_action(
    tool_name: str,
    args: Dict[str, Any],
    dry_run: bool = True,
    approval_token: Optional[str] = None,
    **config
) -> ToolResult:
    """Execute a network action with full guardrails"""
    tool = await create_network_tool(tool_name, **config)
    return await tool.execute(
        action=tool_name,
        args=args,
        dry_run=dry_run,
        approval_token=approval_token
    )

# ==============================================================================
# Testing and Validation
# ==============================================================================

async def test_network_tools():
    """Test all network tools with mock data"""
    test_cases = [
        {
            "tool": "rate_limit_ip",
            "args": {
                "ip_address": "192.168.1.100",
                "rate_limit": "1_per_minute",
                "duration": "1h"
            }
        },
        {
            "tool": "block_ip",
            "args": {
                "ip_address": "203.0.113.5",  # TEST-NET-3
                "duration": "24h",
                "reason": "C2 beacon activity detected"
            }
        },
        {
            "tool": "block_domains",
            "args": {
                "domains": ["evil-c2.com", "malicious-beacon.net"],
                "duration": "48h",
                "reason": "C2 domains detected"
            }
        }
    ]
    
    print("🧪 Testing Network tools...")
    for test_case in test_cases:
        print(f"\n🔧 Testing {test_case['tool']}...")
        
        # Test dry-run first
        result = await execute_network_action(
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
    asyncio.run(test_network_tools())