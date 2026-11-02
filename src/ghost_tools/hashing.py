"""Streaming file hashing to avoid loading entire files into memory."""
import hashlib
from pathlib import Path


def sha256_file(path: Path) -> str:
    if not path.is_file():
        raise FileNotFoundError(f"File not found: {path}")
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_sha256(path: Path, expected: str) -> bool:
    if len(expected) != 64 or any(c not in "0123456789abcdefABCDEF" for c in expected):
        raise ValueError("Expected SHA-256 must be exactly 64 hexadecimal characters")
    return sha256_file(path).lower() == expected.lower()
