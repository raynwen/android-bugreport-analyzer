# Android Bug Report 分析系统 - 功能规格说明书 (FSD)

## 1. 文件结构

```
android-bugreport-analyzer/
├── requirements.txt              # 根目录：一次性安装所有依赖
├── requirements-shared.txt       # 共享依赖：所有Skills都需要
├── FSD.md
├── PRD.md
├── bugreport-extractor/
│   ├── SKILL.md
│   ├── __init__.py
│   ├── extractor.py
│   ├── config.py
│   └── requirements.txt         # Extractor依赖清单
├── bugreport-parser/
│   ├── SKILL.md
│   ├── __init__.py
│   ├── parser.py
│   ├── patterns.py
│   ├── deduplicator.py
│   ├── sampler.py
│   ├── config.py
│   └── requirements.txt         # Parser依赖清单
├── bugreport-analyzer/
│   ├── SKILL.md
│   ├── __init__.py
│   ├── analyzer.py
│   ├── priority.py
│   ├── config.py
│   └── requirements.txt         # Analyzer依赖清单
└── bugreport-coordinator/
    ├── SKILL.md
    ├── __init__.py
    ├── coordinator.py
    ├── report_generator.py
    ├── config.py
    └── requirements.txt         # Coordinator依赖清单
```

**输出目录结构**:
```
<output_dir>/
├── extracted/              # 解压后的文件
├── intermediate/           # 中间 JSON 文件
│   ├── manifest.json
│   ├── extracted_info.json
│   └── analysis_report.json
├── resources/              # 资源文件 (堆栈、上下文等)
│   ├── stacks/
│   ├── contexts/
│   ├── patterns/
│   └── errors/
└── reports/                # 最终报告
    └── final_report.md
```

**依赖文件说明**:
- `requirements.txt` - 根目录：一次性安装所有依赖
- `requirements-shared.txt` - 共享依赖：所有Skills都需要
- 每个Skill目录下的`requirements.txt` - 该Skill的独立依赖

## 2. 数据结构定义

### 2.1 通用数据结构

```python
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class Severity(Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class Frequency(Enum):
    ALWAYS = "ALWAYS"
    OFTEN = "OFTEN"
    SOMETIMES = "SOMETIMES"
    RARE = "RARE"


class FixComplexity(Enum):
    SIMPLE = "SIMPLE"
    MODERATE = "MODERATE"
    COMPLEX = "COMPLEX"
    DIFFICULT = "DIFFICULT"


@dataclass
class URIReference:
    uri: str
    line_start: Optional[int] = None
    line_end: Optional[int] = None

    def to_uri(self) -> str:
        if self.line_start and self.line_end:
            return f"{self.uri}#L{self.line_start}-L{self.line_end}"
        return self.uri


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
```

### 2.2 Manifest 数据结构

```python
@dataclass
class FileInfo:
    name: str
    size: str
    type: str
    encoding: str = "utf-8"
    path: Optional[str] = None


@dataclass
class DirectoryInfo:
    path: str
    type: str = "directory"
    files: List[FileInfo] = field(default_factory=list)


@dataclass
class ExtractionStats:
    total_files: int
    total_size: str
    extraction_time: str
    max_depth_reached: int
    compressed_size: str
    compression_ratio: float


@dataclass
class Manifest:
    version: str = "1.0"
    extracted_at: str = field(default_factory=lambda: datetime.now().isoformat())
    source_file: str = ""
    extraction_stats: Optional[ExtractionStats] = None
    file_tree: List[DirectoryInfo] = field(default_factory=list)
    key_files: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "extracted_at": self.extracted_at,
            "source_file": self.source_file,
            "extraction_stats": self.extraction_stats.__dict__ if self.extraction_stats else None,
            "file_tree": [vars(d) for d in self.file_tree],
            "key_files": self.key_files
        }
```

### 2.3 Extracted Info 数据结构

```python
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
    stack_summary: StackSummary


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
```

### 2.4 Analysis Report 数据结构

```python
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
class FreezeInfo:
    freeze_event_id: str
    freeze_mechanism: str
    freeze_reason: str
    time_from_freeze_to_crash_seconds: float = 0.0


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
```

## 3. Skill 1: Extractor 实现

### 3.1 依赖清单 (requirements.txt)
```txt
# 核心依赖（必需）
# Python标准库，无需额外安装:
# - zipfile      # ZIP格式解压
# - tarfile      # TAR/TAR.GZ格式解压
# - gzip         # GZIP格式解压
# - bz2          # BZ2格式解压
# - shutil       # 文件操作
# - pathlib     # 路径操作
# - concurrent.futures  # 并发处理

# 可选依赖（推荐安装以增强功能）
psutil>=5.9.0        # 用于磁盘空间和内存检测，自动配置并发数
```

### 3.2 config.py

```python
from dataclasses import dataclass


@dataclass
class ExtractorConfig:
    max_depth: int = 10
    max_workers: int = 4
    max_file_size_mb: int = 1024
    max_total_size_gb: int = 10
    space_multiplier: int = 3
    supported_formats: tuple = ('.zip', '.tar.gz', '.tgz', '.gz', '.bz2')
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ExtractorConfig':
        return cls(
            max_depth=data.get('max_depth', 10),
            max_workers=data.get('max_workers', 4),
            max_file_size_mb=data.get('max_file_size_mb', 1024),
            max_total_size_gb=data.get('max_total_size_gb', 10),
            space_multiplier=data.get('space_multiplier', 3)
        )
```

### 3.2 extractor.py

