import os
import pandas as pd

# Directory containing CSV data files
DATA_DIR = os.getenv('NBA_CSV_DATA_DIR', 'data')

# Columns to load from team.csv
TEAM_COLS = [
    'id', 'full_name', 'abbreviation', 'nickname', 'city', 'state', 'year_founded'
]

# Load team table with strict cols
_team_df = pd.read_csv(
    os.path.join(DATA_DIR, 'team.csv'),
    usecols=TEAM_COLS
)

# Load the full game table (all columns) and parse dates
_game_df = pd.read_csv(
    os.path.join(DATA_DIR, 'game.csv'),
    parse_dates=['game_date']
)

# Load other small tables without filtering
_player_df = pd.read_csv(os.path.join(DATA_DIR, 'player.csv'))
_common_player_info_df = pd.read_csv(os.path.join(DATA_DIR, 'common_player_info.csv'))
_inactive_players_df = pd.read_csv(os.path.join(DATA_DIR, 'inactive_players.csv'))
_line_score_df = pd.read_csv(os.path.join(DATA_DIR, 'line_score.csv'))
_other_stats_df = pd.read_csv(os.path.join(DATA_DIR, 'other_stats.csv'))
_officials_df = pd.read_csv(os.path.join(DATA_DIR, 'officials.csv'))
_team_details_df = pd.read_csv(os.path.join(DATA_DIR, 'team_details.csv'))
_team_history_df = pd.read_csv(os.path.join(DATA_DIR, 'team_history.csv'))
_team_info_common_df = pd.read_csv(os.path.join(DATA_DIR, 'team_info_common.csv'))
_draft_combine_df = pd.read_csv(os.path.join(DATA_DIR, 'draft_combine_stats.csv'))
_draft_history_df = pd.read_csv(os.path.join(DATA_DIR, 'draft_history.csv'))
_game_info_df = pd.read_csv(os.path.join(DATA_DIR, 'game_info.csv'))
_game_summary_df = pd.read_csv(os.path.join(DATA_DIR, 'game_summary.csv'))

def get_team_list():
    """Returns DataFrame with columns id, full_name, abbreviation."""
    return _team_df[['id', 'full_name', 'abbreviation']].copy()

def get_team_schedule(team_id, season=None):
    """Returns games for a team; filter by season if given."""
    df = _game_df[
        (_game_df['team_id_home'] == team_id) |
        (_game_df['team_id_away'] == team_id)
    ].copy()
    if season is not None:
        df = df[df['season_id'].astype(str) == str(season)]
    return df.sort_values('game_date')

def get_roster(team_id, season):
    """Returns dict {'players': [player_id,...]} for common or inactive players."""
    roster = _common_player_info_df[
        ( _common_player_info_df['team_id'] == team_id ) &
        ( _common_player_info_df['season'] == int(season) )
    ]
    if roster.empty:
        roster = _inactive_players_df[
            ( _inactive_players_df['team_id'] == team_id ) &
            ( _inactive_players_df['season'] == int(season) )
        ]
    return {'players': roster['player_id'].tolist()}

def iter_play_by_play(game_id, season, chunksize=100_000):
    """
    Streams play-by-play events for a given game_id and season.
    Yields each play as a dict.
    """
    filename = f'play_by_play_{season}.csv.gz'
    path = os.path.join(DATA_DIR, filename)
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Play-by-play file not found: {path}")

    for chunk in pd.read_csv(path, compression='gzip', chunksize=chunksize):
        plays = chunk[chunk['game_id'] == int(game_id)]
        for _, row in plays.iterrows():
            yield row.to_dict()
