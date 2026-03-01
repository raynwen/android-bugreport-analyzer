---
name: "bugreport-extractor"
description: "解压 Android bug report 归档文件 (zip/tar.gz/gz/bz2)，生成文件清单。当用户说'解压bugreport'、'只解压'时触发。"
---

# Bug Report Extractor

递归解压 Android bug report 归档文件，生成文件清单。

## 调用方式

**Python 模块调用 (推荐)**:
```python
from bugreport_extractor import ArchiveExtractor

extractor = ArchiveExtractor()
manifest = extractor.extract(
    source_path="/path/to/bugreport.zip",
    output_dir="./output"
)
```

**命令行调用**:
```bash
python -m bugreport_extractor /path/to/bugreport.zip -o ./output
```

## 输入输出

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| source_path | string | 是 | 归档文件路径 |
| output_dir | string | 否 | 输出目录，默认 `./extracted_{文件名}` |

**输出**: `{output_dir}/manifest.json`

## 支持格式

zip, tar.gz, tgz, gz, bz2

## 配置参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| max_depth | 10 | 最大递归深度 |
| max_workers | 4 | 并行线程数 |
| max_file_size_mb | 1024 | 单文件限制 |
| max_total_size_gb | 10 | 总大小限制 |

## 下一步

解压后使用 `bugreport-parser` 解析日志。
