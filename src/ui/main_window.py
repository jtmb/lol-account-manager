"""Main application window"""
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QToolButton,
    QListWidget, QListWidgetItem, QLabel, QDialog, QLineEdit,
    QMessageBox, QFrame, QFileDialog, QComboBox, QProgressBar, QTabWidget,
    QDateEdit, QGraphicsDropShadowEffect, QMenu, QCheckBox, QGridLayout,
    QTextEdit, QSpinBox, QSystemTrayIcon, QAction, QCompleter, QColorDialog, QInputDialog,
    QStackedWidget, QSizePolicy
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize, QTimer, QDate, QEvent, QRectF, QUrl, QObject
from PyQt5.QtGui import QFont, QColor, QPixmap, QBitmap, QPalette, QPainter, QLinearGradient, QRadialGradient, QPainterPath, QIcon, QPen
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
import math
from urllib.request import Request, urlopen
from urllib.parse import quote

try:
    import qtawesome as qta
except Exception:
    qta = None

try:
    from PyQt5.QtWebEngineWidgets import QWebEngineView
except Exception:
    QWebEngineView = None

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
from src.config.app_config import SETTINGS_PANEL_DEFAULTS
from src import __version__ as APP_VERSION

LOGS_DIR = BACKUPS_DIR.parent / "logs"
LOG_FILE = LOGS_DIR / "app.log"
GITHUB_RELEASES_API = "https://api.github.com/repos/jtmb/lol-account-manager/releases/latest"
DDRAGON_VERSION = "14.24.1"
DEFAULT_LOGGED_IN_HIGHLIGHT_DARK = str(SETTINGS_PANEL_DEFAULTS.get("logged_in_gradient_color", "#6b7280"))
DEFAULT_LOGGED_IN_HIGHLIGHT_LIGHT = str(SETTINGS_PANEL_DEFAULTS.get("logged_in_gradient_color", "#6b7280"))
DEFAULT_ROW_HOVER_HIGHLIGHT_DARK = "#45475a"
DEFAULT_ROW_HOVER_HIGHLIGHT_LIGHT = "#c8c9d1"
HOVER_HIGHLIGHT_THEME_AUTO = "__theme__"
SPLASH_THEME_AUTO = "__none__"
LOCKED_CHAMPION_SPLASH_EDGE_FADE = 80
LOCKED_CHAMPION_SPLASH_INNER_FADE = 75
DEFAULT_APP_BG_COLOR = str(SETTINGS_PANEL_DEFAULTS.get("app_bg_color", "#1e1e2e"))
DEFAULT_APP_SURFACE_COLOR = str(SETTINGS_PANEL_DEFAULTS.get("app_surface_color", "#181825"))
DEFAULT_APP_BORDER_COLOR = str(SETTINGS_PANEL_DEFAULTS.get("app_border_color", "#313244"))
DEFAULT_APP_TEXT_COLOR = str(SETTINGS_PANEL_DEFAULTS.get("app_text_color", "#cdd6f4"))
DEFAULT_APP_ACCENT_COLOR = str(SETTINGS_PANEL_DEFAULTS.get("app_accent_color", "#313244"))
DEFAULT_APP_HOVER_COLOR = str(SETTINGS_PANEL_DEFAULTS.get("app_hover_color", "#45475a"))


def _default_logged_in_highlight(dark_mode: bool) -> str:
    """Return theme-appropriate default logged-in highlight color."""
    return DEFAULT_LOGGED_IN_HIGHLIGHT_DARK


def _default_row_hover_highlight(dark_mode: bool) -> str:
    """Return theme-appropriate default hover/selection row highlight color."""
    return DEFAULT_ROW_HOVER_HIGHLIGHT_DARK


def _resolve_row_hover_highlight(setting_value: str, dark_mode: bool) -> str:
    """Resolve effective hover color from saved setting or theme auto mode."""
    value = str(setting_value or HOVER_HIGHLIGHT_THEME_AUTO).strip()
    if value == HOVER_HIGHLIGHT_THEME_AUTO:
        return _default_row_hover_highlight(True)
    return value


class ClickableIconLabel(QLabel):
    clicked = pyqtSignal()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mouseReleaseEvent(event)


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
CHAMPION_NAME_BY_ID = {champ_id: name for name, champ_id in CHAMPION_SPLASH_OPTIONS}


class _ResizeCallbackFilter(QObject):
    """Event filter that invokes a callback whenever the watched widget is resized.

    Used instead of monkey-patching ``resizeEvent`` on existing QWidget instances,
    which does not work in PyQt5 because Qt dispatches virtual methods via the C++
    vtable and ignores Python instance attributes.
    """

    def __init__(self, callback, parent=None):
        super().__init__(parent)
        self._callback = callback

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Resize:
            self._callback()
        return False  # always pass the event through


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
        self._base_color = QColor(DEFAULT_APP_SURFACE_COLOR)

    def set_base_color(self, color: str):
        candidate = QColor(str(color or "").strip())
        if candidate.isValid():
            self._base_color = candidate
            self.update()

    def set_background(self, enabled: bool, pixmap: Optional[QPixmap], opacity: int, edge_fade: int, inner_fade: int):
        self._enabled = bool(enabled)
        self._pixmap = pixmap
        self._opacity = max(0, min(100, int(opacity)))
        self._edge_fade = max(0, min(100, int(edge_fade)))
        self._inner_fade = max(0, min(100, int(inner_fade)))
        self.update()

    def set_dark_mode(self, enabled: bool):
        self._dark_mode = True
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

        rect = self.rect()
        radius = 10.0
        path = QPainterPath()
        path.addRoundedRect(QRectF(rect).adjusted(0.5, 0.5, -0.5, -0.5), radius, radius)
        painter.setClipPath(path)

        base_color = self._base_color if self._dark_mode else QColor("#ededf0")
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
    # Enabled by default to keep dark non-white window chrome.
    # Set LOLAM_DISABLE_WIN11_CHROME=1 to opt out for troubleshooting.
    if os.environ.get("LOLAM_DISABLE_WIN11_CHROME", "0") == "1":
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

        value = ctypes.c_int(1)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd,
            DWMWA_USE_IMMERSIVE_DARK_MODE,
            ctypes.byref(value),
            ctypes.sizeof(value),
        )

        disable_transitions = ctypes.c_int(1)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd,
            DWMWA_TRANSITIONS_FORCEDISABLED,
            ctypes.byref(disable_transitions),
            ctypes.sizeof(disable_transitions),
        )

        caption_color = ctypes.c_int(0x302B2B)
        text_color = ctypes.c_int(0xF4D6CD)

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


def _arm_first_show_reveal(widget):
    """Hide a top-level window until its first show cycle is complete."""
    if not sys.platform.startswith("win"):
        return
    try:
        widget.setProperty("_first_show_hidden", True)
        widget.setWindowOpacity(0.0)
    except Exception:
        pass


def _reveal_after_first_show(widget):
    """Reveal a window that was hidden during initial paint setup."""
    if not sys.platform.startswith("win"):
        return
    try:
        if not bool(widget.property("_first_show_hidden")):
            return
        widget.setProperty("_first_show_hidden", False)
        # Give Qt/DWM one short beat to complete any deferred style/chrome work
        # before making the first frame visible.
        QTimer.singleShot(40, lambda w=widget: w.setWindowOpacity(1.0) if w is not None and w.isVisible() else None)
    except Exception:
        pass


def _hide_windows_console_window():
    """Hide the attached Windows console window if one exists."""
    if not sys.platform.startswith("win"):
        return
    # Disabled by default because low-level Win32 calls here have caused
    # native startup aborts on some Windows/PyQt combinations.
    if os.environ.get("LOLAM_ENABLE_WIN_WINDOW_HACKS", "0") != "1":
        return
    try:
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if hwnd:
            SW_HIDE = 0
            ctypes.windll.user32.ShowWindow(hwnd, SW_HIDE)
    except Exception:
        pass


