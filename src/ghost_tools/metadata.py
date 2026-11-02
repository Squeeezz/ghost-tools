"""Read image EXIF metadata locally without altering the source file."""
from __future__ import annotations

from pathlib import Path
from PIL import Image, ExifTags, UnidentifiedImageError
from .core import ScanResult, assess_field


def inspect_image(path: Path) -> ScanResult:
    if not path.is_file():
        raise FileNotFoundError(f"File not found: {path}")
    findings = []
    warnings = []
    try:
        with Image.open(path) as img:
            exif = img.getexif()
            for tag_id, value in exif.items():
                name = ExifTags.TAGS.get(tag_id, str(tag_id))
                if name == "GPSInfo":
                    try:
                        gps = exif.get_ifd(ExifTags.IFD.GPSInfo)
                        # Do not interpret GPS data as accurate coordinates by default.
                        if gps:
                            findings.append(assess_field("GPSInfo", "GPS metadata present"))
                    except (KeyError, TypeError, ValueError, AttributeError):
                        warnings.append("Could not interpret GPS metadata")
                elif isinstance(value, (str, int, float)):
                    findings.append(assess_field(str(name), value))
            if not findings:
                warnings.append("No readable EXIF metadata found; this is not proof of privacy.")
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError) as exc:
        raise ValueError(f"Cannot inspect this image: {exc}") from exc
    return ScanResult(str(path), findings, warnings)
