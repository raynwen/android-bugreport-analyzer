from dataclasses import dataclass, field
from typing import Optional, List, Dict
from datetime import datetime


@dataclass
class FileInfo:
    name: str
    size: str
    type: str
    encoding: str = "utf-8"
    path: Optional[str] = None


@dataclass
class DirectoryInfo:
    path: str
    type: str = "directory"
    files: List[FileInfo] = field(default_factory=list)


@dataclass
class ExtractionStats:
    total_files: int
    total_size: str
    extraction_time: str
    max_depth_reached: int
    compressed_size: str
    compression_ratio: float


@dataclass
class Manifest:
    version: str = "1.0"
    extracted_at: str = field(default_factory=lambda: datetime.now().isoformat())
    source_file: str = ""
    extraction_stats: Optional[ExtractionStats] = None
    file_tree: List[DirectoryInfo] = field(default_factory=list)
    key_files: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "extracted_at": self.extracted_at,
            "source_file": self.source_file,
            "extraction_stats": self.extraction_stats.__dict__ if self.extraction_stats else None,
            "file_tree": [vars(d) for d in self.file_tree],
            "key_files": self.key_files
        }
