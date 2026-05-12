"""Main application window"""
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QListWidget, QListWidgetItem, QLabel, QDialog, QLineEdit,
    QMessageBox, QFrame, QFileDialog, QProgressDialog, QComboBox,
    QDateEdit, QGraphicsDropShadowEffect, QMenu
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize, QTimer, QDate, QEvent
from PyQt5.QtGui import QFont, QColor
from pathlib import Path
from typing import Optional
import sys
import ctypes
import time

from src.core.account_manager import AccountManager, Account
from src.core.riot_integration import RiotClientIntegration
from src.security.encryption import PasswordEncryption
from src.config.paths import (
    get_lol_executable,
    set_custom_lol_exe,
    reset_settings,
    get_default_lol_executable_path,
    load_settings,
    save_settings,
)


DARK_STYLESHEET = """
QMainWindow, QDialog, QWidget {
    background-color: #1e1e2e;
    color: #cdd6f4;
}
QListWidget {
    background-color: #181825;
    border: 1px solid #313244;
    border-radius: 6px;
    color: #cdd6f4;
}
QListWidget::item:selected {
    background-color: #45475a;
}
QListWidget::item:hover {
    background-color: #313244;
}
QPushButton {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 5px;
    padding: 5px 10px;
}
QPushButton:hover {
    background-color: #45475a;
}
QPushButton:pressed {
    background-color: #585b70;
}
QPushButton:disabled {
    background-color: #1e1e2e;
    color: #585b70;
    border: 1px solid #313244;
}
QLineEdit, QComboBox, QDateEdit {
    background-color: #181825;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 4px;
    padding: 4px;
}
QComboBox QAbstractItemView {
    background-color: #181825;
    color: #cdd6f4;
    selection-background-color: #45475a;
}
QLabel {
    color: #cdd6f4;
}
QProgressDialog {
    background-color: #1e1e2e;
    color: #cdd6f4;
}
"""

LIGHT_STYLESHEET = """
QListWidget {
    background-color: #ffffff;
    border: 1px solid #cfcfcf;
    border-radius: 6px;
}
"""

REGION_OPTIONS = [
    ("NA", "North America"),
    ("EUW", "Europe West"),
    ("EUNE", "Europe Nordic & East"),
    ("KR", "Korea"),
    ("JP", "Japan"),
    ("OCE", "Oceania"),
    ("BR", "Brazil"),
    ("LAN", "Latin America North"),
    ("LAS", "Latin America South"),
    ("RU", "Russia"),
    ("TR", "Turkey"),
    ("ME", "Middle East"),
    ("PH", "Philippines"),
    ("SG", "Singapore"),
    ("TH", "Thailand"),
    ("TW", "Taiwan"),
    ("VN", "Vietnam"),
    ("CN", "China"),
    ("PBE", "Public Beta Environment"),
]
REGION_NAMES = {code: label for code, label in REGION_OPTIONS}