```python
import os
import zipfile
import tarfile
import shutil
import threading
from pathlib import Path
from typing import Optional, List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

from .config import ExtractorConfig
from .models import Manifest, DirectoryInfo, FileInfo, ExtractionStats


class DiskSpaceChecker:
    
    @staticmethod
    def check_available_space(path: str, required_bytes: int) -> Tuple[bool, int]:
        stat = shutil.disk_usage(path)
        available = stat.free
        return available >= required_bytes, available
    
    @staticmethod
    def get_required_space(file_size: int, multiplier: int = 3) -> int:
        return file_size * multiplier


class ArchiveExtractor:
    
    def __init__(self, config: Optional[ExtractorConfig] = None):
        self.config = config or ExtractorConfig()
        self._lock = threading.Lock()
        self._total_extracted_size = 0
        self._max_depth_reached = 0
    
    def extract(self, source_path: str, output_dir: Optional[str] = None) -> Manifest:
        source = Path(source_path)
        if not source.exists():
            raise FileNotFoundError(f"Source file not found: {source_path}")
        
        if output_dir is None:
            output_dir = f"extracted_{source.stem}"
        
        output = Path(output_dir)
        output.mkdir(parents=True, exist_ok=True)
        
        self._validate_source(source)
        self._check_disk_space(source, output)
        
        start_time = datetime.now()
        
        extracted_files = self._extract_archive(source, output, depth=0)
        
        end_time = datetime.now()
        extraction_time = (end_time - start_time).total_seconds()
        
        manifest = self._build_manifest(
            source_path=str(source),
            output_dir=output,
            extracted_files=extracted_files,
            extraction_time=extraction_time
        )
        
        manifest_path = output / "manifest.json"
        self._save_manifest(manifest, manifest_path)
        
        return manifest
    
    def _validate_source(self, source: Path) -> None:
        if source.suffix.lower() not in self.config.supported_formats:
            if not any(str(source).endswith(fmt) for fmt in self.config.supported_formats):
                raise ValueError(f"Unsupported format: {source.suffix}")
    
    def _check_disk_space(self, source: Path, output: Path) -> None:
        file_size = source.stat().st_size
        required = DiskSpaceChecker.get_required_space(
            file_size, self.config.space_multiplier
        )
        
        ok, available = DiskSpaceChecker.check_available_space(
            str(output.parent), required
        )
        
        if not ok:
            raise IOError(
                f"Insufficient disk space. Required: {required // (1024*1024)}MB, "
                f"Available: {available // (1024*1024)}MB"
            )
    
    def _extract_archive(
        self, 
        source: Path, 
        output: Path, 
        depth: int
    ) -> List[Tuple[Path, int]]:
        if depth > self.config.max_depth:
            print(f"Max depth {self.config.max_depth} reached, skipping: {source}")
            return []
        
        with self._lock:
            if depth > self._max_depth_reached:
                self._max_depth_reached = depth
        
        extracted = []
        
        if source.suffix == '.zip':
            extracted = self._extract_zip(source, output, depth)
        elif str(source).endswith('.tar.gz') or source.suffix == '.tgz':
            extracted = self._extract_tar(source, output, depth)
        elif source.suffix == '.gz':
            extracted = self._extract_gzip(source, output, depth)
        elif source.suffix == '.bz2':
            extracted = self._extract_bzip2(source, output, depth)
        
        nested = []
        for file_path, size in extracted:
            if self._is_archive(file_path):
                nested.extend(self._extract_archive(file_path, output, depth + 1))
        
        return extracted + nested
    
    def _extract_zip(
        self, 
        source: Path, 
        output: Path, 
        depth: int
    ) -> List[Tuple[Path, int]]:
        extracted = []
        
        with zipfile.ZipFile(source, 'r') as zf:
            for member in zf.namelist():
                self._check_file_size(member, zf.getinfo(member).file_size)
                
                zf.extract(member, output)
                file_path = output / member
                
                if file_path.is_file():
                    size = file_path.stat().st_size
                    extracted.append((file_path, size))
                    self._update_total_size(size)
        
        return extracted
    
    def _extract_tar(
        self, 
        source: Path, 
        output: Path, 
        depth: int
    ) -> List[Tuple[Path, int]]:
        extracted = []
        
        with tarfile.open(source, 'r:gz') as tf:
            for member in tf.getmembers():
                if member.isfile():
                    self._check_file_size(member.name, member.size)
                
                tf.extract(member, output)
                
                if member.isfile():
                    file_path = output / member.name
                    extracted.append((file_path, member.size))
                    self._update_total_size(member.size)
        
        return extracted
    
    def _extract_gzip(
        self, 
        source: Path, 
        output: Path, 
        depth: int
    ) -> List[Tuple[Path, int]]:
        import gzip
        
        target = output / source.stem
        with gzip.open(source, 'rb') as f_in:
            with open(target, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        size = target.stat().st_size
        self._check_file_size(str(target), size)
        self._update_total_size(size)
        
        return [(target, size)]
    
    def _extract_bzip2(
        self, 
        source: Path, 
        output: Path, 
        depth: int
    ) -> List[Tuple[Path, int]]:
        import bz2
        
        target = output / source.stem
        with bz2.open(source, 'rb') as f_in:
            with open(target, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        size = target.stat().st_size
        self._check_file_size(str(target), size)
        self._update_total_size(size)
        
        return [(target, size)]
    
    def _check_file_size(self, name: str, size: int) -> None:
        max_size = self.config.max_file_size_mb * 1024 * 1024
        if size > max_size:
            raise IOError(
                f"File too large: {name} ({size // (1024*1024)}MB > {self.config.max_file_size_mb}MB)"
            )
    
    def _update_total_size(self, size: int) -> None:
        with self._lock:
            self._total_extracted_size += size
            max_total = self.config.max_total_size_gb * 1024 * 1024 * 1024
            if self._total_extracted_size > max_total:
                raise IOError(
                    f"Total extracted size exceeded limit: "
                    f"{self._total_extracted_size // (1024*1024*1024)}GB > {self.config.max_total_size_gb}GB"
                )
    
    def _is_archive(self, path: Path) -> bool:
        return any(str(path).endswith(fmt) for fmt in self.config.supported_formats)
    
    def _build_manifest(
        self,
        source_path: str,
        output_dir: Path,
        extracted_files: List[Tuple[Path, int]],
        extraction_time: float
    ) -> Manifest:
        total_size = sum(size for _, size in extracted_files)
        
        file_tree = self._build_file_tree(output_dir)
        key_files = self._identify_key_files(output_dir)
        
        stats = ExtractionStats(
            total_files=len(extracted_files),
            total_size=self._format_size(total_size),
            extraction_time=f"{extraction_time:.1f}s",
            max_depth_reached=self._max_depth_reached,
            compressed_size=self._format_size(Path(source_path).stat().st_size),
            compression_ratio=round(total_size / Path(source_path).stat().st_size, 1) if Path(source_path).stat().st_size > 0 else 0
        )
        
        return Manifest(
            source_file=source_path,
            extraction_stats=stats,
            file_tree=file_tree,
            key_files=key_files
        )
    
    def _build_file_tree(self, output_dir: Path) -> List[DirectoryInfo]:
        tree = []
        
        for root, dirs, files in os.walk(output_dir):
            root_path = Path(root)
            rel_path = root_path.relative_to(output_dir)
            
            if rel_path == Path('.'):
                continue
            
            dir_info = DirectoryInfo(
                path=str(rel_path),
                files=[
                    FileInfo(
                        name=f.name,
                        size=self._format_size(f.stat().st_size),
                        type=self._detect_file_type(f)
                    )
                    for f in root_path.iterdir()
                    if f.is_file()
                ]
            )
            tree.append(dir_info)
        
        return tree
    
    def _detect_file_type(self, file_path: Path) -> str:
        name = file_path.name.lower()
        
        if 'anr' in name:
            return 'anr_trace'
        elif 'tombstone' in name:
            return 'tombstone'
        elif 'logcat' in name:
            return 'logcat'
        elif 'dumpstate' in name:
            return 'dumpstate'
        elif 'dropbox' in str(file_path).lower():
            return 'dropbox'
        else:
            return 'unknown'
    
    def _identify_key_files(self, output_dir: Path) -> Dict[str, str]:
        key_files = {}
        
        for file_path in output_dir.rglob('*'):
            if not file_path.is_file():
                continue
            
            name = file_path.name.lower()
            rel_path = str(file_path.relative_to(output_dir))
            
            if 'logcat' in name:
                key_files['logcat'] = rel_path
            elif 'dumpstate' in name:
                key_files['dumpstate'] = rel_path
            elif 'anr' in name and 'anr_dir' not in key_files:
                key_files['anr_dir'] = str(file_path.parent.relative_to(output_dir))
            elif 'tombstone' in name and 'tombstone_dir' not in key_files:
                key_files['tombstone_dir'] = str(file_path.parent.relative_to(output_dir))
            elif 'dropbox' in name and 'dropbox_dir' not in key_files:
                key_files['dropbox_dir'] = str(file_path.parent.relative_to(output_dir))
        
        return key_files
    
    def _format_size(self, size: int) -> str:
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f}{unit}"
            size /= 1024
        return f"{size:.1f}TB"
    
    def _save_manifest(self, manifest: Manifest, path: Path) -> None:
        import json
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(manifest.to_dict(), f, indent=2, ensure_ascii=False)
```

## 4. Skill 2: Parser 实现

### 4.0 依赖清单 (requirements.txt)
```txt
# 核心依赖（必需）
regex>=2022.9.0     # 高性能正则表达式库，比标准re库快3-5倍，用于复杂模式匹配

# 可选依赖（推荐安装以增强功能）
psutil>=5.9.0       # 用于内存使用监控和采样策略决策
```

### 4.1 并行处理架构

```python
from dataclasses import dataclass
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading


@dataclass
class ParallelConfig:
    max_workers: int = 4
    chunk_size: int = 10000
    enable_parallel: bool = True


class FileProcessorPool:
    
    def __init__(self, config: Optional[ParallelConfig] = None):
        self.config = config or ParallelConfig()
        self._lock = threading.Lock()
        self._results: List = []
    
    def process_files_parallel(
        self, 
        file_paths: List[Path], 
        processor_func,
        package_name: str,
        uids: List[int]
    ) -> List:
        if not self.config.enable_parallel or len(file_paths) == 1:
            return [processor_func(fp, package_name, uids) for fp in file_paths]
        
        results = []
        
        with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
            futures = {
                executor.submit(processor_func, fp, package_name, uids): fp
                for fp in file_paths
            }
            
            for future in as_completed(futures):
                try:
                    result = future.result()
                    with self._lock:
                        results.extend(result)
                except Exception as e:
                    print(f"Error processing file: {e}")
        
        return results


class ChunkProcessor:
    
    def __init__(self, chunk_size: int = 10000):
        self.chunk_size = chunk_size
    
    def process_large_file(self, file_path: Path, processor_func) -> List:
        results = []
        chunk = []
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for i, line in enumerate(f):
                chunk.append(line)
                
                if len(chunk) >= self.chunk_size:
                    chunk_results = processor_func(chunk)
                    results.extend(chunk_results)
                    chunk = []
            
            if chunk:
                chunk_results = processor_func(chunk)
                results.extend(chunk_results)
        
        return results
```

### 4.1 patterns.py - 高效正则表达式引擎

```python
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
            return regex.compile(pattern, flags | regex.OPTIMIZE)
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
```

### 4.2 deduplicator.py

```python
import hashlib
from typing import List, Dict, Tuple, Any
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
        
        import re
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
```

### 4.3 sampler.py

```python
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
```

### 4.4 parser.py

```python
import os
import json
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime

from .config import ParserConfig
from .patterns import LogPatterns, FileTypeDetector
from .deduplicator import LogDeduplicator, DedupResult
from .sampler import LogSampler, SamplingConfig, SamplingResult
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
    
    def parse(
        self,
        manifest_path: str,
        package_name: str,
        output_dir: Optional[str] = None
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
            )
        )
        
        output_path = Path(output_dir) / "extracted_info.json"
        self._save_extracted_info(extracted_info, output_path)
        
        return extracted_info
    
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
```

### 4.5 freeze_parser.py - 冻结分析模块

```python
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
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
        if 'am_freeze' in line_lower or 'freeze' in line_lower and 'unfreeze' not in line_lower:
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
        elif 'baseRestrictionMgr' in line_lower or 'baserestrictionmgr' in line_lower:
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
    
    def get_analysis(self) -> FreezeAnalysis:
        self.identify_suspicious_packages()
        return FreezeAnalysis(
            analysis_mode=self.analysis_mode,
            freeze_events=self.freeze_events,
            mars_info=self.mars_info,
            freecess_info=self.freecess_info,
            anomaly_summary=self.anomaly_summary
        )
```

## 5. Skill 3: Analyzer 实现

### 5.0 依赖清单 (requirements.txt)
```txt
# 核心依赖（必需）
# Python标准库，无需额外安装:
# - json          # JSON序列化
# - datetime      # 时间处理
# - typing        # 类型提示
# - dataclasses   # 数据类

# 可选依赖（推荐安装以增强功能）
# 无额外依赖
```

### 5.1 priority.py

