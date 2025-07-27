# nba_sim/data_csv.py
import pandas as pd
from pathlib import Path

# =============================
# Data Loading
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

# Load core tables
_team_df = _load_csv('team')
_game_df = _load_csv('game')
_common_player_info_df = _load_csv('common_player_info')
_inactive_players_df = _load_csv('inactive_players')

# =============================
# Constants
# =============================
MIN_ROSTER_SIZE = 12  # fallback threshold

# =============================
# Play-by-Play Stub
# =============================
def iter_play_by_play(game_id: int, season: int):
    """
    Yield play-by-play events for given game and season.
    To be implemented with real PBP data (e.g., from CSVs). Stubbed here.
    """
    raise NotImplementedError("play-by-play loader not implemented")

# =============================
# Team & Schedule API
# =============================
def get_team_list() -> pd.DataFrame:
    """
    Return a DataFrame of teams with columns ['team_id', 'team_name', 'team_abbreviation'].
    """
    df = _team_df
    cols = []
    if 'team_id' in df.columns:
        cols.append('team_id')
    if 'team_name' in df.columns:
        cols.append('team_name')
    if 'team_abbreviation' in df.columns:
        cols.append('team_abbreviation')
    if cols:
        return df[cols].drop_duplicates().reset_index(drop=True)
    return pd.DataFrame()


def get_team_schedule(team_id: int, season: int) -> pd.DataFrame:
    """
    Return schedule DataFrame for a given team and season.
    Columns include at least ['game_id','date','team_id_home','team_id_visitor',...].
    """
    df = _game_df
    # Determine season column
    if 'season_id' in df.columns:
        season_col = 'season_id'
    elif 'season' in df.columns:
        season_col = 'season'
    else:
        season_col = None
    # Filter by season
    if season_col:
        df = df[df[season_col] == season]
    # Filter by team involvement
    if 'team_id_home' in df.columns and 'team_id_visitor' in df.columns:
        schedule = df[(df['team_id_home'] == team_id) | (df['team_id_visitor'] == team_id)]
    else:
        schedule = pd.DataFrame()
    return schedule.reset_index(drop=True)

# =============================
# Roster Retrieval
# =============================
def get_roster(team_id: int, season: int) -> pd.DataFrame:
    """
    Return the combined active and inactive roster for a given team and season.
    Dynamically handles 'season_id' vs 'season' columns, falls back to from_year/to_year,
    and infers from play-by-play if roster is undersized.

    Returns:
        pandas.DataFrame with at least 'player_id', plus any available metadata.
    """
    # Helper to pick season column
    def _season_col(df: pd.DataFrame) -> str:
        if 'season_id' in df.columns:
            return 'season_id'
        if 'season' in df.columns:
            return 'season'
        return None

    # === Active roster ===
    season_col = _season_col(_common_player_info_df)
    df_active = _common_player_info_df
    if season_col and season_col in df_active.columns:
        active = df_active[(df_active.get('team_id') == team_id) & (df_active[season_col] == season)]
    else:
        active = df_active[(df_active.get('team_id') == team_id) &
                           (df_active.get('from_year', 0) <= season) &
                           (df_active.get('to_year', season) >= season)]

    # === Inactive roster ===
    season_col_inact = _season_col(_inactive_players_df) or season_col
    df_inact = _inactive_players_df
    if season_col_inact and season_col_inact in df_inact.columns:
        inactive = df_inact[(df_inact.get('team_id') == team_id) & (df_inact[season_col_inact] == season)]
    else:
        inactive = df_inact[(df_inact.get('team_id') == team_id) &
                             (df_inact.get('from_year', 0) <= season) &
                             (df_inact.get('to_year', season) >= season)]

    # Combine and dedupe by player_id
    roster_df = pd.concat([active, inactive], ignore_index=True)
    if 'player_id' in roster_df.columns:
        roster_df = roster_df.drop_duplicates(subset='player_id')

    # === Fallback inference ===
    if roster_df.shape[0] < MIN_ROSTER_SIZE:
        # Filter relevant games
        season_col_games = _season_col(_game_df)
        if season_col_games and season_col_games in _game_df.columns:
            games = _game_df[((_game_df['team_id_home'] == team_id) |
                               (_game_df['team_id_visitor'] == team_id)) & ( _game_df[season_col_games] == season)]
        else:
            games = _game_df[((_game_df['team_id_home'] == team_id) |
                               (_game_df['team_id_visitor'] == team_id)) & ( _game_df.get('season', season) == season)]
        # Collect player IDs
        player_ids = set()
        for gid in games.get('game_id', []):
            for play in iter_play_by_play(gid, season):
                pid = play.get('player1_id')
                tid = play.get('team_id')
                if pid and tid == team_id:
                    player_ids.add(pid)
        if player_ids:
            df_pbp = pd.DataFrame({'player_id': list(player_ids)})
            meta = pd.concat([_common_player_info_df, _inactive_players_df], ignore_index=True)
            inferred = pd.merge(df_pbp, meta, on='player_id', how='left')
            if 'player_id' in inferred.columns:
                inferred = inferred.drop_duplicates(subset='player_id')
            roster_df = pd.concat([roster_df, inferred], ignore_index=True)
            roster_df = roster_df.drop_duplicates(subset='player_id')

    return roster_df
