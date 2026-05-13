<h1 align="center">
	<a href="https://github.com/brajam/lol-account-manager">
		<img src="assets/icon.ico" alt="LoL Account Manager Logo" width="220" height="auto">
	</a>
</h1>

<div align="center">
	<b>League of Legends Account Manager</b> - Securely manage, organize, and launch multiple LoL accounts from one desktop app.
	<br />
	<br />
	<a href="https://github.com/brajam/lol-account-manager/issues/new?assignees=&labels=bug&title=bug%3A+">Report a Bug</a>
	·
	<a href="https://github.com/brajam/lol-account-manager/issues/new?assignees=&labels=enhancement&title=feat%3A+">Request a Feature</a>
</div>

<br>

<details open="open">
<summary>Table of Contents</summary>

- [About](#about)
	- [Highlighted Features](#highlighted-features)
- [Installation](#installation)
- [First Launch](#first-launch)
- [Backup and Restore](#backup-and-restore)
- [Security](#security)
- [Requirements](#requirements)
- [Running From Source](#running-from-source)
- [Building the EXE](#building-the-exe)
- [Documentation](#documentation)
- [Notes](#notes)

</details>

## About

Windows desktop app for saving, organizing, and launching multiple League of Legends accounts from one place.

## Highlighted Features

## Full Feature List

- Secure local credential storage protected by a master password
- Add, edit, and delete saved League accounts
- One-click Riot Client login and League launch flow
- Automatic cleanup of existing Riot / League processes before switching accounts
- Custom display names for easier account management
- Display name + tagline support for modern Riot IDs
- Region-aware account handling
- Ban status tracking per account
- Temporary ban end date support
- Red / green account indicators based on current ban state
- Optional op.gg rank fetching and rank badge display
- Optional account card images
- Account tags with color-coded badges
- Tag-based filtering and quick search
- Encrypted per-account notes
- Encrypted backup export and import
- Merge or replace restore modes when importing a backup
- Automatic versioned backups with retention controls
- Custom League install path override if auto-detection fails
- In-app settings dialog for launcher and display preferences
- Optional auto-open op.gg in-game page after launch
- Launch progress UI with cancellation support
- Dark mode and light mode toggle
- Native Windows title bar theming support
- Standalone executable build support with app icon support

## Installation

1. Go to the GitHub releases page for this project.
2. Download the latest release.
3. Extract it if the release is packaged as a zip.
4. Run `LoLAccountManager.exe`.

## First Launch

1. Set a master password.
2. Add one or more League accounts.
3. Optionally set ban status and ban end date for each account.
4. Select an account and click `Launch Selected Account`.

## Backup and Restore

Use `Backup / Restore...` in the main window to:

- Export an encrypted backup of your saved accounts
- Import a previously exported backup
- Merge imported accounts with your current list
- Replace your current list with the imported backup

Backups are encrypted and require the master password that was active when the backup was created.

## Security

- Credentials are stored locally only
- Account passwords are encrypted before being written to disk
- The master password is hashed and verified locally
- No telemetry or account data is sent by this app

Application data is stored in:

- `%APPDATA%\LoLAccountManager\accounts.json`
- `%APPDATA%\LoLAccountManager\master.key`
- `%APPDATA%\LoLAccountManager\settings.json`

## Requirements

- Windows
- Riot Client installed
- League of Legends installed

## Running From Source

If you want to run or build the project yourself:

```bash
python -m venv venv
venv\Scripts\activate.bat
pip install -r requirements.txt
python src/main.py
```

## Building the EXE

```bash
build_exe.bat
```

If `assets/icon.ico` exists, it will be used for the built executable and runtime window icon.

## Documentation

- [Usage Guide](docs/USAGE.md)
- [Configuration](docs/CONFIGURATION.md)
- [Developer Guide](docs/DEVELOPER.md)

## Notes

- The app is designed around Riot Client based launching.
- If Riot login UI changes significantly, automation behavior may need updating.
- If League is installed in a non-standard location, use `Set LoL Path...` in the app.
