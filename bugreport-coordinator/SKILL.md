---
name: "bugreport-coordinator"
description: "协调生成 Android bug report 最终分析报告。当用户说'生成报告'时触发。"
---

# Bug Report Coordinator

协调各模块，生成最终报告。

## 调用方式

**Python 模块调用 (推荐)**:
```python
from bugreport_coordinator import AnalysisCoordinator

coordinator = AnalysisCoordinator()
final_report = coordinator.coordinate(
    analysis_report_path="./output/analysis_report.json",
    output_dir="./output"
)
```

## 输入输出

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| analysis_report_path | string | 是 | analysis_report.json 路径 |
| output_dir | string | 否 | 输出目录 |

**输出**: `{output_dir}/final_report.md`

## 报告内容

- 问题摘要
- 详细分析
- 优先级排序
- 解决建议
- 相关日志片段

## 报告格式

- Markdown 格式
- 人类可读
- 包含关键日志引用
