from __future__ import annotations

from pathlib import Path

import typer

from windrose.config.manager import ConfigManager, WindroseConfig, WorldConfig
from windrose.drive.auth import run_oauth_flow, build_service
from windrose.drive.client import DriveClient


def init() -> None:
    """Interactive setup: configure game path, save path, and sign in with Google."""
    typer.echo("windrose init\n")

    game_name = typer.prompt("Game name", default="Windrose")

    exe_path = typer.prompt("Full path to Windrose.exe (or game executable)")
    if not Path(exe_path).is_file():
        typer.echo(f"Error: file not found: {exe_path}", err=True)
        raise typer.Exit(1)

    world_name = typer.prompt("Name for your first world", default="main")

    save_path = typer.prompt("Full path to save file or save folder")
    save_p = Path(save_path)
    if save_p.is_dir():
        save_type = "directory"
    elif save_p.is_file():
        save_type = "file"
    else:
        typer.echo(f"Error: path does not exist: {save_path}", err=True)
        raise typer.Exit(1)

    folder_name = typer.prompt("Google Drive folder name", default="windrose-saves")

    typer.echo("\nOpening browser for Google sign-in...")
    run_oauth_flow()
    typer.echo("Authentication successful.")

    typer.echo("Creating Drive folder...")
    client = DriveClient(build_service())
    folder_id = client.find_or_create_folder(folder_name)

    cfg = WindroseConfig(
        game_name=game_name,
        game_exe_path=exe_path,
        drive_folder_id=folder_id,
        drive_folder_name=folder_name,
        worlds=[WorldConfig(name=world_name, save_path=save_path, save_type=save_type)],
    )
    ConfigManager().save(cfg)

    typer.echo(f"\nConfig saved. Drive folder '{folder_name}' ready.")
    typer.echo(f"Share your folder ID with other players: {folder_id}")
    typer.echo("Run `windrose launch` to start playing.")
    typer.echo("Add more worlds with `windrose add-world <name> <path>`.")
