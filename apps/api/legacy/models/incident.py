"""
Incident models for Whis SOAR system
"""

from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, Optional
from datetime import datetime


class IncidentSeverity(Enum):
    """Incident severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Incident:
    """Incident data structure"""
    id: str
    title: str
    description: str
    severity: IncidentSeverity
    status: str
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any]
    assignee: Optional[str] = None
    tags: list = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []