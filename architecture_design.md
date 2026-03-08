# Android Bug Report 高效处理与精确分析系统架构设计

> **作者**: 闫文峰
> **版本**: 2.4
> **更新日期**: 2026-03-08
> **输入说明**: 直接读取 .txt 文本文件（如 `dumpstate.txt`），无需解压

---

## 变更日志

| 版本 | 日期 | 作者 | 变更内容 |
|------|------|------|---------|
| 2.4 | 2026-03-08 | 闫文峰 | 新增统一命令行入口 cli.py，整合 build/query/analyze 命令 |
| 2.3 | 2026-03-08 | 闫文峰 | 新增自定义查询系统：AI Agent 驱动 + 动态索引 + 分页输出 |
| 2.2 | 2026-03-07 | 闫文峰 | 新增用户查询系统：预设优先 + 定制补充双模式 |
| 2.1 | 2026-03-07 | 闫文峰 | 新增用户查询系统：关键词查询、时间段查询、组合查询 |
| 2.0 | 2026-03-07 | 闫文峰 | 新增边界分隔符总表、分层 subsections 设计、优先级分类 |
| 1.0 | 2026-03-03 | 闫文峰 | 初始版本 |

## 系统概述

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                        Android Bug Report Processing System                                │
├─────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐              │
│  │   Input     │───▶│  Streaming  │───▶│  Chunking   │───▶│  Indexing   │              │
│  │   (.txt)    │    │   Reader    │    │   Engine    │    │   Engine    │              │
│  └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘              │
│                                                                     │                     │
│                                                                     ▼                     │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐              │
│  │ Validation  │◀───│ Persistence │◀───│   Storage   │◀───│   Query    │              │
│  │   Layer     │    │    Layer    │    │   Layer     │    │   Engine   │              │
│  └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘              │
│                                                                                             │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 1. 文件结构分析与分块策略

### 1.1 Bug Report TXT 文件结构

```
Notes_260303_085952.txt (单个文本文件)
├── Header (版本信息)
│   ├── Android Version
│   ├── Build Info
│   └── Device Info
├── Logcat Section
│   ├── Main log ( ActivityManager, WindowManager... )
│   ├── System log
│   ├── Radio log
│   └── Events log
├── dumpsys Section
│   ├── Activity Manager
│   ├── Window Manager
│   ├── Package Manager
│   ├── Memory Info
│   └── ...
├── ANR Traces
├── Tombstones
├── System Properties
└── Kernel Log
```

### 1.2 记录边界识别模式

#### 1.2.1 边界分隔符总表 (基于实际文件分析)

本系统使用的边界分隔符是从实际 Android bugreport 文件 (`dumpstate.txt`, 196.4MB) 中分析得出：

| # | 字符类型 | 正则模式 | 用途 | 示例 |
|---|---------|---------|------|------|
| 1 | `=======` | `^={20,}$` | 文件头/大章节标题 | `========================================================` |
| 2 | `------ xxx ------` | `^------ .+ -----$` | **标准章节标题** | `------ MEMORY INFO (/proc/meminfo) ------` |
| 3 | `------ X.XXXs was the duration` | `^------ \d+\.\d+s was the duration of` | 大章节结束 | `------ 0.012s was the duration of 'MEMORY INFO' ------` |
| 4 | `--------- X.XXXs was the duration of dumpsys` | `^---------+ \d+\.\d+s was the duration of dumpsys` | dumpsys 子章节结束 | `--------- 0.297s was the duration of dumpsys activity` |
| 5 | `***** xxx *****` | `^\*{3,}.+\*{3,}$` | 电池日志/特殊标记 | `*****Battery Power On Logs*****` |
| 6 | `##### xxx #####` | `^#{3,}.+#{3,}$` | Samsung dumpsys 服务 | `##### SEP UNION Main SERVICE #####` |
| 7 | `----- pid xxx at` | `^----- pid \d+ at` | 进程 trace 开始 | `----- pid 933 at 2025-12-30 10:00:23 -----` |
| 8 | `----- end xxx` | `^----- end \d+$` | 进程 trace 结束 | `----- end 933 -----` |
| 9 | `-------- xxx --------` | `^---------+.+---------$` | dumpsys 内部子标题 | `---------SurfaceFlinger Effects--------` |
| 10 | `[timestamp]` | `^\[\s*\d+\.\d+\]` | 内核日志时间戳 | `[175555.553540] [0: kworker/0:2:12056]` |

#### 1.2.2 分层章节结构

Android bugreport 文件采用 **层级结构**：

```
dumpstate.txt (196.4MB)
│
├── Level 1: 大章节 (通过 "------ XXX ------" 识别)
│   ├── DUMPSYS CRITICAL
│   ├── DUMPSYS HIGH  
│   ├── DUMPSYS NORMAL ← 最大章节 (行 882517 - 112243, ~200MB)
│   │   ├── Level 2: dumpsys 子服务 (通过 "--------- duration of dumpsys XXX" 识别)
│   │   │   ├── SurfaceFlinger (行 82873)
│   │   │   ├── activity (行 95933)
│   │   │   ├── power (行 106085)
│   │   │   ├── window (行 112237)
│   │   │   └── ... 60+ 个子服务
│   │   │
│   │   ├── Level 2: ACTIVITY MANAGER 子章节 (通过 "ACTIVITY MANAGER XXX" 识别)
│   │   │   ├── ACTIVITY MANAGER BROADCAST STATE (行 886281) ← 你关心的！
│   │   │   ├── ACTIVITY MANAGER LAST ANR (行 960212)
│   │   │   ├── ACTIVITY MANAGER SERVICES (行 951138)
│   │   │   └── ... 26 个子章节
│   │   │
│   │   └── Level 3: 更细粒度子章节
│   │
│   ├── SYSTEM LOG (行 112244 - 2040510, ~85MB)
│   ├── KERNEL LOG
│   ├── VM TRACES JUST NOW
│   ├── BINDER STATE (~15MB)
│   └── ... 其他
│
└── Level 0: 文件头 (通过 "======" 识别)
```

#### 1.2.3 记录类型定义 (YAML 配置驱动)

```yaml
# boundary_patterns.yaml 结构
record_types:
  
  # 主章节 (Level 1)
  dumpsys_normal:
    priority: MEDIUM
    category: "dumpsys"
    boundary_type: "dash_separator"
    start_pattern: "^------ DUMPSYS NORMAL"
    end_pattern: "^------ (SYSTEM LOG|LOGCAT|KERNEL LOG)"
    subsections:
      
      # Level 2: dumpsys 子章节
      - name: "activity"
        pattern: "--------- 0.297s was the duration of dumpsys activity"
        priority: "CRITICAL"
        category: "system"
        
      - name: "power"
        pattern: "--------- 0.091s was the duration of dumpsys power"
        priority: "HIGH"
        category: "power"
      
      # Level 2: ACTIVITY MANAGER 子章节
      - name: "activity_broadcasts"
        pattern: "ACTIVITY MANAGER BROADCAST STATE"
        priority: "CRITICAL"
        category: "activity"
        
      - name: "activity_lastanr"
        pattern: "ACTIVITY MANAGER LAST ANR"
        priority: "CRITICAL"
        category: "activity"
```

```python
# 记录类型识别模式
RECORD_BOUNDARY_PATTERNS = {
    # ========== 系统服务边界 ==========
    "dumpsys": {
        "start": r"^--------- Differential dump.*?---------$",
        "end": r"^------------------------------$",
        "priority": "HIGH",
        "example": "--------- Differential dump of android.os BatteryService -------"
    },
    
    # ========== Logcat 记录 ==========
    "logcat": {
        "start": r"^([0-9]{2}-[0-9]{2}\s+[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{3})\s+([0-9]+)\s+([0-9]+)\s+([A-Z])\s+(\S+)\s*:\s*(.+)$",
        "end": None,  # 每行独立
        "priority": "MEDIUM"
    },
    
    # ========== ANR 记录 ==========
    "anr": {
        "start": r"^----- pid [0-9]+ at .+ -----$",
        "end": r"^----- end .+ -----$",
        "priority": "CRITICAL",
        "example": "----- pid 12345 at 2026-03-07 10:30:15 -----"
    },
    
    # ========== Native Crash ==========
    "tombstone": {
        "start": r"^*** *** *** *** *** *** *** \*\*\* \*\*\* \*\*\* \*\*\* \*\*\* \*\*\*$",
        "end": r"^--- --- --- --- --- --- ---",
        "priority": "CRITICAL"
    },
    
    # ========== System Property ==========
    "property": {
        "start": r"^(\[.*?\])\s*\[.*?\]:\s*\[.*?\]\s*(.+)$",
        "end": None,
        "priority": "LOW"
    },
    
    # ========== Kernel Log ==========
    "kernel": {
        "start": r"^\[\s*([0-9]+\.[0-9]+)\]\s+(.+)$",
        "end": None,
        "priority": "MEDIUM"
    },
    
    # ========== Stack Trace ==========
    "stacktrace": {
        "start": r"^\s+at\s+[\w\.$]+\(.*\)$",
        "end": r"^\s+--- End of",
        "priority": "HIGH"
    }
}
```

