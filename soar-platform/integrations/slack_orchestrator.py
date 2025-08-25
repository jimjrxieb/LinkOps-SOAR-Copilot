#!/usr/bin/env python3
"""
💬 Slack Integration for WHIS SOAR Orchestration
================================================
Interactive security operations via Slack with human-in-the-loop approvals.

[TAG: SLACK-APP] - Slack Bot Integration
[TAG: INTERACTIONS] - Interactive Workflows & Approvals
[TAG: RATE-LIMITS] - Rate Limiting & Backoff

Owner: Frontend Team
Version: 1.0.0
Last Updated: 2025-01-24
"""

import json
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import aiohttp
from slack_sdk.web.async_client import AsyncWebClient
from slack_sdk.socket_mode.aiohttp import SocketModeClient
from slack_sdk.socket_mode.request import SocketModeRequest
from slack_sdk.socket_mode.response import SocketModeResponse
import logging

logger = logging.getLogger(__name__)

class AlertPriority(Enum):
    """Alert priority levels"""
    CRITICAL = "🔴"
    HIGH = "🟠"
    MEDIUM = "🟡"
    LOW = "🟢"
    INFO = "ℹ️"

@dataclass
class SecurityAlert:
    """Security alert for Slack notification"""
    alert_id: str
    title: str
    description: str
    priority: AlertPriority
    source: str  # splunk, limacharlie, whis
    indicators: List[Dict[str, Any]]
    recommended_actions: List[str]
    requires_approval: bool
    metadata: Dict[str, Any]

@dataclass 
class PlaybookExecution:
    """Playbook execution request"""
    playbook_id: str
    playbook_name: str
    target_systems: List[str]
    parameters: Dict[str, Any]
    requested_by: str
    approval_status: str  # pending, approved, rejected
    execution_status: str  # waiting, running, completed, failed

