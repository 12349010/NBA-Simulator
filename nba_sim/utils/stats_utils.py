# nba_sim/utils/stats_utils.py

import pandas as pd
from nba_sim.data_csv import _pbp_df

class StatsProvider:
    """
    Provides synthetic shooting & rebounding rates for NBA players
    by aggregating the in‑memory play‑by‑play DataFrame.
    """

    def get_player_shooting(self, player_id: int, season: int) -> dict:
        """
        Returns a dict with:
          - 'fg_pct':   field goal percentage
          - 'three_pct': three‑point percentage
          - 'three_prop': proportion of FG attempts that are threes
        """
        # filter to that player and regulation periods
        pbp = _pbp_df
        sub = pbp[
            (pbp["player1_id"] == player_id)
            & (pbp["period"].between(1, 4))
        ]

        # fill NAs so string operations are safe
        home_desc = sub["homedescription"].fillna("")
        vis_desc = sub["visitordescription"].fillna("")

        made  = (sub["eventmsgtype"] == 1).sum()
        att   = sub["eventmsgtype"].isin([1, 2]).sum()
        mask3 = sub["eventmsgtype"].isin([1, 2]) & (
            home_desc.str.contains("3PT") | vis_desc.str.contains("3PT")
        )
        made3 = ((sub["eventmsgtype"] == 1) & mask3).sum()
        att3  = mask3.sum()

        # avoid division by zero with league‑average fallbacks
        fg_pct     = made  / att  if att  > 0 else 0.45
        three_pct  = made3 / att3 if att3 > 0 else 0.35
        three_prop = att3  / att  if att  > 0 else 0.30

        return {
            "fg_pct": fg_pct,
            "three_pct": three_pct,
            "three_prop": three_prop,
        }

    def get_player_rebounding(self, player_id: int, season: int) -> dict:
        """
        Returns rebounding rate:
          - 'reb_rate': chance to secure a rebound on any rebound opportunity
        """
        pbp = _pbp_df
        sub = pbp[pbp["player1_id"] == player_id]

        rebs  = sub["eventmsgtype"].isin([4, 5]).sum()
        games = sub["game_id"].nunique()

        if games > 0:
            # assume ~100 rebound opportunities per game
            reb_rate = min(1.0, (rebs / games) / 100)
        else:
            reb_rate = 0.15

        return {"reb_rate": reb_rate}


# Instantiate a single provider for import elsewhere
stats_provider = StatsProvider()