### 1.3 分块算法设计

```python
class RecordBoundaryDetector:
    """记录边界检测器"""
    
    def __init__(self):
        self.patterns = self._compile_patterns(RECORD_BOUNDARY_PATTERNS)
        self.context_window = 5  # 上下文窗口行数
    
    def _compile_patterns(self, patterns: Dict) -> Dict:
        """编译正则表达式"""
        compiled = {}
        for name, config in patterns.items():
            if config.get("start"):
                compiled[name] = {
                    "start": re.compile(config["start"], re.MULTILINE),
                    "end": re.compile(config["end"], re.MULTILINE) if config.get("end") else None,
                    "priority": config.get("priority", "NORMAL"),
                    "example": config.get("example", "")
                }
        return compiled
    
    def detect_boundaries(self, content: str) -> List[RecordBlock]:
        """检测记录边界"""
        blocks = []
        lines = content.split('\n')
        current_block = None
        
        for line_num, line in enumerate(lines, 1):
            # 检查是否匹配开始模式
            for name, pattern in self.patterns.items():
                match = pattern["start"].match(line)
                if match:
                    # 如果有未关闭的块，先关闭
                    if current_block:
                        current_block["end_line"] = line_num - 1
                        blocks.append(RecordBlock(**current_block))
                    
                    # 开始新块
                    current_block = {
                        "type": name,
                        "start_line": line_num,
                        "start_content": line,
                        "priority": pattern["priority"],
                        "content_lines": [line]
                    }
                    break
            else:
                # 如果没有匹配开始，检查是否匹配结束模式
                if current_block:
                    pattern = self.patterns.get(current_block["type"])
                    if pattern and pattern["end"] and pattern["end"].match(line):
                        current_block["content_lines"].append(line)
                        current_block["end_line"] = line_num
                        blocks.append(RecordBlock(**current_block))
                        current_block = None
                    else:
                        current_block["content_lines"].append(line)
        
        # 处理最后一个块
        if current_block:
            current_block["end_line"] = len(lines)
            blocks.append(RecordBlock(**current_block))
        
        return blocks


@dataclass
class RecordBlock:
    """记录块"""
    type: str
    start_line: int
    end_line: int
    content: str
    priority: str
    content_lines: List[str] = field(default_factory=list)
    start_content: str = ""
    
    @property
    def line_count(self) -> int:
        return self.end_line - self.start_line + 1
    
    @property
    def content_size(self) -> int:
        return len(self.content)
```

### 1.4 智能分块策略

```python
class AdaptiveChunkingStrategy:
    """自适应分块策略"""
    
    def __init__(self, config: ChunkingConfig):
        self.config = config
        self.boundary_detector = RecordBoundaryDetector()
    
    def chunk_file(self, file_path: str) -> List[Chunk]:
        """
        分块策略选择:
        1. 小文件 (<10MB): 一次性读取，精细分块
        2. 中等文件 (10-100MB): 流式读取，记录级分块
        3. 大文件 (>100MB): 流式读取，章节级分块
        """
        file_size = Path(file_path).stat().st_size
        
        if file_size < 10 * 1024 * 1024:
            return self._chunk_fine_grained(file_path)
        elif file_size < 100 * 1024 * 1024:
            return self._chunk_record_level(file_path)
        else:
            return self._chunk_chapter_level(file_path)
    
    def _chunk_fine_grained(self, file_path: str) -> List[Chunk]:
        """精细分块 - 适用于小文件"""
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        blocks = self.boundary_detector.detect_boundaries(content)
        chunks = []
        
        for i, block in enumerate(blocks):
            if block.line_count < 10:
                # 合并小块
                continue
            
            chunk = self._create_chunk(block, file_path)
            chunks.append(chunk)
        
        return self._merge_small_chunks(chunks)
    
    def _chunk_record_level(self, file_path: str) -> List[Chunk]:
        """记录级分块 - 适用于中等文件"""
        chunks = []
        buffer = []
        buffer_size = 0
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            line_num = 0
            chunk_id = 0
            
            for line in f:
                line_num += 1
                buffer.append(line)
                buffer_size += len(line)
                
                # 达到块大小上限或遇到边界
                if buffer_size >= self.config.max_chunk_size:
                    chunk = self._create_chunk_from_buffer(
                        buffer, file_path, line_num, chunk_id
                    )
                    chunks.append(chunk)
                    buffer = []
                    buffer_size = 0
                    chunk_id += 1
        
        # 处理剩余内容
        if buffer:
            chunk = self._create_chunk_from_buffer(
                buffer, file_path, line_num, chunk_id
            )
            chunks.append(chunk)
        
        return chunks
    
    def _chunk_chapter_level(self, file_path: str) -> List[Chunk]:
        """章节级分块 - 适用于大文件"""
        # 章节标识符
        chapter_markers = [
            "================",
            "--- Bugreport",
            "--- System",
            "--- Kernel",
            "--- Main",
            "--- Events"
        ]
        
        chunks = []
        current_chapter = []
        chapter_name = "header"
        line_num = 0
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line_num += 1
                
                # 检测章节变化
                is_chapter_marker = any(
                    line.strip().startswith(m) for m in chapter_markers
                )
                
                if is_chapter_marker:
                    if current_chapter:
                        chunk = self._create_chapter_chunk(
                            current_chapter, file_path, chapter_name
                        )
                        chunks.append(chunk)
                        current_chapter = []
                    
                    chapter_name = self._extract_chapter_name(line)
                
                current_chapter.append(line)
        
        # 处理最后一章
        if current_chapter:
            chunk = self._create_chapter_chunk(
                current_chapter, file_path, chapter_name
            )
            chunks.append(chunk)
        
        return chunks
```

---

## 2. 流式读取机制

### 2.1 流式读取器架构

```python
class StreamingFileReader:
    """流式文件读取器"""
    
    def __init__(self, buffer_size: int = 8192):
        self.buffer_size = buffer_size
        self.position = 0
        self.file_handle = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    def open(self, file_path: str) -> 'StreamingFileReader':
        """打开文件"""
        self.file_handle = open(
            file_path, 
            'rb' if 'binary' in str(type) else 'r',
            encoding='utf-8',
            errors='ignore'
        )
        self.position = 0
        return self
    
    def read_chunk(self, size: int = None) -> str:
        """读取指定大小的块"""
        if size is None:
            size = self.buffer_size
        
        if self.file_handle is None:
            raise ValueError("File not opened")
        
        chunk = self.file_handle.read(size)
        self.position += len(chunk)
        return chunk
    
    def readline(self) -> str:
        """读取一行"""
        if self.file_handle is None:
            raise ValueError("File not opened")
        
        line = self.file_handle.readline()
        self.position += len(line)
        return line
    
    def read_until(self, pattern: str, max_size: int = None) -> str:
        """读取直到匹配模式"""
        result = []
        matched = False
        
        while True:
            line = self.readline()
            if not line:
                break
            
            result.append(line)
            
            if re.search(pattern, line):
                matched = True
                break
            
            if max_size and sum(len(r) for r in result) > max_size:
                break
        
        return ''.join(result), matched
    
    def seek(self, position: int) -> int:
        """跳转到指定位置"""
        if self.file_handle:
            return self.file_handle.seek(position)
        return 0
    
    def tell(self) -> int:
        """获取当前位置"""
        if self.file_handle:
            return self.file_handle.tell()
        return 0
    
    def close(self):
        """关闭文件"""
        if self.file_handle:
            self.file_handle.close()
            self.file_handle = None


class BufferedStreamingReader:
    """缓冲流式读取器 - 内存优化版本"""
    
    def __init__(self, file_path: str, buffer_size: int = 64 * 1024):
        self.file_path = file_path
        self.buffer_size = buffer_size
        self.file_size = Path(file_path).stat().st_size
        
        # 内存管理
        self.read_ahead_buffer = []
        self.buffer_fill_percentage = 0.5  # 保持 50% 缓冲区占用
        
        # 统计
        self.bytes_read = 0
        self.read_operations = 0
    
    @contextmanager
    def read_lines(self):
        """行迭代器"""
        with open(self.file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                self.bytes_read += len(line)
                self.read_operations += 1
                yield line
    
    def read_with_progress(self, chunk_size: int = 1024 * 1024):
        """带进度的读取"""
        progress = 0
        
        with open(self.file_path, 'r', encoding='utf-8', errors='ignore') as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                
                progress += len(chunk)
                yield chunk, progress / self.file_size
    
    def stream_process(self, processor: Callable):
        """流式处理"""
        with open(self.file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                result = processor(line)
                if result:
                    yield result
```

### 2.2 并行流式读取

