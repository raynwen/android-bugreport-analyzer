from dataclasses import dataclass


@dataclass
class ParserConfig:
    max_workers: int = 4
    chunk_size: int = 10000
    enable_parallel: bool = True
    trigger_sample_size_mb: int = 500
    key_event_window_seconds: int = 30

    @classmethod
    def from_dict(cls, data: dict) -> 'ParserConfig':
        return cls(
            max_workers=data.get('max_workers', 4),
            chunk_size=data.get('chunk_size', 10000),
            enable_parallel=data.get('enable_parallel', True),
            trigger_sample_size_mb=data.get('trigger_sample_size_mb', 500),
            key_event_window_seconds=data.get('key_event_window_seconds', 30)
        )
