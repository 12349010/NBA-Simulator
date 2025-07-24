import random, numpy as np
from nba_sim.data_sqlite import (
    get_team_list,      # for populating your team dropdown
    get_roster,         # to fetch starters & bench
    get_team_schedule,  # for fatigue / schedule lookups
    played_yesterday,   # to check back‑to‑back games
    play_by_play        # (if/when you need play‑by‑play data)
)
import pandas as pd, datetime as dt

def played_yesterday(team: str, game_date: str) -> bool:
    sched = get_team_schedule(team)
    if sched.empty:
        return False
    gd = pd.to_datetime(game_date).date()
    return (gd - dt.timedelta(days=1)) in sched["startDate"].dt.date.values


def simulate_game(home, away, date, config):
    # initialize RNG
    rng = np.random.default_rng(config.get("seed"))

    # check fatigue/back-to-back
    fat_h = played_yesterday(home.name, date)
    fat_a = played_yesterday(away.name, date)

    # load rosters
    home.players = get_roster(home.name, date)
    away.players = get_roster(away.name, date)

    # set starters/bench
    # TODO: verify bench logic
    lineup_home = [p for p in home.players if p.starter]
    lineup_away = [p for p in away.players if p.starter]

    # possession simulation
    score = {home.name: 0, away.name: 0}
    qsplit = {home.name: {i: 0 for i in range(4)}, away.name: {i: 0 for i in range(4)}}
    clock = 0.0
    quarter = 0

    while quarter < 4:
        # simulate a single possession
        off = home if quarter % 2 == 0 else away
        defn = away if off is home else home
        lineup = lineup_home if off is home else lineup_away
        # placeholder: random outcome
        made = rng.random() < 0.45
        is3 = rng.random() < 0.35
        pts = 3 if (made and is3) else (2 if made else 0)
        shooter = lineup[rng.integers(len(lineup))]
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
