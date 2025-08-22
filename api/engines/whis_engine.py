"""
Whis Engine: The core reasoning and enrichment engine
Implements both Teacher and Assistant modes for SOAR operations
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

from .llm_engine import LLMEngine
from .rag_engine import RAGEngine
from ..models.incident import Incident, IncidentSeverity
from ..models.playbook import Playbook, PlaybookAction
from ..schemas.detection import Detection, EnrichmentResult

logger = logging.getLogger(__name__)


class WhisMode(Enum):
    """Whis operational modes"""
    TEACHER = "teacher"
    ASSISTANT = "assistant"


@dataclass
class TeacherExplanation:
    """Teacher mode output structure"""
    event_summary: str
    attack_mapping: Dict[str, str]  # technique_id -> description
    false_positive_analysis: str
    threshold_recommendations: str
    best_practices: List[str]
    learning_resources: List[str]


@dataclass
class AssistantProposal:
    """Assistant mode output structure"""
    incident_assessment: str
    severity_rating: IncidentSeverity
    recommended_playbooks: List[Playbook]
    proposed_actions: List[PlaybookAction]
    enrichment_context: Dict[str, Any]
    approval_required: bool = True


class WhisEngine:
    """
    Core Whis reasoning engine implementing:
    - Teacher: Explains events, correlates with frameworks
    - Assistant: Proposes actions, routes playbooks
    """
    
    def __init__(self, llm_engine: LLMEngine, rag_engine: RAGEngine):
        self.llm = llm_engine
        self.rag = rag_engine
        self.logger = logging.getLogger(__name__)
        
        # Load knowledge base mappings
        self._load_attack_mappings()
        self._load_playbook_mappings()
    
    def _load_attack_mappings(self):
        """Load MITRE ATT&CK technique mappings"""
        # This would load from knowledge base
        self.attack_mappings = {
            "4625": "T1110",  # Failed logon -> Brute Force
            "4624": "T1078",  # Successful logon -> Valid Accounts
            "4648": "T1134",  # Logon with explicit credentials -> Token Manipulation
            "1102": "T1070.001",  # Audit log cleared -> Indicator Removal
            "7045": "T1543.003",  # Service installed -> Windows Service
        }
    
    def _load_playbook_mappings(self):
        """Load playbook routing rules"""
        self.playbook_mappings = {
            "T1110": ["Account_Lockdown", "Brute_Force_Investigation"],
            "T1078": ["Privilege_Review", "Account_Audit"],
            "T1543.003": ["Service_Analysis", "Persistence_Hunt"],
            "T1070.001": ["Log_Integrity_Check", "Forensic_Collection"],
        }

    async def explain_event(self, detection: Detection) -> TeacherExplanation:
        """
        Teacher mode: Explain security event with educational context
        
        Example: 4625 events -> T1110 brute force explanation
        """
        self.logger.info(f"🎓 Teacher mode: Explaining {detection.event_type}")
        
        # Get ATT&CK mapping
        attack_technique = self._map_to_attack(detection)
        
        # Retrieve knowledge from RAG
        context = await self._get_educational_context(detection, attack_technique)
        
        # Generate explanation using LLM
        explanation_prompt = self._build_teacher_prompt(detection, attack_technique, context)
        
        explanation = await self.llm.generate_response(
            prompt=explanation_prompt,
            max_tokens=1000,
            temperature=0.3  # More deterministic for education
        )
        
        return self._parse_teacher_response(explanation, attack_technique)
    
    async def propose_response(self, detection: Detection) -> AssistantProposal:
        """
        Assistant mode: Propose response actions and playbook routing
        
        Example: Confirmed brute force -> Account lockdown + investigation
        """
        self.logger.info(f"🤖 Assistant mode: Proposing response for {detection.event_type}")
        
        # Get attack context and severity
        attack_technique = self._map_to_attack(detection)
        severity = self._assess_severity(detection)
        
        # Retrieve relevant playbooks
        playbooks = await self._get_relevant_playbooks(attack_technique)
        
        # Generate response proposal
        proposal_prompt = self._build_assistant_prompt(detection, attack_technique, playbooks)
        
        proposal = await self.llm.generate_response(
            prompt=proposal_prompt,
            max_tokens=800,
            temperature=0.2  # Conservative for action proposals
        )
        
        return self._parse_assistant_response(proposal, severity, playbooks)
    
    async def enrich_detection(self, detection: Detection) -> EnrichmentResult:
        """
        Enrich detection with Whis intelligence for Splunk
        
        Output format: whis:enrichment with ATT&CK mapping + context
        """
        self.logger.info(f"🔍 Enriching detection: {detection.id}")
        
        # Get both teacher and assistant perspectives
        if detection.severity in ["low", "medium"]:
            # Educational enrichment for training
            explanation = await self.explain_event(detection)
            enrichment = {
                "whis_mode": "teacher",
                "attack_technique": explanation.attack_mapping,
                "educational_context": explanation.event_summary,
                "false_positive_guidance": explanation.false_positive_analysis,
                "tuning_recommendations": explanation.threshold_recommendations
            }
        else:
            # Response-focused enrichment for incidents
            proposal = await self.propose_response(detection)
            enrichment = {
                "whis_mode": "assistant", 
                "severity_assessment": proposal.severity_rating.value,
                "incident_summary": proposal.incident_assessment,
                "recommended_playbooks": [pb.name for pb in proposal.recommended_playbooks],
                "proposed_actions": [action.description for action in proposal.proposed_actions]
            }
        
        # Common enrichment fields
        enrichment.update({
            "timestamp": datetime.utcnow().isoformat(),
            "whis_version": "1.0.0",
            "confidence_score": self._calculate_confidence(detection),
            "requires_approval": True
        })
        
        return EnrichmentResult(
            detection_id=detection.id,
            enrichment_data=enrichment,
            source="whis_engine"
        )
    
    def _map_to_attack(self, detection: Detection) -> Optional[str]:
        """Map Windows event ID or detection type to MITRE ATT&CK technique"""
        # Simple mapping - in production this would be more sophisticated
        event_id = str(detection.event_id) if detection.event_id else detection.event_type
        return self.attack_mappings.get(event_id)
    
    def _assess_severity(self, detection: Detection) -> IncidentSeverity:
        """Assess incident severity based on detection characteristics"""
        # Simplified severity assessment
        if detection.severity == "critical":
            return IncidentSeverity.CRITICAL
        elif detection.severity == "high":
            return IncidentSeverity.HIGH
        elif detection.severity == "medium":
            return IncidentSeverity.MEDIUM
        else:
            return IncidentSeverity.LOW
    
    async def _get_educational_context(self, detection: Detection, technique: str) -> str:
        """Retrieve educational context from RAG knowledge base"""
        query = f"MITRE ATT&CK {technique} technique explanation false positives best practices"
        
        results = await self.rag.search_knowledge(
            query=query,
            namespace="attack_framework",
            limit=3
        )
        
        return "\n".join([doc.content for doc in results])
    
    async def _get_relevant_playbooks(self, technique: str) -> List[Playbook]:
        """Get relevant playbooks for ATT&CK technique"""
        # In production, this would query playbook database
        playbook_names = self.playbook_mappings.get(technique, [])
        
        # Mock playbook objects for now
        playbooks = []
        for name in playbook_names:
            playbooks.append(Playbook(
                id=f"pb_{name.lower()}",
                name=name,
                description=f"Automated response for {technique}",
                technique_mapping=[technique]
            ))
        
        return playbooks
    
    def _build_teacher_prompt(self, detection: Detection, technique: str, context: str) -> str:
        """Build prompt for teacher mode explanation"""
        return f"""
