# Android Bug Report YAML 配置更新子方案

> **作者**: 闫文峰
> **版本**: 1.0
> **日期**: 2026-03-07
> **目标**: 当 bugreport 文件结构变化时，快速更新 boundary_patterns.yaml

---

## 概述

本文档记录如何从零开始分析新的 Android bugreport 文件，逐步发现边界分隔符和章节结构的过程。

**核心原则**: 先发现边界字符，再识别章节，最后验证完整性。

---

## 分析流程图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        YAML 配置更新流程                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐               │
│  │ 1. 扫描边界   │───▶│ 2. 识别章节   │───▶│ 3. 验证完整性 │               │
│  │   字符       │    │   结构        │    │              │               │
│  └──────────────┘    └──────────────┘    └──────────────┘               │
│         │                   │                   │                         │
│         ▼                   ▼                   ▼                         │
│  10种边界分隔符        14种主章节            正则验证                      │
│  =============        =========            =========                      │
│  ------ xxx ------    dumpsys_normal       grep 匹配                      │
│  *** xxx ***         system_log                                       │
│  ##### xxx #####    kernel_log                                        │
│  ----- pid          activity_broadcasts                                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 第一步: 扫描边界字符

### 1.1 搜索等号 (=====)

```bash
# 搜索连续 20+ 个等号
grep -n "^===" dumpstate.txt
```

**发现**:
- 文件头分隔符
- 大章节标题
- 正则: `^={20,}$`

### 1.2 搜索短横线 (------)

```bash
# 搜索 6 个短横线 + 文字 + 短横线
grep -n "^------ " dumpstate.txt
```

**发现**:
- 标准章节标题: `------ MEMORY INFO (/proc/meminfo) ------`
- 正则: `^------ .+ -----$`

### 1.3 搜索持续时间标记

```bash
# 搜索 duration 标记
grep -n "was the duration of" dumpstate.txt
```

**发现** 有两种不同的 duration 标记：

| 类型 | 正则 | 示例 |
|------|------|------|
| 大章节结束 | `^------ \d+\.\d+s was the duration of` | `------ 0.012s was the duration of 'MEMORY INFO' ------` |
| dumpsys 子章节结束 | `^---------+ \d+\.\d+s was the duration of dumpsys` | `--------- 0.297s was the duration of dumpsys activity` |

> **关键发现**: 子章节使用 9 个横线 (---------)，比大章节的 6 个横线 (------) 更多！

### 1.4 搜索星号 (***)

```bash
grep -n "^\*{3,}" dumpstate.txt
```

**发现**:
- 电池日志: `*****Battery Power On Logs*****`
- 正则: `^\*{3,}.+\*{3,}$`

### 1.5 搜索井号 (#####)

```bash
grep -n "^#{3,}" dumpstate.txt
```

**发现**:
- Samsung 特定服务: `##### SEP UNION Main SERVICE #####`
- 正则: `^#{3,}.+#{3,}$`

### 1.6 搜索进程 trace

```bash
grep -n "^----- pid" dumpstate.txt
grep -n "^----- end" dumpstate.txt
```

**发现**:
- 进程开始: `----- pid 933 at 2025-12-30 10:00:23 -----`
- 进程结束: `----- end 933 -----`
- 正则: 
  - 开始: `^----- pid \d+ at`
  - 结束: `^----- end \d+$`

### 1.7 搜索内核日志

```bash
grep -n "^\[" dumpstate.txt | head -20
```

**发现**:
- 内核时间戳: `[175555.553540] [0: kworker/0:2:12056] message`
- 正则: `^\[\s*\d+\.\d+\]`

---

## 第二步: 识别章节结构

### 2.1 识别 dumpsys 子章节

```bash
# 搜索 dumpsys 服务结束标记
grep -n "--------- .* was the duration of dumpsys" dumpstate.txt
```

**发现**: ~60 个 dumpsys 子服务

| 服务名 | 行号 | 耗时 |
|--------|------|------|
| meminfo | 879782 | 30.847s |
| sem_wifi | 1116092 | 10.006s |
| activity | 95933 | 0.297s |
| power | 106085 | 0.091s |
| ... | ... | ... |

### 2.2 识别 ACTIVITY MANAGER 子章节

```bash
# 搜索 ACTIVITY MANAGER 开头
grep -n "^ACTIVITY MANAGER" dumpstate.txt
```

**发现**: 26 个子章节

