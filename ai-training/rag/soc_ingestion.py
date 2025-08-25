#!/usr/bin/env python3
"""
🚨 Event-Driven SOC Ingestion
=============================
Converts Splunk/LimaCharlie HIGH/CRITICAL events into curated summaries.
NO raw logs - only derived knowledge (playbook-quality narratives).

Senior-level SOC integration:
- Event-driven webhooks/queues
- Detection/Incident summary normalization
- ATT&CK technique mapping
- Triage playbook generation
- Severity-based filtering
- Real-time sanitization
"""

import os
import json
import re
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from urllib.parse import urlencode
import requests

# Add parent directories
import sys
sys.path.append(str(Path(__file__).parent.parent))

from rag.hybrid_retrieval import HybridRetriever


@dataclass
class DetectionSummary:
    """Normalized detection/incident summary"""
    detection_id: str
    title: str
    severity: str  # HIGH, CRITICAL
    timestamp: datetime
    source_system: str  # splunk, limacharlie
    
    # What happened
    description: str
    evidence_summary: str
    affected_systems: List[str]
    user_accounts: List[str]
    
    # ATT&CK mapping
    mitre_techniques: List[str]
    mitre_tactics: List[str]
    
    # Response info
    triage_steps: List[str]
    remediation_actions: List[str]
    playbook_reference: Optional[str]
    
    # Investigation
    search_queries: List[str]  # Sanitized search examples
    source_urls: List[str]     # Links back to Splunk/LC
    
    # Metadata
    analyst_notes: Optional[str]
    incident_status: str  # open, investigating, resolved
    assigned_to: Optional[str]
    
    def to_indexable_content(self) -> str:
        """Convert to searchable RAG content"""
        content_parts = [
            f"DETECTION: {self.title}",
            f"Severity: {self.severity} | System: {self.source_system}",
            f"Time: {self.timestamp.strftime('%Y-%m-%d %H:%M UTC')}",
            "",
            "DESCRIPTION:",
            self.description,
            "",
            "EVIDENCE:",
            self.evidence_summary,
            ""
        ]
        
        if self.affected_systems:
            content_parts.extend([
                "AFFECTED SYSTEMS:",
                ", ".join(self.affected_systems),
                ""
            ])
            
        if self.mitre_techniques:
            content_parts.extend([
                "MITRE ATT&CK TECHNIQUES:",
                ", ".join(self.mitre_techniques),
                ""
            ])
            
        if self.triage_steps:
            content_parts.extend([
                "TRIAGE STEPS:",
                *[f"{i+1}. {step}" for i, step in enumerate(self.triage_steps)],
                ""
            ])
            
        if self.remediation_actions:
            content_parts.extend([
                "REMEDIATION:",
                *[f"- {action}" for action in self.remediation_actions],
                ""
            ])
            
        if self.search_queries:
            content_parts.extend([
                "INVESTIGATION QUERIES:",
                *[f"- {query}" for query in self.search_queries[:3]],  # Limit to 3
                ""
            ])
            
        return "\n".join(content_parts)


