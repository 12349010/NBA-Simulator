# nba_sim/team_model.py

from typing import List, Optional
from nba_sim.data_csv import get_roster
from nba_sim.player_model import Player
from nba_sim.utils.roster_utils import assign_lineup

class Team:
    """
    Represents an NBA team in a given season, with a roster broken into starters and bench.
    You can pass in explicit `starters` and `bench` lists of player display names,
    or omit them to have them selected automatically.
    """
    def __init__(
        self,
        team_id: int,
        season: int,
        *,
        starters: Optional[List[str]] = None,
        bench: Optional[List[str]] = None,
    ):
        self.team_id = team_id
        self.season = season

        # Load the raw roster info and build Player objects
        roster_df = get_roster(team_id, season)
        # display_first_last is the column containing full names
        self.roster = [
            Player(row["display_first_last"], season)
            for _, row in roster_df.iterrows()
        ]

        # If the user provided exact starters/bench, slice them out
        if starters is not None and bench is not None:
            name_to_player = {p.name: p for p in self.roster}
            self.starters = [name_to_player[n] for n in starters if n in name_to_player]
            self.bench    = [name_to_player[n] for n in bench    if n in name_to_player]
        else:
            # Otherwise, auto‑assign a starting five and bench via utility
            self.starters, self.bench = assign_lineup(self.roster)

    def __repr__(self):
        return (
            f"<Team id={self.team_id!r} season={self.season!r} "
            f"starters={[p.name for p in self.starters]!r}>"
        )
