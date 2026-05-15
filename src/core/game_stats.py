"""Game statistics tracking and storage"""
import json
from datetime import datetime
from dataclasses import dataclass, asdict, field
from typing import List, Dict, Optional


@dataclass
class PlayerStats:
    """Stats for a single player in a game"""
    name: str
    champion: str
    level: int = 0
    kills: int = 0
    deaths: int = 0
    assists: int = 0
    gold: int = 0
    cs: int = 0
    wards_placed: int = 0
    items: List[str] = field(default_factory=list)
    damage_dealt: int = 0


@dataclass
class GameStats:
    """Complete game statistics"""
    account_username: str
    game_id: str
    timestamp: str  # ISO datetime when game ended
    duration_seconds: int = 0
    queue_type: str = ""
    game_result: str = ""  # "victory", "defeat", "remake"
    rank_before: str = ""
    rank_after: str = ""
    
    # Team stats
    blue_team_players: List[PlayerStats] = field(default_factory=list)
    red_team_players: List[PlayerStats] = field(default_factory=list)
    blue_team_result: str = ""  # "victory", "defeat"
    
    # Player-specific
    player_champion: str = ""
    player_kills: int = 0
    player_deaths: int = 0
    player_assists: int = 0
    player_kda: float = 0.0
    player_damage: int = 0
    player_gold: int = 0
    player_cs: int = 0
    player_team: str = ""  # "blue" or "red"
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'GameStats':
        """Create from dictionary"""
        if isinstance(data.get('blue_team_players'), list):
            data['blue_team_players'] = [
                PlayerStats(**p) if isinstance(p, dict) else p 
                for p in data.get('blue_team_players', [])
            ]
        if isinstance(data.get('red_team_players'), list):
            data['red_team_players'] = [
                PlayerStats(**p) if isinstance(p, dict) else p 
                for p in data.get('red_team_players', [])
            ]
        return cls(**data)


class GameStatsTracker:
    """Track game stats per account"""
    
    def __init__(self):
        self._stats_by_account: Dict[str, List[GameStats]] = {}
    
    def record_game(self, stats: GameStats) -> None:
        """Record a completed game"""
        username = stats.account_username
        if username not in self._stats_by_account:
            self._stats_by_account[username] = []
        self._stats_by_account[username].append(stats)
    
    def get_account_stats(self, username: str, limit: int = 20) -> List[GameStats]:
        """Get recent game stats for account"""
        stats_list = self._stats_by_account.get(username, [])
        # Return most recent games first
        return sorted(stats_list, key=lambda s: s.timestamp, reverse=True)[:limit]
    
    def get_account_summary(self, username: str) -> Dict:
        """Get summary stats for an account"""
        stats_list = self._stats_by_account.get(username, [])
        if not stats_list:
            return {
                'total_games': 0,
                'wins': 0,
                'losses': 0,
                'win_rate': 0.0,
                'avg_kda': 0.0,
                'avg_damage': 0,
                'avg_gold': 0,
                'avg_cs': 0,
            }
        
        wins = sum(1 for s in stats_list if s.game_result == "victory")
        losses = sum(1 for s in stats_list if s.game_result == "defeat")
        total = len(stats_list)
        
        avg_kda = sum(s.player_kda for s in stats_list) / total if total > 0 else 0.0
        avg_damage = sum(s.player_damage for s in stats_list) // total if total > 0 else 0
        avg_gold = sum(s.player_gold for s in stats_list) // total if total > 0 else 0
        avg_cs = sum(s.player_cs for s in stats_list) // total if total > 0 else 0
        
        return {
            'total_games': total,
            'wins': wins,
            'losses': losses,
            'win_rate': (wins / total * 100) if total > 0 else 0.0,
            'avg_kda': avg_kda,
            'avg_damage': avg_damage,
            'avg_gold': avg_gold,
            'avg_cs': avg_cs,
        }
    
    def clear_account_stats(self, username: str) -> None:
        """Clear all stats for an account"""
        if username in self._stats_by_account:
            del self._stats_by_account[username]
    
    def to_dict(self) -> Dict:
        """Serialize to dictionary"""
        return {
            username: [s.to_dict() for s in stats]
            for username, stats in self._stats_by_account.items()
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'GameStatsTracker':
        """Deserialize from dictionary"""
        tracker = cls()
        for username, stats_list in data.items():
            tracker._stats_by_account[username] = [
                GameStats.from_dict(s) if isinstance(s, dict) else s
                for s in stats_list
            ]
        return tracker
