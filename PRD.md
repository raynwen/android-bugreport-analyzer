# Android Bug Report 分析系统 - 产品需求文档 (PRD)

## 1. 项目概述

### 1.1 项目背景
在 Android 开发和 PLM 流程中，bug report 分析是一个耗时且复杂的工作。一个典型的 Android bug report 压缩包可能包含数百个文件，大小从几十 MB 到几 GB 不等。开发人员需要从中提取关键信息，分析问题根因，这需要丰富的经验和大量时间。

### 1.2 项目目标
构建一个基于 AI Agent 的 Android Bug Report 自动分析系统，通过多个专业化的 Skills 协作，实现：
- 自动解压和遍历复杂的压缩文件结构
- 智能提取关键信息，控制上下文膨胀
- 多轮推理分析，生成专业的问题诊断报告
- 提供可操作的建议和解决方案

### 1.3 核心设计原则
1. **上下文最小化**: 每个 Skill 只保留必要的上下文信息传递给下一个
2. **格式化输出**: 所有中间结果使用 JSON 格式，便于解析和传递
3. **流式处理**: 大文件采用流式读取，避免内存溢出
4. **可复用性**: 每个 Skill 独立完整，可被其他场景复用
5. **自我配置**: Skills 具备环境检测和自动配置能力
6. **Context 窗口保护**: 只传递文件路径，不传递大段内容，确保 AI Agent 推理能力不下降

## 2. 系统架构

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    Android Bug Report Analysis System                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│    ┌─────────────┐                                                       │
│    │ Bug Report  │                                                       │
│    │   .zip/.gz  │                                                       │
│    └──────┬──────┘                                                       │
│           │                                                              │
│           ▼                                                              │
│    ┌─────────────────────────────────────────────────────────────────┐  │
│    │                     Skill 1: Extractor                          │  │
│    │  - 递归解压所有嵌套压缩文件                                       │  │
│    │  - 生成文件清单和元数据                                          │  │
│    │  - 输出: manifest.json                                          │  │
│    └──────────────────────────┬──────────────────────────────────────┘  │
│                               │                                          │
│                               ▼                                          │
│    ┌─────────────────────────────────────────────────────────────────┐  │
│    │                     Skill 2: Parser                             │  │
│    │  - 流式读取大文件                                                │  │
│    │  - 关键词提取和过滤                                              │  │
│    │  - 输出: extracted_info.json                                    │  │
│    └──────────────────────────┬──────────────────────────────────────┘  │
│                               │                                          │
│                               ▼                                          │
│    ┌─────────────────────────────────────────────────────────────────┐  │
│    │                     Skill 3: Analyzer                           │  │
│    │  - 问题类型识别                                                  │  │
│    │  - 根因分析推理                                                  │  │
│    │  - 输出: analysis_report.json                                   │  │
│    └──────────────────────────┬──────────────────────────────────────┘  │
│                               │                                          │
│                               ▼                                          │
│    ┌─────────────────────────────────────────────────────────────────┐  │
│    │                     Skill 4: Coordinator                        │  │
│    │  - 迭代优化分析 (最多3轮)                                         │  │
│    │  - 生成最终报告                                                  │  │
│    │  - 输出: final_report.md                                        │  │
│    └─────────────────────────────────────────────────────────────────┘  │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 数据流向

```
Bug Report → manifest.json → extracted_info.json → analysis_report.json → final_report.md
   (zip)       (文件清单)      (提取的信息)          (分析结果)            (最终报告)
```

## 3. Skills 详细设计

### 3.1 Skill 1: Extractor (解压遍历)

#### 3.1.1 功能描述
递归解压所有嵌套的压缩文件，生成完整的文件清单和元数据。

#### 3.1.2 输入输出
| 项目 | 描述 |
|-----|------|
| 输入 | Bug Report 压缩包路径 |
| 输出 | `manifest.json` - 文件清单和元数据 |

#### 3.1.3 核心功能
- 支持格式: `.zip`, `.tar.gz`, `.tgz`, `.gz`, `.bz2`
- **磁盘空间预检查**: 解压前检查可用空间，要求预留压缩包大小 3-5 倍的空间
- **递归解压嵌套压缩包**: 最大深度限制 10 层，防止 zip bomb 攻击
- **并发解压控制**: 默认 4 线程，可根据磁盘类型配置（SSD 可增加，HDD 建议 2 线程）
- **安全限制**: 单文件大小限制 1GB，总解压大小限制 10GB
- 检测文件编码
- 生成文件树结构
- 记录文件大小、修改时间等元数据

#### 3.1.4 配置参数
| 参数 | 默认值 | 说明 |
|-----|-------|------|
| `max_depth` | 10 | 递归解压最大深度 |
| `max_workers` | 4 | 并发解压线程数 |
| `max_file_size` | 1GB | 单文件大小上限 |
| `max_total_size` | 10GB | 总解压大小上限 |
| `space_multiplier` | 3 | 磁盘空间预留倍数 |

#### 3.1.5 依赖清单 (requirements.txt)
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

#### 3.1.6 输出格式 (manifest.json)
```json
{
  "version": "1.0",
  "extracted_at": "2026-03-01T10:00:00Z",
  "source_file": "bugreport.zip",
  "extraction_stats": {
    "total_files": 150,
    "total_size": "256MB",
    "extraction_time": "12.5s",
    "max_depth_reached": 3,
    "compressed_size": "85MB",
    "compression_ratio": 3.0
  },
  "file_tree": [
    {
      "path": "FS/data/anr/",
      "type": "directory",
      "files": [
        {
          "name": "anr_2026-03-01-09-30-00-001",
          "size": "1.2MB",
          "type": "anr_trace",
          "encoding": "utf-8"
        }
      ]
    },
    {
      "path": "FS/data/system/dropbox/",
      "type": "directory",
      "files": [
        {
          "name": "SYSTEM_TOMBSTONE@1234567890.txt",
          "size": "45KB",
          "type": "tombstone",
          "encoding": "utf-8"
        }
      ]
    }
  ],
  "key_files": {
    "logcat": "bugreport-logcat.txt",
    "dumpstate": "dumpstate.txt",
    "anr_dir": "FS/data/anr/",
    "tombstone_dir": "FS/data/tombstones/",
    "dropbox_dir": "FS/data/system/dropbox/"
  }
}
```

