from __future__ import annotations

from typing import Optional

import typer

from alvault.cli._world_utils import resolve_world
from alvault.config.manager import ConfigManager
from alvault.drive.auth import build_service
from alvault.drive.client import DriveClient
from alvault.sync.engine import SyncEngine, WorldLockedError


def pull(world: Optional[str] = typer.Option(None, "--world", "-w", help="World name to pull")) -> None:
    """Manually pull the latest save from Google Drive."""
    cfg = ConfigManager().load()
    w = resolve_world(cfg, world)
    engine = SyncEngine(cfg, w, DriveClient(build_service()))

    typer.echo(f"Pulling '{w.name}' from Drive...")
    try:
        engine.pull()
    except WorldLockedError as e:
        typer.echo(f"\n'{w.name}' is checked out by {e.locked_by} (since {e.locked_at}).")
        typer.echo("Your local save has been hidden so the game cannot load it.")
        typer.echo("Wait for them to finish and push, then run `alvault pull` to get the latest save.")
        typer.echo("Or ask them to host the game and join their server directly.")
        raise typer.Exit(1)
    typer.echo("Done.")
