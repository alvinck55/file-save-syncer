from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from windrose.cli._world_utils import resolve_world
from windrose.config.manager import ConfigManager


def set_save(
    path: str = typer.Argument(..., help="Path to save file or save folder"),
    world: Optional[str] = typer.Option(None, "--world", "-w", help="World name to update"),
) -> None:
    """Update the save path for a world without re-running full setup."""
    save_p = Path(path)
    if save_p.is_dir():
        save_type = "directory"
    elif save_p.is_file():
        save_type = "file"
    else:
        typer.echo(f"Error: path does not exist: {path}", err=True)
        raise typer.Exit(1)

    mgr = ConfigManager()
    cfg = mgr.load()
    w = resolve_world(cfg, world)

    w.save_path = str(save_p)
    w.save_type = save_type
    w.drive_file_id = None  # force a fresh upload on the next push
    mgr.save(cfg)

    kind = "folder" if save_type == "directory" else "file"
    typer.echo(f"World '{w.name}' save path updated to {kind}: {save_p}")
    typer.echo("Run `windrose-save-sync push` to upload it now, or `windrose-save-sync launch` to start playing.")
