# nba_sim/player_model.py

from dataclasses import dataclass
from nba_sim.data_csv import get_player_id
from nba_sim.utils.stats_utils import stats_provider

@dataclass
class Player:
    """Represents a single NBA player for a given season."""
    name: str
    season: int

    def __post_init__(self):
        # Resolve the display name into the NBA Stats person_id
        self.person_id = get_player_id(self.name, self.season)
        # Fetch that player’s baseline season stats
        self.stats = stats_provider(self.person_id, self.season)

    def __repr__(self):
        return f"<Player {self.name!r} (ID={self.person_id}, Season={self.season})>"
