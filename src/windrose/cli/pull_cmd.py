from __future__ import annotations

import typer

from windrose.config.manager import ConfigManager
from windrose.drive.auth import build_service
from windrose.drive.client import DriveClient
from windrose.sync.engine import SyncEngine


def pull() -> None:
    """Manually pull the latest save from Google Drive."""
    cfg = ConfigManager().load()
    engine = SyncEngine(cfg, DriveClient(build_service()))
    typer.echo("Pulling save from Drive...")
    engine.pull()
    typer.echo("Done.")
