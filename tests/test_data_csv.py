# tests/test_data_csv.py
import os
import sys
# Ensure the project root is on PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
import pytest

from nba_sim.data_csv import get_roster, MIN_ROSTER_SIZE
import nba_sim.data_csv as data_csv


def test_roster_length_rich_season():
    """
    For a historically full roster (e.g., 1995–96 Chicago Bulls), ensure get_roster returns at least MIN_ROSTER_SIZE players.
    """
    # 1610612741 is the Bulls' team_id in the standard NBA stats schema
    roster = get_roster(team_id=1610612741, season=1996)
    assert isinstance(roster, pd.DataFrame), "get_roster should return a DataFrame"
    assert roster.shape[0] >= MIN_ROSTER_SIZE, (
        f"Expected at least {MIN_ROSTER_SIZE} players, got {roster.shape[0]}"
    )


def test_roster_sparsity_triggers_fallback(monkeypatch):
    """
    When active/inactive data is empty, fallback should infer players from play-by-play.
    """
    team_id = 9999
    season = 3000

    # Monkey-patch dataframes to be empty
    data_csv._common_player_info_df = pd.DataFrame(
        columns=["player_id", "team_id", "from_year", "to_year"]
    )
    data_csv._inactive_players_df = pd.DataFrame(
        columns=["player_id", "team_id", "from_year", "to_year"]
    )

    # Create a fake game entry for fallback
    data_csv._game_df = pd.DataFrame({
        "game_id": [1],
        "team_id_home": [team_id],
        "team_id_visitor": [0],
        "season": [season],
    })

    # Fake play-by-play generator yields two player IDs for that team
    def fake_iter_pbp(gid, sea):
        # Only one game, two distinct players
        yield {"player1_id": 10, "team_id": team_id}
        yield {"player1_id": 20, "team_id": team_id}
    monkeypatch.setattr(data_csv, "iter_play_by_play", fake_iter_pbp)

    roster = get_roster(team_id=team_id, season=season)
    assert set(roster["player_id"]) == {10, 20}, (
        "Fallback inference should include player IDs 10 and 20"
    )


def test_roster_no_duplicate_player_ids(monkeypatch):
    """
    Ensure duplicate player entries are dropped when both active and inactive lists or fallback infer the same ID.
    """
    team_id = 1234
    season = 2025

    # Active includes player 1 twice, inactive includes player 1 once
    data_csv._common_player_info_df = pd.DataFrame({
        "player_id": [1, 1],
        "team_id": [team_id, team_id],
        "season": [season, season],
    })
    data_csv._inactive_players_df = pd.DataFrame({
        "player_id": [1],
        "team_id": [team_id],
        "season": [season],
    })
    # No games => fallback not triggered
    data_csv._game_df = pd.DataFrame({
        "game_id": [],
        "team_id_home": [],
        "team_id_visitor": [],
        "season": [],
    })

    roster = get_roster(team_id=team_id, season=season)
    # Expect a single row for player 1
    assert list(roster["player_id"]) == [1], "Duplicate player_id entries should be dropped"
