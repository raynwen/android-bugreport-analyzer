---
name: "bugreport-parser"
description: "Extracts and parses key information from large bug report files using keyword matching and pattern recognition. Supports freeze analysis for Mars/Freecess/Freezer. Invoke when user needs to analyze Android bug reports for crashes, ANRs, or freeze issues."
---

# Bug Report Parser

Extracts key information from large bug report files using streaming, keyword matching, and pattern recognition.

## When to Use

Invoke this skill when:
- User wants to extract logs from bug reports
- Need to filter logs by package name or UID
- Need to analyze freeze-related issues (Mars/Freecess/Freezer)
- Need to process large files with memory efficiency

## Features

- **Streaming Processing**: Handle large files without loading into memory
- **Multi-keyword Matching**: Aho-Corasick algorithm for efficient pattern matching
- **Package/UID Filtering**: Filter logs by target application
- **Auto File Type Detection**: Identify logcat, ANR, tombstone formats
- **Deduplication**: Remove duplicate log entries
- **Intelligent Sampling**: Sample large files while preserving key events
- **Freeze Analysis**: Analyze Mars/Freecess/Freezer freeze events

## Input

| Field | Description |
|-------|-------------|
| manifest_path | Path to manifest.json from extractor |
| package_name | Target application package name |
| output_dir | Optional output directory |

## Output

Generates `extracted_info.json` with:
- Filtered log entries
- Crash/ANR information
- Error and warning summaries
- Performance issues
- Freeze analysis (if enabled)

## Freeze Analysis Modes

### Mode 1: Independent Analysis
Analyzes freeze events only without correlating with crashes/ANRs.

```python
extracted = parser.parse(
    "manifest.json",
    "com.example.app",
    enable_freeze_analysis=True,
    freeze_analysis_mode="independent"
)
```

### Mode 2: Correlated Analysis
Correlates freeze events with crashes and ANRs.

```python
extracted = parser.parse(
    "manifest.json",
    "com.example.app",
    enable_freeze_analysis=True,
    freeze_analysis_mode="correlated"
)
```

## Usage Examples

### Basic Parsing
```python
from bugreport_parser import LogParser

parser = LogParser()
extracted_info = parser.parse(
    "manifest.json",
    "com.example.app",
    "./output"
)
print(f"Extracted {extracted_info.summary['total_entries']} log entries")
```

### With Freeze Analysis
```python
parser = LogParser()
extracted = parser.parse(
    manifest_path="manifest.json",
    package_name="com.example.app",
    output_dir="./output",
    enable_freeze_analysis=True,
    freeze_analysis_mode="correlated"
)

freeze_info = extracted.freeze_analysis
print(f"Freeze events: {len(freeze_info.freeze_events)}")
print(f"Frozen crashes: {freeze_info.anomaly_summary.frozen_crashes}")
```

## Key Log Keywords

| Category | Keywords |
|----------|----------|
| Freeze | am_freeze, am_unfreeze, mars, freecess, BaseRestrictionMgr, FROZEN |
| Crash | ANR, CRASH, FATAL, Exception |
| Error | ERROR, Exception, fail |
| Performance | GC, memory, cpu |

## Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| max_workers | 4 | Parallel processing threads |
| chunk_size | 10000 | Streaming chunk size |
| trigger_sample_size_mb | 500 | Size threshold for sampling |
| key_event_window_seconds | 30 | Time window for context extraction |
