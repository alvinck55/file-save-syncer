from __future__ import annotations

import typer

from windrose.cli._world_utils import prompt_game_selection, prompt_mod_config, prompt_save_path
from windrose.config.manager import ConfigManager, WindroseConfig, WorldConfig
from windrose.drive.auth import run_oauth_flow, build_service
from windrose.drive.client import DriveClient


def init() -> None:
    """Interactive setup: configure game, save path, and sign in with Google."""
    typer.echo("alvault init\n")

    game = prompt_game_selection()

    world_name = typer.prompt("Name for your first world", default="main")

    save_path, save_type = prompt_save_path(game_key=game.key)
    if game.supports_mods:
        mod_dir, mod_sync, mod_pull_strategy = prompt_mod_config()
    else:
        mod_dir, mod_sync, mod_pull_strategy = None, "off", "merge"

    folder_name = typer.prompt("Google Drive folder name", default="alvault-saves")

    typer.echo("\nOpening browser for Google sign-in...")
    run_oauth_flow()
    typer.echo("Authentication successful.")

    typer.echo("Creating Drive folder...")
    client = DriveClient(build_service())
    folder_id = client.find_or_create_folder(folder_name)

    cfg = WindroseConfig(
        game_name=game.name,
        steam_app_id=game.steam_app_id,
        game_process_name=game.process_name,
        supports_mods=game.supports_mods,
        drive_folder_id=folder_id,
        drive_folder_name=folder_name,
        worlds=[WorldConfig(
            name=world_name,
            save_path=save_path,
            save_type=save_type,
            mod_dir=mod_dir,
            mod_sync=mod_sync,
            mod_pull_strategy=mod_pull_strategy,
        )],
    )
    ConfigManager().save(cfg)

    typer.echo(f"\nConfig saved. Drive folder '{folder_name}' ready.")
    typer.echo(f"Share your folder ID with other players: {folder_id}")
    typer.echo("Run `alvault launch` to start playing.")
    typer.echo("Add more worlds with `alvault add-world <name> <path>`.")
