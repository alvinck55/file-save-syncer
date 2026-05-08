from pathlib import Path

ALVAULT_DIR = Path.home() / ".alvault"
CONFIG_FILE = ALVAULT_DIR / "config.toml"
TOKEN_FILE = ALVAULT_DIR / "token.json"
STATE_FILE = ALVAULT_DIR / "state.json"
GAME_FILE = ALVAULT_DIR / "game.toml"

ALVAULT_DIR.mkdir(parents=True, exist_ok=True)
