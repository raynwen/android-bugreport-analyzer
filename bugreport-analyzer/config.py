from dataclasses import dataclass


@dataclass
class AnalyzerConfig:
    enable_freeze_analysis: bool = True
    freeze_window_seconds: int = 60
    analysis_mode: str = "correlated"

    @classmethod
    def from_dict(cls, data: dict) -> 'AnalyzerConfig':
        return cls(
            enable_freeze_analysis=data.get('enable_freeze_analysis', True),
            freeze_window_seconds=data.get('freeze_window_seconds', 60),
            analysis_mode=data.get('analysis_mode', 'correlated')
        )
