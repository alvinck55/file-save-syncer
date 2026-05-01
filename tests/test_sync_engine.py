from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from windrose.config.manager import WindroseConfig, WorldConfig
from windrose.sync.engine import SyncEngine


def _cfg_and_world(save_path: str, save_type: str, file_id: str | None = None):
    world = WorldConfig(name="main", save_path=save_path, save_type=save_type, drive_file_id=file_id)
    cfg = WindroseConfig(
        game_name="Windrose",
        game_exe_path="/game/Windrose.exe",
        drive_folder_id="folder123",
        drive_folder_name="windrose-saves",
        worlds=[world],
    )
    return cfg, world


def test_push_single_file(tmp_path, monkeypatch):
    import windrose.sync.engine as eng
    monkeypatch.setattr(eng, "STATE_FILE", tmp_path / "state.json")

    save = tmp_path / "save.sav"
    save.write_text("data")

    cfg, world = _cfg_and_world(str(save), "file", file_id="existing_id")
    client = MagicMock()
    client.upload_file.return_value = "existing_id"

    SyncEngine(cfg, world, client).push()

    client.upload_file.assert_called_once_with(save, "folder123", "save.sav", "existing_id")
    assert (tmp_path / "state.json").exists()


def test_push_directory(tmp_path, monkeypatch):
    import windrose.sync.engine as eng
    monkeypatch.setattr(eng, "STATE_FILE", tmp_path / "state.json")

    save_dir = tmp_path / "saves"
    save_dir.mkdir()
    (save_dir / "world.dat").write_text("world")

    cfg, world = _cfg_and_world(str(save_dir), "directory", file_id="fid")
    client = MagicMock()
    client.upload_file.return_value = "fid"

    SyncEngine(cfg, world, client).push()

    args = client.upload_file.call_args
    assert args[0][2] == "saves.zip"


def test_pull_skips_when_no_file_id(tmp_path, monkeypatch):
    import windrose.sync.engine as eng
    monkeypatch.setattr(eng, "STATE_FILE", tmp_path / "state.json")

    cfg, world = _cfg_and_world(str(tmp_path / "save.sav"), "file", file_id=None)
    client = MagicMock()

    SyncEngine(cfg, world, client).pull()
    client.download_file.assert_not_called()


def test_pull_single_file(tmp_path, monkeypatch):
    import windrose.sync.engine as eng
    monkeypatch.setattr(eng, "STATE_FILE", tmp_path / "state.json")

    save = tmp_path / "save.sav"
    cfg, world = _cfg_and_world(str(save), "file", file_id="fid")
    client = MagicMock()

    SyncEngine(cfg, world, client).pull()
    client.download_file.assert_called_once_with("fid", save)


def test_push_caches_new_file_id(tmp_path, monkeypatch):
    import windrose.sync.engine as eng
    monkeypatch.setattr(eng, "STATE_FILE", tmp_path / "state.json")

    save = tmp_path / "save.sav"
    save.write_text("data")

    cfg, world = _cfg_and_world(str(save), "file", file_id=None)
    client = MagicMock()
    client.upload_file.return_value = "brand_new_id"

    with patch("windrose.config.manager.ConfigManager.save") as mock_save:
        SyncEngine(cfg, world, client).push()

    assert world.drive_file_id == "brand_new_id"
    mock_save.assert_called_once_with(cfg)


def test_state_written_per_world(tmp_path, monkeypatch):
    import json
    import windrose.sync.engine as eng
    state_file = tmp_path / "state.json"
    monkeypatch.setattr(eng, "STATE_FILE", state_file)

    save = tmp_path / "save.sav"
    save.write_text("data")

    cfg, world = _cfg_and_world(str(save), "file", file_id="fid")
    client = MagicMock()
    client.upload_file.return_value = "fid"

    SyncEngine(cfg, world, client).push()

    state = json.loads(state_file.read_text())
    assert "main" in state
    assert state["main"]["direction"] == "push"