if sys.platform.startswith("win"):
    DWMWA_USE_IMMERSIVE_DARK_MODE = 20
    DWMWA_WINDOW_CORNER_PREFERENCE = 33
    DWMWA_BORDER_COLOR = 34
    DWMWA_CAPTION_COLOR = 35
    DWMWA_TEXT_COLOR = 36


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
    """Dialog for adding or editing an account"""

    def __init__(self, parent=None, account: Optional[Account] = None):
        super().__init__(parent)
        self.editing_account = account
        self.account = None
        self.init_ui()
    
    def init_ui(self):
        is_edit = self.editing_account is not None
        self.setWindowTitle("Edit Account" if is_edit else "Add Account")
        self.setModal(True)
        self.setMinimumWidth(350)
        
        layout = QVBoxLayout()
        
        # Username
        layout.addWidget(QLabel("Username (or Email):"))
        self.username_input = QLineEdit()
        layout.addWidget(self.username_input)

        # Tag Line
        layout.addWidget(QLabel("Tag Line:"))
        self.tag_line_input = QLineEdit()
        self.tag_line_input.setPlaceholderText("NA1")
        self.tag_line_input.setText("NA1")
        layout.addWidget(self.tag_line_input)
        
        # Password
        layout.addWidget(QLabel("Password:"))
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password_input)
        
        # Display Name (optional)
        layout.addWidget(QLabel("Display Name (optional):"))
        self.display_name_input = QLineEdit()
        layout.addWidget(self.display_name_input)

        # Region
        layout.addWidget(QLabel("Region:"))
        self.region_combo = QComboBox()
        for code, label in REGION_OPTIONS:
            self.region_combo.addItem(label, code)
        self.region_combo.setCurrentIndex(self.region_combo.findData("NA"))
        layout.addWidget(self.region_combo)
        
        # Ban Status
        layout.addWidget(QLabel("Ban Status:"))
        self.ban_status_combo = QComboBox()
        self.ban_status_combo.addItem("Not Banned", "none")
        self.ban_status_combo.addItem("Temporary Ban", "temporary")
        self.ban_status_combo.addItem("Permanent Ban", "permanent")
        self.ban_status_combo.currentIndexChanged.connect(self._on_ban_status_changed)
        layout.addWidget(self.ban_status_combo)

        self.ban_end_date_label = QLabel("Ban End Date:")
        layout.addWidget(self.ban_end_date_label)
        self.ban_end_date_edit = QDateEdit()
        self.ban_end_date_edit.setCalendarPopup(True)
        self.ban_end_date_edit.setDate(QDate.currentDate())
        self.ban_end_date_edit.setDisplayFormat("yyyy-MM-dd")
        layout.addWidget(self.ban_end_date_edit)

        button_layout = QHBoxLayout()

        add_btn = QPushButton("Save Changes" if is_edit else "Add Account")
        add_btn.clicked.connect(self.validate_and_accept)
        button_layout.addWidget(add_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)
        self.setLayout(layout)

        if self.editing_account:
            self.username_input.setText(self.editing_account.username)
            self.tag_line_input.setText(getattr(self.editing_account, "tag_line", "NA1"))
            self.password_input.setText(self.editing_account.password)
            self.display_name_input.setText(self.editing_account.display_name)
            region = self.editing_account.region if getattr(self.editing_account, "region", None) else "NA"
            idx = self.region_combo.findData(region)
            if idx < 0:
                idx = self.region_combo.findText(region)
            if idx >= 0:
                self.region_combo.setCurrentIndex(idx)
            idx = self.ban_status_combo.findData(self.editing_account.ban_status)
            if idx >= 0:
                self.ban_status_combo.setCurrentIndex(idx)
            if self.editing_account.ban_end_date:
                self.ban_end_date_edit.setDate(
                    QDate.fromString(self.editing_account.ban_end_date, "yyyy-MM-dd")
                )

        self._on_ban_status_changed()

    def _on_ban_status_changed(self):
        is_temporary = self.ban_status_combo.currentData() == "temporary"
        self.ban_end_date_label.setVisible(is_temporary)
        self.ban_end_date_edit.setVisible(is_temporary)
    
    def validate_and_accept(self):
        if not self.username_input.text().strip():
            QMessageBox.warning(self, "Error", "Please enter a username!")
            return
        if not self.password_input.text():
            QMessageBox.warning(self, "Error", "Please enter a password!")
            return
        self.accept()
    
    def get_data(self):
        ban_status = self.ban_status_combo.currentData()
        ban_end_date = ""
        if ban_status == "temporary":
            ban_end_date = self.ban_end_date_edit.date().toString("yyyy-MM-dd")
        return {
            'username': self.username_input.text().strip(),
            'tag_line': self.tag_line_input.text().strip() or "NA1",
            'password': self.password_input.text(),
            'display_name': self.display_name_input.text().strip() or self.username_input.text().strip(),
            'region': self.region_combo.currentData(),
            'ban_status': ban_status,
            'ban_end_date': ban_end_date,
        }


