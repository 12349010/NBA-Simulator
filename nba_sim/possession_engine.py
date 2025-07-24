import random, numpy as np
from nba_sim.data_sqlite import roster as get_roster
from nba_sim.data_sqlite import get_team_list, team_schedule as get_team_schedule
from nba_sim.data_sqlite import played_yesterday
from nba_sim.data_sqlite import play_by_play
import pandas as pd, datetime as dt

def played_yesterday(team: str, game_date: str) -> bool:
    sched = get_team_schedule(team)
    if sched.empty:
        return False
    gd = pd.to_datetime(game_date).date()
    return (gd - dt.timedelta(days=1)) in sched["startDate"].dt.date.values

def _def_adj(team_def:dict)->float:
    drtg, opo = team_def["DRtg"], team_def["Opp_eFG"]
    return 1 - (drtg-113)/500 - (opo-0.535)/5   # clamp happens later

def simulate_game(home, away, game_date:str, fatigue_on=True, seed:int|None=None):
    if seed is not None: random.seed(seed)
    season=int(game_date[:4])+(1 if int(game_date[5:7])>=7 else 0)
    def_h=get_team_defense(home.name,season)
    def_a=get_team_defense(away.name,season)
    adj_h=_def_adj(def_h); adj_a=_def_adj(def_a)
    fat_h = played_yesterday(home.name, game_date) if fatigue_on else False
    fat_a = played_yesterday(away.name, game_date) if fatigue_on else False

    clock=0; quarter=0
    score={home.name:0, away.name:0}
    qsplit={home.name:[0,0,0,0], away.name:[0,0,0,0]}
    minute_targets=[34,34,34,34,34,22,22,22]
    home.players+=home.players[5:8]; away.players+=away.players[5:8]

    rng=np.random.default_rng(seed)

    while clock<48*60:
        off, deff, adj, fat = ((home,away,adj_a,fat_h) if (clock//24)%2==0
                               else (away,home,adj_h,fat_a))
        lineup=[]
        for p,mt in zip(off.players, minute_targets):
            if p.minutes_so_far<mt and len(lineup)<5: lineup.append(p)
        if len(lineup)<5: lineup=off.players[:5]

        shooter=rng.choice(lineup, p=np.array([p.base_stats.get("USG%",20) for p in lineup]))
        is3=rng.random()<shooter.tendencies["three_pt_rate"]
        p_make=shooter.eff_fg()*adj
        if fat: p_make*=0.95
        p_make+=rng.uniform(-0.02,0.02)
        p_make=np.clip(p_make,0.25,0.75)
        made=rng.random()<p_make
        pts=3 if (made and is3) else (2 if made else 0)
        shooter.shot(made,is3); shooter.misc()
        score[off.name]+=pts; qsplit[off.name][quarter]+=pts
        poss=rng.integers(4,23); clock+=poss
        for p in lineup: p.minutes_so_far+=poss/60
        if clock//60>=(quarter+1)*12 and quarter<3: quarter+=1

    return {"Final Score":score,
            "Quarter Splits":qsplit,
            "Box Scores": {
                home.name:[p.g|{"Player":p.name} for p in home.players],
                away.name:[p.g|{"Player":p.name} for p in away.players]
            },
            "Fatigue Flags": {home.name:fat_h, away.name:fat_a}}
