# 数据交互规范 (Data Contract)

本文档定义了 android-bugreport-analyzer 系统中各 skill 之间的数据交互格式，确保字段唯一、无歧义。

## 核心原则

1. **字段唯一性**: 每个字段有且仅有一个含义
2. **向后兼容**: 版本号机制保证兼容性
3. **独立传递**: 每个 skill 可独立运行，不依赖其他 skill 的内部状态
4. **文件驱动**: 所有数据通过 JSON 文件传递
5. **Context 保护**: 只传递文件路径，不传递大段内容，保护 AI context 窗口

## 数据流图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              数据交互流程                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  用户输入                                                                    │
│     │                                                                        │
│     ▼                                                                        │
│  ┌─────────────────┐                                                        │
│  │   用户请求解析   │  bugreport_path, package_name, analysis_mode          │
│  └────────┬────────┘                                                        │
│           │                                                                  │
│           ▼                                                                  │
│  ┌─────────────────┐     manifest.json      ┌────────────────────────────┐ │
│  │    extractor    │ ─────────────────────▶ │  文件清单 + 关键文件索引    │ │
│  └────────┬────────┘                        └────────────────────────────┘ │
│           │                                                                  │
│           ▼                                                                  │
│  ┌─────────────────┐   extracted_info.json  ┌────────────────────────────┐ │
│  │     parser      │ ─────────────────────▶ │  日志 + 崩溃 + 冻结信息     │ │
│  └────────┬────────┘                        └────────────────────────────┘ │
│           │                                                                  │
│           ▼                                                                  │
│  ┌─────────────────┐   analysis_report.json ┌────────────────────────────┐ │
│  │    analyzer     │ ─────────────────────▶ │  问题 + 原因 + 建议        │ │
│  └────────┬────────┘                        └────────────────────────────┘ │
│           │                                                                  │
│           ▼                                                                  │
│  ┌─────────────────┐     final_report.md    ┌────────────────────────────┐ │
│  │   coordinator   │ ─────────────────────▶ │  人类可读报告              │ │
│  └─────────────────┘                        └────────────────────────────┘ │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 1. manifest.json (Extractor 输出)

**用途**: 记录解压后的文件清单和关键文件位置

```json
{
  "version": "1.0",
  "extracted_at": "2024-01-15T10:30:00",
  "source_file": "/path/to/bugreport.zip",
  "extraction_stats": {
    "total_files": 150,
    "total_size": "256.5MB",
    "extraction_time": "12.3s",
    "max_depth_reached": 3,
    "compressed_size": "85.2MB",
    "compression_ratio": 3.0
  },
  "file_tree": [
    {
      "path": "FS/data/anr",
      "type": "directory",
      "files": [
        {"name": "anr_2024-01-15-10-00-00.txt", "size": "1.2MB", "type": "anr_trace"}
      ]
    }
  ],
  "key_files": {
    "logcat": "FS/data/logcat.txt",
    "dumpstate": "FS/data/dumpstate.txt",
    "anr_dir": "FS/data/anr",
    "tombstone_dir": "FS/data/tombstones",
    "dropbox_dir": "FS/data/dropbox"
  }
}
```

**字段说明**:

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| version | string | 是 | 数据格式版本号 |
| extracted_at | string | 是 | 解压时间 (ISO 8601) |
| source_file | string | 是 | 源文件路径 |
| extraction_stats | object | 是 | 解压统计信息 |
| file_tree | array | 是 | 文件树结构 |
| key_files | object | 是 | 关键文件路径映射 |

## 2. extracted_info.json (Parser 输出)

**用途**: 存储解析后的日志、崩溃、冻结等关键信息

