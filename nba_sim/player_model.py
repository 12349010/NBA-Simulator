# nba_sim/player_model.py
from dataclasses import dataclass, field
from nba_sim.data_csv import get_player_id
from nba_sim.utils.stats_utils import stats_provider

@dataclass
class Player:
    name: str
    season: int
    stats: dict = field(init=False)
    person_id: int = field(init=False)

    def __post_init__(self):
        # Resolve the display name into the NBA Stats person_id
        self.person_id = get_player_id(self.name, self.season)

        # Fetch shooting and rebounding stats from your SQLite DB
        shooting = stats_provider.get_player_shooting(self.person_id, self.season)
        rebounding = stats_provider.get_player_rebounding(self.person_id, self.season)

        # Merge them into a single stats dict
        self.stats = {**shooting, **rebounding}

    def __repr__(self):
        return f"<Player {self.name!r} (ID={self.person_id}, Season={self.season})>"
