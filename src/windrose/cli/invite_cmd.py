from __future__ import annotations

import typer

from windrose.config.manager import ConfigManager
from windrose.drive.auth import build_service
from windrose.drive.client import DriveClient


def invite(email: str = typer.Argument(..., help="Gmail address of the player to invite")) -> None:
    """Invite a player to the shared world by granting them Drive folder access."""
    cfg = ConfigManager().load()
    client = DriveClient(build_service())

    try:
        client.invite_user(cfg.drive_folder_id, email)
    except Exception as e:
        typer.echo(f"Error: could not invite {email}: {e}", err=True)
        raise typer.Exit(1)

    typer.echo(f"Invited {email} — they'll receive an email from Google.")
    typer.echo(f"Tell them to run: windrose join {cfg.drive_folder_id}")
