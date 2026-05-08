import pytest
from alvault.config.manager import ConfigManager, AlvaultConfig, WorldConfig


def _sample_cfg() -> AlvaultConfig:
    return AlvaultConfig(
        game_name="Windrose",
        game_exe_path="/path/to/Windrose.exe",
        drive_folder_id="folder123",
        drive_folder_name="windrose-saves",
        worlds=[
            WorldConfig(name="main", save_path="/path/to/saves", save_type="directory"),
        ],
    )


def test_round_trip(tmp_alvault_dir, monkeypatch):
    import alvault.config.manager as mgr_mod
    monkeypatch.setattr(mgr_mod, "CONFIG_FILE", tmp_alvault_dir / "config.toml")

    mgr = ConfigManager()
    cfg = _sample_cfg()
    mgr.save(cfg)
    loaded = mgr.load()

    assert loaded.game_name == cfg.game_name
    assert loaded.game_exe_path == cfg.game_exe_path
    assert loaded.drive_folder_id == cfg.drive_folder_id
    assert len(loaded.worlds) == 1
    assert loaded.worlds[0].name == "main"
    assert loaded.worlds[0].save_path == "/path/to/saves"
    assert loaded.worlds[0].save_type == "directory"
    assert loaded.worlds[0].drive_file_id is None


def test_round_trip_with_file_id(tmp_alvault_dir, monkeypatch):
    import alvault.config.manager as mgr_mod
    monkeypatch.setattr(mgr_mod, "CONFIG_FILE", tmp_alvault_dir / "config.toml")

    mgr = ConfigManager()
    cfg = _sample_cfg()
    cfg.worlds[0].drive_file_id = "abc123"
    mgr.save(cfg)
    loaded = mgr.load()

    assert loaded.worlds[0].drive_file_id == "abc123"


def test_multiple_worlds_round_trip(tmp_alvault_dir, monkeypatch):
    import alvault.config.manager as mgr_mod
    monkeypatch.setattr(mgr_mod, "CONFIG_FILE", tmp_alvault_dir / "config.toml")

    mgr = ConfigManager()
    cfg = AlvaultConfig(
        game_name="Windrose",
        game_exe_path="/path/to/Windrose.exe",
        drive_folder_id="folder123",
        drive_folder_name="windrose-saves",
        worlds=[
            WorldConfig(name="main", save_path="/saves/main", save_type="directory", drive_file_id="id1"),
            WorldConfig(name="modded", save_path="/saves/modded", save_type="directory"),
        ],
    )
    mgr.save(cfg)
    loaded = mgr.load()

    assert len(loaded.worlds) == 2
    assert loaded.get_world("main").drive_file_id == "id1"
    assert loaded.get_world("modded").drive_file_id is None


def test_migrate_old_format(tmp_alvault_dir, monkeypatch):
    import alvault.config.manager as mgr_mod
    config_file = tmp_alvault_dir / "config.toml"
    monkeypatch.setattr(mgr_mod, "CONFIG_FILE", config_file)

    old_toml = (
        '[game]\nname = "Windrose"\nexe_path = "/game/Windrose.exe"\n'
        'save_path = "/saves"\nsave_type = "directory"\n\n'
        '[drive]\nfolder_id = "f1"\nfolder_name = "windrose-saves"\nfile_id = "fid"\n'
    )
    config_file.write_text(old_toml)

    loaded = ConfigManager().load()
    assert len(loaded.worlds) == 1
    assert loaded.worlds[0].name == "main"
    assert loaded.worlds[0].save_path == "/saves"
    assert loaded.worlds[0].drive_file_id == "fid"


def test_missing_config_raises(tmp_alvault_dir, monkeypatch):
    import alvault.config.manager as mgr_mod
    monkeypatch.setattr(mgr_mod, "CONFIG_FILE", tmp_alvault_dir / "config.toml")

    with pytest.raises(FileNotFoundError, match="alvault init"):
        ConfigManager().load()


def test_exists(tmp_alvault_dir, monkeypatch):
    import alvault.config.manager as mgr_mod
    monkeypatch.setattr(mgr_mod, "CONFIG_FILE", tmp_alvault_dir / "config.toml")

    mgr = ConfigManager()
    assert not mgr.exists()
    mgr.save(_sample_cfg())
    assert mgr.exists()


def test_get_world(tmp_alvault_dir):
    cfg = _sample_cfg()
    assert cfg.get_world("main") is cfg.worlds[0]
    assert cfg.get_world("missing") is None


def test_default_world_single():
    cfg = _sample_cfg()
    assert cfg.default_world() is cfg.worlds[0]


def test_default_world_empty():
    cfg = AlvaultConfig(
        game_name="Windrose",
        game_exe_path="/path/to/Windrose.exe",
        drive_folder_id="f1",
        drive_folder_name="windrose-saves",
    )
    assert cfg.default_world() is None
