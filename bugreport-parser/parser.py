import os
import json
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime

from .config import ParserConfig
from .patterns import LogPatterns, FileTypeDetector
from .deduplicator import LogDeduplicator, DedupResult
from .sampler import LogSampler, SamplingConfig, SamplingResult
from .freeze_parser import FreezeAnalyzer
from .models import (
    ExtractedInfo, TargetApp, ExtractionStatsDetail,
    ContextInfo, CrashInfo, ErrorInfo, PerformanceIssue,
    AggregatedPattern, ResourceIndex, StackSummary, TimeRange
)


class LogParser:

    def __init__(self, config: Optional[ParserConfig] = None):
        self.config = config or ParserConfig()
        self.deduplicator = LogDeduplicator()
        self.sampler = LogSampler(SamplingConfig())
        self.patterns = LogPatterns()
        self.freeze_analyzer = None

    def parse(
        self,
        manifest_path: str,
        package_name: str,
        output_dir: Optional[str] = None,
        enable_freeze_analysis: bool = True,
        freeze_analysis_mode: str = "correlated"
    ) -> ExtractedInfo:
        manifest = self._load_manifest(manifest_path)

        if output_dir is None:
            output_dir = Path(manifest_path).parent

        extracted_dir = Path(manifest_path).parent / "extracted"

        uids = self._find_uids(extracted_dir, package_name)

        target_app = TargetApp(package_name=package_name, uids=uids)

        start_time = datetime.now()

        entries, stats = self._extract_entries(extracted_dir, package_name, uids)

        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()

        file_size_mb = self._estimate_file_size(extracted_dir)
        entries, sampling_result = self.sampler.sample(entries, file_size_mb)

        entries, dedup_result = self.deduplicator.deduplicate(entries)

        resource_dir = Path(output_dir) / "resources"
        resource_dir.mkdir(parents=True, exist_ok=True)

        contexts = self._build_contexts(entries, resource_dir)
        crashes = self._extract_crashes(entries, resource_dir)
        errors = self._extract_errors(entries, resource_dir)
        warnings = self._extract_warnings(entries, resource_dir)
        perf_issues = self._extract_performance_issues(entries, resource_dir)

        freeze_analysis = None
        if enable_freeze_analysis:
            freeze_analysis = self._analyze_freezes(
                extracted_dir, crashes, anrs=crashes,
                mode=freeze_analysis_mode
            )

        extracted_info = ExtractedInfo(
            target_app=target_app,
            extraction_stats=ExtractionStatsDetail(
                total_files_processed=stats['files_processed'],
                total_lines_scanned=stats['lines_scanned'],
                processing_time=f"{processing_time:.1f}s",
                memory_peak=self._get_memory_peak()
            ),
            sampling=self._build_sampling_info(sampling_result),
            deduplication=self._build_dedup_info(dedup_result),
            summary={
                'total_entries': len(entries),
                'time_range': self._get_time_range(entries)
            },
            contexts=contexts,
            crashes=crashes,
            errors=errors,
            warnings=warnings,
            performance_issues=perf_issues,
            aggregated_patterns=self._build_aggregated_patterns(dedup_result),
            resource_index=ResourceIndex(
                base_path=str(resource_dir),
                files={
                    'stacks_dir': 'stacks/',
                    'contexts_dir': 'contexts/',
                    'patterns_dir': 'patterns/'
                }
            ),
            freeze_analysis=freeze_analysis
        )

        output_path = Path(output_dir) / "extracted_info.json"
        self._save_extracted_info(extracted_info, output_path)

        return extracted_info

    def _analyze_freezes(
        self,
        extracted_dir: Path,
        crashes: List[CrashInfo],
        anrs: Optional[List[CrashInfo]] = None,
        mode: str = "correlated"
    ):
        self.freeze_analyzer = FreezeAnalyzer(analysis_mode=mode)

        for log_file in extracted_dir.rglob("*.txt"):
            self.freeze_analyzer.analyze_log_file(log_file)

        for mars_file in extracted_dir.rglob("*mars*"):
            self.freeze_analyzer.analyze_dumpsys_mars(mars_file)

        for freecess_file in extracted_dir.rglob("*freecess*"):
            self.freeze_analyzer.analyze_dumpsys_freecess(freecess_file)

        crashes_dict = [vars(c) if hasattr(c, '__dict__') else c for c in crashes]
        anrs_dict = [vars(a) if hasattr(a, '__dict__') else a for a in (anrs or [])]

        return self.freeze_analyzer.get_analysis(crashes=crashes_dict, anrs=anrs_dict)

    def _load_manifest(self, path: str) -> Dict:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _find_uids(self, extracted_dir: Path, package_name: str) -> List[int]:
        uids = set()
        uid_pattern = self.patterns.get('uid_pattern')

        for file_path in extracted_dir.rglob('*'):
            if not file_path.is_file():
                continue

            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        if package_name in line:
                            matches = uid_pattern.findall(line)
                            for uid_str in matches:
                                try:
                                    uids.add(int(uid_str))
                                except ValueError:
                                    continue
            except Exception:
                continue

        return sorted(list(uids))

    def _extract_entries(
        self,
        extracted_dir: Path,
        package_name: str,
        uids: List[int]
    ) -> Tuple[List[Dict], Dict]:
        entries = []
        stats = {'files_processed': 0, 'lines_scanned': 0}

        uid_strs = [str(uid) for uid in uids]

        for file_path in extracted_dir.rglob('*'):
            if not file_path.is_file():
                continue

            stats['files_processed'] += 1

            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        stats['lines_scanned'] += 1

                        if self._should_include(line, package_name, uid_strs):
                            entry = self._parse_line(line, file_path)
                            if entry:
                                entries.append(entry)
            except Exception:
                continue

        return entries, stats

    def _should_include(self, line: str, package_name: str, uid_strs: List[str]) -> bool:
        if package_name in line:
            return True
        for uid_str in uid_strs:
            if uid_str in line:
                return True
        return False

    def _parse_line(self, line: str, file_path: Path) -> Optional[Dict]:
        line = line.rstrip('\n')

        logcat_pattern = self.patterns.get('logcat_line')
        match = logcat_pattern.match(line)

        if match:
            return {
                'timestamp': match.group(1),
                'pid': int(match.group(2)),
                'tid': int(match.group(3)),
                'level': match.group(4),
                'tag': match.group(5).strip(),
                'message': match.group(6),
                'raw_line': line,
                'source_file': str(file_path)
            }

        return {
            'raw_line': line,
            'source_file': str(file_path),
            'timestamp': None,
            'level': None,
            'tag': None,
            'message': line[:500]
        }

    def _build_contexts(self, entries: List[Dict], resource_dir: Path) -> List[ContextInfo]:
        contexts = []
        context_dir = resource_dir / "contexts"
        context_dir.mkdir(parents=True, exist_ok=True)

        key_events = [e for e in entries if self._is_key_event(e)]

        for i, event in enumerate(key_events):
            event_id = f"event_{i+1:03d}"
            ts = event.get('timestamp')

            if not ts:
                continue

            window_entries = [
                e for e in entries
                if e.get('timestamp') and self._within_seconds(e['timestamp'], ts, 30)
            ]

            context_file = context_dir / f"{event_id}.log"
            with open(context_file, 'w', encoding='utf-8') as f:
                for e in window_entries:
                    f.write(e.get('raw_line', '') + '\n')

            contexts.append(ContextInfo(
                type=f"{event.get('type', 'EVENT')}_CONTEXT",
                event_id=event_id,
                time_window=TimeRange(start=ts, end=ts),
                related_entries=len(window_entries),
                processes=list(set(e.get('pid', 0) for e in window_entries if e.get('pid'))),
                detail_uri=f"file://{context_file}"
            ))

        return contexts

    def _is_key_event(self, entry: Dict) -> bool:
        level = entry.get('level', '').upper()
        return level in {'E', 'F'}

    def _within_seconds(self, ts1: str, ts2: str, seconds: int) -> bool:
        try:
            from datetime import datetime
            fmt = "%m-%d %H:%M:%S.%f"
            dt1 = datetime.strptime(ts1[:18], fmt)
            dt2 = datetime.strptime(ts2[:18], fmt)
            return abs((dt1 - dt2).total_seconds()) <= seconds
        except:
            return False

    def _extract_crashes(self, entries: List[Dict], resource_dir: Path) -> List[CrashInfo]:
        crashes = []
        stack_dir = resource_dir / "stacks"
        stack_dir.mkdir(parents=True, exist_ok=True)

        anr_entries = [
            e for e in entries
            if 'ANR' in e.get('message', '').upper() or 'anr' in e.get('tag', '').lower()
        ]

        for i, entry in enumerate(anr_entries):
            crash_id = f"anr_{i+1:03d}"

            stack_trace = self._extract_stack_trace(entry, entries)
            top_frames = stack_trace.split('\n')[:3] if stack_trace else []

            stack_file = stack_dir / f"{crash_id}_stack.txt"
            with open(stack_file, 'w', encoding='utf-8') as f:
                f.write(stack_trace)

            crashes.append(CrashInfo(
                type='ANR',
                timestamp=entry.get('timestamp', ''),
                reason=self._extract_anr_reason(entry),
                pid=entry.get('pid', 0),
                occurrence_count=1,
                context_id=crash_id,
                stack_summary=StackSummary(
                    top_frames=top_frames,
                    total_frames=len(stack_trace.split('\n')) if stack_trace else 0,
                    uri=f"file://{stack_file}"
                )
            ))

        return crashes

    def _extract_stack_trace(self, entry: Dict, all_entries: List[Dict]) -> str:
        lines = []
        ts = entry.get('timestamp')

        if ts:
            for e in all_entries:
                if e.get('timestamp') == ts:
                    lines.append(e.get('raw_line', ''))

        return '\n'.join(lines)

    def _extract_anr_reason(self, entry: Dict) -> str:
        message = entry.get('message', '')
        reason_pattern = self.patterns.get('anr_reason')
        match = reason_pattern.search(message)
        if match:
            return match.group(1)
        return "Unknown"

    def _extract_errors(self, entries: List[Dict], resource_dir: Path) -> List[ErrorInfo]:
        errors = []
        error_dir = resource_dir / "errors"
        error_dir.mkdir(parents=True, exist_ok=True)

        error_entries = [e for e in entries if e.get('level') == 'E']

        for i, entry in enumerate(error_entries[:100]):
            error_id = f"error_{i+1:03d}"

            error_file = error_dir / f"{error_id}.log"
            with open(error_file, 'w', encoding='utf-8') as f:
                f.write(entry.get('raw_line', ''))

            errors.append(ErrorInfo(
                level='ERROR',
                tag=entry.get('tag', ''),
                message_summary=entry.get('message', '')[:200],
                timestamp=entry.get('timestamp', ''),
                occurrence_count=1,
                detail_uri=f"file://{error_file}"
            ))

        return errors

    def _extract_warnings(self, entries: List[Dict], resource_dir: Path) -> List[ErrorInfo]:
        warnings = []
        warn_entries = [e for e in entries if e.get('level') == 'W']

        for i, entry in enumerate(warn_entries[:50]):
            warnings.append(ErrorInfo(
                level='WARNING',
                tag=entry.get('tag', ''),
                message_summary=entry.get('message', '')[:200],
                timestamp=entry.get('timestamp', ''),
                occurrence_count=1
            ))

        return warnings

    def _extract_performance_issues(self, entries: List[Dict], resource_dir: Path) -> List[PerformanceIssue]:
        issues = []

        gc_entries = [e for e in entries if 'GC' in e.get('message', '').upper()]
        if len(gc_entries) > 10:
            issues.append(PerformanceIssue(
                type='GC_OVERHEAD',
                summary=f"Frequent GC detected, {len(gc_entries)} times",
                impact='MEDIUM'
            ))

        return issues

    def _estimate_file_size(self, directory: Path) -> float:
        total_size = 0
        for file_path in directory.rglob('*'):
            if file_path.is_file():
                total_size += file_path.stat().st_size
        return total_size / (1024 * 1024)

    def _get_memory_peak(self) -> str:
        try:
            import resource
            mem = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            return f"{mem // 1024}MB"
        except:
            return "Unknown"

    def _build_sampling_info(self, result: SamplingResult) -> Dict:
        return {
            'applied': result.applied,
            'trigger_reason': result.trigger_reason,
            'original_size': result.original_size,
            'sampled_size': result.sampled_size,
            'compression_ratio': result.compression_ratio,
            'stats': result.stats
        }

    def _build_dedup_info(self, result: DedupResult) -> Dict:
        return {
            'original_count': result.original_count,
            'deduplicated_count': result.deduplicated_count,
            'dedup_stats': {
                'exact_duplicates': result.exact_duplicates,
                'pattern_duplicates': result.pattern_duplicates,
                'stack_duplicates': result.stack_duplicates
            }
        }

    def _get_time_range(self, entries: List[Dict]) -> Dict:
        timestamps = [e.get('timestamp') for e in entries if e.get('timestamp')]
        if timestamps:
            return {
                'start': min(timestamps),
                'end': max(timestamps)
            }
        return {'start': '', 'end': ''}

    def _build_aggregated_patterns(self, dedup_result: DedupResult) -> List[AggregatedPattern]:
        return [
            AggregatedPattern(
                pattern=p['pattern'],
                count=p['count'],
                first_occurrence=p.get('first_occurrence', ''),
                last_occurrence=p.get('last_occurrence', ''),
                sample_summary=p.get('sample', '')[:200]
            )
            for p in dedup_result.aggregated_entries[:20]
        ]

    def _save_extracted_info(self, info: ExtractedInfo, path: Path) -> None:
        def convert_to_dict(obj):
            if hasattr(obj, 'to_dict'):
                return obj.to_dict()
            elif hasattr(obj, '__dict__'):
                return {k: convert_to_dict(v) for k, v in obj.__dict__.items()}
            elif isinstance(obj, list):
                return [convert_to_dict(item) for item in obj]
            elif isinstance(obj, dict):
                return {k: convert_to_dict(v) for k, v in obj.items()}
            else:
                return obj

        data = convert_to_dict(info)

        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