```json
{
  "version": "1.0",
  "extracted_at": "2024-01-15T10:31:00",
  "target_app": {
    "package_name": "com.example.app",
    "uids": [10123]
  },
  "extraction_stats": {
    "total_files_processed": 45,
    "total_lines_scanned": 1250000,
    "processing_time": "45.2s",
    "memory_peak": "512MB"
  },
  "sampling": {
    "applied": true,
    "trigger_reason": "file_size_exceeded_500MB",
    "original_size": "1.2GB",
    "sampled_size": "400MB",
    "compression_ratio": 3
  },
  "deduplication": {
    "original_count": 500000,
    "deduplicated_count": 150000,
    "dedup_stats": {
      "exact_duplicates": 200000,
      "pattern_duplicates": 100000,
      "stack_duplicates": 50000
    }
  },
  "summary": {
    "total_entries": 150000,
    "time_range": {
      "start": "01-15 10:00:00.000",
      "end": "01-15 10:30:00.000"
    }
  },
  "crashes": [
    {
      "type": "ANR",
      "timestamp": "01-15 10:15:30.500",
      "reason": "Input dispatching timed out",
      "pid": 12345,
      "occurrence_count": 1,
      "context_id": "anr_001",
      "stack_summary": {
        "top_frames": ["android.os.Handler.dispatchMessage", "com.example.app.MainActivity$1.run"],
        "total_frames": 25,
        "uri": "file://resources/stacks/anr_001_stack.txt"
      }
    }
  ],
  "errors": [
    {
      "level": "ERROR",
      "tag": "ExampleTag",
      "message_summary": "Something went wrong...",
      "timestamp": "01-15 10:15:31.000",
      "occurrence_count": 5,
      "detail_uri": "file://resources/errors/error_001.log"
    }
  ],
  "warnings": [],
  "performance_issues": [
    {
      "type": "GC_OVERHEAD",
      "summary": "Frequent GC detected, 50 times",
      "impact": "MEDIUM",
      "detail_uri": null
    }
  ],
  "freeze_analysis": {
    "analysis_mode": "correlated",
    "freeze_events": [
      {
        "id": "freeze_001",
        "timestamp": "01-15 10:14:00.000",
        "type": "FREEZE",
        "package_name": "com.example.app",
        "uid": 10123,
        "pid": 12345,
        "mechanism": "Mars",
        "reason": "bg_check",
        "duration_seconds": 120,
        "related_crash_id": "anr_001",
        "related_anr_id": null,
        "detail_uri": "file://resources/freeze/freeze_001.log"
      }
    ],
    "mars_info": {
      "current_frozen_packages": ["com.example.app", "com.other.app"],
      "history_count": 15,
      "restriction_policies": ["bg_check", "idle"],
      "detail_uri": null
    },
    "freecess_info": {
      "frozen_processes": [12345, 12346],
      "detail_uri": null
    },
    "anomaly_summary": {
      "total_freezes": 10,
      "total_unfreezes": 8,
      "frozen_crashes": 2,
      "frozen_anrs": 1,
      "freeze_timeouts": 0,
      "suspicious_packages": ["com.example.app"]
    }
  },
  "resource_index": {
    "base_path": "./output/resources",
    "files": {
      "stacks_dir": "stacks/",
      "contexts_dir": "contexts/",
      "patterns_dir": "patterns/"
    }
  }
}
```

**字段说明**:

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| version | string | 是 | 数据格式版本号 |
| target_app | object | 是 | 目标应用信息 |
| crashes | array | 是 | 崩溃/ANR 列表 |
| errors | array | 是 | 错误日志列表 |
| freeze_analysis | object | 否 | 冻结分析结果 (可选) |

## 3. analysis_report.json (Analyzer 输出)

**用途**: 存储分析后的问题、原因和建议

```json
{
  "version": "1.0",
  "analyzed_at": "2024-01-15T10:32:00",
  "issues": [
    {
      "id": "ISSUE-001",
      "type": "ANR",
      "severity": "HIGH",
      "confidence": 0.85,
      "title": "ANR detected in MainActivity",
      "description": "ANR occurred due to input dispatching timeout",
      "possible_causes": [
        {
          "rank": 1,
          "priority_score": 0.92,
          "type": "BLOCKING_IO",
          "description": "Main thread blocked on I/O operation",
          "location": "com.example.app.MainActivity.onCreate",
          "stack_trace": "android.os.Handler.dispatchMessage...",
          "evidence": ["File read operation on main thread"],
          "confidence": 0.9,
          "severity": "HIGH",
          "frequency": "OFTEN",
          "fix_complexity": "SIMPLE"
        }
      ],
      "primary_cause": {},
      "timeline": [
        {"time": "01-15 10:14:00", "event": "App frozen by Mars"},
        {"time": "01-15 10:15:30", "event": "ANR detected"}
      ],
      "impact": {
        "user_visible": true,
        "affected_users": "All background users",
        "frequency": "OFTEN"
      },
      "suggestions": [
        {
          "priority": 1,
          "action": "Move I/O operation to background thread",
          "target_cause_rank": 1,
          "code_example": "Use AsyncTask or Coroutines"
        }
      ],
      "freeze_info": {
        "freeze_event_id": "freeze_001",
        "freeze_mechanism": "Mars",
        "freeze_reason": "bg_check",
        "time_from_freeze_to_crash_seconds": 90.5
      }
    }
  ],
  "needs_deeper_analysis": false,
  "additional_files_needed": []
}
```

