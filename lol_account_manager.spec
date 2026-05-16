# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs, collect_submodules

# PyInstaller executes spec files without __file__; resolve from current working directory.
project_root = Path.cwd().resolve()
icon_file = project_root / "assets" / "icon.ico"

hiddenimports = []
hiddenimports += collect_submodules("PyQt5.QtWebEngineWidgets")
hiddenimports += collect_submodules("PyQt5.QtWebEngineCore")
hiddenimports += ["PyQt5.QtWebChannel", "PyQt5.QtNetwork"]

# Include Qt WebEngine resources, translations, and helper process binaries.
datas = []
datas += collect_data_files(
    "PyQt5",
    includes=[
        "Qt5/resources/*",
        "Qt5/translations/*",
        "Qt5/libexec/*",
    ],
)
datas += [
    (str(project_root / "src"), "src"),
    (str(project_root / "app_config.json"), "."),
]
if icon_file.exists():
    datas.append((str(icon_file), "assets"))

binaries = []
binaries += collect_dynamic_libs("PyQt5")

block_cipher = None


a = Analysis(
    [str(project_root / "src" / "main.py")],
    pathex=[str(project_root)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="LoL Account Manager",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    icon=str(icon_file) if icon_file.exists() else None,
)
