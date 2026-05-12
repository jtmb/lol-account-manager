# Installation Guide

## Prerequisites

- **Windows 11** (or Windows 10+)
- **League of Legends** installed
- **Riot Client** installed
- ✅ **Python 3.9+** (optional - auto-installs if missing!)

## Installation Steps

### ⭐ Option 1: Quick Start (Recommended - Auto Everything!)

**This is the easiest way. No Python installation required!**

1. Download this repository (Green "Code" button → "Download ZIP")
2. Extract to any folder
3. **Double-click `run.bat`**
4. Wait for setup (2-5 minutes on first run)
5. App launches automatically!

**What it does automatically:**
- ✅ Checks for Python
- ✅ Downloads & installs Python if missing
- ✅ Creates virtual environment
- ✅ Installs dependencies
- ✅ Launches the app

---

### Option 2: PowerShell Launch

**If `run.bat` doesn't work, try this:**

1. Right-click `run.ps1`
2. Select "Run with PowerShell"
3. Follow the same process as Option 1

---

### Option 3: Manual Installation with Python Already Installed

**Use this if Python is already installed on your system:**

1. Open Command Prompt
2. Navigate to the project directory
3. Create virtual environment:
   ```bash
   python -m venv venv
   ```
4. Activate the virtual environment:
   ```bash
   venv\Scripts\activate.bat
   ```
5. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
6. Run the application:
   ```bash
   python src/main.py
   ```

---

### Option 4: Manual Installation (No Python Pre-Installed)

**Follow these steps if you want to install Python manually:**

1. **Install Python**:
   - Go to https://www.python.org/downloads/
   - Download Python 3.11 or later
   - Run the installer
   - ⚠️ **CRITICAL**: Check "Add Python to PATH" ⚠️
   - Click "Install Now"
   - **Restart your computer**

2. **Then follow Option 3** above

---

### Option 5: Build Standalone Executable

**Create a `.exe` file that doesn't need Python:**

1. Install Python (Option 4)
2. Follow steps in [DEVELOPER.md](DEVELOPER.md) to build with PyInstaller
3. Distribute the `.exe` to other computers without Python

---

## First Time Setup

After installation, the app will:

1. **Ask for Master Password** (first time only)
   - Choose a strong password (8+ characters recommended)
   - Confirm by typing again
   - **Important**: Don't forget this password!

2. **Add Your Accounts**
   - Click "+ Add Account"
   - Enter League username/email
   - Enter password
   - Optionally add a display name
   - Click "Add Account"

3. **Launch and Play**
   - Select an account
   - Click "Launch Selected Account"
   - Riot Client opens
   - League of Legends launches
   - Play!

---

## Troubleshooting

### "Python not found" error
- Try **Option 2** (PowerShell)
- Or manually install Python from https://www.python.org/

### "Failed to download Python" error
- Check your internet connection
- Firewall might be blocking downloads
- Try **Option 4** to install Python manually

### Script stops or seems frozen
- **Wait longer** - first setup takes 2-5 minutes
- Check internet connection (downloads ~30MB of dependencies)
- Don't close the window until it says "Starting League of Legends Account Manager"

### "Access denied" error
- Right-click `run.bat` or `run.ps1`
- Select "Run as Administrator"

### "League of Legends not found"
- Ensure League is installed in the default location
- Or see [CONFIGURATION.md](CONFIGURATION.md) to set custom path

### "Dependency installation failed"
- Check internet connection
- Try running again (sometimes temporary failures)
- If persistent, try **Option 3** or **Option 4**

---

## What Gets Installed

The script automatically installs:

- **PyQt5** - Desktop UI framework
- **cryptography** - Password encryption library
- **keyring** - Credential management
- **psutil** - Process management
- **requests** - HTTP library
- **pywin32** - Windows API access
- **python-dotenv** - Environment variables

Total download size: ~50-100MB (first time only)

---

## Storage Locations

- **Accounts file**: `%APPDATA%\LoLAccountManager\accounts.json`
- **Master password**: `%APPDATA%\LoLAccountManager\master.key`
- **Virtual environment**: `venv\` (in project folder)

To access: Press `Win + R`, type `%APPDATA%\LoLAccountManager`

---

## Next Steps

1. **Read [QUICKSTART.md](QUICKSTART.md)** for quick overview
2. **Read [USAGE.md](USAGE.md)** to learn all features
3. **See [CONFIGURATION.md](CONFIGURATION.md)** if League is in custom location
4. **Check [DEVELOPER.md](DEVELOPER.md)** if building/modifying

---

## System Requirements

- **OS**: Windows 10/11 (64-bit)
- **RAM**: 2GB minimum (8GB+ recommended)
- **Storage**: 500MB available
- **Internet**: Required for first setup (downloads Python & dependencies)
- **League of Legends**: Must be installed
- **Riot Client**: Must be installed

---

## Getting Help

- Stuck? Check [USAGE.md#troubleshooting](USAGE.md#troubleshooting)
- Want to customize paths? See [CONFIGURATION.md](CONFIGURATION.md)
- Want to develop/build? See [DEVELOPER.md](DEVELOPER.md)
