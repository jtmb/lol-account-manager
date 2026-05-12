"""Build and package the application as standalone executable"""
import PyInstaller.__main__
import os
from pathlib import Path

# Get the project root directory
root_dir = Path(__file__).parent
spec_file = root_dir / 'build' / 'lol_account_manager.spec'

# Create build command
PyInstaller.__main__.run([
    'src/main.py',
    '--name', 'LoL Account Manager',
    '--windowed',  # Hide console window
    '--onefile',  # Create single executable
    '--icon', 'assets/icon.ico' if (root_dir / 'assets' / 'icon.ico').exists() else None,
    '--add-data', f'src:src',
    '--distpath', 'dist',
    '--buildpath', 'build/.build',
    '--specpath', 'build',
])

print("\nBuild complete! Executable is in the 'dist' folder.")
