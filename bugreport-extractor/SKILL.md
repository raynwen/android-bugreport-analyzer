---
name: "bugreport-extractor"
description: "Recursively extracts nested compressed bug report files (zip/tar.gz/gz/bz2), generates file manifest and metadata. Invoke when user needs to extract Android bug report archives."
---

# Bug Report Extractor

Recursively extracts all nested compressed files in Android bug reports and generates a complete file manifest.

## When to Use

Invoke this skill when:
- User provides a bug report archive (.zip, .tar.gz, .tgz, .gz, .bz2)
- Need to extract and analyze the contents of bug reports
- Need to get file listing and metadata from extracted bug reports

## Features

- **Multi-format Support**: zip, tar.gz, tg, gz, bz2
- **Disk Space Check**: Pre-check available disk space before extraction
- **Recursive Extraction**: Handle nested archives up to 10 levels deep
- **Concurrent Processing**: Configurable worker threads for parallel extraction
- **Security Limits**: Single file 1GB, total 10GB limits
- **File Tree Generation**: Generate structured file hierarchy

## Input

| Field | Description |
|-------|-------------|
| source_path | Bug report archive file path |
| output_dir | Optional output directory |

## Output

Generates `manifest.json` with:
- File tree structure
- Key files identification (logcat, ANR, tombstone, dropbox)
- Extraction statistics (file count, size, time)

## Usage Examples

### Basic Extraction
```python
from bugreport_extractor import ArchiveExtractor

extractor = ArchiveExtractor()
manifest = extractor.extract("bugreport.zip", "./output")
print(f"Extracted {manifest.extraction_stats.total_files} files")
```

### With Custom Config
```python
from bugreport_extractor import ExtractorConfig, ArchiveExtractor

config = ExtractorConfig(max_depth=5, max_workers=2)
extractor = ArchiveExtractor(config)
manifest = extractor.extract("bugreport.zip", "./output")
```

## Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| max_depth | 10 | Maximum recursion depth |
| max_workers | 4 | Parallel extraction threads |
| max_file_size_mb | 1024 | Single file size limit |
| max_total_size_gb | 10 | Total extraction size limit |
| space_multiplier | 3 | Disk space reserve ratio |
