"""
Playbook models for Whis SOAR system
"""

from dataclasses import dataclass
from typing import Dict, Any, List, Optional


@dataclass
class PlaybookAction:
    """Individual playbook action"""
    id: str
    name: str
    description: str
    requires_approval: bool = True
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class Playbook:
    """SOAR playbook definition"""
    id: str
    name: str
    description: str
    technique_mapping: List[str] = None
    actions: List[PlaybookAction] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.technique_mapping is None:
            self.technique_mapping = []
        if self.actions is None:
            self.actions = []
        if self.metadata is None:
            self.metadata = {}