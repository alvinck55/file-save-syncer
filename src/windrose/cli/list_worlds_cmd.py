from __future__ import annotations

from rich.console import Console
from rich.table import Table

from windrose.config.manager import ConfigManager

console = Console()


def list_worlds() -> None:
    """List all configured worlds."""
    cfg = ConfigManager().load()

    if not cfg.worlds:
        console.print("No worlds configured. Run `windrose add-world <name> <path>`.")
        return

    table = Table(show_header=True)
    table.add_column("Name")
    table.add_column("Type")
    table.add_column("Save path")
    table.add_column("Drive file ID")

    for w in cfg.worlds:
        table.add_row(
            w.name,
            w.save_type,
            w.save_path,
            w.drive_file_id or "(not yet synced)",
        )

    console.print(table)
