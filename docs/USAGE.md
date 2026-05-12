# Usage Guide

## Launching the Application

### Windows
- **Quick start**: Double-click `run.bat` in the project folder
- **With Python installed**: `python src/main.py` from command prompt
- **Standalone executable**: Double-click the `.exe` file (if built)

## First Time Use

### 1. Set Master Password
On first launch, you'll see the "Set Master Password" dialog:

- Choose a **strong, memorable password** (minimum 4 characters, but 8+ recommended)
- Confirm the password by typing it again
- Click "OK"

**Important**: If you forget this password, you'll need to delete the `master.key` file and start over (you'll lose access to saved accounts).

### 2. Add Your Accounts

Click **"+ Add Account"** to register a League of Legends account:

- **Username (or Email)**: Your League of Legends login username or email
- **Password**: Your account password
- **Display Name** (optional): A friendly name to identify this account in the list

Example:
```
Username: john.doe@email.com
Password: [your password]
Display Name: John's Main Account
```

Click **"Add Account"** to save.

## Logging In and Launching

### Quick Launch

1. **Select an account** from the list
2. Click **"Launch Selected Account"**
3. The Riot Client will start
4. **Complete any login prompts** if needed (if your credentials aren't cached)
5. League of Legends will automatically launch
6. Play!

### What Happens Behind the Scenes

- The app stores your password securely using AES-256 encryption
- When you launch an account, it:
  - Decrypts your stored password
  - Launches the Riot Client
  - Passes credentials to attempt automatic login
  - Launches League of Legends
  - Closes itself

## Managing Accounts

### View Accounts
All saved accounts are listed in the main window with:
- Display name (bold)
- Username/email (gray text)

### Delete an Account
1. Select the account you want to remove
2. Click **"Delete"**
3. Confirm the deletion
4. The account is removed and no longer saved

### Change Master Password
Click **"Change Master Password"** at the bottom:

1. Enter your current master password to verify
2. Enter and confirm your new master password
3. All accounts are automatically re-encrypted with the new password

## Security Features

### Password Encryption
- All stored passwords are encrypted with **AES-256 encryption**
- Encryption uses your master password as the key
- Passwords are never stored in plain text
- All data is stored locally on your computer

### Master Password Protection
- Your master password is hashed and stored securely
- The master password is required every time you launch the app
- You get 3 attempts to enter the correct master password

### No Data Transmission
- The app does NOT:
  - Send passwords to external servers
  - Log sensitive information
  - Share data with third parties
  - Require internet connection (except for Riot/League servers)

## Troubleshooting

### Correct password but login fails
- Make sure your League of Legends account is not already logged in elsewhere
- Wait 30 seconds before trying to launch again
- Check your username/password is typed correctly (edit the account to verify)

### Riot Client launches but nothing happens
- Wait a few seconds - it may still be loading
- Try logging in manually through the Riot Client to ensure credentials work
- Check that League of Legends is fully installed

### Application won't start
- Try deleting the `AppData/LoLAccountManager` folder and restarting
- Make sure Python is installed and in your PATH
- Reinstall dependencies: `pip install -r requirements.txt --force-reinstall`

### Lost Master Password
- Unfortunately, there's no recovery if you forget the master password
- You must delete the `master.key` file in your AppData folder
- All saved accounts will be lost - you'll need to re-add them
- To access AppData:
  1. Press `Win + R`
  2. Type `%APPDATA%\LoLAccountManager`
  3. Delete the `master.key` file

## Advanced Usage

### Custom League of Legends Installation
If League of Legends is installed in a non-standard location, edit [src/config/paths.py](src/config/paths.py) and add your installation path to the `LOL_PATHS` list.

### Running from Source
If you prefer to always run from source:
```bash
# Activate virtual environment
venv\Scripts\activate.bat

# Run the app
python src/main.py
```

## Tips & Tricks

- **Shortcut to AppData**: Press `Win + R` and type `%APPDATA%\LoLAccountManager`
- **Remove an account completely**: Delete its entry from `accounts.json` (after backing it up)
- **Backup your accounts**: Copy the `accounts.json` file to another location
- **Use different passwords**: Don't reuse the same password across multiple League accounts

## Contact & Support

For issues or suggestions, please open an issue in the repository or check the README for more information.
