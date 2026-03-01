import hashlib
import re
from typing import List, Dict, Tuple
from dataclasses import dataclass, field
from collections import defaultdict


@dataclass
class DedupResult:
    original_count: int
    deduplicated_count: int
    exact_duplicates: int = 0
    pattern_duplicates: int = 0
    stack_duplicates: int = 0
    aggregated_entries: List[Dict] = field(default_factory=list)


class LogDeduplicator:

    def __init__(self):
        self._seen_hashes: Dict[str, int] = {}
        self._pattern_counts: Dict[str, Dict] = defaultdict(lambda: {
            'count': 0,
            'first': None,
            'last': None,
            'sample': None
        })
        self._stack_hashes: Dict[str, Dict] = {}

    def deduplicate(self, entries: List[Dict]) -> Tuple[List[Dict], DedupResult]:
        result = DedupResult(original_count=len(entries))
        deduplicated = []

        for entry in entries:
            entry_hash = self._compute_hash(entry)

            if entry_hash in self._seen_hashes:
                self._seen_hashes[entry_hash] += 1
                result.exact_duplicates += 1
                continue

            self._seen_hashes[entry_hash] = 1

            pattern_key = self._extract_pattern(entry)
            if pattern_key:
                self._pattern_counts[pattern_key]['count'] += 1
                if self._pattern_counts[pattern_key]['first'] is None:
                    self._pattern_counts[pattern_key]['first'] = entry.get('timestamp')
                    self._pattern_counts[pattern_key]['sample'] = entry.get('message', '')[:200]
                self._pattern_counts[pattern_key]['last'] = entry.get('timestamp')

                if self._pattern_counts[pattern_key]['count'] > 1:
                    result.pattern_duplicates += 1
                    continue

            stack_hash = self._compute_stack_hash(entry)
            if stack_hash and stack_hash in self._stack_hashes:
                self._stack_hashes[stack_hash]['count'] += 1
                result.stack_duplicates += 1
                continue
            elif stack_hash:
                self._stack_hashes[stack_hash] = {
                    'count': 1,
                    'entry': entry
                }

            deduplicated.append(entry)

        result.deduplicated_count = len(deduplicated)
        result.aggregated_entries = self._build_aggregated_entries()

        return deduplicated, result

    def _compute_hash(self, entry: Dict) -> str:
        key = f"{entry.get('timestamp', '')}:{entry.get('level', '')}:{entry.get('tag', '')}:{entry.get('message', '')}"
        return hashlib.md5(key.encode()).hexdigest()

    def _extract_pattern(self, entry: Dict) -> str:
        message = entry.get('message', '')

        pattern = re.sub(r'\d+', 'N', message)
        pattern = re.sub(r'0x[0-9a-fA-F]+', 'HEX', pattern)
        pattern = re.sub(r'[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}', 'UUID', pattern)

        return pattern if len(pattern) < len(message) else ''

    def _compute_stack_hash(self, entry: Dict) -> str:
        stack = entry.get('stack_trace', '')
        if not stack:
            return ''

        top_frames = stack.split('\n')[:5]
        return hashlib.md5('\n'.join(top_frames).encode()).hexdigest()

    def _build_aggregated_entries(self) -> List[Dict]:
        entries = []
        for pattern, data in self._pattern_counts.items():
            if data['count'] > 1:
                entries.append({
                    'pattern': pattern[:100],
                    'count': data['count'],
                    'first_occurrence': data['first'],
                    'last_occurrence': data['last'],
                    'sample': data['sample']
                })
        return sorted(entries, key=lambda x: x['count'], reverse=True)
