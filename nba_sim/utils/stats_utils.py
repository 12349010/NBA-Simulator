from dataclasses import dataclass, field
from nba_sim.utils.stats_utils import stats_provider
from nba_sim.data_sqlite import get_player_id

@dataclass
class Player:
    """
    Represents an NBA player with precomputed historical probabilities and in-game stats.
    """
    id: int
    name: str
    season: int
    position: str = None
    height: float = None
    weight: float = None

    # Historical event probabilities (initialized in __post_init__)
    fg_pct: float = field(init=False)
    three_pct: float = field(init=False)
    three_prop: float = field(init=False)
    reb_rate: float = field(init=False)

    # In-game stat tracking
    g: dict = field(default_factory=lambda: {
        'minutes': 0.0,
        'points': 0,
        'rebounds': 0,
        'assists': 0,
        'field_goals': 0,
        'three_points': 0,
        'two_points': 0
    })
    minutes_so_far: float = 0.0

    def __post_init__(self):
        # Ensure we have a valid player ID
        if self.id is None:
            self.id = get_player_id(self.name, self.season)
        # Load shooting probabilities
        stats = stats_provider.get_player_shooting(self.id, self.season)
        self.fg_pct = stats['fg_pct']
        self.three_pct = stats['three_pct']
        self.three_prop = stats['three_prop']
        # Load rebounding probabilities
        reb_stats = stats_provider.get_player_rebounding(self.id, self.season)
        self.reb_rate = reb_stats['reb_rate']

    def shot(self, made: bool, is3: bool):
        """
        Record a shot attempt and update scoring stats.
        """
        self.g['field_goals'] += 1
        if made:
            pts = 3 if is3 else 2
            self.g['points'] += pts
            if is3:
                self.g['three_points'] += 1
            else:
                self.g['two_points'] += 1

    def misc(self):
        """
        Placeholder for additional stats (rebounds, assists, etc.)
        Extend this to simulate events based on probabilities.
        """
        pass
