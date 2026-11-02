"""Opt-in local directory scan; no file contents are uploaded or modified."""
import os
import stat
from pathlib import Path
from .core import ScanResult
from .metadata import inspect_image

SUPPORTED = {".jpg", ".jpeg", ".tif", ".tiff", ".png", ".webp"}


def _linked(path: Path) -> bool:
    # Path.is_junction exists only on Python 3.12+. Reparse attributes work on 3.10 too.
    details = path.lstat()
    return stat.S_ISLNK(details.st_mode) or bool(
        getattr(details, 'st_file_attributes', 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT
    )


def scan_directory(directory: Path, limit: int = 500) -> list[ScanResult]:
    if _linked(directory):
        raise ValueError("Choose a real directory, not a symlink or Windows reparse point")
    if not directory.is_dir():
        raise NotADirectoryError(f"Not a directory: {directory}")
    if not 1 <= limit <= 10000:
        raise ValueError("Limit must be between 1 and 10000")
    reports = []
    attempted = 0

    def traversal_error(error):
        reports.append(ScanResult(str(error.filename), [], [f"Traversal skipped: {error}"]))

    def linked(path):
        try:
            return _linked(path)
        except OSError as exc:
            reports.append(ScanResult(str(path), [], [f"Skipped: {exc}"]))
            return True

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
