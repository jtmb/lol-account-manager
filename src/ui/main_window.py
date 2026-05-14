"""Main application window"""
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QListWidget, QListWidgetItem, QLabel, QDialog, QLineEdit,
    QMessageBox, QFrame, QFileDialog, QComboBox, QProgressBar, QTabWidget,
    QDateEdit, QGraphicsDropShadowEffect, QMenu, QCheckBox, QGridLayout,
    QTextEdit, QSpinBox, QSystemTrayIcon, QAction, QCompleter
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize, QTimer, QDate, QEvent, QRectF
from PyQt5.QtGui import QFont, QColor, QPixmap, QPalette, QPainter, QLinearGradient, QRadialGradient, QPainterPath
from pathlib import Path
from typing import Optional, Callable
import sys
import ctypes
import time
import random
import webbrowser
import logging
import json
import os
import tempfile
import subprocess
import shutil
import zipfile
import hashlib
import re
from urllib.request import Request, urlopen
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
    BACKUPS_DIR,
    load_settings,
    save_settings,
)
from src import __version__ as APP_VERSION

LOGS_DIR = BACKUPS_DIR.parent / "logs"
LOG_FILE = LOGS_DIR / "app.log"
GITHUB_RELEASES_API = "https://api.github.com/repos/jtmb/lol-account-manager/releases/latest"
DEFAULT_LOGGED_IN_HIGHLIGHT_DARK = "#9ca3af"
DEFAULT_LOGGED_IN_HIGHLIGHT_LIGHT = "#9ca3af"
DEFAULT_ROW_HOVER_HIGHLIGHT_DARK = "#45475a"
DEFAULT_ROW_HOVER_HIGHLIGHT_LIGHT = "#c8c9d1"
HOVER_HIGHLIGHT_THEME_AUTO = "__theme__"
SPLASH_THEME_AUTO = "__none__"
LOCKED_CHAMPION_SPLASH_EDGE_FADE = 80
LOCKED_CHAMPION_SPLASH_INNER_FADE = 75


def _default_logged_in_highlight(dark_mode: bool) -> str:
    """Return theme-appropriate default logged-in highlight color."""
    return DEFAULT_LOGGED_IN_HIGHLIGHT_DARK if dark_mode else DEFAULT_LOGGED_IN_HIGHLIGHT_LIGHT


def _default_row_hover_highlight(dark_mode: bool) -> str:
    """Return theme-appropriate default hover/selection row highlight color."""
    return DEFAULT_ROW_HOVER_HIGHLIGHT_DARK if dark_mode else DEFAULT_ROW_HOVER_HIGHLIGHT_LIGHT


def _resolve_row_hover_highlight(setting_value: str, dark_mode: bool) -> str:
    """Resolve effective hover color from saved setting or theme auto mode."""
    value = str(setting_value or HOVER_HIGHLIGHT_THEME_AUTO).strip()
    if value == HOVER_HIGHLIGHT_THEME_AUTO:
        return _default_row_hover_highlight(dark_mode)
    return value


CHAMPION_SPLASH_OPTIONS = [
    ('Aatrox', 'Aatrox'), ('Ahri', 'Ahri'), ('Akali', 'Akali'), ('Akshan', 'Akshan'),
    ('Alistar', 'Alistar'), ('Ambessa', 'Ambessa'), ('Amumu', 'Amumu'), ('Anivia', 'Anivia'),
    ('Annie', 'Annie'), ('Aphelios', 'Aphelios'), ('Ashe', 'Ashe'), ('Aurelion Sol', 'AurelionSol'),
    ('Aurora', 'Aurora'), ('Azir', 'Azir'), ('Bard', 'Bard'), ("Bel'Veth", 'Belveth'),
    ('Blitzcrank', 'Blitzcrank'), ('Brand', 'Brand'), ('Braum', 'Braum'), ('Briar', 'Briar'),
    ('Caitlyn', 'Caitlyn'), ('Camille', 'Camille'), ('Cassiopeia', 'Cassiopeia'), ("Cho'Gath", 'Chogath'),
    ('Corki', 'Corki'), ('Darius', 'Darius'), ('Diana', 'Diana'), ('Dr. Mundo', 'DrMundo'),
    ('Draven', 'Draven'), ('Ekko', 'Ekko'), ('Elise', 'Elise'), ('Evelynn', 'Evelynn'),
    ('Ezreal', 'Ezreal'), ('Fiddlesticks', 'Fiddlesticks'), ('Fiora', 'Fiora'), ('Fizz', 'Fizz'),
    ('Galio', 'Galio'), ('Gangplank', 'Gangplank'), ('Garen', 'Garen'), ('Gnar', 'Gnar'),
    ('Gragas', 'Gragas'), ('Graves', 'Graves'), ('Gwen', 'Gwen'), ('Hecarim', 'Hecarim'),
    ('Heimerdinger', 'Heimerdinger'), ('Hwei', 'Hwei'), ('Illaoi', 'Illaoi'), ('Irelia', 'Irelia'),
    ('Ivern', 'Ivern'), ('Janna', 'Janna'), ('Jarvan IV', 'JarvanIV'), ('Jax', 'Jax'),
    ('Jayce', 'Jayce'), ('Jhin', 'Jhin'), ('Jinx', 'Jinx'), ("K'Sante", 'KSante'),
    ("Kai'Sa", 'Kaisa'), ('Kalista', 'Kalista'), ('Karma', 'Karma'), ('Karthus', 'Karthus'),
    ('Kassadin', 'Kassadin'), ('Katarina', 'Katarina'), ('Kayle', 'Kayle'), ('Kayn', 'Kayn'),
    ('Kennen', 'Kennen'), ("Kha'Zix", 'Khazix'), ('Kindred', 'Kindred'), ('Kled', 'Kled'),
    ("Kog'Maw", 'KogMaw'), ('LeBlanc', 'Leblanc'), ('Lee Sin', 'LeeSin'), ('Leona', 'Leona'),
    ('Lillia', 'Lillia'), ('Lissandra', 'Lissandra'), ('Lucian', 'Lucian'), ('Lulu', 'Lulu'),
    ('Lux', 'Lux'), ('Malphite', 'Malphite'), ('Malzahar', 'Malzahar'), ('Maokai', 'Maokai'),
    ('Master Yi', 'MasterYi'), ('Milio', 'Milio'), ('Miss Fortune', 'MissFortune'), ('Mordekaiser', 'Mordekaiser'),
    ('Morgana', 'Morgana'), ('Naafiri', 'Naafiri'), ('Nami', 'Nami'), ('Nasus', 'Nasus'),
    ('Nautilus', 'Nautilus'), ('Neeko', 'Neeko'), ('Nidalee', 'Nidalee'), ('Nilah', 'Nilah'),
    ('Nocturne', 'Nocturne'), ('Nunu & Willump', 'Nunu'), ('Olaf', 'Olaf'), ('Orianna', 'Orianna'),
    ('Ornn', 'Ornn'), ('Pantheon', 'Pantheon'), ('Poppy', 'Poppy'), ('Pyke', 'Pyke'),
    ('Qiyana', 'Qiyana'), ('Quinn', 'Quinn'), ('Rakan', 'Rakan'), ('Rammus', 'Rammus'),
    ("Rek'Sai", 'RekSai'), ('Rell', 'Rell'), ('Renata Glasc', 'Renata'), ('Renekton', 'Renekton'),
    ('Rengar', 'Rengar'), ('Riven', 'Riven'), ('Rumble', 'Rumble'), ('Ryze', 'Ryze'),
    ('Samira', 'Samira'), ('Sejuani', 'Sejuani'), ('Senna', 'Senna'), ('Seraphine', 'Seraphine'),
    ('Sett', 'Sett'), ('Shaco', 'Shaco'), ('Shen', 'Shen'), ('Shyvana', 'Shyvana'),
    ('Singed', 'Singed'), ('Sion', 'Sion'), ('Sivir', 'Sivir'), ('Skarner', 'Skarner'),
    ('Smolder', 'Smolder'), ('Sona', 'Sona'), ('Soraka', 'Soraka'), ('Swain', 'Swain'),
    ('Sylas', 'Sylas'), ('Syndra', 'Syndra'), ('Tahm Kench', 'TahmKench'), ('Taliyah', 'Taliyah'),
    ('Talon', 'Talon'), ('Taric', 'Taric'), ('Teemo', 'Teemo'), ('Thresh', 'Thresh'),
    ('Tristana', 'Tristana'), ('Trundle', 'Trundle'), ('Tryndamere', 'Tryndamere'), ('Twisted Fate', 'TwistedFate'),
    ('Twitch', 'Twitch'), ('Udyr', 'Udyr'), ('Urgot', 'Urgot'), ('Varus', 'Varus'),
    ('Vayne', 'Vayne'), ('Veigar', 'Veigar'), ("Vel'Koz", 'Velkoz'), ('Vex', 'Vex'),
    ('Vi', 'Vi'), ('Viego', 'Viego'), ('Viktor', 'Viktor'), ('Vladimir', 'Vladimir'),
    ('Volibear', 'Volibear'), ('Warwick', 'Warwick'), ('Wukong', 'MonkeyKing'), ('Xayah', 'Xayah'),
    ('Xerath', 'Xerath'), ('Xin Zhao', 'XinZhao'), ('Yasuo', 'Yasuo'), ('Yone', 'Yone'),
    ('Yorick', 'Yorick'), ('Yuumi', 'Yuumi'), ('Zac', 'Zac'), ('Zed', 'Zed'),
    ('Zeri', 'Zeri'), ('Ziggs', 'Ziggs'), ('Zilean', 'Zilean'), ('Zoe', 'Zoe'), ('Zyra', 'Zyra'),
]


class AccountListBackgroundFrame(QFrame):
    """Paintable background container for the account list splash art."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._enabled = False
        self._pixmap: Optional[QPixmap] = None
        self._opacity = 25
        self._edge_fade = 55
        self._inner_fade = 20
        self._dark_mode = True

    def set_background(self, enabled: bool, pixmap: Optional[QPixmap], opacity: int, edge_fade: int, inner_fade: int):
        self._enabled = bool(enabled)
        self._pixmap = pixmap
        self._opacity = max(0, min(100, int(opacity)))
        self._edge_fade = max(0, min(100, int(edge_fade)))
        self._inner_fade = max(0, min(100, int(inner_fade)))
        self.update()

    def set_dark_mode(self, enabled: bool):
        self._dark_mode = bool(enabled)
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

        rect = self.rect()
        radius = 6.0
        path = QPainterPath()
        path.addRoundedRect(QRectF(rect.adjusted(1, 1, -1, -1)), radius, radius)
        painter.setClipPath(path)

        base_color = QColor("#181b2b") if self._dark_mode else QColor("#ededf0")
        painter.fillRect(rect, base_color)

        if self._enabled and self._pixmap and not self._pixmap.isNull():
            target = rect.adjusted(1, 1, -1, -1)
            scaled = self._pixmap.scaled(target.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            if self._dark_mode:
                x = max(0, (scaled.width() - target.width()) // 2)
            else:
                # In light mode, keep visual focus to the right so account text remains cleaner on the left.
                x = max(0, int((scaled.width() - target.width()) * 0.68))
            y = max(0, (scaled.height() - target.height()) // 2)
            crop = scaled.copy(x, y, target.width(), target.height())
            effective_opacity = self._opacity
            if not self._dark_mode:
                # Light mode needs a stronger base image to avoid washed-out splash art.
                effective_opacity = min(100, int(self._opacity * 1.25) + 6)
            painter.setOpacity(effective_opacity / 100.0)
            painter.drawPixmap(target.topLeft(), crop)
            painter.setOpacity(1.0)

            if not self._dark_mode:
                # Add a subtle veil across the left content area for text readability.
                readability = QLinearGradient(rect.left(), 0, rect.left() + int(rect.width() * 0.68), 0)
                readability.setColorAt(0.0, QColor(236, 240, 246, 125))
                readability.setColorAt(0.55, QColor(236, 240, 246, 70))
                readability.setColorAt(1.0, QColor(236, 240, 246, 10))
                painter.fillRect(rect, readability)

            edge_alpha_base = 230 if self._dark_mode else 135
            edge_alpha = int(edge_alpha_base * (self._edge_fade / 100.0))
            if edge_alpha > 0:
                edge_color = base_color if self._dark_mode else QColor("#c8ccd6")
                fade_ratio = 0.20 if self._dark_mode else 0.22
                fade_width = max(24, int(min(rect.width(), rect.height()) * fade_ratio))
                left_grad = QLinearGradient(rect.left(), 0, rect.left() + fade_width, 0)
                left_grad.setColorAt(0.0, QColor(edge_color.red(), edge_color.green(), edge_color.blue(), edge_alpha))
                left_grad.setColorAt(1.0, QColor(edge_color.red(), edge_color.green(), edge_color.blue(), 0))
                painter.fillRect(rect.left(), rect.top(), fade_width, rect.height(), left_grad)

                right_grad = QLinearGradient(rect.right(), 0, rect.right() - fade_width, 0)
                right_grad.setColorAt(0.0, QColor(edge_color.red(), edge_color.green(), edge_color.blue(), edge_alpha))
                right_grad.setColorAt(1.0, QColor(edge_color.red(), edge_color.green(), edge_color.blue(), 0))
                painter.fillRect(rect.right() - fade_width, rect.top(), fade_width, rect.height(), right_grad)

                top_grad = QLinearGradient(0, rect.top(), 0, rect.top() + fade_width)
                top_grad.setColorAt(0.0, QColor(edge_color.red(), edge_color.green(), edge_color.blue(), edge_alpha))
                top_grad.setColorAt(1.0, QColor(edge_color.red(), edge_color.green(), edge_color.blue(), 0))
                painter.fillRect(rect.left(), rect.top(), rect.width(), fade_width, top_grad)

                bottom_grad = QLinearGradient(0, rect.bottom(), 0, rect.bottom() - fade_width)
                bottom_grad.setColorAt(0.0, QColor(edge_color.red(), edge_color.green(), edge_color.blue(), edge_alpha))
                bottom_grad.setColorAt(1.0, QColor(edge_color.red(), edge_color.green(), edge_color.blue(), 0))
                painter.fillRect(rect.left(), rect.bottom() - fade_width, rect.width(), fade_width, bottom_grad)

            inner_alpha_base = 120 if self._dark_mode else 110
            inner_alpha = int(inner_alpha_base * (self._inner_fade / 100.0))
            if inner_alpha > 0:
                radial = QRadialGradient(rect.center(), max(rect.width(), rect.height()) * 0.45)
                radial.setColorAt(0.0, QColor(0, 0, 0, inner_alpha))
                radial.setColorAt(0.62, QColor(0, 0, 0, int(inner_alpha * 0.42)))
                radial.setColorAt(1.0, QColor(0, 0, 0, 0))
                painter.fillRect(rect, radial)


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
            caption_color = ctypes.c_int(0xF2F2F2)
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
    padding: 0px;
}
QListWidget::item {
    background: transparent;
    border: none;
    margin: 0px;
    padding: 0px;
}
QListWidget::item:selected {
    background: transparent;
    border: none;
}
QListWidget::item:hover {
    background: transparent;
    border: none;
}
QScrollBar:vertical {
    background: #161a2a;
    width: 12px;
    margin: 2px;
    border: 1px solid #313244;
    border-radius: 6px;
}
QScrollBar::handle:vertical {
    background: #5b6384;
    min-height: 26px;
    border-radius: 5px;
}
QScrollBar::handle:vertical:hover {
    background: #7a85ad;
}
QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    background: transparent;
    height: 0px;
}
QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {
    background: transparent;
}
QScrollBar:horizontal {
    background: #161a2a;
    height: 12px;
    margin: 2px;
    border: 1px solid #313244;
    border-radius: 6px;
}
QScrollBar::handle:horizontal {
    background: #5b6384;
    min-width: 26px;
    border-radius: 5px;
}
QScrollBar::handle:horizontal:hover {
    background: #7a85ad;
}
QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {
    background: transparent;
    width: 0px;
}
QScrollBar::add-page:horizontal,
QScrollBar::sub-page:horizontal {
    background: transparent;
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

QProgressBar {
    border: 1px solid #45475a;
    border-radius: 6px;
    background-color: #181825;
    text-align: center;
    min-height: 16px;
}
QProgressBar::chunk {
    border-radius: 5px;
    background-color: #7aa2f7;
}
QTabWidget::pane {
    border: 1px solid #45475a;
    border-radius: 8px;
    top: -1px;
    background-color: #1e1e2e;
}
QTabBar::tab {
    background-color: #2a2f45;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    padding: 6px 12px;
    margin-right: 4px;
}
QTabBar::tab:selected {
    background-color: #1e1e2e;
    color: #ffffff;
}
QTabBar::tab:hover:!selected {
    background-color: #353b55;
}
"""