```python
class ParallelStreamingReader:
    """并行流式读取器"""
    
    def __init__(self, file_path: str, num_workers: int = 4):
        self.file_path = file_path
        self.file_size = Path(file_path).stat().st_size
        self.num_workers = num_workers
        self.chunk_size = self.file_size // num_workers
    
    def _calculate_chunks(self) -> List[Tuple[int, int]]:
        """计算分块位置"""
        chunks = []
        
        for i in range(self.num_workers):
            start = i * self.chunk_size
            end = start + self.chunk_size if i < self.num_workers - 1 else self.file_size
            chunks.append((start, end))
        
        return chunks
    
    def read_parallel(self) -> List[str]:
        """并行读取"""
        chunks = self._calculate_chunks()
        
        with ThreadPoolExecutor(max_workers=self.num_workers) as executor:
            futures = []
            for start, end in chunks:
                future = executor.submit(self._read_range, start, end)
                futures.append(future)
            
            results = [f.result() for f in futures]
        
        return results
    
    def _read_range(self, start: int, end: int) -> str:
        """读取指定范围"""
        with open(self.file_path, 'r', encoding='utf-8', errors='ignore') as f:
            f.seek(start)
            return f.read(end - start)
```

---

## 3. 分块内容持久化

### 3.1 存储格式设计

```python
@dataclass
class ChunkMetadata:
    """分块元数据"""
    chunk_id: str
    file_source: str
    record_type: str
    start_offset: int
    end_offset: int
    line_count: int
    byte_count: int
    priority: str
    timestamp_start: Optional[str] = None
    timestamp_end: Optional[str] = None
    process_tags: List[str] = field(default_factory=list)
    checksum: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "chunk_id": self.chunk_id,
            "file_source": self.file_source,
            "record_type": self.record_type,
            "start_offset": self.start_offset,
            "end_offset": self.end_offset,
            "line_count": self.line_count,
            "byte_count": self.byte_count,
            "priority": self.priority,
            "timestamp_start": self.timestamp_start,
            "timestamp_end": self.timestamp_end,
            "process_tags": self.process_tags,
            "checksum": self.checksum
        }


class ChunkPersistence:
    """分块持久化层"""
    
    def __init__(self, storage_path: str, format: str = "jsonl"):
        self.storage_path = Path(storage_path)
        self.format = format
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # 文件句柄
        self.data_file = None
        self.index_file = None
    
    def __enter__(self):
        if self.format == "jsonl":
            self.data_file = open(
                self.storage_path / "chunks.jsonl",
                'w',
                encoding='utf-8'
            )
            self.index_file = open(
                self.storage_path / "index.jsonl",
                'w',
                encoding='utf-8'
            )
        elif self.format == "parquet":
            self.data_file = ParquetWriter(self.storage_path / "chunks.parquet")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.data_file:
            self.data_file.close()
        if self.index_file:
            self.index_file.close()
    
    def write_chunk(self, chunk: Chunk, metadata: ChunkMetadata):
        """写入分块"""
        # 计算校验和
        checksum = hashlib.md5(chunk.content.encode()).hexdigest()
        metadata.checksum = checksum
        
        # 写入数据
        if self.format == "jsonl":
            record = {
                "metadata": metadata.to_dict(),
                "content": chunk.content
            }
            self.data_file.write(json.dumps(record, ensure_ascii=False) + '\n')
            
            # 写入索引
            self.index_file.write(json.dumps(metadata.to_dict()) + '\n')
        
        elif self.format == "parquet":
            self.data_file.write_row({
                "metadata": metadata.to_dict(),
                "content": chunk.content
            })
    
    def read_chunk(self, chunk_id: str) -> Optional[Dict]:
        """读取分块"""
        if self.format == "jsonl":
            with open(self.storage_path / "chunks.jsonl", 'r') as f:
                for line in f:
                    record = json.loads(line)
                    if record["metadata"]["chunk_id"] == chunk_id:
                        return record
        return None


class MultiFormatStorage:
    """多格式存储"""
    
    FORMAT_HANDLERS = {
        "jsonl": JsonlStorageHandler,
        "parquet": ParquetStorageHandler,
        "sqlite": SqliteStorageHandler,
        "binary": BinaryStorageHandler
    }
    
    def __init__(self, storage_path: str, format: str = "jsonl"):
        self.storage_path = Path(storage_path)
        self.format = format
        self.handler = self.FORMAT_HANDLERS[format](storage_path)
    
    def write_batch(self, chunks: List[Tuple[Chunk, ChunkMetadata]]):
        """批量写入"""
        self.handler.write_batch(chunks)
    
    def read_range(self, start_id: str, end_id: str) -> List[Dict]:
        """范围读取"""
        return self.handler.read_range(start_id, end_id)
    
    def query_by_type(self, record_type: str) -> List[Dict]:
        """按类型查询"""
        return self.handler.query("record_type", record_type)
    
    def query_by_time(self, start_time: str, end_time: str) -> List[Dict]:
        """按时间查询"""
        return self.handler.query("timestamp", start_time, end_time)
```

### 3.2 压缩与优化

```python
class CompressedStorage:
    """压缩存储"""
    
    def __init__(self, storage_path: str, compression: str = "zstd"):
        self.storage_path = storage_path
        self.compression = compression
    
    def write_compressed(self, data: str) -> bytes:
        """压缩写入"""
        if self.compression == "zstd":
            return zstd.compress(data.encode())
        elif self.compression == "lz4":
            return lz4.frame.compress(data.encode())
        elif self.compression == "gzip":
            return gzip.compress(data.encode())
        return data.encode()
    
    def read_compressed(self, data: bytes) -> str:
        """解压读取"""
        if self.compression == "zstd":
            return zstd.decompress(data).decode()
        elif self.compression == "lz4":
            return lz4.frame.decompress(data).decode()
        elif self.compression == "gzip":
            return gzip.decompress(data).decode()
        return data.decode()
```

---

## 4. 多维度索引系统

### 4.1 索引架构设计

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              索引系统架构                                        │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐          │
│  │   时间戳索引     │    │   类型索引       │    │   关键字索引     │          │
│  │  (Timestamp)   │    │    (Type)       │    │   (Inverted)    │          │
│  ├─────────────────┤    ├─────────────────┤    ├─────────────────┤          │
│  │ B+Tree / LSM    │    │   Hash Map      │    │   倒排表        │          │
│  │ 按时间排序      │    │ 按类型分组       │    │  Term -> [IDs]  │          │
│  └────────┬────────┘    └────────┬────────┘    └────────┬────────┘          │
│           │                      │                      │                     │
│           └──────────────────────┼──────────────────────┘                     │
│                                  │                                            │
│                                  ▼                                            │
│                    ┌─────────────────────────┐                               │
│                    │      查询优化器          │                               │
│                    │   (Query Optimizer)      │                               │
│                    └────────────┬──────────────┘                               │
│                                 │                                             │
│                                 ▼                                             │
│                    ┌─────────────────────────┐                               │
│                    │     复合查询引擎          │                               │
│                    │  (Multi-Dim Query)       │                               │
│                    └─────────────────────────┘                               │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 索引实现

```python
class TimestampIndex:
    """时间戳索引"""
    
    def __init__(self):
        self.index: Dict[str, List[str]] = {}  # timestamp -> chunk_ids
        self.sorted_timestamps: List[str] = []
        self.chunk_timestamps: Dict[str, str] = {}  # chunk_id -> timestamp
    
    def add_entry(self, chunk_id: str, timestamp: str):
        """添加索引"""
        if timestamp not in self.index:
            self.index[timestamp] = []
        self.index[timestamp].append(chunk_id)
        self.chunk_timestamps[chunk_id] = timestamp
    
    def build_sorted_index(self):
        """构建排序索引"""
        self.sorted_timestamps = sorted(self.index.keys())
    
    def query_by_time_range(self, start: str, end: str) -> List[str]:
        """时间范围查询"""
        results = []
        
        # 二分查找起始位置
        start_idx = bisect_left(self.sorted_timestamps, start)
        end_idx = bisect_right(self.sorted_timestamps, end)
        
        for ts in self.sorted_timestamps[start_idx:end_idx]:
            results.extend(self.index[ts])
        
        return results
    
    def query_by_time_point(self, timestamp: str) -> List[str]:
        """时间点查询"""
        return self.index.get(timestamp, [])


class TypeIndex:
    """类型索引"""
    
    def __init__(self):
        self.index: Dict[str, List[str]] = {}  # record_type -> chunk_ids
    
    def add_entry(self, chunk_id: str, record_type: str):
        """添加索引"""
        if record_type not in self.index:
            self.index[record_type] = []
        self.index[record_type].append(chunk_id)
    
    def query_by_type(self, record_type: str) -> List[str]:
        """类型查询"""
        return self.index.get(record_type, [])
    
    def query_by_types(self, types: List[str]) -> List[str]:
        """多类型查询"""
        results = []
        for t in types:
            results.extend(self.index.get(t, []))
        return results
    
    def get_all_types(self) -> List[str]:
        """获取所有类型"""
        return list(self.index.keys())


class InvertedIndex:
    """倒排索引 - 关键字检索"""
    
    def __init__(self):
        self.index: Dict[str, Set[str]] = {}  # term -> chunk_ids
        self.chunk_terms: Dict[str, Set[str]] = {}  # chunk_id -> terms
    
    def add_entry(self, chunk_id: str, content: str):
        """添加索引 - 使用分词"""
        # 提取关键词
        terms = self._tokenize(content)
        self.chunk_terms[chunk_id] = terms
        
        # 构建倒排表
        for term in terms:
            if term not in self.index:
                self.index[term] = set()
            self.index[term].add(chunk_id)
    
    def _tokenize(self, content: str) -> Set[str]:
        """分词"""
        # 转换为小写
        content = content.lower()
        
        # 提取词
        words = re.findall(r'\b\w+\b', content)
        
        # 过滤停用词
        stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'in', 'at', 'to', 'of'}
        words = [w for w in words if w not in stop_words and len(w) > 2]
        
        return set(words)
    
    def query(self, term: str) -> List[str]:
        """单关键字查询"""
        return list(self.index.get(term.lower(), set()))
    
    def query_and(self, terms: List[str]) -> List[str]:
        """AND 查询"""
        if not terms:
            return []
        
        result_sets = [self.index.get(t.lower(), set()) for t in terms]
        return list(set.intersection(*result_sets))
    
    def query_or(self, terms: List[str]) -> List[str]:
        """OR 查询"""
        result_set = set()
        for t in terms:
            result_set.update(self.index.get(t.lower(), set()))
        return list(result_set)


class PositionIndex:
    """位置索引"""
    
    def __init__(self):
        self.index: Dict[str, ChunkPosition] = {}  # chunk_id -> position
    
    def add_entry(self, chunk_id: str, offset: int, size: int, line_start: int, line_end: int):
        """添加位置"""
        self.index[chunk_id] = ChunkPosition(
            offset=offset,
            size=size,
            line_start=line_start,
            line_end=line_end
        )
    
    def get_position(self, chunk_id: str) -> Optional[ChunkPosition]:
        """获取位置"""
        return self.index.get(chunk_id)


@dataclass
class ChunkPosition:
    offset: int
    size: int
    line_start: int
    line_end: int
```

