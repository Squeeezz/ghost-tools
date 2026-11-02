# Third-party components

GHOST//TOOLS source is MIT licensed. The portable Windows distribution also
contains Python, Pillow, PySide6 Essentials, Shiboken6, Qt and the PyInstaller
bootloader. Their respective licenses continue to apply.

Qt/PySide6/Shiboken are dynamically loaded, unmodified libraries distributed
under their applicable LGPL/GPL or permissive component licenses. Qt license
texts are included under `_internal/licenses/Qt`, with wheel metadata and any
additional wheel notices included alongside the bundled packages.
The portable folder intentionally keeps these libraries replaceable. You may
replace compatible libraries and reverse engineer for debugging modifications
as permitted by the LGPL. Do not distribute the EXE without its companion files.

- Qt/PySide source and license information: https://code.qt.io/pyside/pyside-setup.git/
- Corresponding Qt sources: https://download.qt.io/official_releases/qt/
- For the tested Qt 6.10.3 build: https://download.qt.io/official_releases/qt/6.10/6.10.3/submodules/
- PySide/Shiboken 6.10.3 sources: https://download.qt.io/official_releases/QtForPython/pyside6/PySide6-6.10.3-src/
- Qt licensing: https://doc.qt.io/qtforpython-6/licenses.html
- Python: https://docs.python.org/3/license.html
- Pillow: https://github.com/python-pillow/Pillow/blob/main/LICENSE
- PyInstaller bootloader exception: https://pyinstaller.org/en/stable/license.html

Package license files and metadata are included by the build where available.
For the exact bundled versions, see `_internal/BUILD-VERSIONS.txt`.
