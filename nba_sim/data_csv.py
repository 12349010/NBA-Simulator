# In nba_sim/data_csv.py
import pandas as pd

# Assuming these DataFrames are defined elsewhere in this module:
# _common_player_info_df = pd.read_csv(...)
# _inactive_players_df = pd.read_csv(...)

def get_roster(team_id: int, season: int) -> pd.DataFrame:
    """
    Return the combined active and inactive roster for a given team and season.
    Dynamically handles columns 'season_id' or 'season', and falls back to from_year/to_year range.
    """
    # Active roster filter
    df_active = _common_player_info_df
    if 'season_id' in df_active.columns:
        season_col = 'season_id'
    elif 'season' in df_active.columns:
        season_col = 'season'
    else:
        season_col = None

    if season_col:
        active = df_active[(df_active['team_id'] == team_id) &
                           (df_active[season_col] == season)]
    else:
        active = df_active[(df_active['team_id'] == team_id) &
                           (df_active['from_year'] <= season) &
                           (df_active['to_year'] >= season)]

    # Inactive roster filter
    df_inact = _inactive_players_df
    if 'season_id' in df_inact.columns:
        in_season_col = 'season_id'
    elif 'season' in df_inact.columns:
        in_season_col = 'season'
    else:
        in_season_col = season_col

    if in_season_col:
        inactive = df_inact[(df_inact['team_id'] == team_id) &
                             (df_inact[in_season_col] == season)]
    else:
        inactive = df_inact[(df_inact['team_id'] == team_id) &
                             (df_inact['from_year'] <= season) &
                             (df_inact['to_year'] >= season)]

    # Combine and dedupe
    roster_df = pd.concat([active, inactive], ignore_index=True)
    roster_df = roster_df.drop_duplicates(subset='player_id')
    return roster_df