```python
from typing import Dict, List
from enum import Enum


class Severity(Enum):
    CRITICAL = 1.0
    HIGH = 0.8
    MEDIUM = 0.6
    LOW = 0.4


class Frequency(Enum):
    ALWAYS = 1.0
    OFTEN = 0.7
    SOMETIMES = 0.4
    RARE = 0.2


class FixComplexity(Enum):
    SIMPLE = 0.2
    MODERATE = 0.5
    COMPLEX = 0.8
    DIFFICULT = 1.0


class PriorityCalculator:
    
    WEIGHTS = {
        'confidence': 0.40,
        'severity': 0.25,
        'frequency': 0.20,
        'fix_complexity': 0.15
    }
    
    @classmethod
    def calculate(
        cls,
        confidence: float,
        severity: str,
        frequency: str,
        fix_complexity: str
    ) -> float:
        severity_score = Severity[severity.upper()].value if severity.upper() in Severity.__members__ else 0.5
        frequency_score = Frequency[frequency.upper()].value if frequency.upper() in Frequency.__members__ else 0.5
        complexity_score = FixComplexity[fix_complexity.upper()].value if fix_complexity.upper() in FixComplexity.__members__ else 0.5
        
        score = (
            confidence * cls.WEIGHTS['confidence'] +
            severity_score * cls.WEIGHTS['severity'] +
            frequency_score * cls.WEIGHTS['frequency'] +
            (1 - complexity_score) * cls.WEIGHTS['fix_complexity']
        )
        
        return round(score, 2)
    
    @classmethod
    def rank_causes(cls, causes: List[Dict]) -> List[Dict]:
        for cause in causes:
            cause['priority_score'] = cls.calculate(
                cause.get('confidence', 0.5),
                cause.get('severity', 'MEDIUM'),
                cause.get('frequency', 'SOMETIMES'),
                cause.get('fix_complexity', 'MODERATE')
            )
        
        sorted_causes = sorted(causes, key=lambda x: x['priority_score'], reverse=True)
        
        for i, cause in enumerate(sorted_causes, 1):
            cause['rank'] = i
        
        return sorted_causes
```

### 5.2 multi_dimension.py - 多维度分析模块

```python
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum


class AnalysisDimension(Enum):
    TEMPORAL = "temporal"
    SPATIAL = "spatial"
    BEHAVIORAL = "behavioral"
    RESOURCE = "resource"
    NETWORK = "network"
    USER_IMPACT = "user_impact"


@dataclass
class DimensionScore:
    dimension: str
    score: float
    evidence: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MultiDimensionAnalysis:
    dimensions: List[DimensionScore]
    overall_score: float
    primary_dimension: str
    recommendations: List[str] = field(default_factory=list)


class TemporalAnalyzer:
    
    def analyze(self, entries: List[Dict], crashes: List[Dict]) -> DimensionScore:
        evidence = []
        score = 0.0
        details = {}
        
        if crashes:
            timestamps = [c.get('timestamp', '') for c in crashes if c.get('timestamp')]
            if timestamps:
                details['crash_times'] = timestamps
                details['crash_count'] = len(timestamps)
                
                if len(timestamps) > 1:
                    score += 0.3
                    evidence.append(f"Multiple crashes at different times: {len(timestamps)}")
        
        error_entries = [e for e in entries if e.get('level') == 'E']
        if error_entries:
            details['error_count'] = len(error_entries)
            if len(error_entries) > 10:
                score += 0.2
                evidence.append(f"High error frequency: {len(error_entries)} errors")
        
        return DimensionScore(
            dimension=AnalysisDimension.TEMPORAL.value,
            score=min(score, 1.0),
            evidence=evidence,
            details=details
        )


class ResourceAnalyzer:
    
    def analyze(self, entries: List[Dict], perf_issues: List[Dict]) -> DimensionScore:
        evidence = []
        score = 0.0
        details = {}
        
        gc_entries = [e for e in entries if 'GC' in e.get('message', '').upper()]
        if gc_entries:
            details['gc_count'] = len(gc_entries)
            if len(gc_entries) > 20:
                score += 0.3
                evidence.append(f"Frequent GC: {len(gc_entries)} times")
        
        memory_entries = [e for e in entries if 'memory' in e.get('message', '').lower()]
        if memory_entries:
            details['memory_related'] = len(memory_entries)
            score += 0.2
            evidence.append(f"Memory-related entries: {len(memory_entries)}")
        
        for perf in perf_issues:
            if perf.get('type') == 'GC_OVERHEAD':
                score += 0.2
                evidence.append("GC overhead detected")
        
        return DimensionScore(
            dimension=AnalysisDimension.RESOURCE.value,
            score=min(score, 1.0),
            evidence=evidence,
            details=details
        )


class BehavioralAnalyzer:
    
    def analyze(self, entries: List[Dict], contexts: List[Dict]) -> DimensionScore:
        evidence = []
        score = 0.0
        details = {}
        
        user_actions = [e for e in entries if any(
            kw in e.get('message', '').lower() 
            for kw in ['click', 'touch', 'scroll', 'input', 'user']
        )]
        
        if user_actions:
            details['user_action_count'] = len(user_actions)
            score += 0.2
            evidence.append(f"User interactions logged: {len(user_actions)}")
        
        lifecycle_entries = [e for e in entries if any(
            kw in e.get('message', '').upper()
            for kw in ['ONCREATE', 'ONSTART', 'ONRESUME', 'ONPAUSE', 'ONSTOP', 'ONDESTROY']
        )]
        
        if lifecycle_entries:
            details['lifecycle_events'] = len(lifecycle_entries)
            score += 0.2
            evidence.append(f"Lifecycle events: {len(lifecycle_entries)}")
        
        return DimensionScore(
            dimension=AnalysisDimension.BEHAVIORAL.value,
            score=min(score, 1.0),
            evidence=evidence,
            details=details
        )


class NetworkAnalyzer:
    
    def analyze(self, entries: List[Dict]) -> DimensionScore:
        evidence = []
        score = 0.0
        details = {}
        
        network_entries = [e for e in entries if any(
            kw in e.get('message', '').lower()
            for kw in ['http', 'network', 'connection', 'timeout', 'socket']
        )]
        
        if network_entries:
            details['network_entries'] = len(network_entries)
            
            error_network = [e for e in network_entries if e.get('level') in ['E', 'W']]
            if error_network:
                score += 0.3
                evidence.append(f"Network errors/warnings: {len(error_network)}")
            
            timeout_entries = [e for e in network_entries if 'timeout' in e.get('message', '').lower()]
            if timeout_entries:
                score += 0.2
                evidence.append(f"Timeout issues: {len(timeout_entries)}")
        
        return DimensionScore(
            dimension=AnalysisDimension.NETWORK.value,
            score=min(score, 1.0),
            evidence=evidence,
            details=details
        )


class UserImpactAnalyzer:
    
    def analyze(self, crashes: List[Dict], errors: List[Dict]) -> DimensionScore:
        evidence = []
        score = 0.0
        details = {}
        
        if crashes:
            score += 0.4
            evidence.append(f"Application crashes: {len(crashes)}")
            details['crash_count'] = len(crashes)
        
        anr_count = sum(1 for c in crashes if c.get('type') == 'ANR')
        if anr_count > 0:
            score += 0.3
            evidence.append(f"ANR events (user-visible freezes): {anr_count}")
            details['anr_count'] = anr_count
        
        fatal_errors = [e for e in errors if 'fatal' in e.get('message_summary', '').lower()]
        if fatal_errors:
            score += 0.2
            evidence.append(f"Fatal errors: {len(fatal_errors)}")
            details['fatal_error_count'] = len(fatal_errors)
        
        return DimensionScore(
            dimension=AnalysisDimension.USER_IMPACT.value,
            score=min(score, 1.0),
            evidence=evidence,
            details=details
        )


class MultiDimensionAnalyzer:
    
    def __init__(self):
        self.analyzers = {
            AnalysisDimension.TEMPORAL: TemporalAnalyzer(),
            AnalysisDimension.RESOURCE: ResourceAnalyzer(),
            AnalysisDimension.BEHAVIORAL: BehavioralAnalyzer(),
            AnalysisDimension.NETWORK: NetworkAnalyzer(),
            AnalysisDimension.USER_IMPACT: UserImpactAnalyzer(),
        }
    
    def analyze(
        self, 
        entries: List[Dict], 
        crashes: List[Dict], 
        errors: List[Dict],
        contexts: List[Dict],
        perf_issues: List[Dict]
    ) -> MultiDimensionAnalysis:
        dimensions = []
        
        temporal = self.analyzers[AnalysisDimension.TEMPORAL].analyze(entries, crashes)
        dimensions.append(temporal)
        
        resource = self.analyzers[AnalysisDimension.RESOURCE].analyze(entries, perf_issues)
        dimensions.append(resource)
        
        behavioral = self.analyzers[AnalysisDimension.BEHAVIORAL].analyze(entries, contexts)
        dimensions.append(behavioral)
        
        network = self.analyzers[AnalysisDimension.NETWORK].analyze(entries)
        dimensions.append(network)
        
        user_impact = self.analyzers[AnalysisDimension.USER_IMPACT].analyze(crashes, errors)
        dimensions.append(user_impact)
        
        overall_score = sum(d.score for d in dimensions) / len(dimensions)
        
        primary = max(dimensions, key=lambda d: d.score)
        
        recommendations = self._generate_recommendations(dimensions)
        
        return MultiDimensionAnalysis(
            dimensions=dimensions,
            overall_score=overall_score,
            primary_dimension=primary.dimension,
            recommendations=recommendations
        )
    
    def _generate_recommendations(self, dimensions: List[DimensionScore]) -> List[str]:
        recommendations = []
        
        for dim in sorted(dimensions, key=lambda d: d.score, reverse=True):
            if dim.score > 0.5:
                if dim.dimension == AnalysisDimension.TEMPORAL.value:
                    recommendations.append("Investigate temporal patterns and crash timing")
                elif dim.dimension == AnalysisDimension.RESOURCE.value:
                    recommendations.append("Optimize resource usage and reduce GC pressure")
                elif dim.dimension == AnalysisDimension.NETWORK.value:
                    recommendations.append("Review network operations and timeout handling")
                elif dim.dimension == AnalysisDimension.USER_IMPACT.value:
                    recommendations.append("Prioritize fixes for user-visible issues")
        
        return recommendations[:5]
```

