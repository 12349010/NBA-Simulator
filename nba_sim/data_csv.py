# nba_sim/data_csv.py
"""
Core CSV-based data layer for NBA Simulator.
Loads all CSV tables under data/, normalizes columns, and exposes API functions:
 - get_team_list()
 - get_team_schedule(team, season=None)
 - get_roster(team, season)
 - get_player_id(name, season)
 - iter_play_by_play(game_id)
"""
import os
import glob
import pandas as pd

# locate data directory
data_dir = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', 'data')
)

# file paths
_team_csv             = os.path.join(data_dir, 'team.csv')
_game_csv             = os.path.join(data_dir, 'game.csv')
_line_score_csv       = os.path.join(data_dir, 'line_score.csv')
_common_player_csv    = os.path.join(data_dir, 'common_player_info.csv')
_inactive_players_csv = os.path.join(data_dir, 'inactive_players.csv')

# load core tables
_team_df              = pd.read_csv(_team_csv)
_game_df              = pd.read_csv(_game_csv)
_line_score_df        = pd.read_csv(_line_score_csv)
_common_player_info_df= pd.read_csv(_common_player_csv)
_inactive_players_df  = pd.read_csv(_inactive_players_csv)

# load all play‑by‑play gzip files, suppress mixed‑type warnings
def iter_play_by_play(game_id):
    """Yield each play-by-play event dict for the given game_id, reading files in chunks."""
    for fpath in _pbp_files:
        for chunk in pd.read_csv(fpath, compression='gzip', chunksize=100_000):
            sub = chunk[chunk['game_id'] == game_id]
            for _, row in sub.iterrows():
                yield row.to_dict()

MIN_ROSTER_SIZE = 8

def _resolve_team_key(key):
    """Accept integer ID, abbreviation, or full name → returns team_id."""
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

def get_team_list():
    """Return DataFrame with columns ['team_id','team_name','team_abbreviation']."""
    return _team_df.rename(
        columns={'id': 'team_id', 'full_name': 'team_name', 'abbreviation': 'team_abbreviation'}
    )[['team_id','team_name','team_abbreviation']]

def get_team_schedule(team, season=None):
    """
    Return schedule for a given team (ID/abbrev/full_name).
    If season is None, returns all seasons; else filters on season_id.
    """
    tid = _resolve_team_key(team)
    df  = _game_df.copy()
    if season is not None:
        df = df[df['season_id']==int(season)]
    mask = (df['team_id_home']==tid)|(df['team_id_away']==tid)
    return df[mask].copy()

def get_player_id(name, season):
    """
    Given a display name + season, return that player's person_id.
    Raises KeyError if not found.
    """
    season = int(season)
    df = _common_player_info_df
    df_season = df[(df['from_year']<=season)&(df['to_year']>=season)]
    match = df_season[df_season['display_first_last']==name]
    if not match.empty:
        return int(match['person_id'].iloc[0])
    raise KeyError(f"Player '{name}' not found for season {season}")

def iter_play_by_play(game_id):
    """Yield each play‑by‑play event as a dict."""
    sub = _pbp_df[_pbp_df['game_id']==game_id]
    for _, row in sub.iterrows():
        yield row.to_dict()

def get_roster(team, season):
    """
    Return roster (active + season‑specific inactives) for team+season.
    Falls back to PBP inference if roster < MIN_ROSTER_SIZE.
    """
    tid    = _resolve_team_key(team)
    season = int(season)

    # --- active players by career span ---
    active = _common_player_info_df[
        ( _common_player_info_df['team_id']==tid ) &
        ( _common_player_info_df['from_year']<=season ) &
        ( _common_player_info_df['to_year']>=season )
    ]

    # --- inactive players who actually appeared that season ---
    # join inactive_players on game → filter by season_id + team
    inactive = (
        _inactive_players_df
        .merge(_game_df[['game_id','season_id']], on='game_id', how='left')
        .query("team_id==@tid and season_id==@season")
    )

    # collect person_ids
    player_ids = set(active['person_id'].astype(int)) \
               | set(inactive['player_id'].astype(int))

    # fallback via play‑by‑play if too few
    if len(player_ids) < MIN_ROSTER_SIZE:
        sched = get_team_schedule(tid, season)
        for gid in sched['game_id']:
            for ev in iter_play_by_play(gid):
                pid = ev.get('player1_id')
                if ev.get('player1_team_id')==tid and pid is not None:
                    player_ids.add(int(pid))

    # build final roster DataFrame — only those in common_player_info
    roster_df = _common_player_info_df[
        _common_player_info_df['person_id'].astype(int).isin(player_ids)
    ].copy()

    # expose the play‐by‐play DataFrame for downstream consumers
    pbp_df = _pbp_df

    # drop duplicates if any and return
    roster_df = roster_df.drop_duplicates(subset='person_id')
    return roster_df

