from __future__ import annotations

import os
import re
from datetime import datetime
from pathlib import Path

import typer

from windrose.config.manager import _GAME_REGISTRY, GameDefaults, WindroseConfig, WorldConfig


def prompt_game_selection() -> GameDefaults:
    games = list(_GAME_REGISTRY.items())
    typer.echo("Select game:")
    for i, (_, g) in enumerate(games, 1):
        typer.echo(f"  [{i}] {g['name']}")
    raw = typer.prompt("Game", default="1")
    idx = (int(raw) - 1) if raw.isdigit() and 1 <= int(raw) <= len(games) else 0
    key, g = games[idx]
    return GameDefaults(key=key, **g)


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


def _discover_enshrouded_save_paths() -> list[Path]:
    program_files_x86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
    program_files = os.environ.get("ProgramFiles", r"C:\Program Files")
    results: list[Path] = []
    seen: set[Path] = set()
    for steam_root in [Path(program_files_x86) / "Steam", Path(program_files) / "Steam"]:
        userdata = steam_root / "userdata"
        if not userdata.is_dir():
            continue
        for user_dir in sorted(userdata.iterdir()):
            if not user_dir.is_dir():
                continue
            remote = user_dir / "1203620" / "remote"
            if not remote.is_dir():
                continue
            for f in sorted(remote.iterdir()):
                if re.fullmatch(r"[0-9a-f]{8}", f.name) and f.is_file():
                    if f not in seen:
                        results.append(f)
                        seen.add(f)
                elif re.fullmatch(r"[0-9a-f]{8}_info", f.name) and f.is_file():
                    base = f.with_name(f.name[: -len("_info")])
                    if base not in seen:
                        results.append(base)
                        seen.add(base)
    return results


def _read_enshrouded_world_name(world_path: Path) -> str | None:
    info_path = world_path.with_name(world_path.name + "_info")
    if not info_path.is_file():
        return None
    try:
        import zstandard as zstd  # type: ignore[import]
        data = info_path.read_bytes()
        offset = data.find(b"\x28\xb5\x2f\xfd")
        if offset < 0:
            return None
        out = zstd.ZstdDecompressor().decompress(data[offset:], max_output_size=64 * 1024)
        idx = out.find(b"\x04\x00name")
        if idx < 0:
            return None
        val_len = int.from_bytes(out[idx + 6 : idx + 8], "little")
        return out[idx + 8 : idx + 8 + val_len].decode("utf-8")
    except Exception:
        return None


def _find_enshrouded_remote_dir() -> Path | None:
    program_files_x86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
    program_files = os.environ.get("ProgramFiles", r"C:\Program Files")
    for steam_root in [Path(program_files_x86) / "Steam", Path(program_files) / "Steam"]:
        userdata = steam_root / "userdata"
        if not userdata.is_dir():
            continue
        for user_dir in sorted(userdata.iterdir()):
            if not user_dir.is_dir():
                continue
            remote = user_dir / "1203620" / "remote"
            if remote.is_dir():
                return remote
    return None


def _discover_save_paths(game_key: str = "windrose") -> list[Path]:
    if game_key == "enshrouded":
        return _discover_enshrouded_save_paths()
    local_app_data = os.environ.get("LOCALAPPDATA")
    if not local_app_data:
        return []
    base = Path(local_app_data) / "R5" / "Saved" / "SaveProfiles"
    if not base.is_dir():
        return []
    return sorted(base.glob("*/RocksDB/*/Worlds"))


def prompt_save_path(game_key: str = "windrose") -> tuple[str, str]:
    """Prompt for the save path, auto-detecting common locations as defaults.

    Returns (save_path, save_type) where save_type is 'file' or 'directory'.
    """
    candidates = _discover_save_paths(game_key)

    if len(candidates) == 1:
        save_path = typer.prompt("Full path to save file or save folder", default=str(candidates[0]))
    elif len(candidates) > 1:
        typer.echo("Found multiple save locations:")
        for i, p in enumerate(candidates, 1):
            try:
                mtime = datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
                typer.echo(f"  [{i}] {p}  (modified {mtime})")
            except OSError:
                typer.echo(f"  [{i}] {p}")
        raw = typer.prompt("Enter a number to select, or type a custom path")
        if raw.isdigit() and 1 <= int(raw) <= len(candidates):
            save_path = str(candidates[int(raw) - 1])
        else:
            save_path = raw
    else:
        if game_key == "enshrouded":
            remote_dir = _find_enshrouded_remote_dir()
            if remote_dir:
                typer.echo("No local Enshrouded worlds detected. Enter the world ID shared by the host.")
                hex_id = typer.prompt("World ID (8-character hex, e.g. 3ad85aea)")
                save_path = str(remote_dir / hex_id.strip().lower())
            else:
                save_path = typer.prompt("Full path to Enshrouded save file")
        else:
            save_path = typer.prompt("Full path to save file or save folder")

    save_p = Path(save_path)
    if save_p.is_dir():
        return save_path, "directory"
    if save_p.is_file():
        return save_path, "file"
    if save_p.parent.is_dir():
        return save_path, "file"
    typer.echo(f"Error: path does not exist: {save_path}", err=True)
    raise typer.Exit(1)


def prompt_world_configs(game_key: str, supports_mods: bool) -> list[WorldConfig]:
    """Prompt to configure one or more worlds, auto-detecting all save paths."""
    candidates = _discover_save_paths(game_key)

    if len(candidates) <= 1:
        detected_name = (_read_enshrouded_world_name(candidates[0]) if candidates else None)
        if detected_name:
            typer.echo(f"  World: {detected_name}")
            name = detected_name
        else:
            name = typer.prompt("Name for your first world", default="main")
        save_path, save_type = prompt_save_path(game_key)
        mod_dir, mod_sync, mod_pull = prompt_mod_config() if supports_mods else (None, "off", "merge")
        return [WorldConfig(name=name, save_path=save_path, save_type=save_type,
                            mod_dir=mod_dir, mod_sync=mod_sync, mod_pull_strategy=mod_pull)]

    typer.echo(f"\nFound {len(candidates)} worlds:")
    configs: list[WorldConfig] = []
    for p in candidates:
        try:
            mtime = datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
            label = f"(modified {mtime})"
        except OSError:
            label = "(not yet created)"
        detected_name = _read_enshrouded_world_name(p)
        if detected_name:
            typer.echo(f"  {detected_name}  [{p.name}  {label}]")
            name = detected_name
        else:
            name = typer.prompt(f"  Name for {p.name} {label}", default=p.name)
            if not name.strip():
                continue
        save_type = "directory" if p.is_dir() else "file"
        mod_dir, mod_sync, mod_pull = prompt_mod_config() if supports_mods else (None, "off", "merge")
        configs.append(WorldConfig(name=name.strip(), save_path=str(p), save_type=save_type,
                                   mod_dir=mod_dir, mod_sync=mod_sync, mod_pull_strategy=mod_pull))

    if not configs:
        typer.echo("No worlds configured.", err=True)
        raise typer.Exit(1)

    return configs


def resolve_world(cfg: WindroseConfig, world_name: str | None) -> WorldConfig:
    """Return the WorldConfig to operate on, prompting when necessary."""
    if world_name:
        world = cfg.get_world(world_name)
        if world is None:
            typer.echo(f"Error: world '{world_name}' not found. Run `alvault list-worlds` to see available worlds.", err=True)
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
