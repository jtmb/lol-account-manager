"""Test suite for the account manager"""
import unittest
import tempfile
import os
from pathlib import Path
from src.security.encryption import PasswordEncryption
from src.core.account_manager import AccountManager, Account


class TestPasswordEncryption(unittest.TestCase):
    """Test encryption functionality"""
    
    def setUp(self):
        self.master_password = "test_password_123"
        self.encryption = PasswordEncryption(self.master_password)
    
    def test_encrypt_decrypt(self):
        """Test that encryption and decryption work correctly"""
        original = "my_secret_password"
        encrypted = self.encryption.encrypt_password(original)
        decrypted = self.encryption.decrypt_password(encrypted)
        self.assertEqual(original, decrypted)
    
    def test_different_passwords_different_encrypted(self):
        """Test that same password encrypted twice gives different results"""
        password = "test_password"
        encrypted1 = self.encryption.encrypt_password(password)
        encrypted2 = self.encryption.encrypt_password(password)
        # Fernet includes timestamp, so they should be different
        self.assertNotEqual(encrypted1, encrypted2)
    
    def test_wrong_password_decryption_fails(self):
        """Test that decrypting with wrong password fails"""
        encrypted = self.encryption.encrypt_password("correct_password")
        wrong_encryption = PasswordEncryption("wrong_password")
        with self.assertRaises(Exception):
            wrong_encryption.decrypt_password(encrypted)
    
    def test_master_password_hashing(self):
        """Test master password hashing"""
        password = "my_master_password"
        hash1 = PasswordEncryption.hash_master_password(password)
        hash2 = PasswordEncryption.hash_master_password(password)
        # Same password should give same hash
        self.assertEqual(hash1, hash2)
    
    def test_master_password_verification(self):
        """Test master password verification"""
        password = "my_master_password"
        hashed = PasswordEncryption.hash_master_password(password)
        self.assertTrue(PasswordEncryption.verify_master_password(password, hashed))
        self.assertFalse(PasswordEncryption.verify_master_password("wrong_password", hashed))


class TestAccountManager(unittest.TestCase):
    """Test account manager functionality"""
    
    def setUp(self):
        # Create temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        self.original_appdata = os.getenv('APPDATA')
        
        # Mock paths
        from src.config import paths
        paths.APP_DATA_DIR = Path(self.test_dir)
        paths.ACCOUNTS_FILE = Path(self.test_dir) / 'accounts.json'
        paths.MASTER_PASSWORD_FILE = Path(self.test_dir) / 'master.key'
        
        self.master_password = "test_master_123"
        self.manager = AccountManager(self.master_password)
    
    def tearDown(self):
        # Clean up
        import shutil
        if Path(self.test_dir).exists():
            shutil.rmtree(self.test_dir)
    
    def test_add_account(self):
        """Test adding an account"""
        account = self.manager.add_account(
            "test_user",
            "test_password",
            "Test Account"
        )
        self.assertEqual(account.username, "test_user")
        self.assertEqual(account.password, "test_password")
        self.assertEqual(account.display_name, "Test Account")
    
    def test_duplicate_account_error(self):
        """Test that duplicate accounts can't be added"""
        self.manager.add_account("test_user", "password")
        with self.assertRaises(ValueError):
            self.manager.add_account("test_user", "another_password")
    
    def test_get_account(self):
        """Test retrieving an account"""
        self.manager.add_account("user1", "pass1", "User One")
        account = self.manager.get_account("user1")
        self.assertIsNotNone(account)
        self.assertEqual(account.display_name, "User One")
    
    def test_delete_account(self):
        """Test deleting an account"""
        self.manager.add_account("user1", "pass1")
        self.manager.add_account("user2", "pass2")
        self.manager.delete_account("user1")
        
        accounts = self.manager.get_all_accounts()
        self.assertEqual(len(accounts), 1)
        self.assertEqual(accounts[0].username, "user2")
    
    def test_update_account(self):
        """Test updating an account"""
        self.manager.add_account("user1", "pass1", "Original")
        self.manager.update_account("user1", password="new_pass", display_name="Updated")
        
        account = self.manager.get_account("user1")
        self.assertEqual(account.password, "new_pass")
        self.assertEqual(account.display_name, "Updated")
    
    def test_persistence(self):
        """Test that accounts persist across instances"""
        self.manager.add_account("user1", "pass1", "User One")
        self.manager.add_account("user2", "pass2", "User Two")
        
        # Create new manager with same password
        manager2 = AccountManager(self.master_password)
        accounts = manager2.get_all_accounts()
        
        self.assertEqual(len(accounts), 2)
        usernames = [a.username for a in accounts]
        self.assertIn("user1", usernames)
        self.assertIn("user2", usernames)


if __name__ == '__main__':
    unittest.main()
