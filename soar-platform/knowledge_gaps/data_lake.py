#!/usr/bin/env python3
"""
🏊 Knowledge Gap Data Lake Manager
==================================
Manages persistence and retrieval of unanswered questions

[TAG: DATA-LAKE] - Structured storage implementation
[TAG: GOVERNANCE] - PII redaction enforcement
[TAG: CATALOG] - Query interface for analytics
"""

import json
import hashlib
import re
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

from .schemas import (
    UnansweredQuestionV1, 
    PIIRedactionSummary, 
    AbstainReason,
    IntentCategory,
    KnowledgeGapMetrics,
    DataLakePartition,
    PII_PATTERNS
)

logger = logging.getLogger(__name__)

class PIIRedactor:
    """
    PII redaction utility
    
    [TAG: GOVERNANCE] - Privacy protection
    """
    
    def __init__(self):
        self.patterns = [re.compile(pattern) for pattern in PII_PATTERNS]
    
    def redact_text(self, text: str) -> tuple[str, PIIRedactionSummary]:
        """Redact PII from text, return cleaned text + summary"""
        redacted_text = text
        patterns_found = []
        redaction_count = 0
        
        for i, pattern in enumerate(self.patterns):
            matches = pattern.findall(text)
            if matches:
                patterns_found.append(PII_PATTERNS[i])
                redaction_count += len(matches)
                redacted_text = pattern.sub('[REDACTED]', redacted_text)
        
        summary = PIIRedactionSummary(
            patterns_found=patterns_found,
            redaction_count=redaction_count,
            safe_for_external=redaction_count == 0,
            redaction_version="1.0.0"
        )
        
        return redacted_text, summary