### 5.3 analyzer.py

```python
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

from .priority import PriorityCalculator
from .models import (
    AnalysisReport, Issue, PossibleCause, TimelineEvent,
    Impact, Suggestion
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
        }
    }
    
    def __init__(self):
        self.priority_calculator = PriorityCalculator()
    
    def analyze(self, extracted_info_path: str, output_dir: Optional[str] = None) -> AnalysisReport:
        with open(extracted_info_path, 'r', encoding='utf-8') as f:
            extracted_info = json.load(f)
        
        if output_dir is None:
            output_dir = Path(extracted_info_path).parent
        
        issues = self._identify_issues(extracted_info)
        
        for issue in issues:
            issue.possible_causes = self._analyze_causes(issue, extracted_info)
            issue.possible_causes = PriorityCalculator.rank_causes([
                vars(c) for c in issue.possible_causes
            ])
            issue.possible_causes = [PossibleCause(**c) for c in issue.possible_causes]
            
            if issue.possible_causes:
                issue.primary_cause = issue.possible_causes[0]
            
            issue.timeline = self._build_timeline(issue, extracted_info)
            issue.impact = self._assess_impact(issue, extracted_info)
            issue.suggestions = self._generate_suggestions(issue)
        
        report = AnalysisReport(
            issues=issues,
            needs_deeper_analysis=self._needs_deeper_analysis(issues)
        )
        
        output_path = Path(output_dir) / "analysis_report.json"
        self._save_report(report, output_path)
        
        return report
    
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
```

### 5.4 freeze_analyzer.py - 冻结问题分析模块

```python
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime


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
```

## 6. Skill 4: Coordinator 实现

### 6.0 依赖清单 (requirements.txt)
```txt
# 核心依赖（必需）
# Python标准库，无需额外安装:
# - json          # JSON序列化
# - datetime      # 时间处理
# - typing        # 类型提示
# - pathlib       # 路径操作

# 可选依赖（推荐安装以增强功能）
# 无额外依赖
```

### 6.1 report_generator.py

