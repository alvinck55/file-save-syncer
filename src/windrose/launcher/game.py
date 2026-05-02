from __future__ import annotations

import ctypes
import os
import subprocess
import time


def launch_game(steam_app_id: str) -> None:
    os.startfile(f"steam://rungameid/{steam_app_id}")


def wait_for_process(process_name: str, start_timeout: int = 60) -> None:
    pid = None
    for _ in range(start_timeout):
        pid = _get_pid(process_name)
        if pid:
            break
        time.sleep(1)

    if not pid:
        return

    kernel32 = ctypes.windll.kernel32
    handle = kernel32.OpenProcess(0x00100000, False, pid)  # SYNCHRONIZE
    if handle:
        kernel32.WaitForSingleObject(handle, 0xFFFFFFFF)   # INFINITE
        kernel32.CloseHandle(handle)


def _get_pid(process_name: str) -> int | None:
    result = subprocess.run(
        ["tasklist", "/FI", f"IMAGENAME eq {process_name}", "/FO", "CSV", "/NH"],
        capture_output=True,
        text=True,
    )
    for line in result.stdout.strip().splitlines():
        parts = line.strip('"').split('","')
        if len(parts) >= 2 and parts[0].lower() == process_name.lower():
            return int(parts[1])
    return None
