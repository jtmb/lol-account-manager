# Project Setup Complete! 🎮

Your League of Legends Account Manager is ready to use!

## 📦 What Was Created

A complete, production-ready Windows 11 application with:

✅ **Secure Account Management**
- AES-256 encrypted password storage
- Master password protection
- Local-only data (no cloud, no telemetry)

✅ **Easy Account Switching**
- Simple UI to select accounts
- One-click login and launch
- Automatic League of Legends startup

✅ **Professional UI**
- PyQt5-based desktop application
- Clean, intuitive interface
- Background login/launch operations

✅ **Complete Documentation**
- Installation guide
- Usage guide  
- Developer documentation
- Quick start guide

## 📁 Project Structure

```
lol-account-manager/
├── src/                          # Application source code
│   ├── main.py                   # Entry point
│   ├── config/paths.py           # Find League/Riot Client
│   ├── core/                     # Core logic
│   │   ├── account_manager.py    # Account storage & encryption
│   │   └── riot_integration.py   # Launch League/Riot
│   ├── security/encryption.py    # AES-256 encryption
│   └── ui/main_window.py         # PyQt5 UI
├── run.bat                       # Quick start (Windows)
├── requirements.txt              # Python dependencies
├── QUICKSTART.md                 # 5-minute setup guide ← START HERE
├── INSTALL.md                    # Installation instructions
├── USAGE.md                      # Feature guide
├── DEVELOPER.md                  # For developers
└── README.md                     # Project overview
```

## 🚀 Getting Started

### Option 1: Quick Start (Recommended) ⭐

1. **Download Python** (if not installed):
   - Visit https://www.python.org/downloads/
   - Install Python 3.9 or later
   - ⚠️ Check "Add Python to PATH" during install
   - Restart your computer

2. **Run the App**:
   - Double-click `run.bat` in this folder
   - Wait for dependencies to install
   - App launches automatically!

3. **First Use**:
   - Set a master password
   - Add your League accounts
   - Click "Launch Selected Account" to play!

### Option 2: Manual Setup

See [INSTALL.md](INSTALL.md) for detailed instructions.

### Option 3: Build Standalone Executable

See [DEVELOPER.md](DEVELOPER.md) for PyInstaller instructions (creates `.exe` that doesn't need Python).

## 📖 Documentation

| Document | Purpose |
|----------|---------|
| [QUICKSTART.md](QUICKSTART.md) | 5-minute setup guide - **START HERE** |
| [USAGE.md](USAGE.md) | Feature guide and troubleshooting |
| [INSTALL.md](INSTALL.md) | Detailed installation steps |
| [DEVELOPER.md](DEVELOPER.md) | Architecture, development, building |
| [README.md](README.md) | Project overview |

## 🔐 Security Features

- **AES-256 Encryption**: All passwords encrypted using military-grade encryption
- **Master Password**: Protect all accounts with one strong password
- **Local Storage**: All data stored on your computer only
- **No Telemetry**: No analytics, no tracking, no phone-home
- **No Network**: Passwords never sent anywhere

## 🎯 Key Features

✅ Add unlimited League of Legends accounts
✅ Securely store passwords with encryption
✅ Quick-switch between accounts
✅ Auto-launch League of Legends
✅ Change master password anytime
✅ Delete accounts you no longer need
✅ Portable - works on any Windows 11 machine

## ⚠️ Important Notes

1. **Master Password**: If you forget it, you must delete `master.key` in AppData and start over (you'll lose saved accounts)
2. **League Installation**: Must be installed in standard location (if custom, see DEVELOPER.md)
3. **Riot Client**: Must be installed (comes with League of Legends)
4. **2FA**: If your League account has 2FA, you'll need to complete the login manually in Riot Client

## 🐛 Troubleshooting

**"Python not found"**
- Install Python from https://www.python.org/
- Make sure to check "Add Python to PATH"
- Restart your computer

**"League of Legends not found"**
- Ensure League of Legends is installed in default location
- See INSTALL.md for custom path setup

**"Riot Client won't start"**
- Make sure Riot Client is installed
- Reinstall League of Legends if needed

See [USAGE.md](USAGE.md#troubleshooting) for more solutions.

## 📝 Files & Purposes

| File | Purpose |
|------|---------|
| `run.bat` | 🟢 Click to start the app (Windows) |
| `requirements.txt` | Python dependencies |
| `setup.py` | Setup script for development |
| `build_exe.py` | Build standalone `.exe` file |
| `test_app.py` | Unit tests |
| `src/main.py` | Application entry point |
| `src/core/` | Account management & Riot integration |
| `src/security/` | Encryption & password management |
| `src/ui/` | User interface (PyQt5) |
| `src/config/` | Path detection & configuration |

## 🎮 Quick Launch

```bash
# Option 1: Click run.bat (easiest)
# Option 2: Command line
python src/main.py

# Option 3: After building executable
LoL_Account_Manager.exe
```

## 💡 Tips

- **First Login**: Might take 5-10 seconds to start (Riot Client loading)
- **Custom Display Names**: Use nicknames to identify accounts (e.g., "Main", "Smurf", "Dad's Account")
- **Multiple Accounts**: You can save as many accounts as you want
- **Safe Password**: Master password is never stored in plain text

## 🔄 What Happens When You Launch

1. Select account from list
2. Click "Launch Selected Account"
3. Riot Client starts
4. Complete login if needed
5. League of Legends launches automatically
6. App closes (stays out of the way)

## 📞 Need Help?

1. Read the relevant guide above
2. Check [USAGE.md#troubleshooting](USAGE.md#troubleshooting)
3. Review [INSTALL.md](INSTALL.md)

## ✨ Ready?

**Next step**: Open [QUICKSTART.md](QUICKSTART.md) for the 5-minute setup guide!

Or just click `run.bat` to get started right now! 🚀

---

**Version**: 1.0.0
**Platform**: Windows 11
**License**: See repository
**Status**: ✅ Ready to use!
