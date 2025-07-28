import numpy as np
import pandas as pd
from typing import Tuple

from nba_sim.data_csv import iter_play_by_play
from nba_sim.team_model import Team
from nba_sim.utils.roster_utils import assign_lineup


def simulate_game(home_team: Team, away_team: Team) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Simulate a single NBA game between two Team instances.

    Args:
        home_team: Team instance for the home side (team_id, season, roster loaded)
        away_team: Team instance for the away side

    Returns:
        A tuple of (box_score_df, pbp_df):
          - box_score_df: pandas DataFrame summarizing final stats per player
          - pbp_df: pandas DataFrame of the play-by-play event log
    """
    # Generate a synthetic game_id for simulation context
    game_id = f"SIM_{home_team.team_id}_{away_team.team_id}_{home_team.season}"
    season = home_team.season

    # Determine if teams played yesterday (stub; replace with real logic)
    def _played_yesterday(team: Team) -> bool:
        return False

    # Select starting lineups using roster_utils logic
    home_start = assign_lineup(home_team.roster)
    away_start = assign_lineup(away_team.roster)

    # Collect play-by-play events
    pbp_records = []
    for event in iter_play_by_play(game_id=game_id, season=season):
        # enrich each event with home/away context if needed
        pbp_records.append(event)
    pbp_df = pd.DataFrame(pbp_records)

    # Placeholder box score: count events per player
    box_score_df = (
        pbp_df.groupby('player1_id')
        .size()
        .reset_index(name='events_count')
    )

    return box_score_df, pbp_df
