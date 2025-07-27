import os
import pandas as pd

# Directory for CSV data files
data_dir = os.getenv('NBA_CSV_DATA_DIR', 'data')

# --- Load tables ---
# Teams
TEAM_COLS = ['id', 'full_name', 'abbreviation', 'nickname', 'city', 'state', 'year_founded']
_team_df = pd.read_csv(
    os.path.join(data_dir, 'team.csv'),
    usecols=TEAM_COLS
)

# Games
_game_df = pd.read_csv(
    os.path.join(data_dir, 'game.csv'),
    parse_dates=['game_date']
)

# Players & Roster info
_player_df = pd.read_csv(os.path.join(data_dir, 'player.csv'))
_common_df = pd.read_csv(os.path.join(data_dir, 'common_player_info.csv'))
# Normalize season column
if 'season' in _common_df.columns and 'season_id' not in _common_df.columns:
    _common_df.rename(columns={'season': 'season_id'}, inplace=True)

_inactive_df = pd.read_csv(os.path.join(data_dir, 'inactive_players.csv'))
if 'season' in _inactive_df.columns and 'season_id' not in _inactive_df.columns:
    _inactive_df.rename(columns={'season': 'season_id'}, inplace=True)

# Line scores for actual quarter splits
_line_score_df = pd.read_csv(os.path.join(data_dir, 'line_score.csv'))

# --- Public API ---

def get_team_list():
    """Return DataFrame of teams with id, full_name, abbreviation."""
    return _team_df[['id', 'full_name', 'abbreviation']].copy()


def get_team_schedule(team_id, season=None):
    """Return DataFrame of games for a team, optionally filtered by season."""
    df = _game_df[
        (_game_df['team_id_home'] == team_id) |
        (_game_df['team_id_away'] == team_id)
    ].copy()
    if season is not None:
        df = df[df['season_id'].astype(int) == int(season)]
    return df.sort_values('game_date')


def get_roster(team_id, season):
    """
    Return {'players': [...]} for given team_id and season (season_id).
    """
    season = int(season)
    roster = _common_df[
        (_common_df['team_id'] == team_id) &
        (_common_df['season_id'] == season)
    ]
    if roster.empty:
        roster = _inactive_df[
            (_inactive_df['team_id'] == team_id) &
            (_inactive_df['season_id'] == season)
        ]
    return {'players': roster['player_id'].tolist()}


def get_player_id(full_name, season=None):
    """
    Lookup a player's ID by full_name from player.csv.
    Season parameter is ignored (for future use).
    """
    matches = _player_df[_player_df['full_name'] == full_name]
    if not matches.empty:
        return int(matches['player_id'].iloc[0])
    raise KeyError(f"No player_id found for {full_name}")


def iter_play_by_play(game_id, season, chunksize=100000):
    """
    Stream play-by-play for a given game_id and season.
    Yields each play event as a dict.
    """
    filename = f"play_by_play_{season}.csv.gz"
    path = os.path.join(data_dir, filename)
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Missing play-by-play file: {path}")
    for chunk in pd.read_csv(path, compression='gzip', chunksize=chunksize):
        plays = chunk[chunk['game_id'] == int(game_id)]
        for _, row in plays.iterrows():
            yield row.to_dict()


# Expose internals if needed
__all__ = [
    'get_team_list', 'get_team_schedule', 'get_roster',
    'get_player_id', 'iter_play_by_play',
    '_game_df', '_line_score_df'
]
