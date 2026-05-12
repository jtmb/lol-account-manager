# Installation Guide

## Prerequisites

- **Windows 11**
- **Python 3.9 or later** (download from https://www.python.org/)
- **League of Legends** installed
- **Riot Client** installed

## Installation Steps

### Option 1: Quick Start (Recommended)

1. Download or clone this repository
2. Navigate to the project folder
3. Double-click `run.bat`
4. The application will install dependencies and launch automatically

### Option 2: Manual Setup

1. Open Command Prompt and navigate to the project directory

2. Create a virtual environment:
   ```bash
   python -m venv venv
   ```

3. Activate the virtual environment:
   ```bash
   venv\Scripts\activate.bat
   ```

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. Run the application:
   ```bash
   python src/main.py
   ```

### Option 3: Build Standalone Executable

To create a standalone `.exe` file (no Python installation required on other machines):

1. Follow steps 1-4 from Option 2

2. Install PyInstaller:
   ```bash
   pip install PyInstaller
   ```

3. Build the executable:
   ```bash
   python build_exe.py
   ```

4. The executable will be created in the `dist` folder
5. You can move this `.exe` to any location and run it directly

## First Time Setup

1. **Set Master Password**: When you launch the app for the first time, you'll be prompted to set a master password. Choose a strong password to protect your credentials.

2. **Add Accounts**: Click "Add Account" and enter:
   - Your League of Legends username/email
   - Your password
   - An optional display name (for easy identification)

3. **Test Launch**: Select an account and click "Launch Selected Account" to test the integration.

## Troubleshooting

### "League of Legends not found"
- Ensure League of Legends is installed in the default location
- If installed elsewhere, the app needs to be configured with the custom path

### "Riot Client not found"
- Ensure the Riot Client is installed
- Reinstall the Riot Client if needed

### "Python not found" (when running `run.bat`)
- Install Python from https://www.python.org/
- Make sure to check "Add Python to PATH" during installation
- Restart your computer after Python installation

### Dependencies installation fails
- Make sure you're connected to the internet
- Try upgrading pip first:
  ```bash
  python -m pip install --upgrade pip
  ```

## Next Steps

See [USAGE.md](USAGE.md) for detailed instructions on using the application.
