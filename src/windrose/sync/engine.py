from __future__ import annotations

import json
import os
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from windrose.config.manager import ConfigManager, WindroseConfig
from windrose.config.paths import STATE_FILE
from windrose.drive.client import DriveClient


class SyncEngine:
    def __init__(self, cfg: WindroseConfig, client: DriveClient) -> None:
        self._cfg = cfg
        self._client = client

    def push(self) -> None:
        save_path = Path(self._cfg.save_path)
        tmp_zip: Path | None = None

        if self._cfg.save_type == "directory":
            tmp_zip = self._zip_directory(save_path)
            upload_path = tmp_zip
            drive_filename = save_path.name + ".zip"
        else:
            upload_path = save_path
            drive_filename = save_path.name

        try:
            file_id = self._client.upload_file(
                upload_path,
                self._cfg.drive_folder_id,
                drive_filename,
                self._cfg.drive_file_id,
            )
        finally:
            if tmp_zip:
                tmp_zip.unlink(missing_ok=True)

        if self._cfg.drive_file_id != file_id:
            self._cfg.drive_file_id = file_id
            ConfigManager().save(self._cfg)

        _write_state(direction="push")

    def pull(self) -> None:
        if not self._cfg.drive_file_id:
            return

        save_path = Path(self._cfg.save_path)

        if self._cfg.save_type == "directory":
            with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tf:
                tmp_zip = Path(tf.name)
            try:
                self._client.download_file(self._cfg.drive_file_id, tmp_zip)
                self._unzip_to_directory(tmp_zip, save_path)
            finally:
                tmp_zip.unlink(missing_ok=True)
        else:
            self._client.download_file(self._cfg.drive_file_id, save_path)

        _write_state(direction="pull")

    def _zip_directory(self, dir_path: Path) -> Path:
        fd, tmp = tempfile.mkstemp(suffix=".zip")
        os.close(fd)
        tmp_path = Path(tmp)
        with zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for file in dir_path.rglob("*"):
                if file.is_file():
                    zf.write(file, file.relative_to(dir_path))
        return tmp_path

    def _unzip_to_directory(self, zip_path: Path, target_dir: Path) -> None:
        target_dir.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(target_dir)


def _write_state(direction: str, error: str | None = None) -> None:
    state = {
        "last_sync": datetime.now(timezone.utc).isoformat(),
        "direction": direction,
        "error": error,
    }
    tmp = STATE_FILE.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(state, indent=2))
    os.replace(tmp, STATE_FILE)