class SOCIngestionPipeline:
    """Event-driven SOC ingestion with real-time summarization"""
    
    def __init__(self, config_path: str = "ai-training/configs/soc_ingestion.yaml"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        
        # Initialize components
        self.retriever = HybridRetriever()
        
        # State tracking
        self.state_file = Path("ai-training/rag/.soc_state.json")
        self.state = self._load_state()
        
        # ATT&CK mapping
        self.attack_mapping = self._load_attack_mapping()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load SOC ingestion configuration"""
        if not self.config_path.exists():
            default_config = {
                "triggers": {
                    "splunk": {
                        "enabled": True,
                        "webhook_endpoint": "/webhooks/splunk",
                        "severity_threshold": ["HIGH", "CRITICAL"],
                        "notable_types": ["alert", "incident"],
                        "auth_token": "${SPLUNK_WEBHOOK_TOKEN}"
                    },
                    "limacharlie": {
                        "enabled": True, 
                        "webhook_endpoint": "/webhooks/limacharlie",
                        "severity_threshold": ["high", "critical"],
                        "detection_types": ["sigma", "yara", "custom"],
                        "auth_token": "${LC_WEBHOOK_TOKEN}"
                    }
                },
                "processing": {
                    "max_description_length": 2000,
                    "max_evidence_items": 10,
                    "auto_assign_techniques": True,
                    "generate_triage_steps": True,
                    "include_search_queries": True,
                    "sanitize_queries": True
                },
                "filtering": {
                    "dedupe_window_minutes": 15,
                    "min_severity_score": 7.0,
                    "blacklist_patterns": [
                        "test alert", "maintenance", "benign", "false positive"
                    ],
                    "required_fields": ["title", "description", "severity"]
                },
                "enrichment": {
                    "mitre_mapping_enabled": True,
                    "playbook_lookup_enabled": True,
                    "threat_intel_enabled": False,  # Would integrate with TIP
                    "asset_context_enabled": True
                },
                "sanitization": {
                    "strip_credentials": True,
                    "strip_pii": True,
                    "strip_internal_ips": True,
                    "neutralize_instructions": True,
                    "max_query_length": 500
                },
                "indexing": {
                    "collection_name": "whis_soc_detections",
                    "chunk_overlap": 50,
                    "batch_size": 10,
                    "ttl_days": 90  # Expire old detections
                },
                "evaluation": {
                    "daily_eval_enabled": True,
                    "eval_queries": [
                        "Show me recent critical alerts",
                        "What lateral movement techniques were detected?",
                        "What are the current triage steps for ransomware?",
                        "How do I investigate privilege escalation?"
                    ],
                    "faithfulness_threshold": 0.75,
                    "citation_coverage_threshold": 0.95
                }
            }
            
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            import yaml
            with open(self.config_path, 'w') as f:
                yaml.dump(default_config, f, indent=2)
                
            return default_config
            
        import yaml
        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)
            
    def _load_state(self) -> Dict[str, Any]:
        """Load SOC ingestion state"""
        if self.state_file.exists():
            with open(self.state_file, 'r') as f:
                return json.load(f)
        else:
            return {
                "processed_detections": {},  # detection_id -> timestamp
                "ingestion_stats": {
                    "total_processed": 0,
                    "total_filtered": 0,
                    "total_duplicates": 0,
                    "by_severity": {"HIGH": 0, "CRITICAL": 0}
                },
                "last_eval": "",
                "eval_history": []
            }
            
    def _save_state(self):
        """Save SOC ingestion state"""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2, default=str)
            
    def _load_attack_mapping(self) -> Dict[str, List[str]]:
        """Load MITRE ATT&CK technique mapping"""
        # Simplified mapping - in practice would load from MITRE CTI
        return {
            "lateral movement": ["T1021", "T1047", "T1563", "T1210"],
            "privilege escalation": ["T1548", "T1134", "T1055", "T1574"],
            "credential access": ["T1003", "T1558", "T1110", "T1212"],
            "persistence": ["T1053", "T1547", "T1543", "T1136"],
            "defense evasion": ["T1055", "T1027", "T1036", "T1218"],
            "initial access": ["T1566", "T1190", "T1078", "T1133"],
            "execution": ["T1059", "T1053", "T1204", "T1569"],
            "collection": ["T1560", "T1005", "T1039", "T1115"],
            "exfiltration": ["T1041", "T1567", "T1052", "T1030"],
            "impact": ["T1486", "T1485", "T1529", "T1490"],
            "reconnaissance": ["T1595", "T1590", "T1589", "T1596"],
            "resource development": ["T1583", "T1588", "T1584", "T1586"]
        }
        
    def normalize_splunk_detection(self, splunk_data: Dict[str, Any]) -> Optional[DetectionSummary]:
        """Normalize Splunk notable event to DetectionSummary"""
        print(f"🔄 Normalizing Splunk detection: {splunk_data.get('search_name', 'unknown')}")
        
        try:
            # Extract basic info
            detection_id = splunk_data.get("search_name", "") + "_" + str(splunk_data.get("_time", ""))
            detection_id = hashlib.sha256(detection_id.encode()).hexdigest()[:16]
            
            title = splunk_data.get("search_name", "Untitled Detection")
            severity = splunk_data.get("urgency", "MEDIUM").upper()
            
            # Parse timestamp
            timestamp_str = splunk_data.get("_time", "")
            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            except:
                timestamp = datetime.now()
                
            # Extract description
            description = splunk_data.get("description", "")
            if not description:
                description = f"Detection triggered: {title}"
                
            # Extract evidence
            evidence_fields = ["src", "dest", "user", "process_name", "file_name", "command"]
            evidence_parts = []
            
            for field in evidence_fields:
                if field in splunk_data and splunk_data[field]:
                    evidence_parts.append(f"{field}: {splunk_data[field]}")
                    
            evidence_summary = "; ".join(evidence_parts[:self.config["processing"]["max_evidence_items"]])
            
            # Extract affected systems
            affected_systems = []
            for field in ["src", "dest", "host"]:
                if field in splunk_data and splunk_data[field]:
                    affected_systems.append(str(splunk_data[field]))
                    
            # Extract user accounts
            user_accounts = []
            for field in ["user", "src_user", "dest_user"]:
                if field in splunk_data and splunk_data[field]:
                    user_accounts.append(str(splunk_data[field]))
                    
            # Map MITRE techniques
            mitre_techniques, mitre_tactics = self._map_mitre_techniques(title, description)
            
            # Generate triage steps
            triage_steps = self._generate_triage_steps(title, severity, mitre_tactics)
            
            # Generate remediation actions
            remediation_actions = self._generate_remediation_actions(mitre_techniques)
            
            # Create search queries (sanitized)
            search_queries = self._generate_search_queries(splunk_data, sanitize=True)
            
            # Create source URLs
            source_urls = []
            if "sid" in splunk_data:
                source_urls.append(f"splunk://search/{splunk_data['sid']}")
                
            detection_summary = DetectionSummary(
                detection_id=detection_id,
                title=title,
                severity=severity,
                timestamp=timestamp,
                source_system="splunk",
                description=description[:self.config["processing"]["max_description_length"]],
                evidence_summary=evidence_summary,
                affected_systems=list(set(affected_systems))[:10],
                user_accounts=list(set(user_accounts))[:10],
                mitre_techniques=mitre_techniques,
                mitre_tactics=mitre_tactics,
                triage_steps=triage_steps,
                remediation_actions=remediation_actions,
                playbook_reference=self._lookup_playbook(mitre_techniques),
                search_queries=search_queries,
                source_urls=source_urls,
                analyst_notes=splunk_data.get("comment", ""),
                incident_status=splunk_data.get("status", "open"),
                assigned_to=splunk_data.get("owner", None)
            )
            
            return detection_summary
            
        except Exception as e:
            print(f"❌ Failed to normalize Splunk detection: {e}")
            return None
            
    def normalize_limacharlie_detection(self, lc_data: Dict[str, Any]) -> Optional[DetectionSummary]:
        """Normalize LimaCharlie detection to DetectionSummary"""
        print(f"🔄 Normalizing LimaCharlie detection: {lc_data.get('detect', {}).get('name', 'unknown')}")
        
        try:
            detect_info = lc_data.get("detect", {})
            
            detection_id = f"lc_{lc_data.get('oid', '')}_{detect_info.get('id', '')}"
            detection_id = hashlib.sha256(detection_id.encode()).hexdigest()[:16]
            
            title = detect_info.get("name", "Untitled LimaCharlie Detection")
            severity = detect_info.get("severity", 5)
            
            # Map LC severity to standard
            if severity >= 8:
                severity_str = "CRITICAL"
            elif severity >= 6:
                severity_str = "HIGH"
            else:
                severity_str = "MEDIUM"
                
            # Parse timestamp
            timestamp_ms = lc_data.get("ts", 0)
            timestamp = datetime.fromtimestamp(timestamp_ms / 1000) if timestamp_ms else datetime.now()
            
            # Extract description
            description = detect_info.get("summary", "")
            if not description:
                description = f"LimaCharlie detection: {title}"
                
            # Extract evidence from event
            event_data = lc_data.get("event", {})
            evidence_parts = []
            
            for field in ["FILE_PATH", "COMMAND_LINE", "PROCESS_ID", "USER_NAME"]:
                if field in event_data:
                    evidence_parts.append(f"{field.lower()}: {event_data[field]}")
                    
            evidence_summary = "; ".join(evidence_parts[:self.config["processing"]["max_evidence_items"]])
            
            # Extract affected systems
            routing = lc_data.get("routing", {})
            affected_systems = [routing.get("hostname", "")] if routing.get("hostname") else []
            
            # Extract user accounts
            user_accounts = []
            if "USER_NAME" in event_data:
                user_accounts.append(event_data["USER_NAME"])
                
            # Map MITRE techniques
            mitre_techniques, mitre_tactics = self._map_mitre_techniques(title, description)
            
            # Use LC's MITRE mapping if available
            if "mitre" in detect_info:
                lc_techniques = detect_info["mitre"].get("technique", [])
                if lc_techniques:
                    mitre_techniques.extend(lc_techniques)
                    mitre_techniques = list(set(mitre_techniques))  # Deduplicate
                    
            triage_steps = self._generate_triage_steps(title, severity_str, mitre_tactics)
            remediation_actions = self._generate_remediation_actions(mitre_techniques)
            
            # Generate search queries (simplified for LC)
            search_queries = [
                f"hostname:{routing.get('hostname', '')} AND detection_name:{title}",
                f"process_name:{event_data.get('FILE_PATH', '').split('/')[-1] if event_data.get('FILE_PATH') else ''}"
            ]
            search_queries = [q for q in search_queries if q.strip() and len(q) > 10]
            
            # Create source URLs
            source_urls = [f"limacharlie://detection/{detection_id}"]
            
            detection_summary = DetectionSummary(
                detection_id=detection_id,
                title=title,
                severity=severity_str,
                timestamp=timestamp,
                source_system="limacharlie",
                description=description[:self.config["processing"]["max_description_length"]],
                evidence_summary=evidence_summary,
                affected_systems=affected_systems,
                user_accounts=user_accounts,
                mitre_techniques=mitre_techniques,
                mitre_tactics=mitre_tactics,
                triage_steps=triage_steps,
                remediation_actions=remediation_actions,
                playbook_reference=self._lookup_playbook(mitre_techniques),
                search_queries=search_queries[:3],  # Limit to 3
                source_urls=source_urls,
                analyst_notes="",
                incident_status="open",
                assigned_to=None
            )
            
            return detection_summary
            
        except Exception as e:
            print(f"❌ Failed to normalize LimaCharlie detection: {e}")
            return None
            
    def _map_mitre_techniques(self, title: str, description: str) -> Tuple[List[str], List[str]]:
        """Map detection to MITRE ATT&CK techniques and tactics"""
        if not self.config["enrichment"]["mitre_mapping_enabled"]:
            return [], []
            
        text = f"{title} {description}".lower()
        
        found_techniques = []
        found_tactics = []
        
        for tactic, techniques in self.attack_mapping.items():
            if tactic in text:
                found_tactics.append(tactic.title().replace(" ", "_"))
                found_techniques.extend(techniques[:2])  # Limit to 2 per tactic
                
        # Additional keyword-based mapping
        keyword_mappings = {
            "powershell": ["T1059.001"],
            "wmi": ["T1047"],
            "psexec": ["T1021.002"],
            "mimikatz": ["T1003.001"],
            "ransomware": ["T1486"],
            "backdoor": ["T1543.003"],
            "persistence": ["T1547.001"]
        }
        
        for keyword, techniques in keyword_mappings.items():
            if keyword in text:
                found_techniques.extend(techniques)
                
        return list(set(found_techniques))[:5], list(set(found_tactics))[:3]
        
    def _generate_triage_steps(self, title: str, severity: str, tactics: List[str]) -> List[str]:
        """Generate context-aware triage steps"""
        if not self.config["processing"]["generate_triage_steps"]:
            return []
            
        base_steps = [
            "Review detection details and evidence",
            "Check affected systems for additional indicators",
            "Validate detection accuracy and reduce false positives"
        ]
        
        # Add severity-specific steps
        if severity == "CRITICAL":
            base_steps.insert(1, "Immediately isolate affected systems if confirmed")
            base_steps.append("Escalate to incident response team")
            
        # Add tactic-specific steps
        tactic_steps = {
            "Lateral_Movement": "Check network logs for additional movement",
            "Privilege_Escalation": "Review user accounts for elevation activity",
            "Credential_Access": "Force password resets for affected accounts",
            "Persistence": "Check for scheduled tasks and startup modifications"
        }
        
        for tactic in tactics:
            if tactic in tactic_steps:
                base_steps.append(tactic_steps[tactic])
                
        return base_steps[:8]  # Limit to 8 steps
        
    def _generate_remediation_actions(self, techniques: List[str]) -> List[str]:
        """Generate technique-specific remediation actions"""
        actions = []
        
        # Technique-specific remediations
        remediation_map = {
            "T1003": "Reset compromised account passwords",
            "T1047": "Restrict WMI access and monitor usage",
            "T1021": "Review and restrict remote access protocols", 
            "T1059": "Implement PowerShell logging and restrictions",
            "T1486": "Isolate systems and activate backup recovery",
            "T1543": "Remove malicious services and persistence"
        }
        
        for technique in techniques:
            # Match technique prefix (e.g., T1003.001 -> T1003)
            technique_prefix = technique.split('.')[0]
            if technique_prefix in remediation_map:
                actions.append(remediation_map[technique_prefix])
                
        # Default actions if none found
        if not actions:
            actions = [
                "Monitor affected systems for additional activity",
                "Review and strengthen relevant security controls"
            ]
            
        return list(set(actions))[:5]  # Limit to 5, deduplicate
        
    def _lookup_playbook(self, techniques: List[str]) -> Optional[str]:
        """Lookup relevant playbook for techniques"""
        if not self.config["enrichment"]["playbook_lookup_enabled"]:
            return None
            
        # Simplified playbook mapping
        playbook_map = {
            "T1003": "credential_access_playbook",
            "T1021": "lateral_movement_playbook", 
            "T1486": "ransomware_response_playbook",
            "T1059": "powershell_empire_playbook"
        }
        
        for technique in techniques:
            technique_prefix = technique.split('.')[0]
            if technique_prefix in playbook_map:
                return playbook_map[technique_prefix]
                
        return None
        
    def _generate_search_queries(self, detection_data: Dict[str, Any], sanitize: bool = True) -> List[str]:
        """Generate investigation search queries"""
        if not self.config["processing"]["include_search_queries"]:
            return []
            
        queries = []
        
        # Basic host-based query
        if "src" in detection_data:
            queries.append(f'host="{detection_data["src"]}" earliest=-24h@h')
            
        # User-based query
        if "user" in detection_data:
            queries.append(f'user="{detection_data["user"]}" earliest=-24h@h')
            
        # Process-based query
        if "process_name" in detection_data:
            queries.append(f'process_name="{detection_data["process_name"]}" earliest=-4h@h')
            
        if sanitize:
            queries = self._sanitize_queries(queries)
            
        return queries[:3]  # Limit to 3
        
    def _sanitize_queries(self, queries: List[str]) -> List[str]:
        """Sanitize search queries to remove sensitive data"""
        if not self.config["sanitization"]["sanitize_queries"]:
            return queries
            
        sanitized = []
        max_length = self.config["sanitization"]["max_query_length"]
        
        # Patterns to sanitize
        sanitize_patterns = [
            (r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', 'IP_ADDR'),  # IP addresses
            (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', 'EMAIL'),  # Emails
            (r'\b[A-Za-z0-9]{32,}\b', 'TOKEN'),  # Tokens/hashes
            (r'password\s*=\s*[^\s]+', 'password=REDACTED'),  # Passwords
        ]
        
        for query in queries:
            sanitized_query = query
            
            # Apply sanitization patterns
            for pattern, replacement in sanitize_patterns:
                sanitized_query = re.sub(pattern, replacement, sanitized_query, flags=re.IGNORECASE)
                
            # Truncate if too long
            if len(sanitized_query) > max_length:
                sanitized_query = sanitized_query[:max_length] + "..."
                
            # Remove potential command injection
            dangerous_chars = [';', '|', '&', '>', '<', '`', '$']
            for char in dangerous_chars:
                sanitized_query = sanitized_query.replace(char, '')
                
            sanitized.append(sanitized_query)
            
        return sanitized
        
    def should_process_detection(self, detection_summary: DetectionSummary) -> Tuple[bool, str]:
        """Determine if detection should be processed"""
        filtering_config = self.config["filtering"]
        
        # Check severity threshold
        if detection_summary.severity not in ["HIGH", "CRITICAL"]:
            return False, f"severity_below_threshold:{detection_summary.severity}"
            
        # Check for blacklisted patterns
        text_to_check = f"{detection_summary.title} {detection_summary.description}".lower()
        for pattern in filtering_config["blacklist_patterns"]:
            if pattern.lower() in text_to_check:
                return False, f"blacklisted_pattern:{pattern}"
                
        # Check for required fields
        for field in filtering_config["required_fields"]:
            if not getattr(detection_summary, field, "").strip():
                return False, f"missing_required_field:{field}"
                
        # Check for duplicates (simplified)
        recent_window = timedelta(minutes=filtering_config["dedupe_window_minutes"])
        cutoff_time = datetime.now() - recent_window
        
        for det_id, timestamp_str in self.state["processed_detections"].items():
            try:
                timestamp = datetime.fromisoformat(timestamp_str)
                if timestamp > cutoff_time:
                    # Check for near-duplicate title
                    if self._are_titles_similar(detection_summary.title, det_id.split('_')[0]):
                        return False, f"duplicate_detection:{det_id}"
            except:
                continue
                
        return True, "passed"
        
    def _are_titles_similar(self, title1: str, title2: str, threshold: float = 0.8) -> bool:
        """Check if two detection titles are similar (simplified)"""
        # Simple word overlap check
        words1 = set(title1.lower().split())
        words2 = set(title2.lower().split())
        
        if not words1 or not words2:
            return False
            
        overlap = len(words1.intersection(words2))
        similarity = overlap / min(len(words1), len(words2))
        
        return similarity >= threshold
        
    def upsert_detection(self, detection_summary: DetectionSummary) -> Dict[str, Any]:
        """Upsert detection summary to RAG index"""
        print(f"📤 Upserting detection: {detection_summary.detection_id}")
        
        try:
            # Get SOC detections collection
            collection_name = self.config["indexing"]["collection_name"]
            
            # Get or create collection
            try:
                collection = self.retriever.vector_stores["docs"]  # Use docs collection for now
            except KeyError:
                print(f"❌ Collection not found: {collection_name}")
                return {"success": False, "error": "collection_not_found"}
                
            # Convert to indexable content
            content = detection_summary.to_indexable_content()
            
            # Generate embedding
            embeddings = self.retriever.dual_embedder.embed_chunk({
                "content": content,
                "chunk_type": "soc_detection",
                "language": "text"
            })
            
            if "prose" not in embeddings:
                return {"success": False, "error": "embedding_failed"}
                
            # Prepare metadata
            metadata = {
                "detection_id": detection_summary.detection_id,
                "title": detection_summary.title,
                "severity": detection_summary.severity,
                "source_system": detection_summary.source_system,
                "timestamp": detection_summary.timestamp.isoformat(),
                "mitre_techniques": ",".join(detection_summary.mitre_techniques),
                "mitre_tactics": ",".join(detection_summary.mitre_tactics),
                "incident_status": detection_summary.incident_status,
                "chunk_type": "soc_detection",
                "symbol_type": "detection_summary",
                "file_path": f"soc/{detection_summary.source_system}/{detection_summary.detection_id}",
                "symbol_name": detection_summary.title,
                "start_line": 1,
                "end_line": len(content.split('\n')),
                "language": "text",
                "commit_hash": "",
                "module_path": "",
                "last_modified": detection_summary.timestamp.isoformat()
            }
            
            # Upsert to collection
            collection.upsert(
                ids=[detection_summary.detection_id],
                documents=[content],
                embeddings=[embeddings["prose"].tolist()],
                metadatas=[metadata]
            )
            
            # Update state
            self.state["processed_detections"][detection_summary.detection_id] = detection_summary.timestamp.isoformat()
            self.state["ingestion_stats"]["total_processed"] += 1
            self.state["ingestion_stats"]["by_severity"][detection_summary.severity] += 1
            
            self._save_state()
            
            return {
                "success": True,
                "detection_id": detection_summary.detection_id,
                "content_length": len(content),
                "mitre_techniques_count": len(detection_summary.mitre_techniques)
            }
            
        except Exception as e:
            print(f"❌ Failed to upsert detection: {e}")
            return {"success": False, "error": str(e)}
            
    def process_detection_event(self, event_data: Dict[str, Any], source: str) -> Dict[str, Any]:
        """Process incoming detection event"""
        print(f"🚨 Processing {source} detection event")
        
        try:
            # Normalize detection based on source
            if source == "splunk":
                detection_summary = self.normalize_splunk_detection(event_data)
            elif source == "limacharlie":
                detection_summary = self.normalize_limacharlie_detection(event_data)
            else:
                return {"success": False, "error": f"unknown_source:{source}"}
                
            if not detection_summary:
                return {"success": False, "error": "normalization_failed"}
                
            # Check if should process
            should_process, reason = self.should_process_detection(detection_summary)
            
            if not should_process:
                self.state["ingestion_stats"]["total_filtered"] += 1
                self._save_state()
                return {
                    "success": False, 
                    "error": "filtered",
                    "reason": reason,
                    "detection_id": detection_summary.detection_id
                }
                
            # Upsert to index
            upsert_result = self.upsert_detection(detection_summary)
            
            if upsert_result["success"]:
                result = {
                    "success": True,
                    "detection_id": detection_summary.detection_id,
                    "title": detection_summary.title,
                    "severity": detection_summary.severity,
                    "source": source,
                    "mitre_techniques": detection_summary.mitre_techniques,
                    "upsert_result": upsert_result
                }
            else:
                result = {
                    "success": False,
                    "error": "upsert_failed",
                    "detection_id": detection_summary.detection_id,
                    "upsert_error": upsert_result["error"]
                }
                
            print(f"{'✅' if result['success'] else '❌'} Detection processing: {detection_summary.title}")
            return result
            
        except Exception as e:
            print(f"❌ Detection event processing failed: {e}")
            return {"success": False, "error": str(e)}


def main():
    """CLI for SOC ingestion testing"""
    import argparse
    
    parser = argparse.ArgumentParser(description="SOC ingestion pipeline")
    parser.add_argument("--config", default="ai-training/configs/soc_ingestion.yaml")
    parser.add_argument("--test-splunk", help="JSON file with Splunk detection data")
    parser.add_argument("--test-limacharlie", help="JSON file with LimaCharlie detection data")
    parser.add_argument("--source", required=True, choices=["splunk", "limacharlie"])
    
    args = parser.parse_args()
    
    # Initialize pipeline
    pipeline = SOCIngestionPipeline(args.config)
    
    # Load test data
    if args.test_splunk:
        with open(args.test_splunk, 'r') as f:
            event_data = json.load(f)
            source = "splunk"
    elif args.test_limacharlie:
        with open(args.test_limacharlie, 'r') as f:
            event_data = json.load(f)
            source = "limacharlie"
    else:
        print("❌ No test data provided")
        sys.exit(1)
        
    # Process event
    result = pipeline.process_detection_event(event_data, source)
    
    print("\n📊 Processing Result:")
    print(json.dumps(result, indent=2, default=str))
    
    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()