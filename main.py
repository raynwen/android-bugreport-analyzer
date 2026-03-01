"""
Android Bug Report Analyzer - 交互式入口
支持多种分析模式的命令行交互工具
"""

import sys
import os
from pathlib import Path
from typing import Optional, Tuple
from enum import Enum


class AnalysisMode(Enum):
    FULL = "full"
    FREEZE = "freeze"
    PLM_ISSUE = "plm_issue"
    QUICK = "quick"


class InteractiveAnalyzer:

    TRIGGER_KEYWORDS = {
        AnalysisMode.FULL: [
            "完整分析", "全流程分析", "分析bug", "解析bug",
            "分析bugreport", "bug报告分析", "分析这个bug"
        ],
        AnalysisMode.FREEZE: [
            "分析冻结", "冻结分析", "freeze分析", "mars冻结",
            "freecess", "冻结问题", "分析freeze"
        ],
        AnalysisMode.PLM_ISSUE: [
            "分析plm issue", "plm问题分析", "issue分析",
            "plm问题", "分析plm"
        ],
        AnalysisMode.QUICK: [
            "快速分析", "只解析", "只分析", "单步分析"
        ]
    }

    def __init__(self):
        self.output_dir = Path("./output")
        self.package_name: Optional[str] = None
        self.bugreport_path: Optional[str] = None

    def detect_mode(self, user_input: str) -> Optional[AnalysisMode]:
        user_input_lower = user_input.lower()
        for mode, keywords in self.TRIGGER_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in user_input_lower:
                    return mode
        return None

    def ask_for_path(self, path_type: str = "bugreport") -> str:
        prompts = {
            "bugreport": "请提供 bug report 文件的路径 (.zip/.tar.gz/.gz): ",
            "plm_issue": "请提供 PLM issue 文件的路径或直接粘贴内容: ",
            "output": "请输入输出目录 (直接回车使用默认 ./output): "
        }
        return input(prompts.get(path_type, "请输入文件路径: ")).strip()

    def ask_for_package_name(self) -> Optional[str]:
        package = input("请输入目标应用的包名 (可选，直接回车跳过): ").strip()
        return package if package else None

    def confirm_analysis(self, mode: AnalysisMode) -> bool:
        mode_names = {
            AnalysisMode.FULL: "完整分析流程",
            AnalysisMode.FREEZE: "冻结问题专项分析",
            AnalysisMode.PLM_ISSUE: "PLM Issue 分析",
            AnalysisMode.QUICK: "快速分析"
        }
        print(f"\n检测到分析模式: {mode_names[mode]}")
        confirm = input("确认开始分析? (y/n): ").strip().lower()
        return confirm == 'y' or confirm == 'yes'

    def run_full_analysis(self) -> str:
        print("\n" + "="*50)
        print("开始完整分析流程")
        print("="*50)

        from bugreport_extractor import ArchiveExtractor
        from bugreport_parser import LogParser
        from bugreport_analyzer import BugAnalyzer
        from bugreport_coordinator import AnalysisCoordinator

        self.output_dir.mkdir(parents=True, exist_ok=True)

        print("\n[1/4] 解压文件...")
        extractor = ArchiveExtractor()
        manifest = extractor.extract(self.bugreport_path, str(self.output_dir))
        print(f"  - 解压完成: {manifest.extraction_stats.total_files} 个文件")

        print("\n[2/4] 解析日志...")
        parser = LogParser()
        manifest_path = str(self.output_dir / "manifest.json")
        extracted = parser.parse(
            manifest_path,
            self.package_name,
            str(self.output_dir),
            enable_freeze_analysis=True,
            freeze_analysis_mode="correlated"
        )
        print(f"  - 解析完成: {extracted.summary.get('total_entries', 0)} 条日志")

        print("\n[3/4] 分析问题...")
        analyzer = BugAnalyzer()
        extracted_path = str(self.output_dir / "extracted_info.json")
        report = analyzer.analyze(extracted_path, str(self.output_dir))
        print(f"  - 发现 {len(report.issues)} 个问题")

        print("\n[4/4] 生成报告...")
        coordinator = AnalysisCoordinator()
        analysis_path = str(self.output_dir / "analysis_report.json")
        final_report = coordinator.coordinate(analysis_path, str(self.output_dir))
        print(f"  - 报告已生成: {final_report}")

        return final_report

    def run_freeze_analysis(self) -> str:
        print("\n" + "="*50)
        print("开始冻结问题专项分析")
        print("="*50)

        from bugreport_extractor import ArchiveExtractor
        from bugreport_parser import LogParser
        from bugreport_analyzer import BugAnalyzer

        self.output_dir.mkdir(parents=True, exist_ok=True)

        print("\n[1/3] 解压文件...")
        extractor = ArchiveExtractor()
        manifest = extractor.extract(self.bugreport_path, str(self.output_dir))
        print(f"  - 解压完成")

        print("\n[2/3] 解析冻结信息...")
        parser = LogParser()
        manifest_path = str(self.output_dir / "manifest.json")
        extracted = parser.parse(
            manifest_path,
            self.package_name,
            str(self.output_dir),
            enable_freeze_analysis=True,
            freeze_analysis_mode="correlated"
        )

        freeze_info = extracted.freeze_analysis
        if freeze_info:
            print(f"  - 冻结事件: {len(freeze_info.freeze_events)} 个")
            print(f"  - 冻结崩溃: {freeze_info.anomaly_summary.frozen_crashes}")
            print(f"  - 冻结 ANR: {freeze_info.anomaly_summary.frozen_anrs}")

        print("\n[3/3] 分析冻结原因...")
        analyzer = BugAnalyzer()
        extracted_path = str(self.output_dir / "extracted_info.json")
        report = analyzer.analyze(extracted_path, str(self.output_dir))

        freeze_issues = [i for i in report.issues if hasattr(i, 'freeze_info') and i.freeze_info]
        print(f"  - 发现 {len(freeze_issues)} 个冻结相关问题")

        output_path = str(self.output_dir / "freeze_analysis_report.md")
        self._generate_freeze_report(report, freeze_issues, output_path)
        print(f"  - 报告已生成: {output_path}")

        return output_path

    def run_plm_issue_analysis(self, issue_path: str) -> str:
        print("\n" + "="*50)
        print("开始 PLM Issue 分析")
        print("="*50)

        self.output_dir.mkdir(parents=True, exist_ok=True)

        print("\n[1/2] 读取 Issue 信息...")
        if Path(issue_path).exists():
            with open(issue_path, 'r', encoding='utf-8') as f:
                issue_content = f.read()
        else:
            issue_content = issue_path

        print(f"  - Issue 内容长度: {len(issue_content)} 字符")

        print("\n[2/2] 分析 Issue...")
        analysis_result = self._analyze_plm_issue(issue_content)

        output_path = str(self.output_dir / "plm_issue_analysis.md")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(analysis_result)
        print(f"  - 报告已生成: {output_path}")

        return output_path

    def _analyze_plm_issue(self, content: str) -> str:
        lines = [
            "# PLM Issue 分析报告",
            "",
            "## Issue 摘要",
            "",
            f"内容长度: {len(content)} 字符",
            "",
            "## 分析建议",
            "",
            "1. 请检查 Issue 描述是否完整",
            "2. 确认复现步骤是否清晰",
            "3. 验证附件是否齐全",
            "",
            "---",
            "*由 Android Bug Report Analyzer 生成*"
        ]
        return "\n".join(lines)

    def _generate_freeze_report(self, report, freeze_issues, output_path: str):
        lines = [
            "# 冻结问题分析报告",
            "",
            "## 概述",
            "",
            f"- 总问题数: {len(report.issues)}",
            f"- 冻结相关问题: {len(freeze_issues)}",
            "",
            "## 冻结问题详情",
            ""
        ]

        for issue in freeze_issues:
            lines.append(f"### {issue.title}")
            lines.append("")
            lines.append(f"- **类型**: {issue.issue_type}")
            lines.append(f"- **严重程度**: {issue.severity}")
            lines.append(f"- **置信度**: {issue.confidence:.0%}")
            if hasattr(issue, 'freeze_info') and issue.freeze_info:
                lines.append(f"- **冻结机制**: {issue.freeze_info.freeze_mechanism}")
                lines.append(f"- **冻结原因**: {issue.freeze_info.freeze_reason}")
            lines.append("")

        lines.extend([
            "---",
            "*由 Android Bug Report Analyzer 生成*"
        ])

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))

    def run(self, user_input: Optional[str] = None) -> Optional[str]:
        print("\n" + "="*50)
        print("Android Bug Report Analyzer")
        print("="*50)

        if user_input:
            mode = self.detect_mode(user_input)
            if not mode:
                print("\n无法识别分析模式，请使用以下关键词:")
                for m, keywords in self.TRIGGER_KEYWORDS.items():
                    print(f"  - {m.value}: {', '.join(keywords[:3])}")
                return None
        else:
            print("\n请选择分析模式:")
            for i, mode in enumerate(AnalysisMode, 1):
                print(f"  {i}. {mode.value}")
            choice = input("\n请输入选项 (1-4): ").strip()
            mode = list(AnalysisMode)[int(choice) - 1]

        if mode == AnalysisMode.PLM_ISSUE:
            issue_path = self.ask_for_path("plm_issue")
            if not issue_path:
                print("错误: 未提供 Issue 路径或内容")
                return None
            return self.run_plm_issue_analysis(issue_path)

        self.bugreport_path = self.ask_for_path("bugreport")
        if not self.bugreport_path or not Path(self.bugreport_path).exists():
            print(f"错误: 文件不存在 - {self.bugreport_path}")
            return None

        self.package_name = self.ask_for_package_name()

        output = self.ask_for_path("output")
        if output:
            self.output_dir = Path(output)

        if not self.confirm_analysis(mode):
            print("已取消分析")
            return None

        if mode == AnalysisMode.FULL:
            return self.run_full_analysis()
        elif mode == AnalysisMode.FREEZE:
            return self.run_freeze_analysis()
        elif mode == AnalysisMode.QUICK:
            print("\n快速分析模式 - 请选择模块:")
            print("  1. extractor - 仅解压")
            print("  2. parser - 仅解析")
            print("  3. analyzer - 仅分析")
            module = input("请输入选项 (1-3): ").strip()
            return self._run_quick_analysis(module)

        return None

    def _run_quick_analysis(self, module: str) -> Optional[str]:
        self.output_dir.mkdir(parents=True, exist_ok=True)

        if module == "1":
            from bugreport_extractor import ArchiveExtractor
            extractor = ArchiveExtractor()
            manifest = extractor.extract(self.bugreport_path, str(self.output_dir))
            print(f"解压完成: {manifest.extraction_stats.total_files} 个文件")
            return str(self.output_dir / "manifest.json")

        elif module == "2":
            from bugreport_parser import LogParser
            parser = LogParser()
            manifest_path = str(self.output_dir / "manifest.json")
            if not Path(manifest_path).exists():
                print("错误: 未找到 manifest.json，请先运行 extractor")
                return None
            extracted = parser.parse(manifest_path, self.package_name, str(self.output_dir))
            print(f"解析完成: {extracted.summary.get('total_entries', 0)} 条日志")
            return str(self.output_dir / "extracted_info.json")

        elif module == "3":
            from bugreport_analyzer import BugAnalyzer
            analyzer = BugAnalyzer()
            extracted_path = str(self.output_dir / "extracted_info.json")
            if not Path(extracted_path).exists():
                print("错误: 未找到 extracted_info.json，请先运行 parser")
                return None
            report = analyzer.analyze(extracted_path, str(self.output_dir))
            print(f"分析完成: 发现 {len(report.issues)} 个问题")
            return str(self.output_dir / "analysis_report.json")

        return None


def main():
    analyzer = InteractiveAnalyzer()

    if len(sys.argv) > 1:
        user_input = " ".join(sys.argv[1:])
        result = analyzer.run(user_input)
    else:
        result = analyzer.run()

    if result:
        print(f"\n分析完成! 报告路径: {result}")
    else:
        print("\n分析未完成")
        sys.exit(1)


if __name__ == "__main__":
    main()
