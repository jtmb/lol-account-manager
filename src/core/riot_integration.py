"""Riot Client integration for automatic login"""
import subprocess
import time
import psutil
from pathlib import Path
from typing import Optional, Tuple
from src.config.paths import get_riot_client_path, get_lol_executable, get_lol_path

import win32api
import win32clipboard
import win32con
import win32gui

from pywinauto import Desktop


class RiotClientIntegration:
    """Handle integration with Riot Client and League of Legends"""
    
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
                if 'LeagueClientUx' in proc.name() or 'League of Legends' in proc.name():
                    return True
        except:
            pass
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

                # Fallback if Riot controls are not exposed through UIA.
                ok, kb_reason = RiotClientIntegration._attempt_keyboard_login(hwnd, username, password)
                if ok:
                    return True, f"Keyboard fallback login submitted ({reason})"

                last_reason = f"UIA: {reason}; Keyboard: {kb_reason}"
            time.sleep(0.5)
        return False, last_reason

    @staticmethod
    def _attempt_uia_login(hwnd: int, username: str, password: str) -> Tuple[bool, str]:
        """Try to set login fields through Windows UI Automation tree."""
        try:
            RiotClientIntegration._focus_window(hwnd)
            win = Desktop(backend="uia").window(handle=hwnd)
            win.wait("visible", timeout=4)

            edits = [e for e in win.descendants(control_type="Edit") if e.is_visible()]
            if len(edits) < 2:
                return False, f"found {len(edits)} visible edit controls"

            user_edit = edits[0]
            pass_edit = edits[1]

            user_edit.set_focus()
            try:
                user_edit.set_edit_text(username)
            except Exception:
                RiotClientIntegration._paste_text(username)

            pass_edit.set_focus()
            try:
                pass_edit.set_edit_text(password)
            except Exception:
                RiotClientIntegration._paste_text(password)

            buttons = [b for b in win.descendants(control_type="Button") if b.is_visible()]
            for button in buttons:
                name = (button.window_text() or "").strip().lower()
                if name in {"sign in", "login", "log in", "play"}:
                    button.click_input()
                    return True, "clicked sign-in button"

            # If sign-in button label is not discoverable, submit via Enter.
            pass_edit.set_focus()
            RiotClientIntegration._tap_key(win32con.VK_RETURN)
            return True, "submitted with Enter key"
        except Exception as e:
            return False, str(e)

    @staticmethod
    def _attempt_keyboard_login(hwnd: int, username: str, password: str) -> Tuple[bool, str]:
        """Fallback keyboard-driven login when UIA fields are unavailable."""
        try:
            RiotClientIntegration._focus_and_click_login_area(hwnd)
            time.sleep(0.2)

            RiotClientIntegration._paste_text(username)
            RiotClientIntegration._tap_key(win32con.VK_TAB)
            RiotClientIntegration._paste_text(password)
            RiotClientIntegration._tap_key(win32con.VK_RETURN)
            return True, "pasted credentials and submitted"
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
    def _focus_and_click_login_area(hwnd: int):
        """Bring Riot window to front and click where login form usually appears."""
        RiotClientIntegration._focus_window(hwnd)

        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        width = max(1, right - left)
        height = max(1, bottom - top)
        x = left + int(width * 0.5)
        y = top + int(height * 0.46)
        win32api.SetCursorPos((x, y))
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)

    @staticmethod
    def _tap_key(vk_code: int):
        """Press and release a virtual key code."""
        win32api.keybd_event(vk_code, 0, 0, 0)
        time.sleep(0.03)
        win32api.keybd_event(vk_code, 0, win32con.KEYEVENTF_KEYUP, 0)
        time.sleep(0.08)

    @staticmethod
    def _paste_text(text: str):
        """Paste text into focused control using clipboard + Ctrl+V."""
        RiotClientIntegration._set_clipboard_text(text)
        win32api.keybd_event(win32con.VK_CONTROL, 0, 0, 0)
        win32api.keybd_event(ord('V'), 0, 0, 0)
        time.sleep(0.03)
        win32api.keybd_event(ord('V'), 0, win32con.KEYEVENTF_KEYUP, 0)
        win32api.keybd_event(win32con.VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)
        time.sleep(0.12)

    @staticmethod
    def _set_clipboard_text(text: str):
        """Set text into clipboard for paste automation."""
        win32clipboard.OpenClipboard()
        try:
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardText(text, win32con.CF_UNICODETEXT)
        finally:
            win32clipboard.CloseClipboard()
    
    @staticmethod
    def _kill_riot_client():
        """Kill running Riot Client process"""
        try:
            for proc in psutil.process_iter(['name']):
                if 'RiotClientServices' in proc.name() or 'RiotClientUx' in proc.name():
                    proc.kill()
                    time.sleep(0.5)
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
            # Preferred path: ask Riot Client to launch LoL.
            # This is more reliable than directly starting game executables.
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
                return True

            # Fallback: launch League Client directly.
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

            return True
            
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
