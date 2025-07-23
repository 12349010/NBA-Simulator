from dataclasses import dataclass
from typing import List
from .player_model import Player

@dataclass
class Team:
    name: str
    players: List[Player]
    coach: dict
    is_home: bool = False

    # Very simple rotation model for now
    def pick_lineup(self, game_minute: int) -> List[Player]:
        """
        Starters play first 8 minutes of each quarter, then 2 starters + 3 bench.
        """
        starters = self.players[:5]
        bench    = self.players[5:]
        if (game_minute % 12) < 8:
            return starters
        return starters[:2] + bench[:3]
