"""Account management and storage"""
import json
import os
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
from src.config.paths import ACCOUNTS_FILE, MASTER_PASSWORD_FILE, ensure_app_data_dir
from src.security.encryption import PasswordEncryption


@dataclass
class Account:
    """Represents a League of Legends account"""
    username: str
    password: str  # Will be encrypted in storage
    display_name: str = ""
    is_encrypted: bool = True
    ban_status: str = "none"   # "none", "temporary", "permanent"
    ban_end_date: str = ""     # ISO date "YYYY-MM-DD", only for temporary bans

    def is_banned(self) -> bool:
        """Return True if the account is currently under an active ban."""
        if self.ban_status == "permanent":
            return True
        if self.ban_status == "temporary" and self.ban_end_date:
            from datetime import date
            try:
                return date.today() <= date.fromisoformat(self.ban_end_date)
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
            encrypted_accounts.append(account_dict)
        
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
                    # Decrypt password
                    encrypted_password = account_dict['password']
                    decrypted_password = self.encryption.decrypt_password(encrypted_password)
                    account_dict['password'] = decrypted_password
                    account = Account(**account_dict)
                    self.accounts.append(account)
                except Exception as e:
                    print(f"Error loading account {account_dict.get('username', 'unknown')}: {e}")
        except Exception as e:
            print(f"Error loading accounts: {e}")
            self.accounts = []
    
    def add_account(
        self,
        username: str,
        password: str,
        display_name: str = "",
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
                if ban_status is not None:
                    account.ban_status = ban_status
                if ban_end_date is not None:
                    account.ban_end_date = ban_end_date
                self.save_accounts()
                return account
        raise ValueError(f"Account '{username}' not found")
    
    def get_account(self, username: str) -> Optional[Account]:
        """Get an account by username"""
        for account in self.accounts:
            if account.username == username:
                return account
        return None
    
    def account_exists(self, username: str) -> bool:
        """Check if an account exists"""
        return any(acc.username == username for acc in self.accounts)
    
    def get_all_accounts(self) -> List[Account]:
        """Get all accounts"""
        return self.accounts.copy()
    
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
