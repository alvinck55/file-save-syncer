import pytest
from pathlib import Path


@pytest.fixture
def tmp_alvault_dir(tmp_path, monkeypatch):
    """Redirect all ~/.alvault/ paths to a temp directory."""
    import alvault.config.paths as paths
    monkeypatch.setattr(paths, "ALVAULT_DIR", tmp_path)
    monkeypatch.setattr(paths, "CONFIG_FILE", tmp_path / "config.toml")
    monkeypatch.setattr(paths, "TOKEN_FILE", tmp_path / "token.json")
    monkeypatch.setattr(paths, "STATE_FILE", tmp_path / "state.json")
    return tmp_path
