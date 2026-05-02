from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path

import pystray
from PIL import Image, ImageDraw

from windrose.config.paths import STATE_FILE
from windrose.sync.engine import SyncEngine, WorldLockedError


def _make_image() -> Image.Image:
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([4, 4, size - 4, size - 4], fill=(70, 130, 180, 255))
    return img


def _last_sync_label(world_name: str) -> str:
    if not STATE_FILE.exists():
        return "Last sync: never"
    try:
        data = json.loads(STATE_FILE.read_text())
        # Support both old flat format and new per-world format
        entry = data.get(world_name) or (data if "last_sync" in data else None)
        if not entry:
            return "Last sync: never"
        ts = datetime.fromisoformat(entry["last_sync"])
        delta = datetime.now(timezone.utc) - ts
        minutes = int(delta.total_seconds() // 60)
        direction = entry.get("direction", "")
        return f"Last sync: {minutes}m ago ({direction})" if minutes > 0 else "Last sync: just now"
    except Exception:
        return "Last sync: unknown"


class TrayIcon:
    def __init__(self, engine: SyncEngine, world_name: str) -> None:
        self._engine = engine
        self._world_name = world_name
        self._icon: pystray.Icon | None = None
        self._timer: threading.Timer | None = None

    def run(self) -> None:
        self._icon = pystray.Icon(
            "windrose",
            _make_image(),
            "windrose",
            menu=self._make_menu(),
        )
        self._schedule_update()
        self._icon.run()

    def stop(self) -> None:
        if self._timer:
            self._timer.cancel()
        if self._icon:
            self._icon.stop()

    def _make_menu(self) -> pystray.Menu:
        return pystray.Menu(
            pystray.MenuItem(_last_sync_label(self._world_name), None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Push save now", self._on_push),
            pystray.MenuItem("Pull save now", self._on_pull),
        )

    def _on_push(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        threading.Thread(target=self._do_push, daemon=True).start()

    def _on_pull(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        import tkinter
        import tkinter.messagebox
        root = tkinter.Tk()
        root.withdraw()
        confirmed = tkinter.messagebox.askyesno(
            "Pull save",
            "Pulling mid-game will overwrite your local save.\n\nContinue?",
        )
        root.destroy()
        if confirmed:
            threading.Thread(target=self._do_pull, daemon=True).start()

    def _do_push(self) -> None:
        try:
            self._engine.push()
            self._refresh_menu()
        except Exception as e:
            self._notify(f"Push failed: {e}")

    def _do_pull(self) -> None:
        try:
            self._engine.pull()
            self._refresh_menu()
        except WorldLockedError as e:
            self._notify(f"Pull blocked: {e.locked_by} has this world checked out. Your local save is hidden. Wait for them to push, then use 'windrose pull'.")
        except Exception as e:
            self._notify(f"Pull failed: {e}")

    def _refresh_menu(self) -> None:
        if self._icon:
            self._icon.menu = self._make_menu()
            self._icon.update_menu()

    def _schedule_update(self) -> None:
        self._timer = threading.Timer(30.0, self._tick)
        self._timer.daemon = True
        self._timer.start()

    def _tick(self) -> None:
        self._refresh_menu()
        self._schedule_update()

    def _notify(self, message: str) -> None:
        if self._icon:
            self._icon.notify(message, "windrose")
