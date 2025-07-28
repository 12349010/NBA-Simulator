import numpy as np
import pandas as pd
from typing import Tuple

from nba_sim.data_csv import iter_play_by_play, _line_score_df
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
    # Stub for fatigue; replace with real logic if desired
    def _played_yesterday(team: Team) -> bool:
        return False

    # Game identifiers
    game_id = None  # placeholder: real implementation should derive or generate a unique game_id
    season = home_team.season

    # Starting lineups based on roster_utils logic
    home_start = assign_lineup(home_team.roster)
    away_start = assign_lineup(away_team.roster)

    # Collect play-by-play events
    pbp_records = []
    for event in iter_play_by_play(game_id=game_id, season=season):
        pbp_records.append(event)
    pbp_df = pd.DataFrame(pbp_records)

    # Compute box score by aggregating pbp events
    # NOTE: this is a placeholder: replace with detailed stat mappings
    box_score_df = (
        pbp_df.groupby('player1_id')
        .size()
        .reset_index(name='events_count')
    )

    return box_score_df, pbp_df
