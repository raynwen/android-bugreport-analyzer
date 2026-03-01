import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

from .priority import PriorityCalculator
from .freeze_analyzer import FreezeIssueAnalyzer
from .models import (
    AnalysisReport, Issue, PossibleCause, TimelineEvent,
    Impact, Suggestion, FreezeInfo
)


class BugAnalyzer:

    ISSUE_TYPE_MAPPING = {
        'ANR': {
            'category': 'crash',
            'causes': ['BLOCKING_IO', 'DEADLOCK', 'CPU_OVERLOAD', 'MEMORY_PRESSURE']
        },
        'CRASH': {
            'category': 'crash',
            'causes': ['NPE', 'OOM', 'RESOURCE_LEAK', 'ILLEGAL_STATE']
        },
        'PERFORMANCE': {
            'category': 'performance',
            'causes': ['UI_THREAD_BLOCK', 'EXCESSIVE_GC', 'MEMORY_LEAK', 'NETWORK_LATENCY']
        },
        'FROZEN_CRASH': {
            'category': 'freeze',
            'causes': ['FROZEN_HANDLER', 'FROZEN_BROADCAST', 'FROZEN_JOB']
        },
        'FROZEN_ANR': {
            'category': 'freeze',
            'causes': ['FROZEN_INPUT_DISPATCH', 'FROZEN_SERVICE_BIND']
        },
        'FREEZE_TIMEOUT': {
            'category': 'freeze',
            'causes': ['LONG_RUNNING_OPERATION', 'IO_BLOCKING']
        }
    }

    def __init__(self):
        self.priority_calculator = PriorityCalculator()
        self.freeze_analyzer = FreezeIssueAnalyzer()

    def analyze(self, extracted_info_path: str, output_dir: Optional[str] = None) -> AnalysisReport:
        with open(extracted_info_path, 'r', encoding='utf-8') as f:
            extracted_info = json.load(f)

        if output_dir is None:
            output_dir = Path(extracted_info_path).parent

        issues = self._identify_issues(extracted_info)

        for issue in issues:
            issue.possible_causes = self._analyze_causes(issue, extracted_info)
            issue.possible_causes = PriorityCalculator.rank_causes([
                vars(c) if hasattr(c, '__dict__') else c for c in issue.possible_causes
            ])
            issue.possible_causes = [PossibleCause(**c) if isinstance(c, dict) else c for c in issue.possible_causes]

            if issue.possible_causes:
                issue.primary_cause = issue.possible_causes[0]

            issue.timeline = self._build_timeline(issue, extracted_info)
            issue.impact = self._assess_impact(issue, extracted_info)
            issue.suggestions = self._generate_suggestions(issue)

        freeze_issues = self.freeze_analyzer.analyze_freeze_issues(extracted_info)
        for freeze_issue in freeze_issues:
            issue = self._convert_freeze_issue(freeze_issue)
            issue.possible_causes = PriorityCalculator.rank_causes(freeze_issue.get('possible_causes', []))
            issue.possible_causes = [PossibleCause(**c) if isinstance(c, dict) else c for c in issue.possible_causes]
            if issue.possible_causes:
                issue.primary_cause = issue.possible_causes[0]
            issue.suggestions = [Suggestion(**s) if isinstance(s, dict) else s for s in freeze_issue.get('suggestions', [])]
            issues.append(issue)

        report = AnalysisReport(
            issues=issues,
            needs_deeper_analysis=self._needs_deeper_analysis(issues)
        )

        output_path = Path(output_dir) / "analysis_report.json"
        self._save_report(report, output_path)

        return report

    def _convert_freeze_issue(self, freeze_issue: Dict) -> Issue:
        freeze_info_dict = freeze_issue.get('freeze_info', {})
        freeze_info = FreezeInfo(**freeze_info_dict) if freeze_info_dict else None

        return Issue(
            id=freeze_issue.get('id', ''),
            type=freeze_issue.get('type', 'UNKNOWN'),
            severity=freeze_issue.get('severity', 'MEDIUM'),
            confidence=freeze_issue.get('confidence', 0.5),
            title=freeze_issue.get('title', ''),
            description=freeze_issue.get('description', ''),
            freeze_info=freeze_info
        )

    def _identify_issues(self, extracted_info: Dict) -> List[Issue]:
        issues = []

        for i, crash in enumerate(extracted_info.get('crashes', [])):
            issue = Issue(
                id=f"ISSUE-{i+1:03d}",
                type=crash.get('type', 'UNKNOWN'),
                severity='HIGH',
                confidence=0.9,
                title=f"{crash.get('type', 'Unknown')} detected",
                description=self._build_crash_description(crash)
            )
            issues.append(issue)

        for i, error in enumerate(extracted_info.get('errors', [])[:5]):
            if self._is_significant_error(error):
                issue = Issue(
                    id=f"ISSUE-{len(issues)+1:03d}",
                    type='ERROR',
                    severity='MEDIUM',
                    confidence=0.8,
                    title=error.get('message_summary', 'Error')[:100],
                    description=error.get('message_summary', '')
                )
                issues.append(issue)

        for i, perf in enumerate(extracted_info.get('performance_issues', [])):
            issue = Issue(
                id=f"ISSUE-{len(issues)+1:03d}",
                type=perf.get('type', 'PERFORMANCE'),
                severity=perf.get('impact', 'MEDIUM'),
                confidence=0.7,
                title=f"Performance issue: {perf.get('type', 'Unknown')}",
                description=perf.get('summary', '')
            )
            issues.append(issue)

        return issues

    def _build_crash_description(self, crash: Dict) -> str:
        crash_type = crash.get('type', 'Unknown')
        reason = crash.get('reason', 'Unknown reason')
        pid = crash.get('pid', 'Unknown')

        return f"{crash_type} occurred in process {pid}. Reason: {reason}"

    def _is_significant_error(self, error: Dict) -> bool:
        message = error.get('message_summary', '').lower()
        significant_keywords = ['exception', 'error', 'fail', 'crash', 'anr', 'oom']
        return any(kw in message for kw in significant_keywords)

    def _analyze_causes(self, issue: Issue, extracted_info: Dict) -> List[PossibleCause]:
        causes = []

        issue_type = issue.type.upper()
        if issue_type in self.ISSUE_TYPE_MAPPING:
            possible_types = self.ISSUE_TYPE_MAPPING[issue_type]['causes']
        else:
            possible_types = ['UNKNOWN']

        for i, cause_type in enumerate(possible_types):
            cause = PossibleCause(
                rank=i + 1,
                priority_score=0.0,
                type=cause_type,
                description=self._get_cause_description(cause_type),
                location=self._locate_cause(cause_type, extracted_info),
                evidence=self._gather_evidence(cause_type, extracted_info),
                confidence=self._estimate_confidence(cause_type, extracted_info),
                severity=self._estimate_severity(cause_type),
                frequency=self._estimate_frequency(cause_type, extracted_info),
                fix_complexity=self._estimate_fix_complexity(cause_type)
            )
            causes.append(cause)

        return causes

    def _get_cause_description(self, cause_type: str) -> str:
        descriptions = {
            'BLOCKING_IO': 'Main thread blocked on I/O operation',
            'DEADLOCK': 'Potential deadlock detected',
            'CPU_OVERLOAD': 'CPU overloaded with too many tasks',
            'MEMORY_PRESSURE': 'Memory pressure causing GC pauses',
            'NPE': 'Null pointer exception',
            'OOM': 'Out of memory',
            'RESOURCE_LEAK': 'Resource not properly released',
            'ILLEGAL_STATE': 'Illegal state encountered',
            'UI_THREAD_BLOCK': 'UI thread blocked by long operation',
            'EXCESSIVE_GC': 'Excessive garbage collection',
            'MEMORY_LEAK': 'Memory leak detected',
            'NETWORK_LATENCY': 'Network latency causing delays'
        }
        return descriptions.get(cause_type, 'Unknown cause')

    def _locate_cause(self, cause_type: str, extracted_info: Dict) -> str:
        crashes = extracted_info.get('crashes', [])
        if crashes:
            stack_summary = crashes[0].get('stack_summary', {})
            top_frames = stack_summary.get('top_frames', [])
            if top_frames:
                return top_frames[0]
        return 'Unknown location'

    def _gather_evidence(self, cause_type: str, extracted_info: Dict) -> List[str]:
        evidence = []

        errors = extracted_info.get('errors', [])
        for error in errors[:3]:
            evidence.append(f"Error: {error.get('message_summary', '')[:100]}")

        return evidence

    def _estimate_confidence(self, cause_type: str, extracted_info: Dict) -> float:
        base_confidence = {
            'BLOCKING_IO': 0.8,
            'DEADLOCK': 0.6,
            'NPE': 0.9,
            'OOM': 0.85,
            'MEMORY_LEAK': 0.7
        }
        return base_confidence.get(cause_type, 0.5)

    def _estimate_severity(self, cause_type: str) -> str:
        high_severity = ['BLOCKING_IO', 'DEADLOCK', 'NPE', 'OOM']
        if cause_type in high_severity:
            return 'HIGH'
        return 'MEDIUM'

    def _estimate_frequency(self, cause_type: str, extracted_info: Dict) -> str:
        crashes = extracted_info.get('crashes', [])
        if len(crashes) > 3:
            return 'OFTEN'
        elif len(crashes) > 1:
            return 'SOMETIMES'
        return 'RARE'

    def _estimate_fix_complexity(self, cause_type: str) -> str:
        simple_fixes = ['NPE', 'BLOCKING_IO']
        complex_fixes = ['MEMORY_LEAK', 'DEADLOCK']

        if cause_type in simple_fixes:
            return 'SIMPLE'
        elif cause_type in complex_fixes:
            return 'COMPLEX'
        return 'MODERATE'

    def _build_timeline(self, issue: Issue, extracted_info: Dict) -> List[TimelineEvent]:
        timeline = []

        contexts = extracted_info.get('contexts', [])
        for ctx in contexts:
            if issue.id in ctx.get('event_id', ''):
                timeline.append(TimelineEvent(
                    time=ctx.get('time_window', {}).get('start', ''),
                    event=f"Context: {ctx.get('type', 'Unknown')}"
                ))

        errors = extracted_info.get('errors', [])
        for error in errors[:5]:
            if issue.type.upper() in error.get('message_summary', '').upper():
                timeline.append(TimelineEvent(
                    time=error.get('timestamp', ''),
                    event=error.get('message_summary', '')[:100]
                ))

        return sorted(timeline, key=lambda x: x.time)

    def _assess_impact(self, issue: Issue, extracted_info: Dict) -> Impact:
        return Impact(
            user_visible=True,
            affected_users="Users experiencing this issue",
            frequency=issue.possible_causes[0].frequency if issue.possible_causes else "UNKNOWN"
        )

    def _generate_suggestions(self, issue: Issue) -> List[Suggestion]:
        suggestions = []

        if not issue.possible_causes:
            return suggestions

        primary_cause = issue.possible_causes[0]

        suggestion_templates = {
            'BLOCKING_IO': [
                "Move I/O operation to background thread",
                "Add timeout for I/O operations"
            ],
            'DEADLOCK': [
                "Review lock ordering",
                "Use timeout-based locks"
            ],
            'NPE': [
                "Add null check before access",
                "Use Optional or null-safe patterns"
            ],
            'OOM': [
                "Optimize memory usage",
                "Implement object pooling"
            ],
            'MEMORY_LEAK': [
                "Review object lifecycle",
                "Use weak references where appropriate"
            ]
        }

        templates = suggestion_templates.get(primary_cause.type, ["Review the issue"])

        for i, template in enumerate(templates):
            suggestions.append(Suggestion(
                priority=i + 1,
                action=template,
                target_cause_rank=primary_cause.rank
            ))

        return suggestions

    def _needs_deeper_analysis(self, issues: List[Issue]) -> bool:
        if not issues:
            return False

        avg_confidence = sum(i.confidence for i in issues) / len(issues)
        return avg_confidence < 0.7

    def _save_report(self, report: AnalysisReport, path: Path) -> None:
        def convert_to_dict(obj):
            if hasattr(obj, '__dict__'):
                return {k: convert_to_dict(v) for k, v in obj.__dict__.items()}
            elif isinstance(obj, list):
                return [convert_to_dict(item) for item in obj]
            elif isinstance(obj, dict):
                return {k: convert_to_dict(v) for k, v in obj.items()}
            else:
                return obj

        data = convert_to_dict(report)

        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