#### 3.1.6 上下文传递
- 仅传递 `manifest.json` 路径给下一个 Skill
- 不保留解压过程中的临时数据

---

### 3.2 Skill 2: Parser (信息提取)

#### 3.2.1 功能描述
根据关键词和文件类型，从大文件中流式提取有效信息。

#### 3.2.2 输入输出
| 项目 | 描述 |
|-----|------|
| 输入 | `manifest.json` 路径 + 目标应用包名/UID |
| 输出 | `extracted_info.json` - 提取的有效信息 |

#### 3.2.3 核心功能
- **流式读取大文件**: 避免内存溢出，支持 GB 级文件处理
- **多关键词并行匹配**: 使用 Aho-Corasick 算法实现多模式高效匹配
- **按应用包名/UID 过滤**: 精准定位目标应用日志
- **自动识别日志类型**: 智能识别 logcat、ANR、tombstone 等格式
- **提取时间戳和关键事件**: 构建时间线基础

#### 3.2.4 上下文感知提取
根据上下文关联提取相关信息，提高提取准确性：

| 上下文类型 | 描述 | 示例 |
|-----------|------|------|
| **进程上下文** | 关联同一 PID 的连续日志 | 从 Crash 日志关联到之前的操作日志 |
| **时间上下文** | 提取时间窗口内的相关事件 | ANR 前后 30 秒的所有日志 |
| **调用链上下文** | 追踪方法调用链路 | 从入口到 Crash 的完整调用链 |
| **组件上下文** | 关联同一组件的生命周期 | Activity/Service 的完整生命周期日志 |
| **异常上下文** | 异常发生时的系统状态 | 内存、CPU、网络等状态信息 |

**上下文感知流程**:
```
1. 识别关键事件 (Crash/ANR/Error)
      ↓
2. 确定上下文窗口 (时间/进程/组件)
      ↓
3. 提取窗口内所有相关日志
      ↓
4. 建立事件关联关系
      ↓
5. 输出结构化上下文信息
```

#### 3.2.5 模式匹配优化
使用高效的正则表达式和模式匹配算法：

| 优化技术 | 说明 | 性能提升 |
|---------|------|---------|
| **Aho-Corasick 算法** | 多模式同时匹配，O(n) 时间复杂度 | 10x+ |
| **正则预编译** | 预编译常用正则表达式 | 3-5x |
| **有限状态机** | 对固定格式日志使用 FSM 解析 | 5-10x |
| **并行匹配** | 多核并行处理不同文件 | 2-4x |
| **增量匹配** | 流式处理，避免全量加载 | 内存降低 90% |

**常用模式预定义**:
```python
PATTERNS = {
    "timestamp": r'\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d{3}',
    "anr_reason": r'Reason: (.+)',
    "java_exception": r'([a-zA-Z0-9_.]+Exception): (.+)',
    "native_signal": r'Signal (\d+) \((SIG\w+)\)',
    "process_died": r'Process ([a-zA-Z0-9_.]+) \(pid (\d+)\) has died',
    "uid_pattern": r'[Uu]id[=:\s]+(\d+)',
}
```

#### 3.2.6 智能去重策略
避免提取重复信息，减少数据量：

| 去重维度 | 策略 | 示例 |
|---------|------|------|
| **完全重复** | 相同日志行只保留一条 | 连续相同的错误日志 |
| **模式重复** | 相同模式的日志聚合计数 | "Connection failed" 出现 100 次 → 计数 |
| **堆栈重复** | 相同堆栈只保留一份，记录出现次数 | 同一 Crash 堆栈出现多次 |
| **时间窗口去重** | 短时间内相同事件合并 | 1秒内相同 Warning 只记录一次 |
| **跨文件去重** | 多个文件中的相同信息去重 | logcat 和 dropbox 中的相同 Crash |

**去重输出格式**:
```json
{
  "original_count": 1000,
  "deduplicated_count": 150,
  "dedup_stats": {
    "exact_duplicates": 500,
    "pattern_duplicates": 300,
    "stack_duplicates": 50
  },
  "aggregated_entries": [
    {
      "pattern": "Connection failed to *.example.com",
      "count": 50,
      "first_occurrence": "2026-03-01T09:00:00Z",
      "last_occurrence": "2026-03-01T09:05:00Z",
      "sample": "Connection failed to api.example.com: timeout"
    }
  ]
}
```

#### 3.2.7 智能采样策略
当日志文件过大（超过 500MB）时，采用智能采样避免下一级 Agent 崩溃：

**采样触发条件**:
| 条件 | 阈值 | 说明 |
|-----|------|------|
| 文件大小 | > 500MB | 触发智能采样 |
| 提取条目数 | > 100,000 | 触发智能采样 |
| 输出 JSON 大小 | > 10MB | 触发压缩采样 |

**采样策略**:

| 策略 | 优先级 | 保留比例 | 说明 |
|-----|-------|---------|------|
| **关键事件全保留** | 最高 | 100% | Crash、ANR、Error 全部保留 |
| **时间窗口采样** | 高 | 100% | 关键事件前后 30 秒的日志全保留 |
| **高频日志压缩** | 中 | 10% | 相同模式的高频日志只保留 10% 样本 |
| **普通日志采样** | 低 | 5% | INFO/DEBUG 级别日志按时间均匀采样 |
| **冗余日志丢弃** | 最低 | 0% | 完全重复的日志丢弃 |

