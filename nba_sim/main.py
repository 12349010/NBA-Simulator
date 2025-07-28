# nba_sim/main.py
"""
Main entrypoint for NBA-Simulator: exposes `play_game` function.
"""
from nba_sim.possession_engine import simulate_game
from nba_sim.team_model import Team


def play_game(config: dict) -> dict:
    """
    Run a single play-by-play simulation for two teams based on the config.

    Args:
        config: {
            'home_team': team name or ID,
            'away_team': team name or ID,
            'season': season end year (e.g., 1996),
            'home_roster': Optional[List[str]] of player names,
            'away_roster': Optional[List[str]] of player names
        }

    Returns:
        Dict containing:
          - 'home_team': Team instance for the home side
          - 'away_team': Team instance for the away side
          - 'season': season year
          - 'box_score': pandas DataFrame of final box score
          - 'pbp': pandas DataFrame of play-by-play events
    """
    # Extract configuration
    home_key = config.get('home_team')
    away_key = config.get('away_team')
    season = config.get('season')
    home_override = config.get('home_roster')
    away_override = config.get('away_roster')

    # Initialize Team objects (handles roster loading/fallback internally)
    home_team = Team(name=home_key, season=season, is_home=True, roster_override=home_override)
    away_team = Team(name=away_key, season=season, is_home=False, roster_override=away_override)

    # Run the simulation engine
    box_score_df, pbp_df = simulate_game(home_team, away_team)

    # Return structured results
    return {
        'home_team': home_team,
        'away_team': away_team,
        'season': season,
        'box_score': box_score_df,
        'pbp': pbp_df
    }
