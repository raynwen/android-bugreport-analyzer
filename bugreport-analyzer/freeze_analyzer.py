from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class FreezeInfo:
    freeze_event_id: str
    freeze_mechanism: str
    freeze_reason: str
    time_from_freeze_to_crash_seconds: float = 0.0


class FreezeIssueAnalyzer:

    def __init__(self):
        self.freeze_issues: List[Dict] = []

    def analyze_freeze_issues(self, extracted_info: Dict) -> List[Dict]:
        freeze_analysis = extracted_info.get('freeze_analysis', {})
        if not freeze_analysis:
            return []

        freeze_events = freeze_analysis.get('freeze_events', [])
        anomaly_summary = freeze_analysis.get('anomaly_summary', {})

        issues = []

        issues.extend(self._analyze_frozen_crashes(freeze_events))
        issues.extend(self._analyze_frozen_anrs(freeze_events))
        issues.extend(self._analyze_freeze_timeouts(freeze_events))
        issues.extend(self._analyze_suspicious_packages(anomaly_summary, freeze_events))

        return issues

    def _analyze_frozen_crashes(self, freeze_events: List[Dict]) -> List[Dict]:
        issues = []

        frozen_crashes = [e for e in freeze_events if e.get('type') == 'FROZEN_CRASH']

        for i, event in enumerate(frozen_crashes):
            issue = {
                'id': f'FREEZE-ISSUE-{i+1:03d}',
                'type': 'FROZEN_CRASH',
                'severity': 'HIGH',
                'confidence': 0.9,
                'title': f'{event.get("mechanism", "Unknown").capitalize()} 冻结状态下发生 Crash',
                'description': self._build_frozen_crash_description(event),
                'freeze_info': FreezeInfo(
                    freeze_event_id=event.get('id', ''),
                    freeze_mechanism=event.get('mechanism', 'unknown'),
                    freeze_reason=event.get('reason', 'Unknown'),
                    time_from_freeze_to_crash_seconds=0.0
                ),
                'possible_causes': self._identify_frozen_crash_causes(event),
                'suggestions': self._generate_frozen_crash_suggestions(event)
            }
            issues.append(issue)

        return issues

    def _build_frozen_crash_description(self, event: Dict) -> str:
        pkg = event.get('package_name', 'Unknown')
        mechanism = event.get('mechanism', 'unknown')
        reason = event.get('reason', 'Unknown')
        return f'应用 {pkg} 在被 {mechanism} 冻结（原因：{reason}）后发生了 Crash。'

    def _identify_frozen_crash_causes(self, event: Dict) -> List[Dict]:
        causes = []

        causes.append({
            'rank': 1,
            'priority_score': 0.0,
            'type': 'FROZEN_HANDLER',
            'description': '应用在冻结状态下仍有 Handler 消息在处理',
            'evidence': [
                f'检测到 {event.get("mechanism", "unknown")} 冻结事件',
                '冻结后发生 Crash'
            ],
            'confidence': 0.85,
            'severity': 'HIGH',
            'frequency': 'OFTEN',
            'fix_complexity': 'MODERATE'
        })

        causes.append({
            'rank': 2,
            'priority_score': 0.0,
            'type': 'FROZEN_BROADCAST',
            'description': '应用在冻结状态下接收到广播未正确处理',
            'evidence': [
                '冻结机制激活',
                'Crash 发生在冻结窗口期内'
            ],
            'confidence': 0.7,
            'severity': 'HIGH',
            'frequency': 'SOMETIMES',
            'fix_complexity': 'MODERATE'
        })

        causes.append({
            'rank': 3,
            'priority_score': 0.0,
            'type': 'FROZEN_JOB',
            'description': '应用在冻结前未正确停止后台 Job',
            'evidence': [
                '应用被冻结',
                '冻结后短时间内 Crash'
            ],
            'confidence': 0.6,
            'severity': 'MEDIUM',
            'frequency': 'SOMETIMES',
            'fix_complexity': 'SIMPLE'
        })

        return causes

    def _generate_frozen_crash_suggestions(self, event: Dict) -> List[Dict]:
        suggestions = []

        suggestions.append({
            'priority': 1,
            'action': '检查应用在冻结前是否正确停止后台任务和 Handler',
            'target_cause_rank': 1
        })

        suggestions.append({
            'priority': 2,
            'action': '实现 ApplicationExitInfo 监听，在应用被系统杀死时执行清理',
            'target_cause_rank': 1
        })

        suggestions.append({
            'priority': 3,
            'action': '检查 BroadcastReceiver 是否在主线程执行耗时操作',
            'target_cause_rank': 2
        })

        return suggestions

    def _analyze_frozen_anrs(self, freeze_events: List[Dict]) -> List[Dict]:
        issues = []

        frozen_anrs = [e for e in freeze_events if e.get('type') == 'FROZEN_ANR']

        for i, event in enumerate(frozen_anrs):
            issue = {
                'id': f'FREEZE-ISSUE-{len(self.freeze_issues)+i+1:03d}',
                'type': 'FROZEN_ANR',
                'severity': 'HIGH',
                'confidence': 0.88,
                'title': f'{event.get("mechanism", "Unknown").capitalize()} 冻结状态下发生 ANR',
                'description': self._build_frozen_anr_description(event),
                'freeze_info': FreezeInfo(
                    freeze_event_id=event.get('id', ''),
                    freeze_mechanism=event.get('mechanism', 'unknown'),
                    freeze_reason=event.get('reason', 'Unknown'),
                    time_from_freeze_to_crash_seconds=0.0
                ),
                'possible_causes': self._identify_frozen_anr_causes(event),
                'suggestions': self._generate_frozen_anr_suggestions(event)
            }
            issues.append(issue)

        return issues

    def _build_frozen_anr_description(self, event: Dict) -> str:
        pkg = event.get('package_name', 'Unknown')
        mechanism = event.get('mechanism', 'unknown')
        return f'应用 {pkg} 在被 {mechanism} 冻结期间发生了 ANR。'

    def _identify_frozen_anr_causes(self, event: Dict) -> List[Dict]:
        causes = []

        causes.append({
            'rank': 1,
            'priority_score': 0.0,
            'type': 'FROZEN_INPUT_DISPATCH',
            'description': '应用在冻结状态下仍有输入事件待处理',
            'evidence': [
                f'{event.get("mechanism", "unknown")} 冻结激活',
                'ANR 原因：Input dispatching timed out'
            ],
            'confidence': 0.9,
            'severity': 'HIGH',
            'frequency': 'OFTEN',
            'fix_complexity': 'MODERATE'
        })

        causes.append({
            'rank': 2,
            'priority_score': 0.0,
            'type': 'FROZEN_SERVICE_BIND',
            'description': '应用在冻结状态下尝试绑定服务',
            'evidence': [
                '冻结事件记录',
                'ANR 发生在冻结后'
            ],
            'confidence': 0.7,
            'severity': 'HIGH',
            'frequency': 'SOMETIMES',
            'fix_complexity': 'MODERATE'
        })

        return causes

    def _generate_frozen_anr_suggestions(self, event: Dict) -> List[Dict]:
        suggestions = []

        suggestions.append({
            'priority': 1,
            'action': '确保应用在 onPause/onStop 时正确移除所有输入事件监听器',
            'target_cause_rank': 1
        })

        suggestions.append({
            'priority': 2,
            'action': '检查服务绑定逻辑，确保在应用进入后台时正确解绑',
            'target_cause_rank': 2
        })

        return suggestions

    def _analyze_freeze_timeouts(self, freeze_events: List[Dict]) -> List[Dict]:
        issues = []

        timeouts = [e for e in freeze_events if e.get('type') == 'FREEZE_TIMEOUT']

        for i, event in enumerate(timeouts):
            issue = {
                'id': f'FREEZE-ISSUE-{len(self.freeze_issues)+i+1:03d}',
                'type': 'FREEZE_TIMEOUT',
                'severity': 'MEDIUM',
                'confidence': 0.75,
                'title': f'{event.get("mechanism", "Unknown").capitalize()} 冻结超时',
                'description': self._build_freeze_timeout_description(event),
                'freeze_info': FreezeInfo(
                    freeze_event_id=event.get('id', ''),
                    freeze_mechanism=event.get('mechanism', 'unknown'),
                    freeze_reason=event.get('reason', 'Unknown'),
                    time_from_freeze_to_crash_seconds=0.0
                ),
                'possible_causes': self._identify_freeze_timeout_causes(event),
                'suggestions': self._generate_freeze_timeout_suggestions(event)
            }
            issues.append(issue)

        return issues

    def _build_freeze_timeout_description(self, event: Dict) -> str:
        pkg = event.get('package_name', 'Unknown')
        mechanism = event.get('mechanism', 'unknown')
        return f'应用 {pkg} 在 {mechanism} 冻结过程中超时。'

    def _identify_freeze_timeout_causes(self, event: Dict) -> List[Dict]:
        causes = []

        causes.append({
            'rank': 1,
            'priority_score': 0.0,
            'type': 'LONG_RUNNING_OPERATION',
            'description': '应用在冻结时仍有长时间运行的操作未完成',
            'evidence': [
                '冻结超时事件记录',
                f'机制：{event.get("mechanism", "unknown")}'
            ],
            'confidence': 0.8,
            'severity': 'MEDIUM',
            'frequency': 'SOMETIMES',
            'fix_complexity': 'MODERATE'
        })

        causes.append({
            'rank': 2,
            'priority_score': 0.0,
            'type': 'IO_BLOCKING',
            'description': '应用在冻结时被 IO 操作阻塞',
            'evidence': [
                '冻结超时发生',
                '可能存在未完成的磁盘或网络 IO'
            ],
            'confidence': 0.65,
            'severity': 'MEDIUM',
            'frequency': 'SOMETIMES',
            'fix_complexity': 'MODERATE'
        })

        return causes

    def _generate_freeze_timeout_suggestions(self, event: Dict) -> List[Dict]:
        suggestions = []

        suggestions.append({
            'priority': 1,
            'action': '检查应用中是否有长时间运行的任务，并确保可以被快速取消',
            'target_cause_rank': 1
        })

        suggestions.append({
            'priority': 2,
            'action': '确保所有 IO 操作都有超时机制',
            'target_cause_rank': 2
        })

        return suggestions

    def _analyze_suspicious_packages(
        self,
        anomaly_summary: Dict,
        freeze_events: List[Dict]
    ) -> List[Dict]:
        issues = []

        suspicious_packages = anomaly_summary.get('suspicious_packages', [])

        for i, pkg in enumerate(suspicious_packages):
            pkg_events = [e for e in freeze_events if e.get('package_name') == pkg]
            if not pkg_events:
                continue

            freeze_count = sum(1 for e in pkg_events if e.get('type') == 'FREEZE')
            crash_count = sum(1 for e in pkg_events if e.get('type') == 'FROZEN_CRASH')
            anr_count = sum(1 for e in pkg_events if e.get('type') == 'FROZEN_ANR')

            if crash_count > 0 or anr_count > 0:
                severity = 'HIGH'
                confidence = 0.85
            elif freeze_count > 10:
                severity = 'MEDIUM'
                confidence = 0.7
            else:
                continue

            issue = {
                'id': f'FREEZE-ISSUE-{len(self.freeze_issues)+i+1:03d}',
                'type': 'SUSPICIOUS_FREEZE_PATTERN',
                'severity': severity,
                'confidence': confidence,
                'title': f'应用 {pkg} 存在可疑的冻结模式',
                'description': self._build_suspicious_pattern_description(
                    pkg, freeze_count, crash_count, anr_count
                ),
                'possible_causes': self._identify_suspicious_pattern_causes(pkg_events),
                'suggestions': self._generate_suspicious_pattern_suggestions()
            }
            issues.append(issue)

        return issues

    def _build_suspicious_pattern_description(
        self,
        pkg: str,
        freeze_count: int,
        crash_count: int,
        anr_count: int
    ) -> str:
        parts = [f'应用 {pkg} 被频繁冻结（{freeze_count} 次）']
        if crash_count > 0:
            parts.append(f'，其中 {crash_count} 次在冻结状态下发生 Crash')
        if anr_count > 0:
            parts.append(f'，{anr_count} 次在冻结状态下发生 ANR')
        return ''.join(parts) + '。'

    def _identify_suspicious_pattern_causes(self, pkg_events: List[Dict]) -> List[Dict]:
        causes = []

        causes.append({
            'rank': 1,
            'priority_score': 0.0,
            'type': 'EXCESSIVE_BACKGROUND_ACTIVITY',
            'description': '应用在后台有过多活动导致频繁被系统冻结',
            'evidence': [
                f'检测到 {len(pkg_events)} 次冻结相关事件'
            ],
            'confidence': 0.75,
            'severity': 'MEDIUM',
            'frequency': 'OFTEN',
            'fix_complexity': 'MODERATE'
        })

        causes.append({
            'rank': 2,
            'priority_score': 0.0,
            'type': 'WAKELOCK_ABUSE',
            'description': '应用可能滥用 WakeLock 导致系统采取更严格的冻结策略',
            'evidence': [
                '频繁冻结模式'
            ],
            'confidence': 0.6,
            'severity': 'MEDIUM',
            'frequency': 'SOMETIMES',
            'fix_complexity': 'MODERATE'
        })

        return causes

    def _generate_suspicious_pattern_suggestions(self) -> List[Dict]:
        suggestions = []

        suggestions.append({
            'priority': 1,
            'action': '审查应用的后台活动，减少不必要的后台工作',
            'target_cause_rank': 1
        })

        suggestions.append({
            'priority': 2,
            'action': '检查 WakeLock 使用，确保及时释放',
            'target_cause_rank': 2
        })

        suggestions.append({
            'priority': 3,
            'action': '考虑使用 WorkManager 替代自定义后台任务',
            'target_cause_rank': 1
        })

        return suggestions
