
import os
import sys
# Ensure the project root is on PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
import pandas as pd

from nba_sim.data_csv import DATA_DIR, get_team_list, get_team_schedule, iter_play_by_play

def test_get_team_list():
    teams = get_team_list()
    assert isinstance(teams, pd.DataFrame)
    assert not teams.empty
    for col in ("id", "full_name", "abbreviation"):
        assert col in teams.columns

def test_get_team_schedule_and_iter_play_by_play():
    # 1) Locate split files
    files = os.listdir(DATA_DIR)
    pbp_files = [f for f in files if f.startswith("play_by_play_") and f.endswith(".csv.gz")]
    assert pbp_files, "No play_by_play_<SEASON>.csv.gz files found in data/"

    # Extract season
    example = pbp_files[0]
    season = example.removeprefix("play_by_play_").removesuffix(".csv.gz")
    assert season.isdigit()

    # 2) Find a team with games in that season
    teams = get_team_list()
    schedule = None
    for team_id in teams["id"]:
        sched = get_team_schedule(team_id)
        has_games = sched[sched["season_id"].astype(str) == season]
        if not has_games.empty:
            schedule = has_games
            break
    assert schedule is not None, f"No games found for season {season}"

    # 3) Stream plays
    game_id = schedule["game_id"].iloc[0]
    plays = list(iter_play_by_play(game_id, season, chunksize=50000))
    assert plays, f"No plays for game {game_id}, season {season}"

    # 4) Sanity check first play
    first = plays[0]
    assert first["game_id"] == game_id
    assert "eventmsgtype" in first or "action" in first

if __name__ == "__main__":
    pytest.main([__file__])