class KnowledgeGapDataLake:
    """
    Data lake for knowledge gaps with partitioned storage
    
    [TAG: DATA-LAKE] - Main storage manager
    [TAG: CATALOG] - Query interface
    """
    
    def __init__(self, base_path: str = "data/knowledge_gaps"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.quarantine_path = self.base_path / "quarantine"
        self.quarantine_path.mkdir(exist_ok=True)
        self.redactor = PIIRedactor()
        
    def _get_partition_path(self, gap: UnansweredQuestionV1) -> Path:
        """Get partitioned storage path"""
        date_str = gap.timestamp.strftime("%Y-%m-%d")
        return self.base_path / date_str / gap.tenant / gap.intent.value
    
    def _generate_gap_id(self, query: str, timestamp: datetime) -> str:
        """Generate unique gap ID"""
        content = f"{query}{timestamp.isoformat()}"
        return f"gap_{hashlib.md5(content.encode()).hexdigest()[:12]}"
    
    def _classify_intent(self, query: str) -> IntentCategory:
        """Simple intent classification"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['what is', 'define', 'definition', 'explain']):
            return IntentCategory.DEFINITION
        elif any(word in query_lower for word in ['how to', 'how do', 'steps', 'procedure']):
            return IntentCategory.HOW_TO
        elif any(word in query_lower for word in ['troubleshoot', 'debug', 'fix', 'error']):
            return IntentCategory.TROUBLESHOOTING
        elif any(word in query_lower for word in ['analyze', 'investigate', 'examine']):
            return IntentCategory.ANALYSIS
        elif any(word in query_lower for word in ['configure', 'setup', 'install']):
            return IntentCategory.CONFIGURATION
        elif any(word in query_lower for word in ['hunt', 'search', 'find', 'detect']):
            return IntentCategory.INVESTIGATION
        else:
            return IntentCategory.UNKNOWN
    
    async def store_gap(self, 
                       query: str,
                       why_abstained: AbstainReason,
                       confidence_score: float,
                       context: Dict[str, Any]) -> UnansweredQuestionV1:
        """
        Store a knowledge gap with governance
        
        [TAG: GOVERNANCE] - PII redaction enforced
        """
        
        try:
            # Generate ID and redact PII
            gap_id = self._generate_gap_id(query, datetime.utcnow())
            query_redacted, pii_summary = self.redactor.redact_text(query)
            
            # Create structured record
            gap = UnansweredQuestionV1(
                id=gap_id,
                timestamp=datetime.utcnow(),
                tenant=context.get("tenant", "default"),
                channel=context.get("channel", "chat"),
                user_hash=hashlib.md5(context.get("user_id", "anonymous").encode()).hexdigest()[:8],
                session_id=context.get("session_id"),
                
                query_text_redacted=query_redacted,
                query_hash=hashlib.md5(query.encode()).hexdigest()[:8],
                intent=self._classify_intent(query),
                tokens=len(query.split()),
                
                why_abstained=why_abstained,
                confidence_score=confidence_score,
                
                rag_topk_meta=context.get("rag_hits", []),
                has_citations=context.get("has_citations", False),
                corpus_versions=context.get("corpus_versions", {}),
                
                environment=context.get("environment", "dev"),
                model_version=context.get("model_version", "1.0.0"),
                latency_ms=context.get("latency_ms", 0.0),
                
                pii_redaction=pii_summary
            )
            
            # Check if safe to store
            if not pii_summary.safe_for_external and context.get("require_safe", True):
                # Quarantine unsafe records
                await self._quarantine_record(gap, "pii_redaction_failed")
                logger.warning(f"Gap {gap_id} quarantined due to PII redaction failure")
                return gap
            
            # Store in partitioned structure
            partition_path = self._get_partition_path(gap)
            partition_path.mkdir(parents=True, exist_ok=True)
            
            file_path = partition_path / f"{gap_id}.json"
            with open(file_path, 'w') as f:
                json.dump(gap.model_dump(), f, indent=2, default=str)
            
            logger.info(f"Stored knowledge gap: {gap_id} ({why_abstained})")
            return gap
            
        except Exception as e:
            logger.error(f"Failed to store knowledge gap: {e}")
            raise
    
    async def _quarantine_record(self, gap: UnansweredQuestionV1, reason: str):
        """Quarantine problematic records"""
        quarantine_file = self.quarantine_path / f"{gap.id}_{reason}.json"
        with open(quarantine_file, 'w') as f:
            json.dump({
                "gap": gap.model_dump(),
                "quarantine_reason": reason,
                "quarantined_at": datetime.utcnow().isoformat()
            }, f, indent=2, default=str)
    
    def get_gaps_by_date(self, target_date: date, tenant: str = "default") -> List[UnansweredQuestionV1]:
        """Retrieve gaps for specific date"""
        date_str = target_date.strftime("%Y-%m-%d")
        date_path = self.base_path / date_str / tenant
        
        if not date_path.exists():
            return []
        
        gaps = []
        for intent_path in date_path.iterdir():
            if intent_path.is_dir():
                for gap_file in intent_path.glob("*.json"):
                    try:
                        with open(gap_file) as f:
                            gap_data = json.load(f)
                            gaps.append(UnansweredQuestionV1(**gap_data))
                    except Exception as e:
                        logger.error(f"Failed to load gap from {gap_file}: {e}")
        
        return gaps
    
    def get_recent_gaps(self, hours: int = 24, tenant: str = "default") -> List[UnansweredQuestionV1]:
        """Get recent knowledge gaps"""
        cutoff = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        gaps = []
        for i in range(hours // 24 + 1):
            target_date = (cutoff - timedelta(days=i)).date()
            daily_gaps = self.get_gaps_by_date(target_date, tenant)
            
            # Filter by actual time window
            recent_gaps = [
                gap for gap in daily_gaps
                if (datetime.utcnow() - gap.timestamp).total_seconds() <= hours * 3600
            ]
            gaps.extend(recent_gaps)
        
        return sorted(gaps, key=lambda x: x.timestamp, reverse=True)
    
    def calculate_metrics(self, hours: int = 24, tenant: str = "default") -> KnowledgeGapMetrics:
        """Calculate knowledge gap metrics"""
        gaps = self.get_recent_gaps(hours, tenant)
        
        if not gaps:
            return KnowledgeGapMetrics(
                timestamp=datetime.utcnow(),
                window_hours=hours,
                total_queries=0,
                gaps_count=0,
                gap_rate=0.0
            )
        
        # Calculate metrics
        gaps_by_intent = {}
        gaps_by_reason = {}
        
        for gap in gaps:
            # Count by intent
            if gap.intent not in gaps_by_intent:
                gaps_by_intent[gap.intent] = 0
            gaps_by_intent[gap.intent] += 1
            
            # Count by reason
            if gap.why_abstained not in gaps_by_reason:
                gaps_by_reason[gap.why_abstained] = 0
            gaps_by_reason[gap.why_abstained] += 1
        
        # Resolution metrics
        pending_review = sum(1 for gap in gaps if gap.approval_state.value == "pending")
        promoted_count = sum(1 for gap in gaps if gap.promoted_to_glossary)
        dismissed_count = sum(1 for gap in gaps if gap.approval_state.value == "dismissed")
        
        return KnowledgeGapMetrics(
            timestamp=datetime.utcnow(),
            window_hours=hours,
            total_queries=len(gaps),  # Simplified - in real system track all queries
            gaps_count=len(gaps),
            gap_rate=1.0,  # Would be gaps/total in real system
            gaps_by_intent=gaps_by_intent,
            gaps_by_reason=gaps_by_reason,
            pending_review=pending_review,
            promoted_count=promoted_count,
            dismissed_count=dismissed_count
        )
    
    def get_partition_info(self, target_date: date, tenant: str = "default") -> List[DataLakePartition]:
        """Get partition statistics"""
        date_str = target_date.strftime("%Y-%m-%d")
        date_path = self.base_path / date_str / tenant
        
        if not date_path.exists():
            return []
        
        partitions = []
        for intent_path in date_path.iterdir():
            if intent_path.is_dir():
                files = list(intent_path.glob("*.json"))
                total_size = sum(f.stat().st_size for f in files)
                
                partition = DataLakePartition(
                    date=date_str,
                    tenant=tenant,
                    intent=IntentCategory(intent_path.name),
                    record_count=len(files),
                    total_size_bytes=total_size,
                    last_updated=datetime.fromtimestamp(max(f.stat().st_mtime for f in files) if files else 0)
                )
                partitions.append(partition)
        
        return partitions
    
    def search_gaps(self, 
                   query_text: Optional[str] = None,
                   intent: Optional[IntentCategory] = None,
                   reason: Optional[AbstainReason] = None,
                   days_back: int = 7,
                   tenant: str = "default") -> List[UnansweredQuestionV1]:
        """Search knowledge gaps with filters"""
        
        gaps = []
        for i in range(days_back):
            target_date = (datetime.utcnow() - timedelta(days=i)).date()
            daily_gaps = self.get_gaps_by_date(target_date, tenant)
            gaps.extend(daily_gaps)
        
        # Apply filters
        if query_text:
            query_text_lower = query_text.lower()
            gaps = [gap for gap in gaps if query_text_lower in gap.query_text_redacted.lower()]
        
        if intent:
            gaps = [gap for gap in gaps if gap.intent == intent]
        
        if reason:
            gaps = [gap for gap in gaps if gap.why_abstained == reason]
        
        return sorted(gaps, key=lambda x: x.timestamp, reverse=True)

# Convenience function for integration
async def log_knowledge_gap(query: str,
                           confidence: float,
                           reason: AbstainReason,
                           context: Dict[str, Any],
                           data_lake: Optional[KnowledgeGapDataLake] = None,
                           notify_slack: bool = True) -> UnansweredQuestionV1:
    """
    Convenience function to log a knowledge gap with optional Slack notification
    
    [TAG: CONFIDENCE-GATES] - Main abstain logging interface
    [TAG: SLACK-ALERT] - Integrated notification pipeline
    """
    if data_lake is None:
        data_lake = KnowledgeGapDataLake()
    
    # Store the gap
    gap = await data_lake.store_gap(query, reason, confidence, context)
    
    # Send Slack notification if enabled and not quarantined
    if notify_slack and gap.pii_redaction.safe_for_external:
        try:
            from .slack_alerts import notify_knowledge_gap
            await notify_knowledge_gap(gap)
        except ImportError:
            logger.warning("Slack alerts not available - install slack_alerts module")
        except Exception as e:
            logger.error(f"Failed to send Slack notification for gap {gap.id}: {e}")
    
    return gap

if __name__ == "__main__":
    # Example usage
    import asyncio
    from datetime import timedelta
    
    async def demo():
        lake = KnowledgeGapDataLake("demo_data_lake")
        
        # Store sample gaps
        await lake.store_gap(
            "What is the latest Splunk configuration for detecting lateral movement?",
            AbstainReason.NO_RAG_HITS,
            0.3,
            {
                "tenant": "acme_corp",
                "channel": "slack",
                "user_id": "user123",
                "environment": "prod"
            }
        )
        
        # Get metrics
        metrics = lake.calculate_metrics(hours=24)
        print("Knowledge Gap Metrics:")
        print(f"- Total gaps: {metrics.gaps_count}")
        print(f"- Gap rate: {metrics.gap_rate:.2%}")
        print(f"- By intent: {metrics.gaps_by_intent}")
        
    asyncio.run(demo())