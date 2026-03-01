---
name: "android-bugreport-analyzer"
description: "Android Bug Report 分析系统。分析 bug、冻结问题和 PLM issue。"
---

# Android Bug Report Analyzer

Android Bug Report 分析系统，提供完整的 bug report 分析流程，包括解压、解析、分析和报告生成。

## 系统架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     Android Bug Report Analyzer System                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│                          ┌─────────────────┐                                │
│                          │   用户输入解析   │                                │
│                          │  (意图识别)      │                                │
│                          └────────┬────────┘                                │
│                                   │                                          │
│           ┌───────────────────────┼───────────────────────┐                 │
│           │                       │                       │                  │
│           ▼                       ▼                       ▼                  │
│    ┌─────────────┐         ┌─────────────┐         ┌─────────────┐          │
│    │   完整分析   │         │  冻结分析   │         │  PLM Issue  │          │
│    │   (full)    │         │  (freeze)   │         │ (plm_issue) │          │
│    └──────┬──────┘         └──────┬──────┘         └──────┬──────┘          │
│           │                       │                       │                  │
│           ▼                       ▼                       │                  │
│    ┌─────────────────────────────────────────────┐       │                  │
│    │              4-Skill Pipeline               │       │                  │
│    │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌────┐│       │                  │
│    │  │extractor│→│ parser  │→│analyzer │→│coor││       │                  │
│    │  └─────────┘ └─────────┘ └─────────┘ └────┘│       │                  │
│    └─────────────────────────────────────────────┘       │                  │
│           │                       │                       │                  │
│           ▼                       ▼                       ▼                  │
│    ┌─────────────────────────────────────────────────────────────┐          │
│    │                      输出分析报告                            │          │
│    │  • final_report.md (完整报告)                                │          │
│    │  • freeze_analysis_report.md (冻结报告)                      │          │
│    │  • plm_issue_analysis.md (PLM报告)                           │          │
│    └─────────────────────────────────────────────────────────────┘          │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 触发方式

### 意图识别规则

根据用户输入自动识别分析模式:

| 模式 | 触发关键词 | 说明 |
|------|-----------|------|
| `full` | "分析bug", "分析 bugreport", "bugreport分析", "完整分析", "解析bug" | 完整分析流程 |
| `freeze` | "分析冻结", "冻结问题", "freeze分析", "mars冻结", "freecess", "分析freeze" | 冻结专项分析 |
| `plm_issue` | "分析plm issue", "plm问题分析", "issue分析", "plm问题", "分析plm" | PLM Issue 分析 |
| `quick` | "快速分析", "只解析", "只分析", "单步分析" | 单步操作 |

### 意图识别代码

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

## 子 Skills

本 skill 包含 4 个子 skills，按顺序协作完成分析:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  bugreport-     │───▶│  bugreport-     │───▶│  bugreport-     │───▶│  bugreport-     │
│  extractor      │    │  parser         │    │  analyzer       │    │  coordinator    │
│  (解压遍历)      │    │  (信息提取)      │    │  (推理分析)      │    │  (管理协调)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
       │                      │                      │                      │
       ▼                      ▼                      ▼                      ▼
  manifest.json         extracted_info.json    analysis_report.json    final_report.md
```

### 子 Skill 详情

| Skill | 功能 | 输入 | 输出 | 可独立使用 |
|-------|------|------|------|-----------|
| bugreport-extractor | 解压归档文件 | bugreport 路径 | manifest.json | ✅ |
| bugreport-parser | 解析日志提取信息 | manifest.json | extracted_info.json | ✅ |
| bugreport-analyzer | 分析问题原因 | extracted_info.json | analysis_report.json | ✅ |
| bugreport-coordinator | 协调生成报告 | analysis_report.json | final_report.md | ✅ |

## 工作流程

### 流程 1: 完整分析 (full)

当用户输入包含"分析bug"、"分析bugreport"等关键词时执行:

```
步骤 1: 获取必要信息
┌─────────────────────────────────────────────────────────────┐
│ 询问用户:                                                    │
│ 1. bug report 文件路径 (必需)                                │
│ 2. 目标应用包名 (可选，提高分析精度)                          │
│ 3. 输出目录 (可选，默认 ./output)                            │
└─────────────────────────────────────────────────────────────┘

