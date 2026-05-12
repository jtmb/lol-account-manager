"""Riot Client integration for automatic login"""
import subprocess
import time
import psutil
from pathlib import Path
from typing import Optional
from src.config.paths import get_riot_client_path, get_lol_executable, get_lol_path
import os
import json


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
            process = subprocess.Popen(
                [str(riot_path)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            # Give it time to start
            time.sleep(3)
            
            # Attempt automated login by injecting credentials
            # Note: This is a placeholder - actual implementation depends on Riot Client's API
            # The app will need to handle the login UI when it appears
            
            return True
            
        except Exception as e:
            print(f"Error launching Riot Client: {e}")
            return False
    
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
            
            # Wait for Riot Client to fully load
            time.sleep(5)
            
            # At this point, the Riot Client UI will appear
            # The user will need to complete the login if credentials aren't stored
            # Future enhancement: implement automated UI interaction
            
            # Launch League of Legends if requested
            if launch_lol:
                time.sleep(2)  # Give Riot Client time to initialize
                if not RiotClientIntegration.launch_lol():
                    return False
            
            return True
            
        except Exception as e:
            print(f"Error in login and launch flow: {e}")
            return False