You are Whis, a cybersecurity teacher. Explain this security event in educational terms.

DETECTION:
- Event ID: {detection.event_id}
- Type: {detection.event_type}
- Source: {detection.source_system}
- Details: {detection.raw_data}

MITRE ATT&CK MAPPING: {technique}

KNOWLEDGE CONTEXT:
{context}

Provide a clear explanation covering:
1. What this event means
2. How it maps to MITRE ATT&CK
3. Common false positive scenarios
4. Detection tuning recommendations
5. Key learning points for analysts

Be educational but practical. Focus on helping analysts understand and improve.
"""
    
    def _build_assistant_prompt(self, detection: Detection, technique: str, playbooks: List[Playbook]) -> str:
        """Build prompt for assistant mode proposal"""
        playbook_list = "\n".join([f"- {pb.name}: {pb.description}" for pb in playbooks])
        
        return f"""
You are Whis, a cybersecurity assistant. Analyze this detection and propose response actions.

DETECTION:
- Event ID: {detection.event_id}
- Type: {detection.event_type}  
- Severity: {detection.severity}
- Source: {detection.source_system}
- Details: {detection.raw_data}

MITRE ATT&CK: {technique}

AVAILABLE PLAYBOOKS:
{playbook_list}

Provide:
1. Incident assessment summary
2. Recommended playbooks (prioritized)
3. Specific actions to propose for approval
4. Rationale for recommendations

Remember: All actions require human approval. Focus on clear, actionable proposals.
"""
    
    def _parse_teacher_response(self, response: str, technique: str) -> TeacherExplanation:
        """Parse LLM response into structured teacher explanation"""
        # Simplified parsing - in production would use structured output
        return TeacherExplanation(
            event_summary=response[:200] + "...",
            attack_mapping={technique: f"MITRE ATT&CK {technique}"},
            false_positive_analysis="Common false positives: service accounts, scheduled tasks",
            threshold_recommendations="Consider threshold tuning based on baseline",
            best_practices=["Monitor for patterns", "Correlate with other events"],
            learning_resources=[f"MITRE ATT&CK {technique}", "NIST IR framework"]
        )
    
    def _parse_assistant_response(self, response: str, severity: IncidentSeverity, playbooks: List[Playbook]) -> AssistantProposal:
        """Parse LLM response into structured assistant proposal"""
        # Simplified parsing - in production would use structured output
        return AssistantProposal(
            incident_assessment=response[:300] + "...",
            severity_rating=severity,
            recommended_playbooks=playbooks[:2],  # Top 2 recommendations
            proposed_actions=[
                PlaybookAction(
                    id="action_1",
                    name="Initial Assessment",
                    description="Analyze detection context and scope",
                    requires_approval=True
                )
            ],
            enrichment_context={
                "confidence": "high",
                "automated_actions": 0,
                "manual_actions": 1
            }
        )
    
    def _calculate_confidence(self, detection: Detection) -> float:
        """Calculate confidence score for enrichment"""
        # Simplified confidence calculation
        base_confidence = 0.7
        
        # Adjust based on data quality
        if detection.raw_data and len(detection.raw_data) > 100:
            base_confidence += 0.1
        
        # Adjust based on source reliability
        if detection.source_system == "limacharlie":
            base_confidence += 0.1
        
        return min(base_confidence, 1.0)


# Global instance
_whis_engine = None

async def get_whis_engine() -> WhisEngine:
    """Get or create global Whis engine instance"""
    global _whis_engine
    if _whis_engine is None:
        from .llm_engine import get_llm_engine
        from .rag_engine import get_rag_engine
        
        llm = await get_llm_engine()
        rag = await get_rag_engine()
        _whis_engine = WhisEngine(llm, rag)
    
    return _whis_engine