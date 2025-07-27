from dataclasses import dataclass, field
from typing import Optional, Dict

from nba_sim.utils.stats_utils import stats_provider
from nba_sim.data_csv import get_player_id

@dataclass
class Player:
    """
    Represents an NBA player in a given season, holding stats and tracking minutes.
    """
    name: str
    season: int
    id: int = field(init=False)
    stats: Dict = field(default_factory=dict)
    minutes_so_far: int = 0
    cap: Optional[int] = None  # minutes cap based on injury status or other rules

    def __post_init__(self):
        # Determine the player's unique ID based on name and season
        self.id = get_player_id(self.name, self.season)
        # Load base stats for this player-season
        self.stats = stats_provider(self.id, self.season)
        # Initialize minutes cap if not set elsewhere (team logic can override)
        # self.cap should be set by team_model during roster build
        return

    def record_minutes(self, mins: int):
        """
        Increment minutes played, useful for rotation logic.
        """
        self.minutes_so_far += mins

    def reset_minutes(self):
        """
        Reset minutes played to zero.
        """
        self.minutes_so_far = 0
