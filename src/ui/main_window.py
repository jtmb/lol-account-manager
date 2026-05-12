"""Main application window"""
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QListWidget, QListWidgetItem, QLabel, QDialog, QLineEdit,
    QMessageBox, QFrame, QFileDialog
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt5.QtGui import QFont
from pathlib import Path
from typing import Optional
import sys
import time

from src.core.account_manager import AccountManager, Account
from src.core.riot_integration import RiotClientIntegration
from src.security.encryption import PasswordEncryption
from src.config.paths import get_lol_executable, set_custom_lol_exe


class LoginThread(QThread):
    """Background thread for login and launch"""
    finished = pyqtSignal(bool)
    error = pyqtSignal(str)
    
    def __init__(self, username: str, password: str, auto_launch_lol: bool = True):
        super().__init__()
        self.username = username
        self.password = password
        self.auto_launch_lol = auto_launch_lol
    
    def run(self):
        try:
            success = RiotClientIntegration.login_and_launch(
                self.username, 
                self.password,
                launch_lol=self.auto_launch_lol
            )
            self.finished.emit(success)
        except Exception as e:
            self.error.emit(str(e))


class MasterPasswordDialog(QDialog):
    """Dialog for setting/entering master password"""
    
    def __init__(self, parent=None, is_setup=False):
        super().__init__(parent)
        self.is_setup = is_setup
        self.password = None
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("Master Password" if not self.is_setup else "Set Master Password")
        self.setModal(True)
        self.setMinimumWidth(350)
        
        layout = QVBoxLayout()
        
        if self.is_setup:
            label = QLabel("Set a master password to protect your credentials:")
            layout.addWidget(label)
        else:
            label = QLabel("Enter your master password:")
            layout.addWidget(label)
        
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password_input)
        
        if self.is_setup:
            confirm_label = QLabel("Confirm password:")
            layout.addWidget(confirm_label)
            
            self.confirm_input = QLineEdit()
            self.confirm_input.setEchoMode(QLineEdit.Password)
            layout.addWidget(self.confirm_input)
        
        button_layout = QHBoxLayout()
        
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        button_layout.addWidget(ok_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def get_password(self):
        if self.is_setup:
            if self.password_input.text() != self.confirm_input.text():
                QMessageBox.warning(self, "Error", "Passwords do not match!")
                return None
            if len(self.password_input.text()) < 4:
                QMessageBox.warning(self, "Error", "Password must be at least 4 characters!")
                return None
        return self.password_input.text()


class AddAccountDialog(QDialog):
    """Dialog for adding a new account"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.account = None
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("Add Account")
        self.setModal(True)
        self.setMinimumWidth(350)
        
        layout = QVBoxLayout()
        
        # Username
        layout.addWidget(QLabel("Username (or Email):"))
        self.username_input = QLineEdit()
        layout.addWidget(self.username_input)
        
        # Password
        layout.addWidget(QLabel("Password:"))
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password_input)
        
        # Display Name (optional)
        layout.addWidget(QLabel("Display Name (optional):"))
        self.display_name_input = QLineEdit()
        layout.addWidget(self.display_name_input)
        
        button_layout = QHBoxLayout()
        
        add_btn = QPushButton("Add Account")
        add_btn.clicked.connect(self.validate_and_accept)
        button_layout.addWidget(add_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def validate_and_accept(self):
        if not self.username_input.text().strip():
            QMessageBox.warning(self, "Error", "Please enter a username!")
            return
        if not self.password_input.text():
            QMessageBox.warning(self, "Error", "Please enter a password!")
            return
        self.accept()
    
    def get_data(self):
        return {
            'username': self.username_input.text().strip(),
            'password': self.password_input.text(),
            'display_name': self.display_name_input.text().strip() or self.username_input.text().strip()
        }


class AccountListItem(QFrame):
    """Custom widget for displaying account in list"""
    
    def __init__(self, account: Account, parent=None):
        super().__init__(parent)
        self.account = account
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 5, 10, 5)
        
        name_font = QFont()
        name_font.setBold(True)
        name_font.setPointSize(11)
        
        name_label = QLabel(self.account.display_name)
        name_label.setFont(name_font)
        layout.addWidget(name_label)
        
        username_label = QLabel(f"@{self.account.username}")
        username_label.setStyleSheet("color: #666666;")
        layout.addWidget(username_label)
        
        self.setLayout(layout)


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.account_manager: Optional[AccountManager] = None
        self.init_ui()
        self.check_master_password()
    
    def init_ui(self):
        self.setWindowTitle("League of Legends Account Manager")
        self.setMinimumSize(500, 400)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Title
        title = QLabel("Account Manager")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Account list
        layout.addWidget(QLabel("Saved Accounts:"))
        self.account_list = QListWidget()
        self.account_list.itemClicked.connect(self.on_account_selected)
        layout.addWidget(self.account_list)
        
        # Button layout
        button_layout = QHBoxLayout()
        
        self.launch_btn = QPushButton("Launch Selected Account")
        self.launch_btn.clicked.connect(self.launch_account)
        self.launch_btn.setEnabled(False)
        button_layout.addWidget(self.launch_btn)
        
        self.add_btn = QPushButton("+ Add Account")
        self.add_btn.clicked.connect(self.add_account)
        button_layout.addWidget(self.add_btn)
        
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.clicked.connect(self.delete_account)
        self.delete_btn.setEnabled(False)
        button_layout.addWidget(self.delete_btn)
        
        layout.addLayout(button_layout)
        
        # Settings
        settings_layout = QHBoxLayout()
        self.master_password_btn = QPushButton("Change Master Password")
        self.master_password_btn.clicked.connect(self.change_master_password)
        settings_layout.addWidget(self.master_password_btn)

        self.browse_lol_btn = QPushButton("Set LoL Path...")
        self.browse_lol_btn.setToolTip("Browse for LeagueClient.exe if auto-detection fails")
        self.browse_lol_btn.clicked.connect(self.browse_for_lol)
        settings_layout.addWidget(self.browse_lol_btn)

        settings_layout.addStretch()
        layout.addLayout(settings_layout)
        
        central_widget.setLayout(layout)
    
    def check_master_password(self):
        """Check if master password is set, if not show setup dialog"""
        if not AccountManager.master_password_set():
            dialog = MasterPasswordDialog(self, is_setup=True)
            if dialog.exec_() == QDialog.Accepted:
                password = dialog.get_password()
                if password:
                    AccountManager.set_master_password(password)
                    self.initialize_account_manager(password)
            else:
                QMessageBox.critical(self, "Error", "Master password is required to use this application.")
                sys.exit(1)
        else:
            # Ask for master password
            self.request_master_password()
    
    def request_master_password(self):
        """Request master password from user"""
        for attempt in range(3):
            dialog = MasterPasswordDialog(self, is_setup=False)
            if dialog.exec_() == QDialog.Accepted:
                password = dialog.password_input.text()
                if AccountManager.verify_master_password(password):
                    self.initialize_account_manager(password)
                    return
                else:
                    remaining = 3 - attempt - 1
                    if remaining > 0:
                        QMessageBox.warning(
                            self, 
                            "Error", 
                            f"Incorrect password. {remaining} attempts remaining."
                        )
                    else:
                        QMessageBox.critical(self, "Error", "Too many failed attempts.")
                        sys.exit(1)
            else:
                sys.exit(1)
    
    def initialize_account_manager(self, password: str):
        """Initialize account manager with master password"""
        self.account_manager = AccountManager(password)
        self.refresh_account_list()
    
    def refresh_account_list(self):
        """Refresh the account list display"""
        self.account_list.clear()
        
        if not self.account_manager:
            return
        
        accounts = self.account_manager.get_all_accounts()
        
        if not accounts:
            item = QListWidgetItem()
            item.setText("No accounts saved. Click 'Add Account' to get started.")
            item.setFlags(item.flags() & ~Qt.ItemIsSelectable)
            self.account_list.addItem(item)
            self.launch_btn.setEnabled(False)
            self.delete_btn.setEnabled(False)
        else:
            for account in accounts:
                item = QListWidgetItem()
                item.setData(Qt.UserRole, account.username)
                item.setSizeHint(QSize(0, 60))
                self.account_list.addItem(item)
                
                # Create custom widget
                widget = AccountListItem(account)
                self.account_list.setItemWidget(item, widget)
    
    def on_account_selected(self):
        """Handle account selection"""
        selected = self.account_list.currentItem()
        if selected:
            username = selected.data(Qt.UserRole)
            self.launch_btn.setEnabled(username is not None)
            self.delete_btn.setEnabled(username is not None)
    
    def add_account(self):
        """Add a new account"""
        if not self.account_manager:
            return
        
        dialog = AddAccountDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            
            try:
                self.account_manager.add_account(
                    data['username'],
                    data['password'],
                    data['display_name']
                )
                self.refresh_account_list()
                QMessageBox.information(self, "Success", "Account added successfully!")
            except ValueError as e:
                self._show_error("Error", str(e))
            except Exception as e:
                self._show_error("Error", f"Failed to add account: {str(e)}")
    
    def delete_account(self):
        """Delete selected account"""
        if not self.account_manager:
            return
        
        selected = self.account_list.currentItem()
        if not selected:
            return
        
        username = selected.data(Qt.UserRole)
        account = self.account_manager.get_account(username)
        
        if not account:
            return
        
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete '{account.display_name}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                self.account_manager.delete_account(username)
                self.refresh_account_list()
                QMessageBox.information(self, "Success", "Account deleted successfully!")
            except Exception as e:
                self._show_error("Error", f"Failed to delete account: {str(e)}")
    
    def launch_account(self):
        """Launch selected account"""
        if not self.account_manager:
            return
        
        selected = self.account_list.currentItem()
        if not selected:
            return
        
        username = selected.data(Qt.UserRole)
        account = self.account_manager.get_account(username)
        
        if not account:
            return
        
        # Show progress dialog
        progress = QMessageBox(self)
        progress.setWindowTitle("Launching...")
        progress.setText(f"Starting League of Legends for {account.display_name}...")
        progress.setStandardButtons(QMessageBox.NoButton)
        progress.show()
        
        # Launch in background thread
        self.login_thread = LoginThread(
            account.username,
            account.password,
            auto_launch_lol=True
        )
        self.login_thread.finished.connect(
            lambda success: self.on_launch_finished(success, progress)
        )
        self.login_thread.error.connect(
            lambda error: self.on_launch_error(error, progress)
        )
        self.login_thread.start()
    
    def on_launch_finished(self, success, progress_dialog):
        """Handle launch completion"""
        progress_dialog.close()
        
        if success:
            QMessageBox.information(
                self,
                "Success",
                "Riot Client launched! Complete the login if needed and League of Legends will start."
            )
        else:
            self._show_error("Error", "Failed to launch. Make sure League of Legends is installed.")
    
    def on_launch_error(self, error, progress_dialog):
        """Handle launch error"""
        progress_dialog.close()
        self._show_error("Error", f"Launch failed: {error}")
    
    def change_master_password(self):
        """Change master password"""
        # First verify current password
        verify_dialog = MasterPasswordDialog(self, is_setup=False)
        verify_dialog.setWindowTitle("Verify Current Password")
        if verify_dialog.exec_() == QDialog.Accepted:
            password = verify_dialog.password_input.text()
            if AccountManager.verify_master_password(password):
                # Now set new password
                new_pass_dialog = MasterPasswordDialog(self, is_setup=True)
                new_pass_dialog.setWindowTitle("Set New Master Password")
                if new_pass_dialog.exec_() == QDialog.Accepted:
                    new_password = new_pass_dialog.get_password()
                    if new_password:
                        # Re-encrypt all accounts with new password
                        try:
                            old_accounts = self.account_manager.get_all_accounts()
                            AccountManager.set_master_password(new_password)
                            self.initialize_account_manager(new_password)
                            
                            # Re-add all accounts with new encryption
                            for account in old_accounts:
                                self.account_manager.add_account(
                                    account.username,
                                    account.password,
                                    account.display_name
                                )
                            
                            QMessageBox.information(self, "Success", "Master password updated!")
                        except Exception as e:
                            QMessageBox.critical(self, "Error", f"Failed to update password: {str(e)}")
            else:
                self._show_error("Error", "Incorrect password!")

    def browse_for_lol(self):
        """Let the user manually locate LeagueClient.exe."""
        current = get_lol_executable()
        start_dir = str(current.parent) if current else "C:\\"
        exe_path, _ = QFileDialog.getOpenFileName(
            self,
            "Locate LeagueClient.exe",
            start_dir,
            "Executable (*.exe);;All files (*)"
        )
        if exe_path:
            from pathlib import Path
            p = Path(exe_path)
            if p.name.lower() not in ('leagueclient.exe', 'league of legends.exe'):
                QMessageBox.warning(
                    self, "Unexpected file",
                    f"Expected LeagueClient.exe but got '{p.name}'.\n"
                    "Saving anyway — update if launch fails."
                )
            set_custom_lol_exe(p)
            QMessageBox.information(
                self, "LoL Path Saved",
                f"League of Legends path set to:\n{exe_path}"
            )

    def _show_error(self, title: str, message: str, icon=QMessageBox.Critical):
        """Show an error dialog with selectable/copyable text."""
        msg = QMessageBox(self)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.setIcon(icon)
        msg.setStandardButtons(QMessageBox.Ok)
        for label in msg.findChildren(QLabel):
            label.setTextInteractionFlags(
                Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard
            )
        msg.exec_()
