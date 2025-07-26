from dataclasses import dataclass, field
from typing import List

from nba_sim.utils.injury import get_status, minutes_cap
from nba_sim.data_csv import get_roster
from .player_model import Player

@dataclass
class Team:
    name: str
    season: int
    is_home: bool = False
    players: List[Player] = field(init=False)

    def __post_init__(self):
        raw = get_roster(self.name, self.season)
        names = raw.get('players', [])
        # Filter out injured players
        self.players = [ Player(n, self.season)
                         for n in names
                         if minutes_cap(get_status(n)) > 0 ]

    def pick_lineup(self, game_minute: int) -> List[Player]:
        # Simple rotation based on minutes
        starters = self.players[:5]
        bench = self.players[5:]
        pool = [p for p in self.players if p.minutes_so_far < p.cap]
        if not pool:
            return starters

        if (game_minute % 12) < 8:
            sel = [p for p in starters if p in pool]
            sel += [p for p in bench if p in pool][:5 - len(sel)]
        else:
            sel = [p for p in starters[:2] if p in pool]
            sel += [p for p in bench if p in pool][:5 - len(sel)]
        return sel
