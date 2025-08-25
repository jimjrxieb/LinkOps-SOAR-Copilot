#!/usr/bin/env python3
"""
🚨 Slack Triage Alert System
============================
Real-time notifications for knowledge gaps requiring human review

[TAG: SLACK-ALERT] - Automated triage notifications
[TAG: HUMAN-IN-LOOP] - Review workflow integration
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import aiohttp
from pathlib import Path

from .schemas import (
    UnansweredQuestionV1,
    KnowledgeGapAlert,
    AbstainReason,
    IntentCategory
)

logger = logging.getLogger(__name__)

class SlackAlertManager:
    """
    Manages Slack notifications for knowledge gaps
    
    [TAG: SLACK-ALERT] - Core notification engine
    [TAG: GOVERNANCE] - PII-safe messaging
    """
    
    def __init__(self, 
                 webhook_url: Optional[str] = None,
                 channel: str = "#whis-triage",
                 console_base_url: str = "https://console.whis.local"):
        self.webhook_url = webhook_url or self._load_webhook_from_env()
        self.channel = channel
        self.console_base_url = console_base_url
        self.alert_queue_path = Path("data/alert_queue")
        self.alert_queue_path.mkdir(parents=True, exist_ok=True)
        
    def _load_webhook_from_env(self) -> Optional[str]:
        """Load Slack webhook from environment or config"""
        import os
        return os.getenv("SLACK_WEBHOOK_URL")
    
    def _truncate_query(self, query: str, max_length: int = 100) -> str:
        """Safely truncate query for preview"""
        if len(query) <= max_length:
            return query
        return query[:max_length - 3] + "..."
    
    def _format_confidence_emoji(self, confidence: float) -> str:
        """Convert confidence score to emoji"""
        if confidence >= 0.8:
            return "🟢"
        elif confidence >= 0.5:
            return "🟡" 
        elif confidence >= 0.3:
            return "🟠"
        else:
            return "🔴"
    
    def _format_abstain_reason(self, reason: AbstainReason) -> str:
        """Human-readable abstain reason"""
        reason_map = {
            AbstainReason.NO_RAG_HITS: "📚 No Knowledge Base Hits",
            AbstainReason.LOW_CONFIDENCE: "🤔 Low Confidence Score", 
            AbstainReason.NO_CITATIONS: "📎 Missing Citations",
            AbstainReason.GLOSSARY_MISS: "📖 Glossary Gap",
            AbstainReason.TOOL_FAILURE: "🔧 Tool Integration Failed",
            AbstainReason.POLICY_BLOCK: "🛡️ Policy Blocked",
            AbstainReason.INCOMPLETE_CONTEXT: "🧩 Incomplete Context"
        }
        return reason_map.get(reason, f"❓ {reason.value}")
    
    def _format_intent_emoji(self, intent: IntentCategory) -> str:
        """Intent category to emoji"""
        intent_map = {
            IntentCategory.DEFINITION: "📝",
            IntentCategory.HOW_TO: "🔧", 
            IntentCategory.TROUBLESHOOTING: "🚨",
            IntentCategory.ANALYSIS: "🔍",
            IntentCategory.CONFIGURATION: "⚙️",
            IntentCategory.INVESTIGATION: "🕵️",
            IntentCategory.UNKNOWN: "❓"
        }
        return intent_map.get(intent, "❓")
    
    async def create_triage_alert(self, gap: UnansweredQuestionV1) -> KnowledgeGapAlert:
        """
        Create structured alert from knowledge gap
        
        [TAG: GOVERNANCE] - PII redaction enforced
        """
        
        # Extract top doc titles for context
        top_k_titles = []
        for rag_hit in gap.rag_topk_meta[:3]:
            top_k_titles.append(rag_hit.doc_title)
        
        alert = KnowledgeGapAlert(
            gap_id=gap.id,
            timestamp=gap.timestamp.isoformat(),
            query_preview=self._truncate_query(gap.query_text_redacted, 100),
            why_abstained=gap.why_abstained,
            intent=gap.intent,
            confidence_score=gap.confidence_score,
            tenant=gap.tenant,
            channel=gap.channel,
            
            top_k_titles=top_k_titles,
            corpus_version=gap.corpus_versions.get("core", "unknown"),
            trace_id=f"trace_{gap.id}"
        )
        
        return alert
    
    async def send_slack_notification(self, alert: KnowledgeGapAlert) -> bool:
        """
        Send Slack notification with action buttons
        
        [TAG: HUMAN-IN-LOOP] - Review workflow trigger
        """
        
        if not self.webhook_url:
            logger.warning("No Slack webhook configured - queuing alert for manual processing")
            await self._queue_alert_for_manual_processing(alert)
            return False
        
        try:
            # Build Slack message
            confidence_emoji = self._format_confidence_emoji(alert.confidence_score)
            reason_display = self._format_abstain_reason(alert.why_abstained)
            intent_emoji = self._format_intent_emoji(alert.intent)
            
            # Main message
            message_text = (
                f"{confidence_emoji} *WHIS Knowledge Gap Detected*\n\n"
                f"*Question:* {alert.query_preview}\n"
                f"*Reason:* {reason_display}\n"
                f"*Intent:* {intent_emoji} {alert.intent.value.title()}\n"
                f"*Confidence:* {alert.confidence_score:.2f}\n"
                f"*Tenant:* {alert.tenant} | *Channel:* {alert.channel}\n"
                f"*Timestamp:* {alert.timestamp}"
            )
            
            # Context section
            if alert.top_k_titles:
                context_text = "\n\n*Closest Matches Found:*\n"
                for i, title in enumerate(alert.top_k_titles[:3], 1):
                    context_text += f"{i}. {title}\n"
                message_text += context_text
            
            # Build Slack payload
            payload = {
                "channel": self.channel,
                "username": "WHIS Triage Bot",
                "icon_emoji": ":robot_face:",
                "text": message_text,
                "attachments": [
                    {
                        "color": self._get_alert_color(alert.confidence_score),
                        "fields": [
                            {
                                "title": "Gap ID",
                                "value": f"`{alert.gap_id}`",
                                "short": True
                            },
                            {
                                "title": "Corpus Version", 
                                "value": alert.corpus_version,
                                "short": True
                            }
                        ],
                        "actions": [
                            {
                                "type": "button",
                                "text": "🔍 View in Console",
                                "url": f"{self.console_base_url}/gaps/{alert.gap_id}",
                                "style": "primary"
                            },
                            {
                                "type": "button", 
                                "text": "🎓 Promote to Teacher",
                                "name": "escalate",
                                "value": alert.gap_id,
                                "style": "default",
                                "confirm": {
                                    "title": "Escalate to Teacher Model?",
                                    "text": "This will send the question to GPT-5 for a draft response. Cost: ~$0.05",
                                    "ok_text": "Yes, Escalate",
                                    "dismiss_text": "Cancel"
                                }
                            },
                            {
                                "type": "button",
                                "text": "❌ Dismiss",
                                "name": "dismiss",
                                "value": alert.gap_id,
                                "style": "danger"
                            }
                        ],
                        "footer": f"WHIS SOAR Copilot | Trace ID: {alert.trace_id}",
                        "ts": int(datetime.fromisoformat(alert.timestamp.replace('Z', '+00:00')).timestamp())
                    }
                ]
            }
            
            # Send to Slack
            async with aiohttp.ClientSession() as session:
                async with session.post(self.webhook_url, json=payload) as response:
                    if response.status == 200:
                        logger.info(f"Slack alert sent successfully for gap {alert.gap_id}")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"Slack webhook failed: {response.status} - {error_text}")
                        await self._queue_alert_for_manual_processing(alert)
                        return False
                        
        except Exception as e:
            logger.error(f"Failed to send Slack notification for gap {alert.gap_id}: {e}")
            await self._queue_alert_for_manual_processing(alert)
            return False
    
    def _get_alert_color(self, confidence: float) -> str:
        """Get Slack attachment color based on confidence"""
        if confidence >= 0.8:
            return "good"  # Green
        elif confidence >= 0.5:
            return "warning"  # Yellow
        else:
            return "danger"  # Red
    
    async def _queue_alert_for_manual_processing(self, alert: KnowledgeGapAlert):
        """Queue alert when Slack delivery fails"""
        queue_file = self.alert_queue_path / f"alert_{alert.gap_id}.json"
        
        try:
            with open(queue_file, 'w') as f:
                json.dump({
                    "alert": alert.model_dump(),
                    "queued_at": datetime.utcnow().isoformat(),
                    "delivery_failed": True
                }, f, indent=2, default=str)
                
            logger.info(f"Alert queued for manual processing: {alert.gap_id}")
            
        except Exception as e:
            logger.error(f"Failed to queue alert {alert.gap_id}: {e}")
    
    def get_queued_alerts(self) -> List[Dict[str, Any]]:
        """Get all queued alerts for manual processing"""
        queued_alerts = []
        
        for alert_file in self.alert_queue_path.glob("alert_*.json"):
            try:
                with open(alert_file) as f:
                    alert_data = json.load(f)
                    queued_alerts.append(alert_data)
                    
            except Exception as e:
                logger.error(f"Failed to load queued alert from {alert_file}: {e}")
        
        return sorted(queued_alerts, key=lambda x: x['queued_at'], reverse=True)
    
    async def process_alert_action(self, action: str, gap_id: str, user_id: str) -> Dict[str, Any]:
        """
        Process Slack button actions
        
        [TAG: HUMAN-IN-LOOP] - Action handler
        """
        
        if action == "escalate":
            # TODO: Integrate with teacher escalation system
            logger.info(f"Teacher escalation requested for gap {gap_id} by user {user_id}")
            return {
                "status": "escalated",
                "message": f"Gap {gap_id} escalated to teacher model",
                "next_step": "Teacher model will generate draft response"
            }
            
        elif action == "dismiss":
            logger.info(f"Gap {gap_id} dismissed by user {user_id}")
            return {
                "status": "dismissed", 
                "message": f"Gap {gap_id} marked as dismissed",
                "dismissed_by": user_id
            }
            
        else:
            logger.warning(f"Unknown action '{action}' for gap {gap_id}")
            return {
                "status": "error",
                "message": f"Unknown action: {action}"
            }

# Integration function for data lake
async def notify_knowledge_gap(gap: UnansweredQuestionV1, 
                              slack_manager: Optional[SlackAlertManager] = None) -> bool:
    """
    Send knowledge gap notification to Slack
    
    [TAG: CONFIDENCE-GATES] - Main notification interface
    """
    
    if slack_manager is None:
        slack_manager = SlackAlertManager()
    
    try:
        # Create alert
        alert = await slack_manager.create_triage_alert(gap)
        
        # Send notification
        success = await slack_manager.send_slack_notification(alert)
        
        if success:
            logger.info(f"Knowledge gap notification sent: {gap.id}")
        else:
            logger.warning(f"Knowledge gap notification queued: {gap.id}")
            
        return success
        
    except Exception as e:
        logger.error(f"Failed to notify knowledge gap {gap.id}: {e}")
        return False

if __name__ == "__main__":
    # Demo usage
    import asyncio
    from datetime import datetime
    
    async def demo():
        # Create mock gap
        from .schemas import AbstainReason, IntentCategory, RAGHitMeta, PIIRedactionSummary
        
        mock_gap = UnansweredQuestionV1(
            id="gap_demo123456",
            timestamp=datetime.utcnow(),
            tenant="acme_corp",
            channel="slack",
            user_hash="user_abc",
            session_id="session_xyz",
            
            query_text_redacted="What is the latest Splunk configuration for detecting lateral movement?",
            query_hash="query_hash",
            intent=IntentCategory.CONFIGURATION,
            tokens=12,
            
            why_abstained=AbstainReason.NO_RAG_HITS,
            confidence_score=0.3,
            
            rag_topk_meta=[
                RAGHitMeta(
                    doc_title="Splunk Detection Rules v2.1",
                    score=0.7,
                    chunk_id="chunk_123",
                    source_type="playbook",
                    excerpt="Basic Splunk configuration for network monitoring..."
                ),
                RAGHitMeta(
                    doc_title="Lateral Movement Playbook",
                    score=0.6, 
                    chunk_id="chunk_456",
                    source_type="incident",
                    excerpt="Common lateral movement techniques include..."
                )
            ],
            has_citations=False,
            
            environment="prod",
            model_version="1.0.0", 
            latency_ms=250.0,
            
            pii_redaction=PIIRedactionSummary(safe_for_external=True)
        )
        
        # Test notification (will queue since no webhook)
        slack_manager = SlackAlertManager()
        await notify_knowledge_gap(mock_gap, slack_manager)
        
        # Show queued alerts
        queued = slack_manager.get_queued_alerts()
        print(f"Queued alerts: {len(queued)}")
        
    asyncio.run(demo())