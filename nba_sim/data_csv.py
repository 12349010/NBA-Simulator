# In nba_sim/data_csv.py
import pandas as pd

# Assuming these DataFrames and engine functions are defined elsewhere in this module:
# _common_player_info_df = pd.read_csv(...)
# _inactive_players_df = pd.read_csv(...)
# _game_df = pd.read_csv(...)
# iter_play_by_play(game_id, season) -> yields play-by-play rows with columns including 'team_id' and 'player1_id'

MIN_ROSTER_SIZE = 12


def get_roster(team_id: int, season: int) -> pd.DataFrame:
    """
    Return the combined active and inactive roster for a given team and season.
    Dynamically handles columns 'season_id' or 'season', falls back to from_year/to_year range,
    and infers roster from play-by-play if primary data is insufficient.
    """
    # Helper to determine season column
    def _season_col(df):
        if 'season_id' in df.columns:
            return 'season_id'
        if 'season' in df.columns:
            return 'season'
        return None

    # Active roster filter
    season_col = _season_col(_common_player_info_df)
    df_active = _common_player_info_df
    if season_col:
        active = df_active[(df_active['team_id'] == team_id) &
                           (df_active[season_col] == season)]
    else:
        active = df_active[(df_active['team_id'] == team_id) &
                           (df_active['from_year'] <= season) &
                           (df_active['to_year'] >= season)]

    # Inactive roster filter
    season_col_inact = _season_col(_inactive_players_df) or season_col
    df_inact = _inactive_players_df
    if season_col_inact:
        inactive = df_inact[(df_inact['team_id'] == team_id) &
                             (df_inact[season_col_inact] == season)]
    else:
        inactive = df_inact[(df_inact['team_id'] == team_id) &
                             (df_inact['from_year'] <= season) &
                             (df_inact['to_year'] >= season)]

    # Combine and dedupe
    roster_df = pd.concat([active, inactive], ignore_index=True)
    roster_df = roster_df.drop_duplicates(subset='player_id')

    # Fallback: infer roster from play-by-play if too few players
    if roster_df.shape[0] < MIN_ROSTER_SIZE:
        # Gather all game_ids for this team and season
        season_col_games = _season_col(_game_df)
        games = _game_df[( (_game_df['team_id_home'] == team_id) |
                           (_game_df['team_id_visitor'] == team_id) ) &
                         (_game_df[season_col_games] == season)]
        player_ids = set()
        for gid in games['game_id'].unique():
            for play in iter_play_by_play(gid, season):
                pid = play.get('player1_id')
                tid = play.get('team_id')
                if pid and tid == team_id:
                    player_ids.add(pid)
        # Build DataFrame of inferred players
        df_pbp = pd.DataFrame({'player_id': list(player_ids)})
        # Merge metadata to get full player info
        meta = pd.concat([_common_player_info_df, _inactive_players_df], ignore_index=True)
        inferred = pd.merge(df_pbp, meta, on='player_id', how='left')
        inferred = inferred.drop_duplicates(subset='player_id')
        roster_df = pd.concat([roster_df, inferred], ignore_index=True)
        roster_df = roster_df.drop_duplicates(subset='player_id')

    return roster_df