```python
from typing import List, Dict, Any
from pathlib import Path
from datetime import datetime


class ReportGenerator:
    
    @staticmethod
    def generate_markdown(report: Dict[str, Any], output_path: Path) -> str:
        lines = []
        
        lines.append("# Android Bug Report 分析报告")
        lines.append("")
        
        lines.append("## 概述")
        lines.append(f"- **分析时间**: {report.get('analyzed_at', 'Unknown')}")
        
        issues = report.get('issues', [])
        lines.append(f"- **问题数量**: {len(issues)}")
        
        if issues:
            severities = [i.get('severity', 'UNKNOWN') for i in issues]
            highest = max(severities, key=lambda s: {'CRITICAL': 4, 'HIGH': 3, 'MEDIUM': 2, 'LOW': 1}.get(s, 0))
            lines.append(f"- **严重程度**: {highest}")
        
        lines.append("")
        
        if issues:
            lines.append("## 问题列表")
            lines.append("")
            
            for i, issue in enumerate(issues, 1):
                lines.extend(ReportGenerator._format_issue(issue, i))
        
        lines.append("---")
        lines.append("")
        lines.append("## 总结")
        
        if issues:
            high_count = sum(1 for i in issues if i.get('severity') in ['CRITICAL', 'HIGH'])
            lines.append(f"本次分析发现 {len(issues)} 个问题，其中 {high_count} 个高危问题需要立即处理。")
            
            if issues[0].get('suggestions'):
                lines.append(f"建议优先解决: {issues[0].get('title', 'Unknown')}")
        else:
            lines.append("本次分析未发现明显问题。")
        
        content = '\n'.join(lines)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return content
    
    @staticmethod
    def _format_issue(issue: Dict, index: int) -> List[str]:
        lines = []
        
        severity = issue.get('severity', 'UNKNOWN')
        title = issue.get('title', 'Unknown Issue')
        
        lines.append(f"### 问题 {index}: {title} [{severity}]")
        lines.append("")
        
        lines.append("**问题描述**")
        lines.append(issue.get('description', 'No description available.'))
        lines.append("")
        
        causes = issue.get('possible_causes', [])
        if causes:
            lines.append("**可能原因**")
            lines.append("")
            
            for cause in causes[:3]:
                rank = cause.get('rank', 0)
                cause_type = cause.get('type', 'Unknown')
                desc = cause.get('description', '')
                score = cause.get('priority_score', 0)
                
                lines.append(f"{rank}. **{cause_type}** (优先级分数: {score})")
                lines.append(f"   - {desc}")
                
                evidence = cause.get('evidence', [])
                if evidence:
                    lines.append(f"   - 证据: {evidence[0][:100]}")
                
                lines.append("")
        
        timeline = issue.get('timeline', [])
        if timeline:
            lines.append("**时间线**")
            lines.append("")
            lines.append("| 时间 | 事件 |")
            lines.append("|-----|------|")
            
            for event in timeline[:10]:
                lines.append(f"| {event.get('time', 'Unknown')} | {event.get('event', '')[:50]} |")
            
            lines.append("")
        
        suggestions = issue.get('suggestions', [])
        if suggestions:
            lines.append("**建议方案**")
            lines.append("")
            
            for sug in suggestions[:5]:
                priority = sug.get('priority', 0)
                action = sug.get('action', '')
                
                priority_label = {1: '高', 2: '中', 3: '低'}.get(priority, '中')
                lines.append(f"{priority}. **[优先级{priority_label}]** {action}")
            
            lines.append("")
        
        lines.append("---")
        lines.append("")
        
        return lines
```

### 6.2 coordinator.py

```python
import json
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from .report_generator import ReportGenerator


class AnalysisCoordinator:
    
    MAX_ITERATIONS = 3
    CONFIDENCE_THRESHOLD = 0.8
    
    def __init__(self):
        self.iteration_count = 0
        self.analysis_history = []
    
    def coordinate(
        self,
        analysis_report_path: str,
        output_dir: Optional[str] = None
    ) -> str:
        if output_dir is None:
            output_dir = Path(analysis_report_path).parent
        
        with open(analysis_report_path, 'r', encoding='utf-8') as f:
            report = json.load(f)
        
        self.analysis_history.append(report)
        
        iteration = 1
        while self._should_iterate(report) and iteration < self.MAX_ITERATIONS:
            iteration += 1
            self.iteration_count = iteration
            
            report = self._request_deeper_analysis(report)
            self.analysis_history.append(report)
        
        output_path = Path(output_dir) / "final_report.md"
        content = ReportGenerator.generate_markdown(report, output_path)
        
        return str(output_path)
    
    def _should_iterate(self, report: Dict[str, Any]) -> bool:
        if not report.get('needs_deeper_analysis', False):
            return False
        
        issues = report.get('issues', [])
        if not issues:
            return False
        
        avg_confidence = sum(i.get('confidence', 0) for i in issues) / len(issues)
        return avg_confidence < self.CONFIDENCE_THRESHOLD
    
    def _request_deeper_analysis(self, report: Dict[str, Any]) -> Dict[str, Any]:
        additional_files = report.get('additional_files_needed', [])
        
        for issue in report.get('issues', []):
            if issue.get('confidence', 0) < self.CONFIDENCE_THRESHOLD:
                for cause in issue.get('possible_causes', []):
                    cause['confidence'] = min(1.0, cause.get('confidence', 0.5) + 0.1)
                
                issue['confidence'] = min(1.0, issue.get('confidence', 0.5) + 0.1)
        
        report['needs_deeper_analysis'] = False
        
        return report
    
    def get_iteration_summary(self) -> Dict[str, Any]:
        return {
            'total_iterations': self.iteration_count + 1,
            'max_iterations_reached': self.iteration_count >= self.MAX_ITERATIONS - 1,
            'analysis_history_count': len(self.analysis_history)
        }
```

## 7. 测试用例

### 7.1 test_extractor.py

