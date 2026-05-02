from __future__ import annotations

import os
from pathlib import Path

import typer

from windrose.config.manager import WindroseConfig, WorldConfig


def _discover_save_paths() -> list[Path]:
    local_app_data = os.environ.get("LOCALAPPDATA")
    if not local_app_data:
        return []
    base = Path(local_app_data) / "R5" / "Saved" / "SaveProfiles"
    if not base.is_dir():
        return []
    return sorted(base.glob("*/RocksDB/*/Worlds"))


def prompt_save_path() -> tuple[str, str]:
    """Prompt for the save path, auto-detecting common locations as defaults.

    Returns (save_path, save_type) where save_type is 'file' or 'directory'.
    """
    candidates = _discover_save_paths()

    if len(candidates) == 1:
        save_path = typer.prompt("Full path to save file or save folder", default=str(candidates[0]))
    elif len(candidates) > 1:
        typer.echo("Found multiple save locations:")
        for i, p in enumerate(candidates, 1):
            typer.echo(f"  [{i}] {p}")
        raw = typer.prompt("Enter a number to select, or type a custom path")
        if raw.isdigit() and 1 <= int(raw) <= len(candidates):
            save_path = str(candidates[int(raw) - 1])
        else:
            save_path = raw
    else:
        save_path = typer.prompt("Full path to save file or save folder")

    save_p = Path(save_path)
    if save_p.is_dir():
        return save_path, "directory"
    if save_p.is_file():
        return save_path, "file"
    typer.echo(f"Error: path does not exist: {save_path}", err=True)
    raise typer.Exit(1)


def resolve_world(cfg: WindroseConfig, world_name: str | None) -> WorldConfig:
    """Return the WorldConfig to operate on, prompting when necessary."""
    if world_name:
        world = cfg.get_world(world_name)
        if world is None:
            typer.echo(f"Error: world '{world_name}' not found. Run `windrose list-worlds` to see available worlds.", err=True)
            raise typer.Exit(1)
        return world

    if not cfg.worlds:
        typer.echo("Error: no worlds configured. Run `windrose add-world <name> <path>`.", err=True)
        raise typer.Exit(1)

    if len(cfg.worlds) == 1:
        return cfg.worlds[0]

    names = [w.name for w in cfg.worlds]
    typer.echo("Multiple worlds found: " + ", ".join(names))
    choice = typer.prompt("Which world?", default=names[0])
    world = cfg.get_world(choice)
    if world is None:
        typer.echo(f"Error: world '{choice}' not found.", err=True)
        raise typer.Exit(1)
    return world
