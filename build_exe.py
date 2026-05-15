"""Build and package the application as standalone executable"""
import PyInstaller.__main__
import os
from pathlib import Path

# Get the project root directory
root_dir = Path(__file__).parent
spec_file = root_dir / 'lol_account_manager.spec'
os.chdir(root_dir)

icon_file = root_dir / 'assets' / 'icon.ico'

# Build from spec so Qt WebEngine runtime assets are always bundled.
args = [
    str(spec_file),
    '--noconfirm',
    '--clean',
]

if not spec_file.exists():
    raise FileNotFoundError(
        f"Missing PyInstaller spec file: {spec_file}. "
        "The spec is required to bundle Qt WebEngine runtime files."
    )

PyInstaller.__main__.run(args)

print("\nBuild complete! Executable is in the 'dist' folder.")
