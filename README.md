# League of Legends Account Manager

A secure desktop application for Windows 11 that lets you quickly switch between saved League of Legends accounts.

## ⭐ Quick Start

### Just double-click `run.bat`!

That's it. The script will:
1. ✅ Check for Python (downloads & installs if needed)
2. ✅ Create a virtual environment
3. ✅ Install dependencies automatically
4. ✅ Launch the app

**First time takes 2-5 minutes. Subsequent runs are instant!**

If `run.bat` doesn't work, try right-clicking `run.ps1` → "Run with PowerShell"

See [QUICKSTART.md](QUICKSTART.md) for more options.

## Features

- 🔐 **Secure Password Storage**: Encrypted credential storage using AES-256 encryption
- 👥 **Account Management**: Add, edit, and delete multiple League of Legends accounts
- ⚡ **Quick Launch**: One-click account switching with automatic LoL client login
- 🎮 **Auto-Launch**: Automatically launches League of Legends after successful login
- 🔑 **Master Password**: Protected with a master password for additional security
- 🚀 **No Python Required**: Auto-installs Python if needed

## Installation

### Option 1: Auto-Installation (Easiest) ⭐
```bash
Double-click run.bat
```

### Option 2: PowerShell
```bash
Right-click run.ps1 → Run with PowerShell
```

### Option 3: Manual
```bash
python -m venv venv
venv\Scripts\activate.bat
pip install -r requirements.txt
python src/main.py
```

See [INSTALL.md](INSTALL.md) for detailed instructions.

## First Time Setup

1. Set a master password to encrypt your account credentials
2. Add your League of Legends accounts
3. Select an account and click "Launch" to automatically log in and start LoL

## Security

- All passwords are encrypted with **AES-256**
- Master password is required to access stored credentials
- Credentials are never logged or sent anywhere
- All data is stored locally on your computer
- No telemetry or external connections

## Requirements

- **Windows 11** (Windows 10 may also work)
- **League of Legends** installed
- **Riot Client** installed (comes with League of Legends)
- ✅ **Python 3.9+** (auto-installs if needed!)

## Architecture

- **main.py**: Application entry point
- **ui/**: Qt-based user interface
- **core/**: Core logic for account management and Riot client integration
- **security/**: Encryption and credential management
- **config/**: Configuration and file paths

## Technology Stack

- **PyQt5**: User interface
- **cryptography**: Secure password encryption (AES-256)
- **Python 3.9+**: Application runtime
- **Windows Registry API**: Riot client integration

## Documentation

- [QUICKSTART.md](QUICKSTART.md) - Quick 5-minute setup
- [USAGE.md](USAGE.md) - How to use features
- [INSTALL.md](INSTALL.md) - Installation options
- [CONFIGURATION.md](CONFIGURATION.md) - Custom paths setup
- [DEVELOPER.md](DEVELOPER.md) - Architecture & development

## Troubleshooting

**Installer doesn't work?**
- Try `run.ps1` (right-click → Run with PowerShell)
- Or manually install Python from https://www.python.org/

**League of Legends not found?**
- Ensure it's installed in the default location
- See [CONFIGURATION.md](CONFIGURATION.md) for custom paths

**App won't start?**
- Try running again (sometimes needs 2 attempts)
- Check internet connection (first setup downloads dependencies)
- See [USAGE.md#troubleshooting](USAGE.md#troubleshooting) for more

## Next Steps

1. **Quick Start**: Open [QUICKSTART.md](QUICKSTART.md)
2. **Just Run**: Double-click `run.bat` or `run.ps1`
3. **Learn More**: See [USAGE.md](USAGE.md)

---

**Ready? Just double-click `run.bat` and let it handle everything!** 🎮
