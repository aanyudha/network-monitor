# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path


repo_root = Path(SPECPATH).parent.parent.resolve()
icon_path = repo_root / "assets" / "icon.ico"


a = Analysis(
    ["app/main.py"],
    pathex=[str(repo_root)],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="HeisenbergNetworkMonitor",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=str(icon_path) if icon_path.exists() else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="HeisenbergNetworkMonitor",
)