```python
import pytest
import tempfile
import zipfile
from pathlib import Path


class TestExtractor:
    
    def test_extract_zip_file(self, tmp_path):
        from bugreport_extractor.extractor import ArchiveExtractor
        from bugreport_extractor.config import ExtractorConfig
        
        zip_file = tmp_path / "test_bugreport.zip"
        
        with zipfile.ZipFile(zip_file, 'w') as zf:
            zf.writestr("logcat.txt", "test log content")
            zf.writestr("anr/trace.txt", "ANR trace content")
        
        output_dir = tmp_path / "extracted"
        config = ExtractorConfig(max_depth=5)
        extractor = ArchiveExtractor(config)
        
        manifest = extractor.extract(str(zip_file), str(output_dir))
        
        assert manifest is not None
        assert manifest.source_file == str(zip_file)
        assert manifest.extraction_stats.total_files >= 1
    
    def test_max_depth_limit(self, tmp_path):
        from bugreport_extractor.extractor import ArchiveExtractor
        from bugreport_extractor.config import ExtractorConfig
        
        inner_zip = tmp_path / "inner.zip"
        with zipfile.ZipFile(inner_zip, 'w') as zf:
            zf.writestr("test.txt", "content")
        
        outer_zip = tmp_path / "outer.zip"
        with zipfile.ZipFile(outer_zip, 'w') as zf:
            zf.write(inner_zip, "inner.zip")
        
        config = ExtractorConfig(max_depth=1)
        extractor = ArchiveExtractor(config)
        
        output_dir = tmp_path / "extracted"
        manifest = extractor.extract(str(outer_zip), str(output_dir))
        
        assert manifest.extraction_stats.max_depth_reached <= 1
    
    def test_disk_space_check(self, tmp_path):
        from bugreport_extractor.extractor import DiskSpaceChecker
        
        ok, available = DiskSpaceChecker.check_available_space(
            str(tmp_path), 
            1024
        )
        
        assert isinstance(ok, bool)
        assert available >= 0
```

### 7.2 test_parser.py

```python
import pytest
import tempfile
import json
from pathlib import Path


class TestParser:
    
    def test_find_uids(self, tmp_path):
        from bugreport_parser.parser import LogParser
        
        log_file = tmp_path / "test.log"
        log_file.write_text("uid=12345 com.example.app\nuid=12346 com.example.app")
        
        parser = LogParser()
        uids = parser._find_uids(tmp_path, "com.example.app")
        
        assert 12345 in uids
        assert 12346 in uids
    
    def test_deduplication(self):
        from bugreport_parser.deduplicator import LogDeduplicator
        
        entries = [
            {'timestamp': '01-01 10:00:00.000', 'level': 'E', 'tag': 'Test', 'message': 'Error 1'},
            {'timestamp': '01-01 10:00:01.000', 'level': 'E', 'tag': 'Test', 'message': 'Error 1'},
            {'timestamp': '01-01 10:00:02.000', 'level': 'E', 'tag': 'Test', 'message': 'Error 2'},
        ]
        
        deduplicator = LogDeduplicator()
        deduplicated, result = deduplicator.deduplicate(entries)
        
        assert result.original_count == 3
        assert result.deduplicated_count < 3
    
    def test_sampling(self):
        from bugreport_parser.sampler import LogSampler, SamplingConfig
        
        entries = [
            {'timestamp': f'01-01 10:00:{i:02d}.000', 'level': 'I', 'tag': 'Test', 'message': f'Message {i}'}
            for i in range(1000)
        ]
        
        config = SamplingConfig(
            trigger_entry_count=100,
            normal_sample_rate=0.1
        )
        sampler = LogSampler(config)
        
        sampled, result = sampler.sample(entries, 100.0)
        
        assert result.applied == True
        assert len(sampled) < len(entries)
```

### 7.3 test_analyzer.py

```python
import pytest
import tempfile
import json
from pathlib import Path


class TestAnalyzer:
    
    def test_priority_calculation(self):
        from bugreport_analyzer.priority import PriorityCalculator
        
        score = PriorityCalculator.calculate(
            confidence=0.9,
            severity='HIGH',
            frequency='ALWAYS',
            fix_complexity='SIMPLE'
        )
        
        assert 0 <= score <= 1
        assert score > 0.7
    
    def test_issue_identification(self):
        from bugreport_analyzer.analyzer import BugAnalyzer
        
        extracted_info = {
            'crashes': [
                {'type': 'ANR', 'timestamp': '2026-03-01T10:00:00Z', 'reason': 'Test ANR', 'pid': 12345}
            ],
            'errors': [],
            'performance_issues': []
        }
        
        analyzer = BugAnalyzer()
        issues = analyzer._identify_issues(extracted_info)
        
        assert len(issues) >= 1
        assert issues[0].type == 'ANR'
    
    def test_cause_ranking(self):
        from bugreport_analyzer.priority import PriorityCalculator
        
        causes = [
            {'type': 'CAUSE_A', 'confidence': 0.5, 'severity': 'MEDIUM', 'frequency': 'SOMETIMES', 'fix_complexity': 'MODERATE'},
            {'type': 'CAUSE_B', 'confidence': 0.9, 'severity': 'HIGH', 'frequency': 'ALWAYS', 'fix_complexity': 'SIMPLE'},
        ]
        
        ranked = PriorityCalculator.rank_causes(causes)
        
        assert ranked[0]['rank'] == 1
        assert ranked[0]['priority_score'] > ranked[1]['priority_score']
```

## 8. API 使用示例

### 8.1 完整流程示例

```python
from bugreport_extractor.extractor import ArchiveExtractor
from bugreport_parser.parser import LogParser
from bugreport_analyzer.analyzer import BugAnalyzer
from bugreport_coordinator.coordinator import AnalysisCoordinator


def analyze_bug_report(bugreport_path: str, package_name: str, output_dir: str):
    print(f"[1/4] 解压 Bug Report: {bugreport_path}")
    extractor = ArchiveExtractor()
    manifest = extractor.extract(bugreport_path, output_dir)
    print(f"      解压完成，共 {manifest.extraction_stats.total_files} 个文件")
    
    print(f"[2/4] 解析日志，目标应用: {package_name}")
    parser = LogParser()
    manifest_path = f"{output_dir}/manifest.json"
    extracted_info = parser.parse(manifest_path, package_name, output_dir)
    print(f"      解析完成，提取 {extracted_info.summary['total_entries']} 条日志")
    
    print(f"[3/4] 分析问题...")
    analyzer = BugAnalyzer()
    extracted_info_path = f"{output_dir}/extracted_info.json"
    report = analyzer.analyze(extracted_info_path, output_dir)
    print(f"      发现 {len(report.issues)} 个问题")
    
    print(f"[4/4] 生成报告...")
    coordinator = AnalysisCoordinator()
    report_path = f"{output_dir}/analysis_report.json"
    final_report = coordinator.coordinate(report_path, output_dir)
    print(f"      报告已保存: {final_report}")
    
    return final_report


if __name__ == "__main__":
    result = analyze_bug_report(
        bugreport_path="bugreport.zip",
        package_name="com.example.app",
        output_dir="./output"
    )
    print(f"\n分析完成！报告路径: {result}")
```

