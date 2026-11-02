"""GUI integration against real file modules; DNS is deliberately mocked."""
import hashlib
import json
import os
import time

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import pytest
pytest.importorskip('PySide6')
from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox
from PIL import Image
from ghost_tools.gui import Window, STYLE


@pytest.fixture
def window():
    app = QApplication.instance() or QApplication([])
    app.setStyleSheet(STYLE)
    widget = Window()
    yield widget
    deadline = time.monotonic() + 10
    while widget.job is not None and time.monotonic() < deadline:
        app.processEvents()
        time.sleep(.01)
    widget.close()


def complete(window):
    deadline = time.monotonic() + 10
    while window.job is not None and time.monotonic() < deadline:
        QApplication.processEvents()
        time.sleep(.01)
    assert window.job is None


def test_real_hash_mismatch_and_error(window, tmp_path):
    path = tmp_path / 'payload.txt'
    path.write_bytes(b'ghost')
    window.file.setText(str(path))
    window.hash_file()
    complete(window)
    assert window.report['rows'][0][1] == hashlib.sha256(b'ghost').hexdigest()
    window.expected.setText('0' * 64)
    window.hash_file()
    complete(window)
    assert window.report['rows'][0][2] == 'MISMATCH'
    window.expected.setText('invalid')
    window.hash_file()
    complete(window)
    assert window.report is None
    assert not window.export.isEnabled()
    assert 'Failed' in window.status.text()


def test_metadata_scan_export_and_source_protection(window, tmp_path, monkeypatch):
    image = tmp_path / 'photo.jpg'
    exif = Image.Exif()
    exif[315] = 'Example creator'
    Image.new('RGB', (8, 8)).save(image, exif=exif)
    original = image.read_bytes()
    window.image.setText(str(image))
    window.inspect()
    complete(window)
    assert any(f['severity'] == 'MEDIUM' for f in window.report['files'][0]['findings'])
    monkeypatch.setattr(QFileDialog, 'getSaveFileName', lambda *args: (str(image), ''))
    warnings = []
    monkeypatch.setattr(QMessageBox, 'warning', lambda *args: warnings.append(args))
    window.export_report()
    assert warnings and image.read_bytes() == original
    destination = tmp_path / 'report.json'
    monkeypatch.setattr(QFileDialog, 'getSaveFileName', lambda *args: (str(destination), ''))
    window.export_report()
    assert json.loads(destination.read_text())['result']['module'] == 'metadata'
    window.directory.setText(str(tmp_path))
    window.scan()
    complete(window)
    assert len(window.report['files']) == 1
    assert image.read_bytes() == original


def test_password_secrets_excluded_and_dns(window, monkeypatch):
    window.generate()
    secret = window.password.text()
    assert len(secret) == 24
    assert secret not in json.dumps(window.report)
    window.password.setText('password123')
    window.check_password()
    assert window.report['rows'][0][1] == 'WEAK'
    monkeypatch.setattr('ghost_tools.gui.lookup_dns', lambda host: ['192.0.2.1'])
    window.host.setText('example.test')
    window.resolve()
    complete(window)
    assert window.report['rows'][0][1] == '192.0.2.1'


def test_busy_window_does_not_close(window):
    import threading
    gate = threading.Event()
    window.start(lambda: (gate.wait(2), {'summary':'Done', 'rows':[]})[1])
    window.show()
    window.close()
    assert window.isVisible()
    gate.set()
    complete(window)


def test_empty_folder_requires_explicit_selection(window):
    window.scan()
    assert window.job is None
    assert 'Choose a folder' in window.status.text()


def test_invalid_scan_discards_previous_report(window):
    window.generate()
    assert window.report is not None
    window.scan()
    assert window.report is None
    assert not window.export.isEnabled()
    assert not window.copy.isEnabled()
    assert window.table.rowCount() == 0


def test_switching_modules_clears_previous_module_result(window):
    window.generate()
    window.nav.setCurrentRow(4)
    assert window.report is None
    assert window.table.rowCount() == 0
    assert not window.export.isEnabled()


def test_gui_rejects_hardlink_to_hashed_source(window, tmp_path, monkeypatch, hardlink):
    source = tmp_path / 'source.txt'
    source.write_bytes(b'preserve me')
    alias = tmp_path / 'report.json'
    hardlink(source, alias)
    window.file.setText(str(source))
    window.hash_file()
    complete(window)
    monkeypatch.setattr(QFileDialog, 'getSaveFileName', lambda *args: (str(alias), ''))
    warnings = []
    monkeypatch.setattr(QMessageBox, 'warning', lambda *args: warnings.append(args))
    window.export_report()
    assert warnings
    assert source.read_bytes() == alias.read_bytes() == b'preserve me'


def test_invalid_expected_digest_does_not_read_file(window, monkeypatch):
    def forbidden(*args):
        raise AssertionError('File was read despite an invalid expected checksum')
    monkeypatch.setattr('ghost_tools.gui.sha256_file', forbidden)
    window.expected.setText('invalid')
    window.hash_file()
    complete(window)
    assert '64 hexadecimal' in window.status.text()

