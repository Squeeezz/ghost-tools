# Portable directory distribution preserves replaceable Qt DLLs and starts quickly.
from pathlib import Path
import sys
from importlib.metadata import distributions
from PyInstaller.utils.hooks import copy_metadata
import PySide6

qt = Path(PySide6.__file__).parent
license_files = [(str(p), 'licenses/Qt') for p in qt.rglob('*')
                 if p.is_file() and (p.name.startswith('LICENSE') or p.name.startswith('COPYING'))]
license_files.extend((str(p), 'licenses/Qt') for p in Path('licenses').glob('*.txt'))
python_license = Path(sys.base_prefix) / 'LICENSE.txt'
if python_license.exists():
    license_files.append((str(python_license), 'licenses/Python'))
versions = Path('build/BUILD-VERSIONS.txt')
versions.parent.mkdir(exist_ok=True)
versions.write_text('\n'.join(sorted(f'{d.metadata["Name"]}=={d.version}' for d in distributions())), encoding='utf-8')
license_files.append((str(versions), '.'))
for package in ['Pillow', 'PySide6-Essentials', 'shiboken6']:
    license_files.extend(copy_metadata(package))
a = Analysis(['desktop.py'], pathex=['src'], binaries=[], datas=license_files,
             hiddenimports=[], hookspath=[], hooksconfig={}, runtime_hooks=[],
             excludes=['tkinter', 'PySide6.QtQml', 'PySide6.QtQuick', 'PySide6.QtNetwork'])
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='GHOST-TOOLS',
          debug=False, bootloader_ignore_signals=False, strip=False, upx=False,
          console=False, disable_windowed_traceback=False)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name='GHOST-TOOLS')
