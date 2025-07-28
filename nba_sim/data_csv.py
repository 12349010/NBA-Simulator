# File: nba_sim/data_csv.py
"""
Core CSV-based data layer for NBA Simulator.
Loads all CSV tables under data/, normalizes columns, and exposes API functions:
 - get_team_list()
 - get_team_schedule(team, season=None)
 - get_roster(team, season)
 - get_player_id(name, season)
 - iter_play_by_play(game_id)
Also provides internal DataFrames: _team_df, _game_df, _line_score_df, _common_player_info_df, _inactive_players_df, _pbp_df
"""
import os
import glob
import pandas as pd

data_dir = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', 'data')
)

# Load core tables
_team_csv = os.path.join(data_dir, 'team.csv')
_game_csv = os.path.join(data_dir, 'game.csv')
_line_score_csv = os.path.join(data_dir, 'line_score.csv')
_common_player_info_csv = os.path.join(data_dir, 'common_player_info.csv')
_inactive_players_csv = os.path.join(data_dir, 'inactive_players.csv')

_team_df = pd.read_csv(_team_csv)
_game_df = pd.read_csv(_game_csv)
_line_score_df = pd.read_csv(_line_score_csv)
_common_player_info_df = pd.read_csv(_common_player_info_csv)
_inactive_players_df = pd.read_csv(_inactive_players_csv)

# Load all play-by-play gzip files
_pbp_files = glob.glob(os.path.join(data_dir, 'play_by_play_*.csv.gz'))
_pbp_df = pd.concat(
    (pd.read_csv(f, compression='gzip', low_memory=False) for f in _pbp_files),
    ignore_index=True
)

# Expose play-by-play for external use
pbp_df = _pbp_df

MIN_ROSTER_SIZE = 8

# Helper: resolve team key to team_id

def _resolve_team_key(key):
    try:
        tid = int(key)
        if tid in _team_df['id'].values:
            return tid
    except Exception:
        pass
    match = _team_df[_team_df['abbreviation'] == str(key)]
    if not match.empty:
        return int(match['id'].iloc[0])
    match = _team_df[_team_df['full_name'] == str(key)]
    if not match.empty:
        return int(match['id'].iloc[0])
    raise KeyError(f"Unknown team key: {key}")

# Team list

def get_team_list():
    return _team_df.rename(
        columns={'id': 'team_id', 'full_name': 'team_name', 'abbreviation': 'team_abbreviation'}
    )[['team_id', 'team_name', 'team_abbreviation']]

# Schedule

def get_team_schedule(team, season=None):
    tid = _resolve_team_key(team)
    df = _game_df
    if season is not None:
        df = df[df['season_id'] == int(season)]
    mask = (df['team_id_home'] == tid) | (df['team_id_away'] == tid)
    return df[mask].copy()

# Player ID lookup

def get_player_id(name, season):
    season = int(season)
    df = _common_player_info_df
    df_season = df[(df['from_year'] <= season) & (df['to_year'] >= season)]
    match = df_season[df_season['display_first_last'] == name]
    if not match.empty:
        return int(match['person_id'].iloc[0])
    raise KeyError(f"Player '{name}' not found for season {season}")

# Play-by-play iterator

def iter_play_by_play(game_id):
    sub = _pbp_df[_pbp_df['game_id'] == game_id]
    for _, row in sub.iterrows():
        yield row.to_dict()

# Roster fetch

def get_roster(team, season):
    tid = _resolve_team_key(team)
    season = int(season)

    active = _common_player_info_df[
        (_common_player_info_df['team_id'] == tid) &
        (_common_player_info_df['from_year'] <= season) &
        (_common_player_info_df['to_year'] >= season)
    ]
    inactive = _inactive_players_df[_inactive_players_df['team_id'] == tid]

    player_ids = set(active['person_id'].astype(int)) | set(inactive['player_id'].astype(int))

    if len(player_ids) < MIN_ROSTER_SIZE:
        sched = get_team_schedule(tid, season)
        for gid in sched['game_id']:
            for ev in iter_play_by_play(gid):
                pid = ev.get('player1_id')
                if ev.get('player1_team_id') == tid and pid is not None:
                    player_ids.add(int(pid))

    roster_df = _common_player_info_df[_common_player_info_df['person_id'].isin(player_ids)].copy()
    return roster_df
