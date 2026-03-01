---
name: "android-bugreport-analyzer"
description: "Android Bug Report 分析系统入口。当用户需要分析 bug、解析 bug、分析冻结问题、分析 plm issue 时触发。系统会引导用户输入文件路径并自动选择合适的分析流程。"
---

# Android Bug Report Analyzer

Android Bug Report 全流程分析系统，支持崩溃、ANR、性能问题、冻结问题等多种场景分析。

## 触发条件

当用户输入包含以下关键词时自动触发：

| 触发场景 | 关键词示例 |
|---------|-----------|
| 分析/解析 bug | "分析bug"、"解析bug"、"分析bugreport"、"bug报告分析" |
| 分析冻结问题 | "分析冻结"、"分析freeze"、"冻结问题"、"mars冻结"、"freecess" |
| 分析 PLM Issue | "分析plm issue"、"plm问题分析"、"issue分析" |
| 完整分析流程 | "完整分析"、"全流程分析" |

## 工作流程

```
用户输入触发词
      │
      ▼
┌─────────────────┐
│  询问文件路径   │ ◄── 等待用户输入 bugreport/issue 文件路径
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  判断分析类型   │
└────────┬────────┘
         │
    ┌────┴────┬──────────┬──────────┐
    ▼         ▼          ▼          ▼
┌───────┐ ┌───────┐ ┌────────┐ ┌────────┐
│完整流程│ │冻结分析│ │PLM分析 │ │快速分析│
└───┬───┘ └───┬───┘ └───┬────┘ └───┬────┘
    │         │          │          │
    ▼         ▼          ▼          ▼
 4步流水线  冻结专项    Issue解析   单模块分析
```

## 分析模式

### 模式 1: 完整分析流程

适用于需要完整分析 bug report 的场景。

```python
# 调用链路
bugreport-extractor → bugreport-parser → bugreport-analyzer → bugreport-coordinator
```

**触发词**: "完整分析"、"全流程分析"、"分析这个bug"

**需要输入**:
- Bug report 文件路径 (.zip, .tar.gz 等)
- 目标应用包名 (可选)

**输出**: 完整分析报告 (final_report.md)

---

### 模式 2: 冻结问题专项分析

适用于分析 Mars/Freecess/Freezer 相关的冻结问题。

**触发词**: "分析冻结"、"freeze分析"、"mars冻结问题"

**需要输入**:
- Bug report 文件路径
- 目标应用包名

**分析内容**:
- 冻结事件时间线
- 冻结与崩溃/ANR 的关联
- 冻结机制识别 (Mars/Freecess/Freezer)
- 冻结原因分析

---

### 模式 3: PLM Issue 分析

适用于分析 PLM 系统中的 Issue。

**触发词**: "分析plm issue"、"plm问题"

**需要输入**:
- Issue 文件路径或内容

**分析内容**:
- Issue 信息提取
- 问题分类与优先级
- 解决建议

---

### 模式 4: 快速分析

适用于只需要特定模块分析的场景。

**触发词**: "只解析"、"只分析"、"快速分析"

**可选模块**:
- extractor: 仅解压
- parser: 仅解析
- analyzer: 仅分析

---

## 使用示例

### 示例 1: 完整分析

```
用户: 帮我分析这个 bug report
助手: 请提供 bug report 文件的路径:
用户: /path/to/bugreport.zip
助手: 请输入目标应用的包名 (可选，直接回车跳过):
用户: com.example.app
助手: [开始分析流程...]
```

### 示例 2: 冻结问题分析

```
用户: 分析一下冻结问题
助手: 请提供 bug report 文件的路径:
用户: /path/to/bugreport.zip
助手: 请输入目标应用的包名:
用户: com.example.app
助手: [开始冻结专项分析...]
```

### 示例 3: PLM Issue 分析

```
用户: 帮我分析这个 plm issue
助手: 请提供 issue 文件的路径或直接粘贴内容:
用户: /path/to/issue.json
助手: [开始 Issue 分析...]
```

## 子模块

| 模块 | 功能 | 触发场景 |
|------|------|---------|
| [bugreport-extractor](bugreport-extractor/SKILL.md) | 解压归档文件 | 需要解压 zip/tar.gz 等 |
| [bugreport-parser](bugreport-parser/SKILL.md) | 解析日志信息 | 需要提取日志、分析冻结 |
| [bugreport-analyzer](bugreport-analyzer/SKILL.md) | 问题分析推理 | 需要识别问题类型和原因 |
| [bugreport-coordinator](bugreport-coordinator/SKILL.md) | 流程协调报告 | 需要生成最终报告 |

## 交互流程

当触发此 Skill 时，系统会：

1. **识别意图**: 根据用户输入判断分析类型
2. **询问路径**: 提示用户输入文件路径
3. **收集参数**: 根据分析类型收集必要参数
4. **执行分析**: 调用相应的子模块
5. **输出结果**: 生成分析报告并给出建议

## 配置

| 参数 | 默认值 | 说明 |
|------|--------|------|
| default_output_dir | ./output | 默认输出目录 |
| enable_freeze_analysis | true | 启用冻结分析 |
| freeze_analysis_mode | correlated | 冻结分析模式 |
| max_iterations | 3 | 最大迭代次数 |
| confidence_threshold | 0.8 | 置信度阈值 |
