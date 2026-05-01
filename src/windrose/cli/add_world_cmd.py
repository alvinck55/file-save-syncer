from __future__ import annotations

from pathlib import Path

import typer

from windrose.config.manager import ConfigManager, WorldConfig


def add_world(
    name: str = typer.Argument(..., help="Name for the world (e.g. 'main', 'modded')"),
    path: str = typer.Argument(..., help="Path to save file or save folder for this world"),
) -> None:
    """Add a new world with its own save path and Drive file."""
    mgr = ConfigManager()
    cfg = mgr.load()

    if cfg.get_world(name) is not None:
        typer.echo(f"Error: world '{name}' already exists. Choose a different name.", err=True)
        raise typer.Exit(1)

    save_p = Path(path)
    if save_p.is_dir():
        save_type = "directory"
    elif save_p.is_file():
        save_type = "file"
    else:
        typer.echo(f"Error: path does not exist: {path}", err=True)
        raise typer.Exit(1)

    cfg.worlds.append(WorldConfig(name=name, save_path=str(save_p), save_type=save_type))
    mgr.save(cfg)

    kind = "folder" if save_type == "directory" else "file"
    typer.echo(f"World '{name}' added ({kind}: {save_p}).")
    typer.echo(f"Run `windrose push --world {name}` to upload it.")