def _hide_any_python_titled_window():
    """Hide any visible top-level window titled like 'python' on Windows.

    This is intentionally broad because the flashing popup has persisted across
    multiple code paths and can be external to Qt's own window lifecycle.
    """
    if not sys.platform.startswith("win"):
        return

    # Disabled by default because EnumWindows callback interop can trigger
    # native crashes on some systems. Opt in only when needed.
    if os.environ.get("LOLAM_ENABLE_WIN_WINDOW_HACKS", "0") != "1":
        return

    try:
        user32 = ctypes.windll.user32
    except Exception:
        return

    try:
        get_text = user32.GetWindowTextW
        get_text_len = user32.GetWindowTextLengthW
        is_visible = user32.IsWindowVisible
        show_window = user32.ShowWindow

        WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

        def _enum_cb(hwnd, _lparam):
            try:
                if not is_visible(hwnd):
                    return True

                text_len = get_text_len(hwnd)
                if text_len <= 0:
                    return True

                text_buf = ctypes.create_unicode_buffer(text_len + 1)
                get_text(hwnd, text_buf, text_len + 1)
                title = (text_buf.value or "").strip().lower()

                if title == "python" or title.startswith("python "):
                    show_window(hwnd, 0)
            except Exception:
                pass
            return True

        user32.EnumWindows(WNDENUMPROC(_enum_cb), 0)
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
QLineEdit, QDateEdit, QTextEdit, QPlainTextEdit {
    background-color: #1a1a24;
    color: #cdd6f4;
    border: 1px solid #404758;
    border-radius: 6px;
    padding: 8px 12px;
    selection-background-color: #7aa2f7;
}
QLineEdit:hover, QDateEdit:hover, QTextEdit:hover, QPlainTextEdit:hover {
    border: 1px solid #585b70;
}
QLineEdit:focus, QDateEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border: 2px solid #7aa2f7;
    outline: none;
}
QLineEdit::placeholder {
    color: #9aa4bf;
}
QSpinBox {
    background-color: #1a1a24;
    color: #cdd6f4;
    border: 1px solid #404758;
    border-radius: 6px;
    padding: 4px 8px;
}
QSpinBox:hover {
    border: 1px solid #585b70;
}
QSpinBox::up-button, QSpinBox::down-button {
    subcontrol-origin: border;
    background-color: #313244;
    border-left: 1px solid #404758;
    width: 18px;
    padding: 2px;
}
QSpinBox::up-button:hover, QSpinBox::down-button:hover {
    background-color: #404758;
}
QComboBox {
    background-color: #1a1a24;
    color: #cdd6f4;
    border: 1px solid #404758;
    border-radius: 6px;
    padding: 8px 12px;
    padding-right: 32px;
    min-height: 24px;
}
QComboBox:hover {
    border: 1px solid #585b70;
    background-color: #1f1f2a;
}
QComboBox:focus {
    border: 2px solid #7aa2f7;
}
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: center right;
    width: 24px;
    border: none;
    background: transparent;
    margin-right: 4px;
}
QComboBox::down-arrow {
    image: url("data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iOCIgdmlld0JveD0iMCAwIDEyIDgiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHBhdGggZD0iTTEgMUw2IDZMMTEgMSIgc3Ryb2tlPSIjY2RkNmY0IiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIvPjwvc3ZnPg==");
    width: 12px;
    height: 8px;
}
QComboBox QAbstractItemView {
    background-color: #1a1a24;
    color: #cdd6f4;
    border: 1px solid #404758;
    border-radius: 6px;
    outline: none;
    selection-background-color: #404758;
    show-decoration-selected: 1;
}
QComboBox QAbstractItemView::item {
    padding: 6px 12px;
    border-radius: 4px;
}
QComboBox QAbstractItemView::item:selected {
    background-color: #7aa2f7;
    color: #1e1e2e;
}
QComboBox QAbstractItemView::item:hover {
    background-color: #313244;
    color: #cdd6f4;
}
QLabel {
    color: #cdd6f4;
    font-weight: 500;
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
    DWMWA_TRANSITIONS_FORCEDISABLED = 3
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
    game_ended = pyqtSignal(object)  # latest match result dict

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
                    if opened_for_current_game:
                        match_result = RiotClientIntegration.get_latest_match_result(timeout_seconds=1.5)
                        match_result["timestamp"] = time.time()
                        self.game_ended.emit(match_result)
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


class _ImageFetchThread(QThread):
    """Background thread that downloads a single image URL and emits the raw bytes."""
    image_ready = pyqtSignal(str, bytes)  # (tag, raw_bytes)

    def __init__(self, tag: str, url: str, parent=None):
        super().__init__(parent)
        self._tag = tag
        self._url = url

    def run(self):
        try:
            req = Request(self._url, headers={"User-Agent": "lol-account-manager/1.0"})
            with urlopen(req, timeout=6) as resp:
                raw = resp.read()
            self.image_ready.emit(self._tag, raw)
        except Exception:
            self.image_ready.emit(self._tag, b"")


class _UggBuildFetchThread(QThread):
    """Fetch u.gg champion page and extract embedded build/rune data from SSR JSON."""

    build_ready = pyqtSignal(dict)

    def __init__(self, page_url: str, role_hint: str = "", parent=None):
        super().__init__(parent)
        self._page_url = str(page_url or "").strip()
        self._role_hint = str(role_hint or "").strip().casefold()

    @staticmethod
    def _extract_ssr_data(html: str) -> Optional[dict]:
        marker = "window.__SSR_DATA__"
        pos = html.find(marker)
        if pos < 0:
            return None

        eq = html.find("=", pos)
        if eq < 0:
            return None
        start = html.find("{", eq)
        if start < 0:
            return None

        depth = 0
        in_str = False
        escaped = False
        end = -1
        for i, ch in enumerate(html[start:], start=start):
            if in_str:
                if escaped:
                    escaped = False
                elif ch == "\\":
                    escaped = True
                elif ch == '"':
                    in_str = False
                continue
            if ch == '"':
                in_str = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    end = i
                    break

        if end < 0:
            return None

        try:
            return json.loads(html[start:end + 1])
        except Exception:
            return None

    def _pick_role_payload(self, role_map: dict) -> tuple[str, dict]:
        if not isinstance(role_map, dict):
            return "", {}

        role_aliases = {
            "top": "top",
            "jungle": "jungle",
            "jg": "jungle",
            "mid": "mid",
            "middle": "mid",
            "adc": "adc",
            "bot": "adc",
            "bottom": "adc",
            "support": "support",
            "supp": "support",
            "sup": "support",
        }
        wanted = role_aliases.get(self._role_hint, "")

        if wanted:
            for key, payload in role_map.items():
                if str(key).split("_")[-1] == wanted and isinstance(payload, dict):
                    return wanted, payload

        best_role = ""
        best_payload: dict = {}
        best_matches = -1
        for key, payload in role_map.items():
            if not isinstance(payload, dict):
                continue
            role_name = str(key).split("_")[-1]
            rune_data = payload.get("rec_runes") if isinstance(payload.get("rec_runes"), dict) else {}
            matches = int(rune_data.get("matches", 0) or 0)
            if matches > best_matches:
                best_matches = matches
                best_role = role_name
                best_payload = payload
        return best_role, best_payload

    def run(self):
        if not self._page_url:
            self.build_ready.emit({"ok": False, "error": "Missing page URL"})
            return

        try:
            req = Request(self._page_url, headers={"User-Agent": "Mozilla/5.0"})
            with urlopen(req, timeout=8) as resp:
                html = resp.read().decode("utf-8", errors="ignore")
        except Exception as exc:
            self.build_ready.emit({"ok": False, "error": f"Failed fetching u.gg page: {exc}"})
            return

        ssr_data = self._extract_ssr_data(html)
        if not ssr_data:
            self.build_ready.emit({"ok": False, "error": "No SSR data found in u.gg page"})
            return

        overview_key = ""
        for key in ssr_data.keys():
            k = str(key)
            if "/overview/" in k and "ap-overview" not in k and "tank-overview" not in k and "ad-overview" not in k and "crit-overview" not in k and "lethality-overview" not in k and "onhit-overview" not in k:
                overview_key = k
                break
            if "overview_" in k and "_recommended::" in k:
                overview_key = k
                break

        if not overview_key:
            self.build_ready.emit({"ok": False, "error": "No recommended overview key in SSR data"})
            return

        overview_obj = ssr_data.get(overview_key)
        role_map = overview_obj.get("data") if isinstance(overview_obj, dict) else None
        if not isinstance(role_map, dict) or not role_map:
            self.build_ready.emit({"ok": False, "error": "Recommended overview payload missing"})
            return

        picked_role, picked_payload = self._pick_role_payload(role_map)
        if not picked_payload:
            self.build_ready.emit({"ok": False, "error": "No role payload available"})
            return

        rec_runes = picked_payload.get("rec_runes") if isinstance(picked_payload.get("rec_runes"), dict) else {}
        rec_shards = picked_payload.get("stat_shards") if isinstance(picked_payload.get("stat_shards"), dict) else {}
        rec_start = picked_payload.get("rec_starting_items") if isinstance(picked_payload.get("rec_starting_items"), dict) else {}
        rec_core = picked_payload.get("rec_core_items") if isinstance(picked_payload.get("rec_core_items"), dict) else {}
        rec_skills = picked_payload.get("rec_skills") if isinstance(picked_payload.get("rec_skills"), dict) else {}
        rec_skill_path = picked_payload.get("rec_skill_path") if isinstance(picked_payload.get("rec_skill_path"), dict) else {}

        item_stage_options: dict[str, list[dict]] = {}
        for i in range(1, 7):
            raw_opts = picked_payload.get(f"item_options_{i}")
            parsed: list[dict] = []
            if isinstance(raw_opts, list):
                for opt in raw_opts:
                    if not isinstance(opt, dict):
                        continue
                    try:
                        item_id = int(opt.get("id", 0) or 0)
                    except (TypeError, ValueError):
                        item_id = 0
                    if item_id <= 0:
                        continue
                    parsed.append({
                        "id": item_id,
                        "win_rate": float(opt.get("win_rate", 0.0) or 0.0),
                        "matches": int(opt.get("matches", 0) or 0),
                    })
            item_stage_options[str(i)] = parsed

        out = {
            "ok": True,
            "source": self._page_url,
            "role": picked_role,
            "matches": int(rec_runes.get("matches", 0) or 0),
            "win_rate": float(rec_runes.get("win_rate", 0.0) or 0.0),
            "primary_style": int(rec_runes.get("primary_style", 0) or 0),
            "sub_style": int(rec_runes.get("sub_style", 0) or 0),
            "perk_ids": [int(x) for x in (rec_runes.get("active_perks") or []) if str(x).isdigit()],
            "shard_ids": [int(x) for x in (rec_shards.get("active_shards") or []) if str(x).isdigit()],
            "starting_item_ids": [int(x) for x in (rec_start.get("ids") or []) if str(x).isdigit()],
            "starting_item_matches": int(rec_start.get("matches", 0) or 0),
            "starting_item_win_rate": float(rec_start.get("win_rate", 0.0) or 0.0),
            "core_item_ids": [int(x) for x in (rec_core.get("ids") or []) if str(x).isdigit()],
            "core_item_matches": int(rec_core.get("matches", 0) or 0),
            "core_item_win_rate": float(rec_core.get("win_rate", 0.0) or 0.0),
            "skill_priority": [str(x) for x in (rec_skills.get("slots") or [])],
            "skill_path": [str(x) for x in (rec_skill_path.get("slots") or [])],
            "skill_matches": int(rec_skill_path.get("matches", 0) or 0),
            "skill_win_rate": float(rec_skill_path.get("win_rate", 0.0) or 0.0),
            "item_stage_options": item_stage_options,
        }
        self.build_ready.emit(out)


class InClientGamePanel(AccountListBackgroundFrame):
    """Inline panel shown in place of the account list during champ select / in-game."""

    _PORTRAIT_SIZE = 100
    _ICON_SIZE = 32          # rune style path icons
    _ACTIVE_PERK_SIZE = 36   # selected perk icons in the active row
    _PERK_TREE_SIZE = 36     # perk icons inside the rune tree grid
    _ITEM_ICON_SIZE = 36     # item chips (starting/core/stage)
    _DDRAGON_VERSION = "16.10.1"

    # Rune style ID → (name, icon-filename-base)
    _RUNE_STYLES = {
        8000: ("Precision",   "Precision"),
        8100: ("Domination",  "Domination"),
        8200: ("Sorcery",     "Sorcery"),
        8300: ("Inspiration", "Whimsy"),
        8400: ("Resolve",     "Resolve"),
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("accountListContainer")

        self._my_champion_name = ""
        self._enemy_champion_name = ""
        self._image_threads: list[_ImageFetchThread] = []
        self._portrait_cache: dict[str, QPixmap] = {}
        self._rune_icon_cache: dict[int, QPixmap] = {}
        self._item_icon_cache: dict[int, QPixmap] = {}
        self._perk_icon_cache: dict[int, QPixmap] = {}
        self._rune_icon_path_by_id: dict[int, str] = {}
        self._rune_style_data_by_id: dict[int, dict] = {}
        self._pending_perk_targets: dict[int, list[QLabel]] = {}

        self._build_fetch_thread: Optional[_UggBuildFetchThread] = None
        self._build_cache: dict[str, dict] = {}
        self._pending_build_key = ""
        self._auto_role_hint = ""
        self._manual_role_hint = ""
        self._last_build_url = ""
        self._last_skill_priority: list[str] = []
        self._last_skill_path: list[str] = []
        self._last_skill_wr: float = 0.0
        self._last_skill_matches: int = 0

        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 16, 20, 16)
        outer.setSpacing(10)

        # ── Phase / Queue header ──────────────────────────────────────────
        header_row = QHBoxLayout()
        header_row.setSpacing(8)
        self._phase_label = QLabel("Champ Select")
        hdr_font = QFont()
        hdr_font.setPointSize(11)
        hdr_font.setBold(True)
        self._phase_label.setFont(hdr_font)
        self._phase_label.setStyleSheet("color: #89b4fa;")
        header_row.addWidget(self._phase_label)

        self._queue_label = QLabel()
        self._queue_label.setStyleSheet("color: #a6adc8; font-size: 9pt;")
        header_row.addWidget(self._queue_label)
        header_row.addStretch()

        self._elo_label = QLabel()
        self._elo_label.setStyleSheet("color: #a6e3a1; font-size: 9pt;")
        header_row.addWidget(self._elo_label)
        outer.addLayout(header_row)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("background: #313244; max-height: 1px; border: none;")
        outer.addWidget(sep)

        content_row = QHBoxLayout()
        content_row.setSpacing(12)

        # Left card: selector + runes/build (one visible at a time)
        left_card = QFrame()
        left_card.setObjectName("gameLeftCard")
        left_card.setStyleSheet(
            "QFrame#gameLeftCard {"
            "background: rgba(20, 24, 36, 0.78);"
            "border: 1px solid #2f3548;"
            "border-radius: 10px;"
            "}"
        )
        left_layout = QVBoxLayout(left_card)
        left_layout.setContentsMargins(12, 10, 12, 10)
        left_layout.setSpacing(8)

        selector_row = QHBoxLayout()
        selector_row.setSpacing(6)
        self._show_runes_btn = QPushButton("Runes")
        self._show_runes_btn.setCheckable(True)
        self._show_build_btn = QPushButton("Build")
        self._show_build_btn.setCheckable(True)
        selector_btn_style = (
            "QPushButton {"
            "background: #1e2333;"
            "color: #a6adc8;"
            "border: 1px solid #343b53;"
            "border-radius: 6px;"
            "padding: 4px 10px;"
            "font-size: 9pt;"
            "}"
            "QPushButton:checked {"
            "background: #2f5fd0;"
            "color: #f5f7ff;"
            "border: 1px solid #5787ff;"
            "}"
        )
        self._show_runes_btn.setStyleSheet(selector_btn_style)
        self._show_build_btn.setStyleSheet(selector_btn_style)
        self._show_runes_btn.clicked.connect(lambda: self._set_left_view(0))
        self._show_build_btn.clicked.connect(lambda: self._set_left_view(1))
        selector_row.addWidget(self._show_runes_btn)
        selector_row.addWidget(self._show_build_btn)

        self._role_tab_buttons: dict[str, QPushButton] = {}
        role_btn_style = (
            "QPushButton {"
            "background: #151b2a;"
            "color: #8ea2d0;"
            "border: 1px solid #2c344b;"
            "border-radius: 5px;"
            "padding: 2px 8px;"
            "font-size: 8pt;"
            "font-weight: bold;"
            "}"
            "QPushButton:checked {"
            "background: #2f5fd0;"
            "color: #f5f7ff;"
            "border: 1px solid #6a90ff;"
            "}"
        )
        for role_key, role_label in (("top", "TOP"), ("jungle", "JG"), ("mid", "MID"), ("adc", "ADC"), ("support", "SUP")):
            role_btn = QPushButton(role_label)
            role_btn.setCheckable(True)
            role_btn.setStyleSheet(role_btn_style)
            role_btn.setToolTip(f"Show {role_label} rune/build recommendation")
            role_btn.clicked.connect(lambda _checked=False, role=role_key: self._set_manual_role(role))
            self._role_tab_buttons[role_key] = role_btn
            selector_row.addWidget(role_btn)
        selector_row.addStretch()
        left_layout.addLayout(selector_row)

        self._left_stack = QStackedWidget()

        # Runes page
        runes_page = QWidget()
        runes_layout = QVBoxLayout(runes_page)
        runes_layout.setContentsMargins(0, 0, 0, 0)
        runes_layout.setSpacing(8)

        rune_header = QHBoxLayout()
        rune_title = QLabel("Top Runes")
        rune_title.setStyleSheet("color: #cdd6f4; font-size: 9pt; font-weight: bold;")
        rune_header.addWidget(rune_title)
        rune_header.addStretch()
        runes_layout.addLayout(rune_header)

        self._rune_paths_row = QHBoxLayout()
        self._rune_paths_row.setSpacing(10)
        self._rune_path_labels: dict[int, QLabel] = {}
        for style_id, (name, _) in self._RUNE_STYLES.items():
            col = QVBoxLayout()
            col.setSpacing(3)
            col.setAlignment(Qt.AlignHCenter)
            icon_lbl = QLabel()
            icon_lbl.setFixedSize(self._ICON_SIZE, self._ICON_SIZE)
            icon_lbl.setScaledContents(True)
            icon_lbl.setAlignment(Qt.AlignCenter)
            icon_lbl.setStyleSheet("border-radius: 5px; background: #1e1e2e; opacity: 0.4;")
            icon_lbl.setToolTip(name)
            col.addWidget(icon_lbl, 0, Qt.AlignHCenter)
            name_lbl = QLabel(name[:4])
            name_lbl.setAlignment(Qt.AlignCenter)
            name_lbl.setStyleSheet("color: #7f8aa3; font-size: 7pt;")
            col.addWidget(name_lbl, 0, Qt.AlignHCenter)
            self._rune_path_labels[style_id] = icon_lbl
            self._rune_paths_row.addLayout(col)
        self._rune_paths_row.addStretch()
        runes_layout.addLayout(self._rune_paths_row)

        self._rune_meta_label = QLabel("Build data pending...")
        self._rune_meta_label.setStyleSheet("color: #a6adc8; font-size: 8pt;")
        runes_layout.addWidget(self._rune_meta_label)

        self._active_perk_row = QHBoxLayout()
        self._active_perk_row.setSpacing(8)
        self._active_perk_labels: list[QLabel] = []
        for _ in range(6):
            lbl = QLabel()
            lbl.setFixedSize(self._ACTIVE_PERK_SIZE, self._ACTIVE_PERK_SIZE)
            lbl.setScaledContents(True)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("border-radius: 6px; background: #1e1e2e;")
            self._active_perk_labels.append(lbl)
            self._active_perk_row.addWidget(lbl)
        self._active_perk_row.addStretch()
        runes_layout.addLayout(self._active_perk_row)

        self._rune_tree_label = QLabel()
        self._rune_tree_label.setWordWrap(True)
        self._rune_tree_label.setStyleSheet("color: #94a0be; font-size: 8pt;")
        runes_layout.addWidget(self._rune_tree_label)

        # Side-by-side primary + secondary trees (matches in-client layout)
        self._rune_slots_stack = QHBoxLayout()
        self._rune_slots_stack.setSpacing(8)

        self._primary_slots_col = QVBoxLayout()
        self._primary_slots_col.setSpacing(6)
        self._primary_slots_title = QLabel("Primary Tree")
        self._primary_slots_title.setStyleSheet(
            "color: #cdd6f4; font-size: 8pt; font-weight: bold;"
            "background: #1e2030; border-radius: 4px; padding: 2px 6px;"
        )
        self._primary_slots_col.addWidget(self._primary_slots_title)
        self._primary_slots_body = QVBoxLayout()
        self._primary_slots_body.setSpacing(8)
        self._primary_slots_col.addLayout(self._primary_slots_body)
        self._primary_slots_col.addStretch()

        self._secondary_slots_col = QVBoxLayout()
        self._secondary_slots_col.setSpacing(6)
        self._secondary_slots_title = QLabel("Secondary Tree")
        self._secondary_slots_title.setStyleSheet(
            "color: #cdd6f4; font-size: 8pt; font-weight: bold;"
            "background: #1e2030; border-radius: 4px; padding: 2px 6px;"
        )
        self._secondary_slots_col.addWidget(self._secondary_slots_title)
        self._secondary_slots_body = QVBoxLayout()
        self._secondary_slots_body.setSpacing(8)
        self._secondary_slots_col.addLayout(self._secondary_slots_body)
        self._secondary_slots_col.addStretch()

        self._rune_slots_stack.addLayout(self._primary_slots_col, 1)
        self._rune_slots_stack.addLayout(self._secondary_slots_col, 1)
        runes_layout.addLayout(self._rune_slots_stack)

        self._shard_row = QHBoxLayout()
        self._shard_row.setSpacing(8)
        self._shard_labels: list[QLabel] = []
        for _ in range(3):
            lbl = QLabel("—")
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setFixedSize(28, 28)
            lbl.setStyleSheet("color: #a6adc8; border-radius: 5px; background: #1e1e2e; font-size: 8pt;")
            self._shard_labels.append(lbl)
            self._shard_row.addWidget(lbl)
        self._shard_row.addStretch()
        runes_layout.addLayout(self._shard_row)

        # Build page
        build_page = QWidget()
        build_layout = QVBoxLayout(build_page)
        build_layout.setContentsMargins(0, 0, 0, 0)
        build_layout.setSpacing(10)

        item_title = QLabel("Top Build")
        item_title.setStyleSheet("color: #f5f7ff; font-size: 10pt; font-weight: bold;")
        build_layout.addWidget(item_title)

        start_label = QLabel("Starting Items")
        start_label.setStyleSheet("color: #a6adc8; font-size: 8pt; letter-spacing: 0.5px;")
        build_layout.addWidget(start_label)
        self._starting_items_row = QHBoxLayout()
        self._starting_items_row.setSpacing(6)
        self._starting_item_labels: list[QLabel] = []
        for _ in range(4):
            lbl = QLabel()
            lbl.setFixedSize(self._ITEM_ICON_SIZE, self._ITEM_ICON_SIZE)
            lbl.setScaledContents(True)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("border-radius: 6px; background: #171b29; border: 1px solid #36415f;")
            self._starting_item_labels.append(lbl)
            self._starting_items_row.addWidget(lbl)
        self._starting_items_row.addStretch()
        build_layout.addLayout(self._starting_items_row)

        self._starting_items_meta = QLabel("—")
        self._starting_items_meta.setStyleSheet("color: #8ea2d0; font-size: 8pt;")
        build_layout.addWidget(self._starting_items_meta)

        core_label = QLabel("Core Items")
        core_label.setStyleSheet("color: #a6adc8; font-size: 8pt; letter-spacing: 0.5px;")
        build_layout.addWidget(core_label)
        self._core_items_row = QHBoxLayout()
        self._core_items_row.setSpacing(4)
        self._core_item_labels: list[QLabel] = []
        for _ in range(4):
            lbl = QLabel()
            lbl.setFixedSize(self._ITEM_ICON_SIZE + 4, self._ITEM_ICON_SIZE + 4)
            lbl.setScaledContents(True)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("border-radius: 7px; background: #171b29; border: 1px solid #4a5f93;")
            self._core_item_labels.append(lbl)
            self._core_items_row.addWidget(lbl)
            if _ < 2:
                arr = QLabel("→")
                arr.setStyleSheet("color: #7fa0ff; font-size: 11pt; font-weight: bold; padding: 0 2px;")
                arr.setAlignment(Qt.AlignCenter)
                self._core_items_row.addWidget(arr)
        self._core_items_row.addStretch()
        build_layout.addLayout(self._core_items_row)

        self._core_items_meta = QLabel("—")
        self._core_items_meta.setStyleSheet("color: #8ea2d0; font-size: 8pt;")
        build_layout.addWidget(self._core_items_meta)

        self._stage_option_icon_labels: dict[int, list[QLabel]] = {}
        self._stage_option_value_labels: dict[int, list[QLabel]] = {}
        for stage_num, stage_title in ((1, "4th Item Options"), (2, "5th Item Options"), (3, "6th Item Options")):
            title_lbl = QLabel(stage_title)
            title_lbl.setStyleSheet("color: #a6adc8; font-size: 8pt; letter-spacing: 0.5px;")
            build_layout.addWidget(title_lbl)

            icon_row = QHBoxLayout()
            icon_row.setSpacing(6)
            icon_labels: list[QLabel] = []
            for _ in range(3):
                il = QLabel()
                il.setFixedSize(self._ITEM_ICON_SIZE, self._ITEM_ICON_SIZE)
                il.setScaledContents(True)
                il.setAlignment(Qt.AlignCenter)
                il.setStyleSheet("border-radius: 6px; background: #171b29; border: 1px solid #36415f;")
                icon_labels.append(il)
                icon_row.addWidget(il)
            icon_row.addStretch()
            build_layout.addLayout(icon_row)
            self._stage_option_icon_labels[stage_num] = icon_labels

            value_row = QHBoxLayout()
            value_row.setSpacing(6)
            value_labels: list[QLabel] = []
            for _ in range(3):
                vl = QLabel("—")
                vl.setAlignment(Qt.AlignCenter)
                vl.setFixedWidth(self._ITEM_ICON_SIZE)
                vl.setStyleSheet("color: #8ea2d0; font-size: 7pt;")
                value_labels.append(vl)
                value_row.addWidget(vl)
            value_row.addStretch()
            build_layout.addLayout(value_row)
            self._stage_option_value_labels[stage_num] = value_labels

        self._left_stack.addWidget(runes_page)
        self._left_stack.addWidget(build_page)
        left_layout.addWidget(self._left_stack)

        # Right card: matchup
        right_card = QFrame()
        right_card.setObjectName("gameRightCard")
        right_card.setStyleSheet(
            "QFrame#gameRightCard {"
            "background: rgba(20, 24, 36, 0.78);"
            "border: 1px solid #2f3548;"
            "border-radius: 10px;"
            "}"
        )
        right_layout = QVBoxLayout(right_card)
        right_layout.setContentsMargins(12, 10, 12, 10)
        right_layout.setSpacing(8)

        matchup_title = QLabel("Champion Matchup")
        matchup_title.setStyleSheet("color: #cdd6f4; font-size: 9pt; font-weight: bold;")

        matchup_row = QHBoxLayout()
        matchup_row.setSpacing(4)

        you_col = QVBoxLayout()
        you_col.setAlignment(Qt.AlignHCenter)
        you_role_lbl = QLabel("YOU")
        you_role_lbl.setAlignment(Qt.AlignCenter)
        you_role_lbl.setStyleSheet("color: #6c7086; font-size: 7pt; letter-spacing: 1px;")
        you_col.addWidget(you_role_lbl)
        self._my_portrait = QLabel()
        self._my_portrait.setFixedSize(self._PORTRAIT_SIZE, self._PORTRAIT_SIZE)
        self._my_portrait.setAlignment(Qt.AlignCenter)
        self._my_portrait.setStyleSheet(
            "border-radius: 50px; background: #313244; border: 2px solid #89b4fa;"
        )
        you_col.addWidget(self._my_portrait, 0, Qt.AlignHCenter)
        champ_font = QFont()
        champ_font.setPointSize(10)
        champ_font.setBold(True)
        self._my_champ_label = QLabel("—")
        self._my_champ_label.setFont(champ_font)
        self._my_champ_label.setAlignment(Qt.AlignCenter)
        self._my_champ_label.setStyleSheet("color: #cdd6f4;")
        you_col.addWidget(self._my_champ_label)
        matchup_row.addLayout(you_col, 1)

        vs_label = QLabel("VS")
        vs_label.setAlignment(Qt.AlignCenter)
        vs_label.setStyleSheet(
            "color: #f38ba8; font-size: 11pt; font-weight: bold; padding: 0 8px;"
        )
        matchup_row.addWidget(vs_label)

        enemy_col = QVBoxLayout()
        enemy_col.setSpacing(4)
        enemy_col.setAlignment(Qt.AlignHCenter)
        enemy_role_lbl = QLabel("ENEMY")
        enemy_role_lbl.setAlignment(Qt.AlignCenter)
        enemy_role_lbl.setStyleSheet("color: #6c7086; font-size: 7pt; letter-spacing: 1px;")
        enemy_col.addWidget(enemy_role_lbl)
        self._enemy_portrait = QLabel()
        self._enemy_portrait.setFixedSize(self._PORTRAIT_SIZE, self._PORTRAIT_SIZE)
        self._enemy_portrait.setAlignment(Qt.AlignCenter)
        self._enemy_portrait.setStyleSheet(
            "border-radius: 50px; background: #313244; border: 2px solid #f38ba8;"
        )
        enemy_col.addWidget(self._enemy_portrait, 0, Qt.AlignHCenter)
        self._enemy_champ_label = QLabel("—")
        self._enemy_champ_label.setFont(champ_font)
        self._enemy_champ_label.setAlignment(Qt.AlignCenter)
        self._enemy_champ_label.setStyleSheet("color: #cdd6f4;")
        enemy_col.addWidget(self._enemy_champ_label)
        matchup_row.addLayout(enemy_col, 1)

        right_layout.addStretch(1)
        right_layout.addWidget(matchup_title)
        right_layout.addLayout(matchup_row)
        right_layout.addStretch(1)

        content_row.addWidget(left_card, 3)
        content_row.addWidget(right_card, 2)
        outer.addLayout(content_row, 3)

        # Bottom card: dedicated skill section
        skill_card = QFrame()
        skill_card.setObjectName("gameSkillCard")
        skill_card.setStyleSheet(
            "QFrame#gameSkillCard {"
            "background: rgba(20, 24, 36, 0.78);"
            "border: 1px solid #2f3548;"
            "border-radius: 10px;"
            "}"
        )
        skill_layout = QHBoxLayout(skill_card)
        skill_layout.setContentsMargins(12, 10, 12, 10)
        skill_layout.setSpacing(14)

        # Left: priority
        priority_col = QVBoxLayout()
        priority_col.setSpacing(6)
        priority_title = QLabel("Skill Priority")
        priority_title.setStyleSheet("color: #cdd6f4; font-size: 9pt; font-weight: bold;")
        priority_col.addWidget(priority_title)

        self._skill_priority_row = QHBoxLayout()
        self._skill_priority_row.setSpacing(6)
        priority_col.addLayout(self._skill_priority_row)

        self._skill_priority_meta = QLabel("—")
        self._skill_priority_meta.setStyleSheet("color: #94a0be; font-size: 8pt;")
        priority_col.addWidget(self._skill_priority_meta)
        priority_col.addStretch()

        # Right: path grid
        path_col = QVBoxLayout()
        path_col.setSpacing(6)
        path_header = QHBoxLayout()
        path_title = QLabel("Skill Path")
        path_title.setStyleSheet("color: #cdd6f4; font-size: 9pt; font-weight: bold;")
        path_subtitle = QLabel("Most popular ability leveling order")
        path_subtitle.setStyleSheet("color: #7f8aa3; font-size: 8pt;")
        path_header.addWidget(path_title)
        path_header.addWidget(path_subtitle)
        path_header.addStretch()
        path_col.addLayout(path_header)

        self._skill_path_grid = QGridLayout()
        self._skill_path_grid.setHorizontalSpacing(3)
        self._skill_path_grid.setVerticalSpacing(4)
        self._skill_path_grid_wrap = QWidget()
        self._skill_path_grid_wrap.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        skill_grid_wrap_layout = QVBoxLayout(self._skill_path_grid_wrap)
        skill_grid_wrap_layout.setContentsMargins(0, 0, 0, 0)
        skill_grid_wrap_layout.setSpacing(0)
        skill_grid_wrap_layout.addLayout(self._skill_path_grid)
        path_col.addWidget(self._skill_path_grid_wrap, 1)
        path_col.addStretch()

        self._skill_path_meta = QLabel("—")
        self._skill_path_meta.setStyleSheet("color: #94a0be; font-size: 8pt;")
        path_col.addWidget(self._skill_path_meta)

        skill_layout.addLayout(priority_col, 1)
        skill_layout.addLayout(path_col, 5)
        outer.addWidget(skill_card)  # natural height, no vertical stretch

        # ── Status hint ───────────────────────────────────────────────────
        self._status_label = QLabel("Waiting for champion selection…")
        self._status_label.setWordWrap(True)
        self._status_label.setAlignment(Qt.AlignCenter)
        self._status_label.setStyleSheet("color: #a6adc8; font-size: 9pt; padding: 2px 0;")
        outer.addWidget(self._status_label)

        self._set_left_view(0)

        self._load_runes_reforged_map()
        self._load_rune_path_icons()
        self._apply_empty_build_state("Waiting for u.gg data...")

    def _load_runes_reforged_map(self):
        """Load runeId -> icon path mapping from Data Dragon runesReforged.json."""
        url = (
            f"https://ddragon.leagueoflegends.com/cdn/{self._DDRAGON_VERSION}"
            "/data/en_US/runesReforged.json"
        )
        try:
            req = Request(url, headers={"User-Agent": "lol-account-manager/1.0"})
            with urlopen(req, timeout=6) as resp:
                raw = resp.read().decode("utf-8", errors="ignore")
            data = json.loads(raw)
            icon_map: dict[int, str] = {}
            style_map: dict[int, dict] = {}
            for style in data:
                if not isinstance(style, dict):
                    continue
                try:
                    sid = int(style.get("id", 0) or 0)
                except (TypeError, ValueError):
                    sid = 0
                if sid > 0:
                    style_map[sid] = style
                for slot in style.get("slots", []) or []:
                    if not isinstance(slot, dict):
                        continue
                    for rune in slot.get("runes", []) or []:
                        if not isinstance(rune, dict):
                            continue
                        try:
                            rid = int(rune.get("id", 0) or 0)
                        except (TypeError, ValueError):
                            rid = 0
                        icon = str(rune.get("icon", "") or "").strip()
                        if rid > 0 and icon:
                            icon_map[rid] = icon
            self._rune_icon_path_by_id = icon_map
            self._rune_style_data_by_id = style_map
        except Exception:
            self._rune_icon_path_by_id = {}
            self._rune_style_data_by_id = {}

    def _load_rune_path_icons(self):
        """Start background threads to fetch rune path icons from DDragon."""
        for style_id, (name, _) in self._RUNE_STYLES.items():
            if style_id in self._rune_icon_cache:
                continue
            # Prefer the icon path embedded in the DDragon runesReforged data
            style_data = self._rune_style_data_by_id.get(style_id, {})
            icon_path = str(style_data.get("icon", "") or "").strip()
            if icon_path:
                url = f"https://ddragon.leagueoflegends.com/cdn/img/{icon_path}"
            else:
                # Fallback: Community Dragon style icon
                url = (
                    f"https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data"
                    f"/global/default/v1/perk-images/styles/"
                    f"{style_id}_{name.lower()}.png"
                )
            t = _ImageFetchThread(f"rune_style_{style_id}", url, self)
            t.image_ready.connect(self._on_image_ready)
            t.finished.connect(lambda thread=t: self._cleanup_thread(thread))
            self._image_threads.append(t)
            t.start()

    def _cleanup_thread(self, thread: "_ImageFetchThread"):
        try:
            self._image_threads.remove(thread)
        except ValueError:
            pass

    def _on_image_ready(self, tag: str, raw: bytes):
        if not raw:
            return
        pix = QPixmap()
        if not pix.loadFromData(raw):
            return

        if tag.startswith("rune_style_"):
            style_id = int(tag[len("rune_style_"):])
            sized = pix.scaled(self._ICON_SIZE, self._ICON_SIZE, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self._rune_icon_cache[style_id] = sized
            lbl = self._rune_path_labels.get(style_id)
            if lbl:
                lbl.setPixmap(sized)
                lbl.setStyleSheet("border-radius: 4px; background: #1e1e2e;")
        elif tag.startswith("rune_perk_generic_"):
            # NOTE: must be checked BEFORE the plain rune_perk_ branch
            try:
                perk_id = int(tag[len("rune_perk_generic_"):])
            except ValueError:
                return
            sized = pix.scaled(self._PERK_TREE_SIZE, self._PERK_TREE_SIZE, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self._perk_icon_cache[perk_id] = sized
            targets = self._pending_perk_targets.pop(perk_id, [])
            for lbl in targets:
                lbl.setPixmap(sized)
        elif tag.startswith("rune_perk_"):
            parts = tag.split("_")
            if len(parts) >= 4:
                try:
                    perk_id = int(parts[2])
                    slot_idx = int(parts[3])
                except ValueError:
                    return
                sized = pix.scaled(self._ACTIVE_PERK_SIZE, self._ACTIVE_PERK_SIZE, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self._perk_icon_cache[perk_id] = sized
                if 0 <= slot_idx < len(self._active_perk_labels):
                    self._active_perk_labels[slot_idx].setPixmap(sized)
        elif tag.startswith("item_icon_"):
            parts = tag.split("_")
            if len(parts) >= 5:
                try:
                    item_id = int(parts[2])
                    row = parts[3]
                    slot_idx = int(parts[4])
                except ValueError:
                    return
                sized = pix.scaled(self._ITEM_ICON_SIZE, self._ITEM_ICON_SIZE, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self._item_icon_cache[item_id] = sized
                labels = self._starting_item_labels if row == "start" else self._core_item_labels
                if 0 <= slot_idx < len(labels):
                    labels[slot_idx].setPixmap(sized)
        elif tag.startswith("item_stage_"):
            parts = tag.split("_")
            if len(parts) >= 5:
                try:
                    item_id = int(parts[2])
                    stage_num = int(parts[3])
                    slot_idx = int(parts[4])
                except ValueError:
                    return
                sized = pix.scaled(self._ITEM_ICON_SIZE, self._ITEM_ICON_SIZE, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self._item_icon_cache[item_id] = sized
                labels = self._stage_option_icon_labels.get(stage_num, [])
                if 0 <= slot_idx < len(labels):
                    labels[slot_idx].setPixmap(sized)
        elif tag.startswith("portrait_"):
            champ_key = tag[len("portrait_"):]
            circular = self._make_circular(pix, self._PORTRAIT_SIZE)
            self._portrait_cache[champ_key] = circular
            if champ_key == self._my_champion_name.lower():
                self._my_portrait.setPixmap(circular)
            if champ_key == self._enemy_champion_name.lower():
                self._enemy_portrait.setPixmap(circular)

    @staticmethod
    def _make_circular(pix: "QPixmap", size: int) -> "QPixmap":
        """Crop and mask a pixmap into a circle of the given size."""
        scaled = pix.scaled(size, size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        # Center-crop to exact size
        if scaled.width() > size or scaled.height() > size:
            x = (scaled.width() - size) // 2
            y = (scaled.height() - size) // 2
            scaled = scaled.copy(x, y, size, size)

        result = QPixmap(size, size)
        result.fill(Qt.transparent)
        painter = QPainter(result)
        painter.setRenderHint(QPainter.Antialiasing, True)
        path = QPainterPath()
        path.addEllipse(0, 0, size, size)
        painter.setClipPath(path)
        painter.drawPixmap(0, 0, scaled)
        painter.end()
        return result

    def _load_portrait(self, champion_name: str):
        """Kick off a background fetch for a champion's square portrait."""
        if not champion_name:
            return
        key = champion_name.lower()
        if key in self._portrait_cache:
            pix = self._portrait_cache[key]
            if key == self._my_champion_name.lower() and pix and not pix.isNull():
                self._my_portrait.setPixmap(pix)
            if key == self._enemy_champion_name.lower() and pix and not pix.isNull():
                self._enemy_portrait.setPixmap(pix)
            return
        # Capitalize first letter only (DDragon uses canonical champion name)
        name_canonical = champion_name.strip()
        url = (
            f"https://ddragon.leagueoflegends.com/cdn/{self._DDRAGON_VERSION}"
            f"/img/champion/{name_canonical}.png"
        )
        tag = f"portrait_{key}"
        t = _ImageFetchThread(tag, url, self)
        t.image_ready.connect(self._on_image_ready)
        t.finished.connect(lambda thread=t: self._cleanup_thread(thread))
        self._image_threads.append(t)
        t.start()

    def _fetch_build_data(self, page_url: str, role_hint: str = ""):
        key = f"{page_url}|{role_hint}"
        self._pending_build_key = key
        cached = self._build_cache.get(key)
        if cached:
            self._apply_build_data(cached)
            return

        if self._build_fetch_thread and self._build_fetch_thread.isRunning():
            self._build_fetch_thread.terminate()
            self._build_fetch_thread.wait(500)

        self._apply_empty_build_state("Loading build data from u.gg...")
        self._build_fetch_thread = _UggBuildFetchThread(page_url, role_hint, self)
        self._build_fetch_thread.build_ready.connect(
            lambda data, expected=key: self._on_build_data_ready(expected, data)
        )
        self._build_fetch_thread.start()

    def _set_left_view(self, index: int):
        idx = 0 if index not in (0, 1) else index
        self._left_stack.setCurrentIndex(idx)
        self._show_runes_btn.setChecked(idx == 0)
        self._show_build_btn.setChecked(idx == 1)

    @staticmethod
    def _normalize_role_hint(raw_role: str) -> str:
        role = str(raw_role or "").strip().casefold()
        aliases = {
            "top": "top",
            "jungle": "jungle",
            "jg": "jungle",
            "mid": "mid",
            "middle": "mid",
            "adc": "adc",
            "bot": "adc",
            "bottom": "adc",
            "support": "support",
            "supp": "support",
            "sup": "support",
            "utility": "support",
        }
        return aliases.get(role, "")

    def _effective_role_hint(self) -> str:
        return self._manual_role_hint or self._auto_role_hint

    def _sync_role_tab_state(self):
        active_role = self._effective_role_hint()
        for role_key, btn in self._role_tab_buttons.items():
            btn.setChecked(role_key == active_role)

    def _set_manual_role(self, role_key: str):
        normalized = self._normalize_role_hint(role_key)
        if not normalized:
            return
        self._manual_role_hint = normalized
        self._sync_role_tab_state()
        if self._my_champion_name and self._last_build_url:
            self._fetch_build_data(self._last_build_url, self._effective_role_hint())

    @staticmethod
    def _clear_layout(layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            child_layout = item.layout()
            if widget is not None:
                widget.deleteLater()
            elif child_layout is not None:
                InClientGamePanel._clear_layout(child_layout)

    def _set_perk_icon(self, label: QLabel, perk_id: int):
        cached = self._perk_icon_cache.get(perk_id)
        if cached and not cached.isNull():
            label.setPixmap(cached)
            return
        pending = self._pending_perk_targets.setdefault(perk_id, [])
        pending.append(label)
        if len(pending) > 1:
            return
        icon_path = self._rune_icon_path_by_id.get(perk_id, "")
        if not icon_path:
            return
        icon_url = f"https://ddragon.leagueoflegends.com/cdn/img/{icon_path}"
        tag = f"rune_perk_generic_{perk_id}"
        t = _ImageFetchThread(tag, icon_url, self)
        t.image_ready.connect(self._on_image_ready)
        t.finished.connect(lambda thread=t: self._cleanup_thread(thread))
        self._image_threads.append(t)
        t.start()

    def _render_skill_section(self, skill_priority: list[str], skill_path: list[str], skill_wr: float = 0.0, skill_matches: int = 0):
        self._last_skill_priority = [str(s).upper().strip() for s in (skill_priority or []) if str(s).strip()]
        self._last_skill_path = [str(s).upper().strip() for s in (skill_path or []) if str(s).strip()]
        self._last_skill_wr = float(skill_wr or 0.0)
        self._last_skill_matches = int(skill_matches or 0)

        self._clear_layout(self._skill_priority_row)
        self._clear_layout(self._skill_path_grid)

        color_by_skill = {
            "Q": "#4fb4ff",
            "W": "#ff9f43",
            "E": "#f5cd5a",
            "R": "#d16cff",
        }

        if skill_priority:
            for idx, skill in enumerate(skill_priority[:3]):
                s = str(skill).upper().strip()
                bubble = QLabel(s or "—")
                bubble.setAlignment(Qt.AlignCenter)
                bubble.setFixedSize(32, 32)
                color = color_by_skill.get(s, "#5b6078")
                bubble.setStyleSheet(
                    f"border-radius: 16px; background: #1e1e2e; border: 2px solid {color}; color: {color}; font-weight: bold; font-size: 10pt;"
                )
                self._skill_priority_row.addWidget(bubble)
                if idx < min(2, len(skill_priority) - 1):
                    arrow = QLabel("→")
                    arrow.setStyleSheet("color: #a6adc8; font-size: 11pt;")
                    self._skill_priority_row.addWidget(arrow)
            self._skill_priority_meta.setText(f"{skill_wr:.2f}% WR · {skill_matches:,} matches")
        else:
            empty = QLabel("—")
            empty.setStyleSheet("color: #7f8aa3; font-size: 9pt;")
            self._skill_priority_row.addWidget(empty)
            self._skill_priority_meta.setText("—")
        self._skill_priority_row.addStretch()

        # Grid headers
        row_skills = ["Q", "W", "E", "R"]
        self._skill_path_grid.setColumnStretch(0, 0)  # row label col fixed

        available_width = self._skill_path_grid_wrap.width() if hasattr(self, "_skill_path_grid_wrap") else 0
        if available_width <= 0:
            available_width = 620
        spacing = max(0, self._skill_path_grid.horizontalSpacing())
        usable = max(520, available_width - 8)
        cell_w = int((usable - 24 - (18 * spacing)) / 18)
        cell_w = max(24, min(34, cell_w))
        cell_h = 26 if cell_w <= 26 else 28
        row_label_w = 24 if cell_w <= 26 else 26
        header_h = 18
        font_size = 7 if cell_w <= 26 else 8

        for col in range(1, 19):
            header = QLabel(str(col))
            header.setAlignment(Qt.AlignCenter)
            header.setFixedSize(cell_w, header_h)
            header.setStyleSheet("color: #7f8aa3; font-size: 7pt;")
            self._skill_path_grid.addWidget(header, 0, col)
            self._skill_path_grid.setColumnStretch(col, 0)

        for row_idx, skill in enumerate(row_skills, start=1):
            row_lbl = QLabel(skill)
            row_lbl.setAlignment(Qt.AlignCenter)
            row_lbl.setFixedSize(row_label_w, cell_h)
            row_lbl.setStyleSheet(
                f"border-radius: 4px; background: #1e1e2e; color: {color_by_skill.get(skill, '#cdd6f4')}; font-weight: bold;"
            )
            self._skill_path_grid.addWidget(row_lbl, row_idx, 0)

            for lv in range(1, 19):
                cell = QLabel("")
                cell.setAlignment(Qt.AlignCenter)
                cell.setFixedSize(cell_w, cell_h)
                cell.setStyleSheet(f"border-radius: 4px; background: #20263a; color: #f5f7ff; font-size: {font_size}pt;")

                if lv <= len(skill_path):
                    picked = str(skill_path[lv - 1]).upper().strip()
                    if picked == skill:
                        color = color_by_skill.get(skill, "#4fb4ff")
                        cell.setText(str(lv))
                        cell.setStyleSheet(
                            f"border-radius: 4px; background: {color}; color: #0b1020; font-size: {font_size}pt; font-weight: bold;"
                        )
                self._skill_path_grid.addWidget(cell, row_idx, lv)

        if skill_path:
            compact = "  ".join(f"{i + 1}:{str(s).upper()}" for i, s in enumerate(skill_path[:18]))
            self._skill_path_meta.setText(compact)
        else:
            self._skill_path_meta.setText("—")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._last_skill_priority or self._last_skill_path:
            self._render_skill_section(
                self._last_skill_priority,
                self._last_skill_path,
                self._last_skill_wr,
                self._last_skill_matches,
            )

    def changeEvent(self, event):
        """Re-render the skill grid when the window is moved to a monitor with
        a different DPI (QEvent.ScreenChangeInternal).  With per-monitor DPI
        scaling enabled the widget's logical width changes, so the adaptive
        cell sizes must be recomputed."""
        super().changeEvent(event)
        screen_change_type = getattr(QEvent, "ScreenChangeInternal", None)
        if screen_change_type is not None and event.type() == screen_change_type:
            if self._last_skill_priority or self._last_skill_path:
                QTimer.singleShot(
                    80,
                    lambda: self._render_skill_section(
                        self._last_skill_priority,
                        self._last_skill_path,
                        self._last_skill_wr,
                        self._last_skill_matches,
                    ),
                )

    def _render_rune_style_slots(self, style_id: int, container_layout, active_ids: set[int], max_slots: int, skip_keystone: bool = False):
        self._clear_layout(container_layout)
        style = self._rune_style_data_by_id.get(style_id)
        if not isinstance(style, dict):
            empty = QLabel("No rune tree data")
            empty.setStyleSheet("color: #7f8aa3; font-size: 8pt;")
            container_layout.addWidget(empty)
            return

        slots = style.get("slots", []) if isinstance(style.get("slots", []), list) else []
        if skip_keystone and len(slots) > 1:
            slots = slots[1:]
        for slot_idx, slot in enumerate(slots[:max_slots]):
            if not isinstance(slot, dict):
                continue
            row = QHBoxLayout()
            row.setSpacing(6)
            runes = slot.get("runes", []) if isinstance(slot.get("runes", []), list) else []
            for rune in runes:
                if not isinstance(rune, dict):
                    continue
                try:
                    rid = int(rune.get("id", 0) or 0)
                except (TypeError, ValueError):
                    rid = 0
                if rid <= 0:
                    continue
                lbl = QLabel()
                lbl.setFixedSize(self._PERK_TREE_SIZE, self._PERK_TREE_SIZE)
                lbl.setScaledContents(True)
                lbl.setAlignment(Qt.AlignCenter)
                if rid in active_ids:
                    lbl.setStyleSheet(f"border-radius: {self._PERK_TREE_SIZE // 2}px; background: #1e1e2e; border: 2px solid #58a6ff;")
                else:
                    lbl.setStyleSheet(f"border-radius: {self._PERK_TREE_SIZE // 2}px; background: #1e1e2e; border: 1px solid #30374b; opacity: 0.7;")
                row.addWidget(lbl)
                self._set_perk_icon(lbl, rid)
            row.addStretch()
            container_layout.addLayout(row)

    def _on_build_data_ready(self, expected_key: str, data: dict):
        if expected_key != self._pending_build_key:
            return
        if not isinstance(data, dict) or not data.get("ok"):
            msg = str((data or {}).get("error", "No build data available") or "No build data available")
            self._apply_empty_build_state(msg)
            return
        self._build_cache[expected_key] = data
        self._apply_build_data(data)

    def _apply_empty_build_state(self, message: str):
        self._rune_meta_label.setText(message)
        for lbl in self._active_perk_labels:
            lbl.clear()
            lbl.setStyleSheet("border-radius: 4px; background: #1e1e2e;")
        self._rune_tree_label.setText("Primary/Secondary rune rows will appear after data loads.")
        self._primary_slots_title.setText("Primary Tree")
        self._secondary_slots_title.setText("Secondary Tree")
        self._clear_layout(self._primary_slots_body)
        self._clear_layout(self._secondary_slots_body)
        for lbl in self._shard_labels:
            lbl.setText("—")
            lbl.setStyleSheet("color: #a6adc8; border-radius: 4px; background: #1e1e2e;")
        for lbl in self._starting_item_labels + self._core_item_labels:
            lbl.clear()
            lbl.setStyleSheet("border-radius: 6px; background: #171b29; border: 1px solid #36415f;")
        self._starting_items_meta.setText("—")
        self._core_items_meta.setText("—")
        for style_id, lbl in self._rune_path_labels.items():
            lbl.setStyleSheet("border-radius: 4px; background: #1e1e2e; opacity: 0.4;")
        for stage_num, labels in self._stage_option_icon_labels.items():
            for lbl in labels:
                lbl.clear()
                lbl.setStyleSheet("border-radius: 6px; background: #171b29; border: 1px solid #36415f;")
            for vl in self._stage_option_value_labels.get(stage_num, []):
                vl.setText("—")
        self._render_skill_section([], [], 0.0, 0)

    def _apply_build_data(self, data: dict):
        role_name = str(data.get("role", "") or "").upper()
        matches = int(data.get("matches", 0) or 0)
        win_rate = float(data.get("win_rate", 0.0) or 0.0)
        self._rune_meta_label.setText(
            f"u.gg {role_name} · {win_rate:.2f}% WR · {matches:,} matches"
        )

        primary_style = int(data.get("primary_style", 0) or 0)
        sub_style = int(data.get("sub_style", 0) or 0)
        for style_id, lbl in self._rune_path_labels.items():
            base = self._rune_icon_cache.get(style_id)
            if base and not base.isNull():
                lbl.setPixmap(base)
            if style_id in (primary_style, sub_style):
                lbl.setStyleSheet("border-radius: 4px; background: #1e1e2e; border: 1px solid #89b4fa;")
            else:
                lbl.setStyleSheet("border-radius: 4px; background: #1e1e2e; opacity: 0.4;")

        perk_ids = list(data.get("perk_ids") or [])[:6]
        for idx, lbl in enumerate(self._active_perk_labels):
            lbl.clear()
            lbl.setStyleSheet("border-radius: 4px; background: #1e1e2e;")
            if idx >= len(perk_ids):
                continue
            perk_id = int(perk_ids[idx])
            cached = self._perk_icon_cache.get(perk_id)
            if cached and not cached.isNull():
                lbl.setPixmap(cached)
                continue
            icon_path = self._rune_icon_path_by_id.get(perk_id, "")
            if not icon_path:
                continue
            icon_url = f"https://ddragon.leagueoflegends.com/cdn/img/{icon_path}"
            tag = f"rune_perk_{perk_id}_{idx}"
            t = _ImageFetchThread(tag, icon_url, self)
            t.image_ready.connect(self._on_image_ready)
            t.finished.connect(lambda thread=t: self._cleanup_thread(thread))
            self._image_threads.append(t)
            t.start()

        # Detailed rune row summary (primary 4 + secondary 2)
        primary_ids = perk_ids[:4]
        secondary_ids = perk_ids[4:6]
        def _rune_name(rid: int) -> str:
            for style in self._rune_style_data_by_id.values():
                for slot in style.get("slots", []) or []:
                    for rune in slot.get("runes", []) or []:
                        try:
                            rrid = int(rune.get("id", 0) or 0)
                        except (TypeError, ValueError):
                            rrid = 0
                        if rrid == rid:
                            return str(rune.get("name", "") or str(rid))
            return str(rid)

        primary_text = " / ".join(_rune_name(int(x)) for x in primary_ids) if primary_ids else "—"
        secondary_text = " / ".join(_rune_name(int(x)) for x in secondary_ids) if secondary_ids else "—"
        self._rune_tree_label.setText(
            f"Primary: {primary_text}\nSecondary: {secondary_text}"
        )

        style_name = lambda sid: self._RUNE_STYLES.get(sid, (str(sid), ""))[0]
        self._primary_slots_title.setText(f"{style_name(primary_style)}")
        self._secondary_slots_title.setText(f"{style_name(sub_style)}")
        active_id_set = set(int(x) for x in perk_ids)
        self._render_rune_style_slots(primary_style, self._primary_slots_body, active_id_set, 4, skip_keystone=False)
        self._render_rune_style_slots(sub_style, self._secondary_slots_body, active_id_set, 3, skip_keystone=True)

        shard_ids = list(data.get("shard_ids") or [])[:3]
        shard_name_map = {
            5008: "AF",
            5005: "AS",
            5007: "AH",
            5001: "HP",
            5002: "AR",
            5003: "MR",
            5010: "MS",
            5011: "TEN",
        }
        for idx, lbl in enumerate(self._shard_labels):
            if idx < len(shard_ids):
                sid = int(shard_ids[idx])
                lbl.setText(shard_name_map.get(sid, str(sid)))
                lbl.setStyleSheet("color: #f5f7ff; border-radius: 4px; background: #2f5fd0;")
            else:
                lbl.setText("—")
                lbl.setStyleSheet("color: #a6adc8; border-radius: 4px; background: #1e1e2e;")

        start_ids = list(data.get("starting_item_ids") or [])[:len(self._starting_item_labels)]
        for idx, lbl in enumerate(self._starting_item_labels):
            lbl.clear()
            lbl.setStyleSheet("border-radius: 6px; background: #171b29; border: 1px solid #36415f;")
            if idx >= len(start_ids):
                continue
            item_id = int(start_ids[idx])
            cached = self._item_icon_cache.get(item_id)
            if cached and not cached.isNull():
                lbl.setPixmap(cached)
                continue
            icon_url = f"https://ddragon.leagueoflegends.com/cdn/{self._DDRAGON_VERSION}/img/item/{item_id}.png"
            tag = f"item_icon_{item_id}_start_{idx}"
            t = _ImageFetchThread(tag, icon_url, self)
            t.image_ready.connect(self._on_image_ready)
            t.finished.connect(lambda thread=t: self._cleanup_thread(thread))
            self._image_threads.append(t)
            t.start()

        start_wr = float(data.get("starting_item_win_rate", 0.0) or 0.0)
        start_matches = int(data.get("starting_item_matches", 0) or 0)
        if start_ids:
            self._starting_items_meta.setText(f"{start_wr:.2f}% WR · {start_matches:,} matches")
        else:
            self._starting_items_meta.setText("—")

        core_ids = list(data.get("core_item_ids") or [])[:len(self._core_item_labels)]
        for idx, lbl in enumerate(self._core_item_labels):
            lbl.clear()
            lbl.setStyleSheet("border-radius: 7px; background: #171b29; border: 1px solid #4a5f93;")
            if idx >= len(core_ids):
                continue
            item_id = int(core_ids[idx])
            cached = self._item_icon_cache.get(item_id)
            if cached and not cached.isNull():
                lbl.setPixmap(cached)
                continue
            icon_url = f"https://ddragon.leagueoflegends.com/cdn/{self._DDRAGON_VERSION}/img/item/{item_id}.png"
            tag = f"item_icon_{item_id}_core_{idx}"
            t = _ImageFetchThread(tag, icon_url, self)
            t.image_ready.connect(self._on_image_ready)
            t.finished.connect(lambda thread=t: self._cleanup_thread(thread))
            self._image_threads.append(t)
            t.start()

        core_wr = float(data.get("core_item_win_rate", 0.0) or 0.0)
        core_matches = int(data.get("core_item_matches", 0) or 0)
        if core_ids:
            self._core_items_meta.setText(f"{core_wr:.2f}% WR · {core_matches:,} matches")
        else:
            self._core_items_meta.setText("—")

        # Stage options (4th/5th/6th item)
        options_map = data.get("item_stage_options") if isinstance(data.get("item_stage_options"), dict) else {}
        for stage_num, labels in self._stage_option_icon_labels.items():
            opt_key = str(stage_num)
            options = options_map.get(opt_key) if isinstance(options_map.get(opt_key), list) else []
            value_labels = self._stage_option_value_labels.get(stage_num, [])
            for lbl in labels:
                lbl.clear()
                lbl.setStyleSheet("border-radius: 6px; background: #171b29; border: 1px solid #36415f;")
            for vl in value_labels:
                vl.setText("—")
            if not options:
                continue
            for idx, opt in enumerate(options[:3]):
                if not isinstance(opt, dict):
                    continue
                item_id = int(opt.get("id", 0) or 0)
                wr = float(opt.get("win_rate", 0.0) or 0.0)
                mm = int(opt.get("matches", 0) or 0)
                if idx < len(labels):
                    cached = self._item_icon_cache.get(item_id)
                    if cached and not cached.isNull():
                        labels[idx].setPixmap(cached)
                    else:
                        icon_url = f"https://ddragon.leagueoflegends.com/cdn/{self._DDRAGON_VERSION}/img/item/{item_id}.png"
                        tag = f"item_stage_{item_id}_{stage_num}_{idx}"
                        t = _ImageFetchThread(tag, icon_url, self)
                        t.image_ready.connect(self._on_image_ready)
                        t.finished.connect(lambda thread=t: self._cleanup_thread(thread))
                        self._image_threads.append(t)
                        t.start()
                if idx < len(value_labels):
                    value_labels[idx].setText(f"{wr:.1f}%\n{mm:,}")

        # Skill sections
        skill_priority = [str(s).upper() for s in (data.get("skill_priority") or []) if str(s).strip()]
        skill_path = [str(s).upper() for s in (data.get("skill_path") or []) if str(s).strip()]
        self._render_skill_section(
            skill_priority,
            skill_path,
            float(data.get("skill_win_rate", 0.0) or 0.0),
            int(data.get("skill_matches", 0) or 0),
        )

    def update_payload(self, payload: dict):
        in_game = bool(payload.get("in_game", False))
        my_champion = str(payload.get("my_champion", "") or "").strip()
        enemy_champion = str(payload.get("enemy_champion", "") or "").strip()
        queue_type = str(payload.get("queue_type", "") or "").strip()
        rank_label = str(payload.get("rank_label", "") or "").strip() or "Overall"
        role_hint = str(payload.get("role_hint", "") or "").strip()
        matchup_url = str(payload.get("matchup_url", "") or "").strip()
        fallback_url = str(payload.get("fallback_url", "") or "").strip()

        self._my_champion_name = my_champion
        self._enemy_champion_name = enemy_champion
        self._auto_role_hint = self._normalize_role_hint(role_hint)

        phase_text = "In Game" if in_game else "Champ Select"
        phase_color = "#fab387" if in_game else "#89b4fa"
        self._phase_label.setText(phase_text)
        self._phase_label.setStyleSheet(
            f"color: {phase_color}; font-size: 11pt; font-weight: bold;"
        )
        self._queue_label.setText(f"— {queue_type}" if queue_type else "")
        self._elo_label.setText(f"Elo: {rank_label}" if (rank_label and not in_game) else "")

        self._my_champ_label.setText(my_champion if my_champion else "—")
        self._enemy_champ_label.setText(enemy_champion if enemy_champion else "—")

        # Reset portraits to placeholder
        placeholder_style_my = (
            "border-radius: 40px; background: #313244; border: 2px solid #89b4fa;"
        )
        placeholder_style_enemy = (
            "border-radius: 40px; background: #313244; border: 2px solid #f38ba8;"
        )
        if not my_champion:
            self._my_portrait.clear()
            self._my_portrait.setStyleSheet(placeholder_style_my)
        if not enemy_champion:
            self._enemy_portrait.clear()
            self._enemy_portrait.setStyleSheet(placeholder_style_enemy)

        # Load portraits if we have champion names
        if my_champion:
            cached = self._portrait_cache.get(my_champion.lower())
            if cached and not cached.isNull():
                self._my_portrait.setPixmap(cached)
            else:
                self._my_portrait.clear()
                self._my_portrait.setStyleSheet(placeholder_style_my)
                self._load_portrait(my_champion)
        if enemy_champion:
            cached = self._portrait_cache.get(enemy_champion.lower())
            if cached and not cached.isNull():
                self._enemy_portrait.setPixmap(cached)
            else:
                self._enemy_portrait.clear()
                self._enemy_portrait.setStyleSheet(placeholder_style_enemy)
                self._load_portrait(enemy_champion)

        if in_game:
            if my_champion and enemy_champion:
                hint = f"Playing {my_champion} against {enemy_champion}"
            elif my_champion:
                hint = f"Playing {my_champion}"
            else:
                hint = "Game in progress"
        else:
            if my_champion and enemy_champion:
                hint = f"Matched up: {my_champion} vs {enemy_champion}"
            elif my_champion:
                hint = f"Picked {my_champion} — waiting for enemy champion…"
            else:
                hint = "Waiting for champion selection…"

        self._status_label.setText(hint)

        build_url = fallback_url or matchup_url
        self._last_build_url = build_url
        self._sync_role_tab_state()
        if my_champion and build_url:
            self._fetch_build_data(build_url, self._effective_role_hint())
        else:
            self._apply_empty_build_state("Waiting for champion selection...")


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

        mw = self.parent()
        app_bg = str(getattr(mw, "_app_bg_color", DEFAULT_APP_BG_COLOR))
        app_surface = str(getattr(mw, "_app_surface_color", DEFAULT_APP_SURFACE_COLOR))
        app_border = str(getattr(mw, "_app_border_color", DEFAULT_APP_BORDER_COLOR))
        app_text = str(getattr(mw, "_app_text_color", DEFAULT_APP_TEXT_COLOR))
        app_hover = str(getattr(mw, "_app_hover_color", DEFAULT_APP_HOVER_COLOR))

        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setAutoFillBackground(True)
        self.setStyleSheet(
            f"QDialog {{ background-color: {app_bg}; color: {app_text}; }}"
            f"QWidget {{ background-color: {app_bg}; color: {app_text}; }}"
            f"QLineEdit {{ background-color: {app_surface}; color: {app_text}; border: 1px solid {app_border}; padding: 4px; }}"
            f"QPushButton {{ background-color: {app_surface}; color: {app_text}; border: 1px solid {app_border}; padding: 5px 10px; }}"
            f"QPushButton:hover {{ background-color: {app_hover}; }}"
        )

        if sys.platform.startswith("win"):
            self.setAttribute(Qt.WA_NativeWindow, True)
            self.create()
            _apply_windows11_chrome(self, True)
            self.setProperty("_chrome_preapplied", True)
            _arm_first_show_reveal(self)
        
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

    def showEvent(self, event):
        super().showEvent(event)
        _reveal_after_first_show(self)


class LaunchProgressDialog(QDialog):
    """Compact launch dialog with predictable proportions."""

    def __init__(self, message: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Launching...")
        self.setModal(True)
        self.setMinimumSize(440, 170)
        self.setMaximumWidth(560)
        self.setAttribute(Qt.WA_StyledBackground, True)

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

        # Email (optional)
        layout.addWidget(QLabel("Email (optional):"))
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("account@example.com")
        layout.addWidget(self.email_input)

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
            self.email_input.setText(getattr(self.editing_account, "email", "") or "")
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
            'email': self.email_input.text().strip(),
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

    CHAMP_SELECT_DEFAULT_RESOLUTION = "1501x1014"

    CHAMP_SELECT_RESOLUTIONS = [
        "941x1053",
        "800x900",
        "900x1000",
        "1000x1100",
        "1134x1200",
        "1280x1300",
        "1440x1440",
        "1501x1014",
        "1600x1600",
        "1920x1080",
        "1920x1200",
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
    CHAMPION_SKIN_CACHE: dict[str, list[tuple[str, int]]] = {}

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

    APP_COLOR_PRESETS = [
        ("Default Dark", {
            "app_bg_color": DEFAULT_APP_BG_COLOR,
            "app_surface_color": DEFAULT_APP_SURFACE_COLOR,
            "app_border_color": DEFAULT_APP_BORDER_COLOR,
            "app_text_color": DEFAULT_APP_TEXT_COLOR,
            "app_accent_color": DEFAULT_APP_ACCENT_COLOR,
            "app_hover_color": DEFAULT_APP_HOVER_COLOR,
        }),
        ("Midnight Slate", {
            "app_bg_color": "#0f111a",
            "app_surface_color": "#171a26",
            "app_border_color": "#2a3142",
            "app_text_color": "#d7dbea",
            "app_accent_color": "#8b5cf6",
            "app_hover_color": "#9d74f8",
        }),
        ("Blurple Night", {
            "app_bg_color": "#1e1f22",
            "app_surface_color": "#2b2d31",
            "app_border_color": "#3f4147",
            "app_text_color": "#dbdee1",
            "app_accent_color": "#4b57c8",
            "app_hover_color": "#5e6ad5",
        }),
        ("Industrial Graphite", {
            "app_bg_color": "#0b0e14",
            "app_surface_color": "#141a24",
            "app_border_color": "#283245",
            "app_text_color": "#c7d0df",
            "app_accent_color": "#66c0f4",
            "app_hover_color": "#3a4d6e",
        }),
        ("Creator Noir", {
            "app_bg_color": "#0f0f0f",
            "app_surface_color": "#1a1a1a",
            "app_border_color": "#2c2c2c",
            "app_text_color": "#f1f1f1",
            "app_accent_color": "#ff3b30",
            "app_hover_color": "#3a3a3a",
        }),
        ("Crimson Night", {
            "app_bg_color": "#1b0f12",
            "app_surface_color": "#2a171c",
            "app_border_color": "#443039",
            "app_text_color": "#f0d7db",
            "app_accent_color": "#e85d8a",
            "app_hover_color": "#584050",
        }),
    ]

    def __init__(
        self,
        parent=None,
        settings: Optional[dict] = None,
        apply_callback: Optional[Callable[[dict], None]] = None,
    ):
        super().__init__(parent)
        merged_settings = dict(SETTINGS_PANEL_DEFAULTS)
        if settings:
            merged_settings.update(settings)
        self._settings = merged_settings
        self._apply_callback = apply_callback
        self._save_requested = False

        # Set dark palette HERE, before init_ui() creates any child widgets.
        # Qt paints each widget's background using the palette before any
        # stylesheet is applied, so this is the only way to prevent the
        # first-frame white flash on Windows.
        self.setAttribute(Qt.WA_StyledBackground, True)
        _bg = QColor(str(getattr(parent, '_app_bg_color', DEFAULT_APP_BG_COLOR)))
        _surface = QColor(str(getattr(parent, '_app_surface_color', DEFAULT_APP_SURFACE_COLOR)))
        _text = QColor(str(getattr(parent, '_app_text_color', DEFAULT_APP_TEXT_COLOR)))
        _pal = QPalette()
        _pal.setColor(QPalette.Window,      _bg)
        _pal.setColor(QPalette.WindowText,  _text)
        _pal.setColor(QPalette.Base,        _surface)
        _pal.setColor(QPalette.AlternateBase, _surface)
        _pal.setColor(QPalette.Text,        _text)
        _pal.setColor(QPalette.Button,      _surface)
        _pal.setColor(QPalette.ButtonText,  _text)
        self.setPalette(_pal)

        # Pre-apply the *final* dialog stylesheet before any child widgets are
        # created so there is no first-frame theme swap.
        app_bg = str(getattr(parent, '_app_bg_color', DEFAULT_APP_BG_COLOR))
        app_surface = str(getattr(parent, '_app_surface_color', DEFAULT_APP_SURFACE_COLOR))
        app_border = str(getattr(parent, '_app_border_color', DEFAULT_APP_BORDER_COLOR))
        app_text = str(getattr(parent, '_app_text_color', DEFAULT_APP_TEXT_COLOR))
        app_hover = str(getattr(parent, '_app_hover_color', DEFAULT_APP_HOVER_COLOR))
        self._dialog_stylesheet = (
            f"QDialog {{ background-color: {app_bg}; color: {app_text}; }}"
            f"QWidget {{ background-color: {app_bg}; color: {app_text}; }}"
            f"QLineEdit {{ background-color: {app_surface}; color: {app_text}; border: 1px solid {app_border}; padding: 4px; }}"
            f"QComboBox {{ background-color: {app_surface}; color: {app_text}; border: 1px solid {app_border}; padding: 4px; }}"
            f"QCheckBox {{ color: {app_text}; }}"
            f"QPushButton {{ background-color: {app_surface}; color: {app_text}; border: 1px solid {app_border}; padding: 5px 10px; }}"
            f"QPushButton:hover {{ background-color: {app_hover}; }}"
        )
        self.setAutoFillBackground(True)
        self.setStyleSheet(self._dialog_stylesheet)

        # Ensure a native HWND exists early and avoid partial paints while
        # the dialog is being constructed and styled.
        self.setAttribute(Qt.WA_NativeWindow, True)
        self.setUpdatesEnabled(False)
        _arm_first_show_reveal(self)

        # Force HWND creation so we can apply dark-mode chrome to the title bar
        # *before* the dialog is shown — prevents the white title bar flash.
        self.create()
        _apply_windows11_chrome(self, True)
        self.setProperty("_chrome_preapplied", True)

        self.init_ui()
        self.setUpdatesEnabled(True)
        self.repaint()

    def showEvent(self, event):
        if sys.platform.startswith("win"):
            _apply_windows11_chrome(self, True)
        super().showEvent(event)
        _reveal_after_first_show(self)

    def _default_settings_values(self) -> dict:
        return dict(SETTINGS_PANEL_DEFAULTS)

    def _all_app_color_presets(self) -> list[tuple[str, dict]]:
        return list(self.APP_COLOR_PRESETS)

    def _populate_theme_presets(self):
        if not hasattr(self, "app_theme_combo"):
            return
        self.app_theme_combo.blockSignals(True)
        self.app_theme_combo.clear()
        for label, preset in self._all_app_color_presets():
            self.app_theme_combo.addItem(label, preset)
        saved_preset = str(self._settings.get("app_theme_preset", "")).strip()
        index = self.app_theme_combo.findText(saved_preset)
        if index < 0:
            index = self._find_app_theme_preset_index()
        self.app_theme_combo.setCurrentIndex(index)
        self.app_theme_combo.blockSignals(False)

    def _is_classic_light_selected(self) -> bool:
        return False

    def _sync_champion_splash_availability(self):
        self.champion_splash_enabled_checkbox.setEnabled(True)
        self.champion_splash_enabled_checkbox.setToolTip(
            "Show selected champion base splash art behind the account entries."
        )

        splash_enabled = self.champion_splash_enabled_checkbox.isChecked()
        self.champion_splash_combo.setEnabled(splash_enabled)
        self.champion_splash_skin_combo.setEnabled(splash_enabled and self.champion_splash_combo.currentData() != SPLASH_THEME_AUTO)
        self.champion_splash_opacity_combo.setEnabled(splash_enabled)

    def _on_theme_preset_changed(self, _index: int):
        self._sync_champion_splash_availability()

    @staticmethod
    def _set_combo_to_data(combo: QComboBox, target_value, fallback_index: int = 0):
        index = combo.findData(target_value)
        combo.setCurrentIndex(fallback_index if index < 0 else index)

    def _apply_values_to_controls(self, values: dict):
        self.startup_checkbox.setChecked(bool(values.get("start_on_windows_startup", _is_startup_enabled())))
        self.start_minimized_checkbox.setChecked(bool(values.get("start_minimized_to_tray", False)))
        self._set_combo_to_data(self.close_behavior_combo, str(values.get("close_behavior", "tray")))
        self._set_combo_to_data(self.auto_lock_combo, int(values.get("auto_lock_minutes", 0)))
        self.remember_password_24h_checkbox.setChecked(bool(values.get("remember_password_24h", True)))
        self._set_combo_to_data(self.clipboard_clear_combo, int(values.get("clipboard_auto_clear_seconds", 0)))
        self.confirm_launch_checkbox.setChecked(bool(values.get("confirm_before_launch", True)))
        self.confirm_delete_checkbox.setChecked(bool(values.get("confirm_before_delete", True)))
        self._set_combo_to_data(self.account_sort_mode_combo, str(values.get("account_sort_mode", "manual")))
        self._set_combo_to_data(self.rank_refresh_combo, str(values.get("rank_refresh_mode", "manual")))
        self.auto_check_updates_checkbox.setChecked(bool(values.get("auto_check_updates", True)))
        self._set_combo_to_data(self.log_level_combo, str(values.get("diagnostics_log_level", "INFO")))

        window_size_mode = str(values.get("window_size_mode", "static"))
        window_size = str(values.get("window_size", "800x600"))
        if window_size_mode == "custom":
            self.window_size_combo.setCurrentIndex(0)
        else:
            index = self.window_size_combo.findText(window_size)
            self.window_size_combo.setCurrentIndex(0 if index < 0 else index)

        champ_select_size = str(values.get("champ_select_window_size", self.CHAMP_SELECT_DEFAULT_RESOLUTION))
        cs_idx = self.champ_select_size_combo.findData(champ_select_size)
        if cs_idx < 0:
            cs_idx = self.champ_select_size_combo.findData(self.CHAMP_SELECT_DEFAULT_RESOLUTION)
        self.champ_select_size_combo.setCurrentIndex(0 if cs_idx < 0 else cs_idx)

        self._set_combo_to_data(self.text_zoom_combo, int(values.get("text_zoom_percent", 110)))
        self.show_ranks_checkbox.setChecked(bool(values.get("show_ranks", True)))
        self.show_images_checkbox.setChecked(bool(values.get("show_rank_images", True)))
        self.show_tags_checkbox.setChecked(bool(values.get("show_tags", True)))
        self.auto_open_ingame_checkbox.setChecked(bool(values.get("auto_open_ingame_page", True)))
        self._set_combo_to_data(self.tag_size_combo, str(values.get("tag_size", "medium")))
        self._set_combo_to_data(self.tag_style_combo, str(values.get("tag_chip_style", "vibrant")))
        self._set_combo_to_data(
            self.logged_in_gradient_color_combo,
            str(values.get("logged_in_gradient_color", _default_logged_in_highlight(bool(getattr(self.parent(), "_dark_mode", True))))),
        )
        self._set_combo_to_data(
            self.hover_highlight_color_combo,
            str(values.get("hover_highlight_color", HOVER_HIGHLIGHT_THEME_AUTO)),
        )

        self.champion_splash_enabled_checkbox.setChecked(bool(values.get("champion_splash_enabled", False)))
        self._set_combo_to_data(
            self.champion_splash_combo,
            str(values.get("champion_splash_champion", SPLASH_THEME_AUTO)),
        )
        self._refresh_champion_skin_options()
        self._set_combo_to_data(self.champion_splash_skin_combo, int(values.get("champion_splash_skin", 0)))
        self._set_combo_to_data(self.champion_splash_opacity_combo, int(values.get("champion_splash_opacity", 70)))
        self._set_combo_to_data(self.logged_in_gradient_intensity_combo, int(values.get("logged_in_gradient_intensity", 20)))
        self._set_combo_to_data(self.logged_in_border_width_combo, int(values.get("logged_in_border_width", 2)))
        self._set_combo_to_data(self.logged_in_border_opacity_combo, int(values.get("logged_in_border_opacity", 60)))
        self._set_combo_to_data(self.row_density_combo, str(values.get("row_density", "compact")))
        self._set_combo_to_data(self.rank_icon_size_combo, int(values.get("rank_icon_size", 34)))
        self._set_combo_to_data(self.rank_text_brightness_combo, int(values.get("rank_text_brightness", 100)))

        self.auto_backup_checkbox.setChecked(bool(values.get("auto_backup_enabled", True)))
        self._set_combo_to_data(self.auto_backup_keep_combo, int(values.get("auto_backup_keep_count", 20)))

        self._settings.update({
            "app_bg_color": str(values.get("app_bg_color", DEFAULT_APP_BG_COLOR)),
            "app_surface_color": str(values.get("app_surface_color", DEFAULT_APP_SURFACE_COLOR)),
            "app_border_color": str(values.get("app_border_color", DEFAULT_APP_BORDER_COLOR)),
            "app_text_color": str(values.get("app_text_color", DEFAULT_APP_TEXT_COLOR)),
            "app_accent_color": str(values.get("app_accent_color", DEFAULT_APP_ACCENT_COLOR)),
            "app_hover_color": str(values.get("app_hover_color", DEFAULT_APP_HOVER_COLOR)),
        })
        self._populate_theme_presets()

        self.show_images_checkbox.setEnabled(self.show_ranks_checkbox.isChecked())
        self.rank_icon_size_combo.setEnabled(self.show_ranks_checkbox.isChecked())
        self.rank_text_brightness_combo.setEnabled(self.show_ranks_checkbox.isChecked())
        self.tag_size_combo.setEnabled(self.show_tags_checkbox.isChecked())
        self.tag_style_combo.setEnabled(self.show_tags_checkbox.isChecked())
        self._sync_champion_splash_availability()
        self.auto_backup_keep_combo.setEnabled(self.auto_backup_checkbox.isChecked())

    def _reset_to_defaults(self):
        self._confirm_reset_btn = getattr(self, "_confirm_reset_btn", None)
        if self._confirm_reset_btn is not None:
            self._confirm_reset_btn.setDown(False)
        QTimer.singleShot(0, self._confirm_reset_to_defaults)

    def _confirm_reset_to_defaults(self):
        result = QMessageBox.question(
            self,
            "Reset Settings",
            "Are you sure you want to reset all settings to defaults?\n\nThis will reset all settings except your master password.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if result != QMessageBox.Yes:
            return

        default_values = self._default_settings_values()
        reset_settings()
        self._settings = dict(default_values)
        self._apply_values_to_controls(default_values)
        if self._apply_callback:
            self._apply_callback(default_values)

    def init_ui(self):
        self.setWindowTitle("Settings")
        self.setModal(True)
        self.setMinimumWidth(620)

        self.setStyleSheet(self._dialog_stylesheet)

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

        general_layout.addWidget(QLabel("Champ Select window size:"))
        self.champ_select_size_combo = QComboBox()
        for res in self.CHAMP_SELECT_RESOLUTIONS:
            label = f"{res} (Default)" if res == self.CHAMP_SELECT_DEFAULT_RESOLUTION else res
            self.champ_select_size_combo.addItem(label, res)
        self.champ_select_size_combo.setToolTip(
            "The window will automatically resize to this resolution when champ select opens."
        )
        cs_size = str(self._settings.get("champ_select_window_size", self.CHAMP_SELECT_DEFAULT_RESOLUTION))
        cs_index = self.champ_select_size_combo.findData(cs_size)
        if cs_index < 0:
            cs_index = self.champ_select_size_combo.findData(self.CHAMP_SELECT_DEFAULT_RESOLUTION)
        self.champ_select_size_combo.setCurrentIndex(0 if cs_index < 0 else cs_index)
        general_layout.addWidget(self.champ_select_size_combo)

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

        appearance_layout.addWidget(QLabel("Application colors:"))

        theme_row = QHBoxLayout()
        theme_row.addWidget(QLabel("Theme preset:"))
        self.app_theme_combo = QComboBox()
        self._populate_theme_presets()
        theme_row.addWidget(self.app_theme_combo)
        theme_row.addStretch()
        appearance_layout.addLayout(theme_row)
        self.app_theme_combo.currentIndexChanged.connect(self._on_theme_preset_changed)

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

        self.champ_select_secondary_monitor_checkbox = QCheckBox("Open champ select on secondary monitor")
        self.champ_select_secondary_monitor_checkbox.setChecked(bool(self._settings.get("champ_select_secondary_monitor", False)))
        self.champ_select_secondary_monitor_checkbox.setToolTip(
            "When enabled, champ select window will open on secondary monitor (if available)."
        )
        general_layout.addWidget(self.champ_select_secondary_monitor_checkbox)

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
        default_gradient_color = _default_logged_in_highlight(True)
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
            "Global Theme follows the dark theme automatically. Pick a color here to override it."
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

        edit_bg = "#171a2a"
        edit_fg = "#dbe4ff"
        edit_border = "#3f4b71"
        placeholder = "#8ea1cf"
        popup_bg = "#151b2d"
        popup_fg = "#e9efff"
        popup_border = "#3f4b71"
        popup_sel_bg = "#2d3d62"
        popup_sel_fg = "#ffffff"

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

        splash_skin_row = QHBoxLayout()
        splash_skin_row.addWidget(QLabel("Splash skin:"))
        self.champion_splash_skin_combo = QComboBox()
        self.champion_splash_skin_combo.setEditable(True)
        self.champion_splash_skin_combo.setInsertPolicy(QComboBox.NoInsert)
        self.champion_splash_skin_combo.setToolTip(
            "Choose a skin variant for the selected champion splash."
        )
        splash_skin_row.addWidget(self.champion_splash_skin_combo)
        splash_skin_row.addStretch()
        appearance_layout.addLayout(splash_skin_row)

        self._refresh_champion_skin_options(initial=True)
        self.champion_splash_combo.currentIndexChanged.connect(self._refresh_champion_skin_options)

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

        self.champion_splash_enabled_checkbox.toggled.connect(lambda _checked: self._sync_champion_splash_availability())
        self.champion_splash_combo.currentIndexChanged.connect(lambda _index: self._sync_champion_splash_availability())
        self._sync_champion_splash_availability()

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
        self._confirm_reset_btn = QPushButton("Reset to Defaults")
        self._confirm_reset_btn.setAutoDefault(False)
        self._confirm_reset_btn.setDefault(False)
        self._confirm_reset_btn.clicked.connect(self._reset_to_defaults)
        button_row.addWidget(self._confirm_reset_btn)
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
        save_btn.clicked.connect(self._save_and_close)
        button_row.addWidget(save_btn)
        layout.addLayout(button_row)

        self.setLayout(layout)

    def _fetch_champion_skin_options(self, champion_id: str) -> list[tuple[str, int]]:
        champ = str(champion_id or "").strip()
        if not champ or champ == SPLASH_THEME_AUTO:
            return [("Base (Default)", 0)]
        cached = self.CHAMPION_SKIN_CACHE.get(champ)
        if cached is not None:
            return cached

        options: list[tuple[str, int]] = [("Base (Default)", 0)]
        try:
            req = Request(
                f"https://ddragon.leagueoflegends.com/cdn/{DDRAGON_VERSION}/data/en_US/champion/{champ}.json",
                headers={"User-Agent": "lol-account-manager"},
            )
            with urlopen(req, timeout=6) as resp:
                payload = json.loads(resp.read().decode("utf-8", errors="ignore"))
            skins = (payload.get("data") or {}).get(champ, {}).get("skins") or []
            parsed: list[tuple[str, int]] = []
            for skin in skins:
                num = int(skin.get("num", 0))
                raw_name = str(skin.get("name") or "Default")
                label = "Base (Default)" if num == 0 or raw_name.strip().lower() == "default" else raw_name.strip()
                parsed.append((label, num))
            if parsed:
                options = parsed
        except Exception:
            logging.debug("Failed loading skin metadata for %s", champ, exc_info=True)

        self.CHAMPION_SKIN_CACHE[champ] = options
        return options

    def _refresh_champion_skin_options(self, *_args, initial: bool = False):
        champion_id = str(self.champion_splash_combo.currentData() or SPLASH_THEME_AUTO)
        options = self._fetch_champion_skin_options(champion_id)

        if initial:
            target_skin = int(self._settings.get("champion_splash_skin", 0))
        else:
            current_data = self.champion_splash_skin_combo.currentData()
            target_skin = int(current_data) if current_data is not None else 0

        self.champion_splash_skin_combo.blockSignals(True)
        self.champion_splash_skin_combo.clear()
        for label, skin_num in options:
            self.champion_splash_skin_combo.addItem(label, skin_num)
        skin_index = self.champion_splash_skin_combo.findData(target_skin)
        if skin_index < 0:
            skin_index = self.champion_splash_skin_combo.findData(0)
        self.champion_splash_skin_combo.setCurrentIndex(max(0, skin_index))
        self.champion_splash_skin_combo.blockSignals(False)

        skin_line_edit = self.champion_splash_skin_combo.lineEdit()
        if skin_line_edit:
            skin_line_edit.setPlaceholderText("Type skin name")
            skin_line_edit.setClearButtonEnabled(True)

        popup_bg = "#151b2d"
        popup_fg = "#e9efff"
        popup_border = "#3f4b71"
        popup_sel_bg = "#2d3d62"
        popup_sel_fg = "#ffffff"

        skin_completer = QCompleter(self.champion_splash_skin_combo.model(), self)
        skin_completer.setCaseSensitivity(Qt.CaseInsensitive)
        skin_completer.setCompletionMode(QCompleter.PopupCompletion)
        try:
            skin_completer.setFilterMode(Qt.MatchContains)
        except Exception:
            pass
        self.champion_splash_skin_combo.setCompleter(skin_completer)
        skin_completer.popup().setStyleSheet(
            f"QListView {{ background: {popup_bg}; color: {popup_fg}; border: 1px solid {popup_border}; border-radius: 8px; padding: 1px; outline: none; }}"
            f"QListView::item {{ padding: 4px 8px; min-height: 20px; border-radius: 6px; }}"
            f"QListView::item:selected {{ background: {popup_sel_bg}; color: {popup_sel_fg}; }}"
            f"QListView::item:hover {{ background: {popup_sel_bg}; color: {popup_sel_fg}; }}"
        )

        splash_enabled = bool(self.champion_splash_enabled_checkbox.isChecked())
        self.champion_splash_skin_combo.setEnabled(splash_enabled and champion_id != SPLASH_THEME_AUTO)

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

        skin_typed = self.champion_splash_skin_combo.currentText().strip().casefold()
        champion_splash_skin = self.champion_splash_skin_combo.currentData()
        if skin_typed:
            for label, skin_num in self._fetch_champion_skin_options(str(champion_splash_value)):
                if skin_typed == label.casefold():
                    champion_splash_skin = skin_num
                    break
        if champion_splash_skin is None:
            champion_splash_skin = 0
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
            "champ_select_window_size": str(self.champ_select_size_combo.currentData() or self.CHAMP_SELECT_DEFAULT_RESOLUTION),
            "text_zoom_percent": int(self.text_zoom_combo.currentData()),
            "show_ranks": self.show_ranks_checkbox.isChecked(),
            "show_rank_images": self.show_images_checkbox.isChecked(),
            "show_tags": self.show_tags_checkbox.isChecked(),
            "auto_open_ingame_page": self.auto_open_ingame_checkbox.isChecked(),
            "champ_select_secondary_monitor": self.champ_select_secondary_monitor_checkbox.isChecked(),
            "tag_size": str(self.tag_size_combo.currentData()),
            "tag_chip_style": str(self.tag_style_combo.currentData()),
            "logged_in_gradient_color": str(self.logged_in_gradient_color_combo.currentData()),
            "hover_highlight_color": str(self.hover_highlight_color_combo.currentData()),
            "champion_splash_enabled": self.champion_splash_enabled_checkbox.isChecked() and not self._is_classic_light_selected(),
            "champion_splash_champion": str(champion_splash_value),
            "champion_splash_skin": int(champion_splash_skin),
            "champion_splash_opacity": int(self.champion_splash_opacity_combo.currentData()),
            "logged_in_gradient_intensity": int(self.logged_in_gradient_intensity_combo.currentData()),
            "logged_in_border_width": int(self.logged_in_border_width_combo.currentData()),
            "logged_in_border_opacity": int(self.logged_in_border_opacity_combo.currentData()),
            "row_density": str(self.row_density_combo.currentData()),
            "rank_icon_size": int(self.rank_icon_size_combo.currentData()),
            "rank_text_brightness": int(self.rank_text_brightness_combo.currentData()),
            "auto_backup_enabled": self.auto_backup_checkbox.isChecked(),
            "auto_backup_keep_count": int(self.auto_backup_keep_combo.currentData()),
            "app_bg_color": str(self._selected_app_preset().get("app_bg_color", DEFAULT_APP_BG_COLOR)),
            "app_surface_color": str(self._selected_app_preset().get("app_surface_color", DEFAULT_APP_SURFACE_COLOR)),
            "app_border_color": str(self._selected_app_preset().get("app_border_color", DEFAULT_APP_BORDER_COLOR)),
            "app_text_color": str(self._selected_app_preset().get("app_text_color", DEFAULT_APP_TEXT_COLOR)),
            "app_accent_color": str(self._selected_app_preset().get("app_accent_color", DEFAULT_APP_ACCENT_COLOR)),
            "app_hover_color": str(self._selected_app_preset().get("app_hover_color", DEFAULT_APP_HOVER_COLOR)),
            "app_theme_preset": str(self.app_theme_combo.currentText()).strip() if hasattr(self, "app_theme_combo") else "Default Dark",
        }

    def apply_settings(self):
        """Apply settings without closing the dialog."""
        if self._apply_callback:
            self._apply_callback(self.get_values())

    def _save_and_close(self):
        """Apply settings and close the dialog."""
        self._save_requested = True
        self.accept()

    def _selected_app_preset(self) -> dict:
        if not hasattr(self, "app_theme_combo"):
            return {}
        preset = self.app_theme_combo.currentData() or {}
        return preset if isinstance(preset, dict) else {}

    def _find_app_theme_preset_index(self) -> int:
        current = {
            "app_bg_color": str(self._settings.get("app_bg_color", DEFAULT_APP_BG_COLOR)),
            "app_surface_color": str(self._settings.get("app_surface_color", DEFAULT_APP_SURFACE_COLOR)),
            "app_border_color": str(self._settings.get("app_border_color", DEFAULT_APP_BORDER_COLOR)),
            "app_text_color": str(self._settings.get("app_text_color", DEFAULT_APP_TEXT_COLOR)),
            "app_accent_color": str(self._settings.get("app_accent_color", DEFAULT_APP_ACCENT_COLOR)),
            "app_hover_color": str(self._settings.get("app_hover_color", DEFAULT_APP_HOVER_COLOR)),
        }
        all_presets = self._all_app_color_presets()
        for index in range(len(all_presets)):
            preset = all_presets[index][1]
            if all(current.get(k) == v for k, v in preset.items()):
                return index
        return 0

    def eventFilter(self, obj, event):
        if getattr(self, "_champion_splash_line_edit", None) is obj and event.type() == QEvent.FocusIn:
            self._champion_splash_line_edit.clear()
        return super().eventFilter(obj, event)


class AccountSpotlightPanel(AccountListBackgroundFrame):
    """Auto-loaded spotlight view for the currently logged-in account."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._profile_url = ""
        self._active_username = ""
        self._loaded_profile_url = ""
        self._is_dark_mode = True
        self._base_color = QColor(DEFAULT_APP_SURFACE_COLOR)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 8, 0, 0)
        outer.setSpacing(8)

        self._content_card = QFrame()
        self._content_card.setObjectName("spotlightContentCard")
        self._content_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        content_layout = QVBoxLayout(self._content_card)
        content_layout.setContentsMargins(6, 6, 6, 6)

        self._web_view = None
        self._fallback_container = QWidget()
        self._fallback_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        fallback_layout = QVBoxLayout(self._fallback_container)
        fallback_layout.setContentsMargins(20, 16, 20, 16)
        fallback_layout.setSpacing(8)
        self._fallback_message = QLabel(
            "Embedded profile view is unavailable in this build.\n"
            "Open the same u.gg profile in your browser."
        )
        self._fallback_message.setWordWrap(True)
        self._fallback_message.setAlignment(Qt.AlignCenter)
        self._fallback_open_btn = QPushButton("Open u.gg Profile")
        self._fallback_open_btn.clicked.connect(self._open_profile_in_browser)
        fallback_layout.addStretch()
        fallback_layout.addWidget(self._fallback_message)
        fallback_layout.addWidget(self._fallback_open_btn, 0, Qt.AlignHCenter)
        fallback_layout.addStretch()

        if QWebEngineView is not None:
            try:
                self._web_view = QWebEngineView(self)
                self._web_view.setContextMenuPolicy(Qt.NoContextMenu)
                self._web_view.loadFinished.connect(self._inject_hide_css)
                self._web_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
                content_layout.addWidget(self._web_view, 1)
            except Exception:
                self._web_view = None

        if self._web_view is None:
            content_layout.addWidget(self._fallback_container, 1)

        outer.addWidget(self._content_card, 1)
        self.setMinimumHeight(420)
        self._apply_panel_styles()

    def _open_profile_in_browser(self):
        if not self._profile_url:
            return
        try:
            webbrowser.open_new_tab(self._profile_url)
        except Exception:
            webbrowser.open(self._profile_url)

    def _inject_hide_css(self, ok: bool):
        """Called on loadFinished. Schedules repeated hide-script runs so that
        React-rendered elements (which arrive after the load event) are also caught."""
        if not ok or self._web_view is None:
            return
        self._run_hide_script()
        QTimer.singleShot(600,  self._run_hide_script)
        QTimer.singleShot(1500, self._run_hide_script)
        QTimer.singleShot(3000, self._run_hide_script)

    def _run_hide_script(self):
        """Inject CSS + directly force-hide u.gg navigation chrome."""
        try:
            if self._web_view is None:
                return
            js = r"""
(function() {
    /* ── 1. Inject persistent style tag (runs once) ─────────────────── */
    if (!document.getElementById('_ugg_embed_hide')) {
        var s = document.createElement('style');
        s.id = '_ugg_embed_hide';
        s.textContent =
            'nav,aside,header,[role="navigation"],[role="complementary"],[role="banner"],' +
            '[class*="Sidebar"],[class*="sidebar"],[class*="NavBar"],[class*="navbar"] ' +
            '{ display:none!important; }' +
            'body,html { margin:0!important; padding:0!important; }';
        (document.head || document.documentElement).appendChild(s);
    }

    /* Track whether the user has scrolled — if so, never force-scroll back to top */
    if (!window._ugg_user_scrolled) {
        window._ugg_user_scrolled = false;
        window.addEventListener('scroll', function() {
            window._ugg_user_scrolled = true;
        }, { passive: true, once: true });
    }

    /* ── 2. Core cleanup function ────────────────────────────────────── */
    function cleanup(allowScroll) {
        /* Hide fixed/sticky bars and sidebars */
        document.querySelectorAll('*').forEach(function(el) {
            var cs = window.getComputedStyle(el);
            if (cs.position !== 'fixed' && cs.position !== 'sticky') return;
            var top = parseFloat(cs.top);
            var left = parseFloat(cs.left);
            var zIdx = parseInt(cs.zIndex) || 0;
            /* Fixed top bar */
            if (!isNaN(top) && top <= 4 && zIdx > 50) {
                el.style.setProperty('display', 'none', 'important');
            }
            /* Fixed left sidebar (narrow) */
            if (!isNaN(left) && left <= 4 && parseFloat(cs.width) < 120) {
                el.style.setProperty('display', 'none', 'important');
            }
        });

        /* Hide any explicit nav/aside/header in the live DOM */
        document.querySelectorAll('nav,aside,header').forEach(function(el) {
            el.style.setProperty('display', 'none', 'important');
        });

        /* Walk top ~6 levels of DOM and zero padding-top/margin-top > threshold.
           This removes the spacer reserved for the now-hidden fixed navbar
           regardless of how deeply React nests it. */
        function zeroTopSpacing(el, depth) {
            if (!el || depth > 6) return;
            var cs = window.getComputedStyle(el);
            var pt = parseFloat(cs.paddingTop) || 0;
            var mt = parseFloat(cs.marginTop) || 0;
            if (pt > 20) el.style.setProperty('padding-top', '0', 'important');
            if (mt > 20) el.style.setProperty('margin-top', '0', 'important');
            /* Recurse into first few children only */
            for (var i = 0; i < Math.min(el.children.length, 4); i++) {
                zeroTopSpacing(el.children[i], depth + 1);
            }
        }
        zeroTopSpacing(document.body, 0);

        document.body.style.setProperty('margin', '0', 'important');
        document.body.style.setProperty('padding', '0', 'important');
        document.documentElement.style.setProperty('margin', '0', 'important');
        document.documentElement.style.setProperty('padding', '0', 'important');

        /* Only scroll to top before the user has scrolled */
        if (allowScroll && !window._ugg_user_scrolled) {
            window.scrollTo(0, 0);
        }
    }

    /* ── 3. Run immediately and after React finishes rendering ───────── */
    cleanup(true);
    setTimeout(function(){ cleanup(true); }, 300);
    setTimeout(function(){ cleanup(true); }, 800);
    setTimeout(function(){ cleanup(true); }, 2000);

    /* ── 4. MutationObserver: re-run cleanup when React mutates the DOM ─ */
    if (!window._ugg_observer) {
        var _debounce_timer = null;
        window._ugg_observer = new MutationObserver(function() {
            clearTimeout(_debounce_timer);
            /* Never force-scroll on observer-triggered runs */
            _debounce_timer = setTimeout(function(){ cleanup(false); }, 150);
        });
        window._ugg_observer.observe(document.documentElement, {
            childList: true, subtree: true,
            attributes: true, attributeFilter: ['style', 'class']
        });
    }
})();
"""
            self._web_view.page().runJavaScript(js)
        except RuntimeError:
            pass

    def _apply_panel_styles(self):
        text_main = "#e8eefc" if self._is_dark_mode else "#1f2937"
        text_muted = "#9fb0d5" if self._is_dark_mode else "#4b5563"
        content_bg = "rgba(10, 14, 24, 0.86)" if self._is_dark_mode else "rgba(248, 250, 252, 0.98)"
        border = "#2f3a55" if self._is_dark_mode else "#cbd5e1"
        accent = "#8ab4ff" if self._is_dark_mode else "#2563eb"

        self.setStyleSheet(
            "QFrame#spotlightContentCard {"
            f"background: {content_bg};"
            f"border: 1px solid {border};"
            "border-radius: 10px;"
            "}"
            f"QLabel {{ color: {text_main}; }}"
            f"QLabel#spotlightMuted {{ color: {text_muted}; }}"
            "QPushButton {"
            f"background: {accent};"
            "color: #ffffff;"
            "border: none;"
            "border-radius: 6px;"
            "padding: 6px 12px;"
            "font-weight: 600;"
            "}"
            "QPushButton:hover { background: #6b95e8; }"
        )

    def set_dark_mode(self, enabled: bool):
        super().set_dark_mode(enabled)
        self._is_dark_mode = bool(enabled)
        self._apply_panel_styles()

    def set_base_color(self, color: str):
        super().set_base_color(color)

    def set_account(self, account: Optional[Account], rank_data: Optional[dict], profile_url: str):
        self._profile_url = str(profile_url or "").strip()
        if not account:
            self._active_username = ""
            self._loaded_profile_url = ""
            return

        self._active_username = account.username

        if self._web_view is not None and self._profile_url:
            if self._profile_url != self._loaded_profile_url:
                self._loaded_profile_url = self._profile_url
                self._web_view.setUrl(QUrl(self._profile_url))
        elif self._profile_url:
            self._fallback_message.setText(
                "Embedded profile view is unavailable in this build.\n"
                "Open the same u.gg profile in your browser."
            )


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
        ui_scale: float = 1.0,
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
        self._ui_scale = max(1.0, min(2.0, float(ui_scale)))
        self.init_ui()

    def _scale_px(self, value: int) -> int:
        return max(1, int(round(int(value) * self._ui_scale)))

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
        self._shadow.setBlurRadius(22)
        self._shadow.setColor(QColor(0, 0, 0, 120))
        # Do NOT call setGraphicsEffect here — applying it during list builds
        # forces Qt to set up a software-rendering pipeline for every row,
        # which can briefly activate the Windows console window. The effect
        # is applied lazily in _update_visual_state on first hover.

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
            tags_wrap = QWidget(self)
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
        rank_widget = QWidget(self)
        rank_widget.setAttribute(Qt.WA_TranslucentBackground, True)
        rank_widget.setStyleSheet("background: transparent; border: none;")
        rank_layout = QHBoxLayout(rank_widget)
        rank_layout.setContentsMargins(0, 0, 0, 0)
        rank_layout.setSpacing(density["rank_spacing"])

        self.rank_icon_label = QLabel()
        self.rank_icon_label.setFixedSize(self._scale_px(self._rank_icon_size), self._scale_px(self._rank_icon_size))
        self.rank_icon_label.setScaledContents(False)
        self.rank_icon_label.setAttribute(Qt.WA_TranslucentBackground, True)
        self.rank_icon_label.setStyleSheet("background: transparent; border: none;")

        self.logged_in_label = QLabel("Logged in")
        self.logged_in_label.setAttribute(Qt.WA_TranslucentBackground, True)
        self.logged_in_label.setVisible(False)
        self.logged_in_label.setAlignment(Qt.AlignCenter)
        self.logged_in_label.setFixedHeight(self._scale_px(density["logged_in_height"]))
        self.logged_in_label.setMinimumWidth(self._scale_px(78))
        rank_layout.addWidget(self.logged_in_label)
        rank_layout.addWidget(self.rank_icon_label)

        self.rank_label = QLabel("...")
        self.rank_label.setAlignment(Qt.AlignVCenter | Qt.AlignRight)
        self.rank_label.setAttribute(Qt.WA_TranslucentBackground, True)
        self.rank_label.setTextFormat(Qt.RichText)
        self.rank_label.setStyleSheet(
            "background: transparent; border: none; color: #8b93a8; font-size: 11px;"
        )
        self.rank_label.setMinimumWidth(self._scale_px(density["rank_min_width"]))
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
        badge_radius = self._scale_px(10)
        badge_font_px = 9.5 * self._ui_scale
        badge_pad_x = self._scale_px(9)
        if self._dark_mode:
            self.logged_in_label.setStyleSheet(
                f"background-color: {self._rgba(self._logged_in_gradient_color, badge_bg_alpha)};"
                f"border: 1px solid {self._rgba(self._logged_in_gradient_color, badge_border_alpha)};"
                f"border-radius: {badge_radius}px;"
                f"color: {badge_fg};"
                f"font-size: {badge_font_px:.1f}px;"
                "font-weight: 700;"
                f"padding: 0px {badge_pad_x}px;"
            )
        else:
            self.logged_in_label.setStyleSheet(
                f"background-color: {self._rgba(self._logged_in_gradient_color, max(20, badge_bg_alpha - 20))};"
                f"border: 1px solid {self._rgba(self._logged_in_gradient_color, max(45, badge_border_alpha - 25))};"
                f"border-radius: {badge_radius}px;"
                f"color: {badge_fg};"
                f"font-size: {badge_font_px:.1f}px;"
                "font-weight: 700;"
                f"padding: 0px {badge_pad_x}px;"
            )

    def apply_ui_scale(self, ui_scale: float):
        """Apply monitor-scale adjustments for fixed-size row elements."""
        self._ui_scale = max(1.0, min(2.0, float(ui_scale)))
        density = self._row_density_preset()
        self.rank_icon_label.setFixedSize(self._scale_px(self._rank_icon_size), self._scale_px(self._rank_icon_size))
        self.logged_in_label.setFixedHeight(self._scale_px(density["logged_in_height"]))
        self.logged_in_label.setMinimumWidth(self._scale_px(78))
        self.rank_label.setMinimumWidth(self._scale_px(density["rank_min_width"]))
        self._refresh_logged_in_badge_style()

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
        self._dark_mode = True
        self._refresh_tag_chip_styles()
        self._refresh_text_styles()
        self._refresh_logged_in_badge_style()
        self._update_visual_state()

    def set_hover_highlight_color(self, color: str):
        self._hover_highlight_color = str(color or self._hover_highlight_color)
        self._update_visual_state()

    def set_logged_in(self, logged_in: bool, status_text: str = "Logged In"):
        self._logged_in = logged_in
        self.logged_in_label.setVisible(logged_in)
        if logged_in:
            self.logged_in_label.setText(str(status_text or "Logged In"))
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
        # Guard: if the C++ shadow object has been deleted (happens when Qt
        # destroys widgets during app close, or via any stale
        # setGraphicsEffect(None) call), bail out silently rather than crash.
        try:
            self._shadow.blurRadius()
        except RuntimeError:
            return

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
                    "border: 1px solid transparent;"
                    "border-radius: 10px;"
                    "}"
                )
                self._shadow.setBlurRadius(0)
                self._shadow.setColor(QColor(0, 0, 0, 0))
            elif self._logged_in:
                self.setStyleSheet(
                    "#accountListItem {"
                    "background: qlineargradient(x1:0, y1:0, x2:1, y2:0,"
                    f"stop:0 {left_idle},"
                    f"stop:0.16 {mid_idle},"
                    "stop:1 rgba(25, 30, 47, 95));"
                    "border: 1px solid transparent;"
                    "border-radius: 10px;"
                    "}"
                )
                self._shadow.setBlurRadius(0)
                self._shadow.setColor(QColor(0, 0, 0, 0))
            elif active:
                hover_bg = self._rgba(self._hover_highlight_color, 170)
                hover_border = self._rgba(self._hover_highlight_color, 118)
                self.setStyleSheet(
                    "#accountListItem {"
                    f"background-color: {hover_bg};"
                    f"border: 1px solid {hover_border};"
                    "border-radius: 10px;"
                    "}"
                )
                self._shadow.setBlurRadius(22)
                self._shadow.setColor(QColor(0, 0, 0, 120))
                self._shadow.setEnabled(True)
                if self.graphicsEffect() is None:
                    self.setGraphicsEffect(self._shadow)
            else:
                self.setStyleSheet(
                    "#accountListItem {"
                    "background-color: transparent;"
                    "border: 1px solid transparent;"
                    "border-radius: 10px;"
                    "}"
                )
                # Disable rather than remove — setGraphicsEffect(None) would
                # delete the C++ object while self._shadow still references it.
                if self.graphicsEffect() is not None:
                    self._shadow.setEnabled(False)
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
                "border: 1px solid transparent;"
                "border-radius: 10px;"
                "}"
            )
            self._shadow.setBlurRadius(0)
            self._shadow.setColor(QColor(0, 0, 0, 0))
        elif self._logged_in:
            self.setStyleSheet(
                "#accountListItem {"
                "background: qlineargradient(x1:0, y1:0, x2:1, y2:0,"
                f"stop:0 {left_idle},"
                f"stop:0.30 {mid_idle},"
                "stop:1 rgba(223, 216, 205, 78));"
                "border: 1px solid transparent;"
                "border-radius: 10px;"
                "}"
            )
            self._shadow.setBlurRadius(0)
            self._shadow.setColor(QColor(0, 0, 0, 0))
        elif active:
            hover_bg = self._rgba(self._hover_highlight_color, 145)
            hover_border = self._rgba(self._hover_highlight_color, 128)
            self.setStyleSheet(
                "#accountListItem {"
                f"background-color: {hover_bg};"
                f"border: 1px solid {hover_border};"
                "border-radius: 10px;"
                "}"
            )
            self._shadow.setBlurRadius(14)
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
        # Avoid first-frame light paints while the window is being built.
        self.setUpdatesEnabled(False)
        self.setAttribute(Qt.WA_StyledBackground, True)
        _hide_windows_console_window()
        _hide_any_python_titled_window()
        self._settings = dict(SETTINGS_PANEL_DEFAULTS)
        self._settings.update(load_settings())
        self.account_manager: Optional[AccountManager] = None
        self.login_thread: Optional[LoginThread] = None
        self.ingame_watch_thread: Optional[InGameWatcherThread] = None
        self.ingame_diag_dialog: Optional[InGameDiagnosticsDialog] = None
        self.game_info_panel: Optional[InClientGamePanel] = None
        self.account_spotlight_panel: Optional[AccountSpotlightPanel] = None
        self.main_area_stack: Optional[QStackedWidget] = None
        self.launch_progress: Optional[LaunchProgressDialog] = None
        self.current_launch_username: Optional[str] = None
        self._rank_data_by_username: dict[str, dict] = {}
        self._last_champ_select_signature: str = ""
        self._last_champ_select_role_hint: str = ""
        self._last_champ_select_refresh_at: float = 0.0
        self._last_champ_select_close_at: float = 0.0
        self._last_launched_username: str = str(self._settings.get('last_launched_username', '') or '')
        self._dark_mode: bool = True
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
        self._champ_select_secondary_monitor: bool = bool(self._settings.get('champ_select_secondary_monitor', False))
        self._tag_size: str = str(self._settings.get('tag_size', 'medium'))
        self._tag_chip_style: str = str(self._settings.get('tag_chip_style', 'vibrant'))
        self._text_zoom_percent: int = int(self._settings.get('text_zoom_percent', 110))
        self._app_bg_color: str = str(self._settings.get('app_bg_color', DEFAULT_APP_BG_COLOR) or DEFAULT_APP_BG_COLOR)
        self._app_surface_color: str = str(self._settings.get('app_surface_color', DEFAULT_APP_SURFACE_COLOR) or DEFAULT_APP_SURFACE_COLOR)
        self._app_border_color: str = str(self._settings.get('app_border_color', DEFAULT_APP_BORDER_COLOR) or DEFAULT_APP_BORDER_COLOR)
        self._app_text_color: str = str(self._settings.get('app_text_color', DEFAULT_APP_TEXT_COLOR) or DEFAULT_APP_TEXT_COLOR)
        self._app_accent_color: str = str(self._settings.get('app_accent_color', DEFAULT_APP_ACCENT_COLOR) or DEFAULT_APP_ACCENT_COLOR)
        self._app_hover_color: str = str(self._settings.get('app_hover_color', DEFAULT_APP_HOVER_COLOR) or DEFAULT_APP_HOVER_COLOR)
        # Apply the final stylesheet before creating child widgets to avoid
        # first-paint fallback styles.
        self.setStyleSheet(self._theme_with_text_zoom(DARK_STYLESHEET, dark_mode=True))
        base_pal = QPalette()
        base_pal.setColor(QPalette.Window, QColor(self._app_bg_color))
        base_pal.setColor(QPalette.WindowText, QColor(self._app_text_color))
        self.setPalette(base_pal)
        self.setAutoFillBackground(True)
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
        self._champion_splash_skin: int = int(self._settings.get('champion_splash_skin', 0))
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
        self._pending_rank_fetch_after_modal: bool = False
        self._window_size: str = self._settings.get('window_size', '800x600')
        self._window_size_mode: str = str(
            self._settings.get(
                'window_size_mode',
                'custom' if self._window_size not in SettingsDialog.COMMON_RESOLUTIONS else 'static',
            )
        ).strip().lower()
        if self._window_size_mode not in {'static', 'custom'}:
            self._window_size_mode = 'custom' if self._window_size not in SettingsDialog.COMMON_RESOLUTIONS else 'static'
        self._champ_select_window_size: str = str(
            self._settings.get('champ_select_window_size', SettingsDialog.CHAMP_SELECT_DEFAULT_RESOLUTION)
        )
        if self._champ_select_window_size == '1134x1200':
            # Migrate old default to new default while keeping user-selected custom values.
            self._champ_select_window_size = SettingsDialog.CHAMP_SELECT_DEFAULT_RESOLUTION
            self._settings['champ_select_window_size'] = self._champ_select_window_size
        self._in_champ_select_mode: bool = False
        self._last_screen_scale_factor: float = 1.0
        self._dpi_resize_in_progress: bool = False
        self._pre_champ_select_size: str = ""
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
        self._last_notified_match_id: Optional[str] = None
        self._ingame_watch_status: dict = {
            "watcher_active": False,
            "status": "idle",
            "summary": "Watcher idle",
            "timestamp": 0,
            "status_code": None,
            "response_bytes": 0,
            "error": "",
            "in_game": False,
            "in_champ_select": False,
            "queue_id": None,
            "queue_type": "",
            "game_phase": "",
            "last_game_result": "",
            "last_game_queue": "",
            "last_game_id": None,
            "last_game_timestamp": 0,
        }
        self._suppress_window_size_persistence = False
        if sys.platform.startswith("win"):
            self.setAttribute(Qt.WA_NativeWindow, True)
            self.create()
            _apply_windows11_chrome(self, self._dark_mode)
            self.setProperty("_chrome_preapplied", True)
            _arm_first_show_reveal(self)
        self.init_ui()
        app = QApplication.instance()
        if app:
            app.installEventFilter(self)
        self._configure_diagnostics_logging()
        self._create_tray_icon()
        self._apply_theme()
        self.ensurePolished()
        self.setUpdatesEnabled(True)
        self.repaint()
        self._session_sync_timer.start()
        self._update_rank_refresh_timer()
        self._reset_auto_lock_timer()
        if sys.platform.startswith("win"):
            # Continuous low-cost suppression for intermittent popup flashes.
            self._python_popup_guard_timer = QTimer(self)
            self._python_popup_guard_timer.setInterval(60)
            self._python_popup_guard_timer.timeout.connect(_hide_any_python_titled_window)
            self._python_popup_guard_timer.start()
        QTimer.singleShot(0, self.check_master_password)
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
        self._home_button = QPushButton("")
        self._home_button.setObjectName("homeIconButton")
        self._home_button.setFixedSize(26, 26)
        self._home_button.setAutoDefault(False)
        self._home_button.setDefault(False)
        self._home_button.setToolTip("Back to Home")
        self._home_button.setEnabled(False)
        self._home_button.clicked.connect(self._on_home_button_clicked)
        top_row.addWidget(self._home_button, 0, Qt.AlignVCenter)

        self._refresh_button = ClickableIconLabel()
        self._refresh_button.setObjectName("refreshIconButton")
        self._refresh_button.setFixedSize(26, 26)
        self._refresh_button.setAlignment(Qt.AlignCenter)
        self._refresh_button.setToolTip("Refresh UI")
        self._refresh_button.clicked.connect(self.refresh_ui)
        top_row.addWidget(self._refresh_button, 0, Qt.AlignVCenter)

        self._settings_button = QPushButton("")
        self._settings_button.setObjectName("settingsCogButton")
        self._settings_button.setFixedSize(26, 26)
        self._settings_button.setAutoDefault(False)
        self._settings_button.setDefault(False)
        self._settings_button.setToolTip("Open Settings")
        self._settings_button.clicked.connect(self.open_settings_dialog)
        top_row.addWidget(self._settings_button, 0, Qt.AlignVCenter)
        layout.addLayout(top_row)

        self._filter_row_widget = QWidget()
        filter_row = QHBoxLayout(self._filter_row_widget)
        filter_row.setContentsMargins(0, 0, 0, 0)
        filter_row.setSpacing(8)
        self._filters_label = QLabel("Filters:")
        filter_row.addWidget(self._filters_label)

        self.search_input = QLineEdit()
        self.search_input.setObjectName("accountSearchInput")
        self.search_input.setPlaceholderText("Search by display name, username, or tag")
        self.search_input.textChanged.connect(self._on_filters_changed)
        filter_row.addWidget(self.search_input, 1)

        self.tag_filter_combo = QComboBox()
        self.tag_filter_combo.setMinimumWidth(150)
        self.tag_filter_combo.currentIndexChanged.connect(self._on_filters_changed)
        filter_row.addWidget(self.tag_filter_combo)

        self.clear_filters_btn = QPushButton("Clear")
        self.clear_filters_btn.clicked.connect(self._clear_filters)
        filter_row.addWidget(self.clear_filters_btn)

        layout.addWidget(self._filter_row_widget)
        
        # Account list
        self._saved_accounts_label = QLabel("Saved Accounts:")
        layout.addWidget(self._saved_accounts_label)
        self.account_list_background = AccountListBackgroundFrame()
        self.account_list_background.setObjectName("accountListContainer")
        account_list_layout = QVBoxLayout(self.account_list_background)
        account_list_layout.setContentsMargins(0, 0, 0, 0)
        account_list_layout.setSpacing(0)
        self.account_list = QListWidget()
        self.account_list.setObjectName("accountListWidget")
        self.account_list.setSpacing(0)
        self.account_list.setViewportMargins(0, 0, 0, 0)
        self.account_list.setFrameShape(QFrame.NoFrame)
        self.account_list.setContentsMargins(0, 0, 0, 0)
        self.account_list.setStyleSheet(
            "QListWidget#accountListWidget { background: transparent; border: none; outline: none; }"
            "QListWidget#accountListWidget:focus { outline: none; }"
            "QListWidget#accountListWidget::item { background: transparent; border: none; margin: 0px; }"
            "QListWidget#accountListWidget::item:selected { background: transparent; border: none; }"
            "QListWidget#accountListWidget::item:selected:active { outline: none; }"
            "QListWidget#accountListWidget::item:hover { background: transparent; border: none; }"
        )
        self.account_list.setFocusPolicy(Qt.NoFocus)
        self.account_list.setAttribute(Qt.WA_TranslucentBackground, True)
        self.account_list.viewport().setAutoFillBackground(False)
        self.account_list.itemClicked.connect(self.on_account_selected)
        self.account_list.itemDoubleClicked.connect(lambda _: self.launch_account())
        self.account_list.itemSelectionChanged.connect(self.update_account_item_states)
        self.account_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.account_list.customContextMenuRequested.connect(self.show_account_context_menu)
        account_list_layout.addWidget(self.account_list)
        self.account_spotlight_panel = AccountSpotlightPanel()
        self.account_spotlight_panel.setParent(self.account_list_background)
        self.account_spotlight_panel.hide()
        self.game_info_panel = InClientGamePanel()
        self.main_area_stack = QStackedWidget()
        self.main_area_stack.addWidget(self.account_list_background)  # index 0: normal account list
        self.main_area_stack.addWidget(self.game_info_panel)          # index 1: in-client game panel
        layout.addWidget(self.main_area_stack)
        
        # Apply clipping mask to account list viewport
        self._apply_account_list_clipping_mask()
        
        # Button layout
        self._button_row_widget = QWidget()
        button_layout = QHBoxLayout(self._button_row_widget)
        button_layout.setContentsMargins(0, 0, 0, 0)
        
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
        
        layout.addWidget(self._button_row_widget)
        
        self.lol_path_label = QLabel()
        self.lol_path_label.setStyleSheet("color: #666666;")
        self.lol_path_label.setTextInteractionFlags(
            Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard
        )
        layout.addWidget(self.lol_path_label)
        self._refresh_lol_path_label()

        self._apply_account_list_background()
        
        central_widget.setLayout(layout)

        self._configure_icon_buttons()

    @staticmethod
    def _champion_splash_url(champion_id: str, skin_num: int = 0) -> str:
        skin = max(0, int(skin_num))
        return f"https://ddragon.leagueoflegends.com/cdn/img/champion/splash/{champion_id}_{skin}.jpg"

    def _load_champion_splash_pixmap(self, champion_id: str, skin_num: int = 0) -> Optional[QPixmap]:
        champ = str(champion_id or "").strip()
        if not champ or champ == SPLASH_THEME_AUTO:
            return None
        skin = max(0, int(skin_num))
        cache_key = f"{champ}:{skin}"
        cached = self._champion_splash_pixmap_cache.get(cache_key)
        if cached is not None:
            return cached
        try:
            req = Request(self._champion_splash_url(champ, skin), headers={"User-Agent": "lol-account-manager"})
            with urlopen(req, timeout=6) as resp:
                raw = resp.read()
            pix = QPixmap()
            if pix.loadFromData(raw):
                self._champion_splash_pixmap_cache[cache_key] = pix
                return pix
        except Exception:
            logging.debug("Failed loading champion splash for %s skin %s", champ, skin, exc_info=True)
        self._champion_splash_pixmap_cache[cache_key] = QPixmap()
        return None

    def _apply_account_list_clipping_mask(self):
        """Apply a rounded-rectangle clipping mask to the account list viewport."""
        if not hasattr(self, "account_list_background") or not hasattr(self, "account_list"):
            return
        
        def apply_clipping_mask():
            w = self.account_list_background.width()
            h = self.account_list_background.height()
            if w <= 0 or h <= 0:
                return

            # Create a bitmap mask with rounded corners, honoring device pixel ratio.
            dpr = max(1.0, self.account_list_background.devicePixelRatioF())
            mask_pixmap = QPixmap(int(w * dpr), int(h * dpr))
            mask_pixmap.setDevicePixelRatio(dpr)
            mask_pixmap.fill(Qt.color0)

            painter = QPainter(mask_pixmap)
            painter.setRenderHint(QPainter.Antialiasing, True)
            painter.setBrush(Qt.color1)
            painter.setPen(Qt.NoPen)
            inset = 1.0
            rect = QRectF(0.5 + inset, 0.5 + inset, w - (2 * inset) - 1.0, h - (2 * inset) - 1.0)
            painter.drawRoundedRect(rect, 9.0, 9.0)
            painter.end()

            # Apply as mask to background frame itself (not viewport)
            self.account_list_background.setMask(QBitmap(mask_pixmap))
        
        # Defer mask application until layout is finalized
        QTimer.singleShot(100, apply_clipping_mask)
        
        # Re-apply mask on container resize.
        # Use installEventFilter instead of monkey-patching resizeEvent: PyQt5
        # dispatches virtual methods via the C++ vtable which ignores Python
        # instance attributes, so a plain assignment never fires.
        if not hasattr(self, '_bg_resize_filter'):
            self._bg_resize_filter = _ResizeCallbackFilter(
                lambda: QTimer.singleShot(50, apply_clipping_mask), self
            )
            self.account_list_background.installEventFilter(self._bg_resize_filter)

        # Update spotlight item height whenever account_list itself resizes
        # (e.g. when filter/button rows are hidden and the list grows taller).
        if not hasattr(self, '_list_resize_filter'):
            self._list_resize_filter = _ResizeCallbackFilter(
                lambda: QTimer.singleShot(0, self._update_spotlight_size_hint), self
            )
            self.account_list.installEventFilter(self._list_resize_filter)

    def _apply_account_list_background(self):
        if not hasattr(self, "account_list_background"):
            return
        self.account_list_background.set_dark_mode(self._dark_mode)
        self.account_list_background.set_base_color(self._app_surface_color)
        pixmap = None
        if self._champion_splash_enabled:
            pixmap = self._load_champion_splash_pixmap(self._champion_splash_champion, self._champion_splash_skin)
        self.account_list_background.set_background(
            enabled=self._champion_splash_enabled and bool(pixmap and not pixmap.isNull()),
            pixmap=pixmap,
            opacity=self._champion_splash_opacity,
            edge_fade=self._champion_splash_edge_fade,
            inner_fade=self._champion_splash_inner_fade,
        )
        if self.game_info_panel:
            self.game_info_panel.set_dark_mode(self._dark_mode)
            self.game_info_panel.set_base_color(self._app_surface_color)
        if self.account_spotlight_panel:
            self.account_spotlight_panel.set_dark_mode(self._dark_mode)
            self.account_spotlight_panel.set_base_color(self._app_surface_color)

    def _apply_window_size(self, resolution: str):
        """Resize the window without treating it as a user-initiated custom resize."""
        width, height = _parse_resolution(resolution, fallback=(660, 480))
        self._suppress_window_size_persistence = True
        try:
            self.resize(width, max(480, height))
        finally:
            self._suppress_window_size_persistence = False

    def _current_screen_scale_factor(self) -> float:
        """Return current monitor scale factor (1.0 == 100% Windows scaling)."""
        screen = None
        handle = self.windowHandle()
        if handle is not None:
            try:
                screen = handle.screen()
            except Exception:
                screen = None
        if screen is None:
            try:
                screen = QApplication.screenAt(self.frameGeometry().center())
            except Exception:
                screen = None
        if screen is None:
            screen = QApplication.primaryScreen()
        if screen is None:
            return 1.0

        try:
            dpi = float(screen.logicalDotsPerInch())
        except Exception:
            dpi = 96.0
        if dpi <= 0:
            dpi = 96.0

        return max(1.0, min(2.0, dpi / 96.0))

    def _apply_champ_select_window_size(self):
        """Apply champ-select size scaled for the monitor's DPI setting."""
        base_w, base_h = _parse_resolution(self._champ_select_window_size, fallback=(941, 1053))
        scale = self._current_screen_scale_factor()
        self._last_screen_scale_factor = scale
        width = max(660, int(round(base_w * scale)))
        height = max(480, int(round(base_h * scale)))

        self._suppress_window_size_persistence = True
        try:
            self.resize(width, height)
            
            # If secondary monitor setting is enabled, move window to secondary monitor
            if self._champ_select_secondary_monitor:
                screens = QApplication.screens()
                if len(screens) > 1:
                    # Move to second screen (index 1)
                    secondary_screen = screens[1]
                    screen_geo = secondary_screen.geometry()
                    # Center window on secondary screen
                    new_x = screen_geo.x() + (screen_geo.width() - width) // 2
                    new_y = screen_geo.y() + (screen_geo.height() - height) // 2
                    self.move(new_x, new_y)
        finally:
            self._suppress_window_size_persistence = False

    def _maybe_reapply_layout_for_dpi(self):
        """Re-apply active layout dimensions after crossing into another monitor scale."""
        if not hasattr(self, "_dpi_resize_in_progress"):
            self._dpi_resize_in_progress = False
        if not hasattr(self, "_last_screen_scale_factor"):
            self._last_screen_scale_factor = self._current_screen_scale_factor()

        if self._dpi_resize_in_progress:
            return

        current_scale = self._current_screen_scale_factor()
        if abs(current_scale - self._last_screen_scale_factor) < 0.01:
            return

        self._dpi_resize_in_progress = True
        try:
            self._last_screen_scale_factor = current_scale
            if self._in_champ_select_mode:
                self._apply_champ_select_window_size()
            else:
                self._apply_account_list_scale(current_scale)
        finally:
            self._dpi_resize_in_progress = False

    def _enter_champ_select_mode(self):
        """Resize window and hide home-page UI elements for champ select."""
        if self._in_champ_select_mode:
            return
        self._in_champ_select_mode = True
        self._pre_champ_select_size = f"{self.width()}x{self.height()}"
        self._last_screen_scale_factor = self._current_screen_scale_factor()
        self._apply_champ_select_window_size()
        self._filter_row_widget.hide()
        self._saved_accounts_label.hide()
        self._button_row_widget.hide()
        self.lol_path_label.hide()
        # Bring the app window to the foreground
        self.activateWindow()
        self.raise_()

    def _exit_champ_select_mode(self):
        """Restore window size and show home-page UI elements after champ select."""
        if not self._in_champ_select_mode:
            return
        self._in_champ_select_mode = False
        restore = self._pre_champ_select_size or self._window_size
        self._pre_champ_select_size = ""
        self._apply_window_size(restore)
        self._apply_account_list_scale(self._current_screen_scale_factor())
        self._filter_row_widget.show()
        self._saved_accounts_label.show()
        self._button_row_widget.show()
        self.lol_path_label.show()
        self.update_account_item_states()

    def _build_ugg_profile_overview_url(self, account: Account) -> str:
        """Build u.gg profile overview URL for the given account."""
        region_code = str(getattr(account, "region", "NA") or "NA").upper()
        region_map = {
            "NA": "na1",
            "EUW": "euw1",
            "EUNE": "eun1",
            "KR": "kr",
            "LAN": "la1",
            "LAS": "la2",
            "BR": "br1",
            "JP": "jp1",
            "OCE": "oc1",
            "TR": "tr1",
            "RU": "ru",
            "ME": "me1",
            "PH": "ph2",
            "SG": "sg2",
            "TH": "th2",
            "TW": "tw2",
            "VN": "vn2",
        }
        region_id = region_map.get(region_code, region_code.lower())
        display_name = (getattr(account, "display_name", "") or "").strip() or account.username
        tag_line = (getattr(account, "tag_line", "") or "NA1").strip() or "NA1"
        encoded_name = quote(display_name, safe="")
        encoded_tag = quote(tag_line.lower(), safe="")
        return f"https://u.gg/lol/profile/{region_id}/{encoded_name}-{encoded_tag}/overview"

    def _show_logged_in_spotlight(self):
        """Ensure the spotlight panel is in the list directly after the logged-in
        account row and has up-to-date content.  Safe to call at any time."""
        if self._in_champ_select_mode:
            return
        if getattr(self, '_spotlight_user_dismissed', False):
            return
        if not (self.account_manager and self._logged_in_username):
            return
        if not self._ensure_spotlight_panel():
            return

        account = self.account_manager.get_account(self._logged_in_username)
        if not account:
            return

        # Find the logged-in account row and check if spotlight is already
        # sitting right after it.
        logged_in_row = -1
        spotlight_already_placed = False
        for index in range(self.account_list.count()):
            item = self.account_list.item(index)
            if self.account_list.itemWidget(item) is self.account_spotlight_panel:
                spotlight_already_placed = True
                break
            if item.data(Qt.UserRole) == account.username:
                logged_in_row = index

        if not spotlight_already_placed:
            if logged_in_row < 0:
                # Logged-in account is not currently visible in the list.
                return
            # Re-parent away from any previous owner so Qt won't delete it
            # when insertItem triggers internal housekeeping.
            self.account_spotlight_panel.setParent(self.account_list_background)
            spotlight_item = QListWidgetItem()
            spotlight_item.setFlags(Qt.NoItemFlags)
            spotlight_item.setSizeHint(QSize(0, 480))
            self.account_list.insertItem(logged_in_row + 1, spotlight_item)
            self.account_list.setItemWidget(spotlight_item, self.account_spotlight_panel)

        self.account_spotlight_panel.show()
        self._enter_spotlight_ui_mode()
        # Safety fallback: list resize event fires instantly if the viewport grew,
        # but add shots at 50 ms and 300 ms in case the layout settles later.
        QTimer.singleShot(50, self._update_spotlight_size_hint)
        QTimer.singleShot(300, self._update_spotlight_size_hint)

        profile_url = self._build_ugg_profile_overview_url(account)
        rank_data = self._rank_data_by_username.get(account.username, {})
        self.account_spotlight_panel.set_account(account, rank_data, profile_url)
        QTimer.singleShot(200, self._update_webview_zoom)

        # Keep the logged-in account row selected.
        for index in range(self.account_list.count()):
            item = self.account_list.item(index)
            if item.data(Qt.UserRole) == account.username:
                if self.account_list.currentItem() is not item:
                    self.account_list.setCurrentItem(item)
                break

    def _update_spotlight_size_hint(self):
        """Resize the spotlight list item so it fills the viewport height.
        Setting height = full list height ensures that, once the account
        row above is scrolled to the top, all rows below the spotlight are
        pushed off-screen regardless of any spacing/DPI differences."""
        try:
            if not self.account_spotlight_panel:
                return
            # Use the list widget height (more reliable than viewport() which may
            # lag behind layout changes by one event-loop iteration).
            list_h = self.account_list.height()
            if list_h <= 0:
                return
            new_h = max(380, list_h)
            for index in range(self.account_list.count()):
                item = self.account_list.item(index)
                if self.account_list.itemWidget(item) is self.account_spotlight_panel:
                    # Always apply — skip-guard can silently miss a post-restore
                    # resize when account_list.height() hasn't settled yet.
                    item.setSizeHint(QSize(0, new_h))
                    self.account_spotlight_panel.setMinimumHeight(new_h)
                    self.account_spotlight_panel.setMaximumHeight(new_h)
                    self.account_list.doItemsLayout()
                    self.account_list.viewport().update()
                    # Restore scroll position that doItemsLayout resets.
                    if index > 0:
                        row_above = self.account_list.item(index - 1)
                        if row_above:
                            self.account_list.scrollToItem(
                                row_above, self.account_list.PositionAtTop
                            )
                    break
        except RuntimeError:
            # C++ object deleted before the deferred timer fired.
            self.account_spotlight_panel = None

    def _on_home_button_clicked(self):
        """Exit spotlight mode and return to the normal home view."""
        if not self.account_spotlight_panel:
            return
        # Suppress auto-reshow until the logged-in account changes
        self._spotlight_user_dismissed = True
        # Remove the spotlight list item without triggering a full list rebuild
        for index in range(self.account_list.count()):
            item = self.account_list.item(index)
            if self.account_list.itemWidget(item) is self.account_spotlight_panel:
                # Re-parent BEFORE takeItem so Qt doesn't delete the widget
                self.account_spotlight_panel.setParent(self.account_list_background)
                self.account_spotlight_panel.hide()
                self.account_list.takeItem(index)
                break
        self._exit_spotlight_ui_mode()

    def _enter_spotlight_ui_mode(self):
        """Hide filters, bottom buttons and main scrollbar while spotlight is visible."""
        self._filter_row_widget.hide()
        self._button_row_widget.hide()
        self.lol_path_label.hide()
        self.account_list.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._home_button.setEnabled(True)
        self._set_icon_state(self._home_button, "normal")

    def _exit_spotlight_ui_mode(self):
        """Restore filters, bottom buttons and scrollbar when spotlight is hidden."""
        self._filter_row_widget.show()
        self._button_row_widget.show()
        self.lol_path_label.show()
        self.account_list.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._home_button.setEnabled(False)
        self._set_icon_state(self._home_button, "normal")
        # Release the fixed-height constraint set during spotlight sizing
        if self.account_spotlight_panel:
            try:
                self.account_spotlight_panel.setMinimumHeight(420)
                self.account_spotlight_panel.setMaximumHeight(16777215)  # QWIDGETSIZE_MAX
            except RuntimeError:
                pass

    def _update_webview_zoom(self):
        """Zoom the embedded webview based on window state."""
        try:
            if not (self.account_spotlight_panel and self.account_spotlight_panel.isVisible()):
                return
            web_view = self.account_spotlight_panel._web_view
            if web_view is None:
                return
            zoom = 1.3 if (self.isMaximized() or self.isFullScreen()) else 1.0
            web_view.setZoomFactor(zoom)
        except RuntimeError:
            # C++ object already deleted (panel or webview was closed before timer fired)
            pass

    def _reapply_ugg_embed_css(self):
        """Dispatch resize event to trigger u.gg's responsive layout."""
        try:
            if not (self.account_spotlight_panel and self.account_spotlight_panel.isVisible()):
                return
            if self.account_spotlight_panel._web_view is not None:
                # Only dispatch resize - don't re-apply CSS which breaks layout
                js = r"""
window.dispatchEvent(new Event('resize', { bubbles: true }));
"""
                self.account_spotlight_panel._web_view.page().runJavaScript(js)
        except RuntimeError:
            pass

    def _persist_window_size(self):
        """Persist the current window size as the custom startup size."""
        if self.isMaximized() or self.isFullScreen():
            return
        if self._in_champ_select_mode:
            return
        current_resolution = f"{self.width()}x{self.height()}"
        self._window_size = current_resolution
        self._window_size_mode = 'custom'
        self._settings['window_size'] = current_resolution
        self._settings['window_size_mode'] = 'custom'
        save_settings(self._settings)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Update spotlight size on every resize (manual drag or maximize/restore).
        # Fire at 10 ms (fast) and 300 ms (safety net after slow layout settle).
        QTimer.singleShot(10, self._update_spotlight_size_hint)
        QTimer.singleShot(300, self._update_spotlight_size_hint)
        # After a window-state change, Qt issues an extra resize; use it to
        # reapply zoom and CSS for the new dimensions.
        if getattr(self, '_should_reapply_css_on_resize', False):
            QTimer.singleShot(50, self._update_webview_zoom)
            QTimer.singleShot(150, self._reapply_ugg_embed_css)
            self._should_reapply_css_on_resize = False
        if self._suppress_window_size_persistence:
            return
        if self.isMaximized() or self.isFullScreen():
            return
        if self._in_champ_select_mode:
            return
        self._window_size_mode = 'custom'
        self._window_resize_save_timer.start()

    def moveEvent(self, event):
        super().moveEvent(event)
        self._maybe_reapply_layout_for_dpi()

    def changeEvent(self, event):
        super().changeEvent(event)
        
        # Re-run the u.gg embed CSS when window is maximized/restored
        if event.type() == QEvent.WindowStateChange:
            # Skip spotlight size shots when the window is being *minimized*:
            # account_list.height() is unreliable while the window is iconified
            # on some compositors, and no visible update is needed anyway.
            # The shots below will still fire when the window is restored.
            is_minimizing = bool(self.windowState() & Qt.WindowMinimized)
            if not is_minimizing:
                QTimer.singleShot(100, self._update_spotlight_size_hint)
                QTimer.singleShot(500, self._update_spotlight_size_hint)  # safety net
            QTimer.singleShot(200, self._update_webview_zoom)
            QTimer.singleShot(300, self._reapply_ugg_embed_css)
            # Set flag to trigger additional CSS reapply on next resize
            self._should_reapply_css_on_resize = True
        
        screen_change_type = getattr(QEvent, "ScreenChangeInternal", None)
        if (
            screen_change_type is not None
            and event.type() == screen_change_type
            and self._in_champ_select_mode
        ):
            QTimer.singleShot(80, self._apply_champ_select_window_size)
        else:
            self._maybe_reapply_layout_for_dpi()

    def toggle_theme(self):
        """Force dark mode."""
        self._dark_mode = True
        self._apply_theme()

    def _theme_with_text_zoom(self, base: str, dark_mode: bool) -> str:
        """Merge base theme with text zoom scaling."""
        point_size = max(8, int(round(9 * self._text_zoom_percent / 100)))
        app_bg = self._sanitize_color(self._app_bg_color, DEFAULT_APP_BG_COLOR)
        app_surface = self._sanitize_color(self._app_surface_color, DEFAULT_APP_SURFACE_COLOR)
        app_border = self._sanitize_color(self._app_border_color, DEFAULT_APP_BORDER_COLOR)
        app_text = self._sanitize_color(self._app_text_color, DEFAULT_APP_TEXT_COLOR)
        app_accent = self._sanitize_color(self._app_accent_color, DEFAULT_APP_ACCENT_COLOR)
        app_hover = self._sanitize_color(self._app_hover_color, DEFAULT_APP_HOVER_COLOR)
        accent_text = self._contrast_text_color(app_accent)
        # When the accent is very dark, app_text (cool-tinted) contrasts better than
        # pure #ffffff, which appears warm/yellow next to cool-tinted labels.
        accent_color_obj = QColor(app_accent)
        accent_lum = (0.2126 * accent_color_obj.redF()
                      + 0.7152 * accent_color_obj.greenF()
                      + 0.0722 * accent_color_obj.blueF())
        button_text = app_text if accent_lum < 0.25 else accent_text
        placeholder = self._placeholder_color(app_text)
        cog_bg = app_surface
        cog_fg = app_text
        cog_border = app_border
        cog_hover = app_accent
        cog_pressed = app_border
        cog_focus = app_border
        list_border = app_border
        search_fg = app_text
        search_bg = app_surface
        search_border = app_border
        search_placeholder = placeholder
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
            + "    min-width: 26px;\n"
            + "    max-width: 26px;\n"
            + "    min-height: 26px;\n"
            + "    max-height: 26px;\n"
            + "    background-color: transparent;\n"
            + f"    color: {cog_fg};\n"
            + "    border: none;\n"
            + "    border-radius: 0px;\n"
            + "    padding: 0px;\n"
            + "    font-size: 15px;\n"
            + "    font-weight: 400;\n"
            + "    margin: 0px;\n"
            + "    text-align: center;\n"
            + "}\n"
            + "QPushButton#settingsCogButton:hover {\n"
            + f"    color: {accent_text};\n"
            + "}\n"
            + "QPushButton#settingsCogButton:pressed {\n"
            + f"    color: {cog_pressed};\n"
            + "}\n"
            + "QPushButton#settingsCogButton:focus {\n"
            + "    outline: none;\n"
            + "    border: none;\n"
            + "}\n"
            + "QToolButton#refreshIconButton {\n"
            + "    min-width: 26px;\n"
            + "    max-width: 26px;\n"
            + "    min-height: 26px;\n"
            + "    max-height: 26px;\n"
            + "    background-color: transparent;\n"
            + f"    color: {cog_fg};\n"
            + "    border: none;\n"
            + "    border-radius: 0px;\n"
            + "    padding: 0px;\n"
            + "    font-size: 15px;\n"
            + "    font-weight: 400;\n"
            + "    margin: 0px;\n"
            + "    text-align: center;\n"
            + "}\n"
            + "QToolButton#refreshIconButton:hover {\n"
            + f"    color: {accent_text};\n"
            + "}\n"
            + "QToolButton#refreshIconButton:focus {\n"
            + "    outline: none;\n"
            + "    border: none;\n"
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
            + "    border-radius: 10px;\n"
            + "    background: transparent;\n"
            + "}\n"
            + "QListWidget#accountListWidget {\n"
            + "    background: transparent;\n"
            + "    border: none;\n"
            + "}\n"
            + "QMainWindow, QDialog, QWidget {\n"
            + f"    background-color: {app_bg};\n"
            + f"    color: {app_text};\n"
            + "}\n"
            + "QListWidget {\n"
            + f"    background-color: {app_surface};\n"
            + f"    border: 1px solid {app_border};\n"
            + "}\n"
            + "QPushButton {\n"
            + f"    background-color: {app_accent};\n"
            + f"    color: {button_text};\n"
            + f"    border: 1px solid {app_border};\n"
            + "}\n"
            + "QPushButton:hover {\n"
            + f"    background-color: {app_hover};\n"
            + "}\n"
            + "QPushButton:pressed {\n"
            + f"    background-color: {app_accent};\n"
            + "}\n"
            + "QPushButton:disabled {\n"
            + f"    background-color: {app_surface};\n"
            + f"    color: {app_border};\n"
            + f"    border: 1px solid {app_border};\n"
            + "}\n"
            + "QLineEdit, QComboBox, QDateEdit, QTextEdit, QPlainTextEdit, QSpinBox {\n"
            + f"    background-color: {app_surface};\n"
            + f"    color: {app_text};\n"
            + f"    border: 1px solid {app_border};\n"
            + "}\n"
            + "QComboBox {\n"
            + "    padding-right: 24px;\n"
            + "}\n"
            + "QComboBox::drop-down {\n"
            + "    subcontrol-origin: padding;\n"
            + "    subcontrol-position: top right;\n"
            + "    width: 20px;\n"
            + f"    border-left: 1px solid {app_border};\n"
            + f"    background-color: {app_surface};\n"
            + "}\n"
            + "QComboBox QAbstractItemView {\n"
            + f"    background-color: {app_surface};\n"
            + f"    color: {app_text};\n"
            + "}\n"
            + "QTabWidget::pane {\n"
            + f"    border: 1px solid {app_border};\n"
            + f"    background-color: {app_bg};\n"
            + "}\n"
            + "QTabBar::tab {\n"
            + f"    background-color: {app_surface};\n"
            + f"    color: {app_text};\n"
            + f"    border: 1px solid {app_border};\n"
            + "}\n"
            + "QTabBar::tab:selected {\n"
            + f"    background-color: {app_bg};\n"
            + f"    color: {app_text};\n"
            + "}\n"
        )

    def _apply_theme(self):
        """Apply the current theme stylesheet."""
        self.setStyleSheet(self._theme_with_text_zoom(DARK_STYLESHEET, dark_mode=True))

        # Palette fallback prevents first-paint placeholder/text color glitches on some Windows setups.
        self._apply_filter_input_palette()
        QTimer.singleShot(0, self._apply_filter_input_palette)
        self._apply_account_list_background()

        self.update_account_item_states()
        if self._tray_menu:
            self._tray_menu.setStyleSheet(self._tray_menu_stylesheet())
        # Delay icon refresh to ensure stylesheet is fully applied
        QTimer.singleShot(10, self._refresh_icon_buttons)

    def refresh_ui(self):
        """Force a refresh of UI styling and list visuals."""
        QTimer.singleShot(0, self._perform_refresh_ui)

    def _perform_refresh_ui(self):
        # Refresh button should not force a full stylesheet reapply.
        _hide_any_python_titled_window()
        self._apply_account_list_background()
        self.update_account_item_states()
        self.refresh_account_list(fetch_ranks=True)
        self._set_refresh_icon_normal()
        # Burst suppression to catch delayed popup creation.
        QTimer.singleShot(25, _hide_any_python_titled_window)
        QTimer.singleShot(75, _hide_any_python_titled_window)
        QTimer.singleShot(150, _hide_any_python_titled_window)

    def _configure_icon_buttons(self):
        self._icon_buttons = {
            self._home_button: "home",
            self._settings_button: "settings",
        }
        self._settings_icon_latched = False
        self._set_refresh_icon_normal()
        self._refresh_button.setCursor(Qt.PointingHandCursor)
        self._refresh_button.installEventFilter(self)
        for button in self._icon_buttons:
            button.setText("")
            button.setIconSize(QSize(24, 24))
            button.setFocusPolicy(Qt.NoFocus)
            button.setCursor(Qt.PointingHandCursor)
            button.installEventFilter(self)
        # Set initial icons
        for button in self._icon_buttons:
            self._set_icon_state(button, "normal")

    def _set_refresh_icon_normal(self):
        icon = self._build_custom_icon("refresh", self._sanitize_color(self._app_text_color, DEFAULT_APP_TEXT_COLOR), 24)
        if icon:
            self._refresh_button.setPixmap(icon.pixmap(24, 24))

    def _set_refresh_icon_hover(self):
        icon = self._build_custom_icon("refresh", self._sanitize_color(self._app_accent_color, DEFAULT_APP_ACCENT_COLOR), 24)
        if icon:
            self._refresh_button.setPixmap(icon.pixmap(24, 24))

    def _refresh_icon_buttons(self):
        self._set_refresh_icon_normal()
        for button in getattr(self, "_icon_buttons", {}):
            if button is self._settings_button and getattr(self, "_settings_icon_latched", False):
                self._set_icon_state(button, "pressed")
            else:
                self._set_icon_state(button, "hover" if button.underMouse() else "normal")
        # Clean stylesheet for icon buttons
        self._refresh_button.setStyleSheet("background-color: transparent; border: none; padding: 0px; margin: 0px;")
        self._home_button.setStyleSheet(
            "QPushButton { background-color: transparent; border: none; padding: 0px; margin: 0px; }"
        )
        self._settings_button.setStyleSheet(
            "QPushButton { background-color: transparent; border: none; padding: 0px; margin: 0px; }"
        )

    def _sync_icon_button_state(self, button: QPushButton):
        if button is self._settings_button and getattr(self, "_settings_icon_latched", False):
            self._set_icon_state(button, "pressed")
            return
        self._set_icon_state(button, "hover" if button.underMouse() else "normal")

    def _sync_refresh_button_state(self):
        self._set_icon_state(self._refresh_button, "normal")

    def _set_icon_state(self, button: QPushButton, state: str):
        icon_type = self._icon_buttons.get(button)
        if not icon_type:
            return
        
        app_text = self._sanitize_color(self._app_text_color, DEFAULT_APP_TEXT_COLOR)
        app_accent = self._sanitize_color(self._app_accent_color, DEFAULT_APP_ACCENT_COLOR)
        app_border = self._sanitize_color(self._app_border_color, DEFAULT_APP_BORDER_COLOR)
        
        if state == "pressed" and button is self._settings_button:
            color = app_border
        elif state == "hover":
            color = app_accent
        else:
            color = app_text
        
        icon = self._build_custom_icon(icon_type, color, 24)
        if icon:
            if hasattr(button, "setPixmap"):
                button.setPixmap(icon.pixmap(24, 24))
            else:
                button.setIcon(icon)

    def _build_custom_icon(self, icon_type: str, color_hex: str, size: int) -> Optional[QIcon]:
        """Build minimalistic custom icons using Qt painting."""
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setPen(Qt.NoPen)
        
        color = QColor(color_hex)
        painter.setBrush(color)
        
        if icon_type == "refresh":
            # Draw circular arrow (refresh icon)
            self._draw_refresh_icon(painter, size, color)
        elif icon_type == "settings":
            # Draw gear (settings icon)
            self._draw_settings_icon(painter, size, color)
        elif icon_type == "home":
            self._draw_home_icon(painter, size, color)
        
        painter.end()
        return QIcon(pixmap)
    
    def _draw_refresh_icon(self, painter: QPainter, size: int, color: QColor):
        """Draw a minimalistic refresh/reload icon."""
        painter.setBrush(color)
        painter.setPen(Qt.NoPen)
        
        center_x = size / 2
        center_y = size / 2
        radius = size / 3.5
        line_width = size / 8
        
        # Draw circular arrow
        pen = QPen(color, line_width, Qt.SolidLine)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        
        # Draw curved path (3/4 of circle)
        path = QPainterPath()
        angle_start = 45
        angle_span = 270
        arc_rect = QRectF(center_x - radius, center_y - radius, radius * 2, radius * 2)
        path.arcMoveTo(arc_rect, angle_start)
        path.arcTo(arc_rect, angle_start, angle_span)
        painter.drawPath(path)
        
        # Draw arrow head
        arrow_size = size / 5
        arrow_angle = 315  # degrees
        arrow_x = center_x + radius * math.cos(math.radians(arrow_angle))
        arrow_y = center_y + radius * math.sin(math.radians(arrow_angle))
        
        arrow_path = QPainterPath()
        arrow_path.moveTo(arrow_x, arrow_y)
        arrow_path.lineTo(arrow_x - arrow_size/2, arrow_y - arrow_size/2)
        arrow_path.lineTo(arrow_x - arrow_size/3, arrow_y + arrow_size/3)
        arrow_path.closeSubpath()
        
        painter.setBrush(color)
        painter.setPen(Qt.NoPen)
        painter.drawPath(arrow_path)

    def _draw_home_icon(self, painter: QPainter, size: int, color: QColor):
        """Draw a minimalistic house/home icon."""
        painter.setBrush(color)
        painter.setPen(Qt.NoPen)
        m = size / 24.0  # scale factor (designed on 24px grid)

        # Roof triangle
        roof = QPainterPath()
        roof.moveTo(12 * m, 2 * m)   # apex
        roof.lineTo(22 * m, 11 * m)  # right eave
        roof.lineTo(2  * m, 11 * m)  # left eave
        roof.closeSubpath()
        painter.drawPath(roof)

        # House body (rectangle below roof)
        body_x = 5 * m
        body_y = 11 * m
        body_w = 14 * m
        body_h = 10 * m
        painter.drawRect(QRectF(body_x, body_y, body_w, body_h))

        # Door cutout (punch out with background colour so it looks like a door)
        door_w = 5 * m
        door_h = 6 * m
        door_x = (size - door_w) / 2
        door_y = 21 * m - door_h
        bg = painter.background().color()
        # Use transparent to cut out the door opening
        painter.setBrush(Qt.transparent)
        painter.setCompositionMode(QPainter.CompositionMode_Clear)
        painter.drawRect(QRectF(door_x, door_y, door_w, door_h))
        painter.setCompositionMode(QPainter.CompositionMode_SourceOver)

    def _draw_settings_icon(self, painter: QPainter, size: int, color: QColor):
        """Draw a minimalistic settings/gear icon."""
        painter.setBrush(color)
        painter.setPen(Qt.NoPen)
        
        center_x = size / 2
        center_y = size / 2
        outer_radius = size / 2.5
        inner_radius = size / 5
        tooth_depth = size / 6
        num_teeth = 8
        
        # Draw gear teeth
        path = QPainterPath()
        
        for i in range(num_teeth * 2):
            angle = (i * 360 / (num_teeth * 2)) * math.pi / 180
            if i % 2 == 0:
                # Outer tooth
                r = outer_radius
            else:
                # Inner gap
                r = outer_radius - tooth_depth
            
            x = center_x + r * math.cos(angle)
            y = center_y + r * math.sin(angle)
            
            if i == 0:
                path.moveTo(x, y)
            else:
                path.lineTo(x, y)
        
        path.closeSubpath()
        painter.drawPath(path)
        
        # Draw center circle
        center_circle = QPainterPath()
        center_circle.addEllipse(QRectF(
            center_x - inner_radius,
            center_y - inner_radius,
            inner_radius * 2,
            inner_radius * 2
        ))
        
        painter.setBrush(QColor("#1e1e2e"))  # Background color
        painter.drawPath(center_circle)

    def eventFilter(self, obj, event):
        if obj is self._refresh_button:
            if event.type() == QEvent.Enter:
                self._set_refresh_icon_hover()
            elif event.type() == QEvent.Leave:
                self._set_refresh_icon_normal()
            elif event.type() == QEvent.MouseButtonRelease:
                self._set_refresh_icon_hover() if self._refresh_button.underMouse() else self._set_refresh_icon_normal()
            return super().eventFilter(obj, event)

        if obj in getattr(self, "_icon_buttons", {}):
            if event.type() == QEvent.MouseButtonPress:
                if obj is self._settings_button:
                    self._set_icon_state(obj, "pressed")
            elif event.type() == QEvent.MouseButtonRelease:
                self._sync_icon_button_state(obj)
            elif event.type() == QEvent.Enter:
                if obj is self._settings_button and getattr(self, "_settings_icon_latched", False):
                    self._set_icon_state(obj, "pressed")
                elif not obj.isDown():
                    self._set_icon_state(obj, "hover")
            elif event.type() == QEvent.Leave:
                self._sync_icon_button_state(obj)
        return super().eventFilter(obj, event)

    def _apply_filter_input_palette(self):
        """Apply stable text/placeholder colors for filter controls."""
        if not hasattr(self, "search_input"):
            return

        search_palette = self.search_input.palette()
        combo_palette = self.tag_filter_combo.palette()

        base_color = QColor(self._sanitize_color(self._app_surface_color, DEFAULT_APP_SURFACE_COLOR))
        text_color = QColor(self._sanitize_color(self._app_text_color, DEFAULT_APP_TEXT_COLOR))
        placeholder_color = QColor(text_color)
        placeholder_color.setAlpha(150)
        search_palette.setColor(QPalette.Base, base_color)
        search_palette.setColor(QPalette.Text, text_color)
        search_palette.setColor(QPalette.PlaceholderText, placeholder_color)
        combo_palette.setColor(QPalette.Base, base_color)
        combo_palette.setColor(QPalette.Text, text_color)
        combo_palette.setColor(QPalette.ButtonText, text_color)

        self.search_input.setPalette(search_palette)
        self.tag_filter_combo.setPalette(combo_palette)

    def _sanitize_color(self, value: str, fallback: str) -> str:
        candidate = QColor(str(value or "").strip())
        if not candidate.isValid():
            return fallback
        return candidate.name()

    def _contrast_text_color(self, value: str) -> str:
        candidate = QColor(str(value or "").strip())
        if not candidate.isValid():
            candidate = QColor("#000000")
        luminance = 0.2126 * candidate.redF() + 0.7152 * candidate.greenF() + 0.0722 * candidate.blueF()
        return "#111111" if luminance > 0.6 else "#ffffff"

    def _placeholder_color(self, value: str) -> str:
        candidate = QColor(str(value or "").strip())
        if not candidate.isValid():
            candidate = QColor(DEFAULT_APP_TEXT_COLOR)
        candidate.setAlpha(150)
        return f"rgba({candidate.red()}, {candidate.green()}, {candidate.blue()}, {candidate.alpha()})"

    def open_settings_dialog(self):
        """Open the settings dialog and apply any changes."""
        dialog_settings = dict(self._settings)
        dialog_settings['current_window_size'] = f"{self.width()}x{self.height()}"
        dialog = SettingsDialog(
            self,
            settings=dialog_settings,
            apply_callback=self._apply_settings_values,
        )
        dialog.ensurePolished()
        if sys.platform.startswith("win"):
            dialog.create()
            _apply_windows11_chrome(dialog, self._dark_mode)
        self._settings_icon_latched = True
        self._set_icon_state(self._settings_button, "pressed")

        def _on_settings_finished(result: int):
            try:
                if result == QDialog.Accepted and getattr(dialog, "_save_requested", False):
                    self._apply_settings_values(dialog.get_values())
            finally:
                self._settings_icon_latched = False
                self._sync_icon_button_state(self._settings_button)
                if self._pending_rank_fetch_after_modal and not QApplication.activeModalWidget():
                    self._pending_rank_fetch_after_modal = False
                    QTimer.singleShot(0, lambda: self.refresh_account_list(fetch_ranks=True))
                dialog.deleteLater()

        dialog.finished.connect(_on_settings_finished)
        dialog.open()

    def _apply_settings_values(self, values: dict, persist: bool = True):
        """Apply settings values to runtime state and persist them."""
        _hide_any_python_titled_window()
        theme_before = (
            self._text_zoom_percent,
            self._app_bg_color,
            self._app_surface_color,
            self._app_border_color,
            self._app_text_color,
            self._app_accent_color,
            self._app_hover_color,
            self._hover_highlight_color_setting,
            self._logged_in_gradient_color,
            self._logged_in_gradient_intensity,
            self._logged_in_border_width,
            self._logged_in_border_opacity,
            self._champion_splash_enabled,
            self._champion_splash_champion,
            self._champion_splash_skin,
            self._champion_splash_opacity,
            self._row_density,
            self._tag_size,
            self._tag_chip_style,
            self._rank_icon_size,
            self._rank_text_brightness,
            self._show_rank_images,
            self._show_tags,
        )

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
        self._champ_select_secondary_monitor = bool(values.get('champ_select_secondary_monitor', False))
        self._tag_size = str(values['tag_size'])
        self._tag_chip_style = str(values.get('tag_chip_style', self._tag_chip_style))
        self._text_zoom_percent = int(values['text_zoom_percent'])
        self._app_bg_color = str(values.get('app_bg_color', self._app_bg_color) or self._app_bg_color)
        self._app_surface_color = str(values.get('app_surface_color', self._app_surface_color) or self._app_surface_color)
        self._app_border_color = str(values.get('app_border_color', self._app_border_color) or self._app_border_color)
        self._app_text_color = str(values.get('app_text_color', self._app_text_color) or self._app_text_color)
        self._app_accent_color = str(values.get('app_accent_color', self._app_accent_color) or self._app_accent_color)
        self._app_hover_color = str(values.get('app_hover_color', self._app_hover_color) or self._app_hover_color)
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
        self._champion_splash_skin = int(values.get('champion_splash_skin', self._champion_splash_skin))
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
        self._champ_select_window_size = str(values.get('champ_select_window_size', self._champ_select_window_size))

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

        if persist:
            save_settings(self._settings)
        self._configure_diagnostics_logging()
        self._update_rank_refresh_timer()
        self._reset_auto_lock_timer()
        theme_after = (
            self._text_zoom_percent,
            self._app_bg_color,
            self._app_surface_color,
            self._app_border_color,
            self._app_text_color,
            self._app_accent_color,
            self._app_hover_color,
            self._hover_highlight_color_setting,
            self._logged_in_gradient_color,
            self._logged_in_gradient_intensity,
            self._logged_in_border_width,
            self._logged_in_border_opacity,
            self._champion_splash_enabled,
            self._champion_splash_champion,
            self._champion_splash_skin,
            self._champion_splash_opacity,
            self._row_density,
            self._tag_size,
            self._tag_chip_style,
            self._rank_icon_size,
            self._rank_text_brightness,
            self._show_rank_images,
            self._show_tags,
        )

        if theme_before != theme_after:
            self._apply_theme()
        else:
            self._apply_account_list_background()
            self.update_account_item_states()

        if QApplication.activeModalWidget():
            self._pending_rank_fetch_after_modal = True
        else:
            self.refresh_account_list(fetch_ranks=True)
        QTimer.singleShot(25, _hide_any_python_titled_window)
        QTimer.singleShot(75, _hide_any_python_titled_window)
        QTimer.singleShot(150, _hide_any_python_titled_window)

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
        self._show_logged_in_spotlight()

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
        next_status.setdefault("last_game_result", self._ingame_watch_status.get("last_game_result", ""))
        next_status.setdefault("last_game_queue", self._ingame_watch_status.get("last_game_queue", ""))
        next_status.setdefault("last_game_id", self._ingame_watch_status.get("last_game_id"))
        next_status.setdefault("last_game_timestamp", self._ingame_watch_status.get("last_game_timestamp", 0))
        next_status["watcher_active"] = bool(
            self.ingame_watch_thread and self.ingame_watch_thread.isRunning()
        )
        self._ingame_watch_status = next_status
        self._update_tray_watcher_status()
        in_champ_select = bool(next_status.get("in_champ_select", False))
        in_game = bool(next_status.get("in_game", False))
        game_phase = str(next_status.get("game_phase", "") or "").strip()
        in_match_phases = {
            "GameStart",
            "InProgress",
            "Reconnect",
            "WaitingForStats",
            "PreEndOfGame",
            "EndOfGame",
        }

        if in_champ_select:
            self._maybe_refresh_champ_select_assistant(force=False)
        elif in_game or game_phase in in_match_phases:
            self._show_game_panel_ingame()
        elif self._in_champ_select_mode and bool(next_status.get("watcher_active", False)) and not game_phase:
            # Keep the panel visible during short LCU/Live API transition gaps.
            self._show_game_panel_ingame()
        else:
            self._close_champ_select_assistant()
        self.update_account_item_states()
        if self.ingame_diag_dialog:
            self.ingame_diag_dialog.refresh_status()

    def _on_ingame_match_ended(self, result: object):
        if not isinstance(result, dict):
            return

        ended_at = float(result.get("timestamp", time.time()) or time.time())
        self._ingame_watch_status["last_game_timestamp"] = ended_at
        self.update_account_item_states()

        if not bool(result.get("found", False)):
            return

        game_id_raw = result.get("game_id")
        game_id = "" if game_id_raw is None else str(game_id_raw)
        if game_id and game_id == self._last_notified_match_id:
            return
        if game_id:
            self._last_notified_match_id = game_id

        last_result = str(result.get("result", "") or "").strip()
        last_queue = str(result.get("queue_type", "") or "").strip()
        if last_result:
            self._ingame_watch_status["last_game_result"] = last_result
            self._ingame_watch_status["last_game_queue"] = last_queue
            self._ingame_watch_status["last_game_id"] = game_id_raw
            self._ingame_watch_status["last_game_timestamp"] = ended_at
            self.update_account_item_states()

        if not (self.account_manager and self._logged_in_username):
            return

        account = self.account_manager.get_account(self._logged_in_username)
        if not account:
            return

        summary = str(result.get("summary", "") or "").strip() or "Match finished"
        prompt = QMessageBox(self)
        prompt.setIcon(QMessageBox.Information)
        prompt.setWindowTitle("Game Ended")
        prompt.setText(f"Last game: {summary}")
        prompt.setInformativeText("Open op.gg match stats?")
        open_button = prompt.addButton("Open Match Stats", QMessageBox.AcceptRole)
        prompt.addButton(QMessageBox.Close)
        prompt.exec_()

        if prompt.clickedButton() == open_button:
            self._open_opgg_matches(account)

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
        popen_kwargs = {}
        if sys.platform.startswith("win"):
            popen_kwargs["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        subprocess.Popen(["cmd", "/c", str(script_path)], **popen_kwargs)

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
        popen_kwargs = {}
        if sys.platform.startswith("win"):
            popen_kwargs["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        subprocess.Popen(["cmd", "/c", str(script_path)], **popen_kwargs)

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
        popen_kwargs = {}
        if sys.platform.startswith("win"):
            popen_kwargs["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        subprocess.Popen([str(current_exe)], **popen_kwargs)
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

            dialog_bg = "#0f1424"
            text_primary = "#eef3ff"
            text_secondary = "#aeb6cc"
            text_accent = "#8bb0ff"
            divider_color = "#2b3652"

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
        if (
            sys.platform.startswith("win")
            and event.type() == QEvent.Show
            and isinstance(obj, QWidget)
            and obj.isWindow()
            and obj is not self
        ):
            title = (obj.windowTitle() or "").strip().lower()
            if title == "python" or title.startswith("python "):
                obj.hide()
                return True

        if event.type() == QEvent.Show and isinstance(obj, QDialog):
            if not bool(obj.property("_chrome_preapplied")):
                _apply_windows11_chrome(obj, self._dark_mode)
                obj.setProperty("_chrome_preapplied", True)
        if event.type() in (QEvent.MouseButtonPress, QEvent.MouseMove, QEvent.KeyPress):
            self._reset_auto_lock_timer()
        return super().eventFilter(obj, event)

    def showEvent(self, event):
        super().showEvent(event)
        self._last_screen_scale_factor = self._current_screen_scale_factor()
        self._apply_account_list_scale(self._last_screen_scale_factor)
        self._apply_title_bar_theme()
        _reveal_after_first_show(self)

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
        self.refresh_account_list(fetch_ranks=False)

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

    def _account_row_height_for_scale(self, scale: float) -> int:
        base = {
            "compact": 74,
            "comfortable": 84,
            "spacious": 96,
        }.get(self._row_density, 84)
        return max(64, int(round(base * max(1.0, min(2.0, float(scale))))))

    def _account_row_height(self) -> int:
        return self._account_row_height_for_scale(self._current_screen_scale_factor())

    def _apply_account_list_scale(self, scale: float):
        """Re-size account row widgets for the current monitor scale."""
        row_height = self._account_row_height_for_scale(scale)
        row_gap = max(4, int(round(6 * max(1.0, min(2.0, float(scale))))))
        for index in range(self.account_list.count()):
            item = self.account_list.item(index)
            widget = self.account_list.itemWidget(item)
            if not isinstance(widget, AccountListItem):
                continue
            item.setSizeHint(QSize(0, row_height + row_gap))
            widget.setFixedHeight(row_height)
            widget.apply_ui_scale(scale)
        self.account_list.doItemsLayout()
        self.account_list.viewport().update()

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
    
    def refresh_account_list(self, fetch_ranks: bool = True):
        """Refresh the account list display"""
        self.account_list.setUpdatesEnabled(False)
        try:
            # On Windows, QWidget::setParent() destroys and recreates the HWND.
            # If the spotlight panel contains an active QWebEngineView the renderer
            # process holds a reference to the old surface and crashes (0xC0000005)
            # the moment that HWND is gone.  The fix is to NEVER call setParent
            # during a refresh: just stop the web-view, take the spotlight item out
            # of the list, and hide the panel.  The panel stays a child of the
            # viewport throughout.  When _show_logged_in_spotlight() later calls
            # setItemWidget() again, Qt calls setParent(viewport()) but the widget
            # is already a viewport child so no HWND is recreated.
            if self.account_spotlight_panel:
                try:
                    for idx in range(self.account_list.count()):
                        item = self.account_list.item(idx)
                        if self.account_list.itemWidget(item) is self.account_spotlight_panel:
                            self.account_list.takeItem(idx)
                            break
                    self.account_spotlight_panel.hide()
                    self._exit_spotlight_ui_mode()
                except RuntimeError:
                    self.account_spotlight_panel = None
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
                current_scale = self._current_screen_scale_factor()
                row_gap = max(4, int(round(6 * max(1.0, min(2.0, float(current_scale))))))
                for account in filtered_accounts:
                    row_height = self._account_row_height_for_scale(current_scale)
                    item = QListWidgetItem()
                    item.setData(Qt.UserRole, account.username)
                    item.setSizeHint(QSize(0, row_height + row_gap))
                    self.account_list.addItem(item)

                    # Create custom widget — parented to the viewport so Qt
                    # never creates a top-level HWND that flashes white at (0,0).
                    widget = AccountListItem(
                        account,
                        parent=self.account_list.viewport(),
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
                        ui_scale=current_scale,
                    )
                    widget.setFixedHeight(row_height)
                    self.account_list.setItemWidget(item, widget)

                self.update_account_item_states()
                if fetch_ranks and self._show_ranks:
                    self._start_rank_fetches()
        finally:
            self.account_list.setUpdatesEnabled(True)
            if not self._in_champ_select_mode:
                self._show_logged_in_spotlight()
    
    def _start_rank_fetches(self):
        """Kick off a background rank fetch for every visible account row."""
        if not self._show_ranks:
            return

        if QApplication.activeModalWidget():
            self._pending_rank_fetch_after_modal = True
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
        self._rank_data_by_username[str(username)] = dict(rank_data or {})
        for index in range(self.account_list.count()):
            item = self.account_list.item(index)
            widget = self.account_list.itemWidget(item)
            if isinstance(widget, AccountListItem) and widget.account.username == username:
                widget.set_rank(rank_data)
                break
        if self._logged_in_username and username == self._logged_in_username and not self._in_champ_select_mode:
            self._show_logged_in_spotlight()

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
                is_logged_in = bool(self._logged_in_username) and item.data(Qt.UserRole) == self._logged_in_username
                badge_text = self._logged_in_badge_text() if is_logged_in else "Logged In"
                widget.set_dark_mode(self._dark_mode)
                widget.set_hover_highlight_color(self._hover_highlight_color)
                widget.set_selected(item.isSelected())
                widget.set_logged_in(is_logged_in, badge_text)

    def _logged_in_badge_text(self) -> str:
        """Build account badge text from the current in-game/champ-select status."""
        status = self._ingame_watch_status or {}
        queue_type = str(status.get("queue_type", "") or "").strip()
        if bool(status.get("in_champ_select", False)):
            return f"Champ Select ({queue_type})" if queue_type else "Champ Select"
        if bool(status.get("in_game", False)):
            return f"In Game ({queue_type})" if queue_type else "In Game"

        # Always return "Logged In" after a game ends (removed "Out of Game" display)
        return "Logged In"

    def _normalize_champion_slug(self, champion_name: str) -> str:
        """Normalize champion names for build-site URL paths."""
        raw = str(champion_name or "").strip().casefold()
        if not raw:
            return ""
        compact = "".join(ch for ch in raw if ch.isalnum())
        return compact

    def _resolve_logged_in_elo(self) -> tuple[str, str]:
        """Return (u.gg rank slug, human-readable label) from cached rank data."""
        username = str(self._logged_in_username or "").strip()
        if not username:
            return "overall", "Overall"

        rank_data = self._rank_data_by_username.get(username, {}) or {}
        if str(rank_data.get("status", "")).lower() != "ok":
            return "overall", "Overall"

        tier = str(rank_data.get("tier", "") or "").strip().casefold()
        if not tier:
            return "overall", "Overall"

        tier_slug = {
            "iron": "iron",
            "bronze": "bronze",
            "silver": "silver",
            "gold": "gold",
            "platinum": "platinum",
            "emerald": "emerald",
            "diamond": "diamond",
            "master": "master",
            "grandmaster": "grandmaster",
            "challenger": "challenger",
        }.get(tier, "overall")
        label = str(rank_data.get("tier", "") or "Overall").strip() or "Overall"
        return tier_slug, label

    def _build_u_gg_build_urls(
        self,
        my_champion: str,
        enemy_champion: str,
        rank_slug: str,
        queue_id: object,
    ) -> tuple[str, str]:
        """Build queue-aware matchup/fallback u.gg build URLs for current champ select."""
        my_slug = self._normalize_champion_slug(my_champion)
        if not my_slug:
            return "", ""

        rank_param = str(rank_slug or "overall").strip() or "overall"
        try:
            qid = int(queue_id)
        except (TypeError, ValueError):
            qid = None

        queue_path = "build"
        queue_query = f"rank={quote(rank_param, safe='')}"

        # ARAM has its own build route and is not tied to ranked tiers.
        if qid == 450:
            queue_path = "aram-build"
            queue_query = ""

        fallback_url = f"https://u.gg/lol/champions/{my_slug}/{queue_path}"
        if queue_query:
            fallback_url = f"{fallback_url}?{queue_query}"

        enemy_slug = self._normalize_champion_slug(enemy_champion)
        matchup_url = ""
        if enemy_slug:
            matchup_query_parts = []
            if queue_query:
                matchup_query_parts.append(queue_query)
            matchup_query_parts.append(f"opp={quote(enemy_slug, safe='')}")
            matchup_url = (
                f"https://u.gg/lol/champions/{my_slug}/{queue_path}"
                f"?{'&'.join(matchup_query_parts)}"
            )
        return matchup_url, fallback_url

    def _maybe_refresh_champ_select_assistant(self, force: bool = False):
        """Refresh champ-select assistant content while in champ select."""
        status = self._ingame_watch_status or {}
        game_phase = str(status.get("game_phase", "") or "").strip()
        in_match_phases = {
            "GameStart",
            "InProgress",
            "Reconnect",
            "WaitingForStats",
            "PreEndOfGame",
            "EndOfGame",
        }

        if not (self.account_manager and self._logged_in_username):
            if bool(status.get("in_game", False)) or game_phase in in_match_phases:
                self._show_game_panel_ingame()
                return
            self._close_champ_select_assistant()
            return

        now = time.time()
        
        # Debounce rapid close/reopen cycles: if we just closed champ select within 0.8 seconds,
        # skip re-opening to prevent double-trigger. This fixes the issue where LCU signal changes
        # cause the window to flicker open and closed.
        if (now - self._last_champ_select_close_at) < 0.8 and not self._in_champ_select_mode:
            return
        
        if not force and (now - self._last_champ_select_refresh_at) < 1.4:
            return
        self._last_champ_select_refresh_at = now

        matchup = RiotClientIntegration.get_champ_select_matchup(timeout_seconds=1.2)
        matchup_phase = str(matchup.get("phase", "") or "")
        if not RiotClientIntegration._is_champ_select_phase(matchup_phase):
            if bool(status.get("in_game", False)) or game_phase in in_match_phases:
                self._show_game_panel_ingame()
                return
            self._close_champ_select_assistant()
            return

        my_champion = str(matchup.get("my_champion", "") or "").strip()
        enemy_champion = str(matchup.get("enemy_champion", "") or "").strip()
        queue_type = str(matchup.get("queue_type", "") or "").strip()
        role_hint = str(matchup.get("role_hint", "") or "").strip()
        queue_id = matchup.get("queue_id")
        rank_slug, rank_label = self._resolve_logged_in_elo()
        matchup_url, fallback_url = self._build_u_gg_build_urls(my_champion, enemy_champion, rank_slug, queue_id)

        summary_lines = []
        if my_champion and enemy_champion:
            summary_lines.append(f"Detected matchup: {my_champion} vs {enemy_champion}")
            summary_lines.append("Open Matchup Build for matchup-specific runes/items.")
        elif my_champion:
            summary_lines.append(f"Detected champion: {my_champion}")
            summary_lines.append("Opponent champion not visible yet. Using fallback champion build.")
        else:
            summary_lines.append("Waiting for your champion pick/lock.")

        summary_lines.append(f"Elo target: {rank_label}")
        if queue_type:
            summary_lines.append(f"Queue: {queue_type}")

        payload = {
            "my_champion": my_champion,
            "enemy_champion": enemy_champion,
            "queue_type": queue_type,
            "role_hint": role_hint,
            "rank_label": rank_label,
            "summary_lines": summary_lines,
            "matchup_url": matchup_url,
            "fallback_url": fallback_url,
        }

        signature = "|".join([
            my_champion,
            enemy_champion,
            str(queue_id),
            queue_type,
            rank_slug,
            role_hint,
        ])
        if (
            signature == self._last_champ_select_signature
            and self.main_area_stack
            and self.main_area_stack.currentIndex() == 1
        ):
            return
        self._last_champ_select_signature = signature
        self._last_champ_select_role_hint = role_hint

        if self.game_info_panel:
            self.game_info_panel.update_payload(payload)
        if self.main_area_stack:
            if self.main_area_stack.currentIndex() != 1:
                self._enter_champ_select_mode()
            self.main_area_stack.setCurrentIndex(1)

    def _close_champ_select_assistant(self):
        """Hide the in-client game panel and switch back to the account list."""
        self._last_champ_select_signature = ""
        self._last_champ_select_role_hint = ""
        self._last_champ_select_refresh_at = 0.0
        self._last_champ_select_close_at = time.time()
        if self.main_area_stack:
            if self.main_area_stack.currentIndex() == 1:
                self._exit_champ_select_mode()
            self._show_logged_in_spotlight()

    def _show_game_panel_ingame(self):
        """Show the inline game panel with in-game state, reusing last known champion data."""
        if not (self.main_area_stack and self.game_info_panel):
            return
        if not self._in_champ_select_mode:
            self._enter_champ_select_mode()
        status = self._ingame_watch_status or {}
        queue_type = str(status.get("queue_type", "") or "")
        queue_id = status.get("queue_id")

        # Recover champion names from the last champ-select signature
        sig = self._last_champ_select_signature or ""
        parts = sig.split("|") if sig else []
        my_champion = parts[0] if len(parts) > 0 else ""
        enemy_champion = parts[1] if len(parts) > 1 else ""
        role_hint = parts[5] if len(parts) > 5 else self._last_champ_select_role_hint
        if not queue_id and len(parts) > 2:
            try:
                queue_id = int(parts[2])
            except (ValueError, TypeError):
                pass

        rank_slug, rank_label = self._resolve_logged_in_elo()
        matchup_url, fallback_url = self._build_u_gg_build_urls(
            my_champion, enemy_champion, rank_slug, queue_id
        )

        payload = {
            "in_game": True,
            "my_champion": my_champion,
            "enemy_champion": enemy_champion,
            "queue_type": queue_type,
            "role_hint": role_hint,
            "rank_label": rank_label,
            "matchup_url": matchup_url,
            "fallback_url": fallback_url,
        }
        self.game_info_panel.update_payload(payload)
        self.main_area_stack.setCurrentIndex(1)

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
                self._spotlight_user_dismissed = False  # new account logged in — allow spotlight
                self.update_account_item_states()
                # Start in-game watcher for externally logged-in account if not already running
                if not self.ingame_watch_thread or not self.ingame_watch_thread.isRunning():
                    account = self.account_manager.get_account(matched_username)
                    if account:
                        self._start_ingame_watcher(account)
            self._show_logged_in_spotlight()
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
        self._stop_ingame_watcher()
        self._show_logged_in_spotlight()

    def _ensure_spotlight_panel(self) -> bool:
        """Return True if account_spotlight_panel is alive, recreating it if deleted."""
        if self.account_spotlight_panel is None:
            return False
        try:
            # Accessing isVisible() will raise RuntimeError if C++ object is gone
            self.account_spotlight_panel.isVisible()
            return True
        except RuntimeError:
            # C++ object was deleted — recreate the panel
            self.account_spotlight_panel = AccountSpotlightPanel()
            self.account_spotlight_panel.setParent(self.account_list_background)
            self.account_spotlight_panel.hide()
            self.account_spotlight_panel.set_dark_mode(self._dark_mode)
            self.account_spotlight_panel.set_base_color(self._app_surface_color)
            return True

    def _show_spotlight_for_account(self, account: "Account"):
        """Show the spotlight panel for any account row (not just the logged-in one)."""
        if not self._ensure_spotlight_panel():
            return
        # Only clear the dismissed flag when showing the logged-in account's spotlight.
        # For any other account, keep it True so the recurring timer cannot overwrite.
        if account.username == self._logged_in_username:
            self._spotlight_user_dismissed = False
        else:
            self._spotlight_user_dismissed = True

        # If spotlight is already in the list, just update content and scroll
        for index in range(self.account_list.count()):
            item = self.account_list.item(index)
            if self.account_list.itemWidget(item) is self.account_spotlight_panel:
                profile_url = self._build_ugg_profile_overview_url(account)
                rank_data = self._rank_data_by_username.get(account.username, {})
                self.account_spotlight_panel.set_account(account, rank_data, profile_url)
                QTimer.singleShot(200, self._update_webview_zoom)
                self._enter_spotlight_ui_mode()
                # Ensure size is correct in case account_list grew (e.g. after
                # a refresh_account_list that temporarily showed filter rows).
                QTimer.singleShot(50, self._update_spotlight_size_hint)
                QTimer.singleShot(300, self._update_spotlight_size_hint)
                # Scroll to the account row above the spotlight
                if index > 0:
                    row_above = self.account_list.item(index - 1)
                    if row_above:
                        QTimer.singleShot(50, lambda r=row_above: self.account_list.scrollToItem(
                            r, self.account_list.PositionAtTop
                        ))
                return

        # Find the row for this account and insert spotlight after it
        target_row = -1
        for index in range(self.account_list.count()):
            item = self.account_list.item(index)
            if item.data(Qt.UserRole) == account.username:
                target_row = index
                break
        if target_row < 0:
            return

        self.account_spotlight_panel.setParent(self.account_list_background)
        spotlight_item = QListWidgetItem()
        spotlight_item.setFlags(Qt.NoItemFlags)
        spotlight_item.setSizeHint(QSize(0, 480))
        self.account_list.insertItem(target_row + 1, spotlight_item)
        self.account_list.setItemWidget(spotlight_item, self.account_spotlight_panel)

        self.account_spotlight_panel.show()
        self._enter_spotlight_ui_mode()
        # Safety fallback at 50 ms and 300 ms; the list's own resizeEvent will also fire
        # immediately if the viewport height changed when filter rows were hidden.
        QTimer.singleShot(50, self._update_spotlight_size_hint)
        QTimer.singleShot(300, self._update_spotlight_size_hint)

        profile_url = self._build_ugg_profile_overview_url(account)
        rank_data = self._rank_data_by_username.get(account.username, {})
        self.account_spotlight_panel.set_account(account, rank_data, profile_url)
        QTimer.singleShot(200, self._update_webview_zoom)
        # Defer scroll until layout has settled so PositionAtTop takes effect
        account_item = self.account_list.item(target_row)
        if account_item:
            QTimer.singleShot(50, lambda: self.account_list.scrollToItem(
                account_item, self.account_list.PositionAtTop
            ))

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
        open_spotlight_action = menu.addAction("View Account Spotlight")
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
        elif chosen_action == open_spotlight_action:
            self._show_spotlight_for_account(account)
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
                self._show_logged_in_spotlight()
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
                self._show_logged_in_spotlight()
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

    def _build_opgg_matches_url(self, account: Account) -> str:
        """Build op.gg match history URL for an account."""
        return f"{self._build_opgg_profile_url(account)}/matches"

    def _open_opgg_profile(self, account: Account):
        """Open an account's op.gg profile in the system browser."""
        url = self._build_opgg_profile_url(account)
        try:
            webbrowser.open_new_tab(url)
        except Exception:
            webbrowser.open(url)

    def _open_opgg_matches(self, account: Account):
        """Open an account's op.gg match history in the system browser."""
        url = self._build_opgg_matches_url(account)
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
            "in_game": False,
            "in_champ_select": False,
            "queue_id": None,
            "queue_type": "",
            "game_phase": "",
            "last_game_result": "",
            "last_game_queue": "",
            "last_game_id": None,
            "last_game_timestamp": 0,
            "opgg_url": opgg_url,
        }
        self._update_tray_watcher_status()
        self.ingame_watch_thread = InGameWatcherThread(opgg_url)
        self.ingame_watch_thread.status_updated.connect(self._on_ingame_watch_status)
        self.ingame_watch_thread.ingame_detected.connect(self._open_ingame_webpage)
        self.ingame_watch_thread.game_ended.connect(self._on_ingame_match_ended)
        self.ingame_watch_thread.finished.connect(self._clear_ingame_watcher)
        self.ingame_watch_thread.start()

    def _open_ingame_webpage(self, url: str):
        """Open op.gg in-game page in the system browser after a 10-second delay."""
        # Delay opening to allow op.gg to populate the game data
        timer = QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(lambda: self._do_open_ingame_webpage(url, timer))
        timer.start(10000)  # 10 seconds

    def _do_open_ingame_webpage(self, url: str, timer: QTimer):
        """Actually open the op.gg in-game page."""
        timer.deleteLater()
        try:
            webbrowser.open_new_tab(url)
        except Exception:
            webbrowser.open(url)

    def _stop_ingame_watcher(self):
        """Stop any existing in-game watcher thread."""
        self._close_champ_select_assistant()
        watcher = self.ingame_watch_thread
        self.ingame_watch_thread = None  # clear first so deferred finished signals don't clobber new watcher
        if watcher:
            try:
                watcher.status_updated.disconnect()
                watcher.ingame_detected.disconnect()
                watcher.game_ended.disconnect()
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
            "in_game": False,
            "in_champ_select": False,
            "queue_id": None,
            "queue_type": "",
            "game_phase": "",
            "last_game_result": "",
            "last_game_queue": "",
            "last_game_id": None,
            "last_game_timestamp": 0,
        }
        self._update_tray_watcher_status()
        if self.ingame_diag_dialog:
            self.ingame_diag_dialog.refresh_status()

    def _clear_ingame_watcher(self):
        """Clear completed watcher thread reference."""
        self._close_champ_select_assistant()
        self.ingame_watch_thread = None
        self._ingame_watch_status = {
            "watcher_active": False,
            "status": "idle",
            "summary": "Watcher idle",
            "timestamp": time.time(),
            "status_code": None,
            "response_bytes": 0,
            "error": "",
            "in_game": False,
            "in_champ_select": False,
            "queue_id": None,
            "queue_type": "",
            "game_phase": "",
            "last_game_result": "",
            "last_game_queue": "",
            "last_game_id": None,
            "last_game_timestamp": 0,
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

        version_label = QLabel(f"Version: {APP_VERSION}")
        version_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(version_label)

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
