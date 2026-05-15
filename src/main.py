"""Main application entry point"""
import sys
import ctypes
import subprocess
from pathlib import Path


from PyQt5.QtCore import QCoreApplication
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon, QPalette, QColor
from src.ui.main_window import MainWindow
from src.config.paths import load_settings


def _detach_console() -> None:
    """Permanently detach this process from its Windows console window.

    When launched via `python.exe` (not `pythonw.exe`), the process has an
    attached console whose window can flash to the foreground at any time —
    whenever Windows briefly activates it due to DWM repaints, ctypes calls,
    or Qt event processing.  Calling FreeConsole() severs that link entirely,
    making it impossible for the console window to ever appear.  This mirrors
    what PyInstaller's --noconsole and pythonw.exe do internally.
    """
    if not sys.platform.startswith("win"):
        return
    try:
        # Hide first so there's no visual glitch during detach
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 0)
        ctypes.windll.kernel32.FreeConsole()
    except Exception:
        pass


def _install_no_console_subprocess_guard() -> None:
    """Force python/cmd child processes to start without a visible console.

    Some Windows environments can surface transient console windows for child
    python/cmd processes even when the parent is a GUI app. This guard patches
    subprocess.Popen at startup and applies CREATE_NO_WINDOW for those command
    types unless the caller already provided explicit creation flags.
    """
    if not sys.platform.startswith("win"):
        return

    original_popen = subprocess.Popen

    def _looks_like_console_python_or_cmd(command) -> bool:
        try:
            if isinstance(command, (list, tuple)):
                head = str(command[0] if command else "")
            else:
                head = str(command or "")
            name = head.replace('"', '').strip().lower().rsplit('\\', 1)[-1]
            return name in {
                'python', 'python.exe', 'py', 'py.exe', 'cmd', 'cmd.exe',
                'powershell', 'powershell.exe', 'pwsh', 'pwsh.exe'
            }
        except Exception:
            return False

    def guarded_popen(*args, **kwargs):
        try:
            command = kwargs.get("args", args[0] if args else None)
            if _looks_like_console_python_or_cmd(command):
                flags = int(kwargs.get("creationflags", 0) or 0)
                flags |= getattr(subprocess, "CREATE_NO_WINDOW", 0)
                kwargs["creationflags"] = flags
        except Exception:
            pass
        return original_popen(*args, **kwargs)

    subprocess.Popen = guarded_popen


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
    try:
        # Detach the Windows console before anything else so it can never flash.
        _detach_console()
        _install_no_console_subprocess_guard()

        # Ensure accidental top-level Qt windows never use the default "python" title.
        QCoreApplication.setApplicationName("League of Legends Account Manager")

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
    except Exception:
        raise


if __name__ == '__main__':
    main()