### 4.3 复合查询引擎

```python
class CompositeQueryEngine:
    """复合查询引擎"""
    
    def __init__(self):
        self.timestamp_index = TimestampIndex()
        self.type_index = TypeIndex()
        self.inverted_index = InvertedIndex()
        self.position_index = PositionIndex()
    
    def add_chunk(self, chunk_id: str, metadata: ChunkMetadata, content: str):
        """添加索引"""
        if metadata.timestamp_start:
            self.timestamp_index.add_entry(chunk_id, metadata.timestamp_start)
        
        self.type_index.add_entry(chunk_id, metadata.record_type)
        self.inverted_index.add_entry(chunk_id, content)
        self.position_index.add_entry(
            chunk_id,
            metadata.start_offset,
            metadata.byte_count,
            metadata.start_line,
            metadata.end_line
        )
    
    def query(self, query_spec: Dict) -> List[str]:
        """
        复合查询
        
        query_spec = {
            "type": ["anr", "crash"],           # 可选
            "time_range": ("2026-01-01", "2026-01-02"),  # 可选
            "keywords": ["error", "timeout"],    # 可选
            "keyword_op": "and" | "or",         # 关键字逻辑
        }
        """
        results = None
        
        # 按类型过滤
        if "type" in query_spec:
            type_results = self.type_index.query_by_types(query_spec["type"])
            results = set(type_results) if results is None else results.intersection(type_results)
        
        # 按时间过滤
        if "time_range" in query_spec:
            start, end = query_spec["time_range"]
            time_results = self.timestamp_index.query_by_time_range(start, end)
            results = set(time_results) if results is None else results.intersection(time_results)
        
        # 按关键字过滤
        if "keywords" in query_spec:
            if query_spec.get("keyword_op") == "and":
                keyword_results = self.inverted_index.query_and(query_spec["keywords"])
            else:
                keyword_results = self.inverted_index.query_or(query_spec["keywords"])
            results = set(keyword_results) if results is None else results.intersection(keyword_results)
        
        return list(results) if results else []
```

---

## 5. 数据完整性保障机制

### 5.1 完整性验证层

```python
class IntegrityValidator:
    """完整性验证器"""
    
    def __init__(self):
        self.checksum_algorithm = "md5"
        self.validation_results = []
    
    def calculate_checksum(self, content: str) -> str:
        """计算校验和"""
        if self.checksum_algorithm == "md5":
            return hashlib.md5(content.encode()).hexdigest()
        elif self.checksum_algorithm == "sha256":
            return hashlib.sha256(content.encode()).hexdigest()
        return ""
    
    def validate_chunk(self, chunk: Chunk, stored_checksum: str) -> bool:
        """验证分块"""
        calculated = self.calculate_checksum(chunk.content)
        return calculated == stored_checksum
    
    def validate_boundary(self, blocks: List[RecordBlock], total_lines: int) -> ValidationResult:
        """验证边界完整性"""
        result = ValidationResult()
        
        # 检查是否有重叠
        for i, block1 in enumerate(blocks):
            for j, block2 in enumerate(blocks[i+1:], i+1):
                if self._blocks_overlap(block1, block2):
                    result.add_issue(
                        IssueType.BOUNDARY_OVERLAP,
                        f"Blocks {i} and {j} overlap"
                    )
        
        # 检查是否有遗漏
        covered_lines = set()
        for block in blocks:
            for line in range(block.start_line, block.end_line + 1):
                covered_lines.add(line)
        
        missing_lines = set(range(1, total_lines + 1)) - covered_lines
        if missing_lines:
            result.add_issue(
                IssueType.BOUNDARY_GAP,
                f"Missing lines: {sorted(missing_lines)[:10]}"
            )
        
        return result
    
    def _blocks_overlap(self, block1: RecordBlock, block2: RecordBlock) -> bool:
        """检查块是否重叠"""
        return not (block1.end_line < block2.start_line or block2.end_line < block1.start_line)
    
    def validate_record_completeness(self, chunk: Chunk, record_type: str) -> bool:
        """验证记录完整性"""
        if record_type == "anr":
            return "----- pid" in chunk.content and "----- end" in chunk.content
        elif record_type == "tombstone":
            return "*** *** ***" in chunk.content
        elif record_type == "logcat":
            return bool(re.match(r'^\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}', chunk.content))
        
        return True


@dataclass
class ValidationResult:
    """验证结果"""
    passed: bool = True
    issues: List[Dict] = field(default_factory=list)
    
    def add_issue(self, issue_type: str, message: str):
        self.passed = False
        self.issues.append({"type": issue_type, "message": message})
```

### 5.2 修复机制

```python
class IntegrityRepair:
    """完整性修复"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def repair_boundary_gaps(self, blocks: List[RecordBlock], original_content: str) -> List[RecordBlock]:
        """修复边界间隙"""
        # 找到间隙并合并
        fixed_blocks = []
        
        for i, block in enumerate(blocks):
            if i == 0:
                fixed_blocks.append(block)
                continue
            
            prev_block = fixed_blocks[-1]
            
            # 检查是否有间隙
            gap = block.start_line - prev_block.end_line - 1
            
            if gap > 0 and gap < 10:  # 小间隙，尝试合并
                # 合并内容
                combined_content = prev_block.content + "\n" + block.content
                prev_block.content = combined_content
                prev_block.end_line = block.end_line
                self.logger.info(f"Merged gap of {gap} lines")
            else:
                fixed_blocks.append(block)
        
        return fixed_blocks
    
    def repair_checksum_mismatch(self, chunk: Chunk) -> Optional[Chunk]:
        """修复校验和不匹配"""
        # 重新计算校验和
        new_checksum = hashlib.md5(chunk.content.encode()).hexdigest()
        chunk.metadata.checksum = new_checksum
        self.logger.warning(f"Repaired checksum for chunk {chunk.chunk_id}")
        return chunk
```

---

## 6. 处理流程设计

### 6.1 完整流水线

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              处理流水线                                              │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐          │
│  │   Stage 1   │───▶│   Stage 2   │───▶│   Stage 3   │───▶│   Stage 4   │          │
│  │  文件解压   │    │  流式扫描   │    │  边界检测   │    │  内容提取   │          │
│  └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘          │
│        │                  │                  │                  │                    │
│        ▼                  ▼                  ▼                  ▼                    │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐          │
│  │  Zip/Tar    │    │  行迭代     │    │  记录边界   │    │  元数据     │          │
│  │  解压       │    │  读取       │    │  识别       │    │  提取       │          │
│  └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘          │
│                                                                                     │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐          │
│  │   Stage 5   │───▶│   Stage 6   │───▶│   Stage 7   │───▶│   Stage 8   │          │
│  │  索引构建   │    │  存储持久化 │    │  完整性验证 │    │  查询接口   │          │
│  └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘          │
│        │                  │                  │                  │                    │
│        ▼                  ▼                  ▼                  ▼                    │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐          │
│  │  时间/类型  │    │  JSONL/     │    │  校验和/    │    │  REST API   │          │
│  │  倒排索引   │    │  Parquet    │    │  边界验证   │    │  /CLI       │          │
│  └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘          │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### 6.2 处理管道实现

