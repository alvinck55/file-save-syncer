from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib  # type: ignore[no-redef]

import tomli_w

from alvault.config.paths import CONFIG_FILE, GAME_FILE


_GAME_REGISTRY: dict[str, dict] = {
    "windrose": {
        "name": "Windrose",
        "steam_app_id": "3041230",
        "process_name": "Windrose.exe",
        "supports_mods": True,
    },
    "enshrouded": {
        "name": "Enshrouded",
        "steam_app_id": "1203620",
        "process_name": "enshrouded.exe",
        "supports_mods": False,
    },
}

_GAME_DEFAULTS = _GAME_REGISTRY["windrose"]


@dataclass
class GameDefaults:
    key: str
    name: str
    steam_app_id: str
    process_name: str
    supports_mods: bool


class GameDefaultsManager:
    def load(self) -> GameDefaults:
        if not GAME_FILE.exists():
            self._write_defaults()
        with open(GAME_FILE, "rb") as f:
            data = tomllib.load(f)["game"]
        return GameDefaults(
            key="windrose",
            name=data["name"],
            steam_app_id=data["steam_app_id"],
            process_name=data["process_name"],
            supports_mods=data.get("supports_mods", True),
        )

    def _write_defaults(self) -> None:
        GAME_FILE.write_bytes(tomli_w.dumps({"game": _GAME_DEFAULTS}).encode())


@dataclass
class WorldConfig:
    name: str
    save_path: str
    save_type: str          # "file" | "directory"
    drive_file_id: str | None = field(default=None)
    mod_dir: str | None = field(default=None)
    mod_sync: str = field(default="off")           # "off" | "manifest_only" | "upload_download"
    mod_pull_strategy: str = field(default="merge") # "merge" | "replace"


@dataclass
class AlvaultConfig:
    game_name: str
    steam_app_id: str
    game_process_name: str
    drive_folder_id: str
    drive_folder_name: str
    supports_mods: bool = field(default=True)
    worlds: list[WorldConfig] = field(default_factory=list)

    def get_world(self, name: str) -> WorldConfig | None:
        for w in self.worlds:
            if w.name == name:
                return w
        return None

    def default_world(self) -> WorldConfig | None:
        return self.worlds[0] if self.worlds else None


class ConfigManager:
    def load(self) -> AlvaultConfig:
        if not CONFIG_FILE.exists():
            raise FileNotFoundError(
                f"No config found at {CONFIG_FILE}. Run `alvault init` first."
            )
        with open(CONFIG_FILE, "rb") as f:
            data = tomllib.load(f)
        game = data["game"]
        drive = data["drive"]

        if "worlds" in data:
            worlds = [
                WorldConfig(
                    name=w["name"],
                    save_path=w["save_path"],
                    save_type=w["save_type"],
                    drive_file_id=w.get("drive_file_id"),
                    mod_dir=w.get("mod_dir"),
                    mod_sync=w.get("mod_sync", "off"),
                    mod_pull_strategy=w.get("mod_pull_strategy", "merge"),
                )
                for w in data["worlds"]
            ]
        else:
            # Migrate old single-world format
            worlds = [
                WorldConfig(
                    name="main",
                    save_path=game["save_path"],
                    save_type=game["save_type"],
                    drive_file_id=drive.get("file_id"),
                )
            ]

        return AlvaultConfig(
            game_name=game["name"],
            steam_app_id=game.get("steam_app_id", _GAME_DEFAULTS["steam_app_id"]),
            game_process_name=game.get("process_name", _GAME_DEFAULTS["process_name"]),
            supports_mods=game.get("supports_mods", True),
            drive_folder_id=drive["folder_id"],
            drive_folder_name=drive["folder_name"],
            worlds=worlds,
        )

    def save(self, cfg: AlvaultConfig) -> None:
        worlds_data = []
        for w in cfg.worlds:
            entry: dict = {
                "name": w.name,
                "save_path": w.save_path,
                "save_type": w.save_type,
            }
            if w.drive_file_id is not None:
                entry["drive_file_id"] = w.drive_file_id
            if w.mod_dir is not None:
                entry["mod_dir"] = w.mod_dir
                entry["mod_sync"] = w.mod_sync
                entry["mod_pull_strategy"] = w.mod_pull_strategy
            worlds_data.append(entry)

        data = {
            "game": {
                "name": cfg.game_name,
                "steam_app_id": cfg.steam_app_id,
                "process_name": cfg.game_process_name,
                "supports_mods": cfg.supports_mods,
            },
            "drive": {
                "folder_id": cfg.drive_folder_id,
                "folder_name": cfg.drive_folder_name,
            },
            "worlds": worlds_data,
        }

        tmp = CONFIG_FILE.with_suffix(".toml.tmp")
        tmp.write_bytes(tomli_w.dumps(data).encode())
        os.replace(tmp, CONFIG_FILE)

    def exists(self) -> bool:
        return CONFIG_FILE.exists()
