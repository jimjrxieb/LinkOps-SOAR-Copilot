"""
Detection schemas for Whis SOAR system
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional
from datetime import datetime


@dataclass
class Detection:
    """Security detection/event"""
    id: str
    event_type: str
    source_system: str
    severity: str
    raw_data: Dict[str, Any]
    event_id: Optional[str] = None
    timestamp: Optional[datetime] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


@dataclass
class EnrichmentResult:
    """Result of detection enrichment"""
    detection_id: str
    enrichment_data: Dict[str, Any]
    source: str
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()