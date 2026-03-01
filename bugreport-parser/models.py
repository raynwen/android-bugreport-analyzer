from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime


@dataclass
class TargetApp:
    package_name: str
    uids: List[int] = field(default_factory=list)


@dataclass
class ExtractionStatsDetail:
    total_files_processed: int
    total_lines_scanned: int
    processing_time: str
    memory_peak: str


@dataclass
class SamplingInfo:
    applied: bool
    trigger_reason: str = ""
    original_size: str = ""
    sampled_size: str = ""
    compression_ratio: int = 0
    stats: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DeduplicationInfo:
    original_count: int
    deduplicated_count: int
    dedup_stats: Dict[str, int] = field(default_factory=dict)


@dataclass
class TimeRange:
    start: str
    end: str


@dataclass
class ContextInfo:
    type: str
    event_id: str
    time_window: TimeRange
    related_entries: int
    processes: List[int]
    detail_uri: Optional[str] = None


@dataclass
class CrashInfo:
    type: str
    timestamp: str
    reason: str
    pid: int
    occurrence_count: int
    context_id: str
    stack_summary: 'StackSummary'


@dataclass
class StackSummary:
    top_frames: List[str]
    total_frames: int
    uri: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "top_frames": self.top_frames,
            "total_frames": self.total_frames,
            "stack_uri": self.uri
        }


@dataclass
class ErrorInfo:
    level: str
    tag: str
    message_summary: str
    timestamp: str
    occurrence_count: int
    detail_uri: Optional[str] = None


@dataclass
class PerformanceIssue:
    type: str
    summary: str
    impact: str
    detail_uri: Optional[str] = None


@dataclass
class AggregatedPattern:
    pattern: str
    count: int
    first_occurrence: str
    last_occurrence: str
    sample_summary: str
    samples_uri: Optional[str] = None


@dataclass
class ResourceIndex:
    base_path: str
    files: Dict[str, str] = field(default_factory=dict)


@dataclass
class FreezeEvent:
    id: str
    timestamp: str
    type: str
    package_name: str
    uid: int
    pid: int
    mechanism: str
    reason: str
    duration_seconds: int = 0
    related_crash_id: Optional[str] = None
    related_anr_id: Optional[str] = None
    detail_uri: Optional[str] = None


@dataclass
class MarsInfo:
    current_frozen_packages: List[str] = field(default_factory=list)
    history_count: int = 0
    restriction_policies: List[str] = field(default_factory=list)
    detail_uri: Optional[str] = None


@dataclass
class FreecessInfo:
    frozen_processes: List[int] = field(default_factory=list)
    detail_uri: Optional[str] = None


@dataclass
class AnomalySummary:
    total_freezes: int = 0
    total_unfreezes: int = 0
    frozen_crashes: int = 0
    frozen_anrs: int = 0
    freeze_timeouts: int = 0
    suspicious_packages: List[str] = field(default_factory=list)


@dataclass
class FreezeAnalysis:
    analysis_mode: str = "correlated"
    freeze_events: List[FreezeEvent] = field(default_factory=list)
    mars_info: Optional[MarsInfo] = None
    freecess_info: Optional[FreecessInfo] = None
    anomaly_summary: Optional[AnomalySummary] = None


@dataclass
class ExtractedInfo:
    version: str = "1.0"
    extracted_at: str = field(default_factory=lambda: datetime.now().isoformat())
    target_app: Optional[TargetApp] = None
    extraction_stats: Optional[ExtractionStatsDetail] = None
    sampling: Optional[SamplingInfo] = None
    deduplication: Optional[DeduplicationInfo] = None
    summary: Dict[str, Any] = field(default_factory=dict)
    contexts: List[ContextInfo] = field(default_factory=list)
    crashes: List[CrashInfo] = field(default_factory=list)
    errors: List[ErrorInfo] = field(default_factory=list)
    warnings: List[ErrorInfo] = field(default_factory=list)
    performance_issues: List[PerformanceIssue] = field(default_factory=list)
    aggregated_patterns: List[AggregatedPattern] = field(default_factory=list)
    resource_index: Optional[ResourceIndex] = None
    freeze_analysis: Optional[FreezeAnalysis] = None
