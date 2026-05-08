# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files

# Collects client_secret.json from windrose/data/
datas = collect_data_files("windrose", include_py_files=False)

a = Analysis(
    ["windrose_entry.py"],
    pathex=["src"],
    binaries=[],
    datas=datas,
    hiddenimports=[
        # CLI subcommands — imported dynamically via __init__.py side-effects
        "windrose.cli.init_cmd",
        "windrose.cli.join_cmd",
        "windrose.cli.invite_cmd",
        "windrose.cli.launch_cmd",
        "windrose.cli.push_cmd",
        "windrose.cli.pull_cmd",
        "windrose.cli.status_cmd",
        "windrose.cli.set_save_cmd",
        "windrose.cli.set_mods_cmd",
        "windrose.cli.add_world_cmd",
        "windrose.cli.list_worlds_cmd",
        # pystray Windows backend
        "pystray._win32",
        # Google auth/Drive — discovery uses dynamic imports
        "google.auth.transport.requests",
        "google.oauth2.credentials",
        "google_auth_oauthlib.flow",
        "googleapiclient.discovery",
        "googleapiclient._helpers",
        "googleapiclient.http",
        # tomli for Python < 3.11
        "tomli",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="alvault",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
