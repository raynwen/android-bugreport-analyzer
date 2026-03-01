from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime


@dataclass
class FreezeInfo:
    freeze_event_id: str
    freeze_mechanism: str
    freeze_reason: str
    time_from_freeze_to_crash_seconds: float = 0.0


@dataclass
class PossibleCause:
    rank: int
    priority_score: float
    type: str
    description: str
    location: str
    stack_trace: Optional[str] = None
    evidence: List[str] = field(default_factory=list)
    confidence: float = 0.0
    severity: str = "MEDIUM"
    frequency: str = "SOMETIMES"
    fix_complexity: str = "MODERATE"


@dataclass
class TimelineEvent:
    time: str
    event: str


@dataclass
class Impact:
    user_visible: bool
    affected_users: str
    frequency: str


@dataclass
class Suggestion:
    priority: int
    action: str
    target_cause_rank: int
    code_example: Optional[str] = None


@dataclass
class Issue:
    id: str
    type: str
    severity: str
    confidence: float
    title: str
    description: str
    possible_causes: List[PossibleCause] = field(default_factory=list)
    primary_cause: Optional[PossibleCause] = None
    timeline: List[TimelineEvent] = field(default_factory=list)
    impact: Optional[Impact] = None
    suggestions: List[Suggestion] = field(default_factory=list)
    freeze_info: Optional[FreezeInfo] = None


@dataclass
class AnalysisReport:
    version: str = "1.0"
    analyzed_at: str = field(default_factory=lambda: datetime.now().isoformat())
    issues: List[Issue] = field(default_factory=list)
    needs_deeper_analysis: bool = False
    additional_files_needed: List[str] = field(default_factory=list)
