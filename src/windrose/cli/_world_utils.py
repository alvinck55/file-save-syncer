from __future__ import annotations

import typer

from windrose.config.manager import WindroseConfig, WorldConfig


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
