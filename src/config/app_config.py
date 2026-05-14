"""Project-level app configuration loader."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

PROJECT_CONFIG_FILENAME = "app_config.json"

_DEFAULT_CONFIG: dict[str, Any] = {
    "app_version": "1.0.2",
    "settings_panel_defaults": {
        "start_on_windows_startup": False,
        "start_minimized_to_tray": False,
        "close_behavior": "tray",
        "auto_lock_minutes": 0,
        "remember_password_24h": True,
        "clipboard_auto_clear_seconds": 0,
        "confirm_before_launch": True,
        "confirm_before_delete": True,
        "account_sort_mode": "manual",
        "rank_refresh_mode": "manual",
        "auto_check_updates": True,
        "diagnostics_log_level": "INFO",
        "window_size": "800x600",
        "window_size_mode": "static",
        "text_zoom_percent": 110,
        "show_ranks": True,
        "show_rank_images": True,
        "show_tags": True,
        "auto_open_ingame_page": True,
        "tag_size": "medium",
        "tag_chip_style": "vibrant",
        "logged_in_gradient_color": "#6b7280",
        "hover_highlight_color": "__theme__",
        "champion_splash_enabled": False,
        "champion_splash_champion": "__none__",
        "champion_splash_skin": 0,
        "champion_splash_opacity": 70,
        "logged_in_gradient_intensity": 20,
        "logged_in_border_width": 2,
        "logged_in_border_opacity": 60,
        "row_density": "compact",
        "rank_icon_size": 34,
        "rank_text_brightness": 100,
        "auto_backup_enabled": True,
        "auto_backup_keep_count": 20,
        "app_bg_color": "#1e1e2e",
        "app_surface_color": "#181825",
        "app_border_color": "#313244",
        "app_text_color": "#cdd6f4",
        "app_accent_color": "#313244",
        "app_hover_color": "#45475a"
    }
}


def _project_root() -> Path:
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", "")
        if meipass:
            return Path(meipass)
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def _load_project_config() -> dict[str, Any]:
    config = dict(_DEFAULT_CONFIG)
    default_settings = dict(_DEFAULT_CONFIG["settings_panel_defaults"])

    config_path = _project_root() / PROJECT_CONFIG_FILENAME
    try:
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                raw = json.load(f)
            if isinstance(raw, dict):
                file_settings = raw.get("settings_panel_defaults", {})
                if isinstance(file_settings, dict):
                    default_settings.update(file_settings)
                if "app_version" in raw:
                    config["app_version"] = str(raw.get("app_version") or _DEFAULT_CONFIG["app_version"])
    except Exception:
        pass

    config["settings_panel_defaults"] = default_settings
    return config


_PROJECT_CONFIG = _load_project_config()
APP_VERSION = str(_PROJECT_CONFIG.get("app_version", _DEFAULT_CONFIG["app_version"]))
SETTINGS_PANEL_DEFAULTS = dict(_PROJECT_CONFIG.get("settings_panel_defaults", _DEFAULT_CONFIG["settings_panel_defaults"]))
