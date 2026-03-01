---
name: "android-bugreport-analyzer"
description: "Android Bug Report 分析系统。分析 bug、冻结问题和 PLM issue。"
---

# Android Bug Report Analyzer

Android Bug Report 分析系统，提供完整的 bug report 分析流程。

## 意图识别

根据用户输入自动选择分析模式:

| 模式 | 触发关键词 | 流程 |
|------|-----------|------|
| `full` | "分析bug", "分析bugreport", "完整分析", "解析bug" | 完整4步流程 |
| `freeze` | "分析冻结", "冻结问题", "freeze", "mars冻结", "freecess" | 冻结专项分析 |
| `plm_issue` | "分析plm", "plm问题", "issue分析" | PLM Issue 分析 |
| `quick` | "快速分析", "只解析", "只解压", "单步" | 单步操作 |

## 分析流程

```
用户输入 → 意图识别 → 执行对应流程 → 输出报告
```

### 完整分析流程 (full)

```
步骤 1: 获取信息
  - bug report 文件路径 (必需)
  - 目标应用包名 (可选)
  - 输出目录 (可选，默认 ./output)

步骤 2: 执行分析管道
  extractor → parser → analyzer → coordinator
  (解压)     (解析)    (分析)     (报告)

步骤 3: 输出结果
  - 报告路径
  - 问题摘要
```

### 冻结分析流程 (freeze)

```
步骤 1: 获取信息 (同上)

步骤 2: 执行分析 (启用冻结模式)
  extractor → parser(freeze_mode) → analyzer → coordinator

步骤 3: 输出冻结报告
  - 冻结事件统计
  - 冻结机制分析
  - 冻结原因和建议
```

### PLM Issue 分析流程 (plm_issue)

```
步骤 1: 获取 Issue 内容
  - 文件路径 或 直接粘贴

步骤 2: 分析 Issue
  - 完整性检查
  - 缺失信息识别
  - 改进建议

步骤 3: 输出分析报告
```

### 快速分析流程 (quick)

```
根据用户选择执行单步操作:
  - extractor: 仅解压
  - parser: 仅解析
  - analyzer: 仅分析
```

## 子 Skills

本 skill 协调 4 个子模块:

| 模块 | 功能 | 输入 | 输出 |
|------|------|------|------|
| bugreport-extractor | 解压归档 | bugreport路径 | manifest.json |
| bugreport-parser | 解析日志 | manifest.json | extracted_info.json |
| bugreport-analyzer | 分析问题 | extracted_info.json | analysis_report.json |
| bugreport-coordinator | 生成报告 | analysis_report.json | final_report.md |

**调用方式**: 通过 Python 模块调用，非 Skill 工具调用。

```python
from bugreport_extractor import ArchiveExtractor
from bugreport_parser import LogParser
from bugreport_analyzer import BugAnalyzer
from bugreport_coordinator import AnalysisCoordinator
```

## 数据规范

详见 [DATA_CONTRACT.md](DATA_CONTRACT.md)

## Context 保护

遵循"只传路径，不传内容"原则:

| 阶段 | Context 占用 |
|------|-------------|
| extractor | ~10KB |
| parser | ~50KB |
| analyzer | ~20KB |
| coordinator | ~10KB |
| **总计** | **< 80KB** |

## 使用示例

**用户**: 帮我分析这个 bug report: /path/to/bugreport.zip

**响应**:
```
检测到分析模式: 完整分析流程

[1/4] 解压文件... ✓
[2/4] 解析日志... ✓ (发现 3 个 ANR, 5 次冻结)
[3/4] 分析问题... ✓ (发现 5 个问题)
[4/4] 生成报告... ✓

报告: ./output/final_report.md
问题摘要:
1. [HIGH] ANR in MainActivity
2. [HIGH] Frozen crash detected
...
```

## 注意事项

1. 支持格式: zip, tar.gz, tgz, gz, bz2
2. 大文件自动采样，支持 GB 级
3. 冻结分析支持: Mars/Freecess/Freezer
4. 每个子模块可独立使用（通过 Python 调用）
