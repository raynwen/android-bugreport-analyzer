---
name: "bugreport-analyzer"
description: "分析 bug report 提取的信息，识别问题类型、根本原因并提供建议。支持冻结问题分析 (Mars/Freecess/Freezer)。当用户需要分析 bug、分析崩溃、分析 ANR、分析性能问题、分析冻结问题时触发。"
---

# Bug Report Analyzer (推理分析)

分析提取的 bug report 信息，识别问题类型和根本原因。

## 独立使用

此 skill 可独立使用，只需提供 `extracted_info.json` 文件。

## 触发时机

- 用户说"分析问题"、"只分析"、"分析原因"
- 需要识别崩溃/ANR 根本原因
- 需要分析性能问题
- 需要分析冻结相关问题

## 输入

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| extracted_info_path | string | 是 | parser 生成的 extracted_info.json 路径 |
| output_dir | string | 否 | 输出目录，默认为 extracted_info.json 同目录 |

## 输出

生成文件:
- `{output_dir}/analysis_report.json` - 分析报告

analysis_report.json 结构:
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
          "confidence": 0.9
        }
      ],
      "suggestions": [
        {
          "priority": 1,
          "action": "Move I/O operation to background thread"
        }
      ],
      "freeze_info": {
        "freeze_mechanism": "Mars",
        "freeze_reason": "bg_check"
      }
    }
  ],
  "needs_deeper_analysis": false
}
```

## 调用方式

### Python 调用
```python
from bugreport_analyzer import BugAnalyzer

analyzer = BugAnalyzer()
report = analyzer.analyze(
    extracted_info_path="./output/extracted_info.json",
    output_dir="./output"
)

print(f"发现 {len(report.issues)} 个问题")
for issue in report.issues:
    print(f"  [{issue.severity}] {issue.title}")
```

### 命令行调用
```bash
python -m bugreport_analyzer ./output/extracted_info.json
```

## 功能特性

- **问题识别**: 检测 ANR、崩溃、性能问题
- **根因分析**: 识别阻塞 I/O、死锁、NPE 等
- **优先级排序**: 基于置信度、严重程度、频率计算优先级
- **影响评估**: 评估用户影响
- **建议生成**: 提供可操作的建议
- **冻结问题分析**: 专门的冻结崩溃/ANR 分析

## 支持的问题类型

| 类型 | 分类 | 说明 |
|------|------|------|
| ANR | crash | 应用无响应 |
| CRASH | crash | 应用崩溃 |
| PERFORMANCE | performance | 性能问题 |
| FROZEN_CRASH | freeze | 冻结状态下崩溃 |
| FROZEN_ANR | freeze | 冻结状态下 ANR |
| FREEZE_TIMEOUT | freeze | 冻结操作超时 |

## 优先级计算

分析器使用加权评分:
- 置信度: 40%
- 严重程度: 25%
- 频率: 20%
- 修复复杂度: 15%

## 配置参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| enable_freeze_analysis | true | 启用冻结问题分析 |
| freeze_window_seconds | 60 | 冻结关联时间窗口 |
| analysis_mode | correlated | 冻结分析模式 |

## 错误处理

| 错误类型 | 处理方式 |
|---------|---------|
| extracted_info.json 不存在 | 抛出 FileNotFoundError |
| JSON 格式错误 | 抛出 ValueError |
| 无问题发现 | 返回空 issues 列表 |

## 下一步

分析完成后，可以使用 `bugreport-coordinator` 生成最终报告:
```python
from bugreport_coordinator import AnalysisCoordinator

coordinator = AnalysisCoordinator()
final_report = coordinator.coordinate(
    analysis_report_path="./output/analysis_report.json"
)
```
