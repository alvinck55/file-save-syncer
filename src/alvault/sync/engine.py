from __future__ import annotations

import json
import os
import socket
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from alvault.config.manager import ConfigManager, AlvaultConfig, WorldConfig
from alvault.config.paths import STATE_FILE
from alvault.drive.client import DriveClient


class WorldLockedError(Exception):
    def __init__(self, locked_by: str, locked_at: str) -> None:
        self.locked_by = locked_by
        self.locked_at = locked_at
        super().__init__(f"World is checked out by {locked_by}")


class SyncEngine:
    def __init__(self, cfg: AlvaultConfig, world: WorldConfig, client: DriveClient) -> None:
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

        if self._world.mod_dir:
            mod_dir = Path(self._world.mod_dir)
            if mod_dir.is_dir():
                self._push_mods(mod_dir)

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
            base_name = self._world.drive_filename if self._world.drive_filename else save_path.name
            drive_filename = base_name + ".zip" if self._world.save_type == "directory" else base_name
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

        if self._world.mod_dir:
            self._pull_mods(Path(self._world.mod_dir))

    def _push_mods(self, mod_dir: Path) -> None:
        from alvault.mods.manager import build_manifest, diff_mod_lists, zip_mod_dir
        world_name = self._world.name
        manifest = build_manifest(mod_dir)
        mod_count = len(manifest["mods"])

        # Tier 1: local cache — free, no network call
        cached = _get_last_pushed_mods(world_name)
        if cached is not None:
            diff = diff_mod_lists(manifest["mods"], cached)
            if not diff["missing"] and not diff["extra"] and not diff["changed"]:
                print(f"Mods unchanged — skipping upload ({mod_count} mod(s)).")
                return

        # Tier 2: cache miss — download Drive manifest once to avoid a redundant upload
        existing_manifest_id = _get_mod_manifest_file_id(world_name)
        if existing_manifest_id:
            try:
                remote_manifest = json.loads(self._client.download_bytes(existing_manifest_id))
                diff = diff_mod_lists(manifest["mods"], remote_manifest.get("mods", []))
                if not diff["missing"] and not diff["extra"] and not diff["changed"]:
                    _set_last_pushed_mods(world_name, manifest["mods"])
                    print(f"Mods unchanged — skipping upload ({mod_count} mod(s)).")
                    return
            except Exception:
                pass

        print(f"Uploading mod manifest ({mod_count} mod(s))...")
        manifest_data = json.dumps(manifest, indent=2).encode()
        manifest_id = self._client.upload_bytes(
            self._cfg.drive_folder_id,
            f"{world_name}-mods.json",
            manifest_data,
            existing_manifest_id,
        )
        zip_id = _get_mod_zip_file_id(world_name)
        if self._world.mod_sync == "upload_download":
            print("Uploading mod files to Drive...")
            tmp_zip = zip_mod_dir(mod_dir)
            try:
                zip_id = self._client.upload_file(
                    tmp_zip,
                    self._cfg.drive_folder_id,
                    f"{world_name}-mods.zip",
                    zip_id,
                )
            finally:
                tmp_zip.unlink(missing_ok=True)
        _update_mod_file_ids(world_name, manifest_id, zip_id)
        _set_last_pushed_mods(world_name, manifest["mods"])

    def _pull_mods(self, mod_dir: Path) -> None:
        from alvault.mods.manager import scan_mod_dir, diff_mod_lists, install_mods
        world_name = self._world.name
        print("Checking mods...")
        manifest_file_id = _get_mod_manifest_file_id(world_name)
        if not manifest_file_id:
            manifest_file_id = self._client.find_file_in_folder(
                f"{world_name}-mods.json", self._cfg.drive_folder_id
            )
            if not manifest_file_id:
                print("No mod manifest on Drive — skipping mod check.")
                return
            _update_mod_file_ids(world_name, manifest_file_id, None)
        try:
            remote_manifest = json.loads(self._client.download_bytes(manifest_file_id))
        except Exception:
            print("Could not read mod manifest from Drive — skipping mod check.")
            return
        remote_mods = remote_manifest.get("mods", [])
        local_mods = scan_mod_dir(mod_dir) if mod_dir.is_dir() else []
        diff = diff_mod_lists(local_mods, remote_mods)
        has_mismatch = bool(diff["missing"] or diff["changed"])
        if not has_mismatch and not diff["extra"]:
            print(f"Mods OK — {len(local_mods)} mod(s) installed.")
        else:
            print("Mod mismatch detected:")
            if diff["missing"]:
                print("  Missing locally:  " + ", ".join(diff["missing"]))
            if diff["extra"]:
                print("  Extra locally:    " + ", ".join(diff["extra"]))
            if diff["changed"]:
                print("  Changed:          " + ", ".join(diff["changed"]))
        if self._world.mod_sync == "upload_download" and has_mismatch:
            zip_file_id = _get_mod_zip_file_id(world_name)
            if not zip_file_id:
                zip_file_id = self._client.find_file_in_folder(
                    f"{world_name}-mods.zip", self._cfg.drive_folder_id
                )
                if zip_file_id:
                    _update_mod_file_ids(world_name, manifest_file_id, zip_file_id)
            if zip_file_id:
                answer = input("Install mods from Drive? [Y/n] ").strip().lower()
                if answer not in ("", "y", "yes"):
                    print("Skipping mod install.")
                else:
                    print("Downloading and installing mods from Drive...")
                    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tf:
                        tmp_zip = Path(tf.name)
                    try:
                        self._client.download_file(zip_file_id, tmp_zip)
                        installed = install_mods(tmp_zip, mod_dir, self._world.mod_pull_strategy)
                        print(f"Mods installed ({len(installed)} file(s)).")
                        if self._world.mod_pull_strategy == "replace":
                            print("Warning: mods replaced — other worlds using different mods may be affected.")
                    finally:
                        tmp_zip.unlink(missing_ok=True)
        elif self._world.mod_sync == "manifest_only" and has_mismatch:
            print("Install missing mods from Nexus Mods before loading this save.")

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
    return Path(str(save_path) + ".alvault-locked")


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
        "mod_manifest_file_id": existing.get("mod_manifest_file_id"),
        "mod_zip_file_id": existing.get("mod_zip_file_id"),
        "last_pushed_mods": existing.get("last_pushed_mods"),
    }
    _save_state(state)


