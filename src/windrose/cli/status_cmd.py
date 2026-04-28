from __future__ import annotations

import json
from datetime import datetime, timezone

import typer
from rich.console import Console
from rich.table import Table

from windrose.config.paths import STATE_FILE

console = Console()


def status() -> None:
    """Show last sync time and direction."""
    if not STATE_FILE.exists():
        typer.echo("No sync history found. Run `windrose launch` or `windrose push` first.")
        return

    data = json.loads(STATE_FILE.read_text())
    ts = datetime.fromisoformat(data["last_sync"])
    delta = datetime.now(timezone.utc) - ts
    minutes = int(delta.total_seconds() // 60)
    age = f"{minutes}m ago" if minutes > 0 else "just now"

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_row("Last sync", f"{ts.strftime('%Y-%m-%d %H:%M:%S UTC')} ({age})")
    table.add_row("Direction", data.get("direction", "unknown"))
    if data.get("error"):
        table.add_row("Error", data["error"])

    console.print(table)
