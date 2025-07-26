from dataclasses import dataclass, field
from typing import Optional, Dict

from nba_sim.utils.stats_utils import stats_provider
from nba_sim.data_sqlite import get_player_id

@dataclass
class Player:
    """
    Represents an NBA player in the simulation, enriched with historical 
    performance probabilities (FG%, 3P%, rebounding rate) loaded at init.
    Tracks cumulative game stats in `g` and time on court in `minutes_so_far`.
    """
    name: str
    season: int
    position: Optional[str] = None
    height: Optional[float] = None
    weight: Optional[float] = None

    id: int = field(init=False)
    fg_pct: float = field(init=False)
    three_pct: float = field(init=False)
    three_prop: float = field(init=False)
    reb_rate: float = field(init=False)

    g: Dict[str, float] = field(default_factory=lambda: {
        'minutes': 0.0,
        'points': 0.0,
        'rebounds': 0.0,
        'assists': 0.0,
        'field_goals': 0.0,
        'three_points': 0.0,
        'two_points': 0.0
    })
    minutes_so_far: float = 0.0

    def __post_init__(self):
        self.id = get_player_id(self.name, self.season)

        shoot = stats_provider.get_player_shooting(self.id, self.season)
        self.fg_pct = shoot['fg_pct']
        self.three_pct = shoot['three_pct']
        self.three_prop = shoot['three_prop']

        reb = stats_provider.get_player_rebounding(self.id, self.season)
        self.reb_rate = reb['reb_rate']

    def shot(self, made: bool, is3: bool):
        self.g['field_goals'] += 1
        if made:
            pts = 3 if is3 else 2
            self.g['points'] += pts
            if is3:
                self.g['three_points'] += 1
            else:
                self.g['two_points'] += 1

    def misc(self):
        pass