步骤 2: 调用 extractor 解压
┌─────────────────────────────────────────────────────────────┐
│ from bugreport_extractor import ArchiveExtractor            │
│                                                              │
│ extractor = ArchiveExtractor()                               │
│ manifest = extractor.extract(                                │
│     source_path=bugreport_path,                              │
│     output_dir=output_dir                                    │
│ )                                                            │
│ # 输出: {output_dir}/manifest.json                           │
└─────────────────────────────────────────────────────────────┘

步骤 3: 调用 parser 解析
┌─────────────────────────────────────────────────────────────┐
│ from bugreport_parser import LogParser                       │
│                                                              │
│ parser = LogParser()                                         │
│ extracted = parser.parse(                                    │
│     manifest_path=f"{output_dir}/manifest.json",             │
│     package_name=package_name,                               │
│     output_dir=output_dir,                                   │
│     enable_freeze_analysis=True,                             │
│     freeze_analysis_mode="correlated"                        │
│ )                                                            │
│ # 输出: {output_dir}/extracted_info.json                     │
└─────────────────────────────────────────────────────────────┘

步骤 4: 调用 analyzer 分析
┌─────────────────────────────────────────────────────────────┐
│ from bugreport_analyzer import BugAnalyzer                   │
│                                                              │
│ analyzer = BugAnalyzer()                                     │
│ report = analyzer.analyze(                                   │
│     extracted_info_path=f"{output_dir}/extracted_info.json", │
│     output_dir=output_dir                                    │
│ )                                                            │
│ # 输出: {output_dir}/analysis_report.json                    │
└─────────────────────────────────────────────────────────────┘

步骤 5: 调用 coordinator 生成报告
┌─────────────────────────────────────────────────────────────┐
│ from bugreport_coordinator import AnalysisCoordinator        │
│                                                              │
│ coordinator = AnalysisCoordinator()                          │
│ final_report = coordinator.coordinate(                       │
│     analysis_report_path=f"{output_dir}/analysis_report.json",│
│     output_dir=output_dir                                    │
│ )                                                            │
│ # 输出: {output_dir}/final_report.md                         │
└─────────────────────────────────────────────────────────────┘

步骤 6: 输出结果
┌─────────────────────────────────────────────────────────────┐
│ 向用户展示:                                                  │
│ • 分析报告路径: {output_dir}/final_report.md                 │
│ • 发现问题数量                                               │
│ • 严重问题摘要                                               │
└─────────────────────────────────────────────────────────────┘
```

### 流程 2: 冻结问题分析 (freeze)

当用户输入包含"分析冻结"、"冻结问题"等关键词时执行:

```
步骤 1: 获取必要信息
┌─────────────────────────────────────────────────────────────┐
│ 询问用户:                                                    │
│ 1. bug report 文件路径 (必需)                                │
│ 2. 目标应用包名 (可选)                                       │
│ 3. 输出目录 (可选，默认 ./output)                            │
└─────────────────────────────────────────────────────────────┘

步骤 2-3: 解压 + 解析 (启用冻结分析)
┌─────────────────────────────────────────────────────────────┐
│ extractor = ArchiveExtractor()                               │
│ manifest = extractor.extract(bugreport_path, output_dir)     │
│                                                              │
│ parser = LogParser()                                         │
│ extracted = parser.parse(                                    │
│     manifest_path=f"{output_dir}/manifest.json",             │
│     package_name=package_name,                               │
│     output_dir=output_dir,                                   │
│     enable_freeze_analysis=True,      # 启用冻结分析         │
│     freeze_analysis_mode="correlated"  # 关联分析模式        │
│ )                                                            │
└─────────────────────────────────────────────────────────────┘

