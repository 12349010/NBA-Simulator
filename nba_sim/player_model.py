from dataclasses import dataclass, field
import pandas as pd
from . import data_acquisition as da
from .utils.age_curve import age_multiplier
from .utils.fatigue import fatigue_factor
from .utils.injury import get_status, minutes_cap

@dataclass
class Player:
    name: str
    age: int
    season: int
    base_stats: pd.Series = field(init=False)
    tendencies: dict      = field(init=False)
    status: str           = field(init=False)
    minutes_cap: int      = field(init=False)
    minutes_so_far: float = 0.0

    def __post_init__(self):
        # b‑ref row
        slug = da.slugify(self.name)
        hist = da.get_player_season_avgs(slug, self.season)
        self.base_stats = (hist.iloc[-1] if not hist.empty
                           else pd.Series({"PTS":12,"AST":3,"TRB":4,"FG%":.46,"USG%":20}))
        if "USG%" not in self.base_stats:
            self.base_stats["USG%"] = 20

        # tendencies
        self.tendencies = da.get_player_tendencies(self.name)

        # injury info
        self.status = get_status(self.name)
        self.minutes_cap = minutes_cap(self.status)

    # ---------------- efficiency with age + fatigue ----------------
    def effective_fg(self) -> float:
        if self.minutes_so_far >= self.minutes_cap:
            return 0.0
        return (float(self.base_stats.get("FG%", .45))
                * age_multiplier(self.age)
                * fatigue_factor(self.minutes_so_far))
