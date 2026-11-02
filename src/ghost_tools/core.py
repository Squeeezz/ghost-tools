"""Shared data types, safe report serialization and metadata risk rules."""
from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


@dataclass
class Finding:
    field: str
    value: str
    severity: str
    explanation: str


@dataclass
class ScanResult:
    filename: str
    findings: list[Finding]
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


SENSITIVE_FIELDS = {
    "gps": ("HIGH", "Location information may reveal where a photo was taken."),
    "artist": ("MEDIUM", "Creator information may identify a person."),
    "copyright": ("MEDIUM", "Copyright information may include a personal name."),
    "hostcomputer": ("MEDIUM", "Computer names may disclose local identifiers."),
    "bodyserialnumber": ("MEDIUM", "Device serial numbers may identify hardware."),
    "serialnumber": ("MEDIUM", "Serial numbers may identify hardware."),
    "model": ("LOW", "The camera model reveals a device type."),
    "software": ("LOW", "Software details reveal tools used to process the file."),
    "datetime": ("INFO", "A timestamp may disclose when content was created."),
}


def assess_field(name: str, value: Any) -> Finding:
    normalized = name.lower().replace(" ", "").replace("_", "")
    severity, explanation = "INFO", "Metadata value stored inside the file."
    for key, risk in SENSITIVE_FIELDS.items():
        if key in normalized:
            severity, explanation = risk
            break
    return Finding(name, str(value)[:250], severity, explanation)


def validate_report_destination(destination: Path, protected_paths: Iterable[Path] = ()) -> None:
    """Protect sources even when the destination is a symlink or hard-link alias."""
    if destination.exists() and not destination.is_file():
        raise ValueError("Report destination is not a file")
    for source in protected_paths:
        if destination.resolve() == source.resolve():
            raise ValueError("A report cannot overwrite an inspected source file or folder")
        if destination.exists() and source.exists() and destination.samefile(source):
            raise ValueError("A report cannot overwrite another link to an inspected source file")


def export_json(result: dict[str, Any], destination: Path,
                protected_paths: Iterable[Path] = ()) -> None:
    """Replace reports atomically, leaving existing files intact on write failure."""
    validate_report_destination(destination, protected_paths)
    payload = json.dumps({
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "tool": "GHOST//TOOLS", "result": result,
    }, indent=2, ensure_ascii=False)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8',
                                         dir=destination.parent, prefix='.ghost-report-',
                                         suffix='.tmp', delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(payload)
        os.replace(temporary, destination)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
