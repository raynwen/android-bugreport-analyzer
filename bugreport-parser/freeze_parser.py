from dataclasses import dataclass, field
from typing import List, Dict, Optional
from pathlib import Path
from datetime import datetime
import re


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


class FreezeAnalyzer:

    FREEZE_KEYWORDS = [
        'am_freeze', 'am_unfreeze', 'mars', 'freecess',
        'BaseRestrictionMgr', 'FROZEN', 'UNFROZEN'
    ]

    FREEZE_PATTERNS = {
        'timestamp': r'(\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d{3})',
        'am_freeze': r'am_freeze.*uid=(\d+).*pid=(\d+).*package=([\w\.]+)',
        'am_unfreeze': r'am_unfreeze.*uid=(\d+).*pid=(\d+).*package=([\w\.]+)',
        'mars_freeze': r'Mars.*freeze.*package=([\w\.]+).*uid=(\d+)',
        'mars_unfreeze': r'Mars.*unfreeze.*package=([\w\.]+).*uid=(\d+)',
        'freecess_freeze': r'freecess.*frozen.*pid=(\d+)',
        'freecess_unfreeze': r'freecess.*unfrozen.*pid=(\d+)',
        'frozen_crash': r'Process.*\(pid\s+(\d+)\).*has died.*while frozen',
        'frozen_anr': r'ANR in.*while frozen',
        'freeze_timeout': r'freeze.*timeout',
        'package_name': r'package=([\w\.]+)',
        'uid': r'uid[=:](\d+)',
        'pid': r'pid[=:](\d+)'
    }

    def __init__(self, analysis_mode: str = "correlated"):
        self.analysis_mode = analysis_mode
        self.patterns = self._compile_patterns()
        self.freeze_events: List[FreezeEvent] = []
        self.mars_info = MarsInfo()
        self.freecess_info = FreecessInfo()
        self.anomaly_summary = AnomalySummary()
        self.event_counter = 0

    def _compile_patterns(self) -> Dict[str, re.Pattern]:
        return {
            name: re.compile(pattern)
            for name, pattern in self.FREEZE_PATTERNS.items()
        }

    def analyze_log_file(self, file_path: Path) -> None:
        if not file_path.exists():
            return

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, 1):
                    self._analyze_line(line, line_num, file_path)
        except Exception as e:
            print(f"Error analyzing freeze logs in {file_path}: {e}")

    def _analyze_line(self, line: str, line_num: int, file_path: Path) -> None:
        if not any(kw.lower() in line.lower() for kw in self.FREEZE_KEYWORDS):
            return

        timestamp_match = self.patterns['timestamp'].search(line)
        timestamp = timestamp_match.group(1) if timestamp_match else datetime.now().strftime("%m-%d %H:%M:%S.%f")[:-3]

        event_type = self._determine_event_type(line)
        if not event_type:
            return

        package_name = self._extract_package_name(line)
        uid = self._extract_uid(line)
        pid = self._extract_pid(line)
        mechanism = self._determine_mechanism(line)
        reason = self._extract_reason(line)

        if package_name or uid > 0:
            self.event_counter += 1
            event = FreezeEvent(
                id=f"freeze_{self.event_counter:03d}",
                timestamp=timestamp,
                type=event_type,
                package_name=package_name or "unknown",
                uid=uid,
                pid=pid,
                mechanism=mechanism,
                reason=reason,
                detail_uri=f"file://{file_path}#L{line_num}"
            )
            self.freeze_events.append(event)
            self._update_anomaly_summary(event_type)

    def _determine_event_type(self, line: str) -> Optional[str]:
        line_lower = line.lower()
        if 'am_freeze' in line_lower or ('freeze' in line_lower and 'unfreeze' not in line_lower):
            return 'FREEZE'
        elif 'am_unfreeze' in line_lower or 'unfreeze' in line_lower:
            return 'UNFREEZE'
        elif 'frozen' in line_lower and 'crash' in line_lower:
            return 'FROZEN_CRASH'
        elif 'frozen' in line_lower and 'anr' in line_lower:
            return 'FROZEN_ANR'
        elif 'timeout' in line_lower and 'freeze' in line_lower:
            return 'FREEZE_TIMEOUT'
        return None

    def _determine_mechanism(self, line: str) -> str:
        line_lower = line.lower()
        if 'mars' in line_lower:
            return 'mars'
        elif 'freecess' in line_lower:
            return 'freecess'
        elif 'baserestrictionmgr' in line_lower:
            return 'freezer'
        return 'unknown'

    def _extract_package_name(self, line: str) -> str:
        match = self.patterns['package_name'].search(line)
        return match.group(1) if match else ""

    def _extract_uid(self, line: str) -> int:
        match = self.patterns['uid'].search(line)
        return int(match.group(1)) if match else 0

    def _extract_pid(self, line: str) -> int:
        match = self.patterns['pid'].search(line)
        return int(match.group(1)) if match else 0

    def _extract_reason(self, line: str) -> str:
        reasons = [
            'Background restriction', 'App standby', 'Battery saver',
            'Screen off', 'Idle maintenance', 'Memory pressure'
        ]
        for reason in reasons:
            if reason.lower() in line.lower():
                return reason
        return 'Unknown'

    def _update_anomaly_summary(self, event_type: str) -> None:
        if event_type == 'FREEZE':
            self.anomaly_summary.total_freezes += 1
        elif event_type == 'UNFREEZE':
            self.anomaly_summary.total_unfreezes += 1
        elif event_type == 'FROZEN_CRASH':
            self.anomaly_summary.frozen_crashes += 1
        elif event_type == 'FROZEN_ANR':
            self.anomaly_summary.frozen_anrs += 1
        elif event_type == 'FREEZE_TIMEOUT':
            self.anomaly_summary.freeze_timeouts += 1

    def analyze_dumpsys_mars(self, file_path: Path) -> None:
        if not file_path.exists():
            return

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

                frozen_packages = self._extract_mars_frozen_packages(content)
                self.mars_info.current_frozen_packages = frozen_packages

                history_count = self._extract_mars_history_count(content)
                self.mars_info.history_count = history_count

                policies = self._extract_mars_policies(content)
                self.mars_info.restriction_policies = policies
                self.mars_info.detail_uri = f"file://{file_path}"

        except Exception as e:
            print(f"Error analyzing dumpsys mars: {e}")

    def _extract_mars_frozen_packages(self, content: str) -> List[str]:
        packages = []
        lines = content.split('\n')
        in_frozen_section = False
        for line in lines:
            if 'Frozen packages:' in line or 'Currently frozen:' in line:
                in_frozen_section = True
                continue
            if in_frozen_section and line.strip() == '':
                break
            if in_frozen_section:
                pkg_match = re.search(r'([\w\.]+)', line)
                if pkg_match:
                    packages.append(pkg_match.group(1))
        return packages

    def _extract_mars_history_count(self, content: str) -> int:
        match = re.search(r'History.*count[:=]\s*(\d+)', content, re.IGNORECASE)
        return int(match.group(1)) if match else 0

    def _extract_mars_policies(self, content: str) -> List[str]:
        policies = []
        policy_keywords = ['STANDBY', 'FROZEN', 'ACTIVE', 'RESTRICTED']
        for keyword in policy_keywords:
            if keyword in content:
                policies.append(keyword)
        return policies

    def analyze_dumpsys_freecess(self, file_path: Path) -> None:
        if not file_path.exists():
            return

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

                frozen_pids = self._extract_freecess_frozen_pids(content)
                self.freecess_info.frozen_processes = frozen_pids
                self.freecess_info.detail_uri = f"file://{file_path}"

        except Exception as e:
            print(f"Error analyzing dumpsys freecess: {e}")

    def _extract_freecess_frozen_pids(self, content: str) -> List[int]:
        pids = []
        pid_matches = re.findall(r'frozen.*pid[=:]\s*(\d+)', content, re.IGNORECASE)
        for pid_str in pid_matches:
            try:
                pids.append(int(pid_str))
            except ValueError:
                continue
        return pids

    def correlate_with_crashes(self, crashes: List[Dict]) -> None:
        for event in self.freeze_events:
            for crash in crashes:
                crash_ts = crash.get('timestamp', '')
                if self._is_within_time_window(event.timestamp, crash_ts, 60):
                    event.related_crash_id = crash.get('id', '')
                    if event.type == 'FREEZE':
                        event.type = 'FROZEN_CRASH'

    def correlate_with_anrs(self, anrs: List[Dict]) -> None:
        for event in self.freeze_events:
            for anr in anrs:
                anr_ts = anr.get('timestamp', '')
                if self._is_within_time_window(event.timestamp, anr_ts, 60):
                    event.related_anr_id = anr.get('id', '')
                    if event.type == 'FREEZE':
                        event.type = 'FROZEN_ANR'

    def _is_within_time_window(self, ts1: str, ts2: str, window_seconds: int) -> bool:
        try:
            fmt = "%m-%d %H:%M:%S.%f"
            dt1 = datetime.strptime(ts1[:18], fmt)
            dt2 = datetime.strptime(ts2[:18], fmt)
            return abs((dt1 - dt2).total_seconds()) <= window_seconds
        except:
            return False

    def identify_suspicious_packages(self) -> None:
        package_stats = {}
        for event in self.freeze_events:
            pkg = event.package_name
            if pkg not in package_stats:
                package_stats[pkg] = {'freezes': 0, 'crashes': 0, 'anrs': 0}
            package_stats[pkg]['freezes'] += 1
            if event.type == 'FROZEN_CRASH':
                package_stats[pkg]['crashes'] += 1
            elif event.type == 'FROZEN_ANR':
                package_stats[pkg]['anrs'] += 1

        for pkg, stats in package_stats.items():
            if stats['crashes'] > 0 or stats['anrs'] > 0 or stats['freezes'] > 5:
                self.anomaly_summary.suspicious_packages.append(pkg)

    def get_analysis(
        self,
        crashes: Optional[List[Dict]] = None,
        anrs: Optional[List[Dict]] = None
    ) -> FreezeAnalysis:
        if self.analysis_mode == "correlated":
            if crashes:
                self.correlate_with_crashes(crashes)
            if anrs:
                self.correlate_with_anrs(anrs)

        self.identify_suspicious_packages()
        return FreezeAnalysis(
            analysis_mode=self.analysis_mode,
            freeze_events=self.freeze_events,
            mars_info=self.mars_info,
            freecess_info=self.freecess_info,
            anomaly_summary=self.anomaly_summary
        )

    def analyze_independent(self) -> FreezeAnalysis:
        self.identify_suspicious_packages()
        return FreezeAnalysis(
            analysis_mode="independent",
            freeze_events=self.freeze_events,
            mars_info=self.mars_info,
            freecess_info=self.freecess_info,
            anomaly_summary=self.anomaly_summary
        )

    def analyze_correlated(
        self,
        crashes: List[Dict],
        anrs: List[Dict]
    ) -> FreezeAnalysis:
        self.correlate_with_crashes(crashes)
        self.correlate_with_anrs(anrs)
        self.identify_suspicious_packages()
        return FreezeAnalysis(
            analysis_mode="correlated",
            freeze_events=self.freeze_events,
            mars_info=self.mars_info,
            freecess_info=self.freecess_info,
            anomaly_summary=self.anomaly_summary
        )
