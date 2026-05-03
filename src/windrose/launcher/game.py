from __future__ import annotations

import ctypes
import os
import subprocess
import time


def launch_game(steam_app_id: str) -> None:
    os.startfile(f"steam://rungameid/{steam_app_id}")


def wait_for_process(process_name: str, start_timeout: int = 60, on_found=None, on_poll=None) -> bool:
    """Poll until the process appears, then wait via Win32 until it exits. Returns True if found."""
    for _ in range(start_timeout):
        if _get_pid(process_name):
            break
        if on_poll:
            on_poll()
        time.sleep(1)
    else:
        return False

    if on_found:
        on_found()

    kernel32 = ctypes.windll.kernel32
    while True:
        pid = _get_pid(process_name)
        if not pid:
            break
        handle = kernel32.OpenProcess(0x00100000, False, pid)  # SYNCHRONIZE
        if handle:
            kernel32.WaitForSingleObject(handle, 5000)          # 5s timeout, then re-poll
            kernel32.CloseHandle(handle)
        else:
            time.sleep(2)

    return True


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
