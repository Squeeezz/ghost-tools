"""Opt-in local directory scan; no file contents are uploaded or modified."""
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
    for path in sorted(directory.rglob("*")):
        if len(reports) >= limit:
            break
        if path.is_symlink() or not path.is_file() or path.suffix.lower() not in SUPPORTED:
            continue
        try:
            reports.append(inspect_image(path))
        except (ValueError, OSError, PermissionError) as exc:
            reports.append(ScanResult(str(path), [], [f"Skipped: {exc}"]))
    return reports
