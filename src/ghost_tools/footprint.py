"""Opt-in local directory scan; no file contents are uploaded or modified."""
import os
from pathlib import Path
from .core import ScanResult
from .metadata import inspect_image

SUPPORTED = {".jpg", ".jpeg", ".tif", ".tiff", ".png", ".webp"}


def scan_directory(directory: Path, limit: int = 500) -> list[ScanResult]:
    if not directory.is_dir():
        raise NotADirectoryError(f"Not a directory: {directory}")
    if not 1 <= limit <= 10000:
        raise ValueError("Limit must be between 1 and 10000")
    reports = []
    attempted = 0

    def traversal_error(error):
        reports.append(ScanResult(str(error.filename), [], [f"Traversal skipped: {error}"]))

    def linked(path):
        return path.is_symlink() or (hasattr(path, 'is_junction') and path.is_junction())

    for root, directories, filenames in os.walk(directory, followlinks=False, onerror=traversal_error):
        directories[:] = sorted(name for name in directories if not linked(Path(root) / name))
        for name in sorted(filenames):
            path = Path(root) / name
            if linked(path) or path.suffix.lower() not in SUPPORTED:
                continue
            if attempted >= limit:
                return reports
            attempted += 1
            try:
                reports.append(inspect_image(path))
            except (ValueError, OSError) as exc:
                reports.append(ScanResult(str(path), [], [f"Skipped: {exc}"]))
    return reports
