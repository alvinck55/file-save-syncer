import pytest
from pathlib import Path


@pytest.fixture
def tmp_windrose_dir(tmp_path, monkeypatch):
    """Redirect all ~/.windrose/ paths to a temp directory."""
    import windrose.config.paths as paths
    monkeypatch.setattr(paths, "WINDROSE_DIR", tmp_path)
    monkeypatch.setattr(paths, "CONFIG_FILE", tmp_path / "config.toml")
    monkeypatch.setattr(paths, "TOKEN_FILE", tmp_path / "token.json")
    monkeypatch.setattr(paths, "CLIENT_SECRET", tmp_path / "client_secret.json")
    monkeypatch.setattr(paths, "STATE_FILE", tmp_path / "state.json")
    return tmp_path
