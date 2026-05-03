from __future__ import annotations

import threading
from typing import Optional

import typer

from windrose.cli._world_utils import resolve_world
from windrose.config.manager import ConfigManager
from windrose.drive.auth import build_service
from windrose.drive.client import DriveClient
from windrose.launcher.game import launch_game, wait_for_process
from windrose.sync.engine import SyncEngine, WorldLockedError
from windrose.tray.icon import TrayIcon


def launch(world: Optional[str] = typer.Option(None, "--world", "-w", help="World name to launch")) -> None:
    """Pull latest save, launch the game, sync back to Drive when done."""
    cfg = ConfigManager().load()
    w = resolve_world(cfg, world)
    client = DriveClient(build_service())
    engine = SyncEngine(cfg, w, client)

    typer.echo(f"Pulling latest save for '{w.name}' from Drive...")
    try:
        engine.pull()
        typer.echo("Save pulled.")
    except WorldLockedError as e:
        typer.echo(f"Cannot launch: '{w.name}' is checked out by {e.locked_by}.")
        typer.echo("Wait for them to push, then run `windrose launch` again.")
        typer.echo("Or ask them to host the game and join their server directly.")
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"Warning: could not pull save ({e}). Launching anyway.")

    typer.echo(f"Launching {cfg.game_name} via Steam...")
    launch_game(cfg.steam_app_id)

    tray = TrayIcon(engine, w.name)
    tray_thread = threading.Thread(target=tray.run, daemon=True)
    tray_thread.start()

    typer.echo(f"Waiting for {cfg.game_name} to start...", nl=False)
    found = wait_for_process(
        cfg.game_process_name,
        on_poll=lambda: typer.echo(".", nl=False),
        on_found=lambda: typer.echo(f"\n{cfg.game_name} is running. Waiting for it to close..."),
    )

    tray.stop()
    tray_thread.join(timeout=3)

    if not found:
        typer.echo(f"Warning: {cfg.game_name} process was not detected. Pushing save anyway...")
    else:
        typer.echo("Game closed. Pushing save to Drive...")
    try:
        engine.push()
        typer.echo("Save pushed. Done.")
    except Exception as e:
        typer.echo(f"Error: could not push save: {e}", err=True)
        raise typer.Exit(1)
