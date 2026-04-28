import pytest
from windrose.config.manager import ConfigManager, WindroseConfig


def _sample_cfg() -> WindroseConfig:
    return WindroseConfig(
        game_name="Windrose",
        game_exe_path="/path/to/Windrose.exe",
        save_path="/path/to/saves",
        save_type="directory",
        drive_folder_id="folder123",
        drive_folder_name="windrose-saves",
        drive_file_id=None,
    )


def test_round_trip(tmp_windrose_dir, monkeypatch):
    import windrose.config.manager as mgr_mod
    monkeypatch.setattr(mgr_mod, "CONFIG_FILE", tmp_windrose_dir / "config.toml")

    mgr = ConfigManager()
    cfg = _sample_cfg()
    mgr.save(cfg)
    loaded = mgr.load()

    assert loaded.game_name == cfg.game_name
    assert loaded.game_exe_path == cfg.game_exe_path
    assert loaded.save_path == cfg.save_path
    assert loaded.save_type == cfg.save_type
    assert loaded.drive_folder_id == cfg.drive_folder_id
    assert loaded.drive_file_id is None


def test_round_trip_with_file_id(tmp_windrose_dir, monkeypatch):
    import windrose.config.manager as mgr_mod
    monkeypatch.setattr(mgr_mod, "CONFIG_FILE", tmp_windrose_dir / "config.toml")

    mgr = ConfigManager()
    cfg = _sample_cfg()
    cfg.drive_file_id = "abc123"
    mgr.save(cfg)
    loaded = mgr.load()

    assert loaded.drive_file_id == "abc123"


def test_missing_config_raises(tmp_windrose_dir, monkeypatch):
    import windrose.config.manager as mgr_mod
    monkeypatch.setattr(mgr_mod, "CONFIG_FILE", tmp_windrose_dir / "config.toml")

    with pytest.raises(FileNotFoundError, match="windrose init"):
        ConfigManager().load()


def test_exists(tmp_windrose_dir, monkeypatch):
    import windrose.config.manager as mgr_mod
    monkeypatch.setattr(mgr_mod, "CONFIG_FILE", tmp_windrose_dir / "config.toml")

    mgr = ConfigManager()
    assert not mgr.exists()
    mgr.save(_sample_cfg())
    assert mgr.exists()
