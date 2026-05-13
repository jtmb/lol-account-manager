"""Account management and storage"""
import json
import os
from datetime import datetime
from datetime import date
from dataclasses import dataclass, asdict, fields, field
from typing import List, Dict, Optional
from pathlib import Path
from src.config.paths import (
    ACCOUNTS_FILE,
    MASTER_PASSWORD_FILE,
    BACKUPS_DIR,
    ensure_app_data_dir,
    load_settings,
)
from src.security.encryption import PasswordEncryption


@dataclass
class Account:
    """Represents a League of Legends account"""
    username: str
    password: str  # Will be encrypted in storage
    display_name: str = ""
    is_encrypted: bool = True
    region: str = "NA"
    tag_line: str = "NA1"
    tags: List[str] = field(default_factory=list)
    notes: str = ""
    ban_status: str = "none"   # "none", "temporary", "permanent"
    ban_end_date: str = ""     # ISO date "YYYY-MM-DD", only for temporary bans

    def is_banned(self) -> bool:
        """Return True if the account is currently under an active ban."""
        if self.ban_status == "permanent":
            return True
        if self.ban_status == "temporary" and self.ban_end_date:
            from datetime import date
            try:
                # Ban is active strictly before end date; on the end date it is considered lifted.
                return date.today() < date.fromisoformat(self.ban_end_date)
            except ValueError:
                return False
        return False

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)