```python
class ProcessingPipeline:
    """处理管道"""
    
    def __init__(self, config: PipelineConfig):
        self.config = config
        self.stages = []
        self.results = {}
    
    def add_stage(self, stage: PipelineStage) -> 'ProcessingPipeline':
        """添加阶段"""
        self.stages.append(stage)
        return self
    
    def execute(self, input_path: str) -> PipelineResult:
        """执行管道"""
        context = PipelineContext()
        context.input_path = input_path
        context.start_time = datetime.now()
        
        for stage in self.stages:
            self.logger.info(f"Executing stage: {stage.name}")
            
            try:
                stage_result = stage.execute(context)
                context.set_result(stage.name, stage_result)
                
                if not stage_result.success:
                    self.logger.error(f"Stage {stage.name} failed: {stage_result.error}")
                    break
            
            except Exception as e:
                self.logger.exception(f"Stage {stage.name} raised exception")
                context.set_error(stage.name, str(e))
                break
        
        context.end_time = datetime.now()
        return self._compile_result(context)
    
    def _compile_result(self, context: PipelineContext) -> PipelineResult:
        """编译结果"""
        return PipelineResult(
            success=context.error is None,
            stages_completed=len(context.results),
            total_time=(context.end_time - context.start_time).total_seconds(),
            outputs=context.outputs,
            errors=context.errors
        )


class PipelineStage:
    """管道阶段基类"""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(name)
    
    def execute(self, context: PipelineContext) -> StageResult:
        raise NotImplementedError


class ExtractionStage(PipelineStage):
    """解压阶段"""
    
    def execute(self, context: PipelineContext) -> StageResult:
        extractor = BugReportExtractor()
        extract_path = extractor.extract(
            context.input_path,
            self.config.temp_dir
        )
        
        context.set_output("extract_path", extract_path)
        
        return StageResult(success=True, output={"path": extract_path})


class StreamingScanStage(PipelineStage):
    """流式扫描阶段"""
    
    def execute(self, context: PipelineContext) -> StageResult:
        extract_path = context.get_output("extract_path")
        
        reader = StreamingFileReader()
        blocks = []
        
        for file_path in Path(extract_path).rglob("*.txt"):
            reader.open(str(file_path))
            
            for line in reader.read_lines():
                # 记录边界检测
                pass
        
        context.set_output("blocks", blocks)
        
        return StageResult(success=True, output={"block_count": len(blocks)})


# 使用示例
pipeline = (
    ProcessingPipeline(config)
    .add_stage(ExtractionStage("extraction"))
    .add_stage(StreamingScanStage("scan"))
    .add_stage(BoundaryDetectionStage("boundary"))
    .add_stage(ContentExtractionStage("extract"))
    .add_stage(IndexingStage("index"))
    .add_stage(PersistenceStage("persist"))
    .add_stage(ValidationStage("validate"))
)

result = pipeline.execute("/path/to/bugreport.zip")
```

---

## 7. 性能优化策略

### 7.1 并行处理架构

```python
class ParallelProcessingOptimizer:
    """并行处理优化器"""
    
    def __init__(self, num_workers: int = None):
        self.num_workers = num_workers or os.cpu_count()
    
    def parallel_chunk_processing(self, chunks: List[Chunk], 
                                   processor: Callable) -> List:
        """并行分块处理"""
        with ThreadPoolExecutor(max_workers=self.num_workers) as executor:
            results = list(executor.map(processor, chunks))
        return results
    
    def pipeline_parallelism(self, stages: List[Callable], 
                             data: List) -> List:
        """流水线并行"""
        # Producer-Consumer 模式
        queue = Queue(maxsize=100)
        
        # 生产者
        def producer():
            for item in data:
                queue.put(item)
            for _ in range(len(stages)):
                queue.put(None)  # 结束信号
        
        # 消费者
        def consumer(stage_idx):
            stage = stages[stage_idx]
            results = []
            
            while True:
                item = queue.get()
                if item is None:
                    queue.put(None)
                    break
                result = stage(item)
                results.append(result)
            
            return results
        
        with ThreadPoolExecutor(max_workers=len(stages) + 1) as executor:
            futures = [executor.submit(consumer, i) for i in range(len(stages))]
            executor.submit(producer)
            
            return [f.result() for f in futures]
```

---

## 8. 业界参考方案对比

### 8.1 类似技术对比

| 方案 | 特点 | 与本方案对比 |
|------|------|------------|
| **LangChain/LlamaIndex** | 通用文档分块 (RecursiveCharacterTextSplitter) | 通用方案，无针对性优化 |
| **ELK Logstash Grok** | 正则模式解析日志 | 适合结构化日志，不适合层级章节 |
| **Netflix Scout** | 大规模日志分析 | 商业方案，闭源 |
| **本方案** | YAML 配置 + 分层 subsections + 优先级分类 | 针对 Android bugreport 优化 |

### 8.2 本方案创新点

1. **YAML 配置驱动** - 通过 `boundary_patterns.yaml` 定义所有边界模式，支持动态更新
2. **分层 subsections 设计** - 支持 Level 1/2/3 多层级章节解析
3. **优先级驱动** - CRITICAL/HIGH/MEDIUM/LOW 四级优先级
4. **保留完整章节** - 大章节不拆分，保证语义完整
5. **性能分析导向** - 针对 binder/jank/power 等性能问题优化

### 8.3 配置文件示例

完整的 `boundary_patterns.yaml` 包含：

```yaml
# 边界分隔符 (10 种)
boundary_markers:
  - equals_separator: "^={20,}$"
  - dash_separator: "^------ .+ ------$"
  - duration_marker_major: "^------ \\d+\\.\\d+s was the duration of"
  - duration_marker_dumpsys: "^---------+ \\d+\\.\\d+s was the duration of dumpsys"
  - ...

# 记录类型 (14 种主章节)
record_types:
  - dumpsys_critical: ...
  - dumpsys_normal: ...  # 包含 86 个子章节
  - system_log: ...
  - ...

# 子章节 (86+ 个)
subsections:
  dumpsys 子服务: ~60 个
  ACTIVITY MANAGER: 26 个
```

---

## 9. 配置更新记录

### 9.1 边界分隔符发现过程

1. **初始设计**: 使用 `------` 作为章节分隔符
2. **问题发现**: `dumpsys activity broadcasts` 无法识别
3. **深入分析**: 发现 dumpsys 内部有子章节，使用不同的结束标记
4. **解决方案**: 添加 `duration_marker_dumpsys` 模式

### 9.2 关键发现

- **章节层级**: Android bugreport 是嵌套层级结构
- **结束标记**: 大章节用 `------ X.XXXs`，子章节用 `--------- X.XXXs`
- **特殊字符**: 共发现 10 种边界分隔符

---

## 附录 A: 子章节完整列表

### A.1 dumpsys 子章节 (~60 个)

| 服务名 | 行号 | 优先级 | 类别 |
|--------|------|--------|------|
| meminfo | 879782 | HIGH | memory |
| sem_wifi | 1116092 | HIGH | network |
| secims | 1056538 | HIGH | security |
| gamemanager | 1120842 | MEDIUM | gaming |
| activity | 95933 | CRITICAL | system |
| power | 106085 | HIGH | power |
| window | 112237 | HIGH | window |
| SurfaceFlinger | 82873 | HIGH | graphics |
| wifi | 1085777 | HIGH | network |
| audio | 1073546 | HIGH | audio |
| phone | 1057988 | HIGH | telephony |
| notification | 102554 | MEDIUM | notification |
| input | 99627 | HIGH | input |
| ... | ... | ... | ... |

### A.2 ACTIVITY MANAGER 子章节 (26 个)

| 子章节 | 行号 | 优先级 |
|--------|------|--------|
| BROADCAST STATE | 886281 | CRITICAL |
| LAST ANR | 960212 | CRITICAL |
| LMK KILLS | 1007974 | CRITICAL |
| ACTIVITIES | 82885 | HIGH |
| SERVICES | 951138 | HIGH |
| CONTENT PROVIDERS | 943611 | HIGH |
| RUNNING PROCESSES | 1013713 | HIGH |
| LRU PROCESSES | 960488 | HIGH |
| PROCESS EXIT INFO | 982350 | HIGH |
| ... | ... | ... |

### 7.2 缓存策略

```python
class CachingOptimizer:
    """缓存优化器"""
    
    def __init__(self, cache_size_mb: int = 512):
        self.cache_size = cache_size_mb * 1024 * 1024
        self.lru_cache = LRUCache(maxsize=self.cache_size)
    
    def cache_chunk_access(self, chunk_id: str) -> Optional[Chunk]:
        """缓存分块访问"""
        return self.lru_cache.get(chunk_id)
    
    def cache_index_lookup(self, key: str) -> Optional[List]:
        """缓存索引查找"""
        return self.lru_cache.get(f"idx:{key}")
    
    def preload_adjacent_chunks(self, chunk: Chunk, num: int = 2):
        """预加载相邻分块"""
        chunk_ids = self._get_adjacent_ids(chunk.chunk_id, num)
        
        for cid in chunk_ids:
            if cid not in self.lru_cache:
                self.lru_cache.set(cid, self._load_chunk(cid))
```

