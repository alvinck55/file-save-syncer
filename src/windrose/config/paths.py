from pathlib import Path

WINDROSE_DIR = Path.home() / ".windrose"
CONFIG_FILE = WINDROSE_DIR / "config.toml"
TOKEN_FILE = WINDROSE_DIR / "token.json"
STATE_FILE = WINDROSE_DIR / "state.json"

WINDROSE_DIR.mkdir(parents=True, exist_ok=True)
