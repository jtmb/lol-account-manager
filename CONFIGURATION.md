# Customization Guide

## Non-Standard League of Legends Installation

If League of Legends is installed in a non-standard location, you can configure it here.

### Finding Your Installation Path

1. Open **File Explorer**
2. Search for `LeagueClient.exe` or `League of Legends`
3. Note the full path (e.g., `D:\Games\League of Legends`)

### Updating Configuration

Edit `src/config/paths.py` and modify the lists:

#### For League of Legends Path:

Find this section:
```python
LOL_PATHS = [
    Path(os.getenv('ProgramFiles', 'C:\\Program Files')) / 'Riot Games' / 'League of Legends',
    Path(os.getenv('ProgramFiles(x86)', 'C:\\Program Files (x86)')) / 'Riot Games' / 'League of Legends',
    Path('C:\\Riot Games\\League of Legends'),
]
```

Add your path to the list:
```python
LOL_PATHS = [
    Path(os.getenv('ProgramFiles', 'C:\\Program Files')) / 'Riot Games' / 'League of Legends',
    Path(os.getenv('ProgramFiles(x86)', 'C:\\Program Files (x86)')) / 'Riot Games' / 'League of Legends',
    Path('C:\\Riot Games\\League of Legends'),
    Path('D:\\Games\\League of Legends'),  # Add your custom path here
]
```

#### For Riot Client Path:

Find this section:
```python
RIOT_CLIENT_PATHS = [
    Path(os.getenv('ProgramFiles', 'C:\\Program Files')) / 'Riot Client' / 'RiotClientServices.exe',
    Path(os.getenv('ProgramFiles(x86)', 'C:\\Program Files (x86)')) / 'Riot Client' / 'RiotClientServices.exe',
    Path('C:\\Riot Games\\Riot Client\\RiotClientServices.exe'),
]
```

Add your path to the list:
```python
RIOT_CLIENT_PATHS = [
    Path(os.getenv('ProgramFiles', 'C:\\Program Files')) / 'Riot Client' / 'RiotClientServices.exe',
    Path(os.getenv('ProgramFiles(x86)', 'C:\\Program Files (x86)')) / 'Riot Client' / 'RiotClientServices.exe',
    Path('C:\\Riot Games\\Riot Client\\RiotClientServices.exe'),
    Path('D:\\Games\\Riot\\Riot Client\\RiotClientServices.exe'),  # Add your custom path here
]
```

Save the file and restart the application.

## Account Storage Location

By default, accounts are stored in:
```
%APPDATA%\LoLAccountManager\accounts.json
```

If you want to change this location:

Edit `src/config/paths.py`:
```python
# Change from:
APP_DATA_DIR = APPDATA / 'LoLAccountManager'

# To:
APP_DATA_DIR = Path('D:\\MyCustomLocation\\LoLAccounts')
```

## Master Password Storage

Master password hash is stored in:
```
%APPDATA%\LoLAccountManager\master.key
```

This is intentionally stored separately from accounts for security.

## Environment Variables

You can also use environment variables for configuration:

```batch
@echo off
REM Set custom League path
set LEAGUE_INSTALL=D:\Games\League of Legends

REM Set custom Riot Client path
set RIOT_CLIENT=D:\Games\Riot\Riot Client\RiotClientServices.exe

REM Set custom data directory
set LOL_MANAGER_DATA=D:\MyData\LoLManager

python src/main.py
```

Save as `run_custom.bat` and use instead of `run.bat`.

## Troubleshooting Paths

### Verify Paths Detected

Add this to `src/main.py` temporarily:

```python
from src.config.paths import get_lol_path, get_riot_client_path

print(f"LoL Path: {get_lol_path()}")
print(f"Riot Path: {get_riot_client_path()}")
```

Run the script and check output.

### Manual Path Override

Edit `src/config/paths.py` and uncomment/modify:

```python
# Uncomment to force specific paths
# FORCED_LOL_PATH = Path('D:\\Games\\League of Legends')
# FORCED_RIOT_PATH = Path('D:\\Games\\Riot Client\\RiotClientServices.exe')

def get_lol_path() -> Optional[Path]:
    """Find League of Legends installation directory"""
    # if FORCED_LOL_PATH and FORCED_LOL_PATH.exists():
    #     return FORCED_LOL_PATH
    
    for path in LOL_PATHS:
        if path.exists():
            return path
    return None
```

## Resetting Configuration

To reset to default configuration:

1. Delete `src/config/paths.py`
2. Delete AppData folder: `%APPDATA%\LoLAccountManager\`
3. Restart the application

## Getting Help

If paths aren't being detected:

1. Verify League of Legends and Riot Client are installed
2. Check the paths manually in File Explorer
3. Add paths to the configuration as shown above
4. Restart the application

If still having issues, see [USAGE.md#troubleshooting](USAGE.md#troubleshooting).
