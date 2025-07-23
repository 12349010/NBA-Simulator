from dataclasses import dataclass, field
from typing import List
import nba_sim.data_acquisition as da
from nba_sim.utils.injury import get_status, minutes_cap
from .player_model import Player

@dataclass
class Team:
    name: str
    roster_names: List[str]
    coach: str
    season: int
    is_home: bool = False
    players: List[Player] = field(init=False)   # ← needs field import

    def __post_init__(self):
        # build Player objects, skip anyone capped at 0 (Out)
        self.players = [
            Player(n, self.season)
            for n in self.roster_names
            if minutes_cap(get_status(n)) > 0
        ]

    # ------ simple rotation logic (unchanged) ------
    def _eligible(self, minute: int) -> List[Player]:
        return [p for p in self.players if p.minutes_so_far < p.cap]

    def pick_lineup(self, game_minute: int) -> List[Player]:
        starters = self.players[:5]
        bench    = self.players[5:]
        pool     = self._eligible(game_minute)
        if not pool:
            return starters[:5]                      # emergency

        if (game_minute % 12) < 8:
            sel = [p for p in starters if p in pool]
            sel += [p for p in bench if p in pool][:5-len(sel)]
        else:
            sel = [p for p in starters[:2] if p in pool]
            sel += [p for p in bench if p in pool][:5-len(sel)]
        return sel
