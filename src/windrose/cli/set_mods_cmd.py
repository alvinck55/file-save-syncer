from __future__ import annotations

from typing import Optional

import typer

from windrose.cli._world_utils import prompt_mod_config, resolve_world
from windrose.config.manager import ConfigManager


def set_mods(
    world: Optional[str] = typer.Option(None, "--world", "-w", help="World name to update"),
) -> None:
    """Configure mod sync for an existing world."""
    mgr = ConfigManager()
    cfg = mgr.load()
    w = resolve_world(cfg, world)

    mod_dir, mod_sync, mod_pull_strategy = prompt_mod_config()
    w.mod_dir = mod_dir
    w.mod_sync = mod_sync
    w.mod_pull_strategy = mod_pull_strategy
    mgr.save(cfg)

    if mod_dir:
        typer.echo(f"Mod sync configured for world '{w.name}' ({mod_sync}).")
        typer.echo("Run `windrose-save-sync push` to upload the mod manifest now.")
    else:
        typer.echo(f"Mod sync disabled for world '{w.name}'.")
