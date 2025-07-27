# nba_sim/possession_engine.py
import numpy as np
import pandas as pd

from nba_sim.data_csv import get_roster, get_team_schedule, iter_play_by_play, _line_score_df
from nba_sim.player_model import Player
from nba_sim.utils.roster_utils import assign_lineup

def simulate_game(home_team, away_team, season):
    """
    Simulate a single NBA game for two teams in the given season.

    Args:
        home_team: Team ID or name for the home team.
        away_team: Team ID or name for the away team.
        season: Season end year (e.g., 1996 for 1995-96 season).

    Returns:
        box_score: DataFrame with columns ['team', 'player_id', 'player_name', 'points', 'rebounds', 'assists']
        pbp_df: DataFrame of play-by-play events for the game.
    """
    # Load rosters
    home_roster_df = get_roster(home_team, season)
    away_roster_df = get_roster(away_team, season)

    # Initialize Player objects
    home_players = [Player(row['player_name'], season) for _, row in home_roster_df.iterrows()]
    away_players = [Player(row['player_name'], season) for _, row in away_roster_df.iterrows()]

    # Get schedule to find game IDs
    schedule = get_team_schedule(home_team, season)
    game_ids = schedule['game_id'].unique() if 'game_id' in schedule.columns else []

    # Collect play-by-play events
    pbp_events = []
    for gid in game_ids:
        try:
            for ev in iter_play_by_play(gid, season):
                pbp_events.append(ev)
        except NotImplementedError:
            break
    pbp_df = pd.DataFrame(pbp_events)

    # Initialize box score placeholders
    def _init_box(players, team_label):
        return pd.DataFrame([
            {'team': team_label,
             'player_id': p.id,
             'player_name': p.name,
             'points': 0,
             'rebounds': 0,
             'assists': 0}
            for p in players
        ])

    box_home = _init_box(home_players, 'home')
    box_away = _init_box(away_players, 'away')
    box_score = pd.concat([box_home, box_away], ignore_index=True)

    return box_score, pbp_df
