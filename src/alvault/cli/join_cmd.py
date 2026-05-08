from __future__ import annotations

import typer

from alvault.cli._world_utils import prompt_game_selection, prompt_world_configs
from alvault.config.manager import ConfigManager, AlvaultConfig
from alvault.drive.auth import build_service, run_oauth_flow
from alvault.drive.client import DriveClient


def join(folder_id: str = typer.Argument(..., help="Google Drive folder ID shared by the host")) -> None:
    """Join an existing shared world. Use the folder ID provided by the host."""
    typer.echo("alvault join\n")

    game = prompt_game_selection()

    worlds = prompt_world_configs(game_key=game.key, supports_mods=game.supports_mods)

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

    cfg = AlvaultConfig(
        game_name=game.name,
        steam_app_id=game.steam_app_id,
        game_process_name=game.process_name,
        supports_mods=game.supports_mods,
        drive_folder_id=folder_id,
        drive_folder_name=folder_name,
        worlds=worlds,
    )
    ConfigManager().save(cfg)

    typer.echo(f"\nJoined '{folder_name}'. Run `alvault launch --world <name>` to start playing.")
    typer.echo("Add more worlds with `alvault add-world <name> <path>`.")
