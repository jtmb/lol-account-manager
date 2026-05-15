"""Main application entry point"""
import sys
from pathlib import Path
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon, QPalette, QColor
from src.ui.main_window import MainWindow
from src.config.paths import load_settings


def _resource_path(relative_path: str) -> Path:
    """Return path to bundled resource (PyInstaller) or project file."""
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / relative_path
    return Path(__file__).resolve().parents[1] / relative_path


def _apply_dark_palette(app: QApplication) -> None:
    """Set a dark QPalette on the application so every widget starts dark.

    On Windows, Qt paints the OS-level window background using the QPalette
    *before* any stylesheet is applied.  Without this, newly created or
    repainted widgets momentarily appear white (the system default), producing
    the visible white flash when buttons are pressed.
    """
    palette = QPalette()
    dark_bg      = QColor("#1e1e2e")
    surface      = QColor("#181825")
    border       = QColor("#313244")
    text         = QColor("#cdd6f4")
    disabled     = QColor("#585b70")
    highlight    = QColor("#45475a")
    hilite_text  = QColor("#cdd6f4")

    palette.setColor(QPalette.Window,          dark_bg)
    palette.setColor(QPalette.WindowText,      text)
    palette.setColor(QPalette.Base,            surface)
    palette.setColor(QPalette.AlternateBase,   dark_bg)
    palette.setColor(QPalette.ToolTipBase,     dark_bg)
    palette.setColor(QPalette.ToolTipText,     text)
    palette.setColor(QPalette.Text,            text)
    palette.setColor(QPalette.Button,          border)
    palette.setColor(QPalette.ButtonText,      text)
    palette.setColor(QPalette.BrightText,      text)
    palette.setColor(QPalette.Highlight,       highlight)
    palette.setColor(QPalette.HighlightedText, hilite_text)
    palette.setColor(QPalette.Link,            QColor("#89b4fa"))
    palette.setColor(QPalette.Disabled, QPalette.Text,       disabled)
    palette.setColor(QPalette.Disabled, QPalette.ButtonText, disabled)
    palette.setColor(QPalette.Disabled, QPalette.WindowText, disabled)
    app.setPalette(palette)


def main():
    """Run the application"""
    app = QApplication(sys.argv)

    # Must be called before any window is created so that every widget's
    # initial OS-level background paint uses dark colors, preventing the
    # white flash on Windows.
    _apply_dark_palette(app)

    icon_path = _resource_path("assets/icon.ico")
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    
    window = MainWindow()
    if bool(load_settings().get("start_minimized_to_tray", False)):
        window.hide()
    else:
        window.show()
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
