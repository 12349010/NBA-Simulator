# nba_sim/team_model.py
from dataclasses import dataclass, field
from typing import List, Optional

from nba_sim.data_csv import get_roster
from nba_sim.player_model import Player
from nba_sim.utils.injury import get_status, minutes_cap

@dataclass
class Team:
    """
    Represents an NBA team for a given season, including its roster of Player objects.
    """
    name: str                        # Team name or ID
    season: int                      # Season end year (e.g., 1996)
    is_home: bool = False            # True if home team
    roster_override: Optional[List[str]] = None  # Optional list of player names to use instead of full roster
    players: List[Player] = field(init=False, default_factory=list)

    def __post_init__(self):
        # Determine roster names
        if self.roster_override:
            names = self.roster_override
        else:
            roster_df = get_roster(self.name, self.season)
            if 'player_name' in roster_df.columns:
                names = roster_df['player_name'].tolist()
            else:
                names = roster_df.get('full_name', []).tolist()

        # Initialize Player objects and apply minutes cap based on injury status
        for pname in names:
            # Determine injury-based cap if possible
            try:
                status = get_status(pname)
                cap = minutes_cap(status)
            except Exception:
                cap = None

            p = Player(pname, self.season)
            p.cap = cap
            self.players.append(p)

    def pick_lineup(self, n_starters: int = 5):
        """
        Select starters and bench from the roster.

        Returns:
            starters: List[Player] for starting lineup
            bench: List[Player] for bench rotation
        """
        # Simple selection: first n_starters as starters
        starters = self.players[:n_starters]
        bench = self.players[n_starters:]
        return starters, bench