**字段说明**:

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| issues | array | 是 | 问题列表 |
| issues[].id | string | 是 | 问题唯一标识 (格式: ISSUE-NNN) |
| issues[].type | string | 是 | 问题类型 (ANR/CRASH/PERFORMANCE/FROZEN_CRASH/FROZEN_ANR) |
| issues[].severity | string | 是 | 严重程度 (CRITICAL/HIGH/MEDIUM/LOW) |
| issues[].confidence | float | 是 | 置信度 (0.0-1.0) |
| issues[].freeze_info | object | 否 | 冻结相关信息 (仅冻结问题) |

## 4. 分析模式 (Analysis Mode)

系统支持以下分析模式:

| 模式 | 触发关键词 | 说明 |
|------|-----------|------|
| `full` | "分析bug", "分析bugreport", "完整分析" | 完整分析流程，输出所有问题 |
| `freeze` | "分析冻结", "冻结问题", "freeze分析" | 冻结专项分析，重点输出冻结相关问题 |
| `plm_issue` | "分析plm issue", "plm问题" | PLM Issue 分析 |
| `quick` | "快速分析", "只解析", "单步分析" | 单步操作，可指定具体模块 |

## 5. 问题类型枚举

### 5.1 问题类型 (Issue Type)

| 类型 | 分类 | 说明 |
|------|------|------|
| ANR | crash | 应用无响应 |
| CRASH | crash | 应用崩溃 |
| PERFORMANCE | performance | 性能问题 |
| FROZEN_CRASH | freeze | 冻结状态下崩溃 |
| FROZEN_ANR | freeze | 冻结状态下 ANR |
| FREEZE_TIMEOUT | freeze | 冻结操作超时 |

### 5.2 严重程度 (Severity)

| 级别 | 值 | 说明 |
|------|-----|------|
| CRITICAL | 4 | 严重问题，需立即处理 |
| HIGH | 3 | 高优先级问题 |
| MEDIUM | 2 | 中等优先级问题 |
| LOW | 1 | 低优先级问题 |

### 5.3 冻结机制 (Freeze Mechanism)

| 机制 | 说明 |
|------|------|
| Mars | 小米 Mars 冻结机制 |
| Freecess | Freecess 冻结机制 |
| Freezer | Android 原生 Freezer |

## 6. 错误处理

每个 skill 在遇到错误时应:

1. **不中断流程**: 尽可能继续处理，记录错误
2. **输出错误信息**: 在输出 JSON 中添加 `errors` 字段
3. **保持格式一致**: 即使出错也要输出符合规范的 JSON

```json
{
  "version": "1.0",
  "errors": [
    {
      "stage": "parser",
      "message": "Failed to parse tombstone file",
      "file": "FS/data/tombstones/tombstone_01",
      "recoverable": true
    }
  ]
}
```

## 7. 版本兼容性

- **主版本号变更**: 不兼容的数据格式变更
- **次版本号变更**: 新增字段，向后兼容
- **修订号变更**: Bug 修复，完全兼容

当前版本: `1.0`

## 8. Context 窗口保护规范

### 8.1 设计原则

**核心目标**: 确保 AI Agent 的 context 窗口不会被撑爆，保持推理能力。

```
原始数据 (1-2GB)  →  处理后数据 (< 1MB)
     ↓                      ↓
  完整日志              摘要 + URI
  完整堆栈              前3行 + URI
  所有错误              统计 + 样本
```

### 8.2 存储策略

