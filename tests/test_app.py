"""Test suite for the account manager."""
import shutil
import tempfile
import unittest
from pathlib import Path

from src.core import account_manager as account_manager_module
from src.core.account_manager import AccountManager
from src.security.encryption import PasswordEncryption


class TestPasswordEncryption(unittest.TestCase):
    """Test encryption functionality."""

    def setUp(self):
        self.master_password = "test_password_123"
        self.encryption = PasswordEncryption(self.master_password)

    def test_encrypt_decrypt(self):
        """Test that encryption and decryption work correctly."""
        original = "my_secret_password"
        encrypted = self.encryption.encrypt_password(original)
        decrypted = self.encryption.decrypt_password(encrypted)
        self.assertEqual(original, decrypted)

    def test_different_passwords_different_encrypted(self):
        """Test that same password encrypted twice gives different results."""
        password = "test_password"
        encrypted1 = self.encryption.encrypt_password(password)
        encrypted2 = self.encryption.encrypt_password(password)
        self.assertNotEqual(encrypted1, encrypted2)

    def test_wrong_password_decryption_fails(self):
        """Test that decrypting with wrong password fails."""
        encrypted = self.encryption.encrypt_password("correct_password")
        wrong_encryption = PasswordEncryption("wrong_password")
        with self.assertRaises(Exception):
            wrong_encryption.decrypt_password(encrypted)

    def test_master_password_hashing(self):
        """Test master password hashing."""
        password = "my_master_password"
        hash1 = PasswordEncryption.hash_master_password(password)
        hash2 = PasswordEncryption.hash_master_password(password)
        self.assertEqual(hash1, hash2)

    def test_master_password_verification(self):
        """Test master password verification."""
        password = "my_master_password"
        hashed = PasswordEncryption.hash_master_password(password)
        self.assertTrue(PasswordEncryption.verify_master_password(password, hashed))
        self.assertFalse(PasswordEncryption.verify_master_password("wrong_password", hashed))


class TestAccountManager(unittest.TestCase):
    """Test account manager functionality."""

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())

        self.original_accounts_file = account_manager_module.ACCOUNTS_FILE
        self.original_master_password_file = account_manager_module.MASTER_PASSWORD_FILE

        account_manager_module.ACCOUNTS_FILE = self.test_dir / "accounts.json"
        account_manager_module.MASTER_PASSWORD_FILE = self.test_dir / "master.key"

        self.master_password = "test_master_123"
        self.manager = AccountManager(self.master_password)

    def tearDown(self):
        account_manager_module.ACCOUNTS_FILE = self.original_accounts_file
        account_manager_module.MASTER_PASSWORD_FILE = self.original_master_password_file
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_add_account(self):
        """Test adding an account."""
        account = self.manager.add_account(
            "test_user",
            "test_password",
            "Test Account",
        )
        self.assertEqual(account.username, "test_user")
        self.assertEqual(account.password, "test_password")
        self.assertEqual(account.display_name, "Test Account")
        self.assertEqual(account.ban_status, "none")

    def test_add_account_with_ban_metadata(self):
        """Test adding an account with ban details."""
        account = self.manager.add_account(
            "banned_user",
            "test_password",
            "Ranked Alt",
            ban_status="temporary",
            ban_end_date="2030-01-01",
        )
        self.assertEqual(account.ban_status, "temporary")
        self.assertEqual(account.ban_end_date, "2030-01-01")
        self.assertTrue(account.is_banned())

    def test_duplicate_account_error(self):
        """Test that duplicate accounts can't be added."""
        self.manager.add_account("test_user", "password")
        with self.assertRaises(ValueError):
            self.manager.add_account("test_user", "another_password")

    def test_get_account(self):
        """Test retrieving an account."""
        self.manager.add_account("user1", "pass1", "User One")
        account = self.manager.get_account("user1")
        self.assertIsNotNone(account)
        self.assertEqual(account.display_name, "User One")

    def test_delete_account(self):
        """Test deleting an account."""
        self.manager.add_account("user1", "pass1")
        self.manager.add_account("user2", "pass2")
        self.manager.delete_account("user1")

        accounts = self.manager.get_all_accounts()
        self.assertEqual(len(accounts), 1)
        self.assertEqual(accounts[0].username, "user2")

    def test_update_account(self):
        """Test updating an account."""
        self.manager.add_account("user1", "pass1", "Original")
        self.manager.update_account(
            "user1",
            password="new_pass",
            display_name="Updated",
            ban_status="permanent",
        )

        account = self.manager.get_account("user1")
        self.assertEqual(account.password, "new_pass")
        self.assertEqual(account.display_name, "Updated")
        self.assertEqual(account.ban_status, "permanent")
        self.assertTrue(account.is_banned())

    def test_persistence(self):
        """Test that accounts persist across instances."""
        self.manager.add_account("user1", "pass1", "User One")
        self.manager.add_account("user2", "pass2", "User Two")

        manager2 = AccountManager(self.master_password)
        accounts = manager2.get_all_accounts()

        self.assertEqual(len(accounts), 2)
        usernames = [a.username for a in accounts]
        self.assertIn("user1", usernames)
        self.assertIn("user2", usernames)

    def test_export_and_import_backup(self):
        """Test exporting and importing accounts through backup file."""
        backup_file = self.test_dir / "backup.lolbak"

        self.manager.add_account(
            "user1",
            "pass1",
            "User One",
            ban_status="temporary",
            ban_end_date="2030-01-01",
        )
        self.manager.export_to_file(str(backup_file))

        restored = AccountManager(self.master_password)
        restored.delete_account("user1")

        imported_count = restored.import_from_file(
            str(backup_file),
            self.master_password,
            merge=True,
        )

        self.assertEqual(imported_count, 1)
        imported = restored.get_account("user1")
        self.assertIsNotNone(imported)
        self.assertEqual(imported.ban_status, "temporary")
        self.assertEqual(imported.ban_end_date, "2030-01-01")

    def test_expired_temporary_ban_is_auto_cleared(self):
        """Temporary bans should clear once the end date is in the past."""
        self.manager.add_account(
            "expired_user",
            "pass1",
            "Expired",
            ban_status="temporary",
            ban_end_date="2000-01-01",
        )

        account = self.manager.get_account("expired_user")
        self.assertIsNotNone(account)
        self.assertEqual(account.ban_status, "none")
        self.assertEqual(account.ban_end_date, "")


if __name__ == "__main__":
    unittest.main()