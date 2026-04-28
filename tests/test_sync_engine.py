from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from windrose.config.manager import WindroseConfig
from windrose.sync.engine import SyncEngine


def _cfg(save_path: str, save_type: str, file_id: str | None = None) -> WindroseConfig:
    return WindroseConfig(
        game_name="Windrose",
        game_exe_path="/game/Windrose.exe",
        save_path=save_path,
        save_type=save_type,
        drive_folder_id="folder123",
        drive_folder_name="windrose-saves",
        drive_file_id=file_id,
    )


def test_push_single_file(tmp_path, monkeypatch):
    import windrose.sync.engine as eng
    monkeypatch.setattr(eng, "STATE_FILE", tmp_path / "state.json")

    save = tmp_path / "save.sav"
    save.write_text("data")

    cfg = _cfg(str(save), "file", file_id="existing_id")
    client = MagicMock()
    client.upload_file.return_value = "existing_id"

    engine = SyncEngine(cfg, client)
    engine.push()

    client.upload_file.assert_called_once_with(save, "folder123", "save.sav", "existing_id")
    assert (tmp_path / "state.json").exists()


def test_push_directory(tmp_path, monkeypatch):
    import windrose.sync.engine as eng
    monkeypatch.setattr(eng, "STATE_FILE", tmp_path / "state.json")

    save_dir = tmp_path / "saves"
    save_dir.mkdir()
    (save_dir / "world.dat").write_text("world")

    cfg = _cfg(str(save_dir), "directory", file_id="fid")
    client = MagicMock()
    client.upload_file.return_value = "fid"

    engine = SyncEngine(cfg, client)
    engine.push()

    args = client.upload_file.call_args
    assert args[0][2] == "saves.zip"


def test_pull_skips_when_no_file_id(tmp_path, monkeypatch):
    import windrose.sync.engine as eng
    monkeypatch.setattr(eng, "STATE_FILE", tmp_path / "state.json")

    cfg = _cfg(str(tmp_path / "save.sav"), "file", file_id=None)
    client = MagicMock()

    SyncEngine(cfg, client).pull()
    client.download_file.assert_not_called()


def test_pull_single_file(tmp_path, monkeypatch):
    import windrose.sync.engine as eng
    monkeypatch.setattr(eng, "STATE_FILE", tmp_path / "state.json")

    save = tmp_path / "save.sav"
    cfg = _cfg(str(save), "file", file_id="fid")
    client = MagicMock()

    SyncEngine(cfg, client).pull()
    client.download_file.assert_called_once_with("fid", save)


def test_push_caches_new_file_id(tmp_path, monkeypatch):
    import windrose.sync.engine as eng
    monkeypatch.setattr(eng, "STATE_FILE", tmp_path / "state.json")

    save = tmp_path / "save.sav"
    save.write_text("data")

    cfg = _cfg(str(save), "file", file_id=None)
    client = MagicMock()
    client.upload_file.return_value = "brand_new_id"

    with patch("windrose.config.manager.ConfigManager.save") as mock_save:
        SyncEngine(cfg, client).push()

    assert cfg.drive_file_id == "brand_new_id"
    mock_save.assert_called_once_with(cfg)
