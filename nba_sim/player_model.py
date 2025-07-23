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
    base_stats: pd.Series = field(init=False)
    tendencies: dict      = field(init=False)
    status: str           = field(init=False)
    cap: int              = field(init=False)
    minutes_so_far: float = 0.0
    game: dict            = field(default_factory=lambda: {
        "PTS":0,"FGA":0,"FGM":0,"3PA":0,"3PM":0
    })

    def __post_init__(self):
        self.base_stats = get_stats(self.name, self.season)
        self.tendencies = get_tendencies(self.name, self.season)
        self.status = get_status(self.name)
        self.cap    = minutes_cap(self.status)

    # ---------- dynamic FG% ----------
    def effective_fg(self) -> float:
        raw_fg = float(self.base_stats.get("FG%", .45))
        mod = age_multiplier(int(self.base_stats.get("Age", 27))) \
              * fatigue_factor(self.minutes_so_far)
        return max(.25, min(.75, raw_fg * mod))      # clamp 25‑75 %

    # ---------- stat helpers ----------
    def record_shot(self, made: bool, is_three: bool):
        self.game["FGA"] += 1
        if made:
            self.game["FGM"] += 1
            self.game["PTS"] += 3 if is_three else 2
        if is_three:
            self.game["3PA"] += 1
            if made:
                self.game["3PM"] += 1
