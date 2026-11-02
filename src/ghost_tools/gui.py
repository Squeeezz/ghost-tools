"""Native desktop interface. Results come exclusively from the local modules."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QFileDialog, QFrame, QHBoxLayout, QLabel,
    QLineEdit, QListWidget, QMainWindow, QMessageBox, QProgressBar,
    QPushButton, QSpinBox, QStackedWidget, QTableWidget, QTableWidgetItem,
    QHeaderView, QVBoxLayout, QWidget,
)

from . import __version__
from .core import export_json
from .credentials import analyze_password, generate_password
from .footprint import scan_directory
from .hashing import sha256_file
from .metadata import inspect_image
from .network import lookup_dns

STYLE = """
QWidget { background:#101418; color:#dbe4e9; font: 10pt 'Segoe UI'; }
QMainWindow { background:#101418; }
QLabel#brand { color:#a8f0c0; font:700 21pt 'Consolas'; }
QLabel#title { font:600 24pt 'Segoe UI'; color:#f1f7fa; }
QLabel#muted { color:#94a6b1; }
QLabel#eyebrow { color:#7edda0; font:10pt 'Consolas'; }
QFrame#panel { background:#171e24; border:1px solid #29353d; border-radius:10px; }
QFrame#panel QLabel { background:transparent; }
QListWidget { border:0; background:#0c1013; padding:12px; outline:0; }
QListWidget::item { padding:15px 12px; margin:3px 0; border-radius:6px; color:#9aaeb9; }
QListWidget::item:selected { background:#203b30; color:#a8f0c0; }
QLineEdit,QSpinBox { background:#0b1014; border:1px solid #35454e; border-radius:6px; padding:10px; selection-background-color:#365b47; }
QLineEdit:focus,QSpinBox:focus { border-color:#7edda0; }
QPushButton { background:#24313a; border:1px solid #3a4b56; border-radius:6px; padding:10px 16px; }
QPushButton:hover { background:#324650; }
QPushButton#primary { background:#9ae6b4; color:#102419; font-weight:600; border:0; }
QPushButton:disabled { background:#1d262c; color:#63737c; }
QTableWidget { background:#12191e; alternate-background-color:#182127; border:1px solid #29353d; gridline-color:#29353d; selection-background-color:#294335; }
QHeaderView::section { background:#202c34; color:#a2b6c0; padding:10px; border:0; }
QProgressBar { border:0; background:#1e2c32; height:3px; }
QProgressBar::chunk { background:#9ae6b4; }
QCheckBox { spacing:8px; }
"""


class Job(QThread):
    succeeded = Signal(object)
    failed = Signal(str)

    def __init__(self, task, parent=None):
        super().__init__(parent)
        self.task = task

    def run(self):
        try:
            self.succeeded.emit(self.task())
        except Exception as exc:
            self.failed.emit(str(exc))


class PathEdit(QLineEdit):
    def __init__(self, directory=False):
        super().__init__()
        self.directory = directory
        self.setAcceptDrops(True)
        self.setPlaceholderText('Drop a folder here or browse…' if directory else 'Drop a file here or browse…')

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls() and len(event.mimeData().urls()) == 1:
            url = event.mimeData().urls()[0]
            if url.isLocalFile() and Path(url.toLocalFile()).is_dir() == self.directory:
                event.acceptProposedAction()

    def dropEvent(self, event):
        self.setText(event.mimeData().urls()[0].toLocalFile())
        event.acceptProposedAction()


def label(text, name=None):
    widget = QLabel(text)
    widget.setWordWrap(True)
    widget.setTextFormat(Qt.TextFormat.PlainText)
    if name:
        widget.setObjectName(name)
    return widget


class Window(QMainWindow):
    names = ['Overview', 'Metadata inspector', 'File integrity', 'Password lab', 'DNS resolver', 'Privacy footprint']

    def __init__(self):
        super().__init__()
        self.setWindowTitle('GHOST//TOOLS — Know your exposure')
        self.resize(1220, 850)
        self.setMinimumSize(900, 700)
        self.job = None
        self.report = None
        self.source_paths = []
        self.completed = 0
        root = QWidget()
        self.setCentralWidget(root)
        outer = QHBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        sidebar = QWidget()
        sidebar.setFixedWidth(245)
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(18, 28, 18, 22)
        side.addWidget(label('GHOST//\nTOOLS', 'brand'))
        side.addWidget(label('KNOW YOUR EXPOSURE.', 'eyebrow'))
        self.nav = QListWidget()
        self.nav.addItems(self.names)
        side.addWidget(self.nav, 1)
        side.addWidget(label(f'v{__version__}  /  DESKTOP\nLocal files stay local.\nDNS uses your system resolver.', 'muted'))
        outer.addWidget(sidebar)
        content = QVBoxLayout()
        content.setContentsMargins(30, 28, 30, 24)
        content.setSpacing(14)
        outer.addLayout(content, 1)
        content.addWidget(label('GHOST SYSTEMS    /    LOCAL-FIRST TOOLKIT', 'eyebrow'))
        self.title = label(self.names[0], 'title')
        content.addWidget(self.title)
        self.stack = QStackedWidget()
        content.addWidget(self.stack)
        self.build_pages()
        self.status = label('Ready — choose a module to begin.', 'muted')
        content.addWidget(self.status)
        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(4)
        self.progress.setRange(0, 1)
        self.progress.setValue(0)
        content.addWidget(self.progress)
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(['FIELD / SOURCE', 'VALUE', 'SIGNAL', 'EXPLANATION'])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setColumnWidth(0, 170)
        self.table.setColumnWidth(1, 245)
        self.table.setColumnWidth(2, 90)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setVisible(False)
        content.addWidget(self.table, 1)
        actions = QHBoxLayout()
        self.copy = QPushButton('Copy result')
        self.copy.clicked.connect(self.copy_result)
        self.export = QPushButton('Export JSON…')
        self.export.clicked.connect(self.export_report)
        self.copy.setEnabled(False)
        self.export.setEnabled(False)
        actions.addWidget(label('Results are observations, never a security guarantee.', 'muted'), 1)
        actions.addWidget(self.copy)
        actions.addWidget(self.export)
        content.addLayout(actions)
        self.nav.currentRowChanged.connect(self.navigate)
        self.nav.setCurrentRow(0)

    def panel(self, explanation):
        frame = QFrame()
        frame.setObjectName('panel')
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)
        layout.addWidget(label(explanation, 'muted'))
        self.stack.addWidget(frame)
        return layout

    def path_row(self, layout, directory=False):
        row = QHBoxLayout()
        edit = PathEdit(directory)
        button = QPushButton('Browse…')
        def browse():
            path = QFileDialog.getExistingDirectory(self, 'Choose folder') if directory else QFileDialog.getOpenFileName(self, 'Choose file')[0]
            if path:
                edit.setText(path)
        button.clicked.connect(browse)
        row.addWidget(edit, 1)
        row.addWidget(button)
        layout.addLayout(row)
        return edit

    def action(self, layout, text, callback):
        button = QPushButton(text)
        button.setObjectName('primary')
        button.clicked.connect(callback)
        layout.addWidget(button, alignment=Qt.AlignmentFlag.AlignLeft)

    def build_pages(self):
        home = self.panel('A focused workspace for inspecting your own files and understanding the traces they carry. No uploads, no telemetry, no invented threat scores.')
        home.addWidget(label('01  INSPECT     Image EXIF and identifying fields\n02  VERIFY       SHA-256 against a trusted checksum\n03  CREATE      Random passwords, checked locally\n04  RESOLVE    Explicit DNS queries\n05  REVIEW      Image metadata across a folder'))
        self.session = label('No analyses run in this session.', 'eyebrow')
        home.addWidget(self.session)
        meta = self.panel('Read supported image EXIF without modifying the source. JPEG, TIFF, PNG and WebP support depends on the metadata present. XMP/IPTC and nested camera EXIF are not comprehensively inspected.')
        self.image = self.path_row(meta)
        self.action(meta, 'Inspect metadata', self.inspect)
        hashes = self.panel('SHA-256 detects differences from a trusted digest. A match alone does not establish that a file is safe.')
        self.file = self.path_row(hashes)
        self.expected = QLineEdit()
        self.expected.setPlaceholderText('Optional: trusted SHA-256 checksum (64 hexadecimal characters)')
        hashes.addWidget(self.expected)
        self.action(hashes, 'Calculate / verify', self.hash_file)
        passwords = self.panel('Local heuristic only; no breach lookup. Passwords are hidden and excluded from reports. Copying explicitly places the secret on your system clipboard.')
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.password.setPlaceholderText('Enter a password or generate one')
        passwords.addWidget(self.password)
        row = QHBoxLayout()
        self.length = QSpinBox()
        self.length.setRange(12, 256)
        self.length.setValue(24)
        row.addWidget(label('Generated length'))
        row.addWidget(self.length)
        reveal = QCheckBox('Show password')
        reveal.toggled.connect(lambda checked: self.password.setEchoMode(QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password))
        row.addWidget(reveal)
        for text, callback in [('Generate', self.generate), ('Check', self.check_password), ('Copy password', self.copy_password), ('Clear', self.password.clear)]:
            button = QPushButton(text)
            button.clicked.connect(callback)
            row.addWidget(button)
        passwords.addLayout(row)
        dns = self.panel('Resolves a hostname through the operating system. This action can send a network query and disclose the hostname to your configured resolver. It is not a port scan or a privacy test.')
        self.host = QLineEdit()
        self.host.setPlaceholderText('Hostname, e.g. example.org')
        dns.addWidget(self.host)
        self.action(dns, 'Resolve hostname', self.resolve)
        footprint = self.panel('Recursively inspect supported images, skipping symlink/junction directories. Limit counts attempted images; skipped files and traversal warnings remain visible. Reaching the limit means the scan may be incomplete.')
        self.directory = self.path_row(footprint, True)
        self.limit = QSpinBox()
        self.limit.setRange(1, 10000)
        self.limit.setValue(100)
        footprint.addWidget(label('Maximum images to attempt'))
        footprint.addWidget(self.limit)
        self.action(footprint, 'Scan image folder', self.scan)

    def navigate(self, index):
        self.stack.setCurrentIndex(index)
        self.title.setText(self.names[index])

    def start(self, task, paths=()):
        if self.job is not None:
            return
        self.source_paths = [Path(p).resolve() for p in paths]
        self.report = None
        self.copy.setEnabled(False)
        self.export.setEnabled(False)
        self.table.setRowCount(0)
        self.status.setText('Working… Results will appear when the operation completes.')
        self.progress.setRange(0, 0)
        self.stack.setEnabled(False)
        self.nav.setEnabled(False)
        self.job = Job(task, self)
        self.job.succeeded.connect(self.show_result)
        self.job.failed.connect(self.show_error)
        self.job.finished.connect(self.finish)
        self.job.start()

    def finish(self):
        job = self.job
        self.job = None
        job.deleteLater()
        self.stack.setEnabled(True)
        self.nav.setEnabled(True)
        self.progress.setRange(0, 1)
        self.progress.setValue(1)

    def show_error(self, message):
        self.status.setText('Failed — ' + message)

    def show_result(self, result):
        self.report = result
        self.completed += 1
        self.session.setText(f'{self.completed} completed operation(s) this session. No persistent history.')
        rows = []
        for report in result.get('files', []):
            for finding in report['findings']:
                rows.append([f"{report['filename']} / {finding['field']}", finding['value'], finding['severity'], finding['explanation']])
            for warning in report['warnings']:
                rows.append([report['filename'], warning, 'NOTICE', 'Inspection limitation'])
        rows.extend(result.get('rows', []))
        self.table.setRowCount(len(rows))
        for row, values in enumerate(rows):
            for column, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setToolTip(str(value))
                if column == 2:
                    item.setForeground(QColor({'HIGH':'#ff9292', 'MEDIUM':'#f2c47c', 'MATCH':'#9ae6b4', 'MISMATCH':'#ff9292'}.get(str(value), '#94b8ca')))
                self.table.setItem(row, column, item)
        self.status.setText(result['summary'])
        self.copy.setEnabled(True)
        self.export.setEnabled(True)

    def inspect(self):
        path = Path(self.image.text())
        self.start(lambda: {'module':'metadata', 'files':[inspect_image(path).to_dict()], 'summary':'Inspection complete. Only readable EXIF fields were assessed.'}, [path])

    def hash_file(self):
        path = Path(self.file.text())
        expected = self.expected.text().strip()
        def task():
            digest = sha256_file(path)
            signal = 'INFO'
            if expected:
                # Validate via the existing API; reuse the computed digest for comparison.
                if len(expected) != 64 or any(c not in '0123456789abcdefABCDEF' for c in expected):
                    raise ValueError('Expected SHA-256 must be exactly 64 hexadecimal characters')
                signal = 'MATCH' if digest.lower() == expected.lower() else 'MISMATCH'
            return {'module':'hash', 'summary':f'SHA-256 complete — {signal}.', 'rows':[[str(path), digest, signal, 'Compare with a checksum from a trusted source.']], 'expected':expected or None}
        self.start(task, [path])

    def generate(self):
        self.password.setText(generate_password(self.length.value()))
        self.check_password()

    def check_password(self):
        self.source_paths = []
        rating, comments = analyze_password(self.password.text())
        self.show_result({'module':'password', 'summary':'Local heuristic complete. Secret excluded from report.', 'rows':[['Password heuristic', rating, 'INFO', comment] for comment in comments]})

    def copy_password(self):
        QApplication.clipboard().setText(self.password.text())
        self.status.setText('Password copied to system clipboard. Clipboard history may retain it.')

    def resolve(self):
        host = self.host.text().strip()
        self.start(lambda: {'module':'dns', 'summary':f'DNS resolution complete for {host}.', 'rows':[[host, ip, 'INFO', 'Address returned by the system resolver.'] for ip in lookup_dns(host)]})

    def scan(self):
        if not self.directory.text().strip():
            self.show_error('Choose a folder before starting a scan.')
            return
        directory = Path(self.directory.text())
        limit = self.limit.value()
        def task():
            reports = scan_directory(directory, limit)
            return {'module':'footprint', 'files':[r.to_dict() for r in reports], 'limit':limit, 'summary':f'{len(reports)} report(s). ' + ('Limit reached; more images may remain.' if len(reports) >= limit else 'Traversal finished; review warnings for skipped paths.')}
        self.start(task, [directory])

    def copy_result(self):
        if self.report is not None:
            QApplication.clipboard().setText(json.dumps(self.report, indent=2, ensure_ascii=False))
            self.status.setText('Result copied. Reports can contain identifying metadata.')

    def export_report(self):
        if self.report is None:
            return
        filename, _ = QFileDialog.getSaveFileName(self, 'Export report', 'ghost-report.json', 'JSON (*.json)')
        if not filename:
            return
        destination = Path(filename).resolve()
        sources = self.source_paths + [Path(r['filename']).resolve() for r in self.report.get('files', [])]
        if destination in sources:
            QMessageBox.warning(self, 'Choose another destination', 'A report cannot overwrite an inspected source file or folder.')
            return
        try:
            export_json(self.report, destination)
            self.status.setText(f'Report saved: {destination}')
        except (OSError, ValueError) as exc:
            self.show_error(str(exc))

    def closeEvent(self, event):
        if self.job is not None:
            self.status.setText('An operation is running. Wait for it to finish before closing.')
            event.ignore()
        else:
            self.password.clear()
            event.accept()


def main():
    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName('GHOST//TOOLS')
    app.setStyle('Fusion')
    app.setStyleSheet(STYLE)
    window = Window()
    window.show()
    if '--smoke-test' in sys.argv:
        QTimer.singleShot(600, window.close)
    return app.exec()


if __name__ == '__main__':
    sys.exit(main())