| 子章节 | 行号 | 优先级 |
|--------|------|--------|
| BROADCAST STATE | 886281 | CRITICAL |
| LAST ANR | 960212 | CRITICAL |
| LMK KILLS | 1007974 | CRITICAL |
| SERVICES | 951138 | HIGH |
| CONTENT PROVIDERS | 943611 | HIGH |
| ... | ... | ... |

---

## 第三步: 验证完整性

### 3.1 验证边界分隔符

```python
# 用正则验证所有 pattern
import re

patterns = {
    "equals_separator": r"^={20,}$",
    "dash_separator": r"^------ .+ -----$",
    "duration_marker_major": r"^------ \d+\.\d+s was the duration of",
    "duration_marker_dumpsys": r"^---------+ \d+\.\d+s was the duration of dumpsys",
}

with open("dumpstate.txt", "r") as f:
    for line_num, line in enumerate(f, 1):
        for name, pattern in patterns.items():
            if re.match(pattern, line.strip()):
                print(f"Line {line_num}: {name} -> {line[:50]}...")
```

### 3.2 验证章节覆盖

```python
# 验证所有主章节是否都能被识别
expected_sections = [
    "MEMORY INFO",
    "DUMPSYS CRITICAL",
    "DUMPSYS HIGH", 
    "DUMPSYS NORMAL",
    "SYSTEM LOG",
    "KERNEL LOG",
    "BINDER STATE",
]

found_sections = []
# ... 扫描逻辑 ...

missing = set(expected_sections) - set(found_sections)
if missing:
    print(f"警告: 以下章节未找到: {missing}")
```

---

## 完整边界分隔符总表

| # | 字符类型 | 正则模式 | 用途 |
|---|---------|---------|------|
| 1 | `=======` | `^={20,}$` | 文件头/大章节标题 |
| 2 | `------ xxx ------` | `^------ .+ -----$` | 标准章节标题 |
| 3 | `------ X.XXXs was the duration` | `^------ \d+\.\d+s was the duration of` | 大章节结束 |
| 4 | `--------- X.XXXs was the duration of dumpsys` | `^---------+ \d+\.\d+s was the duration of dumpsys` | dumpsys 子章节结束 |
| 5 | `***** xxx *****` | `^\*{3,}.+\*{3,}$` | 电池日志 |
| 6 | `##### xxx #####` | `^#{3,}.+#{3,}$` | Samsung dumpsys |
| 7 | `----- pid xxx at` | `^----- pid \d+ at` | 进程 trace 开始 |
| 8 | `----- end xxx` | `^----- end \d+$` | 进程 trace 结束 |
| 9 | `-------- xxx --------` | `^---------+.+---------$` | dumpsys 内部子标题 |
| 10 | `[timestamp]` | `^\[\s*\d+\.\d+\]` | 内核日志时间戳 |

---

## 常见问题与解决方案

### Q1: 新增了一个大章节，如何添加？

1. 搜索新章节的边界字符
2. 确定 start_pattern 和 end_pattern
3. 在 boundary_patterns.yaml 的 record_types 中添加
4. 验证是否能匹配

### Q2: dumpsys 下新增了子服务，如何添加？

1. 搜索: `grep -n "--------- .* was the duration of dumpsys NEW_SERVICE" dumpstate.txt`
2. 记录行号和耗时
3. 在对应的 record_type.subsections 中添加

### Q3: ACTIVITY MANAGER 下新增了子章节？

1. 搜索: `grep -n "^ACTIVITY MANAGER NEW_SECTION" dumpstate.txt`
2. 记录行号
3. 在 dumpsys_normal.subsections 中添加

---

## 自动化工具 (可选)

未来可以开发 `auto_analyze.py` 脚本：

```python
def auto_analyze(bugreport_path: str) -> dict:
    """自动分析 bugreport 文件，生成候选配置"""
    results = {
        "boundary_markers": [],
        "record_types": [],
        "subsections": [],
    }
    
    # 1. 扫描边界字符
    for pattern in BOUNDARY_PATTERNS:
        matches = scan_pattern(bugreport_path, pattern)
        results["boundary_markers"].extend(matches)
    
    # 2. 识别章节
    sections = detect_sections(bugreport_path)
    results["record_types"] = sections
    
    # 3. 识别子章节
    subsections = detect_subsections(bugreport_path)
    results["subsections"] = subsections
    
    return results
```

---

## 变更记录

| 版本 | 日期 | 变更 |
|------|------|------|
| 1.0 | 2026-03-07 | 初始版本 |