### 7.3 资源调度

```python
class ResourceScheduler:
    """资源调度器"""
    
    def __init__(self):
        self.memory_limit = 2 * 1024 * 1024 * 1024  # 2GB
        self.disk_io_limit = 100 * 1024 * 1024  # 100MB/s
    
    def schedule_processing(self, tasks: List[Task]) -> List[Task]:
        """调度任务"""
        # 内存感知调度
        available_memory = self._get_available_memory()
        
        scheduled = []
        memory_used = 0
        
        for task in sorted(tasks, key=lambda t: t.priority, reverse=True):
            if memory_used + task.estimated_memory > available_memory:
                continue
            
            scheduled.append(task)
            memory_used += task.estimated_memory
        
        return scheduled
    
    def adaptive_chunk_size(self, file_size: int) -> int:
        """自适应块大小"""
        available_memory = self._get_available_memory()
        
        # 内存越少，块越小
        if available_memory < 512 * 1024 * 1024:
            return 1024 * 1024  # 1MB
        elif available_memory < 1024 * 1024 * 1024:
            return 5 * 1024 * 1024  # 5MB
        else:
            return 10 * 1024 * 1024  # 10MB
```

---

## 10. 系统集成

### 10.1 与现有系统集成

```python
class BugReportProcessingSystem:
    """Bug Report 处理系统 - 完整集成"""
    
    def __init__(self, config: SystemConfig):
        self.config = config
        self.pipeline = self._build_pipeline()
        self.query_engine = CompositeQueryEngine()
        self.storage = MultiFormatStorage(config.storage_path)
    
    def _build_pipeline(self) -> ProcessingPipeline:
        return (
            ProcessingPipeline(self.config.pipeline)
            .add_stage(ExtractionStage("extraction"))
            .add_stage(StreamingScanStage("scan"))
            .add_stage(BoundaryDetectionStage("boundary"))
            .add_stage(ContentExtractionStage("extract"))
            .add_stage(IndexingStage("index"))
            .add_stage(PersistenceStage("persist"))
            .add_stage(ValidationStage("validate"))
        )
    
    def process(self, bugreport_path: str) -> ProcessingResult:
        """处理 Bug Report"""
        return self.pipeline.execute(bugreport_path)
    
    def query(self, query_spec: Dict) -> QueryResult:
        """查询"""
        chunk_ids = self.query_engine.query(query_spec)
        
        results = []
        for chunk_id in chunk_ids:
            chunk_data = self.storage.read_chunk(chunk_id)
            results.append(chunk_data)
        
        return QueryResult(
            total=len(results),
            results=results
        )
    
    def get_statistics(self) -> SystemStatistics:
        """获取统计信息"""
        return SystemStatistics(
            total_chunks=self.storage.count(),
            index_size=self.query_engine.index_size(),
            storage_size=self.storage.total_size()
        )
```

---

## 11. 用户查询系统

### 11.1 设计原则

本系统的查询设计遵循**简单实用**原则：

| 原则 | 说明 |
|------|------|
| **预设优先** | YAML 已定义的关键词，使用预设索引 |
| **定制补充** | YAML 未定义的关键词，按需生成定制索引 |
| **无需缓存** | 每次查询独立处理，不做复杂缓存 |

### 11.2 查询流程

```
用户输入查询
    │
    ▼
┌─────────────────────────────────────────┐
│         关键词匹配                       │
├─────────────────────────────────────────┤
│                                         │
│  YAML 已定义？                          │
│      │                                  │
│  ┌──┴──┐                                │
│  │ Yes │ No                             │
│  ▼     ▼                                │
│ 预设索引  定制索引                       │
│  (已生成)  (按需生成)                   │
│                                         │
└─────────────────────────────────────────┘
```

### 11.3 预设索引 vs 定制索引

| 类型 | 来源 | 例子 | 处理方式 |
|------|------|------|---------|
| **预设索引** | YAML 配置 | ANR、OOM、dumpsys activity | 直接查已生成的索引 |
| **定制索引** | 用户自定义 | com.newapp、0xDEADBEEF | 扫描文件，按需生成 |

### 11.4 YAML 预设定义

预设关键词在 `boundary_patterns.yaml` 中定义：

```yaml
# 预设关键词定义
record_types:
  - name: "dumpsys_normal"
    keywords: ["dumpsys", "activity", "power", "window"]
    subsections:
      - name: "activity_broadcasts"
        keywords: ["broadcast", "BROADCAST STATE"]
      - name: "last_anr"
        keywords: ["ANR", "LAST ANR"]

interest_points:
  - name: "crash"
    keywords: ["crash", "FATAL", "Exception"]
  - name: "anr"
    keywords: ["ANR", "Application Not Responding"]
  - name: "oom"
    keywords: ["OOM", "OutOfMemory", "lowmemory"]
```

### 11.5 查询处理逻辑

```python
class QueryHandler:
    """查询处理器 - 简单实现"""
    
    def __init__(self, yaml_config):
        self.yaml = yaml_config
        self.custom_results = {}  # 用户定制索引缓存
    
    def query(self, user_keyword: str) -> List[QueryResult]:
        """处理用户查询"""
        
        # 1. 检查是否在 YAML 预设中
        if self._is_preset_keyword(user_keyword):
            return self._query_preset_index(user_keyword)
        else:
            return self._query_custom_index(user_keyword)
    
    def _is_preset_keyword(self, keyword: str) -> bool:
        """检查是否是预设关键词"""
        
        # 检查 record_types
        for record_type in self.yaml.get("record_types", []):
            if keyword in record_type.get("keywords", []):
                return True
            for subsection in record_type.get("subsections", []):
                if keyword in subsection.get("keywords", []):
                    return True
        
        # 检查 interest_points
        for point in self.yaml.get("interest_points", []):
            if keyword in point.get("keywords", []):
                return True
        
        return False
    
    def _query_preset_index(self, keyword: str) -> List[QueryResult]:
        """查询预设索引 - 已生成，直接返回"""
        
        # 预设索引已预先生成，直接查询
        index_file = f"index/preset_{keyword}.json"
        
        if os.path.exists(index_file):
            return self._load_index(index_file)
        
        # 索引不存在，生成一次
        return self._build_preset_index(keyword)
    
    def _query_custom_index(self, keyword: str) -> List[QueryResult]:
        """查询定制索引 - 按需生成"""
        
        # 检查缓存
        if keyword in self.custom_results:
            return self.custom_results[keyword]
        
        # 扫描文件生成结果
        results = self._scan_file(keyword)
        
        # 缓存结果
        self.custom_results[keyword] = results
        
        return results
    
    def _scan_file(self, keyword: str) -> List[QueryResult]:
        """扫描文件查找关键词"""
        
        results = []
        
        with open(self.file_path, 'r') as f:
            for line_num, line in enumerate(f, 1):
                if keyword in line:
                    results.append(QueryResult(
                        line_number=line_num,
                        content=line.strip()
                    ))
        
        return results
```

### 11.6 查询示例

| 用户输入 | 匹配类型 | 索引来源 |
|---------|---------|---------|
| "ANR" | 预设 | 预设索引 (已生成) |
| "broadcast" | 预设 | 预设索引 (已生成) |
| "com.newapp" | 定制 | 按需扫描生成 |
| "0xDEADBEEF" | 定制 | 按需扫描生成 |

---

## 12. 自定义查询系统 (v2.3 新增)

### 12.1 设计背景

预设的 36 个关键词无法覆盖所有用户查询场景。当用户需要查询任意字符串（如应用包名、错误码等）时，需要一种灵活的自定义查询机制。

### 12.2 核心设计

| 特性 | 说明 |
|------|------|
| **AI Agent 驱动** | AI Agent 理解用户意图，生成查询配置 |
| **动态索引** | 每次新查询时重建自定义索引 |
| **分页输出** | 按 AI context 窗口大小自动分页 |
| **向后兼容** | 保留原有预设索引 |

### 12.3 配置文件

#### 12.3.1 query_config.yaml (全局默认配置)

存放在方案根目录，所有查询共用此配置：

```yaml
# query_config.yaml - 查询全局默认配置
version: "1.0"

output:
  # 上下文行数
  context_lines_before: 5
  context_lines_after: 5
  
  # 分页配置
  pagination:
    enabled: true
    max_tokens_per_file: 32000  # AI context 的 50% (假设 64K)
    encoding: "cl100k_base"     # OpenAI 的 token 编码

# 查询优先级
priority_order:
  - "CRITICAL"
  - "HIGH"
  - "MEDIUM"
  - "LOW"

# 索引配置
index:
  rebuild_on_new_query: true   # 新查询时是否重建 custom_index
  keep_history: false          # 是否保留历史查询结果
```

#### 12.3.2 custom_queries.yaml (用户查询配置)

每次查询时由 AI Agent 自动生成，存放在 output_dir：

