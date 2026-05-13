"""Main application window"""
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QListWidget, QListWidgetItem, QLabel, QDialog, QLineEdit,
    QMessageBox, QFrame, QFileDialog, QProgressDialog, QComboBox,
    QDateEdit, QGraphicsDropShadowEffect, QMenu, QCheckBox, QGridLayout,
    QTextEdit, QSpinBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize, QTimer, QDate, QEvent
from PyQt5.QtGui import QFont, QColor, QPixmap
from pathlib import Path
from typing import Optional
import sys
import ctypes
import time
import random
import webbrowser
from urllib.parse import quote

if sys.platform.startswith("win"):
    import winreg

from src.core.account_manager import AccountManager, Account
from src.core.riot_integration import RiotClientIntegration
from src.core.opgg_service import fetch_rank
from src.core.opgg_service import OPGG_REGION_MAP
from src.security.encryption import PasswordEncryption
from src.config.paths import (
    get_lol_executable,
    set_custom_lol_exe,
    reset_settings,
    get_default_lol_executable_path,
    load_settings,
    save_settings,
)


def _escape_html(text: str) -> str:
    """Escape text before inserting it into rich-text labels."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _build_rank_pixmap(image_bytes: bytes) -> QPixmap:
    """Convert fetched medal bytes into a row icon."""
    pixmap = QPixmap()
    if image_bytes:
        pixmap.loadFromData(image_bytes)
    return pixmap


def _parse_resolution(resolution: str, fallback: tuple[int, int] = (660, 480)) -> tuple[int, int]:
    """Parse a WxH resolution string."""
    try:
        width_str, height_str = resolution.lower().split("x", 1)
        return int(width_str), int(height_str)
    except Exception:
        return fallback


def _parse_tags(raw: str) -> list[str]:
    """Parse comma-separated tags into a normalized unique list."""
    seen = set()
    tags = []
    for part in raw.split(','):
        tag = part.strip().lower()
        if not tag or tag in seen:
            continue
        seen.add(tag)
        tags.append(tag)
    return tags


def _startup_command() -> str:
    """Build command line used for Windows startup registration."""
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}"'
    entry_script = str(Path(sys.argv[0]).resolve())
    return f'"{sys.executable}" "{entry_script}"'


def _is_startup_enabled() -> bool:
    """Return whether app startup is currently registered on Windows."""
    if not sys.platform.startswith("win"):
        return False
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\\Microsoft\\Windows\\CurrentVersion\\Run",
            0,
            winreg.KEY_READ,
        ) as key:
            value, _ = winreg.QueryValueEx(key, "LoLAccountManager")
            return bool(value)
    except OSError:
        return False


def _set_startup_enabled(enabled: bool):
    """Enable or disable app startup registration on Windows."""
    if not sys.platform.startswith("win"):
        return
    with winreg.OpenKey(
        winreg.HKEY_CURRENT_USER,
        r"Software\\Microsoft\\Windows\\CurrentVersion\\Run",
        0,
        winreg.KEY_SET_VALUE,
    ) as key:
        if enabled:
            winreg.SetValueEx(key, "LoLAccountManager", 0, winreg.REG_SZ, _startup_command())
        else:
            try:
                winreg.DeleteValue(key, "LoLAccountManager")
            except FileNotFoundError:
                pass


def _apply_windows11_chrome(widget, dark_mode: bool):
    """Apply Windows 11 title bar/chrome colors to a top-level window."""
    if not sys.platform.startswith("win"):
        return

    try:
        hwnd = int(widget.winId())
        corner_preference = ctypes.c_int(2)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd,
            DWMWA_WINDOW_CORNER_PREFERENCE,
            ctypes.byref(corner_preference),
            ctypes.sizeof(corner_preference),
        )

        value = ctypes.c_int(1 if dark_mode else 0)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd,
            DWMWA_USE_IMMERSIVE_DARK_MODE,
            ctypes.byref(value),
            ctypes.sizeof(value),
        )

        if dark_mode:
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
QLineEdit, QComboBox, QDateEdit, QTextEdit, QPlainTextEdit, QSpinBox {
    background-color: #181825;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 4px;
    padding: 4px;
}
QSpinBox::up-button, QSpinBox::down-button {
    subcontrol-origin: border;
    background-color: #313244;
    border-left: 1px solid #45475a;
    width: 16px;
}
QSpinBox::up-button:hover, QSpinBox::down-button:hover {
    background-color: #45475a;
}
QLineEdit::placeholder {
    color: #9aa4bf;
}
QComboBox QAbstractItemView {
    background-color: #181825;
    color: #cdd6f4;
    selection-background-color: #45475a;
}
QComboBox {
    padding-right: 24px;
}
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 20px;
    border-left: 1px solid #45475a;
    background-color: #22263a;
    border-top-right-radius: 4px;
    border-bottom-right-radius: 4px;
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
QMainWindow, QDialog, QWidget {
    background-color: #f5f6f8;
    color: #111827;
}
QListWidget {
    background-color: #ffffff;
    border: 1px solid #cfcfcf;
    border-radius: 6px;
}
QPushButton {
    background-color: #f3f4f6;
    color: #111827;
    border: 1px solid #cfcfcf;
    border-radius: 5px;
    padding: 5px 10px;
}
QPushButton:hover {
    background-color: #e5e7eb;
}
QPushButton:pressed {
    background-color: #d1d5db;
}
QPushButton:disabled {
    background-color: #f9fafb;
    color: #9ca3af;
    border: 1px solid #d1d5db;
}
QLineEdit, QComboBox, QDateEdit, QTextEdit, QPlainTextEdit, QSpinBox {
    background-color: #ffffff;
    color: #111827;
    border: 1px solid #cfcfcf;
    border-radius: 4px;
    padding: 4px;
}
QComboBox {
    padding-right: 24px;
}
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 20px;
    border-left: 1px solid #cfcfcf;
    background-color: #f3f4f6;
    border-top-right-radius: 4px;
    border-bottom-right-radius: 4px;
}
QSpinBox::up-button, QSpinBox::down-button {
    subcontrol-origin: border;
    background-color: #f3f4f6;
    border-left: 1px solid #cfcfcf;
    width: 16px;
}
QSpinBox::up-button:hover, QSpinBox::down-button:hover {
    background-color: #e5e7eb;
}
QComboBox QAbstractItemView {
    background-color: #ffffff;
    color: #111827;
    selection-background-color: #dbeafe;
}
QLabel {
    color: #111827;
}
QLineEdit::placeholder {
    color: #6b7280;
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


class RankFetchThread(QThread):
    """Background thread that fetches rank data from op.gg for one account."""
    result_ready = pyqtSignal(str, dict)  # username, rank_data

    def __init__(self, username: str, display_name: str, tag_line: str, region: str):
        super().__init__()
        self.username = username
        self.display_name = display_name
        self.tag_line = tag_line
        self.region = region

    def run(self):
        data = fetch_rank(self.display_name, self.tag_line, self.region)
        self.result_ready.emit(self.username, data)


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


class InGameWatcherThread(QThread):
    """Poll local Live Client API until an active match is detected."""

    ingame_detected = pyqtSignal(str)  # op.gg url

    def __init__(self, opgg_url: str, timeout_seconds: int = 900, poll_interval_seconds: float = 3.0):
        super().__init__()
        self._opgg_url = opgg_url
        self._timeout_seconds = timeout_seconds
        self._poll_interval_seconds = poll_interval_seconds

    def run(self):
        deadline = time.time() + self._timeout_seconds
        while time.time() < deadline:
            if self.isInterruptionRequested():
                return
            if RiotClientIntegration.is_in_active_game(timeout_seconds=1.5):
                self.ingame_detected.emit(self._opgg_url)
                return
            self.msleep(max(200, int(self._poll_interval_seconds * 1000)))


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

        # Tags
        layout.addWidget(QLabel("Tags (comma-separated):"))
        self.tags_input = QLineEdit()
        self.tags_input.setPlaceholderText("main, ranked, smurf")
        layout.addWidget(self.tags_input)

        # Notes
        layout.addWidget(QLabel("Private Notes (encrypted):"))
        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Optional notes for this account")
        self.notes_input.setFixedHeight(90)
        layout.addWidget(self.notes_input)
        
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
            self.tags_input.setText(", ".join(getattr(self.editing_account, "tags", []) or []))
            self.notes_input.setPlainText(getattr(self.editing_account, "notes", "") or "")
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
            'tags': _parse_tags(self.tags_input.text()),
            'notes': self.notes_input.toPlainText().strip(),
            'ban_status': ban_status,
            'ban_end_date': ban_end_date,
        }


class SettingsDialog(QDialog):
    """Dialog for global app settings."""

    COMMON_RESOLUTIONS = [
        "640x480",
        "800x600",
        "1024x768",
        "1280x720",
        "1366x768",
        "1600x900",
        "1920x1080",
    ]

    TEXT_ZOOM_OPTIONS = [
        ("90%", 90),
        ("100%", 100),
        ("110%", 110),
        ("125%", 125),
        ("140%", 140),
    ]

    TAG_SIZE_OPTIONS = [
        ("Small", "small"),
        ("Medium", "medium"),
        ("Large", "large"),
    ]

    BACKUP_KEEP_OPTIONS = [10, 20, 40, 80]

    def __init__(self, parent=None, settings: Optional[dict] = None):
        super().__init__(parent)
        self._settings = settings or {}
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Settings")
        self.setModal(True)
        self.setMinimumWidth(360)

        layout = QVBoxLayout()

        startup_default = self._settings.get("start_on_windows_startup", _is_startup_enabled())
        self.startup_checkbox = QCheckBox("Start Program at Windows startup")
        self.startup_checkbox.setChecked(bool(startup_default))
        self.startup_checkbox.setEnabled(sys.platform.startswith("win"))
        if not sys.platform.startswith("win"):
            self.startup_checkbox.setToolTip("Available on Windows only")
        layout.addWidget(self.startup_checkbox)

        layout.addWidget(QLabel("Window size:"))
        self.window_size_combo = QComboBox()
        self.window_size_combo.addItems(self.COMMON_RESOLUTIONS)
        current_resolution = self._settings.get("window_size", "800x600")
        if current_resolution not in self.COMMON_RESOLUTIONS:
            self.window_size_combo.addItem(current_resolution)
        self.window_size_combo.setCurrentText(current_resolution)
        layout.addWidget(self.window_size_combo)

        layout.addWidget(QLabel("Text Size:"))
        self.text_zoom_combo = QComboBox()
        for label, value in self.TEXT_ZOOM_OPTIONS:
            self.text_zoom_combo.addItem(label, value)
        current_zoom = int(self._settings.get("text_zoom_percent", 110))
        zoom_index = self.text_zoom_combo.findData(current_zoom)
        if zoom_index < 0:
            self.text_zoom_combo.addItem(f"{current_zoom}%", current_zoom)
            zoom_index = self.text_zoom_combo.findData(current_zoom)
        self.text_zoom_combo.setCurrentIndex(max(0, zoom_index))
        layout.addWidget(self.text_zoom_combo)

        self.show_ranks_checkbox = QCheckBox("Show ranks")
        self.show_ranks_checkbox.setChecked(bool(self._settings.get("show_ranks", True)))
        layout.addWidget(self.show_ranks_checkbox)

        self.show_images_checkbox = QCheckBox("Show rank images")
        self.show_images_checkbox.setChecked(bool(self._settings.get("show_rank_images", True)))
        layout.addWidget(self.show_images_checkbox)
        self.show_ranks_checkbox.toggled.connect(self.show_images_checkbox.setEnabled)
        self.show_images_checkbox.setEnabled(self.show_ranks_checkbox.isChecked())

        self.show_tags_checkbox = QCheckBox("Show tags")
        self.show_tags_checkbox.setChecked(bool(self._settings.get("show_tags", True)))
        layout.addWidget(self.show_tags_checkbox)

        self.auto_open_ingame_checkbox = QCheckBox("Auto-open op.gg live game page")
        self.auto_open_ingame_checkbox.setChecked(bool(self._settings.get("auto_open_ingame_page", True)))
        layout.addWidget(self.auto_open_ingame_checkbox)

        tag_size_row = QHBoxLayout()
        tag_size_row.addWidget(QLabel("Tag size:"))
        self.tag_size_combo = QComboBox()
        for label, value in self.TAG_SIZE_OPTIONS:
            self.tag_size_combo.addItem(label, value)
        current_tag_size = str(self._settings.get("tag_size", "medium"))
        tag_size_index = self.tag_size_combo.findData(current_tag_size)
        self.tag_size_combo.setCurrentIndex(max(0, tag_size_index))
        tag_size_row.addWidget(self.tag_size_combo)
        tag_size_row.addStretch()
        layout.addLayout(tag_size_row)
        self.show_tags_checkbox.toggled.connect(self.tag_size_combo.setEnabled)
        self.tag_size_combo.setEnabled(self.show_tags_checkbox.isChecked())

        self.auto_backup_checkbox = QCheckBox("Automatic versioned backups")
        self.auto_backup_checkbox.setChecked(bool(self._settings.get("auto_backup_enabled", True)))
        layout.addWidget(self.auto_backup_checkbox)

        backup_keep_row = QHBoxLayout()
        keep_backups_tip = (
            "A backup is created each time account data is saved "
            "(for example after add, edit, delete, or import).\n"
            "This value controls how many recent auto backups are kept; "
            "older backups are removed automatically."
        )
        keep_backups_label = QLabel("Keep auto backups:")
        keep_backups_label.setToolTip(keep_backups_tip)
        backup_keep_row.addWidget(keep_backups_label)
        self.auto_backup_keep_combo = QComboBox()
        self.auto_backup_keep_combo.setToolTip(keep_backups_tip)
        for value in self.BACKUP_KEEP_OPTIONS:
            self.auto_backup_keep_combo.addItem(f"{value}", value)
        current_keep = int(self._settings.get("auto_backup_keep_count", 20))
        keep_index = self.auto_backup_keep_combo.findData(current_keep)
        if keep_index < 0:
            # Keep values constrained to the preset choices.
            nearest = min(self.BACKUP_KEEP_OPTIONS, key=lambda option: abs(option - current_keep))
            keep_index = self.auto_backup_keep_combo.findData(nearest)
        self.auto_backup_keep_combo.setCurrentIndex(max(0, keep_index))
        backup_keep_row.addWidget(self.auto_backup_keep_combo)
        backup_keep_row.addStretch()
        layout.addLayout(backup_keep_row)
        self.auto_backup_checkbox.toggled.connect(self.auto_backup_keep_combo.setEnabled)
        self.auto_backup_keep_combo.setEnabled(self.auto_backup_checkbox.isChecked())

        # ── Actions section ────────────────────────────────────────────
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFrameShadow(QFrame.Sunken)
        layout.addSpacing(4)
        layout.addWidget(sep)
        layout.addSpacing(2)

        actions_label = QLabel("Actions")
        actions_label.setStyleSheet("font-weight: bold; font-size: 10pt; color: #888;")
        layout.addWidget(actions_label)

        actions_grid = QGridLayout()
        actions_grid.setSpacing(8)
        actions_grid.setColumnStretch(0, 1)
        actions_grid.setColumnStretch(1, 1)

        mw = self.parent()

        pw_btn = QPushButton("🔑  Change Master Password")
        pw_btn.setToolTip("Update the master encryption password")
        pw_btn.setAutoDefault(False)
        pw_btn.setDefault(False)
        pw_btn.clicked.connect(lambda: mw.change_master_password() if mw else None)
        actions_grid.addWidget(pw_btn, 0, 0)

        about_btn = QPushButton("ℹ  About")
        about_btn.setAutoDefault(False)
        about_btn.setDefault(False)
        about_btn.clicked.connect(lambda: mw.show_about() if mw else None)
        actions_grid.addWidget(about_btn, 0, 1)

        lol_btn = QPushButton("📁  Set LoL Path…")
        lol_btn.setToolTip("Browse for LeagueClient.exe if auto-detection fails")
        lol_btn.setAutoDefault(False)
        lol_btn.setDefault(False)
        lol_btn.clicked.connect(lambda: mw.browse_for_lol() if mw else None)
        actions_grid.addWidget(lol_btn, 1, 0)

        backup_btn = QPushButton("💾  Backup / Restore…")
        backup_btn.setToolTip("Export or import an encrypted account backup")
        backup_btn.setAutoDefault(False)
        backup_btn.setDefault(False)
        backup_btn.clicked.connect(lambda: mw.open_backup_dialog() if mw else None)
        actions_grid.addWidget(backup_btn, 1, 1)

        layout.addLayout(actions_grid)
        layout.addSpacing(4)

        # ── Dialog buttons ─────────────────────────────────────────────
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setFrameShadow(QFrame.Sunken)
        layout.addWidget(sep2)
        layout.addSpacing(2)

        button_row = QHBoxLayout()
        button_row.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedWidth(100)
        cancel_btn.setAutoDefault(False)
        cancel_btn.setDefault(False)
        cancel_btn.clicked.connect(self.reject)
        button_row.addWidget(cancel_btn)
        save_btn = QPushButton("Save")
        save_btn.setFixedWidth(100)
        save_btn.setAutoDefault(False)
        save_btn.setDefault(False)
        save_btn.clicked.connect(self.accept)
        button_row.addWidget(save_btn)
        layout.addLayout(button_row)

        self.setLayout(layout)

    def get_values(self) -> dict:
        """Collect validated settings values."""
        return {
            "start_on_windows_startup": self.startup_checkbox.isChecked(),
            "window_size": self.window_size_combo.currentText(),
            "text_zoom_percent": int(self.text_zoom_combo.currentData()),
            "show_ranks": self.show_ranks_checkbox.isChecked(),
            "show_rank_images": self.show_images_checkbox.isChecked(),
            "show_tags": self.show_tags_checkbox.isChecked(),
            "auto_open_ingame_page": self.auto_open_ingame_checkbox.isChecked(),
            "tag_size": str(self.tag_size_combo.currentData()),
            "auto_backup_enabled": self.auto_backup_checkbox.isChecked(),
            "auto_backup_keep_count": int(self.auto_backup_keep_combo.currentData()),
        }


class AccountListItem(QFrame):
    """Custom widget for displaying account in list"""

    _TAG_COLOR_SLOT_BY_TEXT: dict[str, int] = {}

    _TAG_PALETTE_DARK = [
        ("#0d2f40", "#1a556d", "#93dcff", "#27b5f7"),
        ("#33250c", "#5f4313", "#ffd38a", "#f5a623"),
        ("#133321", "#24613d", "#9de8bd", "#32c46d"),
        ("#35152b", "#662a57", "#f4b5e5", "#de4db5"),
        ("#3a171d", "#6f2d38", "#ffb8c2", "#ff5c7a"),
        ("#202d46", "#374c72", "#b9d2ff", "#5f9cff"),
    ]

    _TAG_PALETTE_LIGHT = [
        ("#e8f7ff", "#badff2", "#0f4c6a", "#1f9ed6"),
        ("#fff5e6", "#f0d3a3", "#6d4a13", "#d18908"),
        ("#ebfaef", "#bde7c8", "#1d6339", "#2fa35d"),
        ("#fff0fb", "#e6c0da", "#7d2f6d", "#c24ea1"),
        ("#fff0f2", "#efc1ca", "#7f3040", "#d75b72"),
        ("#edf2ff", "#c3d0ef", "#27467a", "#4d78db"),
    ]
    
    def __init__(
        self,
        account: Account,
        parent=None,
        show_ranks: bool = True,
        show_rank_images: bool = True,
        show_tags: bool = True,
        tag_size: str = "small",
    ):
        super().__init__(parent)
        self.account = account
        self._show_ranks = show_ranks
        self._show_rank_images = show_rank_images
        self._show_tags = show_tags
        self._tag_size = tag_size
        self.init_ui()

    def _tag_size_preset(self) -> dict:
        presets = {
            "small": {
                "max_height": 14,
                "font_size": 8,
                "padding": "0px 4px 0px 3px",
                "left_border": 2,
                "radius": 3,
                "spacing": 2,
            },
            "medium": {
                "max_height": 16,
                "font_size": 9,
                "padding": "0px 5px 0px 4px",
                "left_border": 2,
                "radius": 4,
                "spacing": 3,
            },
            "large": {
                "max_height": 18,
                "font_size": 10,
                "padding": "0px 6px 0px 5px",
                "left_border": 3,
                "radius": 4,
                "spacing": 3,
            },
        }
        return presets.get(self._tag_size, presets["small"])
    
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
        self._tag_chip_labels: list[QLabel] = []
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

        tags = getattr(self.account, "tags", []) or []
        if self._show_tags and tags:
            size = self._tag_size_preset()
            tags_wrap = QWidget()
            tags_wrap.setAttribute(Qt.WA_TranslucentBackground, True)
            tags_layout = QHBoxLayout(tags_wrap)
            tags_layout.setContentsMargins(0, 0, 0, 0)
            tags_layout.setSpacing(size["spacing"])
            for tag in tags[:4]:
                tag_label = QLabel(f"#{tag}")
                tag_label.setMaximumHeight(size["max_height"])
                tag_label.setStyleSheet(self._tag_chip_stylesheet(tag))
                self._tag_chip_labels.append(tag_label)
                tags_layout.addWidget(tag_label)
            if len(tags) > 4:
                more_label = QLabel(f"+{len(tags) - 4}")
                more_label.setMaximumHeight(size["max_height"])
                more_label.setStyleSheet(self._tag_more_chip_stylesheet())
                self._tag_chip_labels.append(more_label)
                tags_layout.addWidget(more_label)
            user_row.addWidget(tags_wrap)

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

        # Rank block (right side)
        rank_widget = QWidget()
        rank_widget.setAttribute(Qt.WA_TranslucentBackground, True)
        rank_widget.setStyleSheet("background: transparent; border: none;")
        rank_layout = QHBoxLayout(rank_widget)
        rank_layout.setContentsMargins(0, 0, 0, 0)
        rank_layout.setSpacing(6)

        self.rank_icon_label = QLabel()
        self.rank_icon_label.setFixedSize(34, 34)
        self.rank_icon_label.setScaledContents(False)
        self.rank_icon_label.setAttribute(Qt.WA_TranslucentBackground, True)
        self.rank_icon_label.setStyleSheet("background: transparent; border: none;")
        rank_layout.addWidget(self.rank_icon_label)

        self.rank_label = QLabel("...")
        self.rank_label.setAlignment(Qt.AlignVCenter | Qt.AlignRight)
        self.rank_label.setAttribute(Qt.WA_TranslucentBackground, True)
        self.rank_label.setTextFormat(Qt.RichText)
        self.rank_label.setStyleSheet(
            "background: transparent; border: none; color: #8b93a8; font-size: 11px;"
        )
        self.rank_label.setMinimumWidth(190)
        rank_layout.addWidget(self.rank_label)

        self.rank_widget = rank_widget
        self.rank_widget.setVisible(self._show_ranks)
        outer.addWidget(rank_widget)

        self.setLayout(outer)
        self._update_visual_state()

    @classmethod
    def _tag_color_slot_for_text(cls, tag_text: str, palette_size: int) -> int:
        """Assign a random unused color slot for new tag text, then reuse it forever."""
        key = (tag_text or "").strip().lower()
        if not key:
            return 0

        existing = cls._TAG_COLOR_SLOT_BY_TEXT.get(key)
        if existing is not None:
            return existing

        used_slots = {
            slot
            for slot in cls._TAG_COLOR_SLOT_BY_TEXT.values()
            if 0 <= slot < palette_size
        }
        available_slots = [slot for slot in range(palette_size) if slot not in used_slots]
        if available_slots:
            slot = random.choice(available_slots)
        else:
            slot = random.randrange(palette_size)

        cls._TAG_COLOR_SLOT_BY_TEXT[key] = slot
        return slot

    def _tag_chip_stylesheet(self, tag_text: str) -> str:
        """Return themed chip style using text-based random color assignment."""
        palette = self._TAG_PALETTE_DARK if self._dark_mode else self._TAG_PALETTE_LIGHT
        size = self._tag_size_preset()
        idx = self._tag_color_slot_for_text(tag_text, len(palette))
        bg, border, fg, accent = palette[idx]
        return (
            f"background-color: {bg};"
            f"border: 1px solid {border};"
            f"border-left: {size['left_border']}px solid {accent};"
            f"border-radius: {size['radius']}px;"
            f"color: {fg};"
            f"font-size: {size['font_size']}px;"
            "font-weight: 700;"
            f"padding: {size['padding']};"
        )

    def _tag_more_chip_stylesheet(self) -> str:
        """Return style for the overflow chip (+N)."""
        size = self._tag_size_preset()
        if self._dark_mode:
            return (
                "background-color: #2e3448;"
                "border: 1px solid #566080;"
                f"border-left: {size['left_border']}px solid #9fb2e8;"
                f"border-radius: {size['radius']}px;"
                "color: #cfd7f2;"
                f"font-size: {size['font_size']}px;"
                "font-weight: 600;"
                f"padding: {size['padding']};"
            )
        return (
            "background-color: #eef1f7;"
            "border: 1px solid #b7bfd3;"
            f"border-left: {size['left_border']}px solid #93a4ce;"
            f"border-radius: {size['radius']}px;"
            "color: #44506d;"
            f"font-size: {size['font_size']}px;"
            "font-weight: 600;"
            f"padding: {size['padding']};"
        )

    def _refresh_tag_chip_styles(self):
        """Refresh chip colors when theme changes."""
        for label in self._tag_chip_labels:
            text = label.text().strip()
            if text.startswith("+"):
                label.setStyleSheet(self._tag_more_chip_stylesheet())
            else:
                label.setStyleSheet(self._tag_chip_stylesheet(text.lstrip("#")))

    def set_rank(self, rank_data: dict):
        """Update the rank label with fetched op.gg data."""
        if not self._show_ranks:
            self.rank_widget.setVisible(False)
            self.rank_label.setText("")
            self.rank_icon_label.clear()
            self.rank_icon_label.setVisible(False)
            return

        self.rank_widget.setVisible(True)
        status = rank_data.get("status", "error")
        color = rank_data.get("color", "#585b70")
        if status == "ok":
            tier = _escape_html(f"{rank_data.get('tier', '')}{(' ' + rank_data.get('division', '')) if rank_data.get('division') else ''}")
            lp = _escape_html(f"{rank_data.get('lp', '')} LP")
            wins = _escape_html(f"{rank_data.get('wins', '')}W / {rank_data.get('losses', '')}L")
            win_rate = _escape_html(f"{rank_data.get('win_rate', '')}% WR")
            neutral_color = "#8b93a8" if self._dark_mode else "#4b5563"
            self.rank_label.setStyleSheet("background: transparent; border: none; font-size: 11px;")
            pixmap = _build_rank_pixmap(rank_data.get("medal_bytes", b""))
            if not pixmap.isNull():
                pixmap = pixmap.scaled(34, 34, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.rank_icon_label.setPixmap(pixmap)
            self.rank_icon_label.setVisible(self._show_rank_images and not self.rank_icon_label.pixmap().isNull())
            self.rank_label.setText(
                f"<span style='color:{color}; font-weight:600;'>{tier}</span> "
                f"<span style='color:{neutral_color};'>{lp}  {wins}  {win_rate}</span>"
            )
        elif status == "unranked":
            self.rank_icon_label.clear()
            self.rank_icon_label.setVisible(False)
            self.rank_label.setStyleSheet(
                "background: transparent; border: none; color: #585b70; font-size: 11px;"
            )
            self.rank_label.setText("Unranked")
        else:
            self.rank_icon_label.clear()
            self.rank_icon_label.setVisible(False)
            self.rank_label.setStyleSheet(
                "background: transparent; border: none; color: #585b70; font-size: 11px;"
            )
            self.rank_label.setText("")

    def set_rank_display_options(self, show_ranks: bool, show_rank_images: bool):
        """Update rank visibility options."""
        self._show_ranks = show_ranks
        self._show_rank_images = show_rank_images
        self.rank_widget.setVisible(show_ranks)
        if not show_ranks or not show_rank_images:
            self.rank_icon_label.setVisible(False)

    def set_dark_mode(self, enabled: bool):
        self._dark_mode = enabled
        self._refresh_tag_chip_styles()
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
        active = self._selected or self._hovered

        if self._dark_mode:
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
            return

        if active:
            self.setStyleSheet(
                "#accountListItem {"
                "background-color: #eef2ff;"
                "border: 1px solid #c7d2fe;"
                "border-radius: 10px;"
                "}"
            )
            self._shadow.setBlurRadius(10)
            self._shadow.setColor(QColor(15, 23, 42, 28))
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
        self._settings = load_settings()
        self.account_manager: Optional[AccountManager] = None
        self.login_thread: Optional[LoginThread] = None
        self.ingame_watch_thread: Optional[InGameWatcherThread] = None
        self.launch_progress: Optional[QProgressDialog] = None
        self.current_launch_username: Optional[str] = None
        self._dark_mode: bool = self._settings.get('dark_mode', True)
        self._show_ranks: bool = self._settings.get('show_ranks', True)
        self._show_rank_images: bool = self._settings.get('show_rank_images', True)
        self._show_tags: bool = self._settings.get('show_tags', True)
        self._auto_open_ingame_page: bool = bool(self._settings.get('auto_open_ingame_page', True))
        self._tag_size: str = str(self._settings.get('tag_size', 'medium'))
        self._text_zoom_percent: int = int(self._settings.get('text_zoom_percent', 110))
        self._window_size: str = self._settings.get('window_size', '800x600')
        self._search_query: str = ""
        self._tag_filter_value: str = "__all__"
        self._rank_threads: list = []  # keep references so threads aren't GC'd
        self.init_ui()
        app = QApplication.instance()
        if app:
            app.installEventFilter(self)
        self._apply_theme()
        self.check_master_password()
    
    def init_ui(self):
        self.setWindowTitle("League of Legends Account Manager")
        self.setMinimumSize(640, 480)
        width, height = _parse_resolution(self._window_size, fallback=(660, 480))
        self.resize(width, max(480, height))

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        layout.setSpacing(8)
        layout.setContentsMargins(12, 10, 12, 12)

        top_row = QHBoxLayout()
        top_row.setSpacing(8)

        title = QLabel("LOL Account Manager")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        top_row.addWidget(title)

        top_row.addStretch()
        self._theme_button = QPushButton()
        self._theme_button.setObjectName("themeTopButton")
        self._theme_button.setFixedSize(132, 30)
        self._theme_button.setToolTip("Switch between dark and light mode")
        self._theme_button.clicked.connect(self.toggle_theme)
        top_row.addWidget(self._theme_button, 0, Qt.AlignVCenter)
        self._settings_button = QPushButton("⚙")
        self._settings_button.setObjectName("settingsCogButton")
        self._settings_button.setFixedSize(30, 30)
        self._settings_button.setAutoDefault(False)
        self._settings_button.setDefault(False)
        self._settings_button.setToolTip("Open Settings")
        self._settings_button.clicked.connect(self.open_settings_dialog)
        top_row.addWidget(self._settings_button, 0, Qt.AlignVCenter)
        layout.addLayout(top_row)

        filter_row = QHBoxLayout()
        filter_row.addWidget(QLabel("Filters:"))

        self.search_input = QLineEdit()
        self.search_input.setObjectName("accountSearchInput")
        self.search_input.setPlaceholderText("Search by display name, username, or tag")
        self.search_input.textChanged.connect(self._on_filters_changed)
        filter_row.addWidget(self.search_input, 1)

        self.tag_filter_combo = QComboBox()
        self.tag_filter_combo.setMinimumWidth(150)
        self.tag_filter_combo.currentIndexChanged.connect(self._on_filters_changed)
        filter_row.addWidget(self.tag_filter_combo)

        clear_filters_btn = QPushButton("Clear")
        clear_filters_btn.clicked.connect(self._clear_filters)
        filter_row.addWidget(clear_filters_btn)

        layout.addLayout(filter_row)
        
        # Account list
        layout.addWidget(QLabel("Saved Accounts:"))
        self.account_list = QListWidget()
        self.account_list.itemClicked.connect(self.on_account_selected)
        self.account_list.itemDoubleClicked.connect(lambda _: self.launch_account())
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
        self._settings['dark_mode'] = self._dark_mode
        save_settings(self._settings)

    def _theme_with_text_zoom(self, base: str, dark_mode: bool) -> str:
        """Merge base theme with text zoom scaling."""
        point_size = max(8, int(round(9 * self._text_zoom_percent / 100)))
        cog_bg = "#313244" if dark_mode else "#f3f4f6"
        cog_fg = "#cdd6f4" if dark_mode else "#111827"
        cog_border = "#45475a" if dark_mode else "#cfcfcf"
        cog_hover = "#45475a" if dark_mode else "#e5e7eb"
        cog_pressed = "#585b70" if dark_mode else "#d1d5db"
        cog_focus = "#6c7086" if dark_mode else "#9ca3af"
        return (
            base
            + f"\nQWidget {{ font-size: {point_size}pt; }}\n"
            + "\n"
            + "QPushButton#settingsCogButton {\n"
            + "    min-width: 30px;\n"
            + "    max-width: 30px;\n"
            + "    min-height: 30px;\n"
            + "    max-height: 30px;\n"
            + f"    background-color: {cog_bg};\n"
            + f"    color: {cog_fg};\n"
            + f"    border: 1px solid {cog_border};\n"
            + "    border-radius: 5px;\n"
            + "    padding: 0px;\n"
            + "    font-size: 14px;\n"
            + "    margin: 0px;\n"
            + "    text-align: center;\n"
            + "}\n"
            + "QPushButton#settingsCogButton:hover {\n"
            + f"    background-color: {cog_hover};\n"
            + "}\n"
            + "QPushButton#settingsCogButton:pressed {\n"
            + f"    background-color: {cog_pressed};\n"
            + "}\n"
            + "QPushButton#settingsCogButton:focus {\n"
            + "    outline: none;\n"
            + f"    border: 1px solid {cog_focus};\n"
            + "}\n"
            + "QPushButton#themeTopButton {\n"
            + "    min-width: 132px;\n"
            + "    max-width: 132px;\n"
            + "    min-height: 30px;\n"
            + "    max-height: 30px;\n"
            + "    padding: 0px 10px;\n"
            + "    margin: 0px;\n"
            + "    text-align: center;\n"
            + "    min-height: 30px;\n"
            + "}\n"
        )

    def _apply_theme(self):
        """Apply the current theme stylesheet."""
        if self._dark_mode:
            self.setStyleSheet(self._theme_with_text_zoom(DARK_STYLESHEET, dark_mode=True))
            self._theme_button.setText("Light Mode")
            self.search_input.setStyleSheet(
                "QLineEdit#accountSearchInput {"
                "color: #dbe4ff;"
                "background-color: #171a2a;"
                "border: 1px solid #3f4b71;"
                "border-radius: 4px;"
                "padding: 4px 6px;"
                "}"
                "QLineEdit#accountSearchInput::placeholder {"
                "color: #a8b4d6;"
                "}"
            )
        else:
            self.setStyleSheet(self._theme_with_text_zoom(LIGHT_STYLESHEET, dark_mode=False))
            self._theme_button.setText("Dark Mode")
            self.search_input.setStyleSheet(
                "QLineEdit#accountSearchInput {"
                "color: #1f2937;"
                "background-color: #ffffff;"
                "border: 1px solid #cfcfcf;"
                "border-radius: 4px;"
                "padding: 4px 6px;"
                "}"
                "QLineEdit#accountSearchInput::placeholder {"
                "color: #6b7280;"
                "}"
            )

        self.update_account_item_states()
        self._apply_title_bar_theme()

    def open_settings_dialog(self):
        """Open the settings dialog and apply any changes."""
        dialog = SettingsDialog(self, settings=self._settings)
        if dialog.exec_() != QDialog.Accepted:
            return

        values = dialog.get_values()
        self._settings.update(values)
        self._show_ranks = bool(values['show_ranks'])
        self._show_rank_images = bool(values['show_rank_images'])
        self._show_tags = bool(values['show_tags'])
        self._auto_open_ingame_page = bool(values['auto_open_ingame_page'])
        self._tag_size = str(values['tag_size'])
        self._text_zoom_percent = int(values['text_zoom_percent'])
        self._window_size = values['window_size']

        width, height = _parse_resolution(self._window_size, fallback=(660, 480))
        self.resize(width, max(480, height))

        if sys.platform.startswith('win'):
            try:
                _set_startup_enabled(bool(values['start_on_windows_startup']))
            except Exception as exc:
                QMessageBox.warning(self, "Settings", f"Could not update startup setting: {exc}")
        else:
            self._settings['start_on_windows_startup'] = False

        save_settings(self._settings)
        self._apply_theme()
        self.refresh_account_list()

    def _apply_title_bar_theme(self):
        """Update the native Windows title bar to match the active theme."""
        _apply_windows11_chrome(self, self._dark_mode)

    def eventFilter(self, obj, event):
        """Apply consistent Windows 11 chrome to all shown dialogs/message boxes."""
        if event.type() == QEvent.Show and isinstance(obj, QDialog):
            _apply_windows11_chrome(obj, self._dark_mode)
        return super().eventFilter(obj, event)

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

    def _on_filters_changed(self, *_):
        self._search_query = self.search_input.text().strip().lower()
        self._tag_filter_value = str(self.tag_filter_combo.currentData() or "__all__")
        self.refresh_account_list()

    def _clear_filters(self):
        self.search_input.clear()
        idx = self.tag_filter_combo.findData("__all__")
        if idx >= 0:
            self.tag_filter_combo.setCurrentIndex(idx)
        self._on_filters_changed()

    def _rebuild_tag_filter_options(self, accounts: list[Account]):
        selected = str(self.tag_filter_combo.currentData() or "__all__")
        tags = sorted({t for acc in accounts for t in (getattr(acc, 'tags', []) or [])})

        self.tag_filter_combo.blockSignals(True)
        self.tag_filter_combo.clear()
        self.tag_filter_combo.addItem("All tags", "__all__")
        for tag in tags:
            self.tag_filter_combo.addItem(f"#{tag}", tag)

        idx = self.tag_filter_combo.findData(selected)
        if idx < 0:
            idx = 0
        self.tag_filter_combo.setCurrentIndex(idx)
        self.tag_filter_combo.blockSignals(False)
        self._tag_filter_value = str(self.tag_filter_combo.currentData() or "__all__")

    def _account_matches_filters(self, account: Account) -> bool:
        if self._tag_filter_value != "__all__":
            tags = set(getattr(account, 'tags', []) or [])
            if self._tag_filter_value not in tags:
                return False

        if self._search_query:
            haystack = " ".join([
                str(getattr(account, 'display_name', '') or ''),
                str(getattr(account, 'username', '') or ''),
                str(getattr(account, 'tag_line', '') or ''),
                " ".join(getattr(account, 'tags', []) or []),
            ]).lower()
            if self._search_query not in haystack:
                return False

        return True
    
    def refresh_account_list(self):
        """Refresh the account list display"""
        self.account_list.clear()
        
        if not self.account_manager:
            return
        
        accounts = self.account_manager.get_all_accounts()
        self._rebuild_tag_filter_options(accounts)
        filtered_accounts = [acc for acc in accounts if self._account_matches_filters(acc)]
        
        if not accounts:
            item = QListWidgetItem()
            item.setText("No accounts saved. Click 'Add Account' to get started.")
            item.setFlags(item.flags() & ~Qt.ItemIsSelectable)
            self.account_list.addItem(item)
            self.launch_btn.setEnabled(False)
            self.edit_btn.setEnabled(False)
            self.delete_btn.setEnabled(False)
        elif not filtered_accounts:
            item = QListWidgetItem()
            item.setText("No accounts match current filters.")
            item.setFlags(item.flags() & ~Qt.ItemIsSelectable)
            self.account_list.addItem(item)
            self.launch_btn.setEnabled(False)
            self.edit_btn.setEnabled(False)
            self.delete_btn.setEnabled(False)
        else:
            for account in filtered_accounts:
                item = QListWidgetItem()
                item.setData(Qt.UserRole, account.username)
                item.setSizeHint(QSize(0, 84))
                self.account_list.addItem(item)
                
                # Create custom widget
                widget = AccountListItem(
                    account,
                    show_ranks=self._show_ranks,
                    show_rank_images=self._show_rank_images,
                    show_tags=self._show_tags,
                    tag_size=self._tag_size,
                )
                self.account_list.setItemWidget(item, widget)

            self.update_account_item_states()
            if self._show_ranks:
                self._start_rank_fetches()
    
    def _start_rank_fetches(self):
        """Kick off a background rank fetch for every visible account row."""
        if not self._show_ranks:
            return

        # Stop leftover threads from a previous refresh
        for t in self._rank_threads:
            t.quit()
        self._rank_threads.clear()

        for index in range(self.account_list.count()):
            item = self.account_list.item(index)
            widget = self.account_list.itemWidget(item)
            if not isinstance(widget, AccountListItem):
                continue
            account = widget.account
            # Use display_name if set, otherwise fall back to username
            display_name = (getattr(account, 'display_name', '') or '').strip() or account.username
            tag_line = (getattr(account, 'tag_line', '') or 'NA1').strip() or 'NA1'
            region = (getattr(account, 'region', '') or 'NA').strip() or 'NA'
            thread = RankFetchThread(
                account.username,
                display_name,
                tag_line,
                region,
            )
            thread.result_ready.connect(self._on_rank_result)
            self._rank_threads.append(thread)
            thread.start()

    def _on_rank_result(self, username: str, rank_data: dict):
        """Update the matching AccountListItem widget with fresh rank data."""
        for index in range(self.account_list.count()):
            item = self.account_list.item(index)
            widget = self.account_list.itemWidget(item)
            if isinstance(widget, AccountListItem) and widget.account.username == username:
                widget.set_rank(rank_data)
                break

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
        menu.setWindowFlags(menu.windowFlags() | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
        menu.setAttribute(Qt.WA_TranslucentBackground, True)
        menu.setContentsMargins(0, 0, 0, 0)
        menu.setStyleSheet(self._account_context_menu_stylesheet())
        copy_username_action = menu.addAction("Copy Username")
        copy_password_action = menu.addAction("Copy Password")
        copy_friend_code_action = menu.addAction("Copy Friend Code")

        chosen_action = menu.exec_(self.account_list.viewport().mapToGlobal(position))
        if chosen_action == copy_username_action:
            self.copy_to_clipboard(account.username)
        elif chosen_action == copy_password_action:
            self.copy_to_clipboard(account.password)
        elif chosen_action == copy_friend_code_action:
            friend_code = f"{account.display_name} #{getattr(account, 'tag_line', 'NA1')}"
            self.copy_to_clipboard(friend_code)

    def copy_to_clipboard(self, text: str):
        """Copy text to the system clipboard."""
        QApplication.clipboard().setText(text)

    def _account_context_menu_stylesheet(self):
        """Return a theme-matched stylesheet for the account context menu."""
        if self._dark_mode:
            return """
