"""GHOST//TOOLS CLI."""
from __future__ import annotations

import getpass
import socket
from pathlib import Path
from typing import Optional
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from . import __version__
from .core import ScanResult, export_json
from .credentials import analyze_password, generate_password
from .footprint import scan_directory
from .hashing import sha256_file, verify_sha256
from .metadata import inspect_image
from .network import lookup_dns

app = typer.Typer(help="GHOST//TOOLS — Know your exposure.", no_args_is_help=False)
metadata_app = typer.Typer(help="Inspect image metadata.")
hash_app = typer.Typer(help="Calculate and verify file hashes.")
password_app = typer.Typer(help="Local password utilities.")
network_app = typer.Typer(help="DNS diagnostics.")
footprint_app = typer.Typer(help="Scan your own local image directory.")
for name, sub in [("metadata", metadata_app), ("hash", hash_app), ("password", password_app), ("network", network_app), ("footprint", footprint_app)]:
    app.add_typer(sub, name=name)
console = Console()


def show_report(report: ScanResult) -> None:
    console.print(Panel.fit(Text(report.filename, style="bold green"), title="LOCAL FILE SCAN"))
    table = Table("Field", "Value", "Signal", show_lines=True)
    for item in report.findings:
        table.add_row(Text(item.field), Text(item.value), Text(item.severity))
    console.print(table)
    for warning in report.warnings:
        console.print(f"! {warning}", style="yellow", markup=False)
    console.print("[dim]Risk labels are informational, not guarantees of security.[/dim]")


def failure(error: Exception) -> None:
    console.print(f"Error: {error}", style="red", markup=False)
    raise typer.Exit(code=1)


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context, version: bool = typer.Option(False, "--version", help="Show version.")) -> None:
    if version:
        console.print(__version__)
        raise typer.Exit()
    if ctx.invoked_subcommand is None:
        console.print(Panel("[bold green]GHOST//TOOLS[/bold green]\nKNOW YOUR EXPOSURE.\n\nRun [cyan]ghost --help[/cyan] to explore modules.", title="LOCAL-FIRST SECURITY TOOLKIT"))


@metadata_app.command("inspect")
def metadata_inspect(path: Path, output: Optional[Path] = typer.Option(None, "--output", "-o")) -> None:
    """Inspect image EXIF fields without modifying the file."""
    try:
        result = inspect_image(path)
        show_report(result)
        if output is not None:
            export_json(result.to_dict(), output, protected_paths=[path])
            console.print(f"Report saved: {output}", markup=False)
    except (OSError, ValueError) as exc:
        failure(exc)


@hash_app.command("calculate")
def hash_calculate(path: Path) -> None:
    """Compute a SHA-256 file checksum."""
    try:
        console.print(f"SHA-256 {sha256_file(path)}  {path}", markup=False)
    except OSError as exc:
        failure(exc)


@hash_app.command("verify")
def hash_verify(path: Path, expected: str) -> None:
    """Compare a file checksum against a trusted expected digest."""
    try:
        valid = verify_sha256(path, expected)
    except (OSError, ValueError) as exc:
        failure(exc)
    console.print("[green]MATCH[/green]" if valid else "[red]MISMATCH[/red]")
    if not valid:
        raise typer.Exit(code=2)


@password_app.command("generate")
def password_generate(length: int = typer.Option(24, min=12, max=256)) -> None:
    """Create a cryptographically random password (visible in the terminal)."""
    try:
        console.print(generate_password(length))
        console.print("[yellow]Warning: terminal output may be retained in logs or scrollback.[/yellow]")
    except ValueError as exc:
        failure(exc)


@password_app.command("check")
def password_check() -> None:
    """Analyze a password locally without placing it in shell history."""
    try:
        password = getpass.getpass("Password (hidden): ")
        rating, comments = analyze_password(password)
        console.print(f"[bold]Result:[/bold] {rating}")
        for comment in comments:
            console.print(f" • {comment}")
        console.print("[dim]No network checks and no password storage.[/dim]")
    except (EOFError, KeyboardInterrupt) as exc:
        failure(exc)


@network_app.command("dns")
def network_dns(host: str) -> None:
    """Resolve a hostname via your operating system's DNS resolver."""
    try:
        for ip in lookup_dns(host):
            console.print(ip)
    except (OSError, ValueError, socket.gaierror) as exc:
        failure(exc)


@footprint_app.command("scan")
def footprint_scan(directory: Path, limit: int = typer.Option(100, min=1, max=10000), output: Optional[Path] = typer.Option(None, "--output", "-o")) -> None:
    """Inspect image metadata recursively; skips symlinks and does not alter files."""
    try:
        results = scan_directory(directory, limit)
        for report in results:
            flagged = sum(f.severity in {"HIGH", "MEDIUM"} for f in report.findings)
            console.print(f"{report.filename}: {flagged} flagged field(s)", markup=False)
            for warning in report.warnings:
                console.print(f"Warning: {warning}", markup=False)
        console.print(f"Produced {len(results)} report(s); review warnings for skipped files.")
        if len(results) >= limit:
            console.print("Scan limit may have been reached; additional images may remain.")
        if output is not None:
            export_json({"directory": str(directory), "files": [r.to_dict() for r in results]},
                        output, protected_paths=[directory, *(Path(r.filename) for r in results)])
            console.print(f"Report saved: {output}", markup=False)
    except (OSError, ValueError) as exc:
        failure(exc)


if __name__ == "__main__":
    app()