步骤 4: 分析冻结问题
┌─────────────────────────────────────────────────────────────┐
│ analyzer = BugAnalyzer()                                     │
│ report = analyzer.analyze(                                   │
│     extracted_info_path=f"{output_dir}/extracted_info.json", │
│     output_dir=output_dir                                    │
│ )                                                            │
│                                                              │
│ # 筛选冻结相关问题                                            │
│ freeze_issues = [                                            │
│     i for i in report.issues                                 │
│     if i.type in ['FROZEN_CRASH', 'FROZEN_ANR',              │
│                   'FREEZE_TIMEOUT']                          │
│ ]                                                            │
└─────────────────────────────────────────────────────────────┘

步骤 5: 生成冻结报告
┌─────────────────────────────────────────────────────────────┐
│ # 生成专门的冻结问题报告                                      │
│ output_path = f"{output_dir}/freeze_analysis_report.md"      │
│                                                              │
│ 报告内容包括:                                                 │
│ • 冻结事件统计                                               │
│ • 冻结机制分析 (Mars/Freecess/Freezer)                       │
│ • 冻结崩溃/ANR 详情                                          │
│ • 冻结原因分析                                               │
│ • 解决建议                                                   │
└─────────────────────────────────────────────────────────────┘
```

### 流程 3: PLM Issue 分析 (plm_issue)

当用户输入包含"分析plm issue"等关键词时执行:

```
步骤 1: 获取 Issue 信息
┌─────────────────────────────────────────────────────────────┐
│ 询问用户:                                                    │
│ 1. PLM Issue 文件路径 或 直接粘贴内容                        │
│ 2. 输出目录 (可选)                                           │
└─────────────────────────────────────────────────────────────┘

步骤 2: 解析 Issue
┌─────────────────────────────────────────────────────────────┐
│ if file_path.exists():                                       │
│     issue_content = read_file(file_path)                     │
│ else:                                                        │
│     issue_content = user_input                               │
│                                                              │
│ # 提取 Issue 关键信息                                         │
│ issue_info = {                                               │
│     "title": extract_title(issue_content),                   │
│     "description": extract_description(issue_content),       │
│     "attachments": extract_attachments(issue_content),       │
│     "repro_steps": extract_repro_steps(issue_content)        │
│ }                                                            │
└─────────────────────────────────────────────────────────────┘

步骤 3: 分析并生成报告
┌─────────────────────────────────────────────────────────────┐
│ # 分析 Issue 完整性                                          │
│ analysis = {                                                 │
│     "completeness": check_completeness(issue_info),          │
│     "missing_info": identify_missing_info(issue_info),       │
│     "suggestions": generate_improvement_suggestions()        │
│ }                                                            │
│                                                              │
│ # 输出: {output_dir}/plm_issue_analysis.md                   │
└─────────────────────────────────────────────────────────────┘
```

### 流程 4: 快速分析/单步操作 (quick)

当用户只需要特定步骤时:

```
步骤 1: 确认操作类型
┌─────────────────────────────────────────────────────────────┐
│ 请选择操作:                                                  │
│ 1. extractor - 仅解压                                        │
│ 2. parser - 仅解析 (需要先有 manifest.json)                  │
│ 3. analyzer - 仅分析 (需要先有 extracted_info.json)          │
└─────────────────────────────────────────────────────────────┘

步骤 2: 执行对应操作
┌─────────────────────────────────────────────────────────────┐
│ 根据用户选择调用对应的子 skill                                │
│ 输出对应的中间文件                                            │
└─────────────────────────────────────────────────────────────┘
```

## 数据交互规范

各 skill 之间通过 JSON 文件传递数据，字段定义见 [DATA_CONTRACT.md](DATA_CONTRACT.md)。

### 核心数据文件

| 文件 | 生成者 | 消费者 | 说明 |
|------|--------|--------|------|
| manifest.json | extractor | parser | 文件清单和关键文件索引 |
| extracted_info.json | parser | analyzer | 日志、崩溃、冻结信息 |
| analysis_report.json | analyzer | coordinator | 问题、原因、建议 |
| final_report.md | coordinator | 用户 | 最终人类可读报告 |

## 使用示例

### 示例 1: 完整分析

**用户**: 帮我分析这个 bug report: /path/to/bugreport.zip

**响应**:
```
检测到分析模式: 完整分析流程

