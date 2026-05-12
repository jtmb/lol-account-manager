"""Application paths and configuration"""
import os
import json
from pathlib import Path
from typing import Optional

# Get user's appdata directory
APPDATA = Path(os.getenv('APPDATA', os.path.expanduser('~')))
APP_DATA_DIR = APPDATA / 'LoLAccountManager'
ACCOUNTS_FILE = APP_DATA_DIR / 'accounts.json'
MASTER_PASSWORD_FILE = APP_DATA_DIR / 'master.key'
SETTINGS_FILE = APP_DATA_DIR / 'settings.json'


def load_settings() -> dict:
    """Load settings from disk, return empty dict if missing."""
    try:
        if SETTINGS_FILE.exists():
            with open(SETTINGS_FILE, 'r') as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def save_settings(settings: dict):
    """Persist settings to disk."""
    ensure_app_data_dir()
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f, indent=2)


def get_custom_lol_exe() -> Optional[Path]:
    """Return user-specified LeagueClient.exe path, or None."""
    p = load_settings().get('lol_exe')
    if p:
        path = Path(p)
        if path.exists():
            return path
    return None


def set_custom_lol_exe(path: Path):
    """Persist user-specified LeagueClient.exe path."""
    settings = load_settings()
    settings['lol_exe'] = str(path)
    save_settings(settings)

# Riot client paths
RIOT_CLIENT_PATHS = [
    Path(os.getenv('ProgramFiles', 'C:\\Program Files')) / 'Riot Client' / 'RiotClientServices.exe',
    Path(os.getenv('ProgramFiles(x86)', 'C:\\Program Files (x86)')) / 'Riot Client' / 'RiotClientServices.exe',
    Path('C:\\Riot Games\\Riot Client\\RiotClientServices.exe'),
]

# League of Legends paths
LOL_PATHS = [
    Path(os.getenv('ProgramFiles', 'C:\\Program Files')) / 'Riot Games' / 'League of Legends',
    Path(os.getenv('ProgramFiles(x86)', 'C:\\Program Files (x86)')) / 'Riot Games' / 'League of Legends',
    Path('C:\\Riot Games\\League of Legends'),
]

# Riot client configuration paths
RIOT_CONFIG_PATHS = [
    APPDATA / 'Riot Games' / 'Riot Client' / 'Config' / 'RiotClientSettings.yaml',
    Path(os.getenv('LOCALAPPDATA', os.path.expanduser('~\\AppData\\Local'))) / 'Riot Games' / 'Riot Client' / 'Config' / 'RiotClientSettings.yaml',
]


def ensure_app_data_dir():
    """Ensure app data directory exists"""
    APP_DATA_DIR.mkdir(parents=True, exist_ok=True)


def get_riot_client_path() -> Optional[Path]:
    """Find Riot Client executable"""
    for path in RIOT_CLIENT_PATHS:
        if path.exists():
            return path
    return None


def get_lol_path() -> Optional[Path]:
    """Find League of Legends installation directory"""
    for path in LOL_PATHS:
        if path.exists():
            return path
    return None


def get_lol_executable() -> Optional[Path]:
    """Get League of Legends executable path.
    Checks user-specified path first, then auto-detects."""
    custom = get_custom_lol_exe()
    if custom:
        return custom
    lol_path = get_lol_path()
    if lol_path:
        candidates = [
            lol_path / 'LeagueClient.exe',
            lol_path / 'LeagueClient' / 'LeagueClient.exe',
            lol_path / 'League of Legends.exe',
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate
    return None


def get_riot_config_path() -> Optional[Path]:
    """Get Riot Client config file path"""
    for path in RIOT_CONFIG_PATHS:
        if path.exists():
            return path
    return None
