#!/usr/bin/env python3
"""
🔄 Universal Event Normalizer for WHIS SOAR-Copilot
Converts Splunk/LimaCharlie events to unified internal schema
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class NormalizedEvent:
    """
    Universal event schema for WHIS processing
    
    This schema provides a common format for all event sources
    (Splunk alerts, LimaCharlie detections, direct API calls)
    """
    # Core identification
    event_id: str
    source_system: str  # "splunk", "limacharlie", "api"
    event_type: str     # Alert type or detection category
    timestamp: str      # ISO format
    
    # Host/Asset information
    host: str
    user: str
    sensor_id: Optional[str] = None
    
    # Process information
    process: str = ""
    command: str = ""
    parent_process: str = ""
    pid: str = ""
    parent_pid: str = ""
    
    # Network information
    src_ip: str = ""
    dest_ip: str = ""
    src_port: str = ""
    dest_port: str = ""
    protocol: str = ""
    
    # File information
    file_path: str = ""
    file_hash: str = ""
    file_size: str = ""
    
    # Registry information
    registry_key: str = ""
    registry_value: str = ""
    
    # Enrichment metadata
    severity: str = "medium"  # low, medium, high, critical
    confidence: float = 0.7
    tags: List[str] = None
    
    # Raw data (must be after default fields)
    raw_event: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.raw_event is None:
            self.raw_event = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "event_id": self.event_id,
            "source_system": self.source_system,
            "event_type": self.event_type,
            "timestamp": self.timestamp,
            "host": self.host,
            "user": self.user,
            "sensor_id": self.sensor_id,
            "process": self.process,
            "command": self.command,
            "parent_process": self.parent_process,
            "pid": self.pid,
            "parent_pid": self.parent_pid,
            "src_ip": self.src_ip,
            "dest_ip": self.dest_ip,
            "src_port": self.src_port,
            "dest_port": self.dest_port,
            "protocol": self.protocol,
            "file_path": self.file_path,
            "file_hash": self.file_hash,
            "file_size": self.file_size,
            "registry_key": self.registry_key,
            "registry_value": self.registry_value,
            "severity": self.severity,
            "confidence": self.confidence,
            "tags": self.tags,
            "raw_event": self.raw_event
        }

class EventNormalizer:
    """Normalizes events from different sources to unified schema"""
    
    def normalize_splunk_alert(self, alert_data: Dict[str, Any]) -> NormalizedEvent:
        """
        Normalize Splunk alert to unified event schema
        
        Expected Splunk webhook format:
        {
            "search_name": "Alert Name",
            "sid": "search_id",
            "result": {...} or "results": [...]
        }
        """
        try:
            # Extract basic info
            search_name = alert_data.get("search_name", "Unknown Splunk Alert")
            sid = alert_data.get("sid", "unknown")
            
            # Get result data
            result = alert_data.get("result", {})
            if not result and "results" in alert_data:
                results = alert_data.get("results", [])
                result = results[0] if results else {}
            
            # Generate event ID
            event_id = f"splunk_{sid}_{int(datetime.now().timestamp())}"
            
            # Map common Splunk fields
            normalized = NormalizedEvent(
                event_id=event_id,
                source_system="splunk",
                event_type=search_name,
                timestamp=result.get("_time", datetime.now().isoformat()),
                host=result.get("host", result.get("dest", result.get("Computer", "unknown"))),
                user=result.get("user", result.get("src_user", result.get("User", "unknown"))),
                
                # Process fields
                process=result.get("process", result.get("process_name", result.get("Image", ""))),
                command=result.get("CommandLine", result.get("command", "")),
                parent_process=result.get("parent_process", result.get("ParentImage", "")),
                pid=str(result.get("process_id", result.get("ProcessId", ""))),
                parent_pid=str(result.get("parent_process_id", result.get("ParentProcessId", ""))),
                
                # Network fields
                src_ip=result.get("src", result.get("src_ip", result.get("SourceIp", ""))),
                dest_ip=result.get("dest", result.get("dest_ip", result.get("DestinationIp", ""))),
                src_port=str(result.get("src_port", result.get("SourcePort", ""))),
                dest_port=str(result.get("dest_port", result.get("DestinationPort", ""))),
                
                # File fields
                file_path=result.get("file_name", result.get("file_path", result.get("TargetFilename", ""))),
                file_hash=result.get("hash", result.get("Hashes", "")),
                
                # Registry fields
                registry_key=result.get("TargetObject", ""),
                registry_value=result.get("Details", ""),
                
                # Metadata
                severity=self._map_splunk_severity(result.get("urgency", "medium")),
                confidence=0.8,
                tags=self._extract_splunk_tags(result),
                raw_event=alert_data
            )
            
            logger.info(f"Normalized Splunk alert: {search_name} -> {event_id}")
            return normalized
            
        except Exception as e:
            logger.error(f"Failed to normalize Splunk alert: {e}")
            # Return minimal normalized event
            return NormalizedEvent(
                event_id=f"splunk_error_{int(datetime.now().timestamp())}",
                source_system="splunk",
                event_type="Splunk Alert (Parse Error)",
                timestamp=datetime.now().isoformat(),
                host="unknown",
                user="unknown",
                raw_event=alert_data,
                severity="medium",
                confidence=0.5
            )
    
    def normalize_limacharlie_detection(self, detection_data: Dict[str, Any]) -> NormalizedEvent:
        """
        Normalize LimaCharlie detection to unified event schema
        
        Expected LC webhook format:
        {
            "detect": {
                "event_id": "...",
                "event_type": "...",
                "event": {...},
                "routing": {...}
            }
        }
        """
        try:
            detect_info = detection_data.get("detect", {})
            event_info = detect_info.get("event", {})
            routing_info = detect_info.get("routing", {})
            
            # Generate event ID
            lc_event_id = detect_info.get("event_id", "unknown")
            event_id = f"lc_{lc_event_id}_{int(datetime.now().timestamp())}"
            
            # Extract process info
            process_path = event_info.get("file_path", event_info.get("IMAGE", ""))
            command_line = event_info.get("command_line", event_info.get("COMMAND_LINE", ""))
            
            # Extract parent info
            parent_info = event_info.get("parent", {})
            parent_path = parent_info.get("file_path", parent_info.get("PARENT_IMAGE", ""))
            
            # Extract network info
            network_info = event_info.get("network", {})
            src_info = network_info.get("source", event_info.get("SOURCE", {}))
            dest_info = network_info.get("destination", event_info.get("DESTINATION", {}))
            
            normalized = NormalizedEvent(
                event_id=event_id,
                source_system="limacharlie",
                event_type=detect_info.get("event_type", "LC_DETECTION"),
                timestamp=detection_data.get("timestamp", datetime.now().isoformat()),
                host=routing_info.get("hostname", routing_info.get("sid", "unknown")),
                user=event_info.get("user_name", event_info.get("USER", "unknown")),
                sensor_id=routing_info.get("sensor_id", routing_info.get("sid", "")),
                
                # Process fields
                process=process_path,
                command=command_line,
                parent_process=parent_path,
                pid=str(event_info.get("process_id", event_info.get("PROCESS_ID", ""))),
                parent_pid=str(parent_info.get("process_id", parent_info.get("PARENT_PROCESS_ID", ""))),
                
                # Network fields  
                src_ip=src_info.get("ip", "") if isinstance(src_info, dict) else str(src_info),
                dest_ip=dest_info.get("ip", "") if isinstance(dest_info, dict) else str(dest_info),
                src_port=str(src_info.get("port", "")) if isinstance(src_info, dict) else "",
                dest_port=str(dest_info.get("port", "")) if isinstance(dest_info, dict) else "",
                
                # File fields
                file_path=event_info.get("file_path", event_info.get("FILE_PATH", "")),
                file_hash=event_info.get("hash", event_info.get("HASH", "")),
                file_size=str(event_info.get("file_size", "")),
                
                # Registry fields
                registry_key=event_info.get("reg_key_path", ""),
                registry_value=event_info.get("reg_value_name", ""),
                
                # Metadata
                severity=self._map_lc_severity(detect_info.get("severity", 3)),
                confidence=0.85,
                tags=self._extract_lc_tags(detect_info),
                raw_event=detection_data
            )
            
            logger.info(f"Normalized LC detection: {detect_info.get('event_type')} -> {event_id}")
            return normalized
            
        except Exception as e:
            logger.error(f"Failed to normalize LC detection: {e}")
            # Return minimal normalized event
            return NormalizedEvent(
                event_id=f"lc_error_{int(datetime.now().timestamp())}",
                source_system="limacharlie", 
                event_type="LC Detection (Parse Error)",
                timestamp=datetime.now().isoformat(),
                host="unknown",
                user="unknown",
                raw_event=detection_data,
                severity="medium",
                confidence=0.5
            )
    
    def normalize_api_event(self, event_data: Dict[str, Any]) -> NormalizedEvent:
        """
        Normalize direct API call to unified event schema
        
        For events submitted directly to /explain endpoint
        """
        try:
            event_id = f"api_{int(datetime.now().timestamp())}"
            
            normalized = NormalizedEvent(
                event_id=event_id,
                source_system="api",
                event_type=event_data.get("search_name", event_data.get("event_type", "Direct API Event")),
                timestamp=event_data.get("timestamp", datetime.now().isoformat()),
                host=event_data.get("host", "unknown"),
                user=event_data.get("user", "unknown"),
                
                # Optional fields
                process=event_data.get("process", ""),
                command=event_data.get("command", event_data.get("CommandLine", "")),
                src_ip=event_data.get("src_ip", event_data.get("source_ip", "")),
                dest_ip=event_data.get("dest_ip", event_data.get("destination_ip", "")),
                file_path=event_data.get("file", event_data.get("file_path", "")),
                
                # Metadata
                severity=event_data.get("severity", "medium"),
                confidence=0.7,
                tags=event_data.get("tags", []),
                raw_event=event_data
            )
            
            logger.info(f"Normalized API event: {normalized.event_type} -> {event_id}")
            return normalized
            
        except Exception as e:
            logger.error(f"Failed to normalize API event: {e}")
            # Return minimal normalized event
            return NormalizedEvent(
                event_id=f"api_error_{int(datetime.now().timestamp())}",
                source_system="api",
                event_type="API Event (Parse Error)", 
                timestamp=datetime.now().isoformat(),
                host="unknown",
                user="unknown",
                raw_event=event_data,
                severity="low",
                confidence=0.3
            )
    
    def _map_splunk_severity(self, urgency: str) -> str:
        """Map Splunk urgency to standard severity"""
        urgency_map = {
            "informational": "low",
            "low": "low", 
            "medium": "medium",
            "high": "high",
            "critical": "critical"
        }
        return urgency_map.get(str(urgency).lower(), "medium")
    
    def _map_lc_severity(self, lc_severity: int) -> str:
        """Map LimaCharlie severity to standard severity"""
        severity_map = {
            1: "low",
            2: "low",
            3: "medium", 
            4: "high",
            5: "critical"
        }
        return severity_map.get(lc_severity, "medium")
    
    def _extract_splunk_tags(self, result: Dict[str, Any]) -> List[str]:
        """Extract relevant tags from Splunk result"""
        tags = []
        
        # Add source type as tag
        if "sourcetype" in result:
            tags.append(f"sourcetype:{result['sourcetype']}")
        
        # Add index as tag
        if "index" in result:
            tags.append(f"index:{result['index']}")
            
        # Add technique if present
        if "technique" in result:
            tags.append(f"mitre:{result['technique']}")
            
        return tags
    
    def _extract_lc_tags(self, detect_info: Dict[str, Any]) -> List[str]:
        """Extract relevant tags from LC detection"""
        tags = []
        
        # Add event type as tag
        if "event_type" in detect_info:
            tags.append(f"lc_event:{detect_info['event_type']}")
        
        # Add severity as tag
        if "severity" in detect_info:
            tags.append(f"severity:{detect_info['severity']}")
            
        # Add routing tags if present
        routing = detect_info.get("routing", {})
        if "tag" in routing:
            tags.append(f"lc_tag:{routing['tag']}")
            
        return tags

# Global normalizer instance
event_normalizer = EventNormalizer()