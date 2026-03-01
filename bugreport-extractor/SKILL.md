---
name: "bugreport-extractor"
description: "解压 Android bug report 归档文件 (zip/tar.gz/gz/bz2)，生成文件清单和元数据。当用户需要解压 bug report、提取 bugreport 文件、处理压缩的 bug 报告时触发。"
---

# Bug Report Extractor (解压遍历)

递归解压 Android bug report 中的所有嵌套压缩文件，生成完整的文件清单。

## 独立使用

此 skill 可独立使用，无需依赖其他 skill。

## 触发时机

- 用户提供 bug report 归档文件 (.zip, .tar.gz, .tgz, .gz, .bz2)
- 用户说"解压bugreport"、"只解压"、"提取文件"
- 需要解压并分析 bug report 内容

## 输入

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| source_path | string | 是 | Bug report 归档文件路径 |
| output_dir | string | 否 | 输出目录，默认为 `./extracted_{文件名}` |

## 输出

生成文件:
- `{output_dir}/manifest.json` - 文件清单和元数据

manifest.json 结构:
```json
{
  "version": "1.0",
  "extracted_at": "2024-01-15T10:30:00",
  "source_file": "/path/to/bugreport.zip",
  "extraction_stats": {
    "total_files": 150,
    "total_size": "256.5MB",
    "extraction_time": "12.3s",
    "max_depth_reached": 3
  },
  "key_files": {
    "logcat": "FS/data/logcat.txt",
    "anr_dir": "FS/data/anr",
    "tombstone_dir": "FS/data/tombstones"
  }
}
```

## 调用方式

### Python 调用
```python
from bugreport_extractor import ArchiveExtractor

extractor = ArchiveExtractor()
manifest = extractor.extract(
    source_path="/path/to/bugreport.zip",
    output_dir="./output"
)

print(f"解压完成: {manifest.extraction_stats.total_files} 个文件")
print(f"关键文件: {manifest.key_files}")
```

### 命令行调用
```bash
python -m bugreport_extractor /path/to/bugreport.zip -o ./output
```

## 功能特性

- **多格式支持**: zip, tar.gz, tgz, gz, bz2
- **递归解压**: 处理最多 10 层嵌套归档
- **磁盘空间检查**: 解压前检查可用空间
- **并行处理**: 可配置并行线程数
- **安全限制**: 单文件 1GB，总计 10GB 限制
- **关键文件识别**: 自动识别 logcat, ANR, tombstone 等关键文件

## 配置参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| max_depth | 10 | 最大递归深度 |
| max_workers | 4 | 并行解压线程数 |
| max_file_size_mb | 1024 | 单文件大小限制 (MB) |
| max_total_size_gb | 10 | 总解压大小限制 (GB) |
| space_multiplier | 3 | 磁盘空间预留倍数 |

## 错误处理

| 错误类型 | 处理方式 |
|---------|---------|
| 文件不存在 | 抛出 FileNotFoundError |
| 格式不支持 | 抛出 ValueError |
| 磁盘空间不足 | 抛出 IOError |
| 文件过大 | 抛出 IOError |

## 下一步

解压完成后，可以使用 `bugreport-parser` 解析日志:
```python
from bugreport_parser import LogParser

parser = LogParser()
extracted = parser.parse(
    manifest_path="./output/manifest.json",
    package_name="com.example.app"
)
```
