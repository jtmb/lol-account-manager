# Developer Guide

## Project Structure

```
lol-account-manager/
├── src/                          # Main source code
│   ├── main.py                   # Application entry point
│   ├── config/
│   │   ├── paths.py              # Path configuration and Riot/LoL detection
│   ├── core/
│   │   ├── account_manager.py    # Account storage and management
│   │   └── riot_integration.py   # Riot Client and LoL integration
│   ├── security/
│   │   └── encryption.py         # AES-256 encryption utilities
│   └── ui/
│       └── main_window.py        # PyQt5 UI components
├── requirements.txt              # Python dependencies
├── setup.py                      # Setup script
├── run.bat                       # Quick launcher for Windows
├── build_exe.py                  # Build standalone executable
├── test_app.py                   # Unit tests
├── README.md                     # Project overview
├── INSTALL.md                    # Installation instructions
├── USAGE.md                      # Usage guide
└── DEVELOPER.md                  # This file
```

## Architecture

### Security Layer (`src/security/`)
- **encryption.py**: Handles AES-256 encryption using PBKDF2 key derivation
  - `PasswordEncryption`: Main class for encrypting/decrypting passwords
  - `hash_master_password()`: Create verifiable hash of master password
  - `verify_master_password()`: Verify master password against stored hash

### Core Logic (`src/core/`)
- **account_manager.py**: Manages account storage and retrieval
  - `Account`: Data class representing a LoL account
  - `AccountManager`: Main class for account CRUD operations
    - `add_account()`: Save new account with encrypted password
    - `load_accounts()`: Load and decrypt accounts from file
    - `save_accounts()`: Persist accounts with encryption
    - `update_account()`: Modify existing account
    - `delete_account()`: Remove account

- **riot_integration.py**: Handles launching Riot Client and LoL
  - `RiotClientIntegration`: Utility class for system integration
    - `find_lol_launch_dir()`: Locate LoL installation
    - `launch_riot_client()`: Start Riot Client process
    - `launch_lol()`: Start League of Legends
    - `login_and_launch()`: Complete login flow
    - `is_riot_client_running()`: Check process status

### Configuration (`src/config/`)
- **paths.py**: Find and manage application paths
  - Detects Riot Client installation location
  - Detects League of Legends installation
  - Manages AppData storage directory
  - Provides helper functions for finding executables

### User Interface (`src/ui/`)
- **main_window.py**: PyQt5 GUI components
  - `MainWindow`: Main application window
  - `MasterPasswordDialog`: Dialog for setting/verifying master password
  - `AddAccountDialog`: Dialog for adding new accounts
  - `AccountListItem`: Custom widget for account display in list
  - `LoginThread`: Background thread for non-blocking login/launch

## Data Storage

### Accounts File Format
Location: `%APPDATA%\LoLAccountManager\accounts.json`

```json
[
  {
    "username": "player_email@example.com",
    "password": "gAAAAABmX...", // encrypted
    "display_name": "Main Account",
    "is_encrypted": true
  }
]
```

### Master Password Hash
Location: `%APPDATA%\LoLAccountManager\master.key`

Contains SHA256 hash of master password (salted and iterated 100,000 times with PBKDF2).

## Key Features & Implementation Details

### 1. Secure Password Storage
- Uses `cryptography` library's `Fernet` cipher (symmetric AES-128)
- Derives encryption key from master password using PBKDF2
- Fixed salt ensures consistency across sessions
- Base64 encoding for storage

### 2. Master Password System
- Master password never stored in plain text
- Stored as SHA256 hash with PBKDF2
- 3 attempts before exit (security feature)
- Must be verified on startup

### 3. Account Management
- Passwords encrypted before file storage
- Accounts loaded and decrypted on initialization
- JSON format for easy manual inspection/backup
- Automatic file persistence

### 4. Riot Client Integration
- Detects LoL installation directory
- Locates Riot Client executable
- Manages process lifecycle (kill existing, launch new)
- Waits for Riot Client initialization before launching LoL

### 5. Multi-Threading
- Login/launch operations run on background thread
- Prevents UI freezing during authentication
- Emit signals for completion/error handling

## Development Workflow

### Running in Development

```bash
# Create virtual environment
python -m venv venv
venv\Scripts\activate.bat

# Install dependencies
pip install -r requirements.txt

# Run tests
python -m unittest test_app.py

# Run application
python src/main.py
```

### Adding New Features

1. **New Account Property**: 
   - Add field to `Account` dataclass in `account_manager.py`
   - Update `AddAccountDialog` in `main_window.py` if user input needed

2. **New Launch Option**:
   - Add method to `RiotClientIntegration` in `riot_integration.py`
   - Call from `MainWindow.launch_account()`

3. **New UI Dialog**:
   - Create new QDialog subclass in `main_window.py`
   - Add button/menu item to `MainWindow`

### Testing

Run the test suite:
```bash
python -m unittest test_app.py -v
```

Add new tests to `test_app.py`:
```python
class TestNewFeature(unittest.TestCase):
    def test_something(self):
        # Test implementation
        pass
```

## Building Standalone Executable

### Prerequisites
```bash
pip install PyInstaller
```

### Build
```bash
python build_exe.py
```

### Output
- Standalone `.exe` in `dist/` folder
- No Python installation required on target machine
- ~100-150MB file size

### Distribution
- Rename to: `LoL_Account_Manager.exe`
- Create installer (optional, using NSIS or InnoSetup)
- Document Python runtime requirements if not using exe

## Known Limitations & Future Improvements

### Current Limitations
1. **Riot Client Login**: Currently shows login UI - future versions could automate this
2. **Custom Install Paths**: Must manually configure if LoL installed in non-standard location
3. **No 2FA Support**: Cannot automatically handle two-factor authentication
4. **Windows Only**: Currently Windows 11 specific

### Future Enhancements
1. Auto-detect and fill login form via UI automation
2. Support for 2FA via email/SMS
3. Account usage statistics/history
4. Hot reload without restarting
5. Dark mode UI
6. Portable version without installer
7. Import/export accounts (with encryption)
8. Cloud backup support (optional)

## Debugging

### Enable Verbose Logging
Add to `src/main.py`:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check Paths
Print detected paths:
```python
from src.config.paths import get_riot_client_path, get_lol_path
print(f"Riot Client: {get_riot_client_path()}")
print(f"LoL Path: {get_lol_path()}")
```

### Inspect Stored Data
```bash
# View accounts (encrypted)
type %APPDATA%\LoLAccountManager\accounts.json

# View master password hash
type %APPDATA%\LoLAccountManager\master.key
```

## Contributing

1. Create a feature branch: `git checkout -b feature/awesome-feature`
2. Make changes and add tests
3. Run tests: `python -m unittest test_app.py`
4. Commit: `git commit -am 'Add awesome feature'`
5. Push: `git push origin feature/awesome-feature`
6. Open Pull Request

## Security Considerations

- ⚠️ Master password stored as hash (can't be recovered if lost)
- ⚠️ Passwords in memory during login (system RAM could be analyzed)
- ⚠️ Local storage vulnerable to local attacks (use strong OS password)
- ✅ Passwords encrypted at rest (AES-256)
- ✅ No network transmission of credentials
- ✅ No telemetry or logging of sensitive data

## License

[Specify your license here]

## Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Check existing issues for solutions
- Review README and USAGE guides
