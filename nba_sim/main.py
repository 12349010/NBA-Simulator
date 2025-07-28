# nba_sim/data_csv.py
import pandas as pd
from pathlib import Path
from typing import Optional

# =============================
# File and Data Loading
# =============================
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / 'data'

def _load_csv(name: str) -> pd.DataFrame:
    """
    Load a CSV by name from DATA_DIR, or return empty DataFrame if not present.
    """
    path = DATA_DIR / f"{name}.csv"
    if path.exists():
        return pd.read_csv(path)
    return pd.DataFrame()

# Core tables
_team_df = _load_csv('team')
_game_df = _load_csv('game')
_line_score_df = _load_csv('line_score')
_common_player_info_df = _load_csv('common_player_info')
_inactive_players_df = _load_csv('inactive_players')
_player_df = _load_csv('player')  # contains player_id, full_name, from_year, to_year

# =============================
# Constants
# =============================
MIN_ROSTER_SIZE = 12  # threshold to trigger PBP roster inference

# =============================
# Play-by-Play Stub
# =============================
def iter_play_by_play(game_id: int, season: int):
    """
    Yield play-by-play events for given game and season.
    To be implemented with real PBP data.
    """
    raise NotImplementedError("play-by-play loader not implemented")

# =============================
# Player Lookup
# =============================
def get_player_id(full_name: str, season: int) -> int:
    """
    Return the player_id for the given full_name active in the specified season.
    If multiple matches, use season range to disambiguate.
    """
    df = _player_df
    matches = df[df['full_name'] == full_name]
    if matches.empty:
        raise KeyError(f"Player '{full_name}' not found in player.csv")
    if len(matches) == 1:
        return int(matches.iloc[0]['player_id'])
    # Filter by career range
    in_season = matches[(matches.get('from_year', 0) <= season) &
                        (matches.get('to_year', season) >= season)]
    if len(in_season) == 1:
        return int(in_season.iloc[0]['player_id'])
    # Fallback to first match
    return int(matches.iloc[0]['player_id'])

# =============================
# Team & Schedule API
# =============================
def _resolve_team_id(team_key) -> int:
    """
    Accept either a team_id (int) or team_name/abbreviation (str) and return team_id.
    """
    if isinstance(team_key, int):
        return team_key
    df = _team_df
    # Match by full name first, then abbreviation
    row = df[df['team_name'] == team_key]
    if row.empty:
        row = df[df['team_abbreviation'] == team_key]
    if row.empty:
        raise KeyError(f"Team '{team_key}' not found in team.csv")
    return int(row.iloc[0]['team_id'])


def get_team_list() -> pd.DataFrame:
    """
    Return a DataFrame of teams with columns ['team_id','team_name','team_abbreviation'].
    """
    df = _team_df
    cols = [c for c in ['team_id','team_name','team_abbreviation'] if c in df.columns]
    return df[cols].drop_duplicates().reset_index(drop=True)


def get_team_schedule(team_key, season: Optional[int] = None) -> pd.DataFrame:
    """
    Return schedule DataFrame for a given team, optionally filtered by season.
    Accepts team_id (int) or team_name/abbreviation (str).
    """
    tid = _resolve_team_id(team_key)
    df = _game_df.copy()

    # Apply season filter if provided
    if season is not None:
        season_col = (
            'season_id' if 'season_id' in df.columns else
            'season'    if 'season'    in df.columns else
            None
        )
        if season_col:
            df = df[df[season_col] == season]

    # Filter by team involvement
    schedule = df[(df['team_id_home'] == tid) | (df['team_id_visitor'] == tid)]
    return schedule.reset_index(drop=True)

# =============================
# Roster Retrieval
# =============================
def get_roster(team_key, season: int) -> pd.DataFrame:
    """
    Return the combined active and inactive roster for a given team and season,
    including 'player_id' and 'player_name'.
    Accepts team_id (int) or team_name/abbreviation (str).
    """
    tid = _resolve_team_id(team_key)

    # Active roster filter
    df_active = _common_player_info_df
    s_col_active = (
        'season_id' if 'season_id' in df_active.columns else
        'season'    if 'season'    in df_active.columns else
        None
    )
    if s_col_active:
        active = df_active[(df_active['team_id'] == tid) & (df_active[s_col_active] == season)]
    else:
        active = df_active[(df_active['team_id'] == tid) &
                           (df_active.get('from_year', 0) <= season) &
                           (df_active.get('to_year', season) >= season)]

    # Inactive roster filter
    df_inact = _inactive_players_df
    s_col_inact = (
        'season_id' if 'season_id' in df_inact.columns else
        'season'    if 'season'    in df_inact.columns else
        s_col_active
    )
    if s_col_inact:
        inactive = df_inact[(df_inact['team_id'] == tid) & (df_inact[s_col_inact] == season)]
    else:
        inactive = df_inact[(df_inact['team_id'] == tid) &
                             (df_inact.get('from_year', 0) <= season) &
                             (df_inact.get('to_year', season) >= season)]

    # Combine active and inactive, drop duplicates
    roster = pd.concat([active, inactive], ignore_index=True)
    if 'player_id' in roster.columns:
        roster = roster.drop_duplicates(subset='player_id')

    # Merge in player_name from player.csv
    if 'player_id' in roster.columns and 'full_name' in _player_df.columns:
        roster = pd.merge(
            roster,
            _player_df[['player_id','full_name']].rename(columns={'full_name':'player_name'}),
            on='player_id', how='left'
        )

    return roster.reset_index(drop=True)
