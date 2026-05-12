"""Build and package the application as standalone executable"""
import PyInstaller.__main__
import os
from pathlib import Path

# Get the project root directory
root_dir = Path(__file__).parent
spec_file = root_dir / 'build' / 'lol_account_manager.spec'

icon_file = root_dir / 'assets' / 'icon.ico'

# Create build command
args = [
    'src/main.py',
    '--name', 'LoL Account Manager',
    '--windowed',  # Hide console window
    '--onefile',  # Create single executable
    '--add-data', f'src:src',
    '--distpath', 'dist',
    '--buildpath', 'build/.build',
    '--specpath', 'build',
]

if icon_file.exists():
    args.extend(['--icon', str(icon_file)])
    args.extend(['--add-data', f'{icon_file}:assets'])

PyInstaller.__main__.run(args)

print("\nBuild complete! Executable is in the 'dist' folder.")