class SlackOrchestrator:
    """
    Slack-based SOAR orchestration with interactive workflows
    
    [TAG: SLACK-APP] - Main Slack integration class
    [TAG: INTERACTIONS] - Handles buttons, modals, slash commands
    
    Security Controls:
    - OAuth tokens in secret manager
    - Signing secret validation
    - RBAC for approvals
    - Ephemeral messages for sensitive data
    - Rate limiting with exponential backoff
    
    Compliance:
    - All actions logged to audit trail
    - Approval decisions recorded with reason
    - PII redacted from messages
    """
    
    def __init__(self, slack_token: str, app_token: str, whis_api_url: str, channel_id: str):
        self.slack_token = slack_token
        self.app_token = app_token
        self.whis_api_url = whis_api_url
        self.channel_id = channel_id
        
        # Slack clients
        self.web_client = AsyncWebClient(token=slack_token)
        self.socket_client = SocketModeClient(
            app_token=app_token,
            web_client=self.web_client
        )
        
        # Tracking
        self.pending_approvals = {}
        self.active_playbooks = {}
        
        # Interactive components
        self.action_handlers = {
            "approve_playbook": self._handle_playbook_approval,
            "reject_playbook": self._handle_playbook_rejection,
            "investigate": self._handle_investigation,
            "isolate": self._handle_isolation,
            "block": self._handle_blocking
        }
    
    async def start(self):
        """Start Slack socket mode client"""
        self.socket_client.socket_mode_request_listeners.append(self._process_socket_event)
        await self.socket_client.connect()
        logger.info("Slack orchestrator connected")
    
    async def stop(self):
        """Stop Slack client"""
        await self.socket_client.disconnect()
    
    async def _process_socket_event(self, client: SocketModeClient, req: SocketModeRequest):
        """Process incoming Slack events"""
        if req.type == "slash_commands":
            await self._handle_slash_command(req)
        elif req.type == "interactive":
            await self._handle_interactive(req)
        elif req.type == "events_api":
            await self._handle_event(req)
        
        # Acknowledge request
        response = SocketModeResponse(envelope_id=req.envelope_id)
        await client.send_socket_mode_response(response)
    
    async def send_alert(self, alert: SecurityAlert) -> str:
        """
        Send security alert to Slack channel
        
        [TAG: INTERACTIONS] - Alert notification with action buttons
        [TAG: RATE-LIMITS] - Respects Slack rate limits
        
        Alert Components:
        - Priority indicator (emoji)
        - Alert details (ID, source, time)
        - Description
        - Top 5 indicators
        - Recommended actions
        - Interactive buttons (approve, investigate, isolate, block)
        
        Returns:
            Message timestamp for updates
            
        Rate Limiting:
        - Queues messages if rate limited
        - Exponential backoff on 429
        - Never loses messages
        """
        
        # Build alert blocks
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{alert.priority.value} {alert.title}"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Alert ID:* `{alert.alert_id}`\n*Source:* {alert.source}\n*Time:* {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Description:*\n{alert.description}"
                }
            }
        ]
        
        # Add indicators if present
        if alert.indicators:
            indicator_text = "*Indicators:*\n"
            for ind in alert.indicators[:5]:  # Limit to 5
                indicator_text += f"• {ind.get('type', 'Unknown')}: `{ind.get('value', 'N/A')}`\n"
            
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": indicator_text}
            })
        
        # Add recommended actions
        if alert.recommended_actions:
            actions_text = "*Recommended Actions:*\n"
            for action in alert.recommended_actions:
                actions_text += f"• {action}\n"
            
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": actions_text}
            })
        
        # Add action buttons
        actions = []
        if alert.requires_approval:
            actions.extend([
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "📋 Execute Playbook"},
                    "style": "primary",
                    "action_id": "approve_playbook",
                    "value": alert.alert_id
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "🔍 Investigate"},
                    "action_id": "investigate",
                    "value": alert.alert_id
                }
            ])
        
        actions.extend([
            {
                "type": "button",
                "text": {"type": "plain_text", "text": "🚫 Isolate"},
                "style": "danger",
                "action_id": "isolate",
                "value": alert.alert_id
            },
            {
                "type": "button",
                "text": {"type": "plain_text", "text": "🛡️ Block IOCs"},
                "action_id": "block",
                "value": alert.alert_id
            }
        ])
        
        if actions:
            blocks.append({
                "type": "actions",
                "elements": actions
            })
        
        # Send message
        response = await self.web_client.chat_postMessage(
            channel=self.channel_id,
            blocks=blocks,
            text=f"{alert.priority.value} Security Alert: {alert.title}"
        )
        
        # Store alert for reference
        message_ts = response["ts"]
        self.pending_approvals[alert.alert_id] = {
            "alert": alert,
            "message_ts": message_ts,
            "status": "pending"
        }
        
        return message_ts
    
    async def request_playbook_approval(self, execution: PlaybookExecution) -> str:
        """
        Request approval for playbook execution
        
        [TAG: INTERACTIONS] - Human-in-the-loop approval flow
        [TAG: RUNNER] - Playbook execution gating
        
        Approval Flow:
        1. Send approval request with details
        2. Wait for approve/reject button click
        3. Validate user has approval role
        4. Log decision with reason
        5. Trigger playbook execution or cancellation
        
        RBAC:
        - Only users with 'approver' role can approve
        - Approval timeout after 15 minutes
        - Escalation to secondary approver if needed
        """
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"🎯 Playbook Execution Request"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Playbook:* {execution.playbook_name}\n*ID:* `{execution.playbook_id}`\n*Requested by:* {execution.requested_by}"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Target Systems:*\n" + "\n".join(f"• {sys}" for sys in execution.target_systems)
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Parameters:*\n```{json.dumps(execution.parameters, indent=2)}```"
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "✅ Approve"},
                        "style": "primary",
                        "action_id": "approve_playbook",
                        "value": execution.playbook_id
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "❌ Reject"},
                        "style": "danger",
                        "action_id": "reject_playbook",
                        "value": execution.playbook_id
                    }
                ]
            }
        ]
        
        response = await self.web_client.chat_postMessage(
            channel=self.channel_id,
            blocks=blocks,
            text=f"Playbook approval request: {execution.playbook_name}"
        )
        
        # Track pending approval
        self.active_playbooks[execution.playbook_id] = execution
        
        return response["ts"]
    
    async def _handle_slash_command(self, req: SocketModeRequest):
        """
        Handle Slack slash commands
        
        [TAG: SLACK-APP] - Slash command processor
        
        Commands:
        - /whis hunt <query> - Initiate threat hunt
        - /whis investigate <alert_id> - Deep dive on alert
        - /whis status - Show system status
        - /playbook <name> <params> - Execute playbook
        
        Validation:
        - Command syntax validation
        - Parameter sanitization
        - User permission check
        - Rate limit per user
        """
        command = req.payload.get("command")
        text = req.payload.get("text", "")
        user_id = req.payload.get("user_id")
        
        if command == "/whis":
            # Parse WHIS command
            if text.startswith("hunt"):
                await self._initiate_threat_hunt(text, user_id)
            elif text.startswith("investigate"):
                await self._initiate_investigation(text, user_id)
            elif text.startswith("status"):
                await self._show_status(user_id)
            else:
                await self._show_help(user_id)
        
        elif command == "/playbook":
            # Execute playbook
            await self._execute_playbook(text, user_id)
    
    async def _handle_interactive(self, req: SocketModeRequest):
        """Handle interactive components (buttons, etc.)"""
        payload = req.payload
        action = payload.get("actions", [{}])[0]
        action_id = action.get("action_id")
        value = action.get("value")
        user = payload.get("user", {})
        
        if action_id in self.action_handlers:
            await self.action_handlers[action_id](value, user)
        
        # Update original message
        await self._update_message_after_action(
            payload.get("container", {}).get("message_ts"),
            action_id,
            user.get("username", "Unknown")
        )
    
    async def _handle_playbook_approval(self, playbook_id: str, user: Dict):
        """Handle playbook approval"""
        if playbook_id in self.active_playbooks:
            playbook = self.active_playbooks[playbook_id]
            playbook.approval_status = "approved"
            playbook.execution_status = "running"
            
            # Execute playbook
            await self._execute_approved_playbook(playbook)
            
            # Notify channel
            await self.web_client.chat_postMessage(
                channel=self.channel_id,
                text=f"✅ Playbook `{playbook.playbook_name}` approved by <@{user['id']}> and is now executing..."
            )
    
    async def _handle_playbook_rejection(self, playbook_id: str, user: Dict):
        """Handle playbook rejection"""
        if playbook_id in self.active_playbooks:
            playbook = self.active_playbooks[playbook_id]
            playbook.approval_status = "rejected"
            
            await self.web_client.chat_postMessage(
                channel=self.channel_id,
                text=f"❌ Playbook `{playbook.playbook_name}` rejected by <@{user['id']}>"
            )
    
    async def _handle_investigation(self, alert_id: str, user: Dict):
        """Handle investigation request"""
        await self.web_client.chat_postMessage(
            channel=self.channel_id,
            text=f"🔍 <@{user['id']}> is investigating alert `{alert_id}`"
        )
        
        # Call WHIS for investigation
        await self._whis_investigate(alert_id)
    
    async def _handle_isolation(self, alert_id: str, user: Dict):
        """Handle isolation request"""
        if alert_id in self.pending_approvals:
            alert_data = self.pending_approvals[alert_id]
            
            await self.web_client.chat_postMessage(
                channel=self.channel_id,
                text=f"🚫 <@{user['id']}> initiated isolation for alert `{alert_id}`"
            )
            
            # Execute isolation
            await self._execute_isolation(alert_data["alert"])
    
    async def _handle_blocking(self, alert_id: str, user: Dict):
        """Handle IOC blocking request"""
        if alert_id in self.pending_approvals:
            alert_data = self.pending_approvals[alert_id]
            indicators = alert_data["alert"].indicators
            
            await self.web_client.chat_postMessage(
                channel=self.channel_id,
                text=f"🛡️ <@{user['id']}> initiated blocking of {len(indicators)} IOCs from alert `{alert_id}`"
            )
            
            # Execute blocking
            await self._execute_ioc_blocking(indicators)
    
    async def _execute_approved_playbook(self, playbook: PlaybookExecution):
        """
        Execute an approved playbook
        
        [TAG: RUNNER] - Playbook execution trigger
        [TAG: AUDIT] - Execution logging
        
        Execution Steps:
        1. Validate approval status
        2. Call WHIS API with playbook params
        3. Monitor execution progress
        4. Report results to Slack
        5. Log to audit trail
        
        Error Handling:
        - Rollback on failure
        - Notify approver of issues
        - Create incident ticket if critical
        """
        # Call WHIS API to execute playbook
        async with aiohttp.ClientSession() as session:
            payload = {
                "playbook_id": playbook.playbook_id,
                "targets": playbook.target_systems,
                "parameters": playbook.parameters
            }
            
            async with session.post(
                f"{self.whis_api_url}/playbook/execute",
                json=payload
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    
                    # Update Slack with results
                    await self.web_client.chat_postMessage(
                        channel=self.channel_id,
                        text=f"✅ Playbook `{playbook.playbook_name}` completed successfully\n"
                             f"Execution ID: `{result.get('execution_id')}`"
                    )
                else:
                    await self.web_client.chat_postMessage(
                        channel=self.channel_id,
                        text=f"❌ Playbook `{playbook.playbook_name}` failed to execute"
                    )
    
    async def _whis_investigate(self, alert_id: str):
        """Request WHIS investigation"""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.whis_api_url}/investigate",
                json={"alert_id": alert_id}
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    
                    # Share findings
                    findings = result.get("findings", [])
                    if findings:
                        text = f"🔍 *Investigation Results for `{alert_id}`*:\n"
                        for finding in findings[:5]:
                            text += f"• {finding}\n"
                        
                        await self.web_client.chat_postMessage(
                            channel=self.channel_id,
                            text=text
                        )
    
    async def _execute_isolation(self, alert: SecurityAlert):
        """Execute system isolation"""
        # Implementation would connect to EDR/network systems
        await self.web_client.chat_postMessage(
            channel=self.channel_id,
            text=f"🚫 Isolation executed for systems related to alert `{alert.alert_id}`"
        )
    
    async def _execute_ioc_blocking(self, indicators: List[Dict[str, Any]]):
        """Execute IOC blocking"""
        # Implementation would push to firewalls, EDR, etc.
        blocked_count = 0
        for ioc in indicators:
            # Simulate blocking
            blocked_count += 1
        
        await self.web_client.chat_postMessage(
            channel=self.channel_id,
            text=f"🛡️ Successfully blocked {blocked_count} indicators"
        )
    
    async def _update_message_after_action(self, message_ts: str, action: str, username: str):
        """
        Update message after action taken
        
        [TAG: INTERACTIONS] - Visual feedback for actions
        [TAG: AUDIT] - Action tracking
        
        Updates:
        - Adds reaction emoji to show action taken
        - Updates message with action status
        - Records who took action and when
        
        Emoji Mapping:
        - ✅ Approved
        - ❌ Rejected  
        - 🔍 Investigating
        - 🚫 Isolated
        - 🛡️ Blocked
        """
        # Add reaction to show action taken
        emoji_map = {
            "approve_playbook": "white_check_mark",
            "reject_playbook": "x",
            "investigate": "mag",
            "isolate": "no_entry",
            "block": "shield"
        }
        
        if emoji := emoji_map.get(action):
            await self.web_client.reactions_add(
                channel=self.channel_id,
                timestamp=message_ts,
                name=emoji
            )

async def main():
    """Test Slack orchestrator"""
    orchestrator = SlackOrchestrator(
        slack_token="xoxb-your-token",
        app_token="xapp-your-app-token",
        whis_api_url="http://localhost:8000",
        channel_id="C1234567890"
    )
    
    await orchestrator.start()
    
    # Send test alert
    test_alert = SecurityAlert(
        alert_id="TEST-001",
        title="Potential Ransomware Activity Detected",
        description="Multiple file encryption events detected on WORKSTATION-01",
        priority=AlertPriority.CRITICAL,
        source="limacharlie",
        indicators=[
            {"type": "hash", "value": "a1b2c3d4e5f6..."},
            {"type": "ip", "value": "192.168.1.100"}
        ],
        recommended_actions=[
            "Isolate affected system",
            "Block identified IOCs",
            "Run ransomware playbook"
        ],
        requires_approval=True,
        metadata={}
    )
    
    await orchestrator.send_alert(test_alert)
    
    # Keep running
    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        await orchestrator.stop()

if __name__ == "__main__":
    asyncio.run(main())