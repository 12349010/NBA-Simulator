# nba_sim/team_model.py

from typing import List, Optional
from nba_sim.data_csv import get_roster
from nba_sim.player_model import Player

class Team:
    def __init__(
        self,
        team_id: int,
        season: int,
        starters: Optional[List[str]] = None,
        bench: Optional[List[str]]   = None,
    ):
        self.team_id = team_id
        self.season  = season

        # Fetch the raw roster DataFrame
        roster_df = get_roster(team_id, season)

        # Grab the list of all display names in roster order
        all_names = roster_df["display_first_last"].tolist()

        # If the user passed explicit starters / bench, use them;
        # otherwise fall back to first‑5 / the rest
        if starters:
            self.starter_names = starters
        else:
            self.starter_names = all_names[:5]

        if bench:
            self.bench_names = bench
        else:
            # everything else not in starters
            self.bench_names = [n for n in all_names if n not in self.starter_names]

        # Instantiate Player objects by display name
        # (Player[name,season] should internally call get_player_id(name,season))
        self.starters = [Player(name, season) for name in self.starter_names]
        self.bench    = [Player(name, season) for name in self.bench_names]

        # Full roster as Player objects
        self.roster = self.starters + self.bench

    def __repr__(self):
        return f"<Team {self.team_id} ({self.season}) | Starters={self.starter_names}>"
