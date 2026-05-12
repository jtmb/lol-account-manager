"""Riot Client integration for automatic login"""
import subprocess
import time
import psutil
from pathlib import Path
from typing import Optional, Tuple
from src.config.paths import get_riot_client_path, get_lol_executable, get_lol_path

import win32con
import win32gui


class RiotClientIntegration:
    """Handle integration with Riot Client and League of Legends"""

    RIOT_PROCESS_NAMES = {
        'RiotClientServices',
        'RiotClientUx',
        'RiotClientUxRender',
    }

    LOL_PROCESS_NAMES = {
        'LeagueClient',
        'LeagueClientUx',
        'LeagueClientUxRender',
        'League of Legends',
    }
    
    @staticmethod
    def find_lol_launch_dir() -> Optional[Path]:
        """Find the directory containing LoL launch configuration"""
        lol_path = get_lol_path()
        if not lol_path:
            return None
        
        # Look for Game directory or similar
        candidates = [
            lol_path / 'Game',
            lol_path / 'drive' / 'c' / 'Riot Games' / 'League of Legends' / 'Game',
        ]
        
        for candidate in candidates:
            if candidate.exists():
                return candidate
        return None
    
    @staticmethod
    def is_riot_client_running() -> bool:
        """Check if Riot Client is running"""
        try:
            for proc in psutil.process_iter(['name']):
                if 'RiotClientServices' in proc.name() or 'RiotClientUx' in proc.name():
                    return True
        except:
            pass
        return False
    
    @staticmethod
    def is_lol_running() -> bool:
        """Check if League of Legends is running"""
        try:
            for proc in psutil.process_iter(['name']):
                proc_name = proc.name() or ''
                if any(name in proc_name for name in RiotClientIntegration.LOL_PROCESS_NAMES):
                    return True
        except:
            pass
        return False

    @staticmethod
    def _wait_for_lol_start(timeout_seconds: int = 20) -> bool:
        """Wait for League processes to appear after a launch request."""
        deadline = time.time() + timeout_seconds
        while time.time() < deadline:
            if RiotClientIntegration.is_lol_running():
                return True
            time.sleep(0.5)
        return False
    
    @staticmethod
    def launch_riot_client(username: str, password: str) -> bool:
        """
        Launch Riot Client and attempt login
        
        Args:
            username: Account username (email or username)
            password: Account password
            
        Returns:
            True if launch was successful
        """
        riot_path = get_riot_client_path()
        if not riot_path:
            raise FileNotFoundError("Riot Client not found. Please ensure League of Legends is installed.")
        
        try:
            # Always close existing League/Riot session before launching selected account.
            RiotClientIntegration._kill_lol_client()
            time.sleep(0.5)

            # Kill existing Riot Client if running
            RiotClientIntegration._kill_riot_client()
            time.sleep(1)
            
            # Launch Riot Client with credentials
            # The Riot Client will attempt to use stored credentials or prompt for login
            subprocess.Popen(
                [str(riot_path)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            # Wait for the client window and fill credentials.
            ok, reason = RiotClientIntegration._attempt_ui_login(username, password)
            if not ok:
                raise RuntimeError(f"Could not automate Riot login screen: {reason}")
            
            return True
            
        except Exception as e:
            print(f"Error launching Riot Client: {e}")
            return False

    @staticmethod
    def _attempt_ui_login(
        username: str,
        password: str,
        timeout_seconds: int = 30,
    ) -> Tuple[bool, str]:
        """Locate Riot window, then enter credentials using robust methods."""
        deadline = time.time() + timeout_seconds
        last_reason = "Riot login window not detected yet"
        while time.time() < deadline:
            hwnd = RiotClientIntegration._find_riot_window()
            if hwnd:
                ok, reason = RiotClientIntegration._attempt_uia_login(hwnd, username, password)
                if ok:
                    return True, "UI Automation login submitted"
                last_reason = f"UIA: {reason}"
            time.sleep(0.5)
        return False, last_reason

    @staticmethod
    def _attempt_uia_login(hwnd: int, username: str, password: str) -> Tuple[bool, str]:
        """Try to set login fields through Windows UI Automation tree."""
        try:
            # Import lazily to avoid COM initialization conflicts during app startup.
            from pywinauto import Desktop
            from pywinauto.keyboard import send_keys

            RiotClientIntegration._focus_window(hwnd)
            win = Desktop(backend="uia").window(handle=hwnd)
            win.wait("visible", timeout=4)

            edits = [e for e in win.descendants(control_type="Edit") if e.is_visible()]
            if len(edits) < 2:
                return False, f"found {len(edits)} visible edit controls"

            user_edit = edits[0]
            pass_edit = edits[1]

            user_edit.set_focus()
            user_edit.set_edit_text(username)

            pass_edit.set_focus()
            pass_edit.set_edit_text(password)

            buttons = [b for b in win.descendants(control_type="Button") if b.is_visible()]
            for button in buttons:
                name = (button.window_text() or "").strip().lower()
                if name in {"sign in", "login", "log in", "play"}:
                    try:
                        button.invoke()
                    except Exception:
                        button.click_input()
                    return True, "invoked sign-in button"

            # Deterministic fallback discovered by user: from username, tab 8 times to sign-in.
            user_edit.set_focus()
            time.sleep(0.08)
            send_keys('{TAB 8}')
            time.sleep(0.05)
            send_keys('{SPACE}')
            time.sleep(0.15)
            send_keys('{ENTER}')
            return True, "submitted via tab-focus fallback (TAB x8 + SPACE/ENTER)"
        except Exception as e:
            return False, str(e)

    @staticmethod
    def _find_riot_window() -> Optional[int]:
        """Return Riot Client top-level window handle if visible."""
        found = []

        def enum_callback(hwnd, _):
            if not win32gui.IsWindowVisible(hwnd):
                return
            title = win32gui.GetWindowText(hwnd) or ""
            lower = title.lower()
            if "riot client" in lower or "league of legends" in lower:
                found.append(hwnd)

        win32gui.EnumWindows(enum_callback, None)
        return found[0] if found else None

    @staticmethod
    def _focus_window(hwnd: int):
        """Bring Riot window to front."""
        try:
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        except Exception:
            pass
        win32gui.SetForegroundWindow(hwnd)

    @staticmethod
    def _kill_riot_client():
        """Kill running Riot Client process"""
        try:
            for proc in psutil.process_iter(['name']):
                proc_name = proc.name() or ''
                if any(name in proc_name for name in RiotClientIntegration.RIOT_PROCESS_NAMES):
                    proc.kill()
                    time.sleep(0.5)
        except:
            pass

    @staticmethod
    def _kill_lol_client():
        """Kill running League of Legends client/game processes."""
        try:
            for proc in psutil.process_iter(['name']):
                proc_name = proc.name() or ''
                if any(name in proc_name for name in RiotClientIntegration.LOL_PROCESS_NAMES):
                    proc.kill()
                    time.sleep(0.3)
        except:
            pass
    
    @staticmethod
    def launch_lol() -> bool:
        """
        Launch League of Legends
        
        Returns:
            True if launch was successful
        """
        try:
            # First try launching via Riot Client services.
            riot_path = get_riot_client_path()
            if riot_path and riot_path.exists():
                subprocess.Popen(
                    [
                        str(riot_path),
                        "--launch-product=league_of_legends",
                        "--launch-patchline=live",
                    ],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                if RiotClientIntegration._wait_for_lol_start(timeout_seconds=20):
                    return True

            # Fallback: launch League Client directly and verify it starts.
            lol_exec = get_lol_executable()

            if not lol_exec:
                raise FileNotFoundError(
                    "League of Legends executable not found. "
                    "Please ensure League of Legends is installed."
                )
            if not lol_exec.is_file():
                raise FileNotFoundError(
                    f"Configured LoL path is not a file: {lol_exec}"
                )

            subprocess.Popen(
                [str(lol_exec)],
                cwd=str(lol_exec.parent),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            return RiotClientIntegration._wait_for_lol_start(timeout_seconds=20)
            
        except Exception as e:
            print(f"Error launching League of Legends: {e}")
            return False
    
    @staticmethod
    def login_and_launch(username: str, password: str, launch_lol: bool = True) -> bool:
        """
        Complete login flow: authenticate with Riot, then optionally launch LoL
        
        Args:
            username: Account username
            password: Account password
            launch_lol: Whether to launch League of Legends after login
            
        Returns:
            True if process was successful
        """
        try:
            # Launch Riot Client
            if not RiotClientIntegration.launch_riot_client(username, password):
                return False
            
            # Allow authentication flow to initialize after credentials are submitted.
            time.sleep(6)
            
            # Launch League of Legends if requested
            if launch_lol:
                time.sleep(2)  # Give Riot Client time to initialize
                if not RiotClientIntegration.launch_lol():
                    return False
            
            return True
            
        except Exception as e:
            print(f"Error in login and launch flow: {e}")
            return False