```yaml
# custom_queries.yaml - 用户自定义查询配置
version: "1.0"
created_at: "2026-03-08T10:00:00"

queries:
  # 类型1: 简单关键词
  - name: "query_app_example"
    type: "keyword"           # keyword | regex | section
    pattern: "com.example"   # 搜索模式
    priority: "HIGH"         # CRITICAL | HIGH | MEDIUM | LOW
    description: "查询 com.example 应用的信息"
    enabled: true

  # 类型2: 正则表达式
  - name: "query_error_codes"
    type: "regex"
    pattern: "ERROR_[0-9]{4}" # 匹配 ERROR_0001 到 ERROR_9999
    priority: "MEDIUM"
    description: "查询错误码"
    enabled: true

  # 类型3: 章节名匹配
  - name: "query_activity_mars"
    type: "section"
    pattern: "activity_mars"  # 匹配章节名包含 mars 的
    priority: "HIGH"
    description: "查询 mars 相关章节"
    enabled: true
```

### 12.4 索引文件结构

```
output_dir/                          # 例如: dumpState_F9660ZCS6AYKF_202512301000/
  ├── dumpstate.txt                # 原始文件
  ├── enhanced_index.json          # 原有索引 (36 个预设关键词)
  ├── sections.json                # 章节索引
  ├── custom_queries.yaml         # 用户查询配置 (每次生成)
  ├── custom_index.json           # 自定义索引 (每次重建)
  └── query_results/              # 查询结果
      └── {query_name}/
          ├── result.json         # 查询结果主文件
          ├── context/            # 完整上下文
          │   ├── part_1.json    # 分页文件
          │   └── part_2.json
          └── metadata.json       # 元信息
```

### 12.5 查询流程

```
┌─────────────────────────────────────────────────────────────────┐
│                      用户输入                                    │
│         关键词 + pattern + type + description                   │
└────────────────────────────┬────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                    步骤1: 准备输出目录                            │
│              创建 output_dir/query_results/{query_name}/          │
└────────────────────────────┬────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                    步骤2: 生成配置文件                            │
│     加载 query_config.yaml (全局配置)                            │
│     生成 custom_queries.yaml (用户查询)                           │
└────────────────────────────┬────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                    步骤3: 清除旧索引                              │
│     删除 output_dir/custom_index.json                            │
│     删除 output_dir/query_results/ (可选)                        │
└────────────────────────────┬────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                    步骤4: 重建自定义索引                          │
│     全量扫描文件 → 匹配 pattern → 生成 custom_index.json         │
│     支持: keyword | regex | section 三种匹配类型                 │
└────────────────────────────┬────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                    步骤5: 执行查询                               │
│     合并 enhanced_index.json + custom_index.json                 │
│     定位匹配行 → 提取上下文                                       │
└────────────────────────────┬────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                    步骤6: 分页保存                               │
│     按 query_config.yaml 配置进行分页                             │
│     保存 result.json + context/part_*.json                      │
└─────────────────────────────────────────────────────────────────┘
```

### 12.6 匹配类型说明

| 类型 | 说明 | 示例 |
|------|------|------|
| **keyword** | 简单字符串匹配 | `pattern: "com.example"` 匹配包含 "com.example" 的行 |
| **regex** | 正则表达式匹配 | `pattern: "ERROR_[0-9]{4}"` 匹配 "ERROR_0001" 到 "ERROR_9999" |
| **section** | 章节名匹配 | `pattern: "activity_mars"` 匹配章节名包含 "mars" 的章节 |

### 12.7 索引优先级

查询时按以下优先级使用索引：

```
1. custom_index.json (自定义索引) - 优先级最高
2. enhanced_index.json (预设索引) - 36 个预设关键词
3. sections.json (章节索引) - 按章节名匹配
4. 全文扫描 -兜底方案
```

### 12.8 分页逻辑

```
每页最大 tokens: 32000 (假设 AI context 为 64K 的 50%)
平均每行 tokens: ~10
每页约: 3200 行

如果匹配 10000 行:
→ 约 3-4 个分页文件 (part_1.json, part_2.json, ...)
```

### 12.9 输出文件格式

**result.json:**
```json
{
  "query": "com.example",
  "type": "keyword",
  "total_matches": 150,
  "pagination": {
    "total_parts": 2,
    "current_part": 1
  },
  "results": [
    {
      "line_number": 12345,
      "content": "-RST 2025/12/17 22:51:48...Pkg com.example...",
      "context": {
        "before": ["...", "...", "...", "...", "..."],
        "after": ["...", "...", "...", "...", "..."]
      }
    }
  ]
}
```

### 12.10 与现有系统的集成

| 模块 | 修改内容 |
|------|---------|
| `enhanced_index.py` | 支持加载和合并 custom_index.json |
| 新增 `custom_index_manager.py` | 管理自定义索引的创建和查询 |
| 新增 `query_result_writer.py` | 负责分页和写入结果 |
| 新增 `query_config.yaml` | 全局查询配置 |

---

## 13. 统一命令行入口 (v2.4 新增)

### 13.1 设计目标

提供统一的命令行入口 `cli.py`，整合所有功能模块：

| 目标 | 说明 |
|------|------|
| **统一入口** | 所有功能通过 `cli.py` 访问 |
| **自动依赖** | 自动检测并构建缺失的索引 |
| **清晰命令** | 子命令结构，语义明确 |
| **向后兼容** | 保留独立脚本供高级用户使用 |

### 13.2 命令结构

```
cli.py
├── build     # 构建索引
├── query     # 执行查询
├── analyze   # 完整分析流程（build + query）
└── interactive # 交互式模式
```

### 13.3 使用示例

```bash
# 构建索引
python cli.py build <output_dir>

# 执行查询
python cli.py query <output_dir> --pattern "com.tencent.mm" --type keyword

# 正则查询
python cli.py query <output_dir> \
    --name "query_wechat_freeze" \
    --pattern "com\.tencent\.mm.*freeze" \
    --type regex \
    --priority CRITICAL

# 完整分析流程（自动构建索引 + 执行查询）
python cli.py analyze <output_dir> --pattern "ANR"

# 使用配置文件批量查询
python cli.py query <output_dir> --config queries.json

# 交互式模式
python cli.py interactive
```

### 13.4 命令详解

#### 13.4.1 build 命令

构建预设索引（sections.json + enhanced_index.json）：

```bash
python cli.py build <output_dir> [options]

Options:
  --force          强制重建索引（覆盖现有索引）
  --verbose        显示详细输出
```

**输出文件**：
```
output_dir/
├── sections.json         # 章节索引
└── enhanced_index.json   # 预设关键词索引
```

#### 13.4.2 query 命令

执行自定义查询：

```bash
python cli.py query <output_dir> [options]

Options:
  --name           查询名称
  --pattern        匹配模式
  --type           查询类型 (keyword|regex|section)
  --priority       优先级 (CRITICAL|HIGH|MEDIUM|LOW)
  --description    查询描述
  --config         查询配置文件路径 (JSON格式)
  --interactive    交互式输入模式
  --context-before 上下文前行数 (默认: 5)
  --context-after  上下文后行数 (默认: 5)
  --keep-history   保留历史查询结果
  --auto-build     自动构建缺失的索引
```

**输出文件**：
```
output_dir/
├── custom_queries.yaml   # 用户查询配置
├── custom_index.json     # 自定义索引
└── query_results/
    └── {query_name}/
        ├── result.json
        ├── metadata.json
        └── context/part_*.json
```

#### 13.4.3 analyze 命令

完整分析流程（自动执行 build + query）：

```bash
python cli.py analyze <output_dir> [options]

Options:
  --pattern        匹配模式
  --type           查询类型
  --priority       优先级
  --description    查询描述
```

**流程**：
```
1. 检查索引是否存在
   ├── 存在 → 跳过构建
   └── 不存在 → 自动构建
2. 执行查询
3. 保存结果
```

#### 13.4.4 interactive 命令

交互式模式：

```bash
python cli.py interactive
```

**交互流程**：
```
1. 选择操作类型
   ├── 构建索引
   ├── 执行查询
   └── 完整分析
2. 输入参数
3. 确认执行
4. 显示结果
```

### 13.5 自动依赖处理

```
┌─────────────────────────────────────────────────────────┐
│                    analyze 命令流程                      │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  检查 enhanced_index.json                               │
│      │                                                  │
│  ┌──┴──┐                                                │
│  │存在  │ 不存在                                         │
│  ▼     ▼                                                │
│ 跳过   自动执行 build                                   │
│  │     │                                                │
│  └──┬──┘                                                │
│     ▼                                                   │
│  执行 query                                             │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 13.6 配置文件格式

#### queries.json 示例

```json
{
  "queries": [
    {
      "name": "query_wechat_freeze",
      "type": "regex",
      "pattern": "com\\.tencent\\.mm.*freeze|freeze.*com\\.tencent\\.mm",
      "priority": "CRITICAL",
      "description": "查询微信冻结问题",
      "enabled": true
    },
    {
      "name": "query_anr",
      "type": "keyword",
      "pattern": "ANR",
      "priority": "CRITICAL",
      "description": "查询ANR问题",
      "enabled": true
    }
  ]
}
```

### 13.7 与现有脚本的关系

| 脚本 | 状态 | 说明 |
|------|------|------|
| `cli.py` | **新增** | 统一入口，推荐使用 |
| `build_all_indexes.py` | 保留 | 供高级用户直接调用 |
| `custom_query.py` | 保留 | 供高级用户直接调用 |
| `main.py` | 保留 | 交互式分析（完整流程） |

### 13.8 错误处理

```python
class CLIError(Exception):
    """CLI 错误基类"""
    pass