**采样算法**:
```
1. 第一遍扫描：识别关键事件和统计分布
      ↓
2. 计算采样权重：
   - 关键事件权重 = 1.0 (全保留)
   - 高频模式权重 = 0.1 (保留10%)
   - 普通日志权重 = 0.05 (保留5%)
      ↓
3. 第二遍扫描：按权重采样
      ↓
4. 确保时间连续性：关键事件前后日志不中断
      ↓
5. 输出采样报告和完整统计
```

**采样输出格式**:
```json
{
  "sampling_applied": true,
  "original_size": "1.2GB",
  "sampled_size": "15MB",
  "compression_ratio": 80,
  "sampling_stats": {
    "total_original_entries": 500000,
    "total_sampled_entries": 6250,
    "key_events_preserved": 150,
    "key_events_ratio": "100%",
    "high_freq_compressed": 45000,
    "high_freq_sampled": 4500,
    "normal_sampled": 1600,
    "discarded_duplicates": 444400
  },
  "sampling_config": {
    "key_event_window_seconds": 30,
    "high_freq_sample_rate": 0.1,
    "normal_sample_rate": 0.05,
    "max_output_size_mb": 10
  },
  "preserved_time_windows": [
    {
      "event": "ANR at 09:15:30",
      "window": "09:15:00 - 09:16:00",
      "entries_preserved": 150
    }
  ]
}
```

**采样保证**:
- ✅ 所有关键事件 100% 保留
- ✅ 关键事件上下文完整保留
- ✅ 时间线连续性保证
- ✅ 统计信息完整（用于后续分析）
- ✅ 原始文件路径保留（需要时可重新提取）

#### 3.2.8 轻量化输出策略
为避免上下文膨胀，大段文本不直接存储在 JSON 中，而是使用 **URI + 摘要** 模式：

**存储原则**:
| 内容类型 | 存储方式 | 说明 |
|---------|---------|------|
| **摘要信息** | 直接存储 | 时间戳、类型、简要描述、统计 |
| **堆栈信息** | URI + 摘要 | 存储文件路径 + 前 3 行摘要 |
| **完整日志** | URI 引用 | 仅存储文件路径，按需读取 |
| **大段文本** | URI + 行号范围 | 存储位置信息，需要时读取 |

**摘要生成规则**:
- 堆栈摘要：保留前 3 行关键帧 + 总行数
- 日志摘要：保留时间戳 + 日志级别 + 标签 + 消息前 100 字符
- 错误摘要：保留错误类型 + 关键信息 + 出现次数

**按需读取机制**:
```
分析阶段：仅使用摘要信息进行推理
      ↓
需要细节时：通过 URI 读取具体内容
      ↓
读取后：立即释放，不保留在上下文中
```

**URI 格式规范**:
```
file://<path>#L<start>-L<end>    # 行范围
file://<path>#<anchor>           # 锚点位置
memory://<key>                   # 内存缓存引用（临时）
```

#### 3.2.9 支持的文件类型
| 文件类型 | 关键信息 |
|---------|---------|
| logcat | 应用日志、系统日志、崩溃栈 |
| dumpstate | 系统状态、进程信息 |
| ANR traces | ANR 堆栈、阻塞原因 |
| Tombstone | Native crash 信息 |
| dropbox | 系统错误报告 |
| kernel log | 内核日志、驱动问题 |
| dumpsys mars | Mars 冻结状态和历史 |
| dumpsys freecess | Freecess 冻结信息 |

#### 3.2.10 Mars/Freecess/Freezer 冻结分析

本模块专门用于分析 Android 系统中的应用冻结机制。

##### 3.2.10.1 冻结机制概述
- **Mars**: 用户空间应用冻结管理器
- **Freecess**: 内核空间应用冻结机制
- **Freezer**: 系统级应用冻结框架

##### 3.2.10.2 关键日志关键词
| 关键词 | 说明 |
|-------|------|
| `am_freeze` | ActivityManager 冻结事件 |
| `am_unfreeze` | ActivityManager 解冻事件 |
| `mars` | Mars 冻结相关日志 |
| `freecess` | Freecess 冻结相关日志 |
| `BaseRestrictionMgr` | 基础限制管理器 |

##### 3.2.10.3 dumpsys 命令分析
- `dumpsys activity mars` - 当前 Mars 冻结状态
- `dumpsys activity mars history` - Mars 冻结历史记录
- `dumpsys activity freecess` - Freecess 冻结信息

##### 3.2.10.4 分析模式
支持两种分析模式：

**模式 1：独立分析冻结异常**
- 仅分析冻结相关事件
- 生成冻结事件时间线
- 识别异常冻结模式

**模式 2：结合已完成的分析异常**
- 冻结事件与 Crash/ANR/Error 关联分析
- 识别冻结导致的问题
- 提供完整根因分析

##### 3.2.10.5 冻结事件类型
| 事件类型 | 说明 |
|---------|------|
| `FREEZE` | 应用被冻结 |
| `UNFREEZE` | 应用被解冻 |
| `FROZEN_CRASH` | 冻结状态下发生 Crash |
| `FROZEN_ANR` | 冻结状态下发生 ANR |
| `FREEZE_TIMEOUT` | 冻结超时 |

##### 3.2.10.6 输出格式扩展
在 `extracted_info.json` 中新增字段：

