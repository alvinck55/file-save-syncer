from __future__ import annotations

import hashlib
import os
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path


_MOD_EXTENSIONS = ("*.pak", "*.ucas", "*.utoc")


def _iter_mod_files(mod_dir: Path):
    """Yield all mod files (.pak, .ucas, .utoc) sorted by name."""
    files = set()
    for pattern in _MOD_EXTENSIONS:
        files.update(mod_dir.glob(pattern))
    return sorted(files, key=lambda f: f.name)


def scan_mod_dir(mod_dir: Path) -> list[dict]:
    """Return sorted list of {filename, sha256} for all mod files in mod_dir."""
    if not mod_dir.is_dir():
        return []
    mods = []
    for f in _iter_mod_files(mod_dir):
        sha256 = hashlib.sha256(f.read_bytes()).hexdigest()
        mods.append({"filename": f.name, "sha256": sha256})
    return mods


def build_manifest(mod_dir: Path) -> dict:
    return {
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "mods": scan_mod_dir(mod_dir),
    }


def zip_mod_dir(mod_dir: Path) -> Path:
    """Zip all mod files (.pak, .ucas, .utoc) in mod_dir into a temp file and return its path."""
    fd, tmp = tempfile.mkstemp(suffix=".zip")
    os.close(fd)
    tmp_path = Path(tmp)
    with zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in _iter_mod_files(mod_dir):
            zf.write(f, f.name)
    return tmp_path


def install_mods(zip_path: Path, mod_dir: Path, strategy: str) -> list[str]:
    """Extract mods from zip into mod_dir. Returns list of installed filenames."""
    mod_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as zf:
        names = zf.namelist()
        if strategy == "replace":
            for f in _iter_mod_files(mod_dir):
                f.unlink()
        zf.extractall(mod_dir)
    return names


def diff_mod_lists(local: list[dict], remote: list[dict]) -> dict:
    """Compare local and remote mod lists. Returns {missing, extra, changed}."""
    local_map = {m["filename"]: m["sha256"] for m in local}
    remote_map = {m["filename"]: m["sha256"] for m in remote}
    missing = [f for f in remote_map if f not in local_map]
    extra = [f for f in local_map if f not in remote_map]
    changed = [f for f in remote_map if f in local_map and local_map[f] != remote_map[f]]
    return {"missing": missing, "extra": extra, "changed": changed}
