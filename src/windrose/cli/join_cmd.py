from __future__ import annotations

from pathlib import Path

import typer

from windrose.cli._world_utils import prompt_save_path
from windrose.config.manager import ConfigManager, WindroseConfig, WorldConfig
from windrose.drive.auth import build_service, run_oauth_flow
from windrose.drive.client import DriveClient


def join(folder_id: str = typer.Argument(..., help="Google Drive folder ID shared by the host")) -> None:
    """Join an existing shared world. Use the folder ID provided by the host."""
    typer.echo("windrose join\n")

    game_name = typer.prompt("Game name", default="Windrose")

    exe_path = typer.prompt("Full path to Windrose.exe (or game executable)")
    if not Path(exe_path).is_file():
        typer.echo(f"Error: file not found: {exe_path}", err=True)
        raise typer.Exit(1)

    world_name = typer.prompt("Name for your first world", default="main")

    save_path, save_type = prompt_save_path()

    typer.echo("\nOpening browser for Google sign-in...")
    run_oauth_flow()
    typer.echo("Authentication successful.")

    typer.echo("Verifying Drive folder access...")
    client = DriveClient(build_service())
    try:
        meta = client.get_folder_metadata(folder_id)
        folder_name = meta.get("name", "unknown")
        typer.echo(f"Found folder: '{folder_name}'")
    except Exception as e:
        typer.echo(f"Error: could not access folder '{folder_id}': {e}", err=True)
        typer.echo("Make sure the host has shared the folder with your Google account, or that the folder ID is correct.")
        raise typer.Exit(1)

    cfg = WindroseConfig(
        game_name=game_name,
        game_exe_path=exe_path,
        drive_folder_id=folder_id,
        drive_folder_name=folder_name,
        worlds=[WorldConfig(name=world_name, save_path=save_path, save_type=save_type)],
    )
    ConfigManager().save(cfg)

    typer.echo(f"\nJoined '{folder_name}'. Run `windrose launch` to start playing.")
    typer.echo("Add more worlds with `windrose add-world <name> <path>`.")
