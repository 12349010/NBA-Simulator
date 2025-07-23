from dataclasses import dataclass, field
import numpy as np, pandas as pd
from .stats_live import get_stats, get_tendencies
from .utils.age_curve import age_multiplier
from .utils.fatigue import fatigue_factor
from .utils.injury import get_status, minutes_cap

_STAT_KEYS = ["PTS","FGA","FGM","3PA","3PM","REB","AST","STL","BLK","TO"]

@dataclass
class Player:
    name: str
    season: int
    base_stats: pd.Series = field(init=False)
    tendencies: dict      = field(init=False)
    status: str           = field(init=False)
    cap: int              = field(init=False)
    minutes_so_far: float = 0.0
    g: dict               = field(default_factory=lambda:{k:0 for k in _STAT_KEYS})

    def __post_init__(self):
        self.base_stats = get_stats(self.name, self.season)
        self.tendencies = get_tendencies(self.name, self.season)
        self.status     = get_status(self.name)
        self.cap        = minutes_cap(self.status)

    # ----- dynamic efficiencies -----
    def eff_fg(self):           # clamp 25‑75 %
        raw=float(self.base_stats.get("FG%",.45))
        mod=age_multiplier(int(self.base_stats.get("Age",27)))*fatigue_factor(self.minutes_so_far)
        return max(.25,min(.75,raw*mod))

    # ----- update helpers -----
    def shot(self, made:bool,is3:bool):
        self.g["FGA"]+=1
        if made:
            self.g["FGM"]+=1
            self.g["PTS"]+=3 if is3 else 2
        if is3:
            self.g["3PA"]+=1
            if made:self.g["3PM"]+=1

    def misc(self):             # single possession misc stat draws
        # Poisson around per‑game averages scaled to 100 possessions
        scale=1/100
        self.g["REB"]+=np.random.poisson(float(self.base_stats.get("TRB",4))*scale)
        self.g["AST"]+=np.random.poisson(float(self.base_stats.get("AST",3))*scale)
        self.g["STL"]+=np.random.poisson(float(self.base_stats.get("STL",1))*scale)
        self.g["BLK"]+=np.random.poisson(float(self.base_stats.get("BLK",0.5))*scale)
        self.g["TO" ]+=np.random.poisson(float(self.base_stats.get("TOV",2))*scale)
