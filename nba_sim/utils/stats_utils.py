import sqlite3
import pandas as pd
from pathlib import Path

class StatsProvider:
    """
    Provides historical statistics for NBA players from the SQLite DB.
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
        """
        con = self._connect()
        query = '''
        SELECT
          SUM(CASE WHEN eventmsgtype=1 THEN 1 ELSE 0 END)          AS made,
          SUM(CASE WHEN eventmsgtype IN (1,2) THEN 1 ELSE 0 END)   AS att,
          SUM(CASE WHEN eventmsgtype=1 AND (homedescription LIKE '%3PT%' OR visitordescription LIKE '%3PT%') THEN 1 ELSE 0 END) AS made3,
          SUM(CASE WHEN eventmsgtype IN (1,2) AND (homedescription LIKE '%3PT%' OR visitordescription LIKE '%3PT%') THEN 1 ELSE 0 END) AS att3
        FROM play_by_play
        WHERE player1_id = ? AND period BETWEEN 1 AND 4
        '''
        df = pd.read_sql(query, con, params=(player_id,))
        con.close()

        row = df.iloc[0]
        made, att, made3, att3 = row['made'], row['att'], row['made3'], row['att3']
        fg_pct     = made / att  if att  > 0 else 0.45
        three_pct  = made3 / att3 if att3 > 0 else 0.35
        three_prop = att3  / att  if att  > 0 else 0.30
        return {'fg_pct': fg_pct, 'three_pct': three_pct, 'three_prop': three_prop}

    def get_player_rebounding(self, player_id: int, season: int) -> dict:
        """
        Returns rebounding rates:
          - 'reb_rate': chance to secure a rebound on any rebound opportunity
        """
        con = self._connect()
        query = '''
        SELECT 
          SUM(CASE WHEN eventmsgtype IN (4,5) THEN 1 ELSE 0 END) AS rebs,
          COUNT(DISTINCT game_id)                                  AS games
        FROM play_by_play
        WHERE player1_id = ?
        '''
        df = pd.read_sql(query, con, params=(player_id,))
        con.close()

        row = df.iloc[0]
        rebs, games = row['rebs'], row['games']
        if games > 0:
            # rough approximation: assume ~100 rebound chances per game
            reb_rate = min(1.0, (rebs / games) / 100)
        else:
            reb_rate = 0.15
        return {'reb_rate': reb_rate}

# Instantiate a single provider for import elsewhere
DB_PATH = Path(__file__).parent.parent / 'data' / 'nba.sqlite'
stats_provider = StatsProvider(DB_PATH)
