---
name: "bugreport-coordinator"
description: "协调 bug report 分析工作流，管理迭代并生成最终报告。当用户需要完整分析流程、生成分析报告、协调多个分析模块时触发。"
---

# Bug Report Coordinator (管理协调)

协调整体分析工作流，管理迭代，生成最终报告。

## 独立使用

此 skill 可独立使用，只需提供 `analysis_report.json` 文件。

## 触发时机

- 用户说"生成报告"、"协调分析"
- 需要生成人类可读的最终报告
- 需要迭代改进分析结果

## 输入

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| analysis_report_path | string | 是 | analyzer 生成的 analysis_report.json 路径 |
| output_dir | string | 否 | 输出目录，默认为 analysis_report.json 同目录 |

## 输出

生成文件:
- `{output_dir}/final_report.md` - 最终人类可读报告

final_report.md 结构:
```markdown
# Android Bug Report 分析报告

## 概述
- **分析时间**: 2024-01-15T10:32:00
- **问题数量**: 5
- **严重程度**: HIGH

## 问题列表

### 问题 1: ANR detected in MainActivity [HIGH]

**问题描述**
ANR occurred due to input dispatching timeout

**可能原因**
1. **BLOCKING_IO** (优先级分数: 0.92)
   - Main thread blocked on I/O operation

**建议方案**
1. **[优先级高]** Move I/O operation to background thread

---

## 总结
本次分析发现 5 个问题，其中 2 个高危问题需要立即处理。
```

## 调用方式

### Python 调用
```python
from bugreport_coordinator import AnalysisCoordinator

coordinator = AnalysisCoordinator()
final_report = coordinator.coordinate(
    analysis_report_path="./output/analysis_report.json",
    output_dir="./output"
)

print(f"报告已生成: {final_report}")
```

### 命令行调用
```bash
python -m bugreport_coordinator ./output/analysis_report.json
```

## 功能特性

- **工作流协调**: 编排完整的 4-skill 流水线
- **迭代控制**: 最多 3 轮深度分析
- **置信度阈值**: 自动判断是否需要更多分析
- **报告生成**: 创建 markdown 最终报告

## 迭代逻辑

协调器在以下情况迭代:
1. 报告中 `needs_deeper_analysis` 标志为 true
2. 问题平均置信度 < 阈值 (默认 0.8)

每次迭代:
- 置信度分数增加 10%
- 重新评估可能原因
- 置信度 >= 阈值或达到最大迭代次数时停止

## 配置参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| max_iterations | 3 | 最大迭代轮数 |
| confidence_threshold | 0.8 | 停止迭代的阈值 |
| enable_iteration | true | 启用迭代功能 |

## 报告格式

生成的报告包含:

| 章节 | 内容 |
|------|------|
| 概述 | 分析时间、问题数量、严重程度 |
| 问题列表 | 每个问题的详细描述、原因、建议 |
| 时间线 | 事件发生顺序 |
| 总结 | 问题摘要和优先建议 |

## 错误处理

| 错误类型 | 处理方式 |
|---------|---------|
| analysis_report.json 不存在 | 抛出 FileNotFoundError |
| JSON 格式错误 | 抛出 ValueError |
| 无问题 | 生成"未发现问题"报告 |

## 完整流水线示例

```python
from bugreport_extractor import ArchiveExtractor
from bugreport_parser import LogParser
from bugreport_analyzer import BugAnalyzer
from bugreport_coordinator import AnalysisCoordinator

def analyze_bug_report(bugreport_path, package_name, output_dir):
    # 步骤 1: 解压
    extractor = ArchiveExtractor()
    manifest = extractor.extract(bugreport_path, output_dir)
    
    # 步骤 2: 解析
    parser = LogParser()
    extracted = parser.parse(
        f"{output_dir}/manifest.json",
        package_name,
        output_dir
    )
    
    # 步骤 3: 分析
    analyzer = BugAnalyzer()
    report = analyzer.analyze(
        f"{output_dir}/extracted_info.json",
        output_dir
    )
    
    # 步骤 4: 协调
    coordinator = AnalysisCoordinator()
    final_report = coordinator.coordinate(
        f"{output_dir}/analysis_report.json",
        output_dir
    )
    
    return final_report
```
