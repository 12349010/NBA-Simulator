# nba_sim/utils/stats_utils.py

import pandas as pd
import nba_sim.data_csv as data_csv

class StatsProvider:
    def get_player_shooting(self, player_id: int, season: int) -> dict:
        pbp = data_csv.pbp_df   # was _pbp_df
        # … rest unchanged …

    def get_player_rebounding(self, player_id: int, season

    def get_player_shooting(self, player_id: int, season: int) -> dict:
        """
        Returns a dict with:
          - 'fg_pct':   field goal percentage
          - 'three_pct': three‑point percentage
          - 'three_prop': proportion of FG attempts that are threes
        """
        # reference the in‑memory PB‑P DataFrame
        pbp = data_csv._pbp_df  

        # filter to that player and regulation periods
        sub = pbp[
            (pbp["player1_id"] == player_id)
            & (pbp["period"].between(1, 4))
        ]

        # fill NAs so string operations are safe
        home_desc = sub["homedescription"].fillna("")
        vis_desc  = sub["visitordescription"].fillna("")

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
            "fg_pct":     fg_pct,
            "three_pct":  three_pct,
            "three_prop": three_prop,
        }

    def get_player_rebounding(self, player_id: int, season: int) -> dict:
        """
        Returns rebounding rate:
          - 'reb_rate': chance to secure a rebound on any rebound opportunity
        """
        pbp = data_csv._pbp_df

        sub   = pbp[pbp["player1_id"] == player_id]
        rebs  = sub["eventmsgtype"].isin([4, 5]).sum()
        games = sub["game_id"].nunique()

        if games > 0:
            # assume ~100 rebound opportunities per game
            reb_rate = min(1.0, (rebs / games) / 100)
        else:
            reb_rate = 0.15

        return {"reb_rate": reb_rate}


# Single instance for import elsewhere
stats_provider = StatsProvider()
