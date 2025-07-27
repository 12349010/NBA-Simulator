# tests/test_data_csv.py
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

    # 2) Extract and sort seasons numerically
    seasons = sorted(
        int(f.removeprefix("play_by_play_").removesuffix(".csv.gz"))
        for f in pbp_files
    )

    # 3) Find a season with at least one game
    teams = get_team_list()
    schedule = None
    selected_season = None
    for season in seasons:
        for team_id in teams["id"]:
            sched = get_team_schedule(team_id, season)
            if not sched.empty:
                schedule = sched
                selected_season = season
                break
        if schedule is not None:
            break

    assert schedule is not None, f"No games found for any season in {seasons[:5]}..."
    assert selected_season is not None

    # 4) Stream plays for the first game in that schedule
    game_id = schedule["game_id"].iloc[0]
    plays = list(iter_play_by_play(game_id, selected_season, chunksize=50000))
    assert plays, f"No plays loaded for game {game_id}, season {selected_season}"

    # 5) Basic sanity on the first play
    first = plays[0]
    assert first.get("game_id") == game_id
    assert "eventmsgtype" in first or "action" in first


if __name__ == "__main__":
    pytest.main([__file__])