```json
{
  "freeze_analysis": {
    "analysis_mode": "independent|correlated",
    "freeze_events": [
      {
        "id": "freeze_001",
        "timestamp": "2026-03-01T09:15:00Z",
        "type": "FREEZE",
        "package_name": "com.example.app",
        "uid": 10123,
        "pid": 12345,
        "mechanism": "mars|freecess|freezer",
        "reason": "Background restriction",
        "duration_seconds": 120,
        "related_crash_id": null,
        "related_anr_id": null,
        "detail_uri": "file://resources/freeze/freeze_001.log"
      }
    ],
    "mars_info": {
      "current_frozen_packages": ["com.example.app"],
      "history_count": 25,
      "restriction_policies": ["STANDBY", "FROZEN"],
      "detail_uri": "file://resources/freeze/mars_info.json"
    },
    "freecess_info": {
      "frozen_processes": [12345, 67890],
      "detail_uri": "file://resources/freeze/freecess_info.json"
    },
    "anomaly_summary": {
      "total_freezes": 15,
      "total_unfreezes": 12,
      "frozen_crashes": 2,
      "frozen_anrs": 1,
      "freeze_timeouts": 0,
      "suspicious_packages": ["com.example.app"]
    }
  }
}
```

#### 3.2.10 依赖清单 (requirements.txt)
```txt
# 核心依赖（必需）
regex>=2022.9.0     # 高性能正则表达式库，比标准re库快3-5倍，用于复杂模式匹配

# 可选依赖（推荐安装以增强功能）
psutil>=5.9.0       # 用于内存使用监控和采样策略决策
```

#### 3.2.11 输出格式 (extracted_info.json)
```json
{
  "version": "1.0",
  "extracted_at": "2026-03-01T10:05:00Z",
  "target_app": {
    "package_name": "com.example.app",
    "uids": [10123, 10124]
  },
  "extraction_stats": {
    "total_files_processed": 15,
    "total_lines_scanned": 500000,
    "processing_time": "45.2s",
    "memory_peak": "256MB"
  },
  "sampling": {
    "applied": true,
    "trigger_reason": "file_size_exceeded",
    "original_size": "1.2GB",
    "sampled_size": "15MB",
    "compression_ratio": 80,
    "stats": {
      "total_original_entries": 500000,
      "total_sampled_entries": 6250,
      "key_events_preserved": 150,
      "key_events_ratio": "100%"
    }
  },
  "deduplication": {
    "original_count": 5000,
    "deduplicated_count": 850,
    "dedup_stats": {
      "exact_duplicates": 2500,
      "pattern_duplicates": 1500,
      "stack_duplicates": 150
    }
  },
  "summary": {
    "total_entries": 850,
    "time_range": {
      "start": "2026-03-01T09:00:00Z",
      "end": "2026-03-01T09:30:00Z"
    }
  },
  "contexts": [
    {
      "type": "ANR_CONTEXT",
      "event_id": "anr_001",
      "time_window": {
        "start": "2026-03-01T09:15:00Z",
        "end": "2026-03-01T09:16:00Z"
      },
      "related_entries": 150,
      "processes": [12345, 67890],
      "detail_uri": "file://extracted_logs/contexts/anr_001.log"
    }
  ],
  "crashes": [
    {
      "type": "ANR",
      "timestamp": "2026-03-01T09:15:30Z",
      "reason": "Input dispatching timed out",
      "pid": 12345,
      "occurrence_count": 3,
      "context_id": "anr_001",
      "stack_summary": {
        "top_frames": [
          "android.os.MessageQueue.nativePollOnce(Native Method)",
          "android.os.MessageQueue.next(MessageQueue.java:326)",
          "android.os.Looper.loop(Looper.java:160)"
        ],
        "total_frames": 45
      },
      "stack_uri": "file://extracted_logs/stacks/anr_001_stack.txt#L1-L45"
    }
  ],
  "errors": [
    {
      "level": "ERROR",
      "tag": "ActivityManager",
      "message_summary": "ANR in com.example.app, reason: Input dispatching timed out",
      "timestamp": "2026-03-01T09:15:35Z",
      "occurrence_count": 1,
      "detail_uri": "file://extracted_logs/errors/error_001.log#L100-L105"
    }
  ],
  "warnings": [
    {
      "level": "WARNING",
      "tag": "PackageManager",
      "message_summary": "Failed to verify signature...",
      "occurrence_count": 5,
      "detail_uri": "file://extracted_logs/warnings/warn_001.log"
    }
  ],
  "performance_issues": [
    {
      "type": "GC_OVERHEAD",
      "summary": "Frequent GC detected, 50 times in 5 minutes",
      "impact": "MEDIUM",
      "detail_uri": "file://extracted_logs/perf/gc_analysis.log"
    }
  ],
  "aggregated_patterns": [
    {
      "pattern": "Connection timeout",
      "count": 25,
      "first_occurrence": "2026-03-01T09:00:00Z",
      "last_occurrence": "2026-03-01T09:10:00Z",
      "sample_summary": "Connection timeout to api.example.com",
      "samples_uri": "file://extracted_logs/patterns/connection_timeout.log"
    }
  ],
  "resource_index": {
    "base_path": "extracted_logs/com_example_app/",
    "files": {
      "raw_log": "filtered_raw.log",
      "stacks_dir": "stacks/",
      "contexts_dir": "contexts/",
      "patterns_dir": "patterns/"
    }
  }
}
```

#### 3.2.11 上下文传递
- 仅传递 `extracted_info.json` 路径
- 原始日志文件路径保留在 JSON 中，需要时再读取

---

### 3.3 Skill 3: Analyzer (推理分析)

#### 3.3.1 功能描述
基于提取的信息进行推理分析，识别问题类型和根因。

#### 3.3.2 输入输出
| 项目 | 描述 |
|-----|------|
| 输入 | `extracted_info.json` 路径 |
| 输出 | `analysis_report.json` - 分析报告 |

