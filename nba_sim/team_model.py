from dataclasses import dataclass
from typing import List
from .player_model import Player
import nba_sim.data_acquisition as da

@dataclass
class Team:
    name: str
    roster_names: List[str]
    coach: str
    season: int
    is_home: bool = False
    players: List[Player] = field(init=False)

    def __post_init__(self):
        ages = {n: 20 + len(da.get_player_season_avgs(da.slugify(n), self.season)) for n in self.roster_names}
        self.players = [Player(n, self.season) for n in self.roster_names if minutes_cap(get_status(n)) > 0]

    def _eligible(self, minute: int) -> List[Player]:
        return [p for p in self.players if p.minutes_so_far < p.minutes_cap]

    def pick_lineup(self, game_minute: int) -> List[Player]:
        """
        Simple: starters first 8 min each quarter *if eligible*,
        else next bench players who haven't hit their cap.
        """
        starters = self.players[:5]
        bench    = self.players[5:]
        pool = self._eligible(game_minute)

        if (game_minute % 12) < 8:
            sel = [p for p in starters if p in pool]
            need = 5 - len(sel)
            sel += [p for p in bench if p in pool][:need]
            return sel if sel else pool[:5]
        else:
            sel = [p for p in starters[:2] if p in pool]
            sel += [p for p in bench if p in pool][:5-len(sel)]
            return sel if sel else pool[:5]
