import sqlite3
import pandas as pd
from pathlib import Path
from nba_sim.data_csv import pbp_df

class StatsProvider:
    """
    Provides historical statistics for NBA players from the SQLite DB and in-memory pbp_df.
    """

    def __init__(self, db_path: Path):
        self.db_path = db_path

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def get_player_shooting(self, player_id: int, season: int) -> dict:
        """
        Returns a dict with:
          - 'fg_pct': field goal percentage
          - 'three_pct': three-point percentage
          - 'three_prop': proportion of attempts that are threes
        Uses pbp_df for play-by-play events.
        """
        # filter to that player and regulation periods
        sub = pbp_df[
            (pbp_df['player1_id'] == player_id) &
            (pbp_df['period'] <= 4)
        ]
        made = len(sub[sub['eventmsgtype'] == 1])
        att = len(sub[sub['eventmsgtype'].isin([1, 2])])
        made3 = len(sub[
            (sub['eventmsgtype'] == 1) &
            (sub['homedescription'].str.contains('3PT', na=False) | sub['visitordescription'].str.contains('3PT', na=False))
        ])
        att3 = len(sub[
            (sub['eventmsgtype'].isin([1, 2])) &
            (sub['homedescription'].str.contains('3PT', na=False) | sub['visitordescription'].str.contains('3PT', na=False))
        ])
        fg_pct     = made / att  if att  > 0 else 0.45
        three_pct  = made3 / att3 if att3 > 0 else 0.35
        three_prop = att3  / att  if att  > 0 else 0.30
        return {'fg_pct': fg_pct, 'three_pct': three_pct, 'three_prop': three_prop}

    def get_player_rebounding(self, player_id: int, season: int) -> dict:
        """
        Returns rebounding rates:
          - 'reb_rate': chance to secure a rebound on any rebound opportunity
        Query the SQLite DB for rebound events.
        """
        con = self._connect()
        query = '''
        SELECT 
          SUM(CASE WHEN eventmsgtype IN (4,5) THEN 1 ELSE 0 END) AS rebs,
          COUNT(DISTINCT game_id)                                 AS games
        FROM play_by_play
        WHERE player1_id = ?
        '''
        df = pd.read_sql(query, con, params=(player_id,))
        con.close()
        row = df.iloc[0]
        rebs, games = row['rebs'], row['games']
        if games > 0:
            reb_rate = min(1.0, (rebs / games) / 100)
        else:
            reb_rate = 0.15
        return {'reb_rate': reb_rate}

# Instantiate a single provider for import elsewhere
DB_PATH = Path(__file__).parent.parent / 'data' / 'nba.sqlite'
stats_provider = StatsProvider(DB_PATH)
