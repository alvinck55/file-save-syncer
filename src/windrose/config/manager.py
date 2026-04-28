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

from windrose.config.paths import CONFIG_FILE


@dataclass
class WindroseConfig:
    game_name: str
    game_exe_path: str
    save_path: str
    save_type: str          # "file" | "directory"
    drive_folder_id: str
    drive_folder_name: str
    drive_file_id: str | None = field(default=None)


class ConfigManager:
    def load(self) -> WindroseConfig:
        if not CONFIG_FILE.exists():
            raise FileNotFoundError(
                f"No config found at {CONFIG_FILE}. Run `windrose init` first."
            )
        with open(CONFIG_FILE, "rb") as f:
            data = tomllib.load(f)
        game = data["game"]
        drive = data["drive"]
        return WindroseConfig(
            game_name=game["name"],
            game_exe_path=game["exe_path"],
            save_path=game["save_path"],
            save_type=game["save_type"],
            drive_folder_id=drive["folder_id"],
            drive_folder_name=drive["folder_name"],
            drive_file_id=drive.get("file_id"),
        )

    def save(self, cfg: WindroseConfig) -> None:
        data = {
            "game": {
                "name": cfg.game_name,
                "exe_path": cfg.game_exe_path,
                "save_path": cfg.save_path,
                "save_type": cfg.save_type,
            },
            "drive": {
                "folder_id": cfg.drive_folder_id,
                "folder_name": cfg.drive_folder_name,
            },
        }
        if cfg.drive_file_id is not None:
            data["drive"]["file_id"] = cfg.drive_file_id

        tmp = CONFIG_FILE.with_suffix(".toml.tmp")
        tmp.write_bytes(tomli_w.dumps(data).encode())
        os.replace(tmp, CONFIG_FILE)

    def exists(self) -> bool:
        return CONFIG_FILE.exists()
