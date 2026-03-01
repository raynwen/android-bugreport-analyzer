---
name: "bugreport-parser"
description: "解析 Android bug report 文件，提取日志、崩溃、ANR 等关键信息。支持冻结问题分析 (Mars/Freecess/Freezer)。当用户需要解析 bug、分析日志、提取 bugreport 信息、分析冻结问题时触发。"
---

# Bug Report Parser (信息提取)

使用流式处理、关键词匹配和模式识别从大型 bug report 文件中提取关键信息。

## 独立使用

此 skill 可独立使用，只需提供 `manifest.json` 文件。

## 触发时机

- 用户说"解析日志"、"只解析"、"提取信息"
- 需要从 bug report 中提取日志
- 需要分析冻结相关问题

## 输入

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| manifest_path | string | 是 | extractor 生成的 manifest.json 路径 |
| package_name | string | 否 | 目标应用包名，用于过滤日志 |
| output_dir | string | 否 | 输出目录，默认为 manifest.json 同目录 |
| enable_freeze_analysis | bool | 否 | 是否启用冻结分析，默认 True |
| freeze_analysis_mode | string | 否 | 冻结分析模式: "correlated" 或 "independent" |

## 输出

生成文件:
- `{output_dir}/extracted_info.json` - 提取的关键信息
- `{output_dir}/resources/` - 详细资源文件

extracted_info.json 结构:
```json
{
  "version": "1.0",
  "target_app": {
    "package_name": "com.example.app",
    "uids": [10123]
  },
  "summary": {
    "total_entries": 150000,
    "time_range": {"start": "01-15 10:00:00", "end": "01-15 10:30:00"}
  },
  "crashes": [...],
  "errors": [...],
  "freeze_analysis": {
    "freeze_events": [...],
    "anomaly_summary": {
      "total_freezes": 10,
      "frozen_crashes": 2,
      "frozen_anrs": 1
    }
  }
}
```

## 调用方式

### Python 调用
```python
from bugreport_parser import LogParser

parser = LogParser()
extracted = parser.parse(
    manifest_path="./output/manifest.json",
    package_name="com.example.app",
    output_dir="./output",
    enable_freeze_analysis=True,
    freeze_analysis_mode="correlated"
)

print(f"提取完成: {extracted.summary['total_entries']} 条日志")
print(f"崩溃数: {len(extracted.crashes)}")
if extracted.freeze_analysis:
    print(f"冻结事件: {len(extracted.freeze_analysis.freeze_events)}")
```

### 命令行调用
```bash
python -m bugreport_parser ./output/manifest.json -p com.example.app
```

## 功能特性

- **流式处理**: 无需将大文件加载到内存
- **多关键词匹配**: Aho-Corasick 算法高效模式匹配
- **包名/UID 过滤**: 按目标应用过滤日志
- **自动文件类型检测**: 识别 logcat, ANR, tombstone 格式
- **去重**: 移除重复日志条目
- **智能采样**: 采样大文件同时保留关键事件
- **冻结分析**: 分析 Mars/Freecess/Freezer 冻结事件

## 冻结分析模式

### correlated (关联分析) - 推荐
将冻结事件与崩溃和 ANR 关联，识别冻结导致的问题。

```python
extracted = parser.parse(
    manifest_path="manifest.json",
    package_name="com.example.app",
    enable_freeze_analysis=True,
    freeze_analysis_mode="correlated"
)
```

### independent (独立分析)
仅分析冻结事件，不关联崩溃/ANR。

## 关键日志关键词

| 类别 | 关键词 |
|------|--------|
| 冻结 | am_freeze, am_unfreeze, mars, freecess, FROZEN |
| 崩溃 | ANR, CRASH, FATAL, Exception |
| 错误 | ERROR, Exception, fail |
| 性能 | GC, memory, cpu |

## 配置参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| max_workers | 4 | 并行处理线程数 |
| chunk_size | 10000 | 流式处理块大小 |
| trigger_sample_size_mb | 500 | 触发采样的文件大小阈值 |
| key_event_window_seconds | 30 | 关键事件上下文提取时间窗口 |

## 错误处理

| 错误类型 | 处理方式 |
|---------|---------|
| manifest.json 不存在 | 抛出 FileNotFoundError |
| 文件编码错误 | 使用 errors='ignore' 跳过 |
| 内存不足 | 自动触发采样模式 |

## 下一步

解析完成后，可以使用 `bugreport-analyzer` 分析问题:
```python
from bugreport_analyzer import BugAnalyzer

analyzer = BugAnalyzer()
report = analyzer.analyze(
    extracted_info_path="./output/extracted_info.json"
)
```
