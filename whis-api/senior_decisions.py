#!/usr/bin/env python3
"""
🧠 Senior-Level Decision Framework for WHIS SOAR-Copilot
Planning pass, thinking artifacts, and safety-first decision making
"""

import json
import logging
import hashlib
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import asyncio

logger = logging.getLogger(__name__)

class DecisionType(Enum):
    """Types of senior-level decisions"""
    SAFE_ANALYSIS = "safe_analysis"
    SAFETY_REFUSAL = "safety_refusal"
    PARTIAL_RESPONSE = "partial_response"
    ESCALATION_NEEDED = "escalation_needed"

class RiskLevel(Enum):
    """Risk assessment levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    UNACCEPTABLE = "unacceptable"

@dataclass
class ThinkingArtifact:
    """Internal thinking/planning artifact (not shown to user)"""
    artifact_id: str
    timestamp: str
    decision_type: DecisionType
    risk_assessment: RiskLevel
    thinking_steps: List[str]
    safety_considerations: List[str]
    planned_approach: str
    confidence_rationale: str
    citations_planned: List[str]
    red_flags_identified: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "artifact_id": self.artifact_id,
            "timestamp": self.timestamp,
            "decision_type": self.decision_type.value,
            "risk_assessment": self.risk_assessment.value,
            "thinking_steps": self.thinking_steps,
            "safety_considerations": self.safety_considerations,
            "planned_approach": self.planned_approach,
            "confidence_rationale": self.confidence_rationale,
            "citations_planned": self.citations_planned,
            "red_flags_identified": self.red_flags_identified
        }

@dataclass
class SeniorDecision:
    """Final senior-level decision with action plan"""
    decision_id: str
    thinking_artifact_id: str
    decision_type: DecisionType
    approved_actions: List[str]
    rejected_actions: List[str]
    safety_guardrails: List[str]
    human_review_required: bool
    escalation_reason: Optional[str]
    response_modifications: Dict[str, Any]
    timestamp: str

class SeniorDecisionEngine:
    """Senior-level decision making with planning and safety"""
    
    def __init__(self):
        self.thinking_artifacts = {}
        self.decisions = {}
        self.unsafe_patterns = [
            # Destructive operations
            r"delete.*all|rm\s+-rf|format\s+c:|wipe.*drive",
            # Credential exposure
            r"password\s*[:=]\s*\S+|api[_-]?key\s*[:=]|secret\s*[:=]",
            # Network attacks
            r"ddos|denial.*service|flood.*attack|exploit.*vulnerability",
            # Data exfiltration
            r"exfiltrat|steal.*data|dump.*credentials|harvest.*password",
            # System compromise
            r"backdoor|rootkit|reverse.*shell|persistent.*access"
        ]
        
        logger.info("🧠 Senior Decision Engine initialized")
    
    async def planning_pass(
        self, 
        event_data: Dict[str, Any],
        initial_response: Dict[str, Any]
    ) -> Tuple[ThinkingArtifact, SeniorDecision]:
        """
        Senior-level planning pass before final response
        
        This is the "thinking" phase where we:
        1. Assess the security event and proposed response
        2. Identify safety concerns and red flags
        3. Plan the approach with proper guardrails
        4. Make senior-level decisions on what to allow/reject
        """
        artifact_id = f"think_{hashlib.md5(json.dumps(event_data).encode()).hexdigest()[:8]}"
        
        # Step 1: Risk Assessment
        risk_level = await self._assess_risk(event_data, initial_response)
        
        # Step 2: Safety Analysis
        safety_concerns = await self._analyze_safety(event_data, initial_response)
        red_flags = await self._identify_red_flags(event_data, initial_response)
        
        # Step 3: Planning
        thinking_steps = await self._generate_thinking_steps(event_data, risk_level)
        planned_approach = await self._plan_approach(event_data, risk_level, safety_concerns)
        
        # Step 4: Confidence and Citation Planning
        confidence_rationale = await self._rationalize_confidence(event_data, initial_response)
        citations_planned = await self._plan_citations(event_data)
        
        # Create thinking artifact (internal use only)
        thinking_artifact = ThinkingArtifact(
            artifact_id=artifact_id,
            timestamp=datetime.now().isoformat(),
            decision_type=self._determine_decision_type(risk_level, red_flags),
            risk_assessment=risk_level,
            thinking_steps=thinking_steps,
            safety_considerations=safety_concerns,
            planned_approach=planned_approach,
            confidence_rationale=confidence_rationale,
            citations_planned=citations_planned,
            red_flags_identified=red_flags
        )
        
        self.thinking_artifacts[artifact_id] = thinking_artifact
        
        # Step 5: Make Senior Decision
        senior_decision = await self._make_senior_decision(
            thinking_artifact, event_data, initial_response
        )
        
        return thinking_artifact, senior_decision
    
    async def _assess_risk(
        self, 
        event_data: Dict[str, Any], 
        response: Dict[str, Any]
    ) -> RiskLevel:
        """Assess risk level of the event and proposed response"""
        risk_score = 0
        
        # Check event severity
        event_type = event_data.get("search_name", "").lower()
        if any(term in event_type for term in ["apt", "ransomware", "critical"]):
            risk_score += 3
        elif any(term in event_type for term in ["suspicious", "malware", "threat"]):
            risk_score += 2
        else:
            risk_score += 1
        
        # Check for dangerous recommendations
        response_text = json.dumps(response).lower()
        for pattern in self.unsafe_patterns:
            import re
            if re.search(pattern, response_text):
                risk_score += 5  # High penalty for unsafe content
        
        # Check system criticality
        host = event_data.get("host", "").lower()
        if any(term in host for term in ["dc", "domain", "critical", "server"]):
            risk_score += 2
        
        # Map score to risk level
        if risk_score >= 8:
            return RiskLevel.UNACCEPTABLE
        elif risk_score >= 6:
            return RiskLevel.CRITICAL
        elif risk_score >= 4:
            return RiskLevel.HIGH
        elif risk_score >= 2:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    async def _analyze_safety(
        self, 
        event_data: Dict[str, Any], 
        response: Dict[str, Any]
    ) -> List[str]:
        """Analyze safety considerations"""
        safety_concerns = []
        
        # Check for destructive operations
        containment = response.get("containment", [])
        for action in containment:
            if any(term in action.lower() for term in ["delete", "wipe", "format", "destroy"]):
                safety_concerns.append(f"Potentially destructive action: {action}")
        
        # Check for credential exposure risk
        if "password" in json.dumps(response).lower() or "secret" in json.dumps(response).lower():
            safety_concerns.append("Response may contain or reference sensitive credentials")
        
        # Check for network-wide impact
        if any(term in json.dumps(response).lower() for term in ["all systems", "entire network", "domain-wide"]):
            safety_concerns.append("Actions may have network-wide impact")
        
        # Check for irreversible actions
        remediation = response.get("remediation", [])
        for action in remediation:
            if any(term in action.lower() for term in ["reinstall", "rebuild", "factory reset"]):
                safety_concerns.append(f"Irreversible action recommended: {action}")
        
        return safety_concerns
    
    async def _identify_red_flags(
        self, 
        event_data: Dict[str, Any], 
        response: Dict[str, Any]
    ) -> List[str]:
        """Identify red flags that require special handling"""
        red_flags = []
        
        # Check if user is asking for help with attacks
        request_text = json.dumps(event_data).lower()
        if any(term in request_text for term in ["how to attack", "exploit", "hack into", "bypass security"]):
            red_flags.append("Request appears to seek offensive security assistance")
        
        # Check for impossible confidence levels
        confidence = response.get("confidence", 0)
        grounded = response.get("grounded", False)
        citations = response.get("citations", [])
        
        if confidence > 0.95 and not citations:
            red_flags.append("Extremely high confidence without supporting citations")
        
        if grounded and not citations:
            red_flags.append("Claims to be grounded but provides no citations")
        
        # Check for hallucinated tools/techniques
        spl_query = response.get("spl_query", "")
        if "SecurityTool" in spl_query or "MagicScanner" in spl_query:
            red_flags.append("Response references non-existent security tools")
        
        return red_flags
    
    async def _generate_thinking_steps(
        self, 
        event_data: Dict[str, Any], 
        risk_level: RiskLevel
    ) -> List[str]:
        """Generate internal thinking steps for the planning pass"""
        steps = []
        
        # Understand the event
        event_type = event_data.get("search_name", "Unknown Event")
        steps.append(f"1. Analyzing security event: {event_type}")
        
        # Assess criticality
        steps.append(f"2. Risk assessment completed: {risk_level.value}")
        
        # Plan response strategy
        if risk_level in [RiskLevel.CRITICAL, RiskLevel.HIGH]:
            steps.append("3. High-risk event requires immediate containment focus")
            steps.append("4. Prioritizing isolation and evidence preservation")
        else:
            steps.append("3. Standard incident response workflow applicable")
            steps.append("4. Following triage -> contain -> remediate sequence")
        
        # Safety considerations
        steps.append("5. Validating all recommendations for safety compliance")
        
        # Confidence calibration
        steps.append("6. Calibrating confidence based on available information")
        
        return steps
    
    async def _plan_approach(
        self, 
        event_data: Dict[str, Any],
        risk_level: RiskLevel,
        safety_concerns: List[str]
    ) -> str:
        """Plan the overall approach for handling this event"""
        if risk_level == RiskLevel.UNACCEPTABLE:
            return "REFUSE: Request contains unacceptable risk. Provide safety guidance only."
        
        elif risk_level == RiskLevel.CRITICAL:
            return "ESCALATE: Critical risk event requires human SOC analyst review. Provide conservative recommendations with clear escalation path."
        
        elif safety_concerns:
            return f"GUARDRAILS: Proceed with response but apply safety guardrails. {len(safety_concerns)} safety considerations identified."
        
        else:
            return "STANDARD: Provide comprehensive SOAR guidance following best practices."
    
    async def _rationalize_confidence(
        self, 
        event_data: Dict[str, Any], 
        response: Dict[str, Any]
    ) -> str:
        """Rationalize the confidence level"""
        confidence = response.get("confidence", 0.7)
        
        if confidence > 0.9:
            return "High confidence due to clear indicators and well-documented attack pattern"
        elif confidence > 0.7:
            return "Moderate confidence based on common security patterns and available context"
        elif confidence > 0.5:
            return "Limited confidence due to incomplete information or ambiguous indicators"
        else:
            return "Low confidence - insufficient data for definitive analysis"
    
    async def _plan_citations(self, event_data: Dict[str, Any]) -> List[str]:
        """Plan appropriate citations for the response"""
        citations = ["MITRE ATT&CK Framework"]
        
        event_type = event_data.get("search_name", "").lower()
        
        if "ransomware" in event_type:
            citations.append("CISA Ransomware Guide")
        elif "apt" in event_type:
            citations.append("Mandiant APT Groups")
        elif "lateral" in event_type:
            citations.append("SANS Lateral Movement Detection")
        
        citations.append("NIST Incident Response Guide SP 800-61r2")
        
        return citations
    
    def _determine_decision_type(
        self, 
        risk_level: RiskLevel, 
        red_flags: List[str]
    ) -> DecisionType:
        """Determine the type of decision to make"""
        if risk_level == RiskLevel.UNACCEPTABLE or len(red_flags) > 3:
            return DecisionType.SAFETY_REFUSAL
        elif risk_level == RiskLevel.CRITICAL:
            return DecisionType.ESCALATION_NEEDED
        elif red_flags:
            return DecisionType.PARTIAL_RESPONSE
        else:
            return DecisionType.SAFE_ANALYSIS
    
    async def _make_senior_decision(
        self,
        thinking: ThinkingArtifact,
        event_data: Dict[str, Any],
        initial_response: Dict[str, Any]
    ) -> SeniorDecision:
        """Make final senior-level decision"""
        decision_id = f"decision_{thinking.artifact_id}"
        
        # Determine what to approve/reject
        approved_actions = []
        rejected_actions = []
        safety_guardrails = []
        response_modifications = {}
        
        if thinking.decision_type == DecisionType.SAFETY_REFUSAL:
            # Reject everything dangerous
            rejected_actions = initial_response.get("containment", []) + initial_response.get("remediation", [])
            response_modifications = {
                "response": "I cannot provide guidance for this request as it appears to involve unsafe or malicious operations. Please consult with your security team for appropriate incident response procedures.",
                "triage_steps": [],
                "containment": [],
                "remediation": [],
                "safety_classification": "REFUSED - Unsafe request detected"
            }
            human_review_required = True
            escalation_reason = "Safety refusal triggered - potential malicious request"
            
        elif thinking.decision_type == DecisionType.ESCALATION_NEEDED:
            # Approve conservative actions only
            approved_actions = initial_response.get("triage_steps", [])[:2]  # Only basic triage
            rejected_actions = [a for a in initial_response.get("containment", []) if "delete" in a.lower() or "wipe" in a.lower()]
            safety_guardrails = [
                "Obtain SOC analyst approval before containment",
                "Preserve all forensic evidence",
                "Document all actions taken"
            ]
            response_modifications["escalation_notice"] = "⚠️ Critical event - SOC analyst review required"
            human_review_required = True
            escalation_reason = f"Critical risk level: {thinking.risk_assessment.value}"
            
        elif thinking.decision_type == DecisionType.PARTIAL_RESPONSE:
            # Approve most but apply guardrails
            approved_actions = initial_response.get("triage_steps", []) + [
                a for a in initial_response.get("containment", []) 
                if "monitor" in a.lower() or "isolate" in a.lower()
            ]
            rejected_actions = [
                a for a in initial_response.get("remediation", [])
                if any(term in a.lower() for term in ["rebuild", "reinstall", "format"])
            ]
            safety_guardrails = [
                "Test containment actions in isolated environment first",
                "Maintain backups before remediation"
            ]
            human_review_required = False
            escalation_reason = None
            
        else:  # SAFE_ANALYSIS
            # Approve everything with standard guardrails
            approved_actions = (
                initial_response.get("triage_steps", []) +
                initial_response.get("containment", []) +
                initial_response.get("remediation", [])
            )
            rejected_actions = []
            safety_guardrails = ["Follow organization's incident response procedures"]
            human_review_required = False
            escalation_reason = None
        
        # Apply confidence calibration
        if thinking.risk_assessment in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            response_modifications["confidence"] = min(initial_response.get("confidence", 0.7), 0.8)
        
        # Apply citation planning
        response_modifications["citations"] = thinking.citations_planned
        
        decision = SeniorDecision(
            decision_id=decision_id,
            thinking_artifact_id=thinking.artifact_id,
            decision_type=thinking.decision_type,
            approved_actions=approved_actions,
            rejected_actions=rejected_actions,
            safety_guardrails=safety_guardrails,
            human_review_required=human_review_required,
            escalation_reason=escalation_reason,
            response_modifications=response_modifications,
            timestamp=datetime.now().isoformat()
        )
        
        self.decisions[decision_id] = decision
        
        logger.info(f"[{decision_id}] Senior decision: {thinking.decision_type.value} (Risk: {thinking.risk_assessment.value})")
        
        return decision
    
    def apply_senior_decision(
        self,
        initial_response: Dict[str, Any],
        decision: SeniorDecision
    ) -> Dict[str, Any]:
        """Apply senior decision to modify the response"""
        modified_response = initial_response.copy()
        
        # Apply response modifications
        for key, value in decision.response_modifications.items():
            modified_response[key] = value
        
        # Add safety guardrails if not refusing
        if decision.decision_type != DecisionType.SAFETY_REFUSAL:
            modified_response["safety_guardrails"] = decision.safety_guardrails
        
        # Add escalation notice if needed
        if decision.human_review_required:
            modified_response["human_review_required"] = True
            modified_response["escalation_reason"] = decision.escalation_reason
        
        # Filter out rejected actions
        if decision.rejected_actions:
            # Remove rejected containment actions
            if "containment" in modified_response:
                modified_response["containment"] = [
                    a for a in modified_response["containment"]
                    if a not in decision.rejected_actions
                ]
            
            # Remove rejected remediation actions
            if "remediation" in modified_response:
                modified_response["remediation"] = [
                    a for a in modified_response["remediation"]
                    if a not in decision.rejected_actions
                ]
        
        return modified_response
    
    def get_thinking_artifact(self, artifact_id: str) -> Optional[ThinkingArtifact]:
        """Retrieve thinking artifact (for debugging/audit only)"""
        return self.thinking_artifacts.get(artifact_id)
    
    def get_decision(self, decision_id: str) -> Optional[SeniorDecision]:
        """Retrieve senior decision record"""
        return self.decisions.get(decision_id)

# Global senior decision engine
senior_decision_engine = SeniorDecisionEngine()