LIGHT_STYLESHEET = """
QMainWindow, QDialog, QWidget {
    background-color: #e7e8ec;
    color: #2e2d2a;
}
QListWidget {
    background-color: #ededf0;
    border: 1px solid #c4c6cf;
    border-radius: 6px;
    padding: 0px;
}
QListWidget::item {
    background: transparent;
    border: none;
    margin: 0px;
    padding: 0px;
}
QListWidget::item:selected {
    background: transparent;
    border: none;
}
QListWidget::item:hover {
    background: transparent;
    border: none;
}
QScrollBar:vertical {
    background: #dfdcd6;
    width: 12px;
    margin: 2px;
    border: 1px solid #c4beb4;
    border-radius: 6px;
}
QScrollBar::handle:vertical {
    background: #9b9489;
    min-height: 26px;
    border-radius: 5px;
}
QScrollBar::handle:vertical:hover {
    background: #847c72;
}
QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    background: transparent;
    height: 0px;
}
QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {
    background: transparent;
}
QScrollBar:horizontal {
    background: #dfdcd6;
    height: 12px;
    margin: 2px;
    border: 1px solid #c4beb4;
    border-radius: 6px;
}
QScrollBar::handle:horizontal {
    background: #9b9489;
    min-width: 26px;
    border-radius: 5px;
}
QScrollBar::handle:horizontal:hover {
    background: #847c72;
}
QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {
    background: transparent;
    width: 0px;
}
QScrollBar::add-page:horizontal,
QScrollBar::sub-page:horizontal {
    background: transparent;
}
QPushButton {
    background-color: #d2d3db;
    color: #2e2d2a;
    border: 1px solid #c4c6cf;
    border-radius: 5px;
    padding: 5px 10px;
}
QPushButton:hover {
    background-color: #c8c9d1;
}
QPushButton:pressed {
    background-color: #bebfc8;
}
QPushButton:disabled {
    background-color: #ececf0;
    color: #9a9a9a;
    border: 1px solid #d8d9e1;
}
QLineEdit, QComboBox, QDateEdit, QTextEdit, QPlainTextEdit, QSpinBox {
    background-color: #fafafa;
    color: #2e2d2a;
    border: 1px solid #d0d0d6;
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
    border-left: 1px solid #c4c6cf;
    background-color: #d2d3db;
    border-top-right-radius: 4px;
    border-bottom-right-radius: 4px;
}
QSpinBox::up-button, QSpinBox::down-button {
    subcontrol-origin: border;
    background-color: #d2d3db;
    border-left: 1px solid #c4c6cf;
    width: 16px;
}
QSpinBox::up-button:hover, QSpinBox::down-button:hover {
    background-color: #c8c9d1;
}
QComboBox QAbstractItemView {
    background-color: #fafafa;
    color: #2e2d2a;
    selection-background-color: #e7e8ee;
}
QLabel {
    color: #2e2d2a;
}
QLineEdit::placeholder {
    color: #7c756b;
}
QTabWidget::pane {
    border: 1px solid #c7c1b6;
    border-radius: 8px;
    top: -1px;
    background-color: #e7e8ec;
}
QTabBar::tab {
    background-color: #e7e8ee;
    color: #4a4742;
    border: 1px solid #d0d0d6;
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    padding: 6px 12px;
    margin-right: 4px;
}
QTabBar::tab:selected {
    background-color: #e7e8ec;
    color: #2e2d2a;
}
QTabBar::tab:hover:!selected {
    background-color: #d2d3db;
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
    """Poll Live Client API and emit once for each newly started match."""

    ingame_detected = pyqtSignal(str)  # op.gg url
    status_updated = pyqtSignal(object)  # probe diagnostics dict

    def __init__(self, opgg_url: str, timeout_seconds: int = 21600, poll_interval_seconds: float = 3.0):
        super().__init__()
        self._opgg_url = opgg_url
        self._timeout_seconds = timeout_seconds
        self._poll_interval_seconds = poll_interval_seconds

    def run(self):
        deadline = time.time() + self._timeout_seconds
        opened_for_current_game = False
        consecutive_out_of_game_polls = 0

        while time.time() < deadline:
            if self.isInterruptionRequested():
                return

            probe = RiotClientIntegration.probe_live_client_api(timeout_seconds=1.5)
            probe["watcher_active"] = True
            probe["opgg_url"] = self._opgg_url
            self.status_updated.emit(probe)

            in_game = bool(probe.get("in_game", False))

            if in_game:
                consecutive_out_of_game_polls = 0
                if not opened_for_current_game:
                    self.ingame_detected.emit(self._opgg_url)
                    opened_for_current_game = True
            else:
                # Require two consecutive out-of-game polls before re-arming.
                # This avoids duplicate opens from short local API hiccups.
                consecutive_out_of_game_polls += 1
                if consecutive_out_of_game_polls >= 2:
                    opened_for_current_game = False

            self.msleep(max(200, int(self._poll_interval_seconds * 1000)))


class InGameDiagnosticsDialog(QDialog):
    """Live diagnostics panel for in-game detection polling."""

    def __init__(self, status_provider: Callable[[], dict], test_callback: Callable[[], dict], parent=None):
        super().__init__(parent)
        self._status_provider = status_provider
        self._test_callback = test_callback
        self._last_test_result = "No manual test run yet"
        self.setWindowTitle("In-Game Detection Diagnostics")
        self.setModal(False)
        self.setMinimumSize(520, 330)

        dark_mode = bool(getattr(parent, "_dark_mode", True))
        if dark_mode:
            self.setStyleSheet(
                "QDialog { background-color: #1e1e2e; color: #cdd6f4; }"
                "QLabel#diagHeader { font-size: 12pt; font-weight: 600; color: #e2e8f0; }"
                "QLabel#diagValue { color: #dbe4ff; }"
                "QPushButton {"
                "background-color: #313244; color: #cdd6f4; border: 1px solid #45475a;"
                "border-radius: 6px; padding: 6px 12px;"
                "}"
                "QPushButton:hover { background-color: #45475a; }"
            )
        else:
            self.setStyleSheet(
                "QDialog { background-color: #fafafa; color: #2e2d2a; }"
                "QLabel#diagHeader { font-size: 12pt; font-weight: 600; color: #2e2d2a; }"
                "QLabel#diagValue { color: #2e2d2a; }"
                "QPushButton {"
                "background-color: #d2d3db; color: #2e2d2a; border: 1px solid #c4c6cf;"
                "border-radius: 6px; padding: 6px 12px;"
                "}"
                "QPushButton:hover { background-color: #c8c9d1; }"
            )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        header = QLabel("Watcher diagnostics")
        header.setObjectName("diagHeader")
        layout.addWidget(header)

        self.watcher_state_value = QLabel("-")
        self.watcher_state_value.setObjectName("diagValue")
        self.last_poll_value = QLabel("-")
        self.last_poll_value.setObjectName("diagValue")
        self.api_status_value = QLabel("-")
        self.api_status_value.setObjectName("diagValue")
        self.response_value = QLabel("-")
        self.response_value.setObjectName("diagValue")
        self.error_value = QLabel("-")
        self.error_value.setObjectName("diagValue")
        self.error_value.setWordWrap(True)
        self.last_test_value = QLabel(self._last_test_result)
        self.last_test_value.setObjectName("diagValue")
        self.last_test_value.setWordWrap(True)

        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(6)
        grid.addWidget(QLabel("Watcher state:"), 0, 0)
        grid.addWidget(self.watcher_state_value, 0, 1)
        grid.addWidget(QLabel("Last poll:"), 1, 0)
        grid.addWidget(self.last_poll_value, 1, 1)
        grid.addWidget(QLabel("Live API status:"), 2, 0)
        grid.addWidget(self.api_status_value, 2, 1)
        grid.addWidget(QLabel("Response details:"), 3, 0)
        grid.addWidget(self.response_value, 3, 1)
        grid.addWidget(QLabel("Last error:"), 4, 0)
        grid.addWidget(self.error_value, 4, 1)
        grid.addWidget(QLabel("Manual test:"), 5, 0)
        grid.addWidget(self.last_test_value, 5, 1)
        layout.addLayout(grid)

        button_row = QHBoxLayout()
        button_row.addStretch()
        test_btn = QPushButton("Test detection now")
        test_btn.setAutoDefault(False)
        test_btn.setDefault(False)
        test_btn.clicked.connect(self._on_test_clicked)
        button_row.addWidget(test_btn)
        close_btn = QPushButton("Close")
        close_btn.setAutoDefault(False)
        close_btn.setDefault(False)
        close_btn.clicked.connect(self.close)
        button_row.addWidget(close_btn)
        layout.addLayout(button_row)

        self._status_timer = QTimer(self)
        self._status_timer.setInterval(1000)
        self._status_timer.timeout.connect(self.refresh_status)
        self._status_timer.start()
        self.refresh_status()

    def _on_test_clicked(self):
        result = self._test_callback() or {}
        status = str(result.get("status", "unknown"))
        summary = str(result.get("summary", "No summary"))
        self._last_test_result = f"{status}: {summary}"
        self.last_test_value.setText(self._last_test_result)
        self.refresh_status()

    def refresh_status(self):
        state = self._status_provider() or {}

        watcher_active = bool(state.get("watcher_active", False))
        watcher_state = "Polling" if watcher_active else "Idle"
        self.watcher_state_value.setText(watcher_state)

        timestamp = float(state.get("timestamp", 0) or 0)
        if timestamp > 0:
            self.last_poll_value.setText(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp)))
        else:
            self.last_poll_value.setText("No poll yet")

        status = str(state.get("status", "unknown"))
        summary = str(state.get("summary", "No summary"))
        self.api_status_value.setText(f"{status} - {summary}")

        status_code = state.get("status_code")
        response_bytes = int(state.get("response_bytes", 0) or 0)
        code_text = "none" if status_code is None else str(status_code)
        self.response_value.setText(f"status_code={code_text}, bytes={response_bytes}")

        error = str(state.get("error", "") or "None")
        self.error_value.setText(error)

    def closeEvent(self, event):
        self._status_timer.stop()
        super().closeEvent(event)


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


class LaunchProgressDialog(QDialog):
    """Compact launch dialog with predictable proportions."""

    def __init__(self, message: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Launching...")
        self.setModal(True)
        self.setMinimumSize(440, 170)
        self.setMaximumWidth(560)
        self.setAttribute(Qt.WA_StyledBackground, True)

        dark_mode = bool(getattr(parent, "_dark_mode", True))
        if dark_mode:
            self.setStyleSheet(
                "QDialog {"
                "background-color: #1e1e2e;"
                "color: #cdd6f4;"
                "}"
                "QLabel#launchTitle {"
                "font-size: 12pt;"
                "font-weight: 600;"
                "color: #e2e8f0;"
                "}"
                "QLabel#launchMessage {"
                "font-size: 10.5pt;"
                "color: #cdd6f4;"
                "}"
                "QProgressBar {"
                "border: 1px solid #45475a;"
                "border-radius: 7px;"
                "background-color: #181825;"
                "text-align: center;"
                "min-height: 18px;"
                "}"
                "QProgressBar::chunk {"
                "border-radius: 6px;"
                "background-color: #7aa2f7;"
                "}"
                "QPushButton {"
                "background-color: #313244;"
                "color: #cdd6f4;"
                "border: 1px solid #45475a;"
                "border-radius: 5px;"
                "padding: 6px 12px;"
                "}"
                "QPushButton:hover { background-color: #45475a; }"
                "QPushButton:pressed { background-color: #585b70; }"
            )
        else:
            self.setStyleSheet(
                "QDialog {"
                "background-color: #f4f4f4;"
                "color: #2e2d2a;"
                "}"
                "QLabel#launchTitle {"
                "font-size: 12pt;"
                "font-weight: 600;"
                "background-color: transparent;"
                "color: #2e2d2a;"
                "}"
                "QLabel#launchMessage {"
                "font-size: 10.5pt;"
                "background-color: transparent;"
                "color: #49453f;"
                "}"
                "QProgressBar {"
                "border: 1px solid #d0d0d6;"
                "border-radius: 7px;"
                "background-color: #f0f1f5;"
                "text-align: center;"
                "min-height: 18px;"
                "}"
                "QProgressBar::chunk {"
                "border-radius: 6px;"
                "background-color: #b6b8c3;"
                "}"
                "QPushButton {"
                "background-color: #d2d3db;"
                "color: #2e2d2a;"
                "border: 1px solid #c4c6cf;"
                "border-radius: 5px;"
                "padding: 6px 12px;"
                "}"
                "QPushButton:hover { background-color: #c8c9d1; }"
                "QPushButton:pressed { background-color: #bebfc8; }"
            )

        self._title_label = QLabel("Starting launch")
        self._title_label.setObjectName("launchTitle")
        self._message_label = QLabel(message)
        self._message_label.setObjectName("launchMessage")
        self._message_label.setWordWrap(True)

        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 0)
        self._progress_bar.setTextVisible(False)

        self._close_button = QPushButton("Close")
        self._close_button.setAutoDefault(False)
        self._close_button.setDefault(False)
        self._close_button.setFixedWidth(86)
        self._close_button.clicked.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        layout.addWidget(self._title_label)
        layout.addWidget(self._message_label)
        layout.addWidget(self._progress_bar)

        button_row = QHBoxLayout()
        button_row.addStretch()
        button_row.addWidget(self._close_button)
        layout.addLayout(button_row)

    def set_message(self, message: str):
        self._message_label.setText(message)


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

    CUSTOM_SIZE_VALUE = "__custom__"

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

    LOGGED_IN_COLOR_OPTIONS = [
        ("Theme Gray (Light Button)", "#d2d3db"),
        ("Soft Silver", "#c6ccd8"),
        ("Cool Gray", "#9ca3af"),
        ("Slate", "#6b7280"),
        ("Blue", "#4f7cff"),
        ("Cyan", "#27b5f7"),
        ("Green", "#32c46d"),
        ("Purple", "#8b5cf6"),
        ("Rose", "#e85d8a"),
        ("Amber", "#f5a623"),
    ]

    HOVER_HIGHLIGHT_COLOR_OPTIONS = [
        ("Global Theme (Auto)", HOVER_HIGHLIGHT_THEME_AUTO),
        ("Theme Gray (Button Hover)", "#c8c9d1"),
        ("Charcoal (Dark Hover)", "#45475a"),
        ("Soft Silver", "#c6ccd8"),
        ("Cool Gray", "#9ca3af"),
        ("Slate", "#6b7280"),
        ("Blue", "#4f7cff"),
        ("Cyan", "#27b5f7"),
        ("Green", "#32c46d"),
        ("Purple", "#8b5cf6"),
        ("Rose", "#e85d8a"),
        ("Amber", "#f5a623"),
    ]

    CHAMPION_SPLASH_OPTIONS = CHAMPION_SPLASH_OPTIONS

    CHAMPION_SPLASH_OPACITY_OPTIONS = [
        ("Off (0%)", 0),
        ("Very Subtle (10%)", 10),
        ("Subtle (20%)", 20),
        ("Balanced (30%)", 30),
        ("Visible (40%)", 40),
        ("Strong (55%)", 55),
        ("Bold (70%)", 70),
    ]

    LOGGED_IN_INTENSITY_OPTIONS = [
        ("Ultra Subtle (5%)", 5),
        ("Very Soft (10%)", 10),
        ("Soft (15%)", 15),
        ("Very Subtle (20%)", 20),
        ("Subtle (35%)", 35),
        ("Balanced (50%)", 50),
        ("Strong (70%)", 70),
        ("Bold (90%)", 90),
    ]

    LOGGED_IN_BORDER_WIDTH_OPTIONS = [
        ("Thin (2px)", 2),
        ("Balanced (3px)", 3),
        ("Bold (4px)", 4),
        ("Heavy (5px)", 5),
    ]

    LOGGED_IN_BORDER_OPACITY_OPTIONS = [
        ("Subtle (60%)", 60),
        ("Balanced (80%)", 80),
        ("Full (100%)", 100),
        ("Boosted (120%)", 120),
    ]

    ROW_DENSITY_OPTIONS = [
        ("Compact", "compact"),
        ("Comfortable", "comfortable"),
        ("Spacious", "spacious"),
    ]

    RANK_ICON_SIZE_OPTIONS = [
        ("Small (28px)", 28),
        ("Medium (34px)", 34),
        ("Large (40px)", 40),
    ]

    RANK_TEXT_BRIGHTNESS_OPTIONS = [
        ("Subdued (85%)", 85),
        ("Normal (100%)", 100),
        ("Bright (115%)", 115),
        ("High Contrast (130%)", 130),
    ]

    TAG_STYLE_OPTIONS = [
        ("Muted", "muted"),
        ("Vibrant", "vibrant"),
        ("Monochrome", "monochrome"),
    ]

    CLOSE_BEHAVIOR_OPTIONS = [
        ("Exit app", "exit"),
        ("Minimize to tray", "tray"),
    ]

    AUTO_LOCK_OPTIONS = [
        ("Disabled", 0),
        ("5 minutes", 5),
        ("15 minutes", 15),
        ("30 minutes", 30),
        ("60 minutes", 60),
    ]

    CLIPBOARD_CLEAR_OPTIONS = [
        ("Never", 0),
        ("15 seconds", 15),
        ("30 seconds", 30),
        ("60 seconds", 60),
    ]

    RANK_REFRESH_OPTIONS = [
        ("Manual", "manual"),
        ("Auto (30s)", "30"),
        ("Auto (60s)", "60"),
        ("Auto (120s)", "120"),
    ]

    ACCOUNT_SORT_OPTIONS = [
        ("Manual", "manual"),
        ("Last Used", "last_used"),
        ("Alphabetical", "alphabetical"),
    ]

    LOG_LEVEL_OPTIONS = [
        ("Error", "ERROR"),
        ("Warning", "WARNING"),
        ("Info", "INFO"),
        ("Debug", "DEBUG"),
    ]

    BACKUP_KEEP_OPTIONS = [10, 20, 40, 80]

    def __init__(self, parent=None, settings: Optional[dict] = None, apply_callback: Optional[Callable[[dict], None]] = None):
        super().__init__(parent)
        self._settings = settings or {}
        self._apply_callback = apply_callback
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Settings")
        self.setModal(True)
        self.setMinimumWidth(620)

        layout = QVBoxLayout()

        tabs = QTabWidget()
        general_tab = QWidget()
        appearance_tab = QWidget()
        advanced_tab = QWidget()
        general_layout = QVBoxLayout(general_tab)
        appearance_layout = QVBoxLayout(appearance_tab)
        advanced_layout = QVBoxLayout(advanced_tab)
        general_layout.setSpacing(8)
        appearance_layout.setSpacing(8)
        advanced_layout.setSpacing(8)

        startup_default = self._settings.get("start_on_windows_startup", _is_startup_enabled())
        self.startup_checkbox = QCheckBox("Start Program at Windows startup")
        self.startup_checkbox.setChecked(bool(startup_default))
        self.startup_checkbox.setEnabled(sys.platform.startswith("win"))
        self.startup_checkbox.setToolTip("Launch the app automatically when you sign in to Windows.")
        if not sys.platform.startswith("win"):
            self.startup_checkbox.setToolTip("Available on Windows only")
        general_layout.addWidget(self.startup_checkbox)

        general_layout.addWidget(QLabel("Window size:"))
        self.window_size_combo = QComboBox()
        self.current_window_size = str(self._settings.get("current_window_size", self._settings.get("window_size", "800x600")))
        custom_label = f"Remember current size ({self.current_window_size})"
        self.window_size_combo.addItem(custom_label, self.CUSTOM_SIZE_VALUE)
        self.window_size_combo.addItems(self.COMMON_RESOLUTIONS)
        self.window_size_combo.setToolTip(
            "Choose a fixed startup size, or select Remember current size to keep the last manually resized window."
        )
        current_resolution = self._settings.get("window_size", "800x600")
        current_mode = str(self._settings.get("window_size_mode", "")).strip().lower()
        if current_mode not in {"static", "custom"}:
            current_mode = "custom" if current_resolution not in self.COMMON_RESOLUTIONS else "static"
        if current_mode == "custom":
            self.window_size_combo.setCurrentIndex(0)
        else:
            index = self.window_size_combo.findText(current_resolution)
            if index < 0:
                index = 0
            self.window_size_combo.setCurrentIndex(index)
        general_layout.addWidget(self.window_size_combo)

        appearance_layout.addWidget(QLabel("Text Size:"))
        self.text_zoom_combo = QComboBox()
        for label, value in self.TEXT_ZOOM_OPTIONS:
            self.text_zoom_combo.addItem(label, value)
        self.text_zoom_combo.setToolTip("Increase or decrease the UI text size for readability.")
        current_zoom = int(self._settings.get("text_zoom_percent", 100))
        zoom_index = self.text_zoom_combo.findData(current_zoom)
        if zoom_index < 0:
            self.text_zoom_combo.addItem(f"{current_zoom}%", current_zoom)
            zoom_index = self.text_zoom_combo.findData(current_zoom)
        self.text_zoom_combo.setCurrentIndex(max(0, zoom_index))
        appearance_layout.addWidget(self.text_zoom_combo)

        self.show_ranks_checkbox = QCheckBox("Show ranks")
        self.show_ranks_checkbox.setChecked(bool(self._settings.get("show_ranks", True)))
        self.show_ranks_checkbox.setToolTip("Show or hide op.gg rank information on each account row.")
        appearance_layout.addWidget(self.show_ranks_checkbox)

        self.show_images_checkbox = QCheckBox("Show rank images")
        self.show_images_checkbox.setChecked(bool(self._settings.get("show_rank_images", True)))
        self.show_images_checkbox.setToolTip("Show or hide the rank medal image next to each account.")
        appearance_layout.addWidget(self.show_images_checkbox)
        self.show_ranks_checkbox.toggled.connect(self.show_images_checkbox.setEnabled)
        self.show_images_checkbox.setEnabled(self.show_ranks_checkbox.isChecked())

        self.show_tags_checkbox = QCheckBox("Show tags")
        self.show_tags_checkbox.setChecked(bool(self._settings.get("show_tags", True)))
        self.show_tags_checkbox.setToolTip("Show or hide account tags under each account entry.")
        appearance_layout.addWidget(self.show_tags_checkbox)

        self.auto_open_ingame_checkbox = QCheckBox("Auto-open op.gg live game page")
        self.auto_open_ingame_checkbox.setChecked(bool(self._settings.get("auto_open_ingame_page", True)))
        self.auto_open_ingame_checkbox.setToolTip(
            "Automatically open the op.gg in-game page when a live match is detected."
        )
        general_layout.addWidget(self.auto_open_ingame_checkbox)

        self.start_minimized_checkbox = QCheckBox("Start minimized to tray")
        self.start_minimized_checkbox.setChecked(bool(self._settings.get("start_minimized_to_tray", False)))
        self.start_minimized_checkbox.setToolTip("Start hidden in system tray instead of opening the full window.")
        general_layout.addWidget(self.start_minimized_checkbox)

        close_behavior_row = QHBoxLayout()
        close_behavior_row.addWidget(QLabel("Close button behavior:"))
        self.close_behavior_combo = QComboBox()
        for label, value in self.CLOSE_BEHAVIOR_OPTIONS:
            self.close_behavior_combo.addItem(label, value)
        current_close_behavior = str(self._settings.get("close_behavior", "tray"))
        close_behavior_index = self.close_behavior_combo.findData(current_close_behavior)
        self.close_behavior_combo.setCurrentIndex(max(0, close_behavior_index))
        self.close_behavior_combo.setToolTip("Choose whether window close exits app or minimizes to tray.")
        close_behavior_row.addWidget(self.close_behavior_combo)
        close_behavior_row.addStretch()
        general_layout.addLayout(close_behavior_row)

        auto_lock_row = QHBoxLayout()
        auto_lock_row.addWidget(QLabel("Auto-lock timeout:"))
        self.auto_lock_combo = QComboBox()
        for label, value in self.AUTO_LOCK_OPTIONS:
            self.auto_lock_combo.addItem(label, value)
        current_auto_lock = int(self._settings.get("auto_lock_minutes", 0))
        auto_lock_index = self.auto_lock_combo.findData(current_auto_lock)
        self.auto_lock_combo.setCurrentIndex(max(0, auto_lock_index))
        self.auto_lock_combo.setToolTip("Require master password again after inactivity.")
        auto_lock_row.addWidget(self.auto_lock_combo)
        auto_lock_row.addStretch()
        general_layout.addLayout(auto_lock_row)

        self.remember_password_24h_checkbox = QCheckBox("Remember master password for 24 hours")
        self.remember_password_24h_checkbox.setChecked(bool(self._settings.get("remember_password_24h", True)))
        self.remember_password_24h_checkbox.setToolTip(
            "Skip password prompts on startup and auto-lock events for 24 hours after successful unlock."
        )
        general_layout.addWidget(self.remember_password_24h_checkbox)

        clipboard_row = QHBoxLayout()
        clipboard_row.addWidget(QLabel("Clipboard auto-clear:"))
        self.clipboard_clear_combo = QComboBox()
        for label, value in self.CLIPBOARD_CLEAR_OPTIONS:
            self.clipboard_clear_combo.addItem(label, value)
        current_clipboard_clear = int(self._settings.get("clipboard_auto_clear_seconds", 0))
        clipboard_index = self.clipboard_clear_combo.findData(current_clipboard_clear)
        self.clipboard_clear_combo.setCurrentIndex(max(0, clipboard_index))
        self.clipboard_clear_combo.setToolTip("Automatically clear copied credentials after a delay.")
        clipboard_row.addWidget(self.clipboard_clear_combo)
        clipboard_row.addStretch()
        general_layout.addLayout(clipboard_row)

        self.confirm_launch_checkbox = QCheckBox("Ask confirmation before launch")
        self.confirm_launch_checkbox.setChecked(bool(self._settings.get("confirm_before_launch", True)))
        general_layout.addWidget(self.confirm_launch_checkbox)

        self.confirm_delete_checkbox = QCheckBox("Ask confirmation before delete")
        self.confirm_delete_checkbox.setChecked(bool(self._settings.get("confirm_before_delete", True)))
        general_layout.addWidget(self.confirm_delete_checkbox)

        sort_mode_row = QHBoxLayout()
        sort_mode_row.addWidget(QLabel("Account sort mode:"))
        self.account_sort_mode_combo = QComboBox()
        for label, value in self.ACCOUNT_SORT_OPTIONS:
            self.account_sort_mode_combo.addItem(label, value)
        current_sort_mode = str(self._settings.get("account_sort_mode", "manual"))
        sort_mode_index = self.account_sort_mode_combo.findData(current_sort_mode)
        self.account_sort_mode_combo.setCurrentIndex(max(0, sort_mode_index))
        self.account_sort_mode_combo.setToolTip("Choose how accounts are ordered in the list.")
        sort_mode_row.addWidget(self.account_sort_mode_combo)
        sort_mode_row.addStretch()
        general_layout.addLayout(sort_mode_row)

        security_row = QHBoxLayout()
        security_row.addWidget(QLabel("Security:"))
        change_pw_btn = QPushButton("Change master password")
        change_pw_btn.setAutoDefault(False)
        change_pw_btn.setDefault(False)
        change_pw_btn.clicked.connect(lambda: mw.change_master_password() if mw else None)
        security_row.addWidget(change_pw_btn)
        security_row.addStretch()
        general_layout.addLayout(security_row)

        rank_refresh_row = QHBoxLayout()
        rank_refresh_row.addWidget(QLabel("Rank refresh cadence:"))
        self.rank_refresh_combo = QComboBox()
        for label, value in self.RANK_REFRESH_OPTIONS:
            self.rank_refresh_combo.addItem(label, value)
        current_rank_refresh = str(self._settings.get("rank_refresh_mode", "manual"))
        rank_refresh_index = self.rank_refresh_combo.findData(current_rank_refresh)
        self.rank_refresh_combo.setCurrentIndex(max(0, rank_refresh_index))
        rank_refresh_row.addWidget(self.rank_refresh_combo)
        rank_refresh_row.addStretch()
        general_layout.addLayout(rank_refresh_row)

        self.auto_check_updates_checkbox = QCheckBox("Auto-check updates on startup")
        self.auto_check_updates_checkbox.setChecked(bool(self._settings.get("auto_check_updates", True)))
        general_layout.addWidget(self.auto_check_updates_checkbox)

        update_row = QHBoxLayout()
        update_row.addWidget(QLabel("Update:"))
        check_updates_btn = QPushButton("Check for updates now")
        check_updates_btn.setAutoDefault(False)
        check_updates_btn.setDefault(False)
        check_updates_btn.clicked.connect(lambda: mw.check_for_updates_now() if mw and hasattr(mw, "check_for_updates_now") else None)
        update_row.addWidget(check_updates_btn)
        update_row.addStretch()
        general_layout.addLayout(update_row)

        paths_row = QHBoxLayout()
        paths_row.addWidget(QLabel("League client path:"))
        lol_path_btn = QPushButton("Set LoL Path...")
        lol_path_btn.setAutoDefault(False)
        lol_path_btn.setDefault(False)
        lol_path_btn.clicked.connect(lambda: mw.browse_for_lol() if mw else None)
        paths_row.addWidget(lol_path_btn)
        paths_row.addStretch()
        general_layout.addLayout(paths_row)

        diagnostics_label = QLabel("Diagnostics")
        diagnostics_label.setStyleSheet("font-weight: 600;")
        advanced_layout.addWidget(diagnostics_label)

        diagnostics_row = QHBoxLayout()
        diagnostics_row.addWidget(QLabel("Diagnostics log level:"))
        self.log_level_combo = QComboBox()
        for label, value in self.LOG_LEVEL_OPTIONS:
            self.log_level_combo.addItem(label, value)
        current_log_level = str(self._settings.get("diagnostics_log_level", "INFO")).upper()
        log_level_index = self.log_level_combo.findData(current_log_level)
        self.log_level_combo.setCurrentIndex(max(0, log_level_index))
        diagnostics_row.addWidget(self.log_level_combo)
        open_logs_btn = QPushButton("Open logs folder")
        open_logs_btn.setAutoDefault(False)
        open_logs_btn.setDefault(False)
        mw = self.parent()
        open_logs_btn.clicked.connect(lambda: mw.open_logs_folder() if mw else None)
        diagnostics_row.addWidget(open_logs_btn)
        watcher_diag_btn = QPushButton("Watcher diagnostics")
        watcher_diag_btn.setAutoDefault(False)
        watcher_diag_btn.setDefault(False)
        watcher_diag_btn.clicked.connect(lambda: mw.open_ingame_diagnostics() if mw and hasattr(mw, "open_ingame_diagnostics") else None)
        diagnostics_row.addWidget(watcher_diag_btn)
        diagnostics_row.addStretch()
        advanced_layout.addLayout(diagnostics_row)

        tag_size_row = QHBoxLayout()
        tag_size_row.addWidget(QLabel("Tag size:"))
        self.tag_size_combo = QComboBox()
        for label, value in self.TAG_SIZE_OPTIONS:
            self.tag_size_combo.addItem(label, value)
        self.tag_size_combo.setToolTip("Choose how large the tag badges appear on account rows.")
        current_tag_size = str(self._settings.get("tag_size", "medium"))
        tag_size_index = self.tag_size_combo.findData(current_tag_size)
        self.tag_size_combo.setCurrentIndex(max(0, tag_size_index))
        tag_size_row.addWidget(self.tag_size_combo)
        tag_size_row.addStretch()
        appearance_layout.addLayout(tag_size_row)
        self.show_tags_checkbox.toggled.connect(self.tag_size_combo.setEnabled)
        self.tag_size_combo.setEnabled(self.show_tags_checkbox.isChecked())

        tag_style_row = QHBoxLayout()
        tag_style_row.addWidget(QLabel("Tag chip style:"))
        self.tag_style_combo = QComboBox()
        for label, value in self.TAG_STYLE_OPTIONS:
            self.tag_style_combo.addItem(label, value)
        self.tag_style_combo.setToolTip("Choose muted, vibrant, or monochrome tag palettes.")
        current_tag_style = str(self._settings.get("tag_chip_style", "vibrant"))
        tag_style_index = self.tag_style_combo.findData(current_tag_style)
        self.tag_style_combo.setCurrentIndex(max(0, tag_style_index))
        tag_style_row.addWidget(self.tag_style_combo)
        tag_style_row.addStretch()
        appearance_layout.addLayout(tag_style_row)
        self.show_tags_checkbox.toggled.connect(self.tag_style_combo.setEnabled)
        self.tag_style_combo.setEnabled(self.show_tags_checkbox.isChecked())

        gradient_color_row = QHBoxLayout()
        gradient_color_row.addWidget(QLabel("Logged-in highlight color:"))
        self.logged_in_gradient_color_combo = QComboBox()
        for label, value in self.LOGGED_IN_COLOR_OPTIONS:
            self.logged_in_gradient_color_combo.addItem(label, value)
        self.logged_in_gradient_color_combo.setToolTip(
            "Choose the color used for the logged-in row highlight."
        )
        parent_dark_mode = bool(getattr(self.parent(), "_dark_mode", True))
        default_gradient_color = _default_logged_in_highlight(parent_dark_mode)
        current_gradient_color = str(
            self._settings.get("logged_in_gradient_color", default_gradient_color) or default_gradient_color
        )
        gradient_color_index = self.logged_in_gradient_color_combo.findData(current_gradient_color)
        self.logged_in_gradient_color_combo.setCurrentIndex(max(0, gradient_color_index))
        gradient_color_row.addWidget(self.logged_in_gradient_color_combo)
        gradient_color_row.addStretch()
        appearance_layout.addLayout(gradient_color_row)

        hover_color_row = QHBoxLayout()
        hover_color_row.addWidget(QLabel("Hover/selection highlight color:"))
        self.hover_highlight_color_combo = QComboBox()
        for label, value in self.HOVER_HIGHLIGHT_COLOR_OPTIONS:
            self.hover_highlight_color_combo.addItem(label, value)
        self.hover_highlight_color_combo.setToolTip(
            "Global Theme follows light/dark mode automatically. Pick a color here to override it."
        )
        default_hover_color = HOVER_HIGHLIGHT_THEME_AUTO
        current_hover_color = str(
            self._settings.get("hover_highlight_color", default_hover_color) or default_hover_color
        )
        hover_color_index = self.hover_highlight_color_combo.findData(current_hover_color)
        if hover_color_index < 0:
            hover_color_index = self.hover_highlight_color_combo.findData(HOVER_HIGHLIGHT_THEME_AUTO)
        self.hover_highlight_color_combo.setCurrentIndex(max(0, hover_color_index))
        hover_color_row.addWidget(self.hover_highlight_color_combo)
        hover_color_row.addStretch()
        appearance_layout.addLayout(hover_color_row)

        self.champion_splash_enabled_checkbox = QCheckBox("Show champion splash background on account list")
        self.champion_splash_enabled_checkbox.setChecked(bool(self._settings.get("champion_splash_enabled", False)))
        self.champion_splash_enabled_checkbox.setToolTip(
            "Show selected champion base splash art behind the account entries."
        )
        appearance_layout.addWidget(self.champion_splash_enabled_checkbox)

        splash_champion_row = QHBoxLayout()
        splash_champion_row.addWidget(QLabel("Splash champion:"))
        self.champion_splash_combo = QComboBox()
        self.champion_splash_combo.setEditable(True)
        self.champion_splash_combo.setInsertPolicy(QComboBox.NoInsert)
        self.champion_splash_combo.addItem("Global Theme (None)", SPLASH_THEME_AUTO)
        for name, champ_id in self.CHAMPION_SPLASH_OPTIONS:
            self.champion_splash_combo.addItem(name, champ_id)
        self.champion_splash_combo.setToolTip(
            "Type champion name to quickly find base splash art."
        )
        completer = QCompleter(self.champion_splash_combo.model(), self)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setCompletionMode(QCompleter.PopupCompletion)
        try:
            completer.setFilterMode(Qt.MatchContains)
        except Exception:
            pass
        self.champion_splash_combo.setCompleter(completer)
        self._champion_splash_line_edit = self.champion_splash_combo.lineEdit()
        if self._champion_splash_line_edit:
            self._champion_splash_line_edit.setPlaceholderText("Type champion name")
            self._champion_splash_line_edit.setClearButtonEnabled(True)
            self._champion_splash_line_edit.installEventFilter(self)

        if parent_dark_mode:
            edit_bg = "#171a2a"
            edit_fg = "#dbe4ff"
            edit_border = "#3f4b71"
            placeholder = "#8ea1cf"
            popup_bg = "#151b2d"
            popup_fg = "#e9efff"
            popup_border = "#3f4b71"
            popup_sel_bg = "#2d3d62"
            popup_sel_fg = "#ffffff"
        else:
            edit_bg = "#fafafa"
            edit_fg = "#2e2d2a"
            edit_border = "#d0d0d6"
            placeholder = "#8a90a3"
            popup_bg = "#ffffff"
            popup_fg = "#273247"
            popup_border = "#cfd6e6"
            popup_sel_bg = "#e2e8f5"
            popup_sel_fg = "#13233f"

        self.champion_splash_combo.setStyleSheet(
            "QComboBox { padding-right: 24px; }"
            f"QComboBox QLineEdit {{ background-color: {edit_bg}; color: {edit_fg}; border: 1px solid {edit_border}; border-radius: 4px; padding: 3px 6px; }}"
            f"QComboBox QLineEdit:placeholder {{ color: {placeholder}; }}"
            f"QComboBox QAbstractItemView {{ background: {popup_bg}; color: {popup_fg}; border: 1px solid {popup_border}; border-radius: 8px; selection-background-color: {popup_sel_bg}; selection-color: {popup_sel_fg}; padding: 4px; }}"
        )
        completer.popup().setStyleSheet(
            f"QListView {{ background: {popup_bg}; color: {popup_fg}; border: 1px solid {popup_border}; border-radius: 8px; padding: 1px; outline: none; }}"
            f"QListView::item {{ padding: 4px 8px; min-height: 20px; border-radius: 6px; }}"
            f"QListView::item:selected {{ background: {popup_sel_bg}; color: {popup_sel_fg}; }}"
            f"QListView::item:hover {{ background: {popup_sel_bg}; color: {popup_sel_fg}; }}"
        )
        current_splash_champion = str(self._settings.get("champion_splash_champion", SPLASH_THEME_AUTO) or SPLASH_THEME_AUTO)
        splash_champion_index = self.champion_splash_combo.findData(current_splash_champion)
        if splash_champion_index < 0:
            splash_champion_index = self.champion_splash_combo.findData(SPLASH_THEME_AUTO)
        self.champion_splash_combo.setCurrentIndex(max(0, splash_champion_index))
        splash_champion_row.addWidget(self.champion_splash_combo)
        splash_champion_row.addStretch()
        appearance_layout.addLayout(splash_champion_row)

        splash_opacity_row = QHBoxLayout()
        splash_opacity_row.addWidget(QLabel("Splash opacity:"))
        self.champion_splash_opacity_combo = QComboBox()
        for label, value in self.CHAMPION_SPLASH_OPACITY_OPTIONS:
            self.champion_splash_opacity_combo.addItem(label, value)
        current_splash_opacity = int(self._settings.get("champion_splash_opacity", 70))
        splash_opacity_index = self.champion_splash_opacity_combo.findData(current_splash_opacity)
        if splash_opacity_index < 0:
            splash_opacity_index = self.champion_splash_opacity_combo.findData(70)
        self.champion_splash_opacity_combo.setCurrentIndex(max(0, splash_opacity_index))
        splash_opacity_row.addWidget(self.champion_splash_opacity_combo)
        splash_opacity_row.addStretch()
        appearance_layout.addLayout(splash_opacity_row)

        self.champion_splash_enabled_checkbox.toggled.connect(self.champion_splash_combo.setEnabled)
        self.champion_splash_enabled_checkbox.toggled.connect(self.champion_splash_opacity_combo.setEnabled)
        splash_enabled = self.champion_splash_enabled_checkbox.isChecked()
        self.champion_splash_combo.setEnabled(splash_enabled)
        self.champion_splash_opacity_combo.setEnabled(splash_enabled)

        gradient_intensity_row = QHBoxLayout()
        gradient_intensity_row.addWidget(QLabel("Logged-in gradient intensity:"))
        self.logged_in_gradient_intensity_combo = QComboBox()
        for label, value in self.LOGGED_IN_INTENSITY_OPTIONS:
            self.logged_in_gradient_intensity_combo.addItem(label, value)
        self.logged_in_gradient_intensity_combo.setToolTip(
            "Controls how subtle or strong the logged-in row gradient appears."
        )
        current_intensity = int(self._settings.get("logged_in_gradient_intensity", 20))
        intensity_index = self.logged_in_gradient_intensity_combo.findData(current_intensity)
        if intensity_index < 0:
            nearest = min(
                [value for _, value in self.LOGGED_IN_INTENSITY_OPTIONS],
                key=lambda option: abs(option - current_intensity),
            )
            intensity_index = self.logged_in_gradient_intensity_combo.findData(nearest)
        self.logged_in_gradient_intensity_combo.setCurrentIndex(max(0, intensity_index))
        gradient_intensity_row.addWidget(self.logged_in_gradient_intensity_combo)
        gradient_intensity_row.addStretch()
        appearance_layout.addLayout(gradient_intensity_row)

        border_width_row = QHBoxLayout()
        border_width_row.addWidget(QLabel("Logged-in border thickness:"))
        self.logged_in_border_width_combo = QComboBox()
        for label, value in self.LOGGED_IN_BORDER_WIDTH_OPTIONS:
            self.logged_in_border_width_combo.addItem(label, value)
        self.logged_in_border_width_combo.setToolTip(
            "Controls the thickness of the logged-in accent border independently from fill intensity."
        )
        current_border_width = int(self._settings.get("logged_in_border_width", 2))
        border_width_index = self.logged_in_border_width_combo.findData(current_border_width)
        self.logged_in_border_width_combo.setCurrentIndex(max(0, border_width_index))
        border_width_row.addWidget(self.logged_in_border_width_combo)
        border_width_row.addStretch()
        appearance_layout.addLayout(border_width_row)

        border_opacity_row = QHBoxLayout()
        border_opacity_row.addWidget(QLabel("Logged-in border opacity:"))
        self.logged_in_border_opacity_combo = QComboBox()
        for label, value in self.LOGGED_IN_BORDER_OPACITY_OPTIONS:
            self.logged_in_border_opacity_combo.addItem(label, value)
        self.logged_in_border_opacity_combo.setToolTip(
            "Controls border opacity independently from the row fill intensity."
        )
        current_border_opacity = int(self._settings.get("logged_in_border_opacity", 60))
        border_opacity_index = self.logged_in_border_opacity_combo.findData(current_border_opacity)
        self.logged_in_border_opacity_combo.setCurrentIndex(max(0, border_opacity_index))
        border_opacity_row.addWidget(self.logged_in_border_opacity_combo)
        border_opacity_row.addStretch()
        appearance_layout.addLayout(border_opacity_row)

        density_row = QHBoxLayout()
        density_row.addWidget(QLabel("Row density:"))
        self.row_density_combo = QComboBox()
        for label, value in self.ROW_DENSITY_OPTIONS:
            self.row_density_combo.addItem(label, value)
        self.row_density_combo.setToolTip("Adjust account row spacing and height.")
        current_density = str(self._settings.get("row_density", "compact"))
        density_index = self.row_density_combo.findData(current_density)
        self.row_density_combo.setCurrentIndex(max(0, density_index))
        density_row.addWidget(self.row_density_combo)
        density_row.addStretch()
        appearance_layout.addLayout(density_row)

        rank_icon_row = QHBoxLayout()
        rank_icon_row.addWidget(QLabel("Rank icon size:"))
        self.rank_icon_size_combo = QComboBox()
        for label, value in self.RANK_ICON_SIZE_OPTIONS:
            self.rank_icon_size_combo.addItem(label, value)
        self.rank_icon_size_combo.setToolTip("Control medal icon size independently from text zoom.")
        current_rank_icon_size = int(self._settings.get("rank_icon_size", 34))
        rank_icon_index = self.rank_icon_size_combo.findData(current_rank_icon_size)
        self.rank_icon_size_combo.setCurrentIndex(max(0, rank_icon_index))
        rank_icon_row.addWidget(self.rank_icon_size_combo)
        rank_icon_row.addStretch()
        appearance_layout.addLayout(rank_icon_row)

        rank_text_row = QHBoxLayout()
        rank_text_row.addWidget(QLabel("Rank text brightness:"))
        self.rank_text_brightness_combo = QComboBox()
        for label, value in self.RANK_TEXT_BRIGHTNESS_OPTIONS:
            self.rank_text_brightness_combo.addItem(label, value)
        self.rank_text_brightness_combo.setToolTip("Control rank text brightness independently from text zoom.")
        current_rank_text_brightness = int(self._settings.get("rank_text_brightness", 100))
        rank_text_index = self.rank_text_brightness_combo.findData(current_rank_text_brightness)
        self.rank_text_brightness_combo.setCurrentIndex(max(0, rank_text_index))
        rank_text_row.addWidget(self.rank_text_brightness_combo)
        rank_text_row.addStretch()
        appearance_layout.addLayout(rank_text_row)

        self.show_ranks_checkbox.toggled.connect(self.rank_icon_size_combo.setEnabled)
        self.show_ranks_checkbox.toggled.connect(self.rank_text_brightness_combo.setEnabled)
        self.rank_icon_size_combo.setEnabled(self.show_ranks_checkbox.isChecked())
        self.rank_text_brightness_combo.setEnabled(self.show_ranks_checkbox.isChecked())

        backups_label = QLabel("Backups")
        backups_label.setStyleSheet("font-weight: 600;")
        advanced_layout.addWidget(backups_label)

        self.auto_backup_checkbox = QCheckBox("Automatic versioned backups")
        self.auto_backup_checkbox.setChecked(bool(self._settings.get("auto_backup_enabled", True)))
        self.auto_backup_checkbox.setToolTip(
            "Create an encrypted backup each time account data is saved."
        )
        advanced_layout.addWidget(self.auto_backup_checkbox)

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
        advanced_layout.addLayout(backup_keep_row)
        self.auto_backup_checkbox.toggled.connect(self.auto_backup_keep_combo.setEnabled)
        self.auto_backup_keep_combo.setEnabled(self.auto_backup_checkbox.isChecked())

        backup_row = QHBoxLayout()
        backup_btn = QPushButton("Backup / Restore...")
        backup_btn.setToolTip("Export or import an encrypted account backup")
        backup_btn.setAutoDefault(False)
        backup_btn.setDefault(False)
        backup_btn.clicked.connect(lambda: mw.open_backup_dialog() if mw else None)
        backup_row.addWidget(backup_btn)
        backup_row.addStretch()
        advanced_layout.addLayout(backup_row)

        about_row = QHBoxLayout()
        about_row.addWidget(QLabel("Application info:"))
        about_btn = QPushButton("About")
        about_btn.setAutoDefault(False)
        about_btn.setDefault(False)
        about_btn.clicked.connect(lambda: mw.show_about() if mw else None)
        about_row.addWidget(about_btn)
        about_row.addStretch()
        advanced_layout.addLayout(about_row)

        general_layout.addStretch()
        appearance_layout.addStretch()
        advanced_layout.addStretch()
        tabs.addTab(general_tab, "General")
        tabs.addTab(appearance_tab, "Appearance")
        tabs.addTab(advanced_tab, "Advanced")
        layout.addWidget(tabs)

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
        apply_btn = QPushButton("Apply")
        apply_btn.setFixedWidth(100)
        apply_btn.setAutoDefault(False)
        apply_btn.setDefault(False)
        apply_btn.clicked.connect(self.apply_settings)
        button_row.addWidget(apply_btn)
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
        window_size_mode = "custom" if self.window_size_combo.currentData() == self.CUSTOM_SIZE_VALUE else "static"
        window_size = self.current_window_size if window_size_mode == "custom" else self.window_size_combo.currentText()
        typed = self.champion_splash_combo.currentText().strip().casefold()
        champion_splash_value = self.champion_splash_combo.currentData()
        if typed:
            for name, champ_id in self.CHAMPION_SPLASH_OPTIONS:
                if typed == name.casefold():
                    champion_splash_value = champ_id
                    break
        if champion_splash_value is None:
            champion_splash_value = SPLASH_THEME_AUTO
        return {
            "start_on_windows_startup": self.startup_checkbox.isChecked(),
            "start_minimized_to_tray": self.start_minimized_checkbox.isChecked(),
            "close_behavior": str(self.close_behavior_combo.currentData()),
            "auto_lock_minutes": int(self.auto_lock_combo.currentData()),
            "remember_password_24h": self.remember_password_24h_checkbox.isChecked(),
            "clipboard_auto_clear_seconds": int(self.clipboard_clear_combo.currentData()),
            "confirm_before_launch": self.confirm_launch_checkbox.isChecked(),
            "confirm_before_delete": self.confirm_delete_checkbox.isChecked(),
            "account_sort_mode": str(self.account_sort_mode_combo.currentData()),
            "rank_refresh_mode": str(self.rank_refresh_combo.currentData()),
            "auto_check_updates": self.auto_check_updates_checkbox.isChecked(),
            "diagnostics_log_level": str(self.log_level_combo.currentData()),
            "window_size": window_size,
            "window_size_mode": window_size_mode,
            "text_zoom_percent": int(self.text_zoom_combo.currentData()),
            "show_ranks": self.show_ranks_checkbox.isChecked(),
            "show_rank_images": self.show_images_checkbox.isChecked(),
            "show_tags": self.show_tags_checkbox.isChecked(),
            "auto_open_ingame_page": self.auto_open_ingame_checkbox.isChecked(),
            "tag_size": str(self.tag_size_combo.currentData()),
            "tag_chip_style": str(self.tag_style_combo.currentData()),
            "logged_in_gradient_color": str(self.logged_in_gradient_color_combo.currentData()),
            "hover_highlight_color": str(self.hover_highlight_color_combo.currentData()),
            "champion_splash_enabled": self.champion_splash_enabled_checkbox.isChecked(),
            "champion_splash_champion": str(champion_splash_value),
            "champion_splash_opacity": int(self.champion_splash_opacity_combo.currentData()),
            "logged_in_gradient_intensity": int(self.logged_in_gradient_intensity_combo.currentData()),
            "logged_in_border_width": int(self.logged_in_border_width_combo.currentData()),
            "logged_in_border_opacity": int(self.logged_in_border_opacity_combo.currentData()),
            "row_density": str(self.row_density_combo.currentData()),
            "rank_icon_size": int(self.rank_icon_size_combo.currentData()),
            "rank_text_brightness": int(self.rank_text_brightness_combo.currentData()),
            "auto_backup_enabled": self.auto_backup_checkbox.isChecked(),
            "auto_backup_keep_count": int(self.auto_backup_keep_combo.currentData()),
        }

    def apply_settings(self):
        """Apply settings without closing the dialog."""
        if self._apply_callback:
            self._apply_callback(self.get_values())

    def eventFilter(self, obj, event):
        if getattr(self, "_champion_splash_line_edit", None) is obj and event.type() == QEvent.FocusIn:
            self._champion_splash_line_edit.clear()
        return super().eventFilter(obj, event)


class AccountListItem(QFrame):
    """Custom widget for displaying account in list"""

    _TAG_COLOR_SLOT_BY_TEXT: dict[str, int] = {}

    _TAG_STYLE_PALETTES = {
        "vibrant": {
            "dark": [
                ("#0d2f40", "#1a556d", "#93dcff", "#27b5f7"),
                ("#33250c", "#5f4313", "#ffd38a", "#f5a623"),
                ("#133321", "#24613d", "#9de8bd", "#32c46d"),
                ("#35152b", "#662a57", "#f4b5e5", "#de4db5"),
                ("#3a171d", "#6f2d38", "#ffb8c2", "#ff5c7a"),
                ("#202d46", "#374c72", "#b9d2ff", "#5f9cff"),
            ],
            "light": [
                ("#e8f7ff", "#badff2", "#0f4c6a", "#1f9ed6"),
                ("#fff5e6", "#f0d3a3", "#6d4a13", "#d18908"),
                ("#ebfaef", "#bde7c8", "#1d6339", "#2fa35d"),
                ("#fff0fb", "#e6c0da", "#7d2f6d", "#c24ea1"),
                ("#fff0f2", "#efc1ca", "#7f3040", "#d75b72"),
                ("#edf2ff", "#c3d0ef", "#27467a", "#4d78db"),
            ],
        },
        "muted": {
            "dark": [
                ("#1a2530", "#344659", "#9db0c3", "#5f7895"),
                ("#2b2620", "#4a4034", "#cdb79a", "#9a7f61"),
                ("#1d2a24", "#385044", "#9fc1af", "#5e8a74"),
                ("#2d2430", "#4c3c53", "#c5b2c8", "#8d6f95"),
                ("#2f2224", "#53393e", "#d0b0b4", "#9a6970"),
                ("#222737", "#3f4a6a", "#b5bfdc", "#6f83b9"),
            ],
            "light": [
                ("#edf2f6", "#c4d1db", "#405161", "#6b859f"),
                ("#f5f1eb", "#d8ccbe", "#5e5040", "#8f775c"),
                ("#edf4ef", "#c8d9ce", "#405a4c", "#6a8c79"),
                ("#f3eef5", "#d5c7d9", "#5b4f60", "#876d8f"),
                ("#f6eff0", "#dcc9cc", "#664b51", "#9a6e76"),
                ("#eef1f8", "#cad1e3", "#455173", "#7083b3"),
            ],
        },
        "monochrome": {
            "dark": [
                ("#232633", "#3b4156", "#d2d8ea", "#909ab6"),
                ("#242835", "#3f465d", "#cfd6e9", "#8f99b7"),
                ("#222633", "#3a4257", "#d3d9ea", "#8d97b6"),
                ("#242734", "#3d4559", "#d0d7e8", "#8d98b4"),
                ("#232632", "#3c4358", "#d1d8e9", "#8c97b5"),
                ("#242734", "#3d445a", "#d2d8ea", "#8d99b5"),
            ],
            "light": [
                ("#f3f5fa", "#ccd3e2", "#48526a", "#7d88a8"),
                ("#f3f5fa", "#cdd3e2", "#475169", "#7e89a8"),
                ("#f3f6fb", "#cbd3e2", "#48526a", "#7c88a7"),
                ("#f4f6fb", "#ccd4e2", "#475169", "#7d88a6"),
                ("#f3f6fb", "#ccd4e3", "#48516a", "#7d89a7"),
                ("#f4f6fb", "#ccd4e3", "#48526b", "#7d89a8"),
            ],
        },
    }

    _TAG_MORE_STYLE = {
        "vibrant": {
            "dark": ("#2e3448", "#566080", "#cfd7f2", "#9fb2e8"),
            "light": ("#eef1f7", "#b7bfd3", "#44506d", "#93a4ce"),
        },
        "muted": {
            "dark": ("#2a2f3f", "#4f596f", "#c4ccdf", "#8594b8"),
            "light": ("#eff2f7", "#bec6d6", "#55627f", "#8ea0c7"),
        },
        "monochrome": {
            "dark": ("#2b2f3c", "#525a6f", "#c9cfdf", "#8b95b2"),
            "light": ("#f1f3f8", "#c2c9d8", "#596179", "#8b98b9"),
        },
    }
    
    def __init__(
        self,
        account: Account,
        parent=None,
        show_ranks: bool = True,
        show_rank_images: bool = True,
        show_tags: bool = True,
        tag_size: str = "small",
        logged_in_gradient_color: str = DEFAULT_LOGGED_IN_HIGHLIGHT_DARK,
        hover_highlight_color: str = DEFAULT_ROW_HOVER_HIGHLIGHT_DARK,
        logged_in_gradient_intensity: int = 20,
        logged_in_border_width: int = 2,
        logged_in_border_opacity: int = 60,
        row_density: str = "compact",
        rank_icon_size: int = 34,
        rank_text_brightness: int = 100,
        tag_chip_style: str = "vibrant",
    ):
        super().__init__(parent)
        self.account = account
        self._show_ranks = show_ranks
        self._show_rank_images = show_rank_images
        self._show_tags = show_tags
        self._tag_size = tag_size
        self._logged_in_gradient_color = logged_in_gradient_color or DEFAULT_LOGGED_IN_HIGHLIGHT_DARK
        self._hover_highlight_color = hover_highlight_color or DEFAULT_ROW_HOVER_HIGHLIGHT_DARK
        self._logged_in_gradient_intensity = max(5, min(100, int(logged_in_gradient_intensity)))
        self._logged_in_border_width = max(2, min(5, int(logged_in_border_width)))
        self._logged_in_border_opacity = max(60, min(120, int(logged_in_border_opacity)))
        self._row_density = row_density if row_density in {"compact", "comfortable", "spacious"} else "comfortable"
        self._rank_icon_size = max(24, min(48, int(rank_icon_size)))
        self._rank_text_brightness = max(70, min(140, int(rank_text_brightness)))
        self._tag_chip_style = tag_chip_style if tag_chip_style in self._TAG_STYLE_PALETTES else "vibrant"
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

    def _row_density_preset(self) -> dict:
        presets = {
            "compact": {
                "outer_margins": (6, 3, 6, 3),
                "outer_spacing": 6,
                "text_spacing": 1,
                "user_row_spacing": 4,
                "rank_spacing": 5,
                "logged_in_height": 18,
                "rank_min_width": 170,
            },
            "comfortable": {
                "outer_margins": (10, 5, 10, 5),
                "outer_spacing": 8,
                "text_spacing": 2,
                "user_row_spacing": 6,
                "rank_spacing": 6,
                "logged_in_height": 20,
                "rank_min_width": 190,
            },
            "spacious": {
                "outer_margins": (12, 7, 12, 7),
                "outer_spacing": 10,
                "text_spacing": 3,
                "user_row_spacing": 8,
                "rank_spacing": 8,
                "logged_in_height": 22,
                "rank_min_width": 205,
            },
        }
        return presets.get(self._row_density, presets["comfortable"])
    
    def init_ui(self):
        density = self._row_density_preset()
        outer = QHBoxLayout()
        outer.setContentsMargins(*density["outer_margins"])
        outer.setSpacing(density["outer_spacing"])
        self.setObjectName("accountListItem")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setMouseTracking(True)
        self._selected = False
        self._hovered = False
        self._logged_in = False
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
        text_layout.setSpacing(density["text_spacing"])

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

        self.pin_label = QLabel("★")
        self.pin_label.setAttribute(Qt.WA_TranslucentBackground, True)
        self.pin_label.setVisible(bool(getattr(self.account, "is_pinned", False)))
        self.pin_label.setStyleSheet("background: transparent; border: none;")
        name_row.addWidget(self.pin_label)

        self.name_label = QLabel(self.account.display_name)
        self.name_label.setFont(name_font)
        self.name_label.setAttribute(Qt.WA_TranslucentBackground, True)
        self.name_label.setStyleSheet("background: transparent; border: none;")
        name_row.addWidget(self.name_label)

        self.tag_line_label = QLabel(f"#{tag_line}")
        self.tag_line_label.setFont(tag_font)
        self.tag_line_label.setAttribute(Qt.WA_TranslucentBackground, True)
        self.tag_line_label.setStyleSheet("background: transparent; border: none; color: #9aa1b2;")
        name_row.addWidget(self.tag_line_label)

        name_row.addStretch()
        text_layout.addLayout(name_row)

        user_row = QHBoxLayout()
        user_row.setSpacing(density["user_row_spacing"])
        self.username_label = QLabel(f"@{self.account.username}")
        self.username_label.setStyleSheet("background: transparent; border: none; color: #666666;")
        self.username_label.setAttribute(Qt.WA_TranslucentBackground, True)
        user_row.addWidget(self.username_label)

        self.region_label = QLabel(f"{region}")
        self.region_label.setAttribute(Qt.WA_TranslucentBackground, True)
        self.region_label.setStyleSheet("background: transparent; border: none; color: #8b93a8; font-size: 10px;")
        user_row.addWidget(self.region_label)

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
        rank_layout.setSpacing(density["rank_spacing"])

        self.rank_icon_label = QLabel()
        self.rank_icon_label.setFixedSize(self._rank_icon_size, self._rank_icon_size)
        self.rank_icon_label.setScaledContents(False)
        self.rank_icon_label.setAttribute(Qt.WA_TranslucentBackground, True)
        self.rank_icon_label.setStyleSheet("background: transparent; border: none;")

        self.logged_in_label = QLabel("Logged in")
        self.logged_in_label.setAttribute(Qt.WA_TranslucentBackground, True)
        self.logged_in_label.setVisible(False)
        self.logged_in_label.setAlignment(Qt.AlignCenter)
        self.logged_in_label.setFixedHeight(density["logged_in_height"])
        self.logged_in_label.setMinimumWidth(78)
        rank_layout.addWidget(self.logged_in_label)
        rank_layout.addWidget(self.rank_icon_label)

        self.rank_label = QLabel("...")
        self.rank_label.setAlignment(Qt.AlignVCenter | Qt.AlignRight)
        self.rank_label.setAttribute(Qt.WA_TranslucentBackground, True)
        self.rank_label.setTextFormat(Qt.RichText)
        self.rank_label.setStyleSheet(
            "background: transparent; border: none; color: #8b93a8; font-size: 11px;"
        )
        self.rank_label.setMinimumWidth(density["rank_min_width"])
        rank_layout.addWidget(self.rank_label)

        self.rank_widget = rank_widget
        self.rank_widget.setVisible(self._show_ranks)
        outer.addWidget(rank_widget)

        self.setLayout(outer)
        self._refresh_text_styles()
        self._refresh_logged_in_badge_style()
        self._update_visual_state()

    def _refresh_text_styles(self):
        """Keep row text readable across theme + logged-in highlight states."""
        if self._dark_mode:
            username_color = "#d2dbf5" if self._logged_in else "#b5bfdc"
            region_color = "#c0cbea" if self._logged_in else "#9aa8cd"
            tag_color = "#c7d3f0"
            pin_color = "#f6c453"
            self.name_label.setStyleSheet("background: transparent; border: none; color: #e8edff;")
        else:
            username_color = "#6b7280"
            region_color = "#6b7280"
            tag_color = "#9aa1b2"
            pin_color = "#9a6f2a"
            self.name_label.setStyleSheet("background: transparent; border: none; color: #111827;")

        self.pin_label.setStyleSheet(
            f"background: transparent; border: none; color: {pin_color}; font-size: 11px;"
        )

        self.tag_line_label.setStyleSheet(
            f"background: transparent; border: none; color: {tag_color};"
        )
        self.username_label.setStyleSheet(
            f"background: transparent; border: none; color: {username_color};"
        )
        self.region_label.setStyleSheet(
            f"background: transparent; border: none; color: {region_color}; font-size: 10px;"
        )

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
        style = self._tag_chip_style if self._tag_chip_style in self._TAG_STYLE_PALETTES else "vibrant"
        palette = self._TAG_STYLE_PALETTES[style]["dark" if self._dark_mode else "light"]
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
        style = self._tag_chip_style if self._tag_chip_style in self._TAG_MORE_STYLE else "vibrant"
        bg, border, fg, accent = self._TAG_MORE_STYLE[style]["dark" if self._dark_mode else "light"]
        return (
            f"background-color: {bg};"
            f"border: 1px solid {border};"
            f"border-left: {size['left_border']}px solid {accent};"
            f"border-radius: {size['radius']}px;"
            f"color: {fg};"
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

    def _refresh_logged_in_badge_style(self):
        """Refresh the logged-in badge style for the active theme."""
        t = max(0.03, min(1.0, self._logged_in_gradient_intensity / 100.0))
        badge_bg_alpha = int(30 + (90 * t))
        badge_border_alpha = int(70 + (130 * t))
        badge_fg = "#eef5ff" if self._dark_mode else "#1e3a8a"
        if self._dark_mode:
            self.logged_in_label.setStyleSheet(
                f"background-color: {self._rgba(self._logged_in_gradient_color, badge_bg_alpha)};"
                f"border: 1px solid {self._rgba(self._logged_in_gradient_color, badge_border_alpha)};"
                "border-radius: 10px;"
                f"color: {badge_fg};"
                "font-size: 9.5px;"
                "font-weight: 700;"
                "padding: 0px 9px;"
            )
        else:
            self.logged_in_label.setStyleSheet(
                f"background-color: {self._rgba(self._logged_in_gradient_color, max(20, badge_bg_alpha - 20))};"
                f"border: 1px solid {self._rgba(self._logged_in_gradient_color, max(45, badge_border_alpha - 25))};"
                "border-radius: 10px;"
                f"color: {badge_fg};"
                "font-size: 9.5px;"
                "font-weight: 700;"
                "padding: 0px 9px;"
            )

    def _hex_to_rgb(self, color: str) -> tuple[int, int, int]:
        raw = (color or "#4f7cff").strip().lstrip('#')
        if len(raw) == 3:
            raw = ''.join(ch * 2 for ch in raw)
        if len(raw) != 6:
            return (79, 124, 255)
        try:
            return int(raw[0:2], 16), int(raw[2:4], 16), int(raw[4:6], 16)
        except ValueError:
            return (79, 124, 255)

    def _rgba(self, color: str, alpha: int) -> str:
        r, g, b = self._hex_to_rgb(color)
        a = max(0, min(255, int(alpha)))
        return f"rgba({r}, {g}, {b}, {a})"

    def _adjust_hex_brightness(self, color: str, percent: int) -> str:
        r, g, b = self._hex_to_rgb(color)
        factor = max(0.5, min(1.8, percent / 100.0))
        nr = max(0, min(255, int(r * factor)))
        ng = max(0, min(255, int(g * factor)))
        nb = max(0, min(255, int(b * factor)))
        return f"#{nr:02x}{ng:02x}{nb:02x}"

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
        color = self._adjust_hex_brightness(str(rank_data.get("color", "#585b70")), self._rank_text_brightness)
        if status == "ok":
            tier = _escape_html(f"{rank_data.get('tier', '')}{(' ' + rank_data.get('division', '')) if rank_data.get('division') else ''}")
            lp = _escape_html(f"{rank_data.get('lp', '')} LP")
            wins = _escape_html(f"{rank_data.get('wins', '')}W / {rank_data.get('losses', '')}L")
            win_rate = _escape_html(f"{rank_data.get('win_rate', '')}% WR")
            neutral_base = "#8b93a8" if self._dark_mode else "#4b5563"
            neutral_color = self._adjust_hex_brightness(neutral_base, self._rank_text_brightness)
            self.rank_label.setStyleSheet("background: transparent; border: none; font-size: 11px;")
            pixmap = _build_rank_pixmap(rank_data.get("medal_bytes", b""))
            if not pixmap.isNull():
                pixmap = pixmap.scaled(self._rank_icon_size, self._rank_icon_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
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
                f"background: transparent; border: none; color: {self._adjust_hex_brightness('#585b70', self._rank_text_brightness)}; font-size: 11px;"
            )
            self.rank_label.setText(str(rank_data.get("text") or "Unranked"))
        else:
            self.rank_icon_label.clear()
            self.rank_icon_label.setVisible(False)
            self.rank_label.setStyleSheet(
                f"background: transparent; border: none; color: {self._adjust_hex_brightness('#585b70', self._rank_text_brightness)}; font-size: 11px;"
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
        self._refresh_text_styles()
        self._refresh_logged_in_badge_style()
        self._update_visual_state()

    def set_hover_highlight_color(self, color: str):
        self._hover_highlight_color = str(color or self._hover_highlight_color)
        self._update_visual_state()

    def set_logged_in(self, logged_in: bool):
        self._logged_in = logged_in
        self.logged_in_label.setVisible(logged_in)
        self._refresh_text_styles()
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
            t = max(0.03, min(1.0, self._logged_in_gradient_intensity / 100.0))
            left_active = self._rgba(self._logged_in_gradient_color, int(26 + 74 * t))
            mid_active = self._rgba(self._logged_in_gradient_color, int(14 + 50 * t))
            left_idle = self._rgba(self._logged_in_gradient_color, int(18 + 56 * t))
            mid_idle = self._rgba(self._logged_in_gradient_color, int(10 + 40 * t))
            border_scale = self._logged_in_border_opacity / 100.0
            border_active = self._rgba(self._logged_in_gradient_color, int((90 + 90 * t) * border_scale))
            border_idle = self._rgba(self._logged_in_gradient_color, int((70 + 70 * t) * border_scale))
            border_width = max(1, self._logged_in_border_width - 2)
            left_border_width = self._logged_in_border_width

            if self._logged_in and active:
                self.setStyleSheet(
                    "#accountListItem {"
                    "background: qlineargradient(x1:0, y1:0, x2:1, y2:0,"
                    f"stop:0 {left_active},"
                    f"stop:0.18 {mid_active},"
                    "stop:1 rgba(37, 41, 61, 170));"
                    f"border: {border_width}px solid {border_active};"
                    f"border-left: {left_border_width}px solid {border_active};"
                    "border-radius: 10px;"
                    "}"
                )
                self._shadow.setBlurRadius(18)
                self._shadow.setColor(QColor(30, 60, 110, 110))
            elif self._logged_in:
                self.setStyleSheet(
                    "#accountListItem {"
                    "background: qlineargradient(x1:0, y1:0, x2:1, y2:0,"
                    f"stop:0 {left_idle},"
                    f"stop:0.16 {mid_idle},"
                    "stop:1 rgba(25, 30, 47, 95));"
                    f"border: {border_width}px solid {border_idle};"
                    f"border-left: {left_border_width}px solid {border_idle};"
                    "border-radius: 10px;"
                    "}"
                )
                self._shadow.setBlurRadius(14)
                self._shadow.setColor(QColor(30, 60, 110, 90))
            elif active:
                hover_bg = self._rgba(self._hover_highlight_color, 180)
                hover_border = self._rgba(self._hover_highlight_color, 150)
                self.setStyleSheet(
                    "#accountListItem {"
                    f"background-color: {hover_bg};"
                    f"border: 1px solid {hover_border};"
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

        t = max(0.03, min(1.0, self._logged_in_gradient_intensity / 100.0))
        left_active = self._rgba(self._logged_in_gradient_color, int(36 + 72 * t))
        mid_active = self._rgba(self._logged_in_gradient_color, int(24 + 56 * t))
        left_idle = self._rgba(self._logged_in_gradient_color, int(28 + 58 * t))
        mid_idle = self._rgba(self._logged_in_gradient_color, int(16 + 44 * t))
        border_scale = self._logged_in_border_opacity / 100.0
        border_active = self._rgba(self._logged_in_gradient_color, int((96 + 90 * t) * border_scale))
        border_idle = self._rgba(self._logged_in_gradient_color, int((78 + 74 * t) * border_scale))
        border_width = max(1, self._logged_in_border_width - 2)
        left_border_width = self._logged_in_border_width

        if self._logged_in and active:
            self.setStyleSheet(
                "#accountListItem {"
                "background: qlineargradient(x1:0, y1:0, x2:1, y2:0,"
                f"stop:0 {left_active},"
                f"stop:0.30 {mid_active},"
                "stop:1 rgba(236, 231, 223, 95));"
                f"border: {border_width}px solid {border_active};"
                f"border-left: {left_border_width}px solid {border_active};"
                "border-radius: 10px;"
                "}"
            )
            self._shadow.setBlurRadius(10)
            self._shadow.setColor(QColor(15, 23, 42, 30))
        elif self._logged_in:
            self.setStyleSheet(
                "#accountListItem {"
                "background: qlineargradient(x1:0, y1:0, x2:1, y2:0,"
                f"stop:0 {left_idle},"
                f"stop:0.30 {mid_idle},"
                "stop:1 rgba(223, 216, 205, 78));"
                f"border: {border_width}px solid {border_idle};"
                f"border-left: {left_border_width}px solid {border_idle};"
                "border-radius: 10px;"
                "}"
            )
            self._shadow.setBlurRadius(8)
            self._shadow.setColor(QColor(15, 23, 42, 20))
        elif active:
            hover_bg = self._rgba(self._hover_highlight_color, 155)
            hover_border = self._rgba(self._hover_highlight_color, 185)
            self.setStyleSheet(
                "#accountListItem {"
                f"background-color: {hover_bg};"
                f"border: 1px solid {hover_border};"
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
        self.ingame_diag_dialog: Optional[InGameDiagnosticsDialog] = None
        self.launch_progress: Optional[LaunchProgressDialog] = None
        self.current_launch_username: Optional[str] = None
        self._last_launched_username: str = str(self._settings.get('last_launched_username', '') or '')
        self._dark_mode: bool = self._settings.get('dark_mode', True)
        self._start_minimized_to_tray: bool = bool(self._settings.get('start_minimized_to_tray', False))
        self._close_behavior: str = str(self._settings.get('close_behavior', 'tray'))
        self._auto_lock_minutes: int = int(self._settings.get('auto_lock_minutes', 0))
        self._remember_password_24h: bool = bool(self._settings.get('remember_password_24h', True))
        self._clipboard_auto_clear_seconds: int = int(self._settings.get('clipboard_auto_clear_seconds', 0))
        self._confirm_before_launch: bool = bool(self._settings.get('confirm_before_launch', True))
        self._confirm_before_delete: bool = bool(self._settings.get('confirm_before_delete', True))
        self._account_sort_mode: str = str(self._settings.get('account_sort_mode', 'manual'))
        self._rank_refresh_mode: str = str(self._settings.get('rank_refresh_mode', 'manual'))
        self._auto_check_updates: bool = bool(self._settings.get('auto_check_updates', True))
        self._diagnostics_log_level: str = str(self._settings.get('diagnostics_log_level', 'INFO')).upper()
        self._show_ranks: bool = self._settings.get('show_ranks', True)
        self._show_rank_images: bool = self._settings.get('show_rank_images', True)
        self._show_tags: bool = self._settings.get('show_tags', True)
        self._auto_open_ingame_page: bool = bool(self._settings.get('auto_open_ingame_page', True))
        self._tag_size: str = str(self._settings.get('tag_size', 'medium'))
        self._tag_chip_style: str = str(self._settings.get('tag_chip_style', 'vibrant'))
        self._text_zoom_percent: int = int(self._settings.get('text_zoom_percent', 110))
        default_gradient_color = _default_logged_in_highlight(self._dark_mode)
        self._logged_in_gradient_color: str = str(
            self._settings.get('logged_in_gradient_color', default_gradient_color) or default_gradient_color
        )
        self._hover_highlight_color_setting: str = str(
            self._settings.get('hover_highlight_color', HOVER_HIGHLIGHT_THEME_AUTO) or HOVER_HIGHLIGHT_THEME_AUTO
        )
        self._hover_highlight_color: str = _resolve_row_hover_highlight(
            self._hover_highlight_color_setting,
            self._dark_mode,
        )
        self._champion_splash_enabled: bool = bool(self._settings.get('champion_splash_enabled', False))
        self._champion_splash_champion: str = str(
            self._settings.get('champion_splash_champion', SPLASH_THEME_AUTO) or SPLASH_THEME_AUTO
        )
        self._champion_splash_opacity: int = int(self._settings.get('champion_splash_opacity', 70))
        self._champion_splash_edge_fade: int = LOCKED_CHAMPION_SPLASH_EDGE_FADE
        self._champion_splash_inner_fade: int = LOCKED_CHAMPION_SPLASH_INNER_FADE
        self._champion_splash_pixmap_cache: dict[str, QPixmap] = {}
        self._logged_in_gradient_intensity: int = int(self._settings.get('logged_in_gradient_intensity', 20))
        self._logged_in_border_width: int = int(self._settings.get('logged_in_border_width', 2))
        self._logged_in_border_opacity: int = int(self._settings.get('logged_in_border_opacity', 60))
        self._row_density: str = str(self._settings.get('row_density', 'compact'))
        self._rank_icon_size: int = int(self._settings.get('rank_icon_size', 34))
        self._rank_text_brightness: int = int(self._settings.get('rank_text_brightness', 100))
        self._window_size: str = self._settings.get('window_size', '800x600')
        self._window_size_mode: str = str(
            self._settings.get(
                'window_size_mode',
                'custom' if self._window_size not in SettingsDialog.COMMON_RESOLUTIONS else 'static',
            )
        ).strip().lower()
        if self._window_size_mode not in {'static', 'custom'}:
            self._window_size_mode = 'custom' if self._window_size not in SettingsDialog.COMMON_RESOLUTIONS else 'static'
        self._search_query: str = ""
        self._tag_filter_value: str = "__all__"
        self._rank_threads: list = []  # keep references so threads aren't GC'd
        self._logged_in_username: Optional[str] = None
        self._session_miss_count: int = 0
        self._manual_logout_grace_misses: int = 2
        self._window_resize_save_timer = QTimer(self)
        self._window_resize_save_timer.setSingleShot(True)
        self._window_resize_save_timer.setInterval(250)
        self._window_resize_save_timer.timeout.connect(self._persist_window_size)
        self._session_sync_timer = QTimer(self)
        self._session_sync_timer.setInterval(5000)
        self._session_sync_timer.timeout.connect(self._sync_logged_in_session_state)
        self._rank_refresh_timer = QTimer(self)
        self._rank_refresh_timer.timeout.connect(self._refresh_visible_ranks)
        self._clipboard_clear_timer = QTimer(self)
        self._clipboard_clear_timer.setSingleShot(True)
        self._clipboard_clear_timer.timeout.connect(self._clear_clipboard_if_needed)
        self._clipboard_last_text: str = ""
        self._auto_lock_timer = QTimer(self)
        self._auto_lock_timer.setSingleShot(True)
        self._auto_lock_timer.timeout.connect(self._handle_auto_lock_timeout)
        self._unlock_prompt_active = False
        self._quitting_to_exit = False
        self._tray_icon: Optional[QSystemTrayIcon] = None
        self._tray_menu: Optional[QMenu] = None
        self._tray_launch_last_action: Optional[QAction] = None
        self._tray_lock_action: Optional[QAction] = None
        self._tray_settings_action: Optional[QAction] = None
        self._tray_watcher_diag_action: Optional[QAction] = None
        self._tray_watcher_status_action: Optional[QAction] = None
        self._ingame_watch_status: dict = {
            "watcher_active": False,
            "status": "idle",
            "summary": "Watcher idle",
            "timestamp": 0,
            "status_code": None,
            "response_bytes": 0,
            "error": "",
        }
        self._suppress_window_size_persistence = False
        self.init_ui()
        app = QApplication.instance()
        if app:
            app.installEventFilter(self)
        self._configure_diagnostics_logging()
        self._create_tray_icon()
        self._apply_theme()
        self._session_sync_timer.start()
        self._update_rank_refresh_timer()
        self._reset_auto_lock_timer()
        self.check_master_password()
        if self._auto_check_updates:
            QTimer.singleShot(4000, self._check_for_updates)
        if self._start_minimized_to_tray and self._tray_icon and self._tray_icon.isVisible():
            QTimer.singleShot(0, self.hide)
    
    def init_ui(self):
        self.setWindowTitle("League of Legends Account Manager")
        self.setMinimumSize(640, 480)
        self._apply_window_size(self._window_size)

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
        self.account_list_background = AccountListBackgroundFrame()
        self.account_list_background.setObjectName("accountListContainer")
        account_list_layout = QVBoxLayout(self.account_list_background)
        account_list_layout.setContentsMargins(0, 0, 0, 0)
        account_list_layout.setSpacing(0)
        self.account_list = QListWidget()
        self.account_list.setObjectName("accountListWidget")
        self.account_list.setSpacing(0)
        self.account_list.setViewportMargins(0, 0, 0, 0)
        self.account_list.setStyleSheet(
            "QListWidget#accountListWidget { background: transparent; border: none; }"
            "QListWidget#accountListWidget::item { background: transparent; border: none; }"
            "QListWidget#accountListWidget::item:selected { background: transparent; border: none; }"
            "QListWidget#accountListWidget::item:hover { background: transparent; border: none; }"
        )
        self.account_list.setAttribute(Qt.WA_TranslucentBackground, True)
        self.account_list.viewport().setAutoFillBackground(False)
        self.account_list.itemClicked.connect(self.on_account_selected)
        self.account_list.itemDoubleClicked.connect(lambda _: self.launch_account())
        self.account_list.itemSelectionChanged.connect(self.update_account_item_states)
        self.account_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.account_list.customContextMenuRequested.connect(self.show_account_context_menu)
        account_list_layout.addWidget(self.account_list)
        layout.addWidget(self.account_list_background)
        
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

        self._apply_account_list_background()
        
        central_widget.setLayout(layout)

    @staticmethod
    def _champion_splash_url(champion_id: str) -> str:
        return f"https://ddragon.leagueoflegends.com/cdn/img/champion/splash/{champion_id}_0.jpg"

    def _load_champion_splash_pixmap(self, champion_id: str) -> Optional[QPixmap]:
        champ = str(champion_id or "").strip()
        if not champ or champ == SPLASH_THEME_AUTO:
            return None
        cached = self._champion_splash_pixmap_cache.get(champ)
        if cached is not None:
            return cached
        try:
            req = Request(self._champion_splash_url(champ), headers={"User-Agent": "lol-account-manager"})
            with urlopen(req, timeout=6) as resp:
                raw = resp.read()
            pix = QPixmap()
            if pix.loadFromData(raw):
                self._champion_splash_pixmap_cache[champ] = pix
                return pix
        except Exception:
            logging.debug("Failed loading champion splash for %s", champ, exc_info=True)
        self._champion_splash_pixmap_cache[champ] = QPixmap()
        return None

    def _apply_account_list_background(self):
        if not hasattr(self, "account_list_background"):
            return
        self.account_list_background.set_dark_mode(self._dark_mode)
        pixmap = None
        if self._champion_splash_enabled:
            pixmap = self._load_champion_splash_pixmap(self._champion_splash_champion)
        self.account_list_background.set_background(
            enabled=self._champion_splash_enabled and bool(pixmap and not pixmap.isNull()),
            pixmap=pixmap,
            opacity=self._champion_splash_opacity,
            edge_fade=self._champion_splash_edge_fade,
            inner_fade=self._champion_splash_inner_fade,
        )

    def _apply_window_size(self, resolution: str):
        """Resize the window without treating it as a user-initiated custom resize."""
        width, height = _parse_resolution(resolution, fallback=(660, 480))
        self._suppress_window_size_persistence = True
        try:
            self.resize(width, max(480, height))
        finally:
            self._suppress_window_size_persistence = False

    def _persist_window_size(self):
        """Persist the current window size as the custom startup size."""
        if self.isMaximized() or self.isFullScreen():
            return
        current_resolution = f"{self.width()}x{self.height()}"
        self._window_size = current_resolution
        self._window_size_mode = 'custom'
        self._settings['window_size'] = current_resolution
        self._settings['window_size_mode'] = 'custom'
        save_settings(self._settings)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._suppress_window_size_persistence:
            return
        if self.isMaximized() or self.isFullScreen():
            return
        self._window_size_mode = 'custom'
        self._window_resize_save_timer.start()
    
    def toggle_theme(self):
        """Toggle between dark and light mode."""
        self._dark_mode = not self._dark_mode
        if 'logged_in_gradient_color' not in self._settings:
            self._logged_in_gradient_color = _default_logged_in_highlight(self._dark_mode)
        self._hover_highlight_color = _resolve_row_hover_highlight(
            self._hover_highlight_color_setting,
            self._dark_mode,
        )
        self._apply_theme()
        self._settings['dark_mode'] = self._dark_mode
        save_settings(self._settings)

    def _theme_with_text_zoom(self, base: str, dark_mode: bool) -> str:
        """Merge base theme with text zoom scaling."""
        point_size = max(8, int(round(9 * self._text_zoom_percent / 100)))
        cog_bg = "#313244" if dark_mode else "#d2d3db"
        cog_fg = "#cdd6f4" if dark_mode else "#2e2d2a"
        cog_border = "#45475a" if dark_mode else "#c4c6cf"
        cog_hover = "#45475a" if dark_mode else "#c8c9d1"
        cog_pressed = "#585b70" if dark_mode else "#bebfc8"
        cog_focus = "#6c7086" if dark_mode else "#a8a8a8"
        list_border = "#45475a" if dark_mode else "#c4c6cf"
        search_fg = "#dbe4ff" if dark_mode else "#2e2d2a"
        search_bg = "#171a2a" if dark_mode else "#f2f3f6"
        search_border = "#3f4b71" if dark_mode else "#d0d0d6"
        search_placeholder = "#a8b4d6" if dark_mode else "#7c756b"
        return (
            base
            + f"\nQWidget {{ font-size: {point_size}pt; }}\n"
            + "\n"
            + "QLineEdit#accountSearchInput {\n"
            + f"    color: {search_fg};\n"
            + f"    background-color: {search_bg};\n"
            + f"    border: 1px solid {search_border};\n"
            + "    border-radius: 4px;\n"
            + "    padding: 4px 6px;\n"
            + "}\n"
            + "QLineEdit#accountSearchInput::placeholder {\n"
            + f"    color: {search_placeholder};\n"
            + "}\n"
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
            + "QFrame#accountListContainer {\n"
            + f"    border: 1px solid {list_border};\n"
            + "    border-radius: 6px;\n"
            + "    background: transparent;\n"
            + "}\n"
            + "QListWidget#accountListWidget {\n"
            + "    background: transparent;\n"
            + "    border: none;\n"
            + "}\n"
        )

    def _apply_theme(self):
        """Apply the current theme stylesheet."""
        if self._dark_mode:
            self.setStyleSheet(self._theme_with_text_zoom(DARK_STYLESHEET, dark_mode=True))
            self._theme_button.setText("Light Mode")
        else:
            self.setStyleSheet(self._theme_with_text_zoom(LIGHT_STYLESHEET, dark_mode=False))
            self._theme_button.setText("Dark Mode")

        # Palette fallback prevents first-paint placeholder/text color glitches on some Windows setups.
        self._apply_filter_input_palette()
        QTimer.singleShot(0, self._apply_filter_input_palette)
        self._apply_account_list_background()

        self.update_account_item_states()
        self._apply_title_bar_theme()
        if self._tray_menu:
            self._tray_menu.setStyleSheet(self._tray_menu_stylesheet())

    def _apply_filter_input_palette(self):
        """Apply stable text/placeholder colors for filter controls."""
        if not hasattr(self, "search_input"):
            return

        search_palette = self.search_input.palette()
        combo_palette = self.tag_filter_combo.palette()

        if self._dark_mode:
            search_palette.setColor(QPalette.Base, QColor("#171a2a"))
            search_palette.setColor(QPalette.Text, QColor("#dbe4ff"))
            search_palette.setColor(QPalette.PlaceholderText, QColor("#a8b4d6"))
            combo_palette.setColor(QPalette.Base, QColor("#181825"))
            combo_palette.setColor(QPalette.Text, QColor("#cdd6f4"))
            combo_palette.setColor(QPalette.ButtonText, QColor("#cdd6f4"))
        else:
            search_palette.setColor(QPalette.Base, QColor("#f2f3f6"))
            search_palette.setColor(QPalette.Text, QColor("#2e2d2a"))
            search_palette.setColor(QPalette.PlaceholderText, QColor("#7c756b"))
            combo_palette.setColor(QPalette.Base, QColor("#f2f3f6"))
            combo_palette.setColor(QPalette.Text, QColor("#2e2d2a"))
            combo_palette.setColor(QPalette.ButtonText, QColor("#2e2d2a"))

        self.search_input.setPalette(search_palette)
        self.tag_filter_combo.setPalette(combo_palette)

    def open_settings_dialog(self):
        """Open the settings dialog and apply any changes."""
        dialog_settings = dict(self._settings)
        dialog_settings['current_window_size'] = f"{self.width()}x{self.height()}"
        dialog = SettingsDialog(self, settings=dialog_settings, apply_callback=self._apply_settings_values)
        if dialog.exec_() != QDialog.Accepted:
            return

        values = dialog.get_values()
        self._apply_settings_values(values)

    def _apply_settings_values(self, values: dict):
        """Apply settings values to runtime state and persist them."""
        self._settings.update(values)
        self._start_minimized_to_tray = bool(values.get('start_minimized_to_tray', self._start_minimized_to_tray))
        self._close_behavior = str(values.get('close_behavior', self._close_behavior))
        self._auto_lock_minutes = int(values.get('auto_lock_minutes', self._auto_lock_minutes))
        self._remember_password_24h = bool(values.get('remember_password_24h', self._remember_password_24h))
        self._clipboard_auto_clear_seconds = int(values.get('clipboard_auto_clear_seconds', self._clipboard_auto_clear_seconds))
        self._confirm_before_launch = bool(values.get('confirm_before_launch', self._confirm_before_launch))
        self._confirm_before_delete = bool(values.get('confirm_before_delete', self._confirm_before_delete))
        self._account_sort_mode = str(values.get('account_sort_mode', self._account_sort_mode or 'manual'))
        self._rank_refresh_mode = str(values.get('rank_refresh_mode', self._rank_refresh_mode))
        self._auto_check_updates = bool(values.get('auto_check_updates', self._auto_check_updates))
        self._diagnostics_log_level = str(values.get('diagnostics_log_level', self._diagnostics_log_level)).upper()
        self._show_ranks = bool(values['show_ranks'])
        self._show_rank_images = bool(values['show_rank_images'])
        self._show_tags = bool(values['show_tags'])
        self._auto_open_ingame_page = bool(values['auto_open_ingame_page'])
        self._tag_size = str(values['tag_size'])
        self._tag_chip_style = str(values.get('tag_chip_style', self._tag_chip_style))
        self._text_zoom_percent = int(values['text_zoom_percent'])
        self._logged_in_gradient_color = str(values.get('logged_in_gradient_color', self._logged_in_gradient_color))
        self._hover_highlight_color_setting = str(
            values.get('hover_highlight_color', self._hover_highlight_color_setting)
        )
        self._hover_highlight_color = _resolve_row_hover_highlight(
            self._hover_highlight_color_setting,
            self._dark_mode,
        )
        self._champion_splash_enabled = bool(values.get('champion_splash_enabled', self._champion_splash_enabled))
        self._champion_splash_champion = str(values.get('champion_splash_champion', self._champion_splash_champion))
        self._champion_splash_opacity = int(values.get('champion_splash_opacity', self._champion_splash_opacity))
        self._champion_splash_edge_fade = LOCKED_CHAMPION_SPLASH_EDGE_FADE
        self._champion_splash_inner_fade = LOCKED_CHAMPION_SPLASH_INNER_FADE
        self._logged_in_gradient_intensity = int(values.get('logged_in_gradient_intensity', self._logged_in_gradient_intensity))
        self._logged_in_border_width = int(values.get('logged_in_border_width', self._logged_in_border_width))
        self._logged_in_border_opacity = int(values.get('logged_in_border_opacity', self._logged_in_border_opacity))
        self._row_density = str(values.get('row_density', self._row_density))
        self._rank_icon_size = int(values.get('rank_icon_size', self._rank_icon_size))
        self._rank_text_brightness = int(values.get('rank_text_brightness', self._rank_text_brightness))
        self._window_size = values['window_size']
        self._window_size_mode = str(values.get('window_size_mode', 'custom')).strip().lower()
        if self._window_size_mode not in {'static', 'custom'}:
            self._window_size_mode = 'custom'

        self._settings['window_size_mode'] = self._window_size_mode
        if self._window_size_mode == 'custom':
            self._apply_window_size(self._window_size)
        else:
            self._apply_window_size(self._window_size)

        if sys.platform.startswith('win'):
            try:
                _set_startup_enabled(bool(values['start_on_windows_startup']))
            except Exception as exc:
                QMessageBox.warning(self, "Settings", f"Could not update startup setting: {exc}")
        else:
            self._settings['start_on_windows_startup'] = False

        if not self._remember_password_24h:
            self._clear_password_grace()

        save_settings(self._settings)
        self._configure_diagnostics_logging()
        self._update_rank_refresh_timer()
        self._reset_auto_lock_timer()
        self._apply_theme()
        self.refresh_account_list()

    def _apply_title_bar_theme(self):
        """Update the native Windows title bar to match the active theme."""
        _apply_windows11_chrome(self, self._dark_mode)

    def _configure_diagnostics_logging(self):
        """Configure lightweight file logging based on user-selected level."""
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        level = getattr(logging, self._diagnostics_log_level, logging.INFO)
        root = logging.getLogger()
        if not root.handlers:
            logging.basicConfig(
                filename=str(LOG_FILE),
                level=level,
                format="%(asctime)s [%(levelname)s] %(message)s",
            )
        else:
            root.setLevel(level)

    def open_logs_folder(self):
        """Open diagnostics logs folder in file manager."""
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        try:
            if sys.platform.startswith("win"):
                os.startfile(str(LOGS_DIR))
            else:
                webbrowser.open(LOGS_DIR.resolve().as_uri())
        except Exception as exc:
            self._show_error("Logs", f"Could not open logs folder: {exc}")

    def _create_tray_icon(self):
        """Create system tray icon and menu for minimize-to-tray behavior."""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            self._tray_icon = None
            self._tray_menu = None
            return

        self._tray_icon = QSystemTrayIcon(self)
        icon = self.windowIcon() or QApplication.windowIcon()
        if not icon.isNull():
            self._tray_icon.setIcon(icon)
        self._tray_icon.setToolTip("League of Legends Account Manager")

        tray_menu = QMenu(self)
        tray_menu.setObjectName("trayQuickMenu")
        tray_menu.setWindowFlags(tray_menu.windowFlags() | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
        tray_menu.setAttribute(Qt.WA_TranslucentBackground, True)
        tray_menu.setContentsMargins(0, 0, 0, 0)
        tray_menu.setStyleSheet(self._tray_menu_stylesheet())
        show_action = QAction("Show", self)
        show_action.triggered.connect(self._show_from_tray)
        self._tray_launch_last_action = QAction("Launch last account", self)
        self._tray_launch_last_action.triggered.connect(self._launch_last_account_from_tray)
        self._tray_lock_action = QAction("Lock app", self)
        self._tray_lock_action.triggered.connect(self._lock_from_tray)
        self._tray_settings_action = QAction("Open settings", self)
        self._tray_settings_action.triggered.connect(self._open_settings_from_tray)
        self._tray_watcher_diag_action = QAction("Watcher diagnostics", self)
        self._tray_watcher_diag_action.triggered.connect(self.open_ingame_diagnostics)
        self._tray_watcher_status_action = QAction("Watcher: idle", self)
        self._tray_watcher_status_action.setEnabled(False)
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self._quit_from_tray)

        tray_menu.addAction(show_action)
        tray_menu.addAction(self._tray_launch_last_action)
        tray_menu.addAction(self._tray_lock_action)
        tray_menu.addAction(self._tray_settings_action)
        tray_menu.addAction(self._tray_watcher_diag_action)
        tray_menu.addSeparator()
        tray_menu.addAction(self._tray_watcher_status_action)
        tray_menu.addSeparator()
        tray_menu.addAction(quit_action)
        self._tray_menu = tray_menu
        self._tray_icon.setContextMenu(tray_menu)
        self._tray_icon.activated.connect(self._on_tray_activated)
        self._tray_icon.show()
        self._update_tray_actions_state()
        self._update_tray_watcher_status()

    def _tray_menu_stylesheet(self):
        """Return a theme-aware stylesheet for standout tray quick actions."""
        if self._dark_mode:
            return """
