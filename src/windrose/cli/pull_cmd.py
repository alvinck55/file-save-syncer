from __future__ import annotations

from typing import Optional

import typer

from windrose.cli._world_utils import resolve_world
from windrose.config.manager import ConfigManager
from windrose.drive.auth import build_service
from windrose.drive.client import DriveClient
from windrose.sync.engine import SyncEngine


def pull(world: Optional[str] = typer.Option(None, "--world", "-w", help="World name to pull")) -> None:
    """Manually pull the latest save from Google Drive."""
    cfg = ConfigManager().load()
    w = resolve_world(cfg, world)
    engine = SyncEngine(cfg, w, DriveClient(build_service()))
    typer.echo(f"Pulling '{w.name}' from Drive...")
    engine.pull()
    typer.echo("Done.")
