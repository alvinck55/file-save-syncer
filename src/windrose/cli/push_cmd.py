from __future__ import annotations

import typer

from windrose.config.manager import ConfigManager
from windrose.drive.auth import build_service
from windrose.drive.client import DriveClient
from windrose.sync.engine import SyncEngine


def push() -> None:
    """Manually push the current save to Google Drive."""
    cfg = ConfigManager().load()
    engine = SyncEngine(cfg, DriveClient(build_service()))
    typer.echo("Pushing save to Drive...")
    engine.push()
    typer.echo("Done.")
