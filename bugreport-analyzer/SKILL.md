---
name: "bugreport-analyzer"
description: "分析 bug report 提取的信息，识别问题类型、根本原因并提供建议。支持冻结问题分析 (Mars/Freecess/Freezer)。当用户需要分析 bug、分析崩溃、分析 ANR、分析性能问题、分析冻结问题时触发。"
---

# Bug Report Analyzer

Analyzes extracted bug report information to identify problem types and root causes.

## When to Use

Invoke this skill when:
- User wants to identify crash/ANR root causes
- Need to analyze performance issues
- Need to analyze freeze-related problems (Mars/Freecess/Freezer)
- Need to generate issue reports with recommendations

## Features

- **Issue Identification**: Detect ANR, Crash, Performance issues
- **Root Cause Analysis**: Identify blocking I/O, deadlocks, NPE, etc.
- **Priority Ranking**: Calculate issue priority based on confidence, severity, frequency
- **Impact Assessment**: Evaluate user impact and affected users
- **Suggestion Generation**: Provide actionable recommendations
- **Freeze Issue Analysis**: Specialized analysis for frozen crashes/ANRs

## Input

| Field | Description |
|-------|-------------|
| extracted_info_path | Path to extracted_info.json from parser |
| output_dir | Optional output directory |

## Output

Generates `analysis_report.json` with:
- Identified issues with severity and confidence
- Possible causes ranked by priority
- Timeline of events
- Impact assessment
- Actionable suggestions

## Supported Issue Types

| Category | Subtypes |
|---------|----------|
| Crash | ANR, Java Crash, Native Crash |
| Performance | UI lag, Slow startup, Memory leak |
| Function | Permission, Network, Storage |
| **Freeze** | **Mars freeze, Freecess freeze, Frozen crash/ANR** |

## Freeze Issue Types

| Type | Description |
|------|-------------|
| FROZEN_CRASH | Crash occurred while app was frozen |
| FROZEN_ANR | ANR occurred while app was frozen |
| FREEZE_TIMEOUT | Freeze operation timed out |
| SUSPICIOUS_FREEZE_PATTERN | Frequent freeze pattern detected |

## Usage Examples

### Basic Analysis
```python
from bugreport_analyzer import BugAnalyzer

analyzer = BugAnalyzer()
report = analyzer.analyze(
    "extracted_info.json",
    "./output"
)
print(f"Found {len(report.issues)} issues")
```

### Analyzing Freeze Issues
```python
analyzer = BugAnalyzer()
report = analyzer.analyze("extracted_info.json", "./output")

for issue in report.issues:
    if hasattr(issue, 'freeze_info') and issue.freeze_info:
        print(f"Freeze issue: {issue.title}")
        print(f"  Mechanism: {issue.freeze_info.freeze_mechanism}")
        print(f"  Reason: {issue.freeze_info.freeze_reason}")
```

### Priority Calculation
The analyzer uses weighted scoring:
- Confidence: 40%
- Severity: 25%
- Frequency: 20%
- Fix Complexity: 15%

## Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| enable_freeze_analysis | true | Enable freeze issue analysis |
| freeze_window_seconds | 60 | Time window for freeze correlation |
| analysis_mode | correlated | Freeze analysis mode |