请确认以下信息:
- Bug report 文件: /path/to/bugreport.zip ✓
- 目标应用包名: (未提供，将分析所有内容)
- 输出目录: ./output

确认开始分析? (y/n): y

[1/4] 解压文件...
  - 解压完成: 150 个文件

[2/4] 解析日志...
  - 解析完成: 150000 条日志
  - 发现 3 个 ANR
  - 检测到冻结事件 5 次

[3/4] 分析问题...
  - 发现 5 个问题
  - 其中 2 个高危问题

[4/4] 生成报告...
  - 报告已生成: ./output/final_report.md

分析完成! 发现问题:
1. [HIGH] ANR detected in MainActivity
2. [HIGH] Frozen crash detected
3. [MEDIUM] GC overhead detected
...
```

### 示例 2: 冻结问题分析

**用户**: 分析一下冻结问题，文件是 /path/to/bugreport.tar.gz，包名是 com.example.app

**响应**:
```
检测到分析模式: 冻结问题专项分析

[1/3] 解压文件...
  - 解压完成

[2/3] 解析冻结信息...
  - 冻结事件: 5 个
  - 冻结崩溃: 2 个
  - 冻结 ANR: 1 个
  - 冻结机制: Mars (3次), Freecess (2次)

[3/3] 分析冻结原因...
  - 发现 3 个冻结相关问题

报告已生成: ./output/freeze_analysis_report.md

冻结问题摘要:
┌──────────────────────────────────────────────────────────┐
│ 冻结机制统计                                              │
├──────────────────────────────────────────────────────────┤
│ Mars 冻结: 3 次                                          │
│ Freecess 冻结: 2 次                                      │
│ 冻结后崩溃: 2 次                                          │
│ 冻结后 ANR: 1 次                                          │
├──────────────────────────────────────────────────────────┤
│ 主要问题:                                                │
│ 1. 应用在冻结状态下处理广播导致崩溃                        │
│ 2. 冻结超时后触发 ANR                                     │
└──────────────────────────────────────────────────────────┘
```

### 示例 3: 单步操作

**用户**: 只需要解压这个 bug report: /path/to/bugreport.zip

**响应**:
```
检测到分析模式: 快速分析 - 仅解压

正在解压...
  - 解压完成: 150 个文件
  - 输出目录: ./output

生成的文件:
  - manifest.json: 文件清单
  - 关键文件位置已识别

如需继续分析，可以使用:
  - parser: 解析日志
  - analyzer: 分析问题
```

## Context 窗口保护机制

**核心原则**: 每个 Skill 只保留必要的上下文信息传递给下一个，确保 AI Agent 的 context 窗口不会被撑爆。

### 保护策略

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     Context 窗口保护机制                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  原始数据                                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Bug Report (1-2GB)                                                  │   │
│  │  • logcat (500MB-1GB)                                               │   │
│  │  • ANR traces (10-50MB)                                             │   │
│  │  • Tombstones (10-100MB)                                            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                               │
│                              ▼                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  技术手段:                                                           │   │
│  │  1. 流式处理 - 不加载到内存                                          │   │
│  │  2. 智能采样 - 关键事件100%保留，普通日志采样                         │   │
│  │  3. 去重压缩 - 相同模式聚合计数                                      │   │
│  │  4. URI引用 - 大文本存文件，JSON只存路径                             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                               │
│                              ▼                                               │
│  传递给 AI 的数据                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  extracted_info.json (通常 < 500KB)                                  │   │
│  │  • 摘要信息 (直接存储)                                               │   │
│  │  • 堆栈: 前3行摘要 + URI引用                                         │   │
│  │  • 日志: 统计信息 + URI引用                                          │   │
│  │  • 错误: 消息摘要 + URI引用                                          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1. 文件驱动传递

**只传递文件路径，不传递内容**:

```python
# 正确做法 ✅
extracted = parser.parse(manifest_path="./output/manifest.json")
# AI 只看到: "./output/extracted_info.json" 这个路径

