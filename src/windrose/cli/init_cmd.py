from __future__ import annotations

from pathlib import Path

import typer

from windrose.cli._world_utils import prompt_game_selection, prompt_world_configs
from windrose.config.manager import ConfigManager, WindroseConfig
from windrose.drive.auth import run_oauth_flow, build_service
from windrose.drive.client import DriveClient


def init() -> None:
    """Interactive setup: configure game, save path, and sign in with Google."""
    typer.echo("alvault init\n")

    if ConfigManager().exists():
        typer.echo("Warning: alvault is already configured.")
        typer.echo("Running init will create a new Drive folder and disconnect you from your current group.")
        typer.echo("To take a turn hosting an existing world, just run `alvault launch` instead.")
        if not typer.confirm("Continue and replace current config?", default=False):
            raise typer.Exit(0)
        typer.echo("")

    game = prompt_game_selection()

    worlds = prompt_world_configs(game_key=game.key, supports_mods=game.supports_mods)

    folder_name = typer.prompt("Google Drive folder name", default="alvault-saves")

    typer.echo("\nOpening browser for Google sign-in...")
    run_oauth_flow()
    typer.echo("Authentication successful.")

    typer.echo("Creating Drive folder...")
    client = DriveClient(build_service())
    folder_id = client.create_folder(folder_name)

    cfg = WindroseConfig(
        game_name=game.name,
        steam_app_id=game.steam_app_id,
        game_process_name=game.process_name,
        supports_mods=game.supports_mods,
        drive_folder_id=folder_id,
        drive_folder_name=folder_name,
        worlds=worlds,
    )
    ConfigManager().save(cfg)

    typer.echo(f"\nConfig saved. Drive folder '{folder_name}' ready.")
    typer.echo(f"Share your folder ID with other players: {folder_id}")
    if game.key == "enshrouded":
        typer.echo("\nWorld IDs (share with players who haven't Steam-joined your worlds yet):")
        for w in worlds:
            typer.echo(f"  {w.name}: {Path(w.save_path).name}")
    typer.echo("Run `alvault launch` to start playing.")
    typer.echo("Add more worlds with `alvault add-world <name> <path>`.")
