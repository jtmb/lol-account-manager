"""Sample game stats for demonstration"""
from src.core.game_stats import GameStats, PlayerStats, GameStatsTracker
from datetime import datetime, timedelta


def create_sample_stats_tracker() -> GameStatsTracker:
    """Create a sample tracker with demo game stats"""
    tracker = GameStatsTracker()
    
    # Sample game 1 - Victory
    game1 = GameStats(
        account_username="ExampleUser",
        game_id="game_001",
        timestamp=(datetime.utcnow() - timedelta(days=1)).isoformat(),
        duration_seconds=1800,
        queue_type="RANKED_SOLO_5x5",
        game_result="victory",
        rank_before="Gold II",
        rank_after="Gold I",
        player_champion="Ahri",
        player_kills=8,
        player_deaths=2,
        player_assists=12,
        player_kda=10.0,
        player_damage=45000,
        player_gold=18500,
        player_cs=287,
        player_team="blue",
        blue_team_result="victory",
    )
    tracker.record_game(game1)
    
    # Sample game 2 - Defeat
    game2 = GameStats(
        account_username="ExampleUser",
        game_id="game_002",
        timestamp=(datetime.utcnow() - timedelta(hours=12)).isoformat(),
        duration_seconds=2100,
        queue_type="RANKED_SOLO_5x5",
        game_result="defeat",
        rank_before="Gold I",
        rank_after="Gold I",
        player_champion="Lux",
        player_kills=5,
        player_deaths=6,
        player_assists=15,
        player_kda=3.33,
        player_damage=38000,
        player_gold=16000,
        player_cs=265,
        player_team="red",
        blue_team_result="victory",
    )
    tracker.record_game(game2)
    
    # Sample game 3 - Victory
    game3 = GameStats(
        account_username="ExampleUser",
        game_id="game_003",
        timestamp=(datetime.utcnow() - timedelta(hours=6)).isoformat(),
        duration_seconds=1650,
        queue_type="RANKED_SOLO_5x5",
        game_result="victory",
        rank_before="Gold I",
        rank_after="Gold I",
        player_champion="Zyra",
        player_kills=3,
        player_deaths=1,
        player_assists=25,
        player_kda=28.0,
        player_damage=32000,
        player_gold=15000,
        player_cs=298,
        player_team="blue",
        blue_team_result="victory",
    )
    tracker.record_game(game3)
    
    return tracker


if __name__ == "__main__":
    tracker = create_sample_stats_tracker()
    summary = tracker.get_account_summary("ExampleUser")
    print(f"Account Summary: {summary}")
