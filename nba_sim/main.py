"""
Main module for NBA Simulator: provides the play_game entrypoint.
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
        Dict containing 'box_score' DataFrame and 'pbp' DataFrame of events.
    """
    # Extract config values
    home_key = config.get('home_team')
    away_key = config.get('away_team')
    season = config.get('season')
    home_override = config.get('home_roster')
    away_override = config.get('away_roster')

    # Initialize Team objects
    home_team = Team(name=home_key, season=season, is_home=True, roster_override=home_override)
    away_team = Team(name=away_key, season=season, is_home=False, roster_override=away_override)

    # Run simulation engine
    box_score, pbp_df = simulate_game(home_team.name, away_team.name, season)

    # Package results
    return {
        'home_team': home_team.name,
        'away_team': away_team.name,
        'season': season,
        'box_score': box_score,
        'pbp': pbp_df
    }
