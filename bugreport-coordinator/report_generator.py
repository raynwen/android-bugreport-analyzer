from typing import List, Dict, Any
from pathlib import Path
from datetime import datetime


class ReportGenerator:

    @staticmethod
    def generate_markdown(report: Dict[str, Any], output_path: Path) -> str:
        lines = []

        lines.append("# Android Bug Report 分析报告")
        lines.append("")

        lines.append("## 概述")
        lines.append(f"- **分析时间**: {report.get('analyzed_at', 'Unknown')}")

        issues = report.get('issues', [])
        lines.append(f"- **问题数量**: {len(issues)}")

        if issues:
            severities = [i.get('severity', 'UNKNOWN') for i in issues]
            highest = max(severities, key=lambda s: {'CRITICAL': 4, 'HIGH': 3, 'MEDIUM': 2, 'LOW': 1}.get(s, 0))
            lines.append(f"- **严重程度**: {highest}")

        lines.append("")

        if issues:
            lines.append("## 问题列表")
            lines.append("")

            for i, issue in enumerate(issues, 1):
                lines.extend(ReportGenerator._format_issue(issue, i))

        lines.append("---")
        lines.append("")
        lines.append("## 总结")

        if issues:
            high_count = sum(1 for i in issues if i.get('severity') in ['CRITICAL', 'HIGH'])
            lines.append(f"本次分析发现 {len(issues)} 个问题，其中 {high_count} 个高危问题需要立即处理。")

            if issues[0].get('suggestions'):
                lines.append(f"建议优先解决: {issues[0].get('title', 'Unknown')}")
        else:
            lines.append("本次分析未发现明显问题。")

        content = '\n'.join(lines)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return content

    @staticmethod
    def _format_issue(issue: Dict, index: int) -> List[str]:
        lines = []

        severity = issue.get('severity', 'UNKNOWN')
        title = issue.get('title', 'Unknown Issue')

        lines.append(f"### 问题 {index}: {title} [{severity}]")
        lines.append("")

        lines.append("**问题描述**")
        lines.append(issue.get('description', 'No description available.'))
        lines.append("")

        causes = issue.get('possible_causes', [])
        if causes:
            lines.append("**可能原因**")
            lines.append("")

            for cause in causes[:3]:
                rank = cause.get('rank', 0)
                cause_type = cause.get('type', 'Unknown')
                desc = cause.get('description', '')
                score = cause.get('priority_score', 0)

                lines.append(f"{rank}. **{cause_type}** (优先级分数: {score})")
                lines.append(f"   - {desc}")

                evidence = cause.get('evidence', [])
                if evidence:
                    lines.append(f"   - 证据: {evidence[0][:100]}")

                lines.append("")

        timeline = issue.get('timeline', [])
        if timeline:
            lines.append("**时间线**")
            lines.append("")
            lines.append("| 时间 | 事件 |")
            lines.append("|-----|------|")

            for event in timeline[:10]:
                lines.append(f"| {event.get('time', 'Unknown')} | {event.get('event', '')[:50]} |")

            lines.append("")

        suggestions = issue.get('suggestions', [])
        if suggestions:
            lines.append("**建议方案**")
            lines.append("")

            for sug in suggestions[:5]:
                priority = sug.get('priority', 0)
                action = sug.get('action', '')

                priority_label = {1: '高', 2: '中', 3: '低'}.get(priority, '中')
                lines.append(f"{priority}. **[优先级{priority_label}]** {action}")

            lines.append("")

        lines.append("---")
        lines.append("")

        return lines