#### 3.3.3 支持的问题类型
| 类型 | 子类型 | 分析要点 |
|-----|-------|---------|
| **崩溃类** | ANR | 主线程阻塞、死锁、耗时操作 |
| | Java Crash | NPE、OOM、资源泄漏 |
| | Native Crash | SIGSEGV、SIGABRT、内存越界 |
| | Kernel Panic | 驱动错误、硬件异常 |
| **性能类** | 卡顿 | UI 线程耗时、频繁 GC |
| | 启动慢 | 初始化耗时、资源加载 |
| | 内存泄漏 | 对象未释放、引用链 |
| | 电量消耗 | 后台活动、唤醒锁 |
| **功能类** | 权限问题 | 权限缺失、权限拒绝 |
| | 网络问题 | 连接失败、超时 |
| | 存储问题 | 空间不足、IO 错误 |
| **冻结类** | Mars 冻结 | 应用被 Mars 冻结导致异常 |
| | Freecess 冻结 | 应用被 Freecess 冻结导致异常 |
| | 冻结异常 | 冻结状态下发生 Crash/ANR |

#### 3.3.4 冻结问题分析流程
```
1. 识别冻结事件 (FREEZE/UNFREEZE)
      ↓
2. 构建冻结事件时间线
      ↓
3. 检测冻结状态下的 Crash/ANR
      ↓
4. 关联分析（correlated 模式）
      ↓
5. 识别冻结导致的问题根因
      ↓
6. 生成冻结异常报告
```

#### 3.3.5 冻结分析配置
| 参数 | 默认值 | 说明 |
|-----|-------|------|
| `analysis_mode` | `correlated` | 分析模式：independent 或 correlated |
| `freeze_window_seconds` | 60 | 冻结事件关联时间窗口 |
| `enable_freeze_analysis` | true | 是否启用冻结分析 |

#### 3.3.6 分析报告扩展
在 `analysis_report.json` 的 `issues` 中新增冻结问题类型：

```json
{
  "issues": [
    {
      "id": "ISSUE-002",
      "type": "FROZEN_CRASH",
      "severity": "HIGH",
      "confidence": 0.92,
      "title": "Mars 冻结状态下发生 Crash",
      "description": "应用在被 Mars 冻结后 5 秒内发生了 Crash",
      "freeze_info": {
        "freeze_event_id": "freeze_001",
        "freeze_mechanism": "mars",
        "freeze_reason": "Background restriction",
        "time_from_freeze_to_crash_seconds": 5.2
      },
      "possible_causes": [
        {
          "rank": 1,
          "priority_score": 0.88,
          "type": "FROZEN_HANDLER",
          "description": "应用在冻结状态下仍有 Handler 消息在处理",
          "confidence": 0.9,
          "severity": "HIGH",
          "frequency": "OFTEN",
          "fix_complexity": "MODERATE"
        }
      ],
      "suggestions": [
        {
          "priority": 1,
          "action": "检查应用在冻结前是否正确停止后台任务",
          "target_cause_rank": 1
        }
      ]
    }
  ]
}
```

#### 3.3.4 分析流程
```
1. 问题类型识别
      ↓
2. 时间线重建
      ↓
3. 因果关系分析
      ↓
4. 根因定位 (可能多个)
      ↓
5. 优先级排序
      ↓
6. 影响范围评估
```

#### 3.3.5 多原因优先级排序算法

当分析出多个可能的原因时，使用以下维度进行优先级排序：

| 排序维度 | 权重 | 说明 |
|---------|------|------|
| **置信度 (confidence)** | 40% | 基于日志证据的确定性程度 |
| **严重程度 (severity)** | 25% | 对用户体验的影响程度 |
| **出现频率 (frequency)** | 20% | 问题复现的概率 |
| **修复难度 (fix_complexity)** | 15% | 修复的复杂度（越简单优先级越高） |

**优先级计算公式**:
```
priority_score = confidence * 0.4 
               + severity_score * 0.25 
               + frequency_score * 0.2 
               + (1 - fix_complexity) * 0.15
```

**严重程度评分标准**:
| 级别 | 分数 | 说明 |
|-----|------|------|
| CRITICAL | 1.0 | 应用崩溃、数据丢失 |
| HIGH | 0.8 | ANR、功能完全不可用 |
| MEDIUM | 0.6 | 功能部分受损、性能下降 |
| LOW | 0.4 | 轻微问题、体验影响小 |

**出现频率评分标准**:
| 频率 | 分数 | 说明 |
|-----|------|------|
| ALWAYS | 1.0 | 必现 |
| OFTEN | 0.7 | 高概率复现 |
| SOMETIMES | 0.4 | 偶发 |
| RARE | 0.2 | 很少出现 |

**修复难度评分标准**:
| 难度 | 分数 | 说明 |
|-----|------|------|
| SIMPLE | 0.2 | 简单修改，1小时内 |
| MODERATE | 0.5 | 中等复杂度，1-4小时 |
| COMPLEX | 0.8 | 复杂修改，需要架构调整 |
| DIFFICULT | 1.0 | 非常复杂，需要重大重构 |

#### 3.3.6 依赖清单 (requirements.txt)
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

