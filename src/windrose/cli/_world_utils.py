from __future__ import annotations

import os
from pathlib import Path

import typer

from windrose.config.manager import WindroseConfig, WorldConfig


def _discover_mod_dir() -> Path | None:
    candidates: list[Path] = []
    program_files_x86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
    program_files = os.environ.get("ProgramFiles", r"C:\Program Files")
    for steam_root in [Path(program_files_x86) / "Steam", Path(program_files) / "Steam"]:
        lib_paths: list[Path] = [steam_root]
        vdf_path = steam_root / "config" / "libraryfolders.vdf"
        if vdf_path.exists():
            try:
                for line in vdf_path.read_text(encoding="utf-8", errors="ignore").splitlines():
                    stripped = line.strip()
                    if '"path"' in stripped:
                        parts = stripped.split('"')
                        if len(parts) >= 4:
                            lib_paths.append(Path(parts[3]))
            except Exception:
                pass
        for lib in lib_paths:
            candidates.append(lib / "steamapps" / "common" / "Windrose" / "R5" / "Content" / "Paks" / "~mods")
    for c in candidates:
        if c.is_dir():
            return c
    return None


def prompt_mod_config() -> tuple[str | None, str, str]:
    """Prompt for mod tracking setup. Returns (mod_dir, mod_sync, mod_pull_strategy)."""
    if not typer.confirm("\nTrack and sync mods for this world?", default=False):
        return None, "off", "merge"
    detected = _discover_mod_dir()
    if detected:
        raw = typer.prompt("Mod directory", default=str(detected))
    else:
        typer.echo(r"Could not auto-detect. Expected: <game_dir>\R5\Content\Paks\~mods")
        raw = typer.prompt("Mod directory path")
    mod_dir_path = Path(raw)
    if not mod_dir_path.is_dir():
        typer.echo(f"Warning: directory not found: {raw}")
    typer.echo("\nMod sync mode:")
    typer.echo("  [1] manifest_only  — record which mods are needed (players install from Nexus)")
    typer.echo("  [2] upload_download — upload .pak files to Drive (larger but fully automatic)")
    mode_raw = typer.prompt("Mode", default="1")
    mod_sync = "upload_download" if mode_raw.strip() == "2" else "manifest_only"
    return str(mod_dir_path), mod_sync, "merge"


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
