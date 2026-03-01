import re
from typing import Dict, Pattern, List, Tuple, Optional
try:
    import regex
    HAS_REGEX = True
except ImportError:
    HAS_REGEX = False


class PatternEngine:

    USE_REGEX_ENGINE = HAS_REGEX

    @classmethod
    def compile(cls, pattern: str, flags: int = 0) -> Pattern:
        if cls.USE_REGEX_ENGINE:
            return regex.compile(pattern, flags)
        return re.compile(pattern, flags)

    @classmethod
    def compile_many(cls, patterns: Dict[str, str]) -> Dict[str, Pattern]:
        return {k: cls.compile(v) for k, v in patterns.items()}


class AhoCorasickMatcher:

    def __init__(self, keywords: List[str]):
        self.keywords = keywords
        self._build_automaton()

    def _build_automaton(self):
        self.goto = {}
        self.output = {}
        self.fail = {}

        state = 0
        for keyword in self.keywords:
            current = 0
            for char in keyword:
                if (current, char) not in self.goto:
                    state += 1
                    self.goto[(current, char)] = state
                current = self.goto[(current, char)]
            self.output[current] = keyword

        queue = []
        for char in set(k[1] for k in self.goto.keys() if k[0] == 0):
            if (0, char) in self.goto:
                next_state = self.goto[(0, char)]
                self.fail[next_state] = 0
                queue.append(next_state)

        while queue:
            current = queue.pop(0)
            for (state, char), next_state in list(self.goto.items()):
                if state == current:
                    fail_state = self.fail.get(current, 0)
                    while (fail_state, char) not in self.goto and fail_state != 0:
                        fail_state = self.fail.get(fail_state, 0)

                    if (fail_state, char) in self.goto:
                        self.fail[next_state] = self.goto[(fail_state, char)]
                    else:
                        self.fail[next_state] = 0

                    if self.fail[next_state] in self.output:
                        if next_state not in self.output:
                            self.output[next_state] = []
                        self.output[next_state] = self.output[self.fail[next_state]]

                    queue.append(next_state)

    def search(self, text: str) -> List[Tuple[int, str]]:
        results = []
        state = 0

        for i, char in enumerate(text):
            while (state, char) not in self.goto and state != 0:
                state = self.fail.get(state, 0)

            if (state, char) in self.goto:
                state = self.goto[(state, char)]

            if state in self.output:
                results.append((i, self.output[state]))

        return results


class LogPatterns:

    ENGINE = PatternEngine

    PATTERNS: Dict[str, Pattern] = ENGINE.compile_many({
        'timestamp': r'(\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d{3})',
        'logcat_line': r'^(\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d{3})\s+(\d+)\s+(\d+)\s+([VDIWEF])\s+([^:]+):\s+(.*)$',
        'anr_reason': r'Reason:\s*(.+)',
        'java_exception': r'^([a-zA-Z0-9_.]+(?:Exception|Error)):\s*(.*)$',
        'java_exception_stack': r'^\s+at\s+([a-zA-Z0-9_.]+\.[a-zA-Z0-9_]+\([^)]*\))$',
        'native_signal': r'Signal\s+(\d+)\s+\((SIG\w+)\)',
        'native_stack': r'#\d+\s+(?:pc\s+)?([0-9a-fx]+)\s+(.+)',
        'process_died': r'Process\s+([a-zA-Z0-9_.]+)\s+\(pid\s+(\d+)\)\s+has\s+died',
        'uid_pattern': r'[Uu]id[=:\s]+(\d+)',
        'pid_pattern': r'[Pp]id[=:\s]+(\d+)',
        'package_pattern': r'([a-zA-Z][a-zA-Z0-9_]*(\.[a-zA-Z][a-zA-Z0-9_]*)+)',
    })

    KEYWORD_MATCHER: Optional[AhoCorasickMatcher] = None

    @classmethod
    def get(cls, name: str) -> Pattern:
        return cls.PATTERNS.get(name)

    @classmethod
    def init_keyword_matcher(cls, keywords: List[str]):
        cls.KEYWORD_MATCHER = AhoCorasickMatcher(keywords)

    @classmethod
    def match_keywords(cls, text: str) -> List[Tuple[int, str]]:
        if cls.KEYWORD_MATCHER:
            return cls.KEYWORD_MATCHER.search(text)
        return []

    @classmethod
    def compile_custom(cls, pattern: str) -> Pattern:
        return cls.ENGINE.compile(pattern)


class FileTypeDetector:

    SIGNATURES = {
        'anr_trace': ['ANR in', 'Input dispatching timed out', 'Broadcast of Intent'],
        'tombstone': ['*** *** *** *** *** *** *** *** *** *** *** *** *** *** *** ***'],
        'logcat': ['--------- beginning of', 'D/', 'E/', 'I/', 'W/', 'V/', 'F/'],
        'dropbox': ['@', 'SYSTEM_', 'data_app_'],
        'kernel_log': ['<', '>', '[', 'Linux version'],
    }

    @classmethod
    def detect(cls, content_sample: str) -> str:
        for file_type, signatures in cls.SIGNATURES.items():
            for sig in signatures:
                if sig in content_sample:
                    return file_type
        return 'unknown'