#### 3.3.7 输出格式 (analysis_report.json)
```json
{
  "version": "1.0",
  "analyzed_at": "2026-03-01T10:10:00Z",
  "issues": [
    {
      "id": "ISSUE-001",
      "type": "ANR",
      "severity": "HIGH",
      "confidence": 0.95,
      "title": "主线程 IO 阻塞导致 ANR",
      "description": "应用在主线程执行了同步数据库查询操作...",
      "possible_causes": [
        {
          "rank": 1,
          "priority_score": 0.89,
          "type": "BLOCKING_IO",
          "description": "主线程执行同步数据库查询",
          "location": "DatabaseHelper.query()",
          "stack_trace": "...",
          "evidence": [
            "logcat 显示主线程阻塞在 SQLiteDatabase.query()",
            "ANR trace 显示主线程状态为 BLOCKED"
          ],
          "confidence": 0.95,
          "severity": "HIGH",
          "frequency": "ALWAYS",
          "fix_complexity": "SIMPLE"
        },
        {
          "rank": 2,
          "priority_score": 0.62,
          "type": "DEADLOCK",
          "description": "可能的数据库锁竞争",
          "location": "DatabaseHelper.getWritableDatabase()",
          "stack_trace": "...",
          "evidence": [
            "检测到多个线程等待数据库锁"
          ],
          "confidence": 0.60,
          "severity": "HIGH",
          "frequency": "SOMETIMES",
          "fix_complexity": "MODERATE"
        },
        {
          "rank": 3,
          "priority_score": 0.35,
          "type": "MEMORY_PRESSURE",
          "description": "内存压力导致 GC 频繁",
          "location": "系统全局",
          "evidence": [
            "GC 日志显示频繁 Full GC"
          ],
          "confidence": 0.40,
          "severity": "MEDIUM",
          "frequency": "RARE",
          "fix_complexity": "COMPLEX"
        }
      ],
      "primary_cause": {
        "rank": 1,
        "type": "BLOCKING_IO",
        "location": "DatabaseHelper.query()",
        "stack_trace": "..."
      },
      "timeline": [
        {
          "time": "2026-03-01T09:15:00Z",
          "event": "用户点击查询按钮"
        },
        {
          "time": "2026-03-01T09:15:05Z",
          "event": "主线程开始数据库查询"
        },
        {
          "time": "2026-03-01T09:15:30Z",
          "event": "ANR 触发 (超时5秒)"
        }
      ],
      "impact": {
        "user_visible": true,
        "affected_users": "所有使用查询功能的用户",
        "frequency": "高频操作必现"
      },
      "suggestions": [
        {
          "priority": 1,
          "action": "将数据库查询移至后台线程",
          "target_cause_rank": 1,
          "code_example": "..."
        },
        {
          "priority": 2,
          "action": "添加查询超时机制",
          "target_cause_rank": 1,
          "code_example": "..."
        },
        {
          "priority": 3,
          "action": "优化数据库锁策略",
          "target_cause_rank": 2,
          "code_example": "..."
        }
      ]
    }
  ],
  "needs_deeper_analysis": false,
  "additional_files_needed": []
}
```

#### 3.3.7 上下文传递
- 传递 `analysis_report.json` 路径
- 如果 `needs_deeper_analysis` 为 true，触发迭代

---

### 3.4 Skill 4: Coordinator (管理协调)

#### 3.4.1 功能描述
协调各 Skills 的执行，管理迭代流程，生成最终报告。

#### 3.4.2 输入输出
| 项目 | 描述 |
|-----|------|
| 输入 | `analysis_report.json` 路径 |
| 输出 | `final_report.md` - 最终报告 |

#### 3.4.3 核心功能
- 迭代控制 (最多 3 轮)
- 决定是否需要深入分析
- 调用其他 Skills 获取更多信息
- 生成人类可读的最终报告

#### 3.4.4 迭代流程
```
第1轮分析
    │
    ├── confidence >= 0.8? ──YES──▶ 生成最终报告
    │
    NO
    │
    ▼
第2轮分析 (请求更多信息)
    │
    ├── confidence >= 0.8? ──YES──▶ 生成最终报告
    │
    NO
    │
    ▼
第3轮分析 (最后一次尝试)
    │
    └──▶ 生成最终报告 (标注不确定性)
```

#### 3.4.5 依赖清单 (requirements.txt)
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

#### 3.4.6 输出格式 (final_report.md)
```markdown
# Android Bug Report 分析报告

## 概述
- **分析时间**: 2026-03-01 10:15:00
- **目标应用**: com.example.app
- **问题数量**: 2
- **严重程度**: 高

## 问题列表

### 问题 1: 主线程 IO 阻塞导致 ANR [HIGH]

**问题描述**
应用在主线程执行了同步数据库查询操作，导致输入事件超时触发 ANR。

**根因分析**
- 类型: BLOCKING_IO
- 位置: DatabaseHelper.query()
- 堆栈: [查看详情](#stack-trace-1)

**时间线**
| 时间 | 事件 |
|-----|------|
| 09:15:00 | 用户点击查询按钮 |
| 09:15:05 | 主线程开始数据库查询 |
| 09:15:30 | ANR 触发 |

**建议方案**
1. **[优先级高]** 将数据库查询移至后台线程
   ```java
   // 示例代码
   Executors.newSingleThreadExecutor().execute(() -> {
       // 数据库查询
   });
   ```
2. **[优先级中]** 添加查询超时机制

---

## 总结
本次分析发现 2 个问题，其中 1 个高危问题需要立即处理。
建议优先解决 ANR 问题，提升用户体验。
```

## 4. 中间文件规范

### 4.1 文件命名规范
| 文件类型 | 命名格式 | 示例 |
|---------|---------|------|
| manifest | `manifest_<timestamp>.json` | `manifest_20260301_100000.json` |
| extracted | `extracted_<package>_<timestamp>.json` | `extracted_com_example_20260301.json` |
| analysis | `analysis_<package>_<timestamp>.json` | `analysis_com_example_20260301.json` |
| final report | `report_<package>_<timestamp>.md` | `report_com_example_20260301.md` |

### 4.2 存储位置
```
.trae/skills/
├── bugreport-extractor/
├── bugreport-parser/
├── bugreport-analyzer/
└── bugreport-coordinator/

<output_dir>/
├── extracted/           # 解压后的文件
├── intermediate/        # 中间 JSON 文件
│   ├── manifest.json
│   ├── extracted_info.json
│   └── analysis_report.json
└── reports/             # 最终报告
    └── final_report.md
```

### 4.2 共享依赖清单

为方便用户按需安装，也提供以下依赖文件：

```
android-bugreport-analyzer/
├── requirements.txt              # 根目录：一次性安装所有依赖
├── requirements-shared.txt       # 共享依赖：所有Skills都需要
├── bugreport-extractor/
│   └── requirements.txt          # 解压Skill依赖
├── bugreport-parser/
│   └── requirements.txt         # 解析Skill依赖
├── bugreport-analyzer/
│   └── requirements.txt          # 分析Skill依赖
└── bugreport-coordinator/
    └── requirements.txt          # 协调Skill依赖
```

