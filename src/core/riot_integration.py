"""Riot Client integration for automatic login"""
import subprocess
import time
import os
import psutil
import requests
import urllib3
from pathlib import Path
from typing import Optional, Tuple
from src.config.paths import get_riot_client_path, get_lol_path, get_lol_executable

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

try:
    import win32con
    import win32gui
except ImportError:
    win32con = None
    win32gui = None


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

    QUEUE_TYPE_BY_ID = {
        0: "Custom",
        400: "Normal Draft",
        420: "Ranked Solo/Duo",
        430: "Normal Blind",
        440: "Ranked Flex",
        450: "ARAM",
        700: "Clash",
        900: "URF",
        1700: "Arena",
        1900: "Pick URF",
        2000: "Tutorial",
        2010: "Tutorial",
        2020: "Tutorial",
        490: "Quickplay",
    }

    _CHAMPION_ALIAS_BY_ID: Optional[dict[int, str]] = None

    @staticmethod
    def _is_champ_select_phase(phase: str) -> bool:
        """Return True for champ-select phases across queue variants."""
        normalized = str(phase or "").strip().casefold()
        return "champselect" in normalized
    
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
    def is_in_active_game(timeout_seconds: float = 1.5) -> bool:
        """Return True when the local Live Client API indicates an active match.

        The endpoint is only available while the game process is in-match.
        """
        probe = RiotClientIntegration.probe_live_client_api(timeout_seconds=timeout_seconds)
        return bool(probe.get("in_game", False))

    @staticmethod
    def probe_live_client_api(timeout_seconds: float = 1.5) -> dict:
        """Return diagnostics for local Live Client API reachability and game state."""
        url = "https://127.0.0.1:2999/liveclientdata/allgamedata"
        result = {
            "timestamp": time.time(),
            "url": url,
            "timeout_seconds": float(timeout_seconds),
            "status": "unreachable",
            "status_code": None,
            "response_bytes": 0,
            "in_game": False,
            "in_champ_select": False,
            "game_phase": "",
            "queue_id": None,
            "queue_type": "",
            "summary": "No response",
            "error": "",
        }

        try:
            response = requests.get(url, timeout=timeout_seconds, verify=False)
            body = response.text or ""
            body_nonempty = bool(body.strip())
            status_code = int(response.status_code)
            in_game = status_code == 200 and body_nonempty

            if in_game:
                status = "in_game"
                summary = "In game (200 with payload)"
            elif status_code == 200:
                status = "idle"
                summary = "200 response but empty payload"
            else:
                status = "idle"
                summary = f"HTTP {status_code}"

            result.update({
                "status": status,
                "status_code": status_code,
                "response_bytes": len(body.encode("utf-8", errors="ignore")),
                "in_game": in_game,
                "summary": summary,
            })
        except requests.Timeout:
            result.update({
                "status": "timeout",
                "summary": "Timeout contacting Live Client API",
                "error": "timeout",
            })
        except requests.RequestException as exc:
            result.update({
                "status": "unreachable",
                "summary": "Live Client API unavailable",
                "error": str(exc),
            })

        gameflow = RiotClientIntegration._probe_lcu_gameflow(timeout_seconds=min(timeout_seconds, 1.2))
        if gameflow:
            phase = str(gameflow.get("game_phase") or "")
            queue_id = gameflow.get("queue_id")
            queue_type = str(gameflow.get("queue_type") or "")
            in_champ_select = bool(gameflow.get("in_champ_select", False))

            result.update({
                "game_phase": phase,
                "queue_id": queue_id,
                "queue_type": queue_type,
                "in_champ_select": in_champ_select,
            })

            if not result.get("in_game") and in_champ_select:
                result["status"] = "champ_select"
                if queue_type:
                    result["summary"] = f"In champ select ({queue_type})"
                else:
                    result["summary"] = "In champ select"
            elif result.get("in_game") and queue_type:
                result["summary"] = f"In game ({queue_type})"

        return result

    @staticmethod
    def _get_lol_lockfile_path() -> Optional[Path]:
        """Return League Client lockfile path when available."""
        candidates = []
        lol_executable = get_lol_executable()
        if lol_executable:
            candidates.append(lol_executable.parent / 'lockfile')
            candidates.append(lol_executable.parent.parent / 'lockfile')
        lol_path = get_lol_path()
        if lol_path:
            candidates.append(lol_path / 'lockfile')

        for candidate in candidates:
            try:
                if candidate and candidate.exists():
                    return candidate
            except Exception:
                continue
        return None

    @staticmethod
    def _read_lol_lockfile() -> Optional[Tuple[int, str, str]]:
        """Parse League lockfile and return (port, password, protocol)."""
        lockfile = RiotClientIntegration._get_lol_lockfile_path()
        if not lockfile:
            return None

        try:
            raw = lockfile.read_text(encoding='utf-8').strip()
            # Format: <name>:<pid>:<port>:<password>:<protocol>
            parts = raw.split(':')
            if len(parts) < 5:
                return None
            port = int(parts[2])
            password = parts[3]
            protocol = parts[4] or 'https'
            return port, password, protocol
        except Exception:
            return None

    @staticmethod
    def _lcu_get(endpoint: str, timeout_seconds: float = 1.2) -> Optional[requests.Response]:
        """GET an authenticated LCU endpoint using League lockfile credentials."""
        lock_data = RiotClientIntegration._read_lol_lockfile()
        if not lock_data:
            return None

        port, password, protocol = lock_data
        base_url = f"{protocol}://127.0.0.1:{port}"
        try:
            return requests.get(
                f"{base_url}{endpoint}",
                auth=('riot', password),
                timeout=timeout_seconds,
                verify=False,
            )
        except requests.RequestException:
            return None

    @staticmethod
    def _queue_type_label(queue_id: Optional[int]) -> str:
        if queue_id is None:
            return ""
        try:
            qid = int(queue_id)
        except (TypeError, ValueError):
            return ""
        return RiotClientIntegration.QUEUE_TYPE_BY_ID.get(qid, f"Queue {qid}")

    @staticmethod
    def _probe_lcu_gameflow(timeout_seconds: float = 1.2) -> Optional[dict]:
        """Return champion-select and queue diagnostics from League Client API."""
        phase_resp = RiotClientIntegration._lcu_get('/lol-gameflow/v1/gameflow-phase', timeout_seconds=timeout_seconds)
        session_resp = RiotClientIntegration._lcu_get('/lol-gameflow/v1/session', timeout_seconds=timeout_seconds)
        if not phase_resp and not session_resp:
            return None

        phase = ""
        if phase_resp and phase_resp.status_code == 200:
            try:
                phase = str(phase_resp.json() or "")
            except ValueError:
                phase = (phase_resp.text or "").strip().strip('"')

        queue_id = None
        queue_type = ""
        if session_resp and session_resp.status_code == 200:
            try:
                session = session_resp.json() or {}
            except ValueError:
                session = {}

            game_data = session.get('gameData') if isinstance(session, dict) else {}
            if isinstance(game_data, dict):
                queue = game_data.get('queue') if isinstance(game_data.get('queue'), dict) else {}
                if isinstance(queue, dict):
                    queue_id = queue.get('id')
                    queue_type = str(queue.get('name') or queue.get('shortName') or "")

        if not queue_type:
            queue_type = RiotClientIntegration._queue_type_label(queue_id)

        return {
            'game_phase': phase,
            'queue_id': queue_id,
            'queue_type': queue_type,
            'in_champ_select': phase == 'ChampSelect',
        }

    @staticmethod
    def get_latest_match_result(timeout_seconds: float = 1.5) -> dict:
        """Return latest completed match result for the currently logged-in player."""
        result = {
            "found": False,
            "game_id": None,
            "result": "",
            "queue_id": None,
            "queue_type": "",
            "summary": "No recent match found",
            "error": "",
        }

        resp = RiotClientIntegration._lcu_get(
            '/lol-match-history/v1/products/lol/current-summoner/matches?begIndex=0&endIndex=1',
            timeout_seconds=timeout_seconds,
        )
        if not resp:
            result["error"] = "match_history_unreachable"
            return result
        if resp.status_code != 200:
            result["error"] = f"http_{resp.status_code}"
            return result

        try:
            payload = resp.json() or {}
        except ValueError:
            result["error"] = "invalid_json"
            return result

        games = payload.get('games') if isinstance(payload, dict) else None
        if not isinstance(games, list) or not games:
            result["summary"] = "No recent games"
            return result

        game = games[0] if isinstance(games[0], dict) else {}
        game_id = game.get('gameId')
        queue_id = game.get('queueId')
        queue_type = RiotClientIntegration._queue_type_label(queue_id)

        duration = game.get('gameDuration')
        try:
            duration_seconds = float(duration)
            if duration_seconds > 100000:
                duration_seconds = duration_seconds / 1000.0
        except (TypeError, ValueError):
            duration_seconds = 0.0

        participants = game.get('participants') if isinstance(game, dict) else []
        identity = RiotClientIntegration.get_riot_session_identity(timeout_seconds=0.8) or {}
        target_puuid = str(identity.get('puuid') or "").strip().lower()

        chosen = None
        if isinstance(participants, list):
            for p in participants:
                if not isinstance(p, dict):
                    continue
                p_puuid = str(p.get('puuid') or "").strip().lower()
                if target_puuid and p_puuid and p_puuid == target_puuid:
                    chosen = p
                    break
            if chosen is None:
                for p in participants:
                    if isinstance(p, dict) and isinstance(p.get('stats'), dict) and 'win' in p.get('stats', {}):
                        chosen = p
                        break

        stats = chosen.get('stats') if isinstance(chosen, dict) and isinstance(chosen.get('stats'), dict) else {}
        win_value = stats.get('win')
        if isinstance(win_value, bool):
            did_win = win_value
        elif isinstance(win_value, str):
            did_win = win_value.strip().lower() == 'true'
        else:
            did_win = None

        if duration_seconds and duration_seconds < 300:
            outcome = "Remake"
        elif did_win is True:
            outcome = "Win"
        elif did_win is False:
            outcome = "Loss"
        else:
            outcome = "Unknown"

        summary = outcome
        if queue_type:
            summary = f"{summary} ({queue_type})"

        result.update({
            "found": True,
            "game_id": game_id,
            "result": outcome,
            "queue_id": queue_id,
            "queue_type": queue_type,
            "summary": summary,
        })
        return result

    @staticmethod
    def _champion_alias_by_id(timeout_seconds: float = 2.0) -> dict[int, str]:
        """Return cached champion alias map keyed by numeric champion id."""
        cached = RiotClientIntegration._CHAMPION_ALIAS_BY_ID
        if isinstance(cached, dict) and cached:
            return cached

        mapping: dict[int, str] = {}
        try:
            response = requests.get(
                'https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/v1/champion-summary.json',
                timeout=timeout_seconds,
            )
            if response.status_code == 200:
                payload = response.json() or []
                if isinstance(payload, list):
                    for entry in payload:
                        if not isinstance(entry, dict):
                            continue
                        champ_id = entry.get('id')
                        alias = entry.get('alias') or entry.get('name')
                        try:
                            cid = int(champ_id)
                        except (TypeError, ValueError):
                            continue
                        if alias:
                            mapping[cid] = str(alias)
        except Exception:
            mapping = {}

        RiotClientIntegration._CHAMPION_ALIAS_BY_ID = mapping
        return mapping

    @staticmethod
    def _champion_name_from_id(champion_id: object) -> str:
        try:
            cid = int(champion_id)
        except (TypeError, ValueError):
            return ""
        if cid <= 0:
            return ""
        mapping = RiotClientIntegration._champion_alias_by_id()
        return str(mapping.get(cid, ""))

    @staticmethod
    def get_champ_select_matchup(timeout_seconds: float = 1.2) -> dict:
        """Return currently selected self/enemy champions from champ select."""
        result = {
            "available": False,
            "phase": "",
            "queue_id": None,
            "queue_type": "",
            "my_champion_id": None,
            "my_champion": "",
            "enemy_champion_id": None,
            "enemy_champion": "",
            "enemy_candidates": [],
        }

        phase_response = RiotClientIntegration._lcu_get('/lol-gameflow/v1/gameflow-phase', timeout_seconds=timeout_seconds)
        if not phase_response or phase_response.status_code != 200:
            return result

        try:
            phase = str(phase_response.json() or "")
        except ValueError:
            phase = (phase_response.text or "").strip().strip('"')
        result["phase"] = phase
        if not RiotClientIntegration._is_champ_select_phase(phase):
            return result

        session_response = RiotClientIntegration._lcu_get('/lol-champ-select/v1/session', timeout_seconds=timeout_seconds)
        if not session_response or session_response.status_code != 200:
            return result

        try:
            session = session_response.json() or {}
        except ValueError:
            return result

        if not isinstance(session, dict):
            return result

        local_cell = session.get('localPlayerCellId')
        my_team = session.get('myTeam') if isinstance(session.get('myTeam'), list) else []
        their_team = session.get('theirTeam') if isinstance(session.get('theirTeam'), list) else []

        queue_id = None
        if isinstance(session.get('gameData'), dict):
            queue = session.get('gameData', {}).get('queue')
            if isinstance(queue, dict):
                queue_id = queue.get('id')
                queue_name = str(queue.get('name') or queue.get('shortName') or "")
                if queue_name:
                    result['queue_type'] = queue_name
        result['queue_id'] = queue_id
        if not result['queue_type']:
            result['queue_type'] = RiotClientIntegration._queue_type_label(queue_id)

        my_champion_id = None
        for player in my_team:
            if not isinstance(player, dict):
                continue
            if player.get('cellId') == local_cell:
                my_champion_id = player.get('championId') or player.get('championPickIntent')
                break
        result['my_champion_id'] = my_champion_id
        result['my_champion'] = RiotClientIntegration._champion_name_from_id(my_champion_id)

        enemy_candidates: list[tuple[int, str]] = []
        for player in their_team:
            if not isinstance(player, dict):
                continue
            champ_id = player.get('championId') or player.get('championPickIntent')
            try:
                cid = int(champ_id)
            except (TypeError, ValueError):
                continue
            if cid <= 0:
                continue
            champ_name = RiotClientIntegration._champion_name_from_id(cid)
            if champ_name:
                enemy_candidates.append((cid, champ_name))

        if enemy_candidates:
            result['enemy_champion_id'] = enemy_candidates[0][0]
            result['enemy_champion'] = enemy_candidates[0][1]
            result['enemy_candidates'] = [name for _, name in enemy_candidates]

        result['available'] = bool(result['my_champion'])
        return result

    @staticmethod
    def _get_riot_lockfile_path() -> Optional[Path]:
        """Return Riot Client lockfile path when available."""
        candidates = [
            Path(os.getenv('LOCALAPPDATA', '')) / 'Riot Games' / 'Riot Client' / 'Config' / 'lockfile',
            Path(os.getenv('APPDATA', '')) / 'Riot Games' / 'Riot Client' / 'Config' / 'lockfile',
        ]
        for candidate in candidates:
            try:
                if candidate and candidate.exists():
                    return candidate
            except Exception:
                continue
        return None

    @staticmethod
    def _read_riot_lockfile() -> Optional[Tuple[int, str, str]]:
        """Parse Riot lockfile and return (port, password, protocol)."""
        lockfile = RiotClientIntegration._get_riot_lockfile_path()
        if not lockfile:
            return None

        try:
            raw = lockfile.read_text(encoding='utf-8').strip()
            # Format: <name>:<pid>:<port>:<password>:<protocol>
            parts = raw.split(':')
            if len(parts) < 5:
                return None
            port = int(parts[2])
            password = parts[3]
            protocol = parts[4] or 'https'
            return port, password, protocol
        except Exception:
            return None

    @staticmethod
    def get_riot_session_identity(timeout_seconds: float = 1.0) -> Optional[dict]:
        """Return authenticated Riot session identity data from local client APIs.

        Returns None when no authenticated Riot session is available.
        """
        lock_data = RiotClientIntegration._read_riot_lockfile()
        if not lock_data:
            return None

        port, password, protocol = lock_data
        base_url = f"{protocol}://127.0.0.1:{port}"
        auth = ('riot', password)

        identity: dict = {}
        endpoints = [
            '/rso-auth/v1/session/credentials',
            '/chat/v1/session',
        ]

        for endpoint in endpoints:
            try:
                response = requests.get(
                    f"{base_url}{endpoint}",
                    auth=auth,
                    timeout=timeout_seconds,
                    verify=False,
                )
            except requests.RequestException:
                continue

            if response.status_code in (401, 403):
                return None
            if response.status_code in (404, 204):
                continue
            if response.status_code != 200:
                continue

            try:
                data = response.json()
            except ValueError:
                continue

            if endpoint == '/rso-auth/v1/session/credentials':
                username = data.get('username') or data.get('name')
                subject = data.get('subject')
                puuid = data.get('puuid') or data.get('sub')
                if username:
                    identity['username'] = str(username)
                if subject:
                    identity['subject'] = str(subject)
                if puuid:
                    identity['puuid'] = str(puuid)
                continue

            if endpoint == '/chat/v1/session':
                if data.get('connected') is False:
                    return None

                game_name = data.get('game_name') or data.get('name')
                game_tag = data.get('game_tag') or data.get('tag_line') or data.get('tag')
                puuid = data.get('puuid')

                if game_name:
                    identity['game_name'] = str(game_name)
                if game_tag:
                    identity['game_tag'] = str(game_tag)
                if puuid:
                    identity['puuid'] = str(puuid)

        if identity.get('game_name') or identity.get('username') or identity.get('subject'):
            return identity
        return None

    @staticmethod
    def is_riot_session_authenticated(timeout_seconds: float = 1.0) -> bool:
        """Return True when Riot local auth/session endpoints report a signed-in session."""
        return RiotClientIntegration.get_riot_session_identity(timeout_seconds=timeout_seconds) is not None

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
        Launch League of Legends via Riot Client only.

        Returns:
            True if launch was successful
        """
        try:
            riot_path = get_riot_client_path()
            if not riot_path or not riot_path.exists():
                raise FileNotFoundError("Riot Client not found. Please ensure Riot Client is installed.")

            # Retry launch request and Play button in case Riot UI is late to become ready.
            for _ in range(4):
                subprocess.Popen(
                    [
                        str(riot_path),
                        "--launch-product=league_of_legends",
                        "--launch-patchline=live",
                    ],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )

                time.sleep(2)
                RiotClientIntegration._click_play_button_uia()

                if RiotClientIntegration._wait_for_lol_start(timeout_seconds=12):
                    return True

            return False

        except Exception as e:
            print(f"Error launching League of Legends: {e}")
            return False

    @staticmethod
    def _click_play_button_uia() -> bool:
        """Attempt to invoke Riot's Play button via UI Automation."""
        try:
            from pywinauto import Desktop

            hwnd = RiotClientIntegration._find_riot_window()
            if not hwnd:
                return False

            RiotClientIntegration._focus_window(hwnd)
            win = Desktop(backend="uia").window(handle=hwnd)
            win.wait("visible", timeout=3)

            buttons = [b for b in win.descendants(control_type="Button") if b.is_visible()]
            for button in buttons:
                name = (button.window_text() or "").strip().lower()
                if name in {"play", "launch", "start"}:
                    try:
                        button.invoke()
                    except Exception:
                        button.click_input()
                    return True
        except Exception:
            return False
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
