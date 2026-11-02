"""Regression coverage for source preservation and linked-directory boundaries."""
import json
import stat
from types import SimpleNamespace

from PIL import Image
import pytest
from typer.testing import CliRunner

from ghost_tools.cli import app
from ghost_tools.core import export_json
from ghost_tools.footprint import _linked, scan_directory
from ghost_tools.metadata import inspect_image


def test_report_rejects_source_hardlink(tmp_path, hardlink):
    source = tmp_path / 'source.jpg'
    source.write_bytes(b'original data')
    alias = tmp_path / 'alias.json'
    hardlink(source, alias)
    with pytest.raises(ValueError, match='link'):
        export_json({'test': True}, alias, protected_paths=[source])
    assert source.read_bytes() == alias.read_bytes() == b'original data'


def test_report_failure_preserves_previous_report(tmp_path, monkeypatch):
    destination = tmp_path / 'report.json'
    destination.write_text('old report', encoding='utf-8')
    def fail(*args):
        raise OSError('simulated write failure')
    monkeypatch.setattr('ghost_tools.core.os.replace', fail)
    with pytest.raises(OSError):
        export_json({'new': True}, destination)
    assert destination.read_text() == 'old report'
    assert list(tmp_path.iterdir()) == [destination]


def test_report_overwrites_only_selected_report(tmp_path):
    destination = tmp_path / 'report.json'
    destination.write_text('old report', encoding='utf-8')
    export_json({'new': True}, destination)
    assert json.loads(destination.read_text())['result']['new']


def test_cli_refuses_image_as_report_destination(tmp_path):
    source = tmp_path / 'image.jpg'
    Image.new('RGB', (4, 4)).save(source)
    original = source.read_bytes()
    result = CliRunner().invoke(app, ['metadata', 'inspect', str(source), '-o', str(source)])
    assert result.exit_code == 1
    assert source.read_bytes() == original


def test_cli_folder_scan_preserves_sources_and_reports_corruption(tmp_path):
    source = tmp_path / 'image.jpg'
    source.write_bytes(b'corrupted image')
    result = CliRunner().invoke(app, ['footprint', 'scan', str(tmp_path), '-o', str(source)])
    assert result.exit_code == 1
    assert 'Skipped:' in result.output
    assert source.read_bytes() == b'corrupted image'


def test_reparse_detection_without_python312_junction_method():
    # Simulate the lstat API available on Windows/Python 3.10.
    path = SimpleNamespace(lstat=lambda: SimpleNamespace(
        st_mode=stat.S_IFDIR, st_file_attributes=stat.FILE_ATTRIBUTE_REPARSE_POINT))
    assert _linked(path)


def test_linked_root_rejected(tmp_path, monkeypatch):
    monkeypatch.setattr('ghost_tools.footprint._linked', lambda path: True)
    with pytest.raises(ValueError, match='real directory'):
        scan_directory(tmp_path)


def test_reparse_child_is_pruned(tmp_path, monkeypatch):
    inside = tmp_path / 'linked'
    inside.mkdir()
    Image.new('RGB', (4, 4)).save(inside / 'private.jpg')
    monkeypatch.setattr('ghost_tools.footprint._linked', lambda path: path == inside)
    assert scan_directory(tmp_path) == []


def test_cli_prints_filename_and_metadata_as_literal_text(tmp_path, monkeypatch):
    monkeypatch.setattr('ghost_tools.cli.console.width', 500)
    source = tmp_path / '[red]x.jpg'
    exif = Image.Exif()
    exif[315] = '[/]'
    Image.new('RGB', (4, 4)).save(source, exif=exif)
    result = CliRunner().invoke(app, ['metadata', 'inspect', str(source)])
    assert result.exit_code == 0
    assert '[red]x.jpg' in result.output
    assert '[/]' in result.output


def test_oversized_image_is_a_reported_error(tmp_path, monkeypatch):
    source = tmp_path / 'large.png'
    Image.new('RGB', (4, 4)).save(source)
    monkeypatch.setattr(Image, 'MAX_IMAGE_PIXELS', 1)
    with pytest.raises(ValueError, match='Cannot inspect'):
        inspect_image(source)
    reports = scan_directory(tmp_path)
    assert len(reports) == 1
    assert reports[0].warnings[0].startswith('Skipped:')
