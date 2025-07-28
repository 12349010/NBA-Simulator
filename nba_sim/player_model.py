# nba_sim/player_model.py

from dataclasses import dataclass
from nba_sim.data_csv import get_player_id
from nba_sim.utils.stats_utils import stats_provider

@dataclass
class Player:
    name: str
    season: int

    def __post_init__(self):
        # resolve display name → numeric id
        self.person_id = get_player_id(self.name, self.season)
        # pull whatever baseline stats you need
        self.stats = stats_provider(self.person_id, self.season)

    def __repr__(self):
        return f"<Player {self.name} ({self.person_id})>"
