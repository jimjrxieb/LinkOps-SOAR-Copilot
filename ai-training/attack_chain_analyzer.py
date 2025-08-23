#!/usr/bin/env python3
"""
🔗 Attack Chain Analyzer for WHIS Red vs Blue Training Loop
Analyzes attack sequences, correlates events, and generates training data
"""

import json
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import hashlib

logger = logging.getLogger(__name__)

class AttackPhase(Enum):
    """MITRE ATT&CK phases"""
    RECONNAISSANCE = "reconnaissance"
    RESOURCE_DEVELOPMENT = "resource_development"
    INITIAL_ACCESS = "initial_access"
    EXECUTION = "execution"
    PERSISTENCE = "persistence"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    DEFENSE_EVASION = "defense_evasion"
    CREDENTIAL_ACCESS = "credential_access"
    DISCOVERY = "discovery"
    LATERAL_MOVEMENT = "lateral_movement"
    COLLECTION = "collection"
    COMMAND_AND_CONTROL = "command_and_control"
    EXFILTRATION = "exfiltration"
    IMPACT = "impact"

@dataclass
class AttackEvent:
    """Single attack event with context"""
    event_id: str
    timestamp: datetime
    source: str  # sysmon, limacharlie, splunk
    event_type: str
    host: str
    user: str
    process: str
    command_line: str
    network_info: Dict[str, Any]
    file_info: Dict[str, Any]
    registry_info: Dict[str, Any]
    mitre_techniques: List[str]
    attack_phase: Optional[AttackPhase]
    confidence: float
    raw_data: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
            "event_type": self.event_type,
            "host": self.host,
            "user": self.user,
            "process": self.process,
            "command_line": self.command_line,
            "network_info": self.network_info,
            "file_info": self.file_info,
            "registry_info": self.registry_info,
            "mitre_techniques": self.mitre_techniques,
            "attack_phase": self.attack_phase.value if self.attack_phase else None,
            "confidence": self.confidence,
            "raw_data": self.raw_data
        }

@dataclass
class AttackChain:
    """Complete attack chain sequence"""
    chain_id: str
    start_time: datetime
    end_time: Optional[datetime]
    attacker_ip: str
    target_hosts: List[str]
    events: List[AttackEvent]
    phases_detected: List[AttackPhase]
    techniques_used: List[str]
    success_indicators: List[str]
    whis_responses: List[Dict[str, Any]]
    training_value: float  # How valuable this chain is for training
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "chain_id": self.chain_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "attacker_ip": self.attacker_ip,
            "target_hosts": self.target_hosts,
            "events": [event.to_dict() for event in self.events],
            "phases_detected": [phase.value for phase in self.phases_detected],
            "techniques_used": self.techniques_used,
            "success_indicators": self.success_indicators,
            "whis_responses": self.whis_responses,
            "training_value": self.training_value
        }

