from __future__ import annotations

from typing import Optional

import typer

from windrose.cli._world_utils import resolve_world
from windrose.config.manager import ConfigManager
from windrose.drive.auth import build_service
from windrose.drive.client import DriveClient
from windrose.sync.engine import SyncEngine


def push(world: Optional[str] = typer.Option(None, "--world", "-w", help="World name to push")) -> None:
    """Manually push the current save to Google Drive."""
    cfg = ConfigManager().load()
    w = resolve_world(cfg, world)
    engine = SyncEngine(cfg, w, DriveClient(build_service()))
    typer.echo(f"Pushing '{w.name}' to Drive...")
    engine.push()
    typer.echo("Done.")
