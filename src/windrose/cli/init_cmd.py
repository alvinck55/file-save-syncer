from __future__ import annotations

import shutil
from pathlib import Path

import typer

from windrose.config.manager import ConfigManager, WindroseConfig
from windrose.config.paths import CLIENT_SECRET
from windrose.drive.auth import run_oauth_flow, build_service
from windrose.drive.client import DriveClient


def init() -> None:
    """Interactive setup: configure save path, GCP credentials, and Google OAuth."""
    typer.echo("windrose init\n")

    game_name = typer.prompt("Game name", default="Windrose")

    exe_path = typer.prompt("Full path to Windrose.exe (or game executable)")
    if not Path(exe_path).is_file():
        typer.echo(f"Error: file not found: {exe_path}", err=True)
        raise typer.Exit(1)

    save_path = typer.prompt("Full path to save file or save folder")
    save_p = Path(save_path)
    if save_p.is_dir():
        save_type = "directory"
    elif save_p.is_file():
        save_type = "file"
    else:
        typer.echo(f"Error: path does not exist: {save_path}", err=True)
        raise typer.Exit(1)

    secret_src = typer.prompt(
        "Path to client_secret.json (from GCP Console)",
        default=str(CLIENT_SECRET),
    )
    secret_src_p = Path(secret_src)
    if not secret_src_p.is_file():
        typer.echo(f"Error: file not found: {secret_src}", err=True)
        raise typer.Exit(1)
    if secret_src_p.resolve() != CLIENT_SECRET.resolve():
        shutil.copy2(secret_src_p, CLIENT_SECRET)
        typer.echo(f"Copied client_secret.json to {CLIENT_SECRET}")

    folder_name = typer.prompt("Google Drive folder name", default="windrose-saves")

    typer.echo("\nOpening browser for Google authentication...")
    creds = run_oauth_flow()
    typer.echo("Authentication successful.")

    typer.echo("Creating Drive folder...")
    service = build_service()
    client = DriveClient(service)
    folder_id = client.find_or_create_folder(folder_name)

    cfg = WindroseConfig(
        game_name=game_name,
        game_exe_path=exe_path,
        save_path=save_path,
        save_type=save_type,
        drive_folder_id=folder_id,
        drive_folder_name=folder_name,
    )
    ConfigManager().save(cfg)

    typer.echo(f"\nConfig saved. Drive folder '{folder_name}' ready.")
    typer.echo("Run `windrose launch` to start playing.")
