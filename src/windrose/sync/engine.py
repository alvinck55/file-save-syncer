from __future__ import annotations

import json
import os
import socket
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from windrose.config.manager import ConfigManager, WindroseConfig, WorldConfig
from windrose.config.paths import STATE_FILE
from windrose.drive.client import DriveClient


class WorldLockedError(Exception):
    def __init__(self, locked_by: str, locked_at: str) -> None:
        self.locked_by = locked_by
        self.locked_at = locked_at
        super().__init__(f"World is checked out by {locked_by}")


class SyncEngine:
    def __init__(self, cfg: WindroseConfig, world: WorldConfig, client: DriveClient) -> None:
        self._cfg = cfg
        self._world = world
        self._client = client

    def push(self) -> None:
        save_path = Path(self._world.save_path)
        tmp_zip: Path | None = None

        if self._world.save_type == "directory":
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
                self._world.drive_file_id,
            )
        finally:
            if tmp_zip:
                tmp_zip.unlink(missing_ok=True)

        if self._world.drive_file_id != file_id:
            self._world.drive_file_id = file_id
            ConfigManager().save(self._cfg)

        lock_filename = save_path.name + ".lock"
        lock_file_id = _get_lock_file_id(self._world.name) or self._client.find_file_in_folder(lock_filename, self._cfg.drive_folder_id)
        if lock_file_id:
            try:
                self._client.delete_file(lock_file_id)
            except Exception:
                pass
            _update_lock_file_id(self._world.name, None)

        _write_state(self._world.name, direction="push")

    def pull(self) -> None:
        save_path = Path(self._world.save_path)
        lock_filename = save_path.name + ".lock"

        existing_lock_id = self._client.find_file_in_folder(lock_filename, self._cfg.drive_folder_id)
        if existing_lock_id:
            try:
                info = json.loads(self._client.download_bytes(existing_lock_id))
                locked_by = info.get("locked_by", "unknown")
                locked_at = info.get("locked_at", "unknown")
            except Exception:
                locked_by = "unknown"
                locked_at = "unknown"
            if locked_by != socket.gethostname():
                locked_path = _locked_path(save_path)
                if save_path.exists() and not locked_path.exists():
                    try:
                        save_path.rename(locked_path)
                    except Exception:
                        pass
                raise WorldLockedError(locked_by, locked_at)

        if not self._world.drive_file_id:
            drive_filename = save_path.name + ".zip" if self._world.save_type == "directory" else save_path.name
            found_id = self._client.find_file_in_folder(drive_filename, self._cfg.drive_folder_id)
            if not found_id:
                return
            self._world.drive_file_id = found_id
            ConfigManager().save(self._cfg)

        locked_path = _locked_path(save_path)
        if locked_path.exists():
            import shutil
            shutil.rmtree(locked_path) if locked_path.is_dir() else locked_path.unlink()

        if self._world.save_type == "directory":
            with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tf:
                tmp_zip = Path(tf.name)
            try:
                self._client.download_file(self._world.drive_file_id, tmp_zip)
                self._unzip_to_directory(tmp_zip, save_path)
            finally:
                tmp_zip.unlink(missing_ok=True)
        else:
            self._client.download_file(self._world.drive_file_id, save_path)

        lock_data = json.dumps({
            "locked_by": socket.gethostname(),
            "locked_at": datetime.now(timezone.utc).isoformat(),
        }).encode()
        lock_file_id = self._client.upload_bytes(self._cfg.drive_folder_id, lock_filename, lock_data)
        _update_lock_file_id(self._world.name, lock_file_id)

        _write_state(self._world.name, direction="pull")

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


def _locked_path(save_path: Path) -> Path:
    return Path(str(save_path) + ".windrose-locked")


def _load_state() -> dict:
    if not STATE_FILE.exists():
        return {}
    try:
        state = json.loads(STATE_FILE.read_text())
        if "last_sync" in state:
            return {"main": state}
        return state
    except Exception:
        return {}


def _save_state(state: dict) -> None:
    tmp = STATE_FILE.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(state, indent=2))
    os.replace(tmp, STATE_FILE)


def _write_state(world_name: str, direction: str, error: str | None = None) -> None:
    state = _load_state()
    existing = state.get(world_name, {})
    state[world_name] = {
        "last_sync": datetime.now(timezone.utc).isoformat(),
        "direction": direction,
        "error": error,
        "lock_file_id": existing.get("lock_file_id"),
    }
    _save_state(state)


def _get_lock_file_id(world_name: str) -> str | None:
    return _load_state().get(world_name, {}).get("lock_file_id")


def _update_lock_file_id(world_name: str, lock_file_id: str | None) -> None:
    state = _load_state()
    state.setdefault(world_name, {})["lock_file_id"] = lock_file_id
    _save_state(state)