#### 共享依赖 (requirements-shared.txt)
```txt
psutil>=5.9.0        # 磁盘空间、内存、CPU检测，环境自适应配置
regex>=2022.9.0      # 高性能正则表达式，用于Parser模式匹配
```

#### 根目录依赖 (requirements.txt)
```txt
# ==================== 核心依赖 ====================
psutil>=5.9.0        # 磁盘空间、内存、CPU检测，环境自适应配置
regex>=2022.9.0      # 高性能正则表达式，用于Parser模式匹配
```

#### 安装指南
```bash
# 方式1: 安装所有依赖
pip install -r requirements.txt

# 方式2: 按需安装（更轻量）
pip install psutil regex

# 方式3: 只安装某个Skill的依赖
cd bugreport-parser && pip install -r requirements.txt
```

## 5. Context 窗口保护机制

### 5.1 设计原则

**核心目标**: 确保 AI Agent 的 context 窗口不会被撑爆，保持推理能力。

```
原始数据 (1-2GB)  →  处理后数据 (< 80KB)
     ↓                      ↓
  完整日志              摘要 + URI
  完整堆栈              前3行 + URI
  所有错误              统计 + 样本
```

### 5.2 文件驱动传递

**只传递文件路径，不传递内容**:

```python
# 正确做法 ✅
extracted = parser.parse(manifest_path="./output/manifest.json")
# AI 只看到: "./output/extracted_info.json" 这个路径

# 错误做法 ❌
extracted = parser.parse(manifest_content=manifest_json_string)
# AI 会看到整个 manifest 内容
```

### 5.3 URI + 摘要模式

大段文本不直接存储在 JSON 中:

| 内容类型 | 存储方式 | Context 占用 |
|---------|---------|-------------|
| 统计信息 | 直接存储 | 低 |
| 时间戳 | 直接存储 | 低 |
| 摘要描述 | 直接存储 (限100字符) | 低 |
| 堆栈信息 | 前3行 + URI | 低 |
| 完整日志 | 仅 URI | 极低 |
| 错误消息 | 前100字符 + URI | 低 |
| 大段文本 | URI + 行号范围 | 极低 |

**URI 格式规范**:
```
file://<path>                    # 文件路径
file://<path>#L<start>-L<end>    # 行范围
file://<path>#<anchor>           # 锚点位置
```

### 5.4 智能采样策略

**采样触发条件**:

| 条件 | 阈值 | 动作 |
|------|------|------|
| 文件大小 | > 500MB | 启动智能采样 |
| 条目数量 | > 100,000 | 启动智能采样 |
| 输出 JSON | > 50KB | 压缩采样 |

**采样保留规则**:

| 数据类型 | 保留比例 | 说明 |
|---------|---------|------|
| ANR/Crash/Error | 100% | 关键事件全保留 |
| 关键事件前后30秒 | 100% | 上下文完整保留 |
| 高频模式日志 | 10% | 相同模式只保留样本 |
| INFO/DEBUG日志 | 5% | 均匀采样 |
| 完全重复日志 | 0% | 丢弃，记录计数 |

### 5.5 Context 大小限制

**重要**: 以下限制基于主流 LLM 的 context 窗口安全使用范围

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

### 5.6 主流 Agent 兼容性

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

### 5.7 按需读取机制

```
分析阶段：仅使用摘要信息进行推理
      ↓
需要细节时：通过 URI 读取具体内容
      ↓
读取后：立即释放，不保留在上下文中
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

## 6. 意图识别与分析模式

### 6.1 意图识别规则

根据用户输入自动识别分析模式:

| 模式 | 触发关键词 | 说明 |
|------|-----------|------|
| `full` | "分析bug", "分析 bugreport", "bugreport分析", "完整分析", "解析bug" | 完整分析流程 |
| `freeze` | "分析冻结", "冻结问题", "freeze分析", "mars冻结", "freecess", "分析freeze" | 冻结专项分析 |
| `plm_issue` | "分析plm issue", "plm问题分析", "issue分析", "plm问题", "分析plm" | PLM Issue 分析 |
| `quick` | "快速分析", "只解析", "只分析", "单步分析" | 单步操作 |

### 6.2 意图识别代码

```python
def detect_mode(user_input: str) -> str:
    user_input_lower = user_input.lower()
    
    if any(kw in user_input_lower for kw in ["分析冻结", "冻结问题", "freeze", "mars冻结", "freecess"]):
        return "freeze"
    
    if any(kw in user_input_lower for kw in ["分析plm", "plm问题", "issue分析"]):
        return "plm_issue"
    
    if any(kw in user_input_lower for kw in ["快速分析", "只解析", "只分析", "单步"]):
        return "quick"
    
    if any(kw in user_input_lower for kw in ["分析bug", "分析 bugreport", "bugreport", "完整分析", "解析bug"]):
        return "full"
    
    return "full"
```

### 6.3 分析模式流程

**模式 1: 完整分析 (full)**
```
用户输入: "分析bug" / "分析bugreport"
    ↓
执行完整 4-skill 流水线
    ↓
输出: final_report.md
```

**模式 2: 冻结问题分析 (freeze)**
```
用户输入: "分析冻结" / "冻结问题"
    ↓
执行完整流水线 + 启用冻结分析
    ↓
筛选冻结相关问题
    ↓
输出: freeze_analysis_report.md
```

**模式 3: PLM Issue 分析 (plm_issue)**
```
用户输入: "分析plm issue"
    ↓
解析 Issue 内容
    ↓
分析完整性和改进建议
    ↓
输出: plm_issue_analysis.md
```

**模式 4: 快速分析 (quick)**
```
用户输入: "只解析" / "单步分析"
    ↓
