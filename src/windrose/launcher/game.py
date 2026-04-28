from __future__ import annotations

import subprocess


def launch_game(exe_path: str) -> subprocess.Popen:
    return subprocess.Popen(exe_path)
