# File: nba_sim/utils/stats_utils.py

import sqlite3
import pandas as pd
from pathlib import Path
import nba_sim.data_csv as data_csv

class StatsProvider:
    """
    Provides historical statistics for NBA players from CSV-based pbp.
    """
    def __init__(self, db_path: Path = None):
        # db_path optional - not used when reading pbp_df directly
        self.db_path = db_path

    def get_player_shooting(self, player_id: int, season: int) -> dict:
        pbp = data_csv.pbp_df
        sub = pbp[(pbp['player1_id'] == player_id) & (pbp['period'] <= 4)]

        made = ((sub['eventmsgtype'] == 1).sum())
        att = ((sub['eventmsgtype'].isin([1,2])).sum())
        made3 = sub[sub['eventmsgtype'] == 1][['homedescription', 'visitordescription']]
        # approximate 3pt detection
        made3 = made3.apply(lambda row: ('3PT' in str(row['homedescription'])) or ('3PT' in str(row['visitordescription'])), axis=1).sum()
        att3 = sub[sub['eventmsgtype'].isin([1,2])]
        att3 = att3.apply(lambda row: ('3PT' in str(row['homedescription'])) or ('3PT' in str(row['visitordescription'])), axis=1).sum()

        fg_pct = made/att if att>0 else 0.45
        three_pct = made3/att3 if att3>0 else 0.35
        three_prop = att3/att if att>0 else 0.30
        return {'fg_pct': fg_pct, 'three_pct': three_pct, 'three_prop': three_prop}

    def get_player_rebounding(self, player_id: int, season: int) -> dict:
        pbp = data_csv.pbp_df
        sub = pbp[pbp['player1_id'] == player_id]
        rebs = ((sub['eventmsgtype'].isin([4,5])).sum())
        games = sub['game_id'].nunique()
        reb_rate = (rebs/games/100) if games>0 else 0.15
        reb_rate = min(reb_rate, 1.0)
        return {'reb_rate': reb_rate}

# single StatsProvider instance for imports
stats_provider = StatsProvider()
