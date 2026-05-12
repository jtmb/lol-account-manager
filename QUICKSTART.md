# Quick Start Guide

## Easiest Setup (Just Click & Go!) ⭐

### Step 1: Download
1. Download this project (Green "Code" button → "Download ZIP")
2. Extract to a folder (e.g., `C:\Games\LoL-Manager`)
3. Open the folder

### Step 2: Run
**Choose ONE of these:**

#### Option A: Double-click `run.bat` (Easiest) ✅
- **Best for**: Most users
- Double-click `run.bat`
- It will automatically download and install Python if needed
- Wait 2-5 minutes for first setup
- App launches automatically!

#### Option B: Right-click `run.ps1` → "Run with PowerShell" 
- **Best for**: If `run.bat` doesn't work
- Slightly more reliable
- Follow the same process as Option A

#### Option C: Manual Python + run `run.bat`
- **Best for**: Advanced users
- Install Python 3.9+ from https://www.python.org/
- ✅ Check "Add Python to PATH" during install
- Restart your computer
- Then double-click `run.bat`

### Step 3: Use the App
1. Set your master password (something you'll remember!)
2. Click "+ Add Account"
3. Enter your League username and password
4. Click "Launch Selected Account"
5. Play!

## First Run Tips

- ⏱️ **First launch takes 2-5 minutes** (installing Python and dependencies)
- 🔒 **Remember your master password** - you can't recover it if lost
- 🎮 **Riot Client will open** - Complete login if credentials aren't cached
- 🚀 **League of Legends launches automatically** after login

## What Happens

```
You double-click run.bat/ps1
    ↓
Script checks for Python
    ↓
If Python missing → Downloads & installs automatically
    ↓
Creates virtual environment
    ↓
Installs dependencies
    ↓
App launches!
```

## Troubleshooting

### "Python installer didn't work"
- **Option 1**: Try `run.ps1` instead (right-click → Run with PowerShell)
- **Option 2**: Install Python manually from https://www.python.org/
  - Make sure to check "Add Python to PATH"
  - Restart your computer
  - Then run the script again

### Script stops or seems frozen
- **Wait longer** - first setup takes 2-5 minutes
- **Check internet** - needs to download Python (~30MB)
- **Try PowerShell version** - `run.ps1` is more reliable on some systems

### "Access denied" error
- Right-click the `.bat` or `.ps1` file
- Select "Run as Administrator"
- Try again

### App starts but crashes immediately
- Make sure you're running from the project folder
- Check that `requirements.txt` is in the same folder as `run.bat`
- Try running again (sometimes needs 2 attempts)

## If Everything Fails

1. **Manual Installation**:
   ```bash
   python -m venv venv
   venv\Scripts\activate.bat
   pip install -r requirements.txt
   python src/main.py
   ```

2. **Or see full installation guide**: [INSTALL.md](INSTALL.md)

## Next Steps

- Read [USAGE.md](USAGE.md) for features
- Read [CONFIGURATION.md](CONFIGURATION.md) if League is in a custom folder
- Read [SETUP_COMPLETE.md](SETUP_COMPLETE.md) for more options

---

**That's it! Just double-click `run.bat` and it handles everything!** 🚀
