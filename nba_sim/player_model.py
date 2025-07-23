from dataclasses import dataclass, field
import pandas as pd
from .stats_live import get_stats, get_tendencies
from .utils.age_curve import age_multiplier
from .utils.fatigue import fatigue_factor
from .utils.injury import get_status, minutes_cap

@dataclass
class Player:
    name: str
    season: int
    age: int = field(init=False)
    base_stats: pd.Series = field(init=False)
    tendencies: dict      = field(init=False)
    status: str           = field(init=False)
    cap: int              = field(init=False)
    minutes_so_far: float = 0.0

    def __post_init__(self):
        self.base_stats = get_stats(self.name, self.season)
        self.tendencies = get_tendencies(self.name, self.season)
        self.age = int(self.base_stats.get("Age", 27))
        self.status = get_status(self.name)
        self.cap = minutes_cap(self.status)

    # ------------ dynamic FG based on fatigue & age ------------
    def effective_fg(self) -> float:
        if self.minutes_so_far >= self.cap:
            return 0.0
        raw_fg = float(self.base_stats.get("FG%", .45))
        return raw_fg * age_multiplier(self.age) * fatigue_factor(self.minutes_so_far)
