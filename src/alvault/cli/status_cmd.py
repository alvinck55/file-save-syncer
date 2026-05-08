from __future__ import annotations

import json
from datetime import datetime, timezone

import typer
from rich.console import Console
from rich.table import Table

from alvault.config.paths import STATE_FILE

console = Console()


def status() -> None:
    """Show last sync time and direction for each world."""
    if not STATE_FILE.exists():
        typer.echo("No sync history found. Run `alvault launch` or `alvault push` first.")
        return

    data = json.loads(STATE_FILE.read_text())

    # Migrate old flat format
    if "last_sync" in data:
        data = {"main": data}

    table = Table(show_header=True)
    table.add_column("World")
    table.add_column("Last sync")
    table.add_column("Direction")
    table.add_column("Error")

    for world_name, entry in data.items():
        ts = datetime.fromisoformat(entry["last_sync"])
        delta = datetime.now(timezone.utc) - ts
        minutes = int(delta.total_seconds() // 60)
        age = f"{minutes}m ago" if minutes > 0 else "just now"
        table.add_row(
            world_name,
            f"{ts.strftime('%Y-%m-%d %H:%M UTC')} ({age})",
            entry.get("direction", "unknown"),
            entry.get("error") or "",
        )

    console.print(table)
