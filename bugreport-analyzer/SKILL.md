---
name: "bugreport-analyzer"
description: "分析 Android bug report 问题原因，生成分析报告。当用户说'分析问题'、'只分析'时触发。"
---

# Bug Report Analyzer

分析 bug report 中的问题，推断原因。

## 调用方式

**Python 模块调用 (推荐)**:
```python
from bugreport_analyzer import BugAnalyzer

analyzer = BugAnalyzer()
report = analyzer.analyze(
    extracted_info_path="./output/extracted_info.json",
    output_dir="./output"
)
```

## 输入输出

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| extracted_info_path | string | 是 | extracted_info.json 路径 |
| output_dir | string | 否 | 输出目录 |

**输出**: `{output_dir}/analysis_report.json`

## 分析内容

- 崩溃原因分析
- ANR 原因分析
- 冻结问题分析
- 问题优先级排序
- 解决建议

## 配置参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| confidence_threshold | 0.8 | 置信度阈值 |
| max_iterations | 3 | 分析迭代次数 |

## 下一步

分析后使用 `bugreport-coordinator` 生成报告。