class AccountManager:
    """Manage saving and loading of LoL accounts"""
    
    def __init__(self, master_password: Optional[str] = None):
        """
        Initialize account manager
        
        Args:
            master_password: Master password for encryption/decryption
        """
        ensure_app_data_dir()
        self.master_password = master_password
        self.encryption = None
        if master_password:
            self.encryption = PasswordEncryption(master_password)
        self.accounts: List[Account] = []
        if self.master_password:
            self.load_accounts()
    
    def save_accounts(self):
        """Save accounts to file with encryption"""
        if not self.encryption:
            raise RuntimeError("Encryption not initialized. Set master password first.")
        
        ensure_app_data_dir()
        
        # Encrypt passwords
        encrypted_accounts = []
        for account in self.accounts:
            account_dict = account.to_dict()
            account_dict['password'] = self.encryption.encrypt_password(account.password)
            notes_value = str(account_dict.get('notes', '') or '')
            account_dict['notes'] = self.encryption.encrypt_password(notes_value)
            account_dict['notes_encrypted'] = True
            encrypted_accounts.append(account_dict)

        self._create_auto_backup(encrypted_accounts)
        
        # Write to file
        with open(ACCOUNTS_FILE, 'w') as f:
            json.dump(encrypted_accounts, f, indent=2)
    
    def load_accounts(self):
        """Load accounts from file and decrypt passwords"""
        if not self.encryption:
            raise RuntimeError("Encryption not initialized. Set master password first.")
        
        if not ACCOUNTS_FILE.exists():
            self.accounts = []
            return
        
        try:
            with open(ACCOUNTS_FILE, 'r') as f:
                account_dicts = json.load(f)
            
            self.accounts = []
            for account_dict in account_dicts:
                try:
                    d = dict(account_dict)
                    # Decrypt password
                    encrypted_password = d['password']
                    decrypted_password = self.encryption.decrypt_password(encrypted_password)
                    d['password'] = decrypted_password

                    # Support both encrypted and legacy plaintext notes.
                    notes_value = str(d.get('notes', '') or '')
                    if d.get('notes_encrypted') and notes_value:
                        try:
                            notes_value = self.encryption.decrypt_password(notes_value)
                        except Exception:
                            notes_value = ""
                    d['notes'] = notes_value

                    # Strip unknown keys so schema changes remain backward compatible.
                    valid_fields = {f.name for f in fields(Account)}
                    d = {k: v for k, v in d.items() if k in valid_fields}
                    account = Account(**d)
                    self.accounts.append(account)
                except Exception as e:
                    print(f"Error loading account {account_dict.get('username', 'unknown')}: {e}")
            if self._clear_expired_temporary_bans():
                self.save_accounts()
        except Exception as e:
            print(f"Error loading accounts: {e}")
            self.accounts = []

    def _clear_expired_temporary_bans(self) -> bool:
        """Clear temporary ban metadata once the end date has passed."""
        changed = False
        today = date.today()
        for account in self.accounts:
            if account.ban_status == "temporary" and account.ban_end_date:
                try:
                    end = date.fromisoformat(account.ban_end_date)
                except ValueError:
                    continue
                # Clear once the configured date is reached.
                if today >= end:
                    account.ban_status = "none"
                    account.ban_end_date = ""
                    changed = True
        return changed
    
    def add_account(
        self,
        username: str,
        password: str,
        display_name: str = "",
        region: str = "NA",
        tag_line: str = "NA1",
        tags: Optional[List[str]] = None,
        notes: str = "",
        ban_status: str = "none",
        ban_end_date: str = "",
    ) -> Account:
        """Add a new account"""
        if not display_name:
            display_name = username

        # Check if account already exists
        if self.account_exists(username):
            raise ValueError(f"Account with username '{username}' already exists")

        account = Account(
            username=username,
            password=password,
            display_name=display_name,
            region=region,
            tag_line=tag_line,
            tags=list(tags or []),
            notes=notes or "",
            ban_status=ban_status,
            ban_end_date=ban_end_date,
        )
        self.accounts.append(account)
        self.save_accounts()
        return account
    
    def delete_account(self, username: str):
        """Delete an account"""
        self.accounts = [acc for acc in self.accounts if acc.username != username]
        self.save_accounts()
    
    def update_account(
        self,
        username: str,
        new_username: Optional[str] = None,
        password: Optional[str] = None,
        display_name: Optional[str] = None,
        region: Optional[str] = None,
        tag_line: Optional[str] = None,
        tags: Optional[List[str]] = None,
        notes: Optional[str] = None,
        ban_status: Optional[str] = None,
        ban_end_date: Optional[str] = None,
    ):
        """Update an account's username, password, or display name."""
        for account in self.accounts:
            if account.username == username:
                if new_username is not None and new_username != username:
                    if self.account_exists(new_username):
                        raise ValueError(f"Account with username '{new_username}' already exists")
                    account.username = new_username
                if password is not None:
                    account.password = password
                if display_name is not None:
                    account.display_name = display_name
                if region is not None:
                    account.region = region
                if tag_line is not None:
                    account.tag_line = tag_line
                if tags is not None:
                    account.tags = list(tags)
                if notes is not None:
                    account.notes = notes
                if ban_status is not None:
                    account.ban_status = ban_status
                if ban_end_date is not None:
                    account.ban_end_date = ban_end_date
                self.save_accounts()
                return account
        raise ValueError(f"Account '{username}' not found")
    
    def get_account(self, username: str) -> Optional[Account]:
        """Get an account by username"""
        if self._clear_expired_temporary_bans():
            self.save_accounts()
        for account in self.accounts:
            if account.username == username:
                return account
        return None
    
    def account_exists(self, username: str) -> bool:
        """Check if an account exists"""
        return any(acc.username == username for acc in self.accounts)
    
    def get_all_accounts(self) -> List[Account]:
        """Get all accounts"""
        if self._clear_expired_temporary_bans():
            self.save_accounts()
        return self.accounts.copy()

    def export_to_file(self, file_path: str):
        """Export accounts to a backup file encrypted with the current master password."""
        if not self.encryption:
            raise RuntimeError("Encryption not initialized.")

        encrypted_accounts = []
        for account in self.accounts:
            account_dict = account.to_dict()
            account_dict['password'] = self.encryption.encrypt_password(account.password)
            notes_value = str(account_dict.get('notes', '') or '')
            account_dict['notes'] = self.encryption.encrypt_password(notes_value)
            account_dict['notes_encrypted'] = True
            encrypted_accounts.append(account_dict)

        backup = {
            "version": 1,
            "app": "LoLAccountManager",
            "accounts": encrypted_accounts,
        }

        with open(file_path, 'w') as f:
            json.dump(backup, f, indent=2)

    def import_from_file(self, file_path: str, source_password: str, merge: bool = True) -> int:
        """Import accounts from a backup file.

        Args:
            file_path: Path to the backup file.
            source_password: Master password that was active when the backup was created.
            merge: If True, skip accounts that already exist. If False, replace all accounts.

        Returns:
            Number of accounts successfully imported.
        """
        source_encryption = PasswordEncryption(source_password)

        with open(file_path, 'r') as f:
            data = json.load(f)

        # Support both a versioned backup dict and a raw list (plain accounts.json copy)
        if isinstance(data, list):
            account_dicts = data
        else:
            if data.get('app') != 'LoLAccountManager':
                raise ValueError("This file does not appear to be a valid LoL Account Manager backup.")
            account_dicts = data.get('accounts', [])

        imported: List[Account] = []
        for account_dict in account_dicts:
            try:
                d = dict(account_dict)
                d['password'] = source_encryption.decrypt_password(d['password'])

                notes_value = str(d.get('notes', '') or '')
                if d.get('notes_encrypted') and notes_value:
                    try:
                        notes_value = source_encryption.decrypt_password(notes_value)
                    except Exception:
                        notes_value = ""
                d['notes'] = notes_value

                # Strip unknown keys so Account(**d) doesn't fail on future schema changes
                valid_fields = {f.name for f in fields(Account)}
                d = {k: v for k, v in d.items() if k in valid_fields}
                imported.append(Account(**d))
            except Exception as e:
                print(f"Skipping account '{account_dict.get('username', 'unknown')}': {e}")

        if not merge:
            self.accounts = []

        count = 0
        for account in imported:
            if not self.account_exists(account.username):
                self.accounts.append(account)
                count += 1

        self.save_accounts()
        return count

    def _create_auto_backup(self, encrypted_accounts: List[Dict]):
        """Write a versioned automatic backup if enabled in settings."""
        settings = load_settings()
        if not bool(settings.get('auto_backup_enabled', True)):
            return

        keep_count = int(settings.get('auto_backup_keep_count', 20) or 20)
        keep_count = max(1, min(200, keep_count))

        ensure_app_data_dir()
        ts = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        backup_file = BACKUPS_DIR / f"auto_backup_{ts}.lolbak"

        payload = {
            "version": 1,
            "app": "LoLAccountManager",
            "kind": "auto",
            "created_at": datetime.now().isoformat(timespec='seconds'),
            "accounts": encrypted_accounts,
        }

        with open(backup_file, 'w') as f:
            json.dump(payload, f, indent=2)

        backup_files = sorted(BACKUPS_DIR.glob('auto_backup_*.lolbak'))
        while len(backup_files) > keep_count:
            oldest = backup_files.pop(0)
            try:
                oldest.unlink()
            except OSError:
                pass

    @staticmethod
    def master_password_set() -> bool:
        """Check if master password is set"""
        return MASTER_PASSWORD_FILE.exists()
    
    @staticmethod
    def set_master_password(password: str):
        """Set a new master password"""
        ensure_app_data_dir()
        hashed = PasswordEncryption.hash_master_password(password)
        with open(MASTER_PASSWORD_FILE, 'w') as f:
            f.write(hashed)
    
    @staticmethod
    def verify_master_password(password: str) -> bool:
        """Verify master password"""
        if not MASTER_PASSWORD_FILE.exists():
            return False
        
        with open(MASTER_PASSWORD_FILE, 'r') as f:
            stored_hash = f.read()
        
        return PasswordEncryption.verify_master_password(password, stored_hash)
