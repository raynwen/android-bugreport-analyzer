---
name: "bugreport-coordinator"
description: "协调 bug report 分析工作流，管理迭代并生成最终报告。当用户需要完整分析流程、生成分析报告、协调多个分析模块时触发。"
---

# Bug Report Coordinator

Coordinates the overall analysis workflow, manages iteration, and generates final reports.

## When to Use

Invoke this skill when:
- User wants to complete the full analysis workflow
- Need to coordinate multiple analysis skills
- Need to generate human-readable final reports
- Need to iterate and improve analysis results

## Features

- **Workflow Coordination**: Orchestrates the complete 4-skill pipeline
- **Iteration Control**: Up to 3 rounds of deeper analysis
- **Confidence Threshold**: Automatically determines if more analysis is needed
- **Report Generation**: Creates markdown final reports

## Input

| Field | Description |
|-------|-------------|
| analysis_report_path | Path to analysis_report.json from analyzer |
| output_dir | Optional output directory |

## Output

Generates `final_report.md` with:
- Executive summary
- Detailed issue descriptions
- Root cause analysis
- Timeline of events
- Prioritized recommendations

## Workflow

```
1. Receive analysis_report.json
       │
       ▼
2. Check confidence threshold
       │
       ▼
3. Iterate if needed (max 3 rounds)
       │
       ▼
4. Generate final markdown report
```

## Usage Examples

### Basic Coordination
```python
from bugreport_coordinator import AnalysisCoordinator

coordinator = AnalysisCoordinator()
final_report = coordinator.coordinate(
    "analysis_report.json",
    "./output"
)
print(f"Report generated: {final_report}")
```

### With Custom Config
```python
from bugreport_coordinator import CoordinatorConfig, AnalysisCoordinator

config = CoordinatorConfig(
    max_iterations=3,
    confidence_threshold=0.8
)
coordinator = AnalysisCoordinator()
final_report = coordinator.coordinate("analysis_report.json", "./output")
```

## Iteration Logic

The coordinator will iterate when:
1. `needs_deeper_analysis` flag is true in report
2. Average confidence of issues < threshold

Each iteration:
- Increases confidence scores by 10%
- Re-evaluates possible causes
- Stops when confidence >= threshold or max iterations reached

## Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| max_iterations | 3 | Maximum iteration rounds |
| confidence_threshold | 0.8 | Threshold to stop iterating |
| enable_iteration | true | Enable iteration feature |

## Full Pipeline Example

```python
from bugreport_extractor import ArchiveExtractor
from bugreport_parser import LogParser
from bugreport_analyzer import BugAnalyzer
from bugreport_coordinator import AnalysisCoordinator

def analyze_bug_report(bugreport_path, package_name, output_dir):
    # Step 1: Extract
    extractor = ArchiveExtractor()
    manifest = extractor.extract(bugreport_path, output_dir)
    
    # Step 2: Parse
    parser = LogParser()
    extracted = parser.parse(
        f"{output_dir}/manifest.json",
        package_name,
        output_dir
    )
    
    # Step 3: Analyze
    analyzer = BugAnalyzer()
    report = analyzer.analyze(
        f"{output_dir}/extracted_info.json",
        output_dir
    )
    
    # Step 4: Coordinate
    coordinator = AnalysisCoordinator()
    final_report = coordinator.coordinate(
        f"{output_dir}/analysis_report.json",
        output_dir
    )
    
    return final_report
```