# 错误做法 ❌
extracted = parser.parse(manifest_content=manifest_json_string)
# AI 会看到整个 manifest 内容
```

### 2. URI + 摘要模式

大段文本不直接存储在 JSON 中:

| 内容类型 | 存储方式 | 示例 |
|---------|---------|------|
| 摘要信息 | 直接存储 | `"total_entries": 150000` |
| 堆栈信息 | 前3行 + URI | `"top_frames": [...], "uri": "file://stacks/anr_001.txt"` |
| 完整日志 | 仅 URI | `"detail_uri": "file://contexts/anr_001.log"` |
| 错误消息 | 前100字符 + URI | `"message_summary": "Connection failed...", "detail_uri": "..."` |

### 3. 智能采样策略

当文件过大时自动触发:

| 触发条件 | 采样策略 |
|---------|---------|
| 文件 > 500MB | 启动采样 |
| 条目 > 100,000 | 启动采样 |

**采样规则**:

| 数据类型 | 保留比例 | 说明 |
|---------|---------|------|
| 关键事件 (ANR/Crash/Error) | 100% | 全部保留 |
| 关键事件前后30秒日志 | 100% | 上下文完整保留 |
| 高频模式日志 | 10% | 相同模式只保留样本 |
| 普通日志 (INFO/DEBUG) | 5% | 均匀采样 |

### 4. 去重压缩

相同模式的日志聚合计数:

```json
{
  "aggregated_patterns": [
    {
      "pattern": "Connection timeout to *.example.com",
      "count": 50,
      "first_occurrence": "2024-01-15T09:00:00Z",
      "sample": "Connection timeout to api.example.com"
    }
  ]
}
```

### 5. 流式处理

大文件不加载到内存:

```python
# 流式读取 - 内存占用恒定
with open(large_file, 'r') as f:
    for line in f:  # 逐行处理
        if is_relevant(line):
            process(line)
        # 处理完立即释放，不保留
```

### 6. 按需读取机制

AI 分析时按需读取详细内容:

```
分析阶段：仅使用摘要信息进行推理
      ↓
需要细节时：通过 URI 读取具体内容
      ↓
读取后：立即释放，不保留在上下文中
```

### Context 大小估算

**重要**: 以下限制基于主流 LLM 的 context 窗口安全使用范围

| 阶段 | 输入大小 | 输出大小 | AI Context 占用 |
|------|---------|---------|----------------|
| extractor | 1-2GB (文件) | ~10KB (manifest.json) | ~10KB |
| parser | ~10KB (manifest) | ~50KB (extracted_info.json) | ~50KB |
| analyzer | ~50KB (extracted_info) | ~20KB (analysis_report.json) | ~20KB |
| coordinator | ~20KB (analysis_report) | ~10KB (final_report.md) | ~10KB |

**总计**: 即使分析 2GB 的 bug report，AI 的 context 窗口占用不超过 **80KB**。

### 主流 Agent 兼容性

| 模型 | Context 窗口 | 本系统占用 | 兼容性 |
|------|-------------|-----------|--------|
| GPT-4 Turbo | 128K tokens (~96KB) | ~80KB (83%) | ✅ 兼容 |
| Claude 3 | 200K tokens (~150KB) | ~80KB (53%) | ✅ 兼容 |
| Gemini 1.5 Pro | 1M tokens (~750KB) | ~80KB (11%) | ✅ 完全兼容 |

## 注意事项

1. **文件格式支持**: zip, tar.gz, tgz, gz, bz2
2. **大文件处理**: 自动使用流式处理和采样，支持 GB 级文件
3. **冻结分析**: 支持 Mars/Freecess/Freezer 三种冻结机制
4. **独立使用**: 每个子 skill 可独立调用，只需提供正确的输入文件
5. **错误隔离**: 单个 skill 出错不会影响已完成的步骤，中间文件保留
6. **Context 保护**: 所有 skill 遵循"只传路径，不传内容"原则

## 配置参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| max_depth | 10 | 解压最大递归深度 |
| max_workers | 4 | 并行处理线程数 |
| enable_freeze_analysis | true | 启用冻结分析 |
| freeze_analysis_mode | correlated | 冻结分析模式 (independent/correlated) |
| confidence_threshold | 0.8 | 置信度阈值 |
| max_iterations | 3 | 分析迭代次数 |