QMenu#trayQuickMenu {
    background-color: #1e1e2e;
    border: 1px solid #45475a;
    border-radius: 11px;
    padding: 4px;
    font-size: 9pt;
    margin: 0px;
}
QMenu#trayQuickMenu::item {
    color: #cdd6f4;
    background-color: transparent;
    border: 1px solid transparent;
    border-radius: 6px;
    margin: 1px 0px;
    padding: 5px 9px;
    min-height: 16px;
}
QMenu#trayQuickMenu::item:selected {
    background-color: #313244;
    border: 1px solid #585b70;
    color: #ffffff;
}
QMenu#trayQuickMenu::item:disabled {
    background-color: transparent;
    border: 1px solid transparent;
    color: #7f849c;
}
QMenu#trayQuickMenu::separator {
    height: 1px;
    background: #45475a;
    margin: 5px 7px;
}
"""

        return """
QMenu#trayQuickMenu {
    background-color: #ece8e1;
    border: 1px solid #c5beb3;
    border-radius: 11px;
    padding: 4px;
    font-size: 9pt;
    margin: 0px;
}
QMenu#trayQuickMenu::item {
    color: #2e2d2a;
    background-color: transparent;
    border: 1px solid transparent;
    border-radius: 6px;
    margin: 1px 0px;
    padding: 5px 9px;
    min-height: 16px;
}
QMenu#trayQuickMenu::item:selected {
    background-color: #d6d0c6;
    border: 1px solid #b9b1a5;
    color: #2e2d2a;
}
QMenu#trayQuickMenu::item:disabled {
    background-color: transparent;
    border: 1px solid transparent;
    color: #8b8377;
}
QMenu#trayQuickMenu::separator {
    height: 1px;
    background: #d0c8be;
    margin: 5px 7px;
}
"""

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            self._show_from_tray()

    def _show_from_tray(self):
        self.showNormal()
        if not self.account_manager:
            unlocked = self.request_master_password(fatal_on_fail=False)
            if not unlocked:
                self.hide()
                return
        self.raise_()
        self.activateWindow()

    def _open_settings_from_tray(self):
        self._show_from_tray()
        if self.isVisible():
            self.open_settings_dialog()

    def _lock_from_tray(self):
        self._lock_application(hide_window=True)

    def _launch_last_account_from_tray(self):
        if not self._last_launched_username:
            QMessageBox.information(self, "Tray", "No previous account launch found yet.")
            return

        self._show_from_tray()
        if not self.account_manager:
            return

        account = self.account_manager.get_account(self._last_launched_username)
        if not account:
            QMessageBox.warning(
                self,
                "Tray",
                f"Saved last account '{self._last_launched_username}' is no longer available.",
            )
            return

        for index in range(self.account_list.count()):
            item = self.account_list.item(index)
            if item.data(Qt.UserRole) == account.username:
                self.account_list.setCurrentItem(item)
                break

        self.launch_account()

    def _lock_application(self, hide_window: bool = False):
        """Force app to locked state so master password is required again."""
        self._clear_password_grace()
        self._stop_ingame_watcher()
        self.account_manager = None
        self._logged_in_username = None
        self._session_miss_count = 0
        self.refresh_account_list()
        self.launch_btn.setEnabled(False)
        self.edit_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)

        if hide_window:
            self.hide()

        if self._tray_icon and self._tray_icon.isVisible():
            self._tray_icon.showMessage(
                "League Account Manager",
                "Application locked. Enter master password to unlock.",
                QSystemTrayIcon.Information,
                2500,
            )

        self._update_tray_actions_state()

    def _quit_from_tray(self):
        self._quitting_to_exit = True
        self.close()

    def closeEvent(self, event):
        if (
            not self._quitting_to_exit
            and self._close_behavior == "tray"
            and self._tray_icon
            and self._tray_icon.isVisible()
        ):
            self.hide()
            event.ignore()
            return
        super().closeEvent(event)

    def _update_tray_actions_state(self):
        if self._tray_launch_last_action:
            if self._last_launched_username:
                self._tray_launch_last_action.setText(f"Launch last account ({self._last_launched_username})")
                self._tray_launch_last_action.setEnabled(True)
            else:
                self._tray_launch_last_action.setText("Launch last account")
                self._tray_launch_last_action.setEnabled(False)

    def _update_tray_watcher_status(self):
        if not self._tray_watcher_status_action:
            return

        status = self._ingame_watch_status or {}
        watcher_active = bool(status.get("watcher_active", False))
        summary = str(status.get("summary", "Watcher idle") or "Watcher idle")
        if watcher_active:
            self._tray_watcher_status_action.setText(f"Watcher: {summary}")
        else:
            self._tray_watcher_status_action.setText("Watcher: idle")

    def _on_ingame_watch_status(self, status: object):
        if not isinstance(status, dict):
            return
        next_status = dict(status)
        next_status["watcher_active"] = bool(
            self.ingame_watch_thread and self.ingame_watch_thread.isRunning()
        )
        self._ingame_watch_status = next_status
        self._update_tray_watcher_status()
        if self.ingame_diag_dialog:
            self.ingame_diag_dialog.refresh_status()

    def _run_ingame_detection_test(self) -> dict:
        result = RiotClientIntegration.probe_live_client_api(timeout_seconds=1.5)
        result["watcher_active"] = bool(self.ingame_watch_thread and self.ingame_watch_thread.isRunning())
        self._ingame_watch_status = dict(result)
        self._update_tray_watcher_status()
        return result

    def _get_ingame_diagnostics_status(self) -> dict:
        return dict(self._ingame_watch_status)

    def open_ingame_diagnostics(self):
        if not self.ingame_diag_dialog:
            self.ingame_diag_dialog = InGameDiagnosticsDialog(
                status_provider=self._get_ingame_diagnostics_status,
                test_callback=self._run_ingame_detection_test,
                parent=self,
            )
        self.ingame_diag_dialog.show()
        self.ingame_diag_dialog.raise_()
        self.ingame_diag_dialog.activateWindow()

    @staticmethod
    def _version_tuple(value: str) -> tuple[int, ...]:
        cleaned = str(value or "").strip().lstrip("vV")
        if not cleaned:
            return (0,)
        core = cleaned.split("-", 1)[0]
        parts = []
        for token in core.split("."):
            try:
                parts.append(int(token))
            except ValueError:
                parts.append(0)
        return tuple(parts) if parts else (0,)

    def _is_newer_release(self, latest_tag: str) -> bool:
        return self._version_tuple(latest_tag) > self._version_tuple(APP_VERSION)

    @staticmethod
    def _build_release_notes_preview(raw_notes: str) -> str:
        """Trim GitHub release notes down to the user-facing summary section."""
        notes = str(raw_notes or "").strip()
        if not notes:
            return ""

        separator = "-------------------------"
        if separator in notes:
            notes = notes.split(separator, 1)[0].rstrip()

        br_matches = list(re.finditer(r"<br\s*/?>", notes, flags=re.IGNORECASE))
        if br_matches:
            notes = notes[br_matches[-1].end():].lstrip()

        return notes[:400] + ("..." if len(notes) > 400 else "")

    def check_for_updates_now(self):
        """User-triggered update check."""
        self._check_for_updates(force=True)

    def _pick_release_asset(self, assets: list[dict]) -> Optional[dict]:
        """Choose best portable asset for current platform."""
        if not assets:
            return None

        def _matches(name: str, exts: tuple[str, ...]) -> bool:
            low = name.lower()
            return any(low.endswith(ext) for ext in exts)

        def _is_installer(name: str) -> bool:
            low = name.lower()
            return "installer" in low or "setup" in low

        if sys.platform.startswith("win"):
            preferred_exts = (".exe", ".zip")
        elif sys.platform == "darwin":
            preferred_exts = (".app", ".dmg", ".zip")
        else:
            preferred_exts = (".appimage", ".deb", ".rpm", ".tar.gz", ".zip")

        for asset in assets:
            name = str(asset.get("name") or "")
            if _is_installer(name):
                continue
            if _matches(name, preferred_exts):
                return asset

        for asset in assets:
            name = str(asset.get("name") or "")
            if _matches(name, preferred_exts):
                return asset

        for asset in assets:
            name = str(asset.get("name") or "")
            if not _is_installer(name):
                return asset

        return None

    def _find_executable_in_zip(
        self,
        zip_path: Path,
        extract_dir: Path,
        preferred_name: str = "",
    ) -> Optional[Path]:
        """Extract zip and return best executable candidate for self-update."""
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(extract_dir)

        if sys.platform.startswith("win"):
            candidates = [
                p
                for p in extract_dir.rglob("*.exe")
                if p.is_file() and "unins" not in p.name.lower()
            ]
        else:
            candidates = [
                p
                for p in extract_dir.rglob("*")
                if p.is_file() and os.access(str(p), os.X_OK)
            ]

        if not candidates:
            return None

        preferred_lower = preferred_name.lower().strip()
        # Prefer matching executable name, then shallower paths.
        candidates.sort(
            key=lambda p: (
                0 if preferred_lower and p.name.lower() == preferred_lower else 1,
                len(p.parts),
                p.name.lower(),
            )
        )
        return candidates[0]

    @staticmethod
    def _file_sha256(path: Path) -> str:
        """Compute SHA-256 checksum for update identity checks."""
        digest = hashlib.sha256()
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def _stage_windows_binary_swap_and_restart(self, new_executable: Path):
        """Replace current .exe after exit, then restart app."""
        current_exe = Path(sys.executable).resolve()
        updates_dir = new_executable.parent
        script_path = updates_dir / f"apply-update-{int(time.time())}.bat"

        script = (
            "@echo off\n"
            "setlocal\n"
            f"set \"SRC={new_executable}\"\n"
            f"set \"DST={current_exe}\"\n"
            "for /l %%i in (1,1,120) do (\n"
            "  move /Y \"%SRC%\" \"%DST%\" >nul 2>nul && goto launch\n"
            "  ping -n 2 127.0.0.1 >nul\n"
            ")\n"
            "goto done\n"
            ":launch\n"
            "start \"\" \"%DST%\"\n"
            ":done\n"
            "del \"%~f0\"\n"
        )
        script_path.write_text(script, encoding="utf-8")
        subprocess.Popen(["cmd", "/c", str(script_path)])

    def _stage_windows_directory_update_and_restart(self, source_dir: Path):
        """Copy extracted onedir build over current app directory after exit."""
        current_exe = Path(sys.executable).resolve()
        current_dir = current_exe.parent
        script_path = source_dir.parent / f"apply-update-{int(time.time())}.bat"

        script = (
            "@echo off\n"
            "setlocal\n"
            f"set \"SRC={source_dir}\"\n"
            f"set \"DST={current_dir}\"\n"
            f"set \"EXE={current_exe.name}\"\n"
            "for /l %%i in (1,1,120) do (\n"
            "  xcopy \"%SRC%\\*\" \"%DST%\\\" /E /I /Y >nul 2>nul\n"
            "  if exist \"%DST%\\%EXE%\" goto launch\n"
            "  ping -n 2 127.0.0.1 >nul\n"
            ")\n"
            "goto done\n"
            ":launch\n"
            "start \"\" \"%DST%\\%EXE%\"\n"
            ":done\n"
            "del \"%~f0\"\n"
        )
        script_path.write_text(script, encoding="utf-8")
        subprocess.Popen(["cmd", "/c", str(script_path)])

    def _replace_binary_and_restart(self, downloaded_asset: Path, latest_tag: str):
        """Directly replace portable app binary and restart when possible."""
        is_frozen = bool(getattr(sys, "frozen", False))
        if not is_frozen:
            raise RuntimeError("Direct self-update is only available in the packaged app.")

        current_exe = Path(sys.executable).resolve()
        candidate = downloaded_asset
        extracted_root: Optional[Path] = None
        asset_name = downloaded_asset.name.lower()
        if asset_name.endswith(".zip"):
            extract_dir = downloaded_asset.parent / f"extract-{latest_tag.strip().lstrip('vV') or 'latest'}"
            if extract_dir.exists():
                shutil.rmtree(extract_dir, ignore_errors=True)
            extract_dir.mkdir(parents=True, exist_ok=True)
            candidate = self._find_executable_in_zip(
                downloaded_asset,
                extract_dir,
                preferred_name=current_exe.name,
            )
            if not candidate:
                raise RuntimeError("Downloaded zip does not contain an executable app binary.")
            extracted_root = candidate.parent

        if candidate.exists() and current_exe.exists():
            if self._file_sha256(candidate) == self._file_sha256(current_exe):
                raise RuntimeError(
                    "Downloaded build is identical to your current app build. "
                    "Upload a freshly built release asset for this version."
                )

        if sys.platform.startswith("win"):
            if candidate.suffix.lower() != ".exe":
                raise RuntimeError("Windows update asset must provide a .exe binary.")
            if extracted_root is not None and extracted_root.exists():
                self._stage_windows_directory_update_and_restart(extracted_root)
            else:
                self._stage_windows_binary_swap_and_restart(candidate)
            self._settings["last_seen_release_tag"] = latest_tag
            save_settings(self._settings)
            self._quitting_to_exit = True
            QApplication.quit()
            return

        shutil.copy2(candidate, current_exe)
        os.chmod(str(current_exe), 0o755)
        self._settings["last_seen_release_tag"] = latest_tag
        save_settings(self._settings)
        subprocess.Popen([str(current_exe)])
        self._quitting_to_exit = True
        QApplication.quit()

    def _download_and_install_update(self, asset: dict, latest_tag: str):
        """Download selected release asset and directly update app binary."""
        download_url = str(asset.get("browser_download_url") or "").strip()
        asset_name = str(asset.get("name") or "update-package").strip() or "update-package"
        if not download_url:
            raise RuntimeError("Release asset is missing a download URL.")

        temp_dir = Path(tempfile.gettempdir()) / "lol-account-manager-updates"
        temp_dir.mkdir(parents=True, exist_ok=True)
        target = temp_dir / asset_name

        req = Request(download_url, headers={"User-Agent": "lol-account-manager"})
        with urlopen(req, timeout=30) as resp:
            data = resp.read()
        target.write_bytes(data)

        self._replace_binary_and_restart(target, latest_tag)

    def _check_for_updates(self, force: bool = False):
        """Check latest GitHub release and optionally self-update directly."""
        if not force and not self._auto_check_updates:
            return
        try:
            req = Request(GITHUB_RELEASES_API, headers={"User-Agent": "lol-account-manager"})
            with urlopen(req, timeout=3) as resp:
                payload = json.loads(resp.read().decode("utf-8", errors="ignore"))
            latest_tag = str(payload.get("tag_name") or "").strip()
            if not latest_tag:
                return
            if not self._is_newer_release(latest_tag):
                if force:
                    QMessageBox.information(
                        self,
                        "Update Check",
                        f"You're up to date.\n\nCurrent version: {APP_VERSION}\nLatest version: {latest_tag}",
                    )
                return

            skipped_tag = str(self._settings.get("skipped_update_tag", "")).strip()
            if not force and skipped_tag == latest_tag:
                return

            assets = payload.get("assets") or []
            chosen_asset = self._pick_release_asset(assets)
            notes = str(payload.get("body") or "").strip()
            note_preview = self._build_release_notes_preview(notes)

            dark_mode = bool(getattr(self, "_dark_mode", True))
            if dark_mode:
                dialog_bg = "#0f1424"
                text_primary = "#eef3ff"
                text_secondary = "#aeb6cc"
                text_accent = "#8bb0ff"
                divider_color = "#2b3652"
            else:
                dialog_bg = "#f3f5fb"
                text_primary = "#1f2937"
                text_secondary = "#5b657a"
                text_accent = "#2d5ca8"
                divider_color = "#d5dcec"

            prompt = (
                "<div style='margin-bottom: 8px;'>"
                f"<div style='font-size: 15px; font-weight: 700; color: {text_primary};'>Update available: {latest_tag}</div>"
                f"<div style='margin-top: 2px; color: {text_secondary};'>Current version: {APP_VERSION}</div>"
                "</div>"
                f"<div style='font-weight: 700; color: {text_accent}; margin-bottom: 2px;'>Update now?</div>"
                f"<div style='color: {text_primary};'>The app will restart to finish the update.</div>"
            )
            body_html = prompt
            if note_preview:
                escaped_notes = _escape_html(note_preview).replace("\n", "<br/>")
                body_html += (
                    f"<div style='border-top: 1px solid {divider_color}; margin: 10px 0 8px 0;'></div>"
                    f"<div style='font-weight: 700; color: {text_primary}; margin-bottom: 6px;'>Release notes</div>"
                    f"<div style='color: {text_primary}; line-height: 1.35;'>{escaped_notes}</div>"
                )

            box = QMessageBox(self)
            box.setIcon(QMessageBox.Information)
            box.setWindowTitle("Update Available")
            box.setTextFormat(Qt.RichText)
            box.setText(body_html)
            box.setStyleSheet(
                f"QMessageBox {{ background-color: {dialog_bg}; }}"
                f"QMessageBox QLabel {{ color: {text_primary}; font-size: 12px; min-width: 320px; background: transparent; }}"
                "QPushButton {"
                "  background-color: #252b40;"
                "  color: #f2f5ff;"
                "  border: 1px solid #3c4665;"
                "  border-radius: 6px;"
                "  padding: 6px 12px;"
                "}"
                "QPushButton:hover { background-color: #2c3550; }"
                "QPushButton:pressed { background-color: #1f2638; }"
            )
            install_btn = box.addButton("Install Update", QMessageBox.AcceptRole)
            skip_btn = box.addButton("Skip This Version", QMessageBox.DestructiveRole)
            later_btn = box.addButton("Later", QMessageBox.RejectRole)
            box.setDefaultButton(install_btn)
            box.exec_()

            clicked = box.clickedButton()
            if clicked == skip_btn:
                self._settings["skipped_update_tag"] = latest_tag
                save_settings(self._settings)
                return
            if clicked == later_btn:
                return
            if clicked != install_btn:
                return

            if not chosen_asset:
                release_url = str(payload.get("html_url") or "").strip()
                if release_url:
                    webbrowser.open(release_url)
                QMessageBox.warning(
                    self,
                    "Update",
                    "No downloadable asset found for this release. Opened GitHub release page instead.",
                )
                return

            self._download_and_install_update(chosen_asset, latest_tag)
        except Exception as exc:
            logging.debug("Update check/install failed", exc_info=True)
            if force:
                QMessageBox.warning(self, "Update", f"Could not check or install update right now.\n\n{exc}")

    def _update_rank_refresh_timer(self):
        mode = str(self._rank_refresh_mode or "manual")
        if mode == "manual":
            self._rank_refresh_timer.stop()
            return
        try:
            seconds = max(15, int(mode))
        except ValueError:
            self._rank_refresh_timer.stop()
            return
        self._rank_refresh_timer.setInterval(seconds * 1000)
        self._rank_refresh_timer.start()

    def _refresh_visible_ranks(self):
        if self._show_ranks and self.account_manager:
            self._start_rank_fetches()

    def _clear_clipboard_if_needed(self):
        if self._clipboard_auto_clear_seconds <= 0:
            return
        clipboard = QApplication.clipboard()
        if clipboard.text() == self._clipboard_last_text:
            clipboard.clear()

    def _has_valid_password_grace(self) -> bool:
        if not self._remember_password_24h:
            return False
        expires_at = float(self._settings.get("password_grace_expires_at", 0) or 0)
        return expires_at > time.time()

    def _clear_password_grace(self):
        self._settings.pop("password_grace_expires_at", None)
        self._settings.pop("password_grace_blob", None)
        save_settings(self._settings)

    def _store_password_grace(self, password: str):
        if not self._remember_password_24h:
            self._clear_password_grace()
            return
        if not sys.platform.startswith("win"):
            return
        try:
            import win32crypt
            protected = win32crypt.CryptProtectData(password.encode("utf-8"), None, None, None, None, 0)
            self._settings["password_grace_blob"] = protected.hex()
            self._settings["password_grace_expires_at"] = time.time() + 86400
            save_settings(self._settings)
        except Exception:
            logging.debug("Password grace storage failed", exc_info=True)

    def _try_unlock_with_password_grace(self) -> bool:
        if not self._remember_password_24h or not sys.platform.startswith("win"):
            return False
        if not self._has_valid_password_grace():
            return False
        blob_hex = str(self._settings.get("password_grace_blob", "") or "")
        if not blob_hex:
            return False
        try:
            import win32crypt
            raw = bytes.fromhex(blob_hex)
            _, unprotected = win32crypt.CryptUnprotectData(raw, None, None, None, 0)
            password = unprotected.decode("utf-8")
            if AccountManager.verify_master_password(password):
                self.initialize_account_manager(password)
                return True
        except Exception:
            logging.debug("Password grace unlock failed", exc_info=True)
        self._clear_password_grace()
        return False

    def _reset_auto_lock_timer(self):
        if self._auto_lock_minutes <= 0 or not self.account_manager:
            self._auto_lock_timer.stop()
            return
        self._auto_lock_timer.start(self._auto_lock_minutes * 60 * 1000)

    def _handle_auto_lock_timeout(self):
        if self._unlock_prompt_active:
            return
        if self._has_valid_password_grace():
            self._reset_auto_lock_timer()
            return
        self._unlock_prompt_active = True
        try:
            self.request_master_password(fatal_on_fail=False)
        finally:
            self._unlock_prompt_active = False
            self._reset_auto_lock_timer()

    def eventFilter(self, obj, event):
        """Apply consistent Windows 11 chrome to all shown dialogs/message boxes."""
        if event.type() == QEvent.Show and isinstance(obj, QDialog):
            _apply_windows11_chrome(obj, self._dark_mode)
        if event.type() in (QEvent.MouseButtonPress, QEvent.MouseMove, QEvent.KeyPress):
            self._reset_auto_lock_timer()
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
            if self._try_unlock_with_password_grace():
                return
            # Ask for master password
            self.request_master_password(fatal_on_fail=True)
    
    def request_master_password(self, fatal_on_fail: bool = True):
        """Request master password from user"""
        for attempt in range(3):
            dialog = MasterPasswordDialog(self, is_setup=False)
            if dialog.exec_() == QDialog.Accepted:
                password = dialog.password_input.text()
                if AccountManager.verify_master_password(password):
                    self.initialize_account_manager(password)
                    self._store_password_grace(password)
                    return True
                else:
                    remaining = 3 - attempt - 1
                    if remaining > 0:
                        QMessageBox.warning(
                            self, 
                            "Error", 
                            f"Incorrect password. {remaining} attempts remaining."
                        )
                    elif fatal_on_fail:
                        QMessageBox.critical(self, "Error", "Too many failed attempts.")
                        sys.exit(1)
                    else:
                        QMessageBox.warning(self, "Locked", "Incorrect password.")
                        return False
            else:
                if fatal_on_fail:
                    sys.exit(1)
                return False
        return False
    
    def initialize_account_manager(self, password: str):
        """Initialize account manager with master password"""
        self.account_manager = AccountManager(password)
        self.refresh_account_list()
        self._reset_auto_lock_timer()
        self._update_tray_actions_state()

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

    def _account_row_height(self) -> int:
        return {
            "compact": 74,
            "comfortable": 84,
            "spacious": 96,
        }.get(self._row_density, 84)

    def _sorted_accounts(self, accounts: list[Account]) -> list[Account]:
        """Return accounts sorted by current mode with pinned accounts first."""
        if not accounts:
            return []

        indexed = list(enumerate(accounts))
        mode = str(self._account_sort_mode or "manual")

        if mode == "alphabetical":
            indexed.sort(
                key=lambda pair: (
                    not bool(getattr(pair[1], "is_pinned", False)),
                    (str(getattr(pair[1], "display_name", "") or pair[1].username)).casefold(),
                    pair[0],
                )
            )
            return [acc for _, acc in indexed]

        if mode == "last_used":
            indexed.sort(
                key=lambda pair: (
                    not bool(getattr(pair[1], "is_pinned", False)),
                    str(getattr(pair[1], "last_launched_at", "") or ""),
                    pair[0],
                )
            )
            # Keep most-recent timestamps first inside each pinned group.
            indexed.sort(
                key=lambda pair: str(getattr(pair[1], "last_launched_at", "") or ""),
                reverse=True,
            )
            indexed.sort(
                key=lambda pair: not bool(getattr(pair[1], "is_pinned", False))
            )
            return [acc for _, acc in indexed]

        # Manual order preserves stored order while still bubbling pinned accounts.
        indexed.sort(key=lambda pair: (not bool(getattr(pair[1], "is_pinned", False)), pair[0]))
        return [acc for _, acc in indexed]
    
    def refresh_account_list(self):
        """Refresh the account list display"""
        self.account_list.clear()
        
        if not self.account_manager:
            return
        
        accounts = self.account_manager.get_all_accounts()
        accounts = self._sorted_accounts(accounts)
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
                item.setSizeHint(QSize(0, self._account_row_height()))
                self.account_list.addItem(item)
                
                # Create custom widget
                widget = AccountListItem(
                    account,
                    show_ranks=self._show_ranks,
                    show_rank_images=self._show_rank_images,
                    show_tags=self._show_tags,
                    tag_size=self._tag_size,
                    tag_chip_style=self._tag_chip_style,
                    logged_in_gradient_color=self._logged_in_gradient_color,
                    hover_highlight_color=self._hover_highlight_color,
                    logged_in_gradient_intensity=self._logged_in_gradient_intensity,
                    logged_in_border_width=self._logged_in_border_width,
                    logged_in_border_opacity=self._logged_in_border_opacity,
                    row_density=self._row_density,
                    rank_icon_size=self._rank_icon_size,
                    rank_text_brightness=self._rank_text_brightness,
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
                widget.set_hover_highlight_color(self._hover_highlight_color)
                widget.set_selected(item.isSelected())
                widget.set_logged_in(
                    bool(self._logged_in_username)
                    and item.data(Qt.UserRole) == self._logged_in_username
                )

    @staticmethod
    def _normalize_identity_value(value: str) -> str:
        return " ".join(str(value or "").strip().casefold().split())

    def _match_account_from_riot_identity(self, identity: Optional[dict]) -> Optional[str]:
        """Return the saved account username that best matches Riot session identity."""
        if not identity or not self.account_manager:
            return None

        accounts = self.account_manager.get_all_accounts()
        if not accounts:
            return None

        riot_username = self._normalize_identity_value(identity.get('username', ''))
        riot_game_name = self._normalize_identity_value(identity.get('game_name', ''))
        riot_game_tag = self._normalize_identity_value(identity.get('game_tag', ''))
        riot_riot_id = ""
        if riot_game_name and riot_game_tag:
            riot_riot_id = f"{riot_game_name}#{riot_game_tag}"

        # Most reliable: Riot ID (display name + tag line)
        if riot_riot_id:
            for account in accounts:
                acc_name = self._normalize_identity_value(getattr(account, 'display_name', '') or account.username)
                acc_tag = self._normalize_identity_value(getattr(account, 'tag_line', '') or 'NA1')
                if f"{acc_name}#{acc_tag}" == riot_riot_id:
                    return account.username

        # Next: login username/email match
        if riot_username:
            for account in accounts:
                if self._normalize_identity_value(account.username) == riot_username:
                    return account.username

        # Last: unique display-name fallback when tag is unavailable
        if riot_game_name:
            name_matches = [
                acc for acc in accounts
                if self._normalize_identity_value(getattr(acc, 'display_name', '') or acc.username) == riot_game_name
            ]
            if len(name_matches) == 1:
                return name_matches[0].username

        return None

    def _sync_logged_in_session_state(self):
        """Reconcile sticky logged-in indicator with the actual Riot session state."""
        if self.login_thread and self.login_thread.isRunning():
            # During launch retries Riot may briefly stop/start; avoid false logout clears.
            return

        if not sys.platform.startswith("win"):
            return

        if not self.account_manager:
            return

        riot_running = RiotClientIntegration.is_riot_client_running()
        identity = RiotClientIntegration.get_riot_session_identity() if riot_running else None

        if identity:
            matched_username = self._match_account_from_riot_identity(identity)
            self._session_miss_count = 0
            if matched_username != self._logged_in_username:
                self._logged_in_username = matched_username
                self.update_account_item_states()
            return

        if not self._logged_in_username:
            self._session_miss_count = 0
            return

        self._session_miss_count += 1
        if self._session_miss_count < self._manual_logout_grace_misses:
            return

        self._logged_in_username = None
        self._session_miss_count = 0
        self.update_account_item_states()

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
        toggle_pin_action = menu.addAction("Unpin Account" if getattr(account, "is_pinned", False) else "Pin Account")
        menu.addSeparator()
        open_opgg_profile_action = menu.addAction("Open OP.GG Profile")
        open_opgg_ingame_action = menu.addAction("Open Live-Game Page")
        menu.addSeparator()
        copy_username_action = menu.addAction("Copy Username")
        copy_password_action = menu.addAction("Copy Password")
        copy_friend_code_action = menu.addAction("Copy Friend Code")

        chosen_action = menu.exec_(self.account_list.viewport().mapToGlobal(position))
        if chosen_action == toggle_pin_action:
            try:
                self.account_manager.set_account_pinned(account.username, not bool(getattr(account, "is_pinned", False)))
                self.refresh_account_list()
            except Exception as exc:
                self._show_error("Pin", f"Could not update pin state: {exc}")
        elif chosen_action == open_opgg_profile_action:
            self._open_opgg_profile(account)
        elif chosen_action == open_opgg_ingame_action:
            self._open_ingame_webpage(self._build_opgg_ingame_url(account))
        elif chosen_action == copy_username_action:
            self.copy_to_clipboard(account.username)
        elif chosen_action == copy_password_action:
            self.copy_to_clipboard(account.password)
        elif chosen_action == copy_friend_code_action:
            friend_code = f"{account.display_name} #{getattr(account, 'tag_line', 'NA1')}"
            self.copy_to_clipboard(friend_code)

    def copy_to_clipboard(self, text: str):
        """Copy text to the system clipboard."""
        QApplication.clipboard().setText(text)
        self._clipboard_last_text = text
        self._clipboard_clear_timer.stop()
        if self._clipboard_auto_clear_seconds > 0:
            self._clipboard_clear_timer.start(self._clipboard_auto_clear_seconds * 1000)

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
                old_logged_in = self._logged_in_username
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
                if old_logged_in and old_logged_in == username:
                    self._logged_in_username = data['username']
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
        
        should_delete = True
        if self._confirm_before_delete:
            reply = QMessageBox.question(
                self,
                "Confirm Delete",
                f"Are you sure you want to delete '{account.display_name}'?",
                QMessageBox.Yes | QMessageBox.No
            )
            should_delete = reply == QMessageBox.Yes

        if should_delete:
            try:
                self.account_manager.delete_account(username)
                if self._logged_in_username == username:
                    self._logged_in_username = None
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

        if self._confirm_before_launch:
            reply = QMessageBox.question(
                self,
                "Confirm Launch",
                f"Launch '{account.display_name}' now?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if reply != QMessageBox.Yes:
                return

        self._stop_ingame_watcher()

        self.current_launch_username = account.username
        self._last_launched_username = account.username
        self._settings["last_launched_username"] = account.username
        save_settings(self._settings)
        self._update_tray_actions_state()
        
        # Show cancellable progress dialog
        self.launch_progress = LaunchProgressDialog(
            f"Starting League of Legends for {account.display_name}...",
            self,
        )
        self.launch_progress.setWindowModality(Qt.WindowModal)
        self.launch_progress.rejected.connect(self._dismiss_launch_progress)
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
            if account:
                try:
                    self.account_manager.mark_account_launched(account.username)
                except Exception:
                    logging.debug("Could not update last launch timestamp", exc_info=True)
                self._logged_in_username = account.username
                self._session_miss_count = 0
                self.refresh_account_list()
            if account and self._auto_open_ingame_page:
                self._start_ingame_watcher(account)
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

    def _build_opgg_profile_url(self, account: Account) -> str:
        """Build op.gg summoner profile URL for an account."""
        region_code = (getattr(account, "region", "NA") or "NA").upper()
        region_slug = OPGG_REGION_MAP.get(region_code, region_code.lower())
        display_name = (getattr(account, "display_name", "") or "").strip() or account.username
        tag_line = (getattr(account, "tag_line", "") or "NA1").strip() or "NA1"
        encoded_name = quote(display_name, safe="")
        encoded_tag = quote(tag_line, safe="")
        return f"https://op.gg/lol/summoners/{region_slug}/{encoded_name}-{encoded_tag}"

    def _open_opgg_profile(self, account: Account):
        """Open an account's op.gg profile in the system browser."""
        url = self._build_opgg_profile_url(account)
        try:
            webbrowser.open_new_tab(url)
        except Exception:
            webbrowser.open(url)

    def _start_ingame_watcher(self, account: Account):
        """Start watching for active-game state and open op.gg once detected."""
        self._stop_ingame_watcher()
        opgg_url = self._build_opgg_ingame_url(account)
        self._ingame_watch_status = {
            "watcher_active": True,
            "status": "starting",
            "summary": "Waiting for active match",
            "timestamp": time.time(),
            "status_code": None,
            "response_bytes": 0,
            "error": "",
            "opgg_url": opgg_url,
        }
        self._update_tray_watcher_status()
        self.ingame_watch_thread = InGameWatcherThread(opgg_url)
        self.ingame_watch_thread.status_updated.connect(self._on_ingame_watch_status)
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
                watcher.status_updated.disconnect()
                watcher.ingame_detected.disconnect()
                watcher.finished.disconnect()
            except Exception:
                pass
            if watcher.isRunning():
                watcher.requestInterruption()
                watcher.wait(1200)
        self._ingame_watch_status = {
            "watcher_active": False,
            "status": "idle",
            "summary": "Watcher stopped",
            "timestamp": time.time(),
            "status_code": None,
            "response_bytes": 0,
            "error": "",
        }
        self._update_tray_watcher_status()
        if self.ingame_diag_dialog:
            self.ingame_diag_dialog.refresh_status()

    def _clear_ingame_watcher(self):
        """Clear completed watcher thread reference."""
        self.ingame_watch_thread = None
        self._ingame_watch_status = {
            "watcher_active": False,
            "status": "idle",
            "summary": "Watcher idle",
            "timestamp": time.time(),
            "status_code": None,
            "response_bytes": 0,
            "error": "",
        }
        self._update_tray_watcher_status()
        if self.ingame_diag_dialog:
            self.ingame_diag_dialog.refresh_status()

    def _dismiss_launch_progress(self):
        """Close and clear launch progress UI if it exists."""
        progress = self.launch_progress
        if not progress:
            return

        # Clear shared reference first to avoid re-entrant double-close crashes.
        self.launch_progress = None
        try:
            progress.rejected.disconnect(self._dismiss_launch_progress)
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
            str(BACKUPS_DIR / "lol_accounts_backup.lolbak"),
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
            str(BACKUPS_DIR),
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
