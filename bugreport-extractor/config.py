from dataclasses import dataclass


@dataclass
class ExtractorConfig:
    max_depth: int = 10
    max_workers: int = 4
    max_file_size_mb: int = 1024
    max_total_size_gb: int = 10
    space_multiplier: int = 3
    supported_formats: tuple = ('.zip', '.tar.gz', '.tgz', '.gz', '.bz2')

    @classmethod
    def from_dict(cls, data: dict) -> 'ExtractorConfig':
        return cls(
            max_depth=data.get('max_depth', 10),
            max_workers=data.get('max_workers', 4),
            max_file_size_mb=data.get('max_file_size_mb', 1024),
            max_total_size_gb=data.get('max_total_size_gb', 10),
            space_multiplier=data.get('space_multiplier', 3)
        )