def _get_lock_file_id(world_name: str) -> str | None:
    return _load_state().get(world_name, {}).get("lock_file_id")


def _update_lock_file_id(world_name: str, lock_file_id: str | None) -> None:
    state = _load_state()
    state.setdefault(world_name, {})["lock_file_id"] = lock_file_id
    _save_state(state)


def _get_mod_manifest_file_id(world_name: str) -> str | None:
    return _load_state().get(world_name, {}).get("mod_manifest_file_id")


def _get_mod_zip_file_id(world_name: str) -> str | None:
    return _load_state().get(world_name, {}).get("mod_zip_file_id")


def _update_mod_file_ids(world_name: str, manifest_file_id: str | None, zip_file_id: str | None) -> None:
    state = _load_state()
    world_state = state.setdefault(world_name, {})
    if manifest_file_id is not None:
        world_state["mod_manifest_file_id"] = manifest_file_id
    if zip_file_id is not None:
        world_state["mod_zip_file_id"] = zip_file_id
    _save_state(state)


def _get_last_pushed_mods(world_name: str) -> list[dict] | None:
    return _load_state().get(world_name, {}).get("last_pushed_mods")


def _set_last_pushed_mods(world_name: str, mods: list[dict]) -> None:
    state = _load_state()
    state.setdefault(world_name, {})["last_pushed_mods"] = mods
    _save_state(state)
