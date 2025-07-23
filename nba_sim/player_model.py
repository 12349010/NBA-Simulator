from dataclasses import dataclass, field
import pandas as pd
from . import data_acquisition as da
from .utils.age_curve import age_multiplier
from .utils.fatigue import fatigue_factor
from .utils.injury import player_is_out

@dataclass
class Player:
    name: str
    age: int
    season: int
    base_stats: pd.Series = field(init=False)
    tendencies: dict     = field(init=False)
    minutes_so_far: float = 0.0
    injured: bool        = field(init=False)

    def __post_init__(self):
        slug = da.slugify(self.name)
        hist = da.get_player_season_avgs(slug, self.season)
        if hist.empty:
            self.base_stats = pd.Series({"PTS":12,"AST":3,"TRB":4,"FG%":.46,"USG%":20})
        else:
            self.base_stats = hist.iloc[-1]
            if "USG%" not in self.base_stats:
                self.base_stats["USG%"] = 20
        self.tendencies = da.get_player_tendencies(self.name)
        self.injured = player_is_out(self.name)

    def effective_fg(self) -> float:
        if self.injured:
            return 0
        return float(self.base_stats.get("FG%", .45)) \
               * age_multiplier(self.age) \
               * fatigue_factor(self.minutes_so_far)