class AccountListItem(QFrame):
    """Custom widget for displaying account in list"""
    
    def __init__(self, account: Account, parent=None):
        super().__init__(parent)
        self.account = account
        self.init_ui()
    
    def init_ui(self):
        outer = QHBoxLayout()
        outer.setContentsMargins(10, 5, 10, 5)
        outer.setSpacing(8)
        self.setObjectName("accountListItem")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setMouseTracking(True)
        self._selected = False
        self._hovered = False
        self._dark_mode = True
        self._shadow = QGraphicsDropShadowEffect(self)
        self._shadow.setOffset(0, 3)
        self._shadow.setBlurRadius(0)
        self._shadow.setColor(QColor(0, 0, 0, 0))
        self.setGraphicsEffect(self._shadow)

        # Colored status circle
        circle = QLabel("\u25CF")
        circle.setFixedWidth(16)
        circle.setAlignment(Qt.AlignVCenter)
        circle.setAttribute(Qt.WA_TranslucentBackground, True)
        color = "#e74c3c" if self.account.is_banned() else "#2ecc71"
        circle.setStyleSheet(
            f"background: transparent; border: none; color: {color}; font-size: 16px;"
        )
        outer.addWidget(circle)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)

        name_font = QFont()
        name_font.setBold(True)
        name_font.setPointSize(11)

        tag_font = QFont()
        tag_font.setBold(True)
        tag_font.setPointSize(10)
        tag_font.setWeight(QFont.DemiBold)

        region_code = self.account.region if getattr(self.account, "region", None) else "NA"
        region = REGION_NAMES.get(region_code, region_code)
        tag_line = self.account.tag_line if getattr(self.account, "tag_line", None) else "NA1"

        name_row = QHBoxLayout()
        name_row.setSpacing(4)

        name_label = QLabel(self.account.display_name)
        name_label.setFont(name_font)
        name_label.setAttribute(Qt.WA_TranslucentBackground, True)
        name_label.setStyleSheet("background: transparent; border: none;")
        name_row.addWidget(name_label)

        tag_label = QLabel(f"#{tag_line}")
        tag_label.setFont(tag_font)
        tag_label.setAttribute(Qt.WA_TranslucentBackground, True)
        tag_label.setStyleSheet("background: transparent; border: none; color: #9aa1b2;")
        name_row.addWidget(tag_label)

        name_row.addStretch()
        text_layout.addLayout(name_row)

        user_row = QHBoxLayout()
        user_row.setSpacing(6)
        username_label = QLabel(f"@{self.account.username}")
        username_label.setStyleSheet("background: transparent; border: none; color: #666666;")
        username_label.setAttribute(Qt.WA_TranslucentBackground, True)
        user_row.addWidget(username_label)

        region_label = QLabel(f"{region}")
        region_label.setAttribute(Qt.WA_TranslucentBackground, True)
        region_label.setStyleSheet("background: transparent; border: none; color: #8b93a8; font-size: 10px;")
        user_row.addWidget(region_label)

        if self.account.ban_status == "permanent":
            ban_label = QLabel("⛔ Permanently Banned")
            ban_label.setStyleSheet("background: transparent; border: none; color: #e74c3c; font-size: 10px;")
            user_row.addWidget(ban_label)
        elif self.account.ban_status == "temporary" and self.account.ban_end_date:
            if self.account.is_banned():
                ban_label = QLabel(f"⛔ Banned until {self.account.ban_end_date}")
                ban_label.setStyleSheet("background: transparent; border: none; color: #e67e22; font-size: 10px;")
                user_row.addWidget(ban_label)

        user_row.addStretch()
        text_layout.addLayout(user_row)

        outer.addLayout(text_layout)
        outer.addStretch()
        self.setLayout(outer)
        self._update_visual_state()

    def set_dark_mode(self, enabled: bool):
        self._dark_mode = enabled
        self._update_visual_state()

    def set_selected(self, selected: bool):
        self._selected = selected
        self._update_visual_state()

    def enterEvent(self, event):
        self._hovered = True
        self._update_visual_state()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovered = False
        self._update_visual_state()
        super().leaveEvent(event)

    def _update_visual_state(self):
        if not self._dark_mode:
            self.setStyleSheet("")
            self._shadow.setBlurRadius(0)
            self._shadow.setColor(QColor(0, 0, 0, 0))
            return

        active = self._selected or self._hovered
        if active:
            self.setStyleSheet(
                "#accountListItem {"
                "background-color: rgba(69, 71, 90, 180);"
                "border: 1px solid rgba(137, 180, 250, 140);"
                "border-radius: 10px;"
                "}"
            )
            self._shadow.setBlurRadius(18)
            self._shadow.setColor(QColor(0, 0, 0, 120))
        else:
            self.setStyleSheet(
                "#accountListItem {"
                "background-color: transparent;"
                "border: 1px solid transparent;"
                "border-radius: 10px;"
                "}"
            )
            self._shadow.setBlurRadius(0)
            self._shadow.setColor(QColor(0, 0, 0, 0))


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.account_manager: Optional[AccountManager] = None
        self.login_thread: Optional[LoginThread] = None
        self.launch_progress: Optional[QProgressDialog] = None
        self.current_launch_username: Optional[str] = None
        self._dark_mode: bool = load_settings().get('dark_mode', True)
        self.init_ui()
        self._apply_theme()
        self.check_master_password()
    
    def init_ui(self):
        self.setWindowTitle("League of Legends Account Manager")
        self.setMinimumSize(500, 400)
        self.resize(500, 400)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)

        top_row = QHBoxLayout()
        top_row.addStretch()
        self._theme_button = QPushButton()
        self._theme_button.setToolTip("Switch between dark and light mode")
        self._theme_button.clicked.connect(self.toggle_theme)
        top_row.addWidget(self._theme_button)
        layout.addLayout(top_row)
        
        # Title
        title = QLabel("LOL Account Manager")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Account list
        layout.addWidget(QLabel("Saved Accounts:"))
        self.account_list = QListWidget()
        self.account_list.itemClicked.connect(self.on_account_selected)
        self.account_list.itemSelectionChanged.connect(self.update_account_item_states)
        self.account_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.account_list.customContextMenuRequested.connect(self.show_account_context_menu)
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

        self.edit_btn = QPushButton("Edit Selected")
        self.edit_btn.clicked.connect(self.edit_account)
        self.edit_btn.setEnabled(False)
        button_layout.addWidget(self.edit_btn)
        
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

        self.about_btn = QPushButton("About")
        self.about_btn.clicked.connect(self.show_about)
        settings_layout.addWidget(self.about_btn)

        self.backup_btn = QPushButton("Backup / Restore...")
        self.backup_btn.setToolTip("Export or import an encrypted account backup")
        self.backup_btn.clicked.connect(self.open_backup_dialog)
        settings_layout.addWidget(self.backup_btn)

        settings_layout.addStretch()
        layout.addLayout(settings_layout)

        self.lol_path_label = QLabel()
        self.lol_path_label.setStyleSheet("color: #666666;")
        self.lol_path_label.setTextInteractionFlags(
            Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard
        )
        layout.addWidget(self.lol_path_label)
        self._refresh_lol_path_label()
        
        central_widget.setLayout(layout)
    
    def toggle_theme(self):
        """Toggle between dark and light mode."""
        self._dark_mode = not self._dark_mode
        self._apply_theme()
        settings = load_settings()
        settings['dark_mode'] = self._dark_mode
        save_settings(settings)

    def _apply_theme(self):
        """Apply the current theme stylesheet."""
        if self._dark_mode:
            self.setStyleSheet(DARK_STYLESHEET)
            self._theme_button.setText("☀  Light Mode")
        else:
            self.setStyleSheet(LIGHT_STYLESHEET)
            self._theme_button.setText("🌙  Dark Mode")

        self.update_account_item_states()
        self._apply_title_bar_theme()

    def _apply_title_bar_theme(self):
        """Update the native Windows title bar to match the active theme."""
        if not sys.platform.startswith("win"):
            return

        try:
            hwnd = int(self.winId())
            corner_preference = ctypes.c_int(2)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd,
                DWMWA_WINDOW_CORNER_PREFERENCE,
                ctypes.byref(corner_preference),
                ctypes.sizeof(corner_preference),
            )

            value = ctypes.c_int(1 if self._dark_mode else 0)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd,
                DWMWA_USE_IMMERSIVE_DARK_MODE,
                ctypes.byref(value),
                ctypes.sizeof(value),
            )

            if self._dark_mode:
                caption_color = ctypes.c_int(0x302B2B)
                text_color = ctypes.c_int(0xF4D6CD)
            else:
                caption_color = ctypes.c_int(0xF3F3F3)
                text_color = ctypes.c_int(0x1E1E1E)

            border_color = caption_color

            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd,
                DWMWA_CAPTION_COLOR,
                ctypes.byref(caption_color),
                ctypes.sizeof(caption_color),
            )
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd,
                DWMWA_TEXT_COLOR,
                ctypes.byref(text_color),
                ctypes.sizeof(text_color),
            )
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd,
                DWMWA_BORDER_COLOR,
                ctypes.byref(border_color),
                ctypes.sizeof(border_color),
            )
        except Exception:
            pass

    def showEvent(self, event):
        super().showEvent(event)
        self._apply_title_bar_theme()

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
            self.edit_btn.setEnabled(False)
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

            self.update_account_item_states()
    
    def on_account_selected(self):
        """Handle account selection"""
        selected = self.account_list.currentItem()
        if selected:
            username = selected.data(Qt.UserRole)
            self.launch_btn.setEnabled(username is not None)
            self.edit_btn.setEnabled(username is not None)
            self.delete_btn.setEnabled(username is not None)

    def update_account_item_states(self):
        """Refresh hover/selected visuals for account rows."""
        for index in range(self.account_list.count()):
            item = self.account_list.item(index)
            widget = self.account_list.itemWidget(item)
            if isinstance(widget, AccountListItem):
                widget.set_dark_mode(self._dark_mode)
                widget.set_selected(item.isSelected())

    def show_account_context_menu(self, position):
        """Show copy actions for the account row under the cursor."""
        item = self.account_list.itemAt(position)
        if not item or not self.account_manager:
            return

        username = item.data(Qt.UserRole)
        account = self.account_manager.get_account(username)
        if not account:
            return

        self.account_list.setCurrentItem(item)
        self.update_account_item_states()

        menu = QMenu(self)
        copy_username_action = menu.addAction("Copy Username")
        copy_password_action = menu.addAction("Copy Password")
        copy_friend_code_action = menu.addAction("Copy Friend Code")

        chosen_action = menu.exec_(self.account_list.viewport().mapToGlobal(position))
        if chosen_action == copy_username_action:
            self.copy_to_clipboard(account.username)
        elif chosen_action == copy_password_action:
            self.copy_to_clipboard(account.password)
        elif chosen_action == copy_friend_code_action:
            friend_code = f"{account.display_name} {getattr(account, 'tag_line', 'NA1')}"
            self.copy_to_clipboard(friend_code)

    def copy_to_clipboard(self, text: str):
        """Copy text to the system clipboard."""
        QApplication.clipboard().setText(text)

    def edit_account(self):
        """Edit the selected account"""
        if not self.account_manager:
            return

        selected = self.account_list.currentItem()
        if not selected:
            return

        username = selected.data(Qt.UserRole)
        account = self.account_manager.get_account(username)

        if not account:
            return

        dialog = AddAccountDialog(self, account=account)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()

            try:
                self.account_manager.update_account(
                    username=username,
                    new_username=data['username'],
                    password=data['password'],
                    display_name=data['display_name'],
                    region=data['region'],
                    tag_line=data['tag_line'],
                    ban_status=data['ban_status'],
                    ban_end_date=data['ban_end_date'],
                )
                self.refresh_account_list()
                QMessageBox.information(self, "Success", "Account updated successfully!")
            except ValueError as e:
                self._show_error("Error", str(e))
            except Exception as e:
                self._show_error("Error", f"Failed to update account: {str(e)}")
    
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
                    data['display_name'],
                    region=data['region'],
                    tag_line=data['tag_line'],
                    ban_status=data['ban_status'],
                    ban_end_date=data['ban_end_date'],
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

        if self.login_thread and self.login_thread.isRunning():
            self._show_error("Error", "A launch is already in progress.")
            return
        
        selected = self.account_list.currentItem()
        if not selected:
            return
        
        username = selected.data(Qt.UserRole)
        account = self.account_manager.get_account(username)
        
        if not account:
            return

        self.current_launch_username = account.username
        
        # Show cancellable progress dialog
        self.launch_progress = QProgressDialog(
            f"Starting League of Legends for {account.display_name}...",
            "Close",
            0,
            0,
            self,
        )
        self.launch_progress.setWindowTitle("Launching...")
        self.launch_progress.setWindowModality(Qt.WindowModal)
        self.launch_progress.setAutoClose(False)
        self.launch_progress.setAutoReset(False)
        self.launch_progress.setMinimumDuration(0)
        self.launch_progress.canceled.connect(self._dismiss_launch_progress)
        self.launch_progress.show()
        QTimer.singleShot(0, self._center_launch_progress)
        
        # Launch in background thread
        self.login_thread = LoginThread(
            account.username,
            account.password,
            auto_launch_lol=True
        )
        self.login_thread.finished.connect(self.on_launch_finished)
        self.login_thread.error.connect(self.on_launch_error)
        self.login_thread.finished.connect(lambda _: self._dismiss_launch_progress())
        self.login_thread.error.connect(lambda _: self._dismiss_launch_progress())
        self.login_thread.start()

        # Safety net: if background flow hangs, close the dialog and inform user.
        QTimer.singleShot(60000, self._handle_launch_timeout)
    
    def on_launch_finished(self, success):
        """Handle launch completion"""
        self._dismiss_launch_progress()
        
        if success:
            username = self.current_launch_username or "Unknown"
            QMessageBox.information(
                self,
                "Success",
                f"{username} login successful!"
            )
        else:
            self._show_error("Error", "Failed to launch. Make sure League of Legends is installed.")

        self.current_launch_username = None
    
    def on_launch_error(self, error):
        """Handle launch error"""
        self._dismiss_launch_progress()
        self._show_error("Error", f"Launch failed: {error}")

    def _dismiss_launch_progress(self):
        """Close and clear launch progress UI if it exists."""
        progress = self.launch_progress
        if not progress:
            return

        # Clear shared reference first to avoid re-entrant double-close crashes.
        self.launch_progress = None
        try:
            progress.canceled.disconnect(self._dismiss_launch_progress)
        except Exception:
            pass

        progress.close()
        progress.deleteLater()

    def _center_launch_progress(self):
        """Center launch progress dialog over the main window."""
        progress = self.launch_progress
        if not progress:
            return

        progress.adjustSize()
        parent_geo = self.frameGeometry()
        dlg_geo = progress.frameGeometry()
        x = parent_geo.x() + (parent_geo.width() - dlg_geo.width()) // 2
        y = parent_geo.y() + (parent_geo.height() - dlg_geo.height()) // 2
        progress.move(max(x, 0), max(y, 0))

    def _handle_launch_timeout(self):
        """Keep waiting quietly while the launch thread continues retries."""
        if self.login_thread and self.login_thread.isRunning() and self.launch_progress:
            # Do not interrupt with an error popup; retry logic runs in background.
            QTimer.singleShot(60000, self._handle_launch_timeout)
    
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
                                    account.display_name,
                                    region=account.region,
                                    tag_line=account.tag_line,
                                    ban_status=account.ban_status,
                                    ban_end_date=account.ban_end_date,
                                )
                            
                            QMessageBox.information(self, "Success", "Master password updated!")
                        except Exception as e:
                            QMessageBox.critical(self, "Error", f"Failed to update password: {str(e)}")
            else:
                self._show_error("Error", "Incorrect password!")

    def open_backup_dialog(self):
        """Prompt user to choose between export and import."""
        msg = QMessageBox(self)
        msg.setWindowTitle("Backup / Restore")
        msg.setText("Would you like to export your accounts to a backup file, or import from an existing backup?")
        export_btn = msg.addButton("Export Backup", QMessageBox.AcceptRole)
        import_btn = msg.addButton("Import Backup", QMessageBox.AcceptRole)
        msg.addButton("Cancel", QMessageBox.RejectRole)
        msg.exec_()
        clicked = msg.clickedButton()
        if clicked is export_btn:
            self.export_accounts()
        elif clicked is import_btn:
            self.import_accounts()

    def export_accounts(self):
        """Export all accounts to an encrypted backup file."""
        if not self.account_manager:
            return

        if not self.account_manager.get_all_accounts():
            QMessageBox.information(self, "No Accounts", "There are no accounts to export.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Backup",
            "lol_accounts_backup.lolbak",
            "LoL Backup (*.lolbak);;JSON files (*.json);;All files (*)",
        )
        if not file_path:
            return

        try:
            self.account_manager.export_to_file(file_path)
            QMessageBox.information(
                self,
                "Export Successful",
                f"Accounts exported to:\n{file_path}\n\n"
                "The backup is encrypted with your current master password.\n"
                "You will need it to import this backup.",
            )
        except Exception as e:
            self._show_error("Export Failed", f"Could not export accounts:\n{str(e)}")

    def import_accounts(self):
        """Import accounts from a backup file."""
        if not self.account_manager:
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Backup",
            "",
            "LoL Backup (*.lolbak);;JSON files (*.json);;All files (*)",
        )
        if not file_path:
            return

        # Ask for the master password used when the backup was created
        pwd_dialog = MasterPasswordDialog(self, is_setup=False)
        pwd_dialog.setWindowTitle("Backup Password")
        pwd_dialog.findChild(QLabel).setText(
            "Enter the master password that was active when this backup was created:"
        )
        if pwd_dialog.exec_() != QDialog.Accepted:
            return
        source_password = pwd_dialog.password_input.text()
        if not source_password:
            return

        # Merge vs Replace
        existing = self.account_manager.get_all_accounts()
        merge = True
        if existing:
            msg = QMessageBox(self)
            msg.setWindowTitle("Import Mode")
            msg.setText(
                "How would you like to import?\n\n"
                "\u2022 Merge \u2014 add new accounts, keep existing ones\n"
                "\u2022 Replace \u2014 delete all current accounts and import fresh"
            )
            merge_btn = msg.addButton("Merge", QMessageBox.AcceptRole)
            replace_btn = msg.addButton("Replace", QMessageBox.DestructiveRole)
            msg.addButton("Cancel", QMessageBox.RejectRole)
            msg.exec_()
            clicked = msg.clickedButton()
            if clicked is None or clicked.text() == "Cancel":
                return
            merge = (clicked is merge_btn)
        else:
            merge = False  # No existing accounts; behaves the same either way

        try:
            count = self.account_manager.import_from_file(file_path, source_password, merge=merge)
            self.refresh_account_list()
            QMessageBox.information(
                self,
                "Import Successful",
                f"{count} account(s) imported successfully.",
            )
        except ValueError as e:
            self._show_error("Import Failed", str(e))
        except Exception as e:
            self._show_error("Import Failed", f"Could not import backup:\n{str(e)}")

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
            p = Path(exe_path)
            if p.name.lower() not in ('leagueclient.exe', 'league of legends.exe'):
                QMessageBox.warning(
                    self, "Unexpected file",
                    f"Expected LeagueClient.exe but got '{p.name}'.\n"
                    "Saving anyway — update if launch fails."
                )
            set_custom_lol_exe(p)
            self._refresh_lol_path_label()
            QMessageBox.information(
                self, "LoL Path Saved",
                f"League of Legends path set to:\n{exe_path}"
            )

    def reset_app_settings(self):
        """Reset app settings to defaults."""
        reply = QMessageBox.question(
            self,
            "Reset Settings",
            "Reset all launcher settings to defaults?\n\n"
            "This clears your custom LoL path and other saved app settings.",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            try:
                reset_settings()
                self._refresh_lol_path_label()
                QMessageBox.information(
                    self,
                    "Settings Reset",
                    "Settings reset to default values.",
                )
            except Exception as e:
                self._show_error("Error", f"Failed to reset settings: {str(e)}")

    def show_about(self):
        """Show About dialog."""
        dlg = QDialog(self)
        dlg.setWindowTitle("About")
        dlg.setMinimumWidth(380)
        dlg.setModal(True)

        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("LoL Account Manager")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        dev_label = QLabel("Developer: jtmb")
        dev_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(dev_label)

        repo_label = QLabel('<a href="https://github.com/jtmb/lol-account-manager">github.com/jtmb/lol-account-manager</a>')
        repo_label.setAlignment(Qt.AlignCenter)
        repo_label.setOpenExternalLinks(True)
        repo_label.setTextInteractionFlags(
            Qt.TextBrowserInteraction
        )
        layout.addWidget(repo_label)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dlg.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignCenter)

        dlg.setLayout(layout)
        dlg.exec_()

    def _refresh_lol_path_label(self):
        """Update the LoL path label to reflect the currently active path."""
        active = get_lol_executable()
        if active:
            self.lol_path_label.setText(f"LoL path: {active}")
        else:
            default = get_default_lol_executable_path()
            self.lol_path_label.setText(f"LoL path (default): {default}")

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
