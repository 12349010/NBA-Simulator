import pandas as pd
import pytest

from nba_sim.data_csv import get_team_schedule

# Assuming tests will set up a minimal _game_df in data_csv
import nba_sim.data_csv as data_csv

def setup_module(module):
    # Create a small game_df for testing
    data_csv._game_df = pd.DataFrame([
        {'game_id': 1, 'team_id_home': 100, 'team_id_visitor': 200, 'season': 2020},
        {'game_id': 2, 'team_id_home': 100, 'team_id_visitor': 300, 'season': 2021},
        {'game_id': 3, 'team_id_home': 400, 'team_id_visitor': 100, 'season': 2021},
        {'game_id': 4, 'team_id_home': 200, 'team_id_visitor': 300, 'season': 2020},
    ])
    # Minimal team_df
    data_csv._team_df = pd.DataFrame([
        {'team_id': 100, 'team_name': 'TeamA', 'team_abbreviation': 'TA'},
        {'team_id': 200, 'team_name': 'TeamB', 'team_abbreviation': 'TB'},
        {'team_id': 300, 'team_name': 'TeamC', 'team_abbreviation': 'TC'},
        {'team_id': 400, 'team_name': 'TeamD', 'team_abbreviation': 'TD'},
    ])


def test_schedule_all_seasons():
    # For TeamA, season=None should return all games where they played: game_id 1,2,3
    df = get_team_schedule('TeamA', season=None)
    assert set(df['game_id']) == {1, 2, 3}


def test_schedule_filtered_season():
    # For TeamA in season 2021, should return games 2 and 3
    df = get_team_schedule(100, season=2021)
    assert set(df['game_id']) == {2, 3}


def test_schedule_by_abbreviation():
    # Using abbreviation should work as well
    df = get_team_schedule('TA', season=None)
    assert set(df['game_id']) == {1, 2, 3}


def test_schedule_no_games():
    # Non-existent or no games should return empty DataFrame
    df = get_team_schedule('TeamB', season=2025)
    assert df.empty
