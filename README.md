# GHOST//TOOLS

**KNOW YOUR EXPOSURE.**

A native dark Windows desktop workspace and Python CLI for inspecting image metadata, verifying file hashes, creating passwords and understanding basic digital privacy exposure.

> **Desktop 0.2.0:** Educational software. It cannot guarantee security or anonymity. It never uploads file contents. DNS lookups intentionally use the configured system resolver and therefore may create network traffic.

## Windows desktop — no Python required

Download `GHOST-TOOLS-windows-x64.zip` from [Releases](https://github.com/Squeeezz/ghost-tools/releases) when a tagged release is available, or from the successful [Windows desktop workflow](https://github.com/Squeeezz/ghost-tools/actions/workflows/windows.yml) artifact for the development branch (GitHub login required for workflow artifacts).

Extract the **entire ZIP**, open the `GHOST-TOOLS` folder and double-click `GHOST-TOOLS.exe`. Keep `_internal` beside the EXE; this portable distribution requires no Python installation or terminal. Windows x64 is the build target. Builds are unsigned; no publisher signature is claimed.

The desktop offers a sidebar, file/folder drag-and-drop, background processing, color-coded findings with explanations, JSON export, hash comparison and hidden password input. It starts with no fabricated analysis results. Reports are held in memory until explicitly exported and exclude passwords. GUI and CLI exports protect inspected source paths, including symlink/hard-link aliases; report writes replace the destination atomically. Switching modules or a failed analysis clears the previous result. Explicit clipboard actions use the system clipboard, whose history may retain copied material.

While an operation runs, navigation and close are held until it completes. DNS duration is controlled by the operating system resolver; folder scans are bounded by the selected image limit but can still take time on large trees. No cancellation or progress percentage is claimed.

## Desktop development and Windows packaging

```powershell
python -m pip install -e ".[desktop,dev,build]"
ghost-desktop
python -m pytest -q
python -m PyInstaller --noconfirm --clean GHOST-TOOLS.spec
```

`python -m ghost_tools.gui` is an alternative desktop entry point. The CLI remains available without installing the desktop extra. GUI tests skip when Qt is absent; Windows CI installs Qt and runs them, bundles the app and smoke-tests the actual EXE. On branch pushes and PRs it uploads a portable ZIP plus SHA-256 checksum for 30 days. Pushing a `v*` tag builds and publishes those assets to GitHub Releases after successful checks. Build Windows distributions on Windows.

Qt/PySide6 remains dynamically linked in the portable folder. See [third-party notices](THIRD-PARTY-NOTICES.md) for licenses and source locations.

## Features

- **METADATA** – Read image EXIF metadata and flag GPS, device identifiers and timestamps.
- **HASH** – Stream SHA-256 checksums and verify file integrity.
- **PASSWORD** – Generate strong random passwords and check simple password heuristics offline.
- **NETWORK** – Resolve a hostname using the operating system's DNS resolver.
- **FOOTPRINT** – Scan a directory of supported images for flagged metadata and export JSON reports.

## Install

Requires Python 3.10 or newer.

```bash
git clone https://github.com/Squeeezz/ghost-tools.git
cd ghost-tools
python -m venv .venv
```

On Windows PowerShell:

```powershell
.venv\Scripts\python -m pip install -e .
.venv\Scripts\ghost --help
```

On Linux/macOS:

```bash
.venv/bin/pip install -e .
.venv/bin/ghost --help
```

## Examples

```bash
ghost metadata inspect ./photo.jpg
ghost metadata inspect ./photo.jpg --output report.json
ghost hash calculate ./download.zip
ghost hash verify ./download.zip <trusted-sha256>
ghost password generate --length 24
ghost password check
ghost network dns example.org
ghost footprint scan ./pictures --limit 100 --output privacy-report.json
```

Use `python -m ghost_tools` as an alternative after installation.

## Safety & privacy

- Source files are opened read-only. Reports are written **only** when `--output` is requested.
- Password checks use hidden interactive input and don't store passwords. Generated passwords are printed to terminal scrollback; handle them carefully.
- Reports may include sensitive metadata, including identifying information. Review before sharing.
- Not all metadata formats or file types are supported. No finding ≠ proof of privacy.
- The inspector reads top-level EXIF and detects GPS presence; it does not comprehensively decode nested camera EXIF, XMP, IPTC, documents or all metadata. Risk labels describe disclosure potential, not malware detection.
- Directory scans reject linked scan roots, skip symlink/Windows reparse-point directories (including junctions on Python 3.10), and report traversal/read errors. Reaching the configured image limit may leave additional images uninspected.
- DNS commands require a network connection and may disclose queried hostnames to your configured resolver.
- Only scan data and systems you own or are permitted to inspect.

## Development

```bash
python -m pip install -e '.[dev]'
pytest -q
```

## Roadmap

- [x] CLI with modular commands
- [x] Local EXIF overview and privacy hints
- [x] SHA-256 hashing and verification
- [x] Local password tools
- [x] DNS diagnostics
- [x] Directory metadata scanning and JSON export
- [x] Native PySide6 desktop and portable Windows build workflow
- [ ] Broader metadata support via ExifTool
- [ ] More advanced contextual privacy analysis
- [ ] Optional safe metadata stripping on **copies**
- [ ] Interactive terminal dashboard

## License

MIT. Copyright (c) 2026 Squeeezz.
