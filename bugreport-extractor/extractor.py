import os
import zipfile
import tarfile
import shutil
import threading
from pathlib import Path
from typing import Optional, List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

from .config import ExtractorConfig
from .models import Manifest, DirectoryInfo, FileInfo, ExtractionStats


class DiskSpaceChecker:

    @staticmethod
    def check_available_space(path: str, required_bytes: int) -> Tuple[bool, int]:
        stat = shutil.disk_usage(path)
        available = stat.free
        return available >= required_bytes, available

    @staticmethod
    def get_required_space(file_size: int, multiplier: int = 3) -> int:
        return file_size * multiplier


class ArchiveExtractor:

    def __init__(self, config: Optional[ExtractorConfig] = None):
        self.config = config or ExtractorConfig()
        self._lock = threading.Lock()
        self._total_extracted_size = 0
        self._max_depth_reached = 0

    def extract(self, source_path: str, output_dir: Optional[str] = None) -> Manifest:
        source = Path(source_path)
        if not source.exists():
            raise FileNotFoundError(f"Source file not found: {source_path}")

        if output_dir is None:
            output_dir = f"extracted_{source.stem}"

        output = Path(output_dir)
        output.mkdir(parents=True, exist_ok=True)

        self._validate_source(source)
        self._check_disk_space(source, output)

        start_time = datetime.now()

        extracted_files = self._extract_archive(source, output, depth=0)

        end_time = datetime.now()
        extraction_time = (end_time - start_time).total_seconds()

        manifest = self._build_manifest(
            source_path=str(source),
            output_dir=output,
            extracted_files=extracted_files,
            extraction_time=extraction_time
        )

        manifest_path = output / "manifest.json"
        self._save_manifest(manifest, manifest_path)

        return manifest

    def _validate_source(self, source: Path) -> None:
        if source.suffix.lower() not in self.config.supported_formats:
            if not any(str(source).endswith(fmt) for fmt in self.config.supported_formats):
                raise ValueError(f"Unsupported format: {source.suffix}")

    def _check_disk_space(self, source: Path, output: Path) -> None:
        file_size = source.stat().st_size
        required = DiskSpaceChecker.get_required_space(
            file_size, self.config.space_multiplier
        )

        ok, available = DiskSpaceChecker.check_available_space(
            str(output.parent), required
        )

        if not ok:
            raise IOError(
                f"Insufficient disk space. Required: {required // (1024*1024)}MB, "
                f"Available: {available // (1024*1024)}MB"
            )

    def _extract_archive(
        self,
        source: Path,
        output: Path,
        depth: int
    ) -> List[Tuple[Path, int]]:
        if depth > self.config.max_depth:
            print(f"Max depth {self.config.max_depth} reached, skipping: {source}")
            return []

        with self._lock:
            if depth > self._max_depth_reached:
                self._max_depth_reached = depth

        extracted = []

        if source.suffix == '.zip':
            extracted = self._extract_zip(source, output, depth)
        elif str(source).endswith('.tar.gz') or source.suffix == '.tgz':
            extracted = self._extract_tar(source, output, depth)
        elif source.suffix == '.gz':
            extracted = self._extract_gzip(source, output, depth)
        elif source.suffix == '.bz2':
            extracted = self._extract_bzip2(source, output, depth)

        nested = []
        for file_path, size in extracted:
            if self._is_archive(file_path):
                nested.extend(self._extract_archive(file_path, output, depth + 1))

        return extracted + nested

    def _extract_zip(
        self,
        source: Path,
        output: Path,
        depth: int
    ) -> List[Tuple[Path, int]]:
        extracted = []

        with zipfile.ZipFile(source, 'r') as zf:
            for member in zf.namelist():
                self._check_file_size(member, zf.getinfo(member).file_size)

                zf.extract(member, output)
                file_path = output / member

                if file_path.is_file():
                    size = file_path.stat().st_size
                    extracted.append((file_path, size))
                    self._update_total_size(size)

        return extracted

    def _extract_tar(
        self,
        source: Path,
        output: Path,
        depth: int
    ) -> List[Tuple[Path, int]]:
        extracted = []

        with tarfile.open(source, 'r:gz') as tf:
            for member in tf.getmembers():
                if member.isfile():
                    self._check_file_size(member.name, member.size)

                tf.extract(member, output)

                if member.isfile():
                    file_path = output / member.name
                    extracted.append((file_path, member.size))
                    self._update_total_size(member.size)

        return extracted

    def _extract_gzip(
        self,
        source: Path,
        output: Path,
        depth: int
    ) -> List[Tuple[Path, int]]:
        import gzip

        target = output / source.stem
        with gzip.open(source, 'rb') as f_in:
            with open(target, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)

        size = target.stat().st_size
        self._check_file_size(str(target), size)
        self._update_total_size(size)

        return [(target, size)]

    def _extract_bzip2(
        self,
        source: Path,
        output: Path,
        depth: int
    ) -> List[Tuple[Path, int]]:
        import bz2

        target = output / source.stem
        with bz2.open(source, 'rb') as f_in:
            with open(target, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)

        size = target.stat().st_size
        self._check_file_size(str(target), size)
        self._update_total_size(size)

        return [(target, size)]

    def _check_file_size(self, name: str, size: int) -> None:
        max_size = self.config.max_file_size_mb * 1024 * 1024
        if size > max_size:
            raise IOError(
                f"File too large: {name} ({size // (1024*1024)}MB > {self.config.max_file_size_mb}MB)"
            )

    def _update_total_size(self, size: int) -> None:
        with self._lock:
            self._total_extracted_size += size
            max_total = self.config.max_total_size_gb * 1024 * 1024 * 1024
            if self._total_extracted_size > max_total:
                raise IOError(
                    f"Total extracted size exceeded limit: "
                    f"{self._total_extracted_size // (1024*1024*1024)}GB > {self.config.max_total_size_gb}GB"
                )

    def _is_archive(self, path: Path) -> bool:
        return any(str(path).endswith(fmt) for fmt in self.config.supported_formats)

    def _build_manifest(
        self,
        source_path: str,
        output_dir: Path,
        extracted_files: List[Tuple[Path, int]],
        extraction_time: float
    ) -> Manifest:
        total_size = sum(size for _, size in extracted_files)

        file_tree = self._build_file_tree(output_dir)
        key_files = self._identify_key_files(output_dir)

        stats = ExtractionStats(
            total_files=len(extracted_files),
            total_size=self._format_size(total_size),
            extraction_time=f"{extraction_time:.1f}s",
            max_depth_reached=self._max_depth_reached,
            compressed_size=self._format_size(Path(source_path).stat().st_size),
            compression_ratio=round(total_size / Path(source_path).stat().st_size, 1) if Path(source_path).stat().st_size > 0 else 0
        )

        return Manifest(
            source_file=source_path,
            extraction_stats=stats,
            file_tree=file_tree,
            key_files=key_files
        )

    def _build_file_tree(self, output_dir: Path) -> List[DirectoryInfo]:
        tree = []

        for root, dirs, files in os.walk(output_dir):
            root_path = Path(root)
            rel_path = root_path.relative_to(output_dir)

            if rel_path == Path('.'):
                continue

            dir_info = DirectoryInfo(
                path=str(rel_path),
                files=[
                    FileInfo(
                        name=f.name,
                        size=self._format_size(f.stat().st_size),
                        type=self._detect_file_type(f)
                    )
                    for f in root_path.iterdir()
                    if f.is_file()
                ]
            )
            tree.append(dir_info)

        return tree

    def _detect_file_type(self, file_path: Path) -> str:
        name = file_path.name.lower()

        if 'anr' in name:
            return 'anr_trace'
        elif 'tombstone' in name:
            return 'tombstone'
        elif 'logcat' in name:
            return 'logcat'
        elif 'dumpstate' in name:
            return 'dumpstate'
        elif 'dropbox' in str(file_path).lower():
            return 'dropbox'
        else:
            return 'unknown'

    def _identify_key_files(self, output_dir: Path) -> Dict[str, str]:
        key_files = {}

        for file_path in output_dir.rglob('*'):
            if not file_path.is_file():
                continue

            name = file_path.name.lower()
            rel_path = str(file_path.relative_to(output_dir))

            if 'logcat' in name:
                key_files['logcat'] = rel_path
            elif 'dumpstate' in name:
                key_files['dumpstate'] = rel_path
            elif 'anr' in name and 'anr_dir' not in key_files:
                key_files['anr_dir'] = str(file_path.parent.relative_to(output_dir))
            elif 'tombstone' in name and 'tombstone_dir' not in key_files:
                key_files['tombstone_dir'] = str(file_path.parent.relative_to(output_dir))
            elif 'dropbox' in name and 'dropbox_dir' not in key_files:
                key_files['dropbox_dir'] = str(file_path.parent.relative_to(output_dir))

        return key_files

    def _format_size(self, size: int) -> str:
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f}{unit}"
            size /= 1024
        return f"{size:.1f}TB"

    def _save_manifest(self, manifest: Manifest, path: Path) -> None:
        import json

        with open(path, 'w', encoding='utf-8') as f:
            json.dump(manifest.to_dict(), f, indent=2, ensure_ascii=False)
