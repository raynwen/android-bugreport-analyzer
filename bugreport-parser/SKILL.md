---
name: "bugreport-parser"
description: "解析 Android bug report 日志，提取崩溃、ANR、冻结等信息。当用户说'解析日志'、'只解析'时触发。"
---

# Bug Report Parser

解析 bug report 日志，提取关键信息。

## 调用方式

**Python 模块调用 (推荐)**:
```python
from bugreport_parser import LogParser

parser = LogParser()
extracted = parser.parse(
    manifest_path="./output/manifest.json",
    package_name="com.example.app",
    output_dir="./output",
    enable_freeze_analysis=True
)
```

## 输入输出

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| manifest_path | string | 是 | manifest.json 路径 |
| package_name | string | 否 | 目标应用包名 |
| output_dir | string | 否 | 输出目录 |
| enable_freeze_analysis | bool | 否 | 启用冻结分析 |

**输出**: `{output_dir}/extracted_info.json`

## 提取内容

- 系统信息 (设备、版本、内存)
- 崩溃信息 (Java/Native)
- ANR 信息
- 冻结事件 (Mars/Freecess/Freezer)
- 日志统计

## 配置参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| enable_freeze_analysis | True | 启用冻结分析 |
| freeze_analysis_mode | correlated | 分析模式 |

## 下一步

解析后使用 `bugreport-analyzer` 分析问题。
