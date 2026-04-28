from __future__ import annotations

import threading

import typer

from windrose.config.manager import ConfigManager
from windrose.drive.auth import build_service
from windrose.drive.client import DriveClient
from windrose.launcher.game import launch_game
from windrose.sync.engine import SyncEngine
from windrose.tray.icon import TrayIcon


def launch() -> None:
    """Pull latest save, launch the game, sync back to Drive when done."""
    cfg = ConfigManager().load()
    client = DriveClient(build_service())
    engine = SyncEngine(cfg, client)

    typer.echo("Pulling latest save from Drive...")
    try:
        engine.pull()
        typer.echo("Save pulled.")
    except Exception as e:
        typer.echo(f"Warning: could not pull save ({e}). Launching anyway.")

    typer.echo(f"Launching {cfg.game_name}...")
    proc = launch_game(cfg.game_exe_path)

    tray = TrayIcon(engine)
    tray_thread = threading.Thread(target=tray.run, daemon=True)
    tray_thread.start()

    proc.wait()

    tray.stop()
    tray_thread.join(timeout=3)

    typer.echo("Game closed. Pushing save to Drive...")
    try:
        engine.push()
        typer.echo("Save pushed. Done.")
    except Exception as e:
        typer.echo(f"Error: could not push save: {e}", err=True)
        raise typer.Exit(1)
