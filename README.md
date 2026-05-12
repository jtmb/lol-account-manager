# League of Legends Account Manager

A secure desktop application for Windows 11 that lets you quickly switch between saved League of Legends accounts.

## Features

- 🔐 **Secure Password Storage**: Encrypted credential storage using AES-256 encryption
- 👥 **Account Management**: Add, edit, and delete multiple League of Legends accounts
- ⚡ **Quick Launch**: One-click account switching with automatic LoL client login
- 🎮 **Auto-Launch**: Automatically launches League of Legends after successful login
- 🔑 **Master Password**: Protected with a master password for additional security

## Requirements

- Windows 11
- League of Legends installed
- Python 3.9+ (for development)
- Riot Client installed

## Installation

1. Clone this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   python src/main.py
   ```

## First Time Setup

1. Set a master password to encrypt your account credentials
2. Add your League of Legends accounts
3. Select an account and click "Launch" to automatically log in and start LoL

## Security

- All passwords are encrypted with AES-256
- Master password is required to access stored credentials
- Credentials are never logged or sent anywhere
- All data is stored locally

## Architecture

- **main.py**: Application entry point
- **ui/**: Qt-based user interface
- **core/**: Core logic for account management and Riot client integration
- **security/**: Encryption and credential management
- **config/**: Configuration and file paths

## Technology Stack

- PyQt5: User interface
- cryptography: Secure password encryption
- Windows Registry API: Riot client integration
