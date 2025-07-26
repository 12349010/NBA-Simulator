import os
import pandas as pd

# Directory containing CSV data files
DATA_DIR = os.getenv('NBA_CSV_DATA_DIR', 'data')

# Columns to load from small tables
TEAM_COLS = [
    'id', 'full_name', 'abbreviation', 'nickname', 'city', 'state', 'year_founded'
]
GAME_COLS = [
    'game_id', 'game_date', 'season_id',
    'team_id_home', 'pts_home', 'team_id_away', 'pts_away',
    'fg_pct_home', 'fg_pct_away', 'fg3_pct_home', 'fg3_pct_away',
    'ft_pct_home', 'ft_pct_away', 'reb_home', 'reb_away',
    'ast_home', 'ast_away', 'blk_home', 'blk_away',
    'stl_home', 'stl_away', 'turnovers_home', 'turnovers_away',
    'pf_home', 'pf_away', 'plus_minus_home', 'plus_minus_away'
]

# Load small CSV tables into module-level DataFrames
_team_df = pd.read_csv(os.path.join(DATA_DIR, 'team.csv'), usecols=TEAM_COLS)
_game_df = pd.read_csv(
    os.path.join(DATA_DIR, 'game.csv'),
    usecols=GAME_COLS,
    parse_dates=['game_date']
)
# Load other small tables (load all columns)
_player_df = pd.read_csv(os.path.join(DATA_DIR, 'player.csv'))
_common_player_info_df = pd.read_csv(os.path.join(DATA_DIR, 'common_player_info.csv'))
_game_info_df = pd.read_csv(os.path.join(DATA_DIR, 'game_info.csv'))
_game_summary_df = pd.read_csv(os.path.join(DATA_DIR, 'game_summary.csv'))
_line_score_df = pd.read_csv(os.path.join(DATA_DIR, 'line_score.csv'))
_other_stats_df = pd.read_csv(os.path.join(DATA_DIR, 'other_stats.csv'))
_officials_df = pd.read_csv(os.path.join(DATA_DIR, 'officials.csv'))
_team_details_df = pd.read_csv(os.path.join(DATA_DIR, 'team_details.csv'))
_team_history_df = pd.read_csv(os.path.join(DATA_DIR, 'team_history.csv'))
_team_info_common_df = pd.read_csv(os.path.join(DATA_DIR, 'team_info_common.csv'))
_draft_combine_df = pd.read_csv(os.path.join(DATA_DIR, 'draft_combine_stats.csv'))
_draft_history_df = pd.read_csv(os.path.join(DATA_DIR, 'draft_history.csv'))
_inactive_players_df = pd.read_csv(os.path.join(DATA_DIR, 'inactive_players.csv'))


def get_team_list():
    """
    Returns a DataFrame of all teams with id, full_name, and abbreviation.
    """
    return _team_df[['id', 'full_name', 'abbreviation']].copy()


def get_team_schedule(team_id, season=None):
    """
    Returns a DataFrame of games for the given team_id.
    Optionally filter by season_id.
    """
    df = _game_df[
        (_game_df['team_id_home'] == team_id) |
        (_game_df['team_id_away'] == team_id)
    ].copy()
    if season is not None:
        df = df[df['season_id'] == season]
    return df.sort_values('game_date')


def get_roster(team_id, season):
    """
    Returns a roster for the given team and season.
    Uses common_player_info; falls back to inactive_players if needed.

    Returns a dict with keys 'players' (list of player_ids).
    Further breakdown (starters/bench) can be added based on available columns.
    """
    roster = _common_player_info_df[
        (_common_player_info_df['team_id'] == team_id) &
        (_common_player_info_df['season'] == season)
    ]
    if roster.empty:
        roster = _inactive_players_df[
            (_inactive_players_df['team_id'] == team_id) &
            (_inactive_players_df['season'] == season)
        ]
    return {
        'players': roster['player_id'].tolist()
    }


def iter_play_by_play(game_id, season, chunksize=100_000):
    """
    Generator that streams play-by-play events for a given game_id and season.
    Yields each play as a dict.
    """
    filename = f'play_by_play_{season}.csv.gz'
    path = os.path.join(DATA_DIR, filename)
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Play-by-play file not found: {path}")

    for chunk in pd.read_csv(
        path,
        compression='gzip',
        chunksize=chunksize,
        parse_dates=['game_date'] if 'game_date' in pd.read_csv(path, nrows=0).columns else []
    ):
        plays = chunk[chunk['game_id'] == game_id]
        if not plays.empty:
            for _, row in plays.iterrows():
                yield row.to_dict()

if __name__ == "__main__":
    # sanity check: pick a known game
    sample_game = get_team_schedule(team_id=1610612737, season=2020).iloc[0]
    gid, season = sample_game.game_id, sample_game.season_id
    seq = [p["eventmsgtype"] for p in iter_play_by_play(gid, season)]
    print(f"{len(seq)} plays loaded for game {gid} in season {season}")