| 内容类型 | 存储方式 | Context 占用 |
|---------|---------|-------------|
| 统计信息 | 直接存储 | 低 |
| 时间戳 | 直接存储 | 低 |
| 摘要描述 | 直接存储 (限100字符) | 低 |
| 堆栈信息 | 前3行 + URI | 低 |
| 完整日志 | 仅 URI | 极低 |
| 错误消息 | 前100字符 + URI | 低 |
| 大段文本 | URI + 行号范围 | 极低 |

### 8.3 URI 格式规范

```
file://<path>                    # 文件路径
file://<path>#L<start>-L<end>    # 行范围
file://<path>#<anchor>           # 锚点位置
```

**示例**:
```json
{
  "stack_uri": "file://resources/stacks/anr_001_stack.txt#L1-L45",
  "detail_uri": "file://resources/contexts/anr_001.log"
}
```

### 8.4 采样触发条件

| 条件 | 阈值 | 动作 |
|------|------|------|
| 文件大小 | > 500MB | 启动智能采样 |
| 条目数量 | > 100,000 | 启动智能采样 |
| 输出 JSON | > 10MB | 压缩采样 |

### 8.5 采样保留规则

| 数据类型 | 保留比例 | 说明 |
|---------|---------|------|
| ANR/Crash/Error | 100% | 关键事件全保留 |
| 关键事件前后30秒 | 100% | 上下文完整保留 |
| 高频模式日志 | 10% | 相同模式只保留样本 |
| INFO/DEBUG日志 | 5% | 均匀采样 |
| 完全重复日志 | 0% | 丢弃，记录计数 |

### 8.6 Context 大小限制

**重要**: 以下限制基于主流 LLM 的 context 窗口安全使用范围 (约 20%)

| 模型 | Context 窗口 | 本系统限制 |
|------|-------------|-----------|
| GPT-4 Turbo | 128K tokens (~96KB) | **< 20KB** |
| Claude 3 | 200K tokens (~150KB) | **< 30KB** |
| Gemini 1.5 Pro | 1M tokens (~750KB) | **< 150KB** |

**推荐配置**:

| 文件 | 最大大小 | 超出处理 |
|------|---------|---------|
| manifest.json | **10KB** | 精简文件树 |
| extracted_info.json | **50KB** | 加强采样 |
| analysis_report.json | **20KB** | 精简描述 |
| **总计** | **< 80KB** | 约等于 20K-40K tokens |

### 8.7 主流 Agent 兼容性

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    主流 Agent Context 兼容性                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  本系统输出 (< 80KB)                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  ████████████████████████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │   │
│  │  ←─────────────────── 80KB ───────────────────→                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  GPT-4 Turbo (128K tokens ≈ 96KB)                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  ████████████████████████████████████████████████████████████████████│   │
│  │  ←───────────────────────── 96KB ────────────────────────────────→  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│  ✅ 兼容 (占用约 83%)                                                        │
│                                                                              │
│  Claude 3 (200K tokens ≈ 150KB)                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  ████████████████████████████████████████████████████████████████████│   │
│  │  ←─────────────────────────────────── 150KB ──────────────────────→ │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│  ✅ 兼容 (占用约 53%)                                                        │
│                                                                              │
│  Gemini 1.5 Pro (1M tokens ≈ 750KB)                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  ████████████████████████████████████████████████████████████████████│   │
│  │  ←──────────────────────────────────────── 750KB ──────────────────→│   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│  ✅ 完全兼容 (占用约 11%)                                                    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 8.7 按需读取机制

```
┌─────────────────────────────────────────────────────────────┐
│                    按需读取流程                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. AI 使用摘要信息进行初步推理                              │
│     ↓                                                        │
│  2. 如需详细信息，通过 URI 读取文件                          │
│     ↓                                                        │
│  3. 读取 → 处理 → 立即释放                                   │
│     ↓                                                        │
│  4. 不将详细内容保留在 context 中                            │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**代码示例**:
```python
# 读取详情后立即处理，不保留
def analyze_issue(issue):
    # 使用摘要信息
    if need_more_details(issue):
        # 临时读取
        details = read_uri(issue.detail_uri)
        # 处理
        result = process(details)
        # 立即释放，不保留在 context
        del details
        return result
    return quick_analyze(issue)
```
