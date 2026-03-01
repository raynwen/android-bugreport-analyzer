from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
import random


@dataclass
class SamplingConfig:
    key_event_window_seconds: int = 30
    high_freq_sample_rate: float = 0.1
    normal_sample_rate: float = 0.05
    max_output_size_mb: int = 10
    trigger_file_size_mb: int = 500
    trigger_entry_count: int = 100000


@dataclass
class SamplingResult:
    applied: bool
    trigger_reason: str = ""
    original_size: str = ""
    sampled_size: str = ""
    compression_ratio: int = 0
    stats: Dict = field(default_factory=dict)
    preserved_time_windows: List[Dict] = field(default_factory=list)


class LogSampler:

    KEY_EVENTS = {'ANR', 'CRASH', 'ERROR', 'FATAL'}

    def __init__(self, config: Optional[SamplingConfig] = None):
        self.config = config or SamplingConfig()

    def should_sample(self, file_size_mb: float, entry_count: int) -> Tuple[bool, str]:
        if file_size_mb > self.config.trigger_file_size_mb:
            return True, "file_size_exceeded"
        if entry_count > self.config.trigger_entry_count:
            return True, "entry_count_exceeded"
        return False, ""

    def sample(
        self,
        entries: List[Dict],
        file_size_mb: float
    ) -> Tuple[List[Dict], SamplingResult]:
        entry_count = len(entries)
        should_trigger, reason = self.should_sample(file_size_mb, entry_count)

        result = SamplingResult(
            applied=should_trigger,
            trigger_reason=reason,
            original_size=f"{file_size_mb:.1f}MB"
        )

        if not should_trigger:
            result.stats = {
                'total_original_entries': entry_count,
                'total_sampled_entries': entry_count,
                'key_events_preserved': 0,
                'key_events_ratio': '100%'
            }
            return entries, result

        key_events = self._identify_key_events(entries)
        time_windows = self._build_time_windows(key_events)

        sampled = []
        key_count = 0
        high_freq_count = 0
        normal_count = 0

        for entry in entries:
            if self._is_key_event(entry):
                sampled.append(entry)
                key_count += 1
            elif self._in_time_window(entry, time_windows):
                sampled.append(entry)
            elif self._is_high_freq(entry):
                if random.random() < self.config.high_freq_sample_rate:
                    sampled.append(entry)
                    high_freq_count += 1
            else:
                if random.random() < self.config.normal_sample_rate:
                    sampled.append(entry)
                    normal_count += 1

        result.sampled_size = self._estimate_size(len(sampled), entry_count, file_size_mb)
        result.compression_ratio = int((1 - len(sampled) / entry_count) * 100) if entry_count > 0 else 0
        result.stats = {
            'total_original_entries': entry_count,
            'total_sampled_entries': len(sampled),
            'key_events_preserved': key_count,
            'key_events_ratio': '100%',
            'high_freq_sampled': high_freq_count,
            'normal_sampled': normal_count
        }
        result.preserved_time_windows = time_windows

        return sampled, result

    def _identify_key_events(self, entries: List[Dict]) -> List[Dict]:
        return [
            e for e in entries
            if self._is_key_event(e)
        ]

    def _is_key_event(self, entry: Dict) -> bool:
        level = entry.get('level', '').upper()
        event_type = entry.get('type', '').upper()
        message = entry.get('message', '').upper()

        if level in {'E', 'F'}:
            return True
        if event_type in self.KEY_EVENTS:
            return True
        if any(kw in message for kw in ['ANR', 'CRASH', 'FATAL', 'EXCEPTION']):
            return True
        return False

    def _build_time_windows(self, key_events: List[Dict]) -> List[Dict]:
        windows = []
        for event in key_events:
            ts = event.get('timestamp')
            if ts:
                windows.append({
                    'event': f"{event.get('type', 'Event')} at {ts}",
                    'start': ts,
                    'end': ts,
                    'entries_preserved': 0
                })
        return windows

    def _in_time_window(self, entry: Dict, windows: List[Dict]) -> bool:
        entry_ts = entry.get('timestamp')
        if not entry_ts or not windows:
            return False

        for window in windows:
            if self._within_seconds(entry_ts, window['start'], self.config.key_event_window_seconds):
                return True
        return False

    def _within_seconds(self, ts1: str, ts2: str, seconds: int) -> bool:
        try:
            from datetime import datetime
            fmt = "%m-%d %H:%M:%S.%f"
            dt1 = datetime.strptime(ts1[:18], fmt)
            dt2 = datetime.strptime(ts2[:18], fmt)
            return abs((dt1 - dt2).total_seconds()) <= seconds
        except:
            return False

    def _is_high_freq(self, entry: Dict) -> bool:
        level = entry.get('level', '').upper()
        return level in {'W', 'I'}

    def _estimate_size(self, sampled_count: int, total_count: int, original_size_mb: float) -> str:
        if total_count == 0:
            return "0MB"
        ratio = sampled_count / total_count
        estimated_mb = original_size_mb * ratio
        return f"{estimated_mb:.1f}MB"
