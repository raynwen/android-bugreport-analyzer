# Android Bug Report 高效处理与精确分析方案

> 解决大文件 bugreport (>200MB) 无法完整读取的行业难题 | 作者: 闫文峰

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Platform: Android](https://img.shields.io/badge/Platform-Android-brightgreen.svg)](https://www.android.com)
[![Version: v2.4](https://img.shields.io/badge/Version-v2.4-blue.svg)](https://github.com/raynwen/android-bugreport-analyzer)

---

## 📋 项目简介

本方案解决了一个行业痛点：**当 Android Bug Report 文件超过 200MB 时，如何在 AI 模型的上下文窗口限制下，完整读取并分析所有内容？**

本方案提供了一套系统化的解决思路，包括智能分块、边界识别、优先级分类、多维度索引、自定义查询等技术实现。

---

## 🔍 解决的问题

| 挑战 | 解决方案 |
|------|---------|
| 文件太大 (>200MB) 无法一次性加载 | 流式读取 + 智能分块 |
| AI 上下文窗口限制 | 语义分块 + 优先级分类 |
| 边界识别不准确 | 10 种边界分隔符模式 |
| 子章节遗漏 | 分层 subsections 设计 (86+ 个) |
| 检索困难 | 多维度索引系统 |
| 自定义查询需求 | AI Agent 驱动的动态索引 |

---

## 🚀 快速开始

### 统一命令行入口 (推荐)

```bash
# 构建索引
python cli.py build <output_dir>

# 执行查询
python cli.py query <output_dir> --pattern "ANR" --type keyword

# 正则查询
python cli.py query <output_dir> \
    --name "query_wechat_freeze" \
    --pattern "com\.tencent\.mm.*freeze" \
    --type regex \
    --priority CRITICAL

# 完整分析流程（自动构建索引 + 执行查询）
python cli.py analyze <output_dir> --pattern "xxx" --type regex

# 使用配置文件批量查询
python cli.py query <output_dir> --config queries.json

# 交互式模式
python cli.py interactive
```

### 命令详解

| 命令 | 功能 | 说明 |
|------|------|------|
| `build` | 构建索引 | 生成 sections.json + enhanced_index.json |
| `query` | 执行查询 | 支持关键词/正则/章节三种查询类型 |
| `analyze` | 完整分析 | 自动检测并构建缺失的索引 |
| `interactive` | 交互式 | 交互式输入参数 |

---

## 🏗️ 核心特性

### 1. YAML 配置驱动
通过配置文件定义记录类型、边界模式、处理规则，便于维护和扩展。

### 2. 智能边界识别
支持 10 种边界分隔符模式：
```
=======                      文件头/大章节标题
------ xxx ------            标准章节标题
------ X.XXXs was the duration of    大章节结束
--------- X.XXXs was the duration of dumpsys  dumpsys 子章节结束
***** xxx *****              电池日志
##### xxx #####              Samsung 特定服务
----- pid xxx at             进程 trace 开始
----- end xxx                进程 trace 结束
-------- xxx --------        dumpsys 内部子标题
[timestamp]                  内核日志时间戳
```

### 3. 分层章节结构
```
Level 1: 大章节 (14 种)
└── Level 2: dumpsys 子服务 (~60 个)
    └── Level 3: ACTIVITY MANAGER 子章节 (26 个)
```

### 4. 优先级分类
| 优先级 | 用途 | 示例 |
|--------|------|------|
| CRITICAL | 必须优先分析 | ANR、Tombstone、LAST ANR |
| HIGH | 重要性能信息 | Binder、SurfaceFlinger、Power |
| MEDIUM | 一般系统信息 | dumpsys normal、Logcat |
| LOW | 辅助信息 | 系统配置、环境变量 |

### 5. 多维度索引系统

#### 5.1 索引文件结构

| 索引文件 | 用途 | 内容 |
|---------|------|------|
| `enhanced_index.json` | 关键词索引 + 行偏移 | 预设关键词出现位置 + 每行字节偏移 |
| `sections.json` | 章节索引 | 层级化的章节结构（Level 1-3） |
| `custom_index.json` | 自定义索引 | 用户查询的动态索引 |

#### 5.2 预设关键词列表（共 36 个）

| 序号 | 关键词 | 序号 | 关键词 |
|------|--------|------|--------|
| 1 | *** *** *** | 19 | ion heap |
| 2 | anr | 20 | kswapd |
| 3 | application not responding | 21 | low memory |
| 4 | binder call | 22 | memory pressure |
| 5 | binder error | 23 | native crash |
| 6 | binder transaction | 24 | not responding |
| 7 | blocking | 25 | process.*exit |
| 8 | cpu idle | 26 | sigkill |
| 9 | cpu usage | 27 | signal 9 |
| 10 | crash | 28 | slow |
| 11 | delay | 29 | surfaceflinger |
| 12 | died | 30 | timeout |
| 13 | error | 31 | tombstone |
| 14 | exception | 32 | transaction failed |
| 15 | failed | 33 | waited too long |
| 16 | fatal | 34 | warn |
| 17 | force finish | 35 | gpu timeout |
| 18 | frame deadline | 36 | lowmemory |

### 6. 自定义查询系统 (v2.3 新增)

#### 6.1 设计原则

| 原则 | 说明 |
|------|------|
| **预设优先** | YAML 已定义的关键词，使用预设索引 |
| **定制补充** | YAML 未定义的关键词，按需生成定制索引 |
| **动态索引** | 每次新查询时重建自定义索引 |
| **分页输出** | 按 AI context 窗口大小自动分页 |

#### 6.2 查询类型

| 类型 | 说明 | 示例 |
|------|------|------|
| **keyword** | 简单字符串匹配 | `pattern: "com.example"` |
| **regex** | 正则表达式匹配 | `pattern: "ERROR_[0-9]{4}"` |
| **section** | 章节名匹配 | `pattern: "activity_mars"` |

#### 6.3 查询配置文件示例

```json
{
  "queries": [
    {
      "name": "query_wechat_freeze",
      "type": "regex",
      "pattern": "com\\.tencent\\.mm.*freeze|freeze.*com\\.tencent\\.mm",
      "priority": "CRITICAL",
      "description": "查询微信冻结问题",
      "enabled": true
    },
    {
      "name": "query_anr",
      "type": "keyword",
      "pattern": "ANR",
      "priority": "CRITICAL",
      "description": "查询ANR问题",
      "enabled": true
    }
  ]
}
```

#### 6.4 查询结果输出

```
output_dir/
├── custom_queries.yaml         # 用户查询配置
├── custom_index.json           # 自定义索引
└── query_results/
    └── {query_name}/
        ├── result.json         # 主结果文件
        ├── metadata.json       # 元信息
        └── context/
            ├── part_1.json     # 分页文件
            └── part_2.json
```

---

## 📂 文件说明

| 文件 | 说明 |
|------|------|
| `cli.py` | **统一命令行入口（推荐使用）** |
| `build_all_indexes.py` | 构建索引脚本 |
| `custom_query.py` | 自定义查询脚本 |
| `architecture_design.md` | 完整系统架构设计文档 |
| `boundary_patterns.yaml` | 边界模式配置文件 |
| `query_config.yaml` | 查询全局配置 |

---

## 📊 实际数据

基于 Samsung SM-F9660 (Android 16) 的 dumpstate.txt 实测：

| 指标 | 数值 |
|------|------|
| 文件大小 | 196.4 MB |
| 总行数 | 约 300 万行 |
| 主章节数 | 14 种 |
| 子章节数 | 86+ 个 |
| dumpsys 子服务 | ~60 个 |
| ACTIVITY MANAGER | 26 个子章节 |
| 预设关键词 | 36 个 |

---

## 📝 更新日志

| 版本 | 日期 | 变更 |
|------|------|------|
| v2.4 | 2026-03-08 | 新增统一命令行入口 cli.py |
| v2.3 | 2026-03-08 | 新增自定义查询系统：AI Agent 驱动 + 动态索引 + 分页输出 |
| v2.2 | 2026-03-07 | 新增用户查询系统：预设优先 + 定制补充双模式 |
| v2.0 | 2026-03-07 | 新增边界分隔符总表、分层 subsections 设计、优先级分类 |
| v1.0 | 2026-03-03 | 初始版本 |

---

## 🔧 相关工具

- **dumpsys**: Android 系统服务状态输出
- **logcat**: Android 日志查看
- **bugreport**: Android bug 报告收集工具
- **ANR Traces**: 应用无响应 traces
- **Tombstone**: Native 崩溃墓碑

---

## 📄 License

MIT License

---

## 👤 作者

**闫文峰**

如果你觉得这个方案有帮助，欢迎 star ⭐ 和分享！

---

## 📖 了解更多

- [系统架构设计](architecture_design.md)
- [边界模式配置](boundary_patterns.yaml)
- [查询配置](query_config.yaml)
