"""Build and package the application as standalone executable"""
import PyInstaller.__main__
import os
from pathlib import Path

# Get the project root directory
root_dir = Path(__file__).parent
os.chdir(root_dir)

icon_file = root_dir / 'assets' / 'icon.ico'

# Prefer a repo-root spec file, but support fallback locations used by older setups.
candidate_specs = [
    root_dir / 'lol_account_manager.spec',
    root_dir / 'build' / 'lol_account_manager.spec',
]
spec_file = next((path for path in candidate_specs if path.exists()), None)

# Build from spec so Qt WebEngine runtime assets are always bundled.
if spec_file is None:
    checked = ', '.join(str(path) for path in candidate_specs)
    raise FileNotFoundError(
        "Missing PyInstaller spec file. Checked: "
        f"{checked}. The spec is required to bundle Qt WebEngine runtime files."
    )

args = [
    str(spec_file),
    '--noconfirm',
    '--clean',
]

PyInstaller.__main__.run(args)

print("\nBuild complete! Executable is in the 'dist' folder.")
