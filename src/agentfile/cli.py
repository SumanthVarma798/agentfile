"""CLI for the Agentfile toolkit."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import click
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

from agentfile import __version__
from agentfile.errors import AgentfileError
from agentfile.loader import load_agentfile
from agentfile.validator import get_schema, validate_file

console = Console()
err_console = Console(stderr=True)


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(__version__, "-v", "--version", prog_name="agent")
def main() -> None:
    """Agentfile: a portable, declarative format for AI agent setups.

    Validate, inspect, and (eventually) run agents from a single manifest.
    """


@main.command()
@click.argument("path", type=click.Path(exists=True, dir_okay=True, file_okay=True, path_type=Path))
@click.option("--strict", is_flag=True, help="Treat warnings as errors.")
@click.option("--quiet", "-q", is_flag=True, help="Only print on failure.")
def validate(path: Path, strict: bool, quiet: bool) -> None:
    """Validate one or more Agentfiles.

    PATH may be a file or a directory. Directories are scanned for agent.yaml,
    Agentfile, agent.yml, and agent.json.
    """
    files = _collect_agentfiles(path)
    if not files:
        err_console.print(f"[red]No Agentfiles found at[/red] {path}")
        sys.exit(2)

    failures = 0
    for f in files:
        result = validate_file(f, strict=strict)

        if result.valid and not result.warnings:
            if not quiet:
                console.print(f"[green]✓[/green] {f}")
            continue

        if result.valid and result.warnings:
            if not quiet:
                console.print(f"[yellow]✓ (with warnings)[/yellow] {f}")
                for w in result.warnings:
                    console.print(f"  [yellow]warning:[/yellow] {w}")
            continue

        # invalid
        failures += 1
        console.print(f"[red]✗[/red] {f}")
        for e in result.errors:
            console.print(f"  [red]error:[/red] {e}")
        for w in result.warnings:
            console.print(f"  [yellow]warning:[/yellow] {w}")

    if failures:
        err_console.print(
            f"\n[red]{failures} of {len(files)} Agentfile(s) failed validation.[/red]"
        )
        sys.exit(1)

    if not quiet:
        console.print(f"\n[green]All {len(files)} Agentfile(s) valid.[/green]")


@main.command()
@click.argument("path", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["yaml", "json", "summary"]),
    default="summary",
    help="Output format.",
)
def show(path: Path, fmt: str) -> None:
    """Pretty-print a parsed Agentfile."""
    try:
        manifest = load_agentfile(path)
    except AgentfileError as e:
        err_console.print(f"[red]error:[/red] {e}")
        sys.exit(1)

    if fmt == "json":
        console.print(Syntax(json.dumps(manifest, indent=2), "json", theme="monokai"))
        return

    if fmt == "yaml":
        console.print(Syntax(yaml.safe_dump(manifest, sort_keys=False), "yaml", theme="monokai"))
        return

    # summary
    _print_summary(manifest, path)


def _print_summary(manifest: dict[str, Any], path: Path) -> None:
    """Print a friendly tabular summary of an Agentfile."""
    meta = manifest.get("metadata", {})
    spec = manifest.get("spec", {})
    model = spec.get("model", {})
    tools = spec.get("tools", []) or []

    header = (
        f"[bold cyan]{meta.get('name', '?')}[/bold cyan] [dim]v{meta.get('version', '?')}[/dim]"
    )
    if desc := meta.get("description"):
        header += f"\n[italic]{desc}[/italic]"
    console.print(Panel(header, title=str(path), border_style="cyan"))

    # Core table
    t = Table(show_header=False, box=None, pad_edge=False)
    t.add_column(style="bold")
    t.add_column()
    t.add_row("apiVersion", manifest.get("apiVersion", "?"))
    t.add_row("kind", manifest.get("kind", "?"))
    t.add_row("model", f"{model.get('provider', '?')}:{model.get('name', '?')}")
    if params := model.get("params"):
        t.add_row("params", ", ".join(f"{k}={v}" for k, v in params.items()))

    sp = spec.get("system_prompt")
    if isinstance(sp, str):
        preview = sp.strip().splitlines()[0][:60]
        t.add_row("system_prompt", f"[inline] {preview}...")
    elif isinstance(sp, dict):
        t.add_row("system_prompt", f"[file] {sp.get('file')}")

    if tools:
        tool_names = ", ".join(tt.get("mcp", "?") for tt in tools)
        t.add_row(f"tools ({len(tools)})", tool_names)
    else:
        t.add_row("tools", "[dim]none[/dim]")

    if mem := spec.get("memory"):
        t.add_row("memory", mem.get("type", "?"))

    if perms := spec.get("permissions"):
        bits = []
        if net := perms.get("network"):
            bits.append(f"network:{net.get('mode')}")
        if fs := perms.get("filesystem"):
            bits.append(f"filesystem:{fs.get('mode')}")
        if bits:
            t.add_row("permissions", ", ".join(bits))

    if env := spec.get("env"):
        if req := env.get("required"):
            t.add_row("env (required)", ", ".join(req))
        if opt := env.get("optional"):
            t.add_row("env (optional)", ", ".join(opt))

    console.print(t)


@main.command()
@click.option("--pretty", is_flag=True, help="Pretty-print with syntax highlighting.")
def schema(pretty: bool) -> None:
    """Print the Agentfile JSON Schema to stdout."""
    schema_dict = get_schema()
    text = json.dumps(schema_dict, indent=2)
    if pretty:
        console.print(Syntax(text, "json", theme="monokai"))
    else:
        click.echo(text)


def _collect_agentfiles(path: Path) -> list[Path]:
    """Resolve a path argument to a list of Agentfile paths."""
    if path.is_file():
        return [path]

    candidates = [
        "agent.yaml",
        "agent.yml",
        "agent.json",
        "Agentfile",
        "Agentfile.yaml",
        "Agentfile.yml",
    ]
    found: list[Path] = []
    # Look directly in the dir
    for c in candidates:
        f = path / c
        if f.is_file():
            found.append(f)
    # And recurse one level into examples-style layouts
    if not found:
        for sub in path.iterdir():
            if sub.is_dir():
                for c in candidates:
                    f = sub / c
                    if f.is_file():
                        found.append(f)
    return found


if __name__ == "__main__":
    main()