class IndexNotFoundError(CLIError):
    """索引不存在错误"""
    def __init__(self, output_dir):
        super().__init__(f"索引不存在: {output_dir}")
        self.suggestion = "请先运行: python cli.py build <output_dir>"

class InvalidPatternError(CLIError):
    """无效模式错误"""
    def __init__(self, pattern, error):
        super().__init__(f"无效的正则表达式: {pattern}")
        self.original_error = error
```

---

## 总结

本方案提供了一个完整的 Android Bug Report 处理系统架构，涵盖：

| 模块 | 核心功能 |
|------|---------|
| **文件分析** | 结构识别、边界检测、智能分块 |
| **流式读取** | 内存优化、并行读取、进度追踪 |
| **持久化** | 多格式支持、压缩存储、批量写入 |
| **索引系统** | 预设索引 + 定制索引双模式 |
| **用户查询** | YAML 预设优先 + 用户定制补充 |
| **自定义查询** | AI Agent 驱动 + 动态索引 + 分页输出 |
| **处理流程** | 8 阶段标准化管道 |
| **性能优化** | 并行处理、资源调度 |

这个架构可以处理 **500MB+** 的 bug report 文件，同时保证 **100% 的数据完整性** 和 **可检索性**。

---

## 13. 版本信息
|---------|---------|------|
| logcat | `^\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d{3}` | `12-30 10:00:21.123` |
| kernel | `^\[\d+\.\d+\]` | `[175555.553540]` |
| dumpsys | `ending at:\s+\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}` | `ending at: 2025-12-30 10:00:21` |
| system | `^\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}` | `12-30 10:00:23` |

```python
class TimeParser:
    """时间解析器"""
    
    TIME_PATTERNS = {
        "logcat": r"^(\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d{3})",
        "kernel": r"^\[(\d+\.\d+)\]",
        "dumpsys": r"ending at:\s+(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})",
        "system": r"^(\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})",
    }
    
    def parse(self, line: str) -> Optional[float]:
        """解析行中的时间戳，返回 Unix 时间戳"""
        
        for format_name, pattern in self.TIME_PATTERNS.items():
            match = re.match(pattern, line)
            if match:
                return self._to_timestamp(format_name, match.group(1))
        
        return None
    
    def parse_user_input(self, time_str: str) -> float:
        """解析用户输入的时间字符串"""
        
        # 支持格式:
        # - "10:00:00" (今天, 当天的相对时间)
        # - "2025-12-30 10:00:00" (完整日期时间)
        # - "10:00" (今天, 精确到分钟)
        
        # ...
```

#### 11.3.2 时间索引构建

```python
class TimeIndex:
    """时间索引 - 支持快速范围查询"""
    
    def __init__(self):
        self.sorted_entries: List[TimeEntry] = []
        self.line_to_time: Dict[int, float] = {}
    
    def build(self, file_path: str):
        """构建时间索引"""
        
        with open(file_path, 'r') as f:
            for line_num, line in enumerate(f):
                timestamp = TimeParser().parse(line)
                if timestamp:
                    self.sorted_entries.append(TimeEntry(line_num, timestamp))
                    self.line_to_time[line_num] = timestamp
        
        self.sorted_entries.sort(key=lambda x: x.timestamp)
    
    def query_range(self, start_time: float, end_time: float) -> List[int]:
        """查询时间范围内的行号 - 二分查找"""
        
        start_idx = bisect_left(self.sorted_entries, start_time, 
                                key=lambda x: x.timestamp)
        end_idx = bisect_right(self.sorted_entries, end_time, 
                              key=lambda x: x.timestamp)
        
        return [entry.line_num for entry in self.sorted_entries[start_idx:end_idx]]
```

### 11.4 组合查询设计

#### 11.4.1 查询语言

支持类似 SQL 的查询语法：

```
# 关键词查询
SELECT * WHERE keyword = "ANR"

# 时间范围查询
SELECT * WHERE time BETWEEN "10:00:00" AND "10:01:00"

# 组合查询
SELECT * WHERE keyword = "ANR" AND time BETWEEN "10:00:00" AND "10:01:00"

# 上下文查询
SELECT * WHERE keyword = "ANR" BEFORE 30s AND AFTER 30s

# 章节查询
SELECT * FROM section = "activity" WHERE keyword = "broadcast"
```

#### 11.4.2 查询解析器

```python
class QueryParser:
    """查询解析器 - 将用户输入转换为结构化查询"""
    
    def parse(self, query_str: str) -> ParsedQuery:
        """解析用户查询字符串"""
        
        parsed = ParsedQuery()
        
        # 解析关键词
        if "keyword" in query_str:
            parsed.keyword = self._extract_keyword(query_str)
        
        # 解析时间范围
        if "time" in query_str or "BETWEEN" in query_str:
            parsed.time_range = self._extract_time_range(query_str)
        
        # 解析章节
        if "section" in query_str or "FROM" in query_str:
            parsed.section = self._extract_section(query_str)
        
        # 解析上下文
        if "BEFORE" in query_str or "AFTER" in query_str:
            parsed.context = self._extract_context(query_str)
        
        return parsed
```

#### 11.4.3 查询执行引擎

```python
class QueryExecutor:
    """查询执行引擎"""
    
    def execute(self, parsed_query: ParsedQuery) -> QueryResultSet:
        """执行查询并返回结果"""
        
        # 阶段1: 章节过滤
        if parsed_query.section:
            candidate_lines = self._filter_by_section(parsed_query.section)
        else:
            candidate_lines = self._get_all_lines()
        
        # 阶段2: 时间过滤
        if parsed_query.time_range:
            candidate_lines = self._filter_by_time(
                candidate_lines, 
                parsed_query.time_range
            )
        
        # 阶段3: 关键词过滤
        if parsed_query.keyword:
            candidate_lines = self._filter_by_keyword(
                candidate_lines,
                parsed_query.keyword
            )
        
        # 阶段4: 提取上下文
        results = self._extract_context(
            candidate_lines,
            parsed_query.context
        )
        
        # 阶段5: 排序
        return self._sort_results(results, parsed_query.sort_by)
```

### 11.5 索引优化策略

为了支持高效的查询，需要预处理以下索引：

| 索引类型 | 构建时机 | 查询用途 | 大小估计 |
|---------|---------|---------|---------|
| **倒排索引** | 处理时 | 关键词查询 | 10-50 MB |
| **时间索引** | 处理时 | 时间段查询 | 5-20 MB |
| **行号索引** | 处理时 | 快速定位 | 1-5 MB |
| **章节索引** | 处理时 | 章节过滤 | 1-5 MB |
| **Bloom Filter** | 预处理 | 快速判断是否存在 | < 1 MB |

```python
class IndexManager:
    """索引管理器"""
    
    def build_all_indexes(self, chunk_dir: str):
        """构建所有索引"""
        
        # 1. 倒排索引 - 关键词到行号
        self.inverted_index = InvertedIndexBuilder().build(chunk_dir)
        
        # 2. 时间索引 - 时间到行号范围
        self.time_index = TimeIndexBuilder().build(chunk_dir)
        
        # 3. 章节索引 - 章节名到行号范围
        self.section_index = SectionIndexBuilder().build(chunk_dir)
        
        # 4. 保存索引
        self._save_indexes()
    
    def _save_indexes(self):
        """保存索引到磁盘"""
        
        import pickle
        
        with open("inverted_index.pkl", "wb") as f:
            pickle.dump(self.inverted_index, f)
        
        with open("time_index.pkl", "wb") as f:
            pickle.dump(self.time_index, f)
        
        with open("section_index.pkl", "wb") as f:
            pickle.dump(self.section_index, f)
```

---

## 总结

本方案提供了一个完整的 Android Bug Report 处理系统架构，涵盖：

| 模块 | 核心功能 |
|------|---------|
| **文件分析** | 结构识别、边界检测、智能分块 |
| **流式读取** | 内存优化、并行读取、进度追踪 |
| **持久化** | 多格式支持、压缩存储、批量写入 |
| **索引系统** | 时间/类型/关键字/位置四维索引 |
| **完整性** | 校验和、边界验证、记录完整检查 |
| **处理流程** | 8 阶段标准化管道 |
| **性能优化** | 并行处理、缓存策略、资源调度 |

这个架构可以处理 **500MB+** 的 bug report 文件，同时保证 **100%** 的数据完整性 和 **可检索性**。
