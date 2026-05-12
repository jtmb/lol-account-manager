"""Encryption utilities for secure password storage"""
import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from cryptography.hazmat.backends import default_backend
from typing import Tuple
import json


class PasswordEncryption:
    """Handle AES-256 encryption of passwords using a master password"""
    
    def __init__(self, master_password: str):
        """
        Initialize encryption with a master password
        
        Args:
            master_password: The master password to use for encryption
        """
        self.master_password = master_password
        self.cipher = self._create_cipher()
    
    def _create_cipher(self) -> Fernet:
        """Create a Fernet cipher from the master password"""
        # Derive a key from the master password
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'LoL_Account_Manager_Salt_v1',  # Fixed salt for consistency
            iterations=100000,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(
            kdf.derive(self.master_password.encode())
        )
        return Fernet(key)
    
    def encrypt_password(self, password: str) -> str:
        """
        Encrypt a password
        
        Args:
            password: Plain text password to encrypt
            
        Returns:
            Base64 encoded encrypted password
        """
        encrypted = self.cipher.encrypt(password.encode())
        return base64.b64encode(encrypted).decode()
    
    def decrypt_password(self, encrypted_password: str) -> str:
        """
        Decrypt a password
        
        Args:
            encrypted_password: Base64 encoded encrypted password
            
        Returns:
            Plain text password
        """
        encrypted = base64.b64decode(encrypted_password.encode())
        decrypted = self.cipher.decrypt(encrypted)
        return decrypted.decode()
    
    @staticmethod
    def hash_master_password(password: str) -> str:
        """
        Hash master password for verification
        
        Args:
            password: Master password to hash
            
        Returns:
            Base64 encoded hash
        """
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'LoL_Master_Password_Hash_Salt',
            iterations=100000,
            backend=default_backend()
        )
        hashed = base64.b64encode(kdf.derive(password.encode()))
        return hashed.decode()
    
    @staticmethod
    def verify_master_password(password: str, stored_hash: str) -> bool:
        """
        Verify a master password against a stored hash
        
        Args:
            password: Master password to verify
            stored_hash: Stored hash to compare against
            
        Returns:
            True if password matches, False otherwise
        """
        return PasswordEncryption.hash_master_password(password) == stored_hash