### 8.2 单独使用各 Skill

```python
from bugreport_extractor.extractor import ArchiveExtractor
from bugreport_extractor.config import ExtractorConfig

config = ExtractorConfig(
    max_depth=5,
    max_workers=2,
    max_file_size_mb=512
)
extractor = ArchiveExtractor(config)
manifest = extractor.extract("bugreport.zip", "./extracted")
```

```python
from bugreport_parser.parser import LogParser

parser = LogParser()
extracted_info = parser.parse(
    manifest_path="./extracted/manifest.json",
    package_name="com.example.app",
    output_dir="./parsed"
)
```

```python
from bugreport_analyzer.analyzer import BugAnalyzer

analyzer = BugAnalyzer()
report = analyzer.analyze(
    extracted_info_path="./parsed/extracted_info.json",
    output_dir="./analyzed"
)
```

```python
from bugreport_coordinator.coordinator import AnalysisCoordinator

coordinator = AnalysisCoordinator()
final_report = coordinator.coordinate(
    analysis_report_path="./analyzed/analysis_report.json",
    output_dir="./report"
)
```

## 9. 错误处理

| 错误类型 | 描述 | 处理方式 |
|---------|------|---------|
| `FileNotFoundError` | 源文件不存在 | 提示用户检查路径 |
| `ValueError` | 不支持的压缩格式 | 提示支持的格式列表 |
| `IOError` | 磁盘空间不足 | 提示所需空间和可用空间 |
| `MemoryError` | 内存不足 | 触发采样或降低处理批次 |
| `PermissionError` | 无写入权限 | 提示更改输出目录 |
| `json.JSONDecodeError` | JSON 解析失败 | 记录错误并跳过该文件 |

## 10. 冻结分析模式使用示例

### 10.1 模式 1：独立分析冻结异常

```python
from bugreport_parser.freeze_parser import FreezeAnalyzer
from pathlib import Path

def analyze_freezes_independent(log_dir: str):
    """独立分析冻结异常，不与其他异常关联"""
    
    analyzer = FreezeAnalyzer(analysis_mode="independent")
    
    log_dir = Path(log_dir)
    
    for log_file in log_dir.rglob("*.txt"):
        analyzer.analyze_log_file(log_file)
    
    for dumpsys_file in log_dir.rglob("*mars*"):
        analyzer.analyze_dumpsys_mars(dumpsys_file)
    
    for dumpsys_file in log_dir.rglob("*freecess*"):
        analyzer.analyze_dumpsys_freecess(dumpsys_file)
    
    freeze_analysis = analyzer.get_analysis()
    
    print(f"独立冻结分析完成:")
    print(f"  - 总冻结次数: {freeze_analysis.anomaly_summary.total_freezes}")
    print(f"  - 总解冻次数: {freeze_analysis.anomaly_summary.total_unfreezes}")
    print(f"  - 可疑应用: {freeze_analysis.anomaly_summary.suspicious_packages}")
    
    return freeze_analysis
```

### 10.2 模式 2：结合已完成的分析异常

```python
from bugreport_parser.freeze_parser import FreezeAnalyzer
from pathlib import Path

def analyze_freezes_correlated(log_dir: str, crashes: List[Dict], anrs: List[Dict]):
    """结合已完成的 Crash/ANR 分析进行关联分析"""
    
    analyzer = FreezeAnalyzer(analysis_mode="correlated")
    
    log_dir = Path(log_dir)
    
    for log_file in log_dir.rglob("*.txt"):
        analyzer.analyze_log_file(log_file)
    
    for dumpsys_file in log_dir.rglob("*mars*"):
        analyzer.analyze_dumpsys_mars(dumpsys_file)
    
    for dumpsys_file in log_dir.rglob("*freecess*"):
        analyzer.analyze_dumpsys_freecess(dumpsys_file)
    
    freeze_analysis = analyzer.get_analysis(crashes=crashes, anrs=anrs)
    
    print(f"关联冻结分析完成:")
    print(f"  - 冻结状态下 Crash: {freeze_analysis.anomaly_summary.frozen_crashes}")
    print(f"  - 冻结状态下 ANR: {freeze_analysis.anomaly_summary.frozen_anrs}")
    print(f"  - 冻结超时: {freeze_analysis.anomaly_summary.freeze_timeouts}")
    
    for event in freeze_analysis.freeze_events:
        if event.type in ['FROZEN_CRASH', 'FROZEN_ANR']:
            print(f"  - {event.type}: {event.package_name} (机制: {event.mechanism})")
    
    return freeze_analysis
```

### 10.3 完整工作流程示例

```python
def full_analysis_workflow(bugreport_path: str, package_name: str):
    """完整分析流程示例"""
    
    from bugreport_extractor.extractor import ArchiveExtractor
    from bugreport_parser.parser import LogParser
    
    output_dir = "./analysis_output"
    
    print("[1/4] 解压 Bug Report...")
    extractor = ArchiveExtractor()
    manifest = extractor.extract(bugreport_path, output_dir)
    
    print("[2/4] 解析日志...")
    parser = LogParser()
    extracted_info = parser.parse(
        f"{output_dir}/manifest.json",
        package_name,
        output_dir
    )
    
    print("[3/4] 冻结分析（两种模式）...")
    
    extracted_dir = Path(output_dir) / "extracted"
    
    # 模式 1：独立分析
    print("  - 独立冻结分析...")
    analyzer_independent = FreezeAnalyzer(analysis_mode="independent")
    for log_file in extracted_dir.rglob("*.txt"):
        analyzer_independent.analyze_log_file(log_file)
    independent_result = analyzer_independent.get_analysis()
    
    # 模式 2：关联分析
    print("  - 关联冻结分析...")
    analyzer_correlated = FreezeAnalyzer(analysis_mode="correlated")
    for log_file in extracted_dir.rglob("*.txt"):
        analyzer_correlated.analyze_log_file(log_file)
    
    crashes = [vars(c) for c in extracted_info.crashes]
    anrs = [vars(c) for c in extracted_info.crashes if c.type == 'ANR']
    correlated_result = analyzer_correlated.get_analysis(crashes=crashes, anrs=anrs)
    
    print("[4/4] 完成！")
    return {
        'independent': independent_result,
        'correlated': correlated_result,
        'extracted_info': extracted_info
    }
```