QMenu {
    background-color: #1e1e2e;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 12px;
    padding: 6px;
    margin: 0px;
}
QMenu::item {
    padding: 8px 24px 8px 18px;
    background: transparent;
    margin: 0px 4px;
}
QMenu::item:selected {
    background-color: #45475a;
    color: #ffffff;
    border-radius: 8px;
}
QMenu::separator {
    height: 1px;
    background: #313244;
    margin: 6px 10px;
}
"""

        return """
QMenu {
    background-color: #ffffff;
    color: #1f2937;
    border: 1px solid #d1d5db;
    border-radius: 12px;
    padding: 6px;
    margin: 0px;
}
QMenu::item {
    padding: 8px 24px 8px 18px;
    background: transparent;
    margin: 0px 4px;
}
QMenu::item:selected {
    background-color: #e5e7eb;
    color: #111827;
    border-radius: 8px;
}
QMenu::separator {
    height: 1px;
    background: #e5e7eb;
    margin: 6px 10px;
}
"""

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
                    tags=data['tags'],
                    notes=data['notes'],
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
                    tags=data['tags'],
                    notes=data['notes'],
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

        self._stop_ingame_watcher()

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
            account = self.account_manager.get_account(username) if self.account_manager else None
            if account and self._auto_open_ingame_page:
                self._start_ingame_watcher(account)
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
        self._stop_ingame_watcher()
        self._show_error("Error", f"Launch failed: {error}")

    def _build_opgg_ingame_url(self, account: Account) -> str:
        """Build op.gg in-game spectator URL for an account."""
        region_code = (getattr(account, "region", "NA") or "NA").upper()
        region_slug = OPGG_REGION_MAP.get(region_code, region_code.lower())
        display_name = (getattr(account, "display_name", "") or "").strip() or account.username
        tag_line = (getattr(account, "tag_line", "") or "NA1").strip() or "NA1"
        encoded_name = quote(display_name, safe="")
        encoded_tag = quote(tag_line, safe="")
        return f"https://op.gg/lol/summoners/{region_slug}/{encoded_name}-{encoded_tag}/ingame"

    def _start_ingame_watcher(self, account: Account):
        """Start watching for active-game state and open op.gg once detected."""
        self._stop_ingame_watcher()
        opgg_url = self._build_opgg_ingame_url(account)
        self.ingame_watch_thread = InGameWatcherThread(opgg_url)
        self.ingame_watch_thread.ingame_detected.connect(self._open_ingame_webpage)
        self.ingame_watch_thread.finished.connect(self._clear_ingame_watcher)
        self.ingame_watch_thread.start()

    def _open_ingame_webpage(self, url: str):
        """Open op.gg in-game page in the system browser."""
        try:
            webbrowser.open_new_tab(url)
        except Exception:
            webbrowser.open(url)

    def _stop_ingame_watcher(self):
        """Stop any existing in-game watcher thread."""
        watcher = self.ingame_watch_thread
        self.ingame_watch_thread = None  # clear first so deferred finished signals don't clobber new watcher
        if watcher:
            try:
                watcher.ingame_detected.disconnect()
                watcher.finished.disconnect()
            except Exception:
                pass
            if watcher.isRunning():
                watcher.requestInterruption()
                watcher.wait(1200)

    def _clear_ingame_watcher(self):
        """Clear completed watcher thread reference."""
        self.ingame_watch_thread = None

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
                                    tags=getattr(account, 'tags', []) or [],
                                    notes=getattr(account, 'notes', '') or "",
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