询问用户选择具体操作
    ↓
执行单个 skill
    ↓
输出: 对应的中间文件
```

## 7. Skill 加载机制

### 7.1 加载方式

Trae 的 Skill 系统采用**按需加载**机制：

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Skill 加载机制                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  初始状态 (Agent 启动时)                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Agent 只看到各 skill 的 description 字段:                           │   │
│  │  "Android Bug Report 分析系统。分析 bug、冻结问题和 PLM issue。"      │   │
│  │  (约 50 字符，极小占用)                                              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                               │
│                              ▼                                               │
│  触发时 (用户说"分析bug")                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Skill 工具被调用                                                    │   │
│  │  → SKILL.md 内容被注入到 prompt 中                                   │   │
│  │  → 仅在当前轮次有效                                                  │   │
│  │  → 下一轮对话自动清除                                                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 7.2 Context 占用估算

| 内容 | 大小 | 加载时机 | 持续时间 |
|------|------|---------|---------|
| 主 SKILL.md | ~4KB (143行) | 主skill触发时 | 当前轮次 |
| 子 SKILL.md (单个) | ~1KB | 子skill独立触发时 | 当前轮次 |
| 分析数据 (manifest.json) | ~10KB | 分析过程中 | 当前轮次 |
| 分析数据 (extracted_info.json) | ~50KB | 分析过程中 | 当前轮次 |
| 分析数据 (analysis_report.json) | ~20KB | 分析过程中 | 当前轮次 |

**最坏情况**: ~85KB (完全兼容主流 LLM)

### 7.3 子 Skill 调用方式

本系统的子模块采用**Python 模块调用**，而非 Skill 工具调用：

```
┌─────────────────────────────────────────────────────────────────┐
│                    调用方式对比                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Skill 工具调用 (不使用)              Python 模块调用 (使用)      │
│  ┌─────────────────────┐            ┌─────────────────────┐     │
│  │ Skill("extractor")  │            │ from bugreport_     │     │
│  │ → 加载 SKILL.md     │            │   extractor import  │     │
│  │ → 注入 prompt       │            │   ArchiveExtractor  │     │
│  │ → 占用 context      │            │ → 直接执行代码      │     │
│  └─────────────────────┘            │ → 不占用 context    │     │
│                                     └─────────────────────┘     │
│                                                                  │
│  优势:                              优势:                        │
│  - 可被 Agent 自动发现              - 不占用 AI context          │
│  - 统一的调用接口                   - 执行效率高                  │
│                                    - 可精确控制                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 7.4 子 SKILL.md 的作用

子模块的 SKILL.md 主要用于：

1. **文档说明**: 开发者理解模块功能
2. **独立调用**: 当用户直接说"只解压"、"只解析"时，Agent 可识别并调用
3. **未来扩展**: 如果需要将子模块升级为独立 Skill

### 7.5 Context 保护策略

```
┌─────────────────────────────────────────────────────────────────┐
│                   Context 保护策略                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. 精简 SKILL.md                                               │
│     - 主 SKILL.md: 143 行 (~4KB)                                │
│     - 子 SKILL.md: ~50 行 (~1KB)                                │
│     - 移除冗余的详细说明                                         │
│                                                                  │
│  2. 数据文件驱动                                                 │
│     - 只传递文件路径，不传递内容                                  │
│     - 大文本存文件，JSON 只存 URI                                │
│                                                                  │
│  3. 流式处理                                                     │
│     - 大文件不加载到内存                                         │
│     - 逐行处理，立即释放                                         │
│                                                                  │
│  4. 单轮有效                                                     │
│     - SKILL.md 仅在触发轮次有效                                  │
│     - 下一轮对话自动清除                                         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 7.6 主流 Agent 兼容性

| 模型 | Context 窗口 | 本系统最大占用 | 兼容性 |
|------|-------------|---------------|--------|
| GPT-4 Turbo | 128K tokens (~96KB) | ~85KB (89%) | ✅ 兼容 |
| Claude 3 | 200K tokens (~150KB) | ~85KB (57%) | ✅ 兼容 |
| Gemini 1.5 Pro | 1M tokens (~750KB) | ~85KB (11%) | ✅ 完全兼容 |

## 8. 非功能需求

### 8.1 性能需求
| 指标 | 要求 |
|-----|------|
| 100MB 压缩包解压 | < 30 秒 |
| 500MB 日志文件解析 | < 2 分钟 |
| 内存占用 | < 日志文件大小的 1.5 倍 |
| 分析响应时间 | < 30 秒 |

### 8.2 可靠性需求
- 支持断点续传
- 异常自动恢复
- 详细的错误日志

### 8.3 可扩展性需求
- 支持自定义关键词
- 支持自定义分析规则
- 支持插件扩展

## 9. 验收标准

### 9.1 功能验收
- [ ] 能够解压标准 Android bug report (zip/tar.gz)
- [ ] 能够递归解压嵌套压缩包
- [ ] 能够流式处理大文件 (>500MB)
- [ ] 能够根据包名/UID 过滤日志
- [ ] 能够识别 ANR、Crash、性能问题
- [ ] 能够生成结构化的分析报告
- [ ] 能够提供可操作的建议

### 9.2 质量验收
- [ ] 每个 Skill 有独立的 SKILL.md
- [ ] 代码有完整的文档注释
- [ ] 包含单元测试
- [ ] 错误处理完善

### 9.3 复用性验收
- [ ] Skills 可独立调用
- [ ] 支持自定义配置
- [ ] 输出格式标准化

## 10. 后续扩展

### 10.1 短期扩展
- 支持更多日志格式
- 添加可视化时间线
- 支持多应用对比分析

### 10.2 长期扩展
- 集成机器学习模型
- 自动生成修复代码
- 与 Issue 跟踪系统集成
