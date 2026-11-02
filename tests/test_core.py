import hashlib
from pathlib import Path
from PIL import Image
from ghost_tools.hashing import sha256_file, verify_sha256
from ghost_tools.credentials import analyze_password, generate_password
from ghost_tools.metadata import inspect_image
from ghost_tools.footprint import scan_directory
from ghost_tools.core import assess_field, export_json
import json
import pytest


def test_hash(tmp_path):
    file = tmp_path / "sample.txt"
    file.write_bytes(b"ghost")
    expected = hashlib.sha256(b"ghost").hexdigest()
    assert sha256_file(file) == expected
    assert verify_sha256(file, expected)
    assert not verify_sha256(file, "0" * 64)
    with pytest.raises(ValueError):
        verify_sha256(file, "invalid")


def test_password():
    pw = generate_password(32)
    assert len(pw) == 32
    assert analyze_password("password123")[0] == "WEAK"
    with pytest.raises(ValueError):
        generate_password(4)


def test_metadata_and_directory(tmp_path):
    image_path = tmp_path / "test.jpg"
    Image.new("RGB", (10, 10), color="white").save(image_path)
    result = inspect_image(image_path)
    assert result.filename == str(image_path)
    assert len(scan_directory(tmp_path)) == 1
    assert assess_field("GPSInfo", "present").severity == "HIGH"


def test_export(tmp_path):
    target = tmp_path / "report.json"
    export_json({"flagged": 2}, target)
    assert json.loads(target.read_text())["result"]["flagged"] == 2
