# GHOST//TOOLS

**KNOW YOUR EXPOSURE.**

A minimal, local-first Python CLI toolkit for inspecting image metadata, verifying file hashes, creating passwords and understanding basic digital privacy exposure.

> **Alpha 0.1.0:** Educational software. It cannot guarantee security or anonymity. It never uploads file contents. DNS lookups intentionally use the configured system resolver and therefore may create network traffic.

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
- [ ] Broader metadata support via ExifTool
- [ ] More advanced contextual privacy analysis
- [ ] Optional safe metadata stripping on **copies**
- [ ] Interactive terminal dashboard

## License

MIT. Copyright (c) 2026 Squeeezz.
