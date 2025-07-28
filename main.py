# nba_sim/main.py
import pandas as pd
from nba_sim.data_csv import get_team_list, get_roster
from nba_sim.team_model import Team
from nba_sim.possession_engine import simulate_game

def play_game(
    home_name: str,
    away_name: str,
    season: int,
    home_players: list[str],
    away_players: list[str],
    speed: float = 1.0
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Build Team objects from names/rosters, kick off the possession-engine
    simulation, and return (box_score_df, play_by_play_df).
    """
    # map team names to IDs
    teams_df = get_team_list()
    name_to_id = {row.team_name: row.team_id for row in teams_df.itertuples()}
    home_id = name_to_id[home_name]
    away_id = name_to_id[away_name]

    # pull full rosters & filter by selected starters
    full_home = get_roster(home_id, season)
    full_away = get_roster(away_id, season)
    home_roster = full_home[full_home.display_first_last.isin(home_players)]
    away_roster = full_away[full_away.display_first_last.isin(away_players)]

    # instantiate Team models
    home_team = Team(home_id, season, roster=home_roster)
    away_team = Team(away_id, season, roster=away_roster)

    # run the simulation
    box_score_df, pbp_df = simulate_game(home_team, away_team)

    # (we can wire `speed` into the playback loop later)
    return box_score_df, pbp_df
