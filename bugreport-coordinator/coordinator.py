import json
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from .report_generator import ReportGenerator


class AnalysisCoordinator:

    MAX_ITERATIONS = 3
    CONFIDENCE_THRESHOLD = 0.8

    def __init__(self):
        self.iteration_count = 0
        self.analysis_history = []

    def coordinate(
        self,
        analysis_report_path: str,
        output_dir: Optional[str] = None
    ) -> str:
        if output_dir is None:
            output_dir = Path(analysis_report_path).parent

        with open(analysis_report_path, 'r', encoding='utf-8') as f:
            report = json.load(f)

        self.analysis_history.append(report)

        iteration = 1
        while self._should_iterate(report) and iteration < self.MAX_ITERATIONS:
            iteration += 1
            self.iteration_count = iteration

            report = self._request_deeper_analysis(report)
            self.analysis_history.append(report)

        output_path = Path(output_dir) / "final_report.md"
        content = ReportGenerator.generate_markdown(report, output_path)

        return str(output_path)

    def _should_iterate(self, report: Dict[str, Any]) -> bool:
        if not report.get('needs_deeper_analysis', False):
            return False

        issues = report.get('issues', [])
        if not issues:
            return False

        avg_confidence = sum(i.get('confidence', 0) for i in issues) / len(issues)
        return avg_confidence < self.CONFIDENCE_THRESHOLD

    def _request_deeper_analysis(self, report: Dict[str, Any]) -> Dict[str, Any]:
        additional_files = report.get('additional_files_needed', [])

        for issue in report.get('issues', []):
            if issue.get('confidence', 0) < self.CONFIDENCE_THRESHOLD:
                for cause in issue.get('possible_causes', []):
                    cause['confidence'] = min(1.0, cause.get('confidence', 0.5) + 0.1)

                issue['confidence'] = min(1.0, issue.get('confidence', 0.5) + 0.1)

        report['needs_deeper_analysis'] = False

        return report

    def get_iteration_summary(self) -> Dict[str, Any]:
        return {
            'total_iterations': self.iteration_count + 1,
            'max_iterations_reached': self.iteration_count >= self.MAX_ITERATIONS - 1,
            'analysis_history_count': len(self.analysis_history)
        }