class AttackChainAnalyzer:
    """Analyzes security events to identify and correlate attack chains"""
    
    def __init__(self):
        self.active_chains = {}  # chain_id -> AttackChain
        self.completed_chains = []
        self.correlation_window = timedelta(hours=2)  # Events within 2 hours are correlated
        self.chain_timeout = timedelta(hours=6)  # Close chains after 6 hours of inactivity
        
        # MITRE technique mapping
        self.technique_to_phase = {
            "T1078": AttackPhase.DEFENSE_EVASION,  # Valid Accounts
            "T1059.001": AttackPhase.EXECUTION,    # PowerShell
            "T1059.003": AttackPhase.EXECUTION,    # Windows Command Shell
            "T1021.001": AttackPhase.LATERAL_MOVEMENT,  # RDP
            "T1021.002": AttackPhase.LATERAL_MOVEMENT,  # SMB/Windows Admin Shares
            "T1055": AttackPhase.DEFENSE_EVASION,  # Process Injection
            "T1003.001": AttackPhase.CREDENTIAL_ACCESS,  # LSASS Memory
            "T1082": AttackPhase.DISCOVERY,        # System Information Discovery
            "T1083": AttackPhase.DISCOVERY,        # File and Directory Discovery
            "T1105": AttackPhase.COMMAND_AND_CONTROL,  # Ingress Tool Transfer
            "T1547.001": AttackPhase.PERSISTENCE,  # Registry Run Keys
            "T1112": AttackPhase.DEFENSE_EVASION,  # Modify Registry
            "T1486": AttackPhase.IMPACT,           # Data Encrypted for Impact
            "T1490": AttackPhase.IMPACT,           # Inhibit System Recovery
        }
        
        logger.info("🔗 Attack Chain Analyzer initialized")
    
    async def analyze_event(self, event_data: Dict[str, Any]) -> Optional[AttackChain]:
        """Analyze a new security event and correlate with attack chains"""
        try:
            # Parse event into AttackEvent
            attack_event = self._parse_security_event(event_data)
            if not attack_event:
                return None
            
            logger.info(f"🔍 Analyzing event: {attack_event.event_type} on {attack_event.host}")
            
            # Find or create attack chain
            chain = await self._correlate_with_chains(attack_event)
            if not chain:
                chain = await self._create_new_chain(attack_event)
            
            # Add event to chain
            chain.events.append(attack_event)
            
            # Update chain analysis
            await self._update_chain_analysis(chain, attack_event)
            
            # Check if chain should be completed
            if await self._should_complete_chain(chain):
                await self._complete_chain(chain)
                return chain
            
            return None  # Chain still active
            
        except Exception as e:
            logger.error(f"Error analyzing attack event: {e}")
            return None
    
    def _parse_security_event(self, event_data: Dict[str, Any]) -> Optional[AttackEvent]:
        """Parse raw security event into AttackEvent structure"""
        try:
            # Determine source system
            source = "unknown"
            if "Microsoft-Windows-Sysmon" in str(event_data):
                source = "sysmon"
            elif "detect" in event_data:
                source = "limacharlie"
            elif "search_name" in event_data:
                source = "splunk"
            
            # Extract common fields
            event_id = event_data.get("event_id", f"evt_{int(datetime.now().timestamp())}")
            timestamp = datetime.now()  # In real implementation, parse from event
            
            # Map to attack event structure
            attack_event = AttackEvent(
                event_id=event_id,
                timestamp=timestamp,
                source=source,
                event_type=event_data.get("search_name", event_data.get("event_type", "Unknown")),
                host=event_data.get("host", event_data.get("Computer", "unknown")),
                user=event_data.get("user", event_data.get("User", "unknown")),
                process=event_data.get("process", event_data.get("Image", "")),
                command_line=event_data.get("CommandLine", event_data.get("command", "")),
                network_info={
                    "src_ip": event_data.get("src_ip", event_data.get("SourceIp", "")),
                    "dest_ip": event_data.get("dest_ip", event_data.get("DestinationIp", "")),
                    "src_port": event_data.get("src_port", ""),
                    "dest_port": event_data.get("dest_port", "")
                },
                file_info={
                    "file_path": event_data.get("file_path", event_data.get("TargetFilename", "")),
                    "file_hash": event_data.get("file_hash", event_data.get("Hashes", ""))
                },
                registry_info={
                    "key_path": event_data.get("registry_key", event_data.get("TargetObject", "")),
                    "value_name": event_data.get("registry_value", event_data.get("Details", ""))
                },
                mitre_techniques=self._extract_mitre_techniques(event_data),
                attack_phase=self._determine_attack_phase(event_data),
                confidence=0.7,  # Default confidence
                raw_data=event_data
            )
            
            return attack_event
            
        except Exception as e:
            logger.error(f"Error parsing security event: {e}")
            return None
    
    def _extract_mitre_techniques(self, event_data: Dict[str, Any]) -> List[str]:
        """Extract MITRE ATT&CK techniques from event"""
        techniques = []
        
        # Check for explicit MITRE field
        if "mitre" in event_data:
            techniques.extend(event_data["mitre"])
        
        # Infer from event content
        event_text = json.dumps(event_data).lower()
        
        if "powershell" in event_text:
            techniques.append("T1059.001")
        if "cmd.exe" in event_text or "command" in event_text:
            techniques.append("T1059.003")
        if "rdp" in event_text or "3389" in event_text:
            techniques.append("T1021.001")
        if "smb" in event_text or "445" in event_text:
            techniques.append("T1021.002")
        if "registry" in event_text:
            techniques.append("T1112")
        if "lsass" in event_text or "credential" in event_text:
            techniques.append("T1003.001")
        
        return list(set(techniques))  # Remove duplicates
    
    def _determine_attack_phase(self, event_data: Dict[str, Any]) -> Optional[AttackPhase]:
        """Determine attack phase from event"""
        # Extract techniques and map to phase
        techniques = self._extract_mitre_techniques(event_data)
        
        for technique in techniques:
            if technique in self.technique_to_phase:
                return self.technique_to_phase[technique]
        
        # Fallback: infer from event type
        event_type = str(event_data.get("event_type", "")).lower()
        
        if "login" in event_type or "logon" in event_type:
            return AttackPhase.INITIAL_ACCESS
        elif "process" in event_type:
            return AttackPhase.EXECUTION
        elif "network" in event_type:
            return AttackPhase.COMMAND_AND_CONTROL
        elif "file" in event_type:
            return AttackPhase.COLLECTION
        
        return None
    
    async def _correlate_with_chains(self, event: AttackEvent) -> Optional[AttackChain]:
        """Find existing attack chain that correlates with this event"""
        
        # Clean up old chains first
        await self._cleanup_old_chains()
        
        # Look for chains with matching indicators
        for chain in self.active_chains.values():
            # Time-based correlation
            time_diff = abs((event.timestamp - chain.start_time).total_seconds())
            if time_diff > self.correlation_window.total_seconds():
                continue
            
            # Host-based correlation
            if event.host in chain.target_hosts:
                return chain
            
            # IP-based correlation (if we can determine attacker IP)
            if (event.network_info.get("src_ip") and 
                event.network_info["src_ip"] == chain.attacker_ip):
                return chain
            
            # User-based correlation
            if (event.user and event.user != "unknown" and
                any(e.user == event.user for e in chain.events)):
                return chain
            
            # Process tree correlation
            if (event.process and 
                any(e.process in event.command_line or event.process in e.command_line 
                    for e in chain.events)):
                return chain
        
        return None
    
    async def _create_new_chain(self, initial_event: AttackEvent) -> AttackChain:
        """Create a new attack chain starting with this event"""
        chain_id = f"chain_{hashlib.md5(f'{initial_event.host}_{initial_event.timestamp}'.encode()).hexdigest()[:8]}"
        
        # Try to determine attacker IP
        attacker_ip = "unknown"
        if initial_event.network_info.get("src_ip"):
            src_ip = initial_event.network_info["src_ip"]
            # External IPs are likely attackers
            if not (src_ip.startswith("10.") or src_ip.startswith("192.168.") or src_ip.startswith("172.")):
                attacker_ip = src_ip
        
        chain = AttackChain(
            chain_id=chain_id,
            start_time=initial_event.timestamp,
            end_time=None,
            attacker_ip=attacker_ip,
            target_hosts=[initial_event.host],
            events=[],
            phases_detected=[],
            techniques_used=[],
            success_indicators=[],
            whis_responses=[],
            training_value=0.0
        )
        
        self.active_chains[chain_id] = chain
        logger.info(f"🔗 Created new attack chain: {chain_id}")
        
        return chain
    
    async def _update_chain_analysis(self, chain: AttackChain, new_event: AttackEvent):
        """Update chain analysis with new event"""
        # Update target hosts
        if new_event.host not in chain.target_hosts:
            chain.target_hosts.append(new_event.host)
        
        # Update attack phases
        if new_event.attack_phase and new_event.attack_phase not in chain.phases_detected:
            chain.phases_detected.append(new_event.attack_phase)
        
        # Update techniques
        for technique in new_event.mitre_techniques:
            if technique not in chain.techniques_used:
                chain.techniques_used.append(technique)
        
        # Detect success indicators
        await self._detect_success_indicators(chain, new_event)
        
        # Calculate training value
        chain.training_value = await self._calculate_training_value(chain)
    
    async def _detect_success_indicators(self, chain: AttackChain, event: AttackEvent):
        """Detect indicators of successful attack progression"""
        indicators = []
        
        # Privilege escalation success
        if event.user in ["administrator", "system", "root"]:
            indicators.append("privilege_escalation_success")
        
        # Lateral movement success
        if len(chain.target_hosts) > 1:
            indicators.append("lateral_movement_success")
        
        # Persistence establishment
        if "registry" in event.command_line.lower() and "run" in event.command_line.lower():
            indicators.append("persistence_established")
        
        # Credential access
        if "lsass" in event.command_line.lower() or "mimikatz" in event.command_line.lower():
            indicators.append("credential_access_success")
        
        # Data access
        if any(keyword in event.file_info.get("file_path", "").lower() 
               for keyword in ["documents", "desktop", "downloads", "confidential"]):
            indicators.append("data_access_success")
        
        # Command and control
        if (event.network_info.get("dest_ip") and 
            not event.network_info["dest_ip"].startswith(("10.", "192.168.", "172."))):
            indicators.append("c2_communication_success")
        
        # Add new indicators
        for indicator in indicators:
            if indicator not in chain.success_indicators:
                chain.success_indicators.append(indicator)
                logger.info(f"🎯 Attack success detected in {chain.chain_id}: {indicator}")
    
    async def _calculate_training_value(self, chain: AttackChain) -> float:
        """Calculate how valuable this attack chain is for training"""
        value = 0.0
        
        # More events = more training data
        value += min(len(chain.events) * 0.1, 1.0)
        
        # More attack phases = more comprehensive
        value += len(chain.phases_detected) * 0.1
        
        # More techniques = more educational
        value += len(chain.techniques_used) * 0.05
        
        # Success indicators = realistic scenarios
        value += len(chain.success_indicators) * 0.2
        
        # Multi-host attacks = lateral movement examples
        if len(chain.target_hosts) > 1:
            value += 0.5
        
        # Long-running attacks = persistent threats
        if chain.end_time and (chain.end_time - chain.start_time).total_seconds() > 3600:
            value += 0.3
        
        return min(value, 1.0)  # Cap at 1.0
    
    async def _should_complete_chain(self, chain: AttackChain) -> bool:
        """Determine if an attack chain should be marked as complete"""
        now = datetime.now()
        
        # Complete if no activity for correlation window
        last_event_time = max(event.timestamp for event in chain.events)
        if (now - last_event_time) > self.correlation_window:
            return True
        
        # Complete if impact phase detected
        if AttackPhase.IMPACT in chain.phases_detected:
            return True
        
        # Complete if multiple success indicators
        if len(chain.success_indicators) >= 3:
            return True
        
        return False
    
    async def _complete_chain(self, chain: AttackChain):
        """Mark attack chain as complete and move to completed chains"""
        chain.end_time = datetime.now()
        
        # Remove from active chains
        if chain.chain_id in self.active_chains:
            del self.active_chains[chain.chain_id]
        
        # Add to completed chains
        self.completed_chains.append(chain)
        
        logger.info(f"✅ Completed attack chain: {chain.chain_id}")
        logger.info(f"   Events: {len(chain.events)}")
        logger.info(f"   Phases: {[p.value for p in chain.phases_detected]}")
        logger.info(f"   Techniques: {chain.techniques_used}")
        logger.info(f"   Success Indicators: {chain.success_indicators}")
        logger.info(f"   Training Value: {chain.training_value:.2f}")
    
    async def _cleanup_old_chains(self):
        """Clean up chains that have timed out"""
        now = datetime.now()
        to_remove = []
        
        for chain_id, chain in self.active_chains.items():
            last_event_time = max(event.timestamp for event in chain.events) if chain.events else chain.start_time
            if (now - last_event_time) > self.chain_timeout:
                to_remove.append(chain_id)
        
        for chain_id in to_remove:
            chain = self.active_chains[chain_id]
            await self._complete_chain(chain)
    
    def get_completed_chains(self, min_training_value: float = 0.3) -> List[AttackChain]:
        """Get completed chains suitable for training"""
        return [chain for chain in self.completed_chains 
                if chain.training_value >= min_training_value]
    
    def get_chain_statistics(self) -> Dict[str, Any]:
        """Get statistics about analyzed attack chains"""
        completed = self.completed_chains
        
        if not completed:
            return {"message": "No completed attack chains"}
        
        techniques_count = {}
        phases_count = {}
        
        for chain in completed:
            for technique in chain.techniques_used:
                techniques_count[technique] = techniques_count.get(technique, 0) + 1
            for phase in chain.phases_detected:
                phases_count[phase.value] = phases_count.get(phase.value, 0) + 1
        
        return {
            "total_chains": len(completed),
            "total_events": sum(len(chain.events) for chain in completed),
            "average_training_value": sum(chain.training_value for chain in completed) / len(completed),
            "most_common_techniques": sorted(techniques_count.items(), key=lambda x: x[1], reverse=True)[:10],
            "attack_phases_observed": sorted(phases_count.items(), key=lambda x: x[1], reverse=True),
            "high_value_chains": len([c for c in completed if c.training_value > 0.7])
        }

# Global attack chain analyzer
attack_chain_analyzer = AttackChainAnalyzer()