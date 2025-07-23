import numpy as np, math, random

def simulate_game(home, away, travel_fatigue:dict|None=None, seed:int|None=None):
    """
    travel_fatigue: {"home":bool,"away":bool} – True if played yesterday.
    """
    if seed is not None: random.seed(seed)
    if travel_fatigue is None: travel_fatigue={"home":False,"away":False}

    clock=0        # seconds
    quarter=0
    score={home.name:0, away.name:0}
    qsplit={home.name:[0,0,0,0], away.name:[0,0,0,0]}

    # minute targets: starters 34, bench3 22
    minute_targets=[34,34,34,34,34,22,22,22]
    home.players+=home.players[5:8]   # ensure 8 man if short
    away.players+=away.players[5:8]

    idx_h=idx_a=[0]*8  # track minutes

    rand=np.random.default_rng(seed)

    while clock<48*60:
        off,idx_o,targ_o,fatigue_flag = (home,idx_h,minute_targets,travel_fatigue["home"]) \
                                        if (clock//24)%2==0 else \
                                       (away,idx_a,minute_targets,travel_fatigue["away"])
        lineup=[]
        # simple rotation: pick next 5 players meeting minute limits
        for p,mt in zip(off.players,targ_o):
            if p.minutes_so_far<mt and len(lineup)<5:
                lineup.append(p)
        if len(lineup)<5: lineup=off.players[:5]

        # choose shooter
        usages=[float(p.base_stats.get("USG%",20)) for p in lineup]
        shooter=rand.choice(lineup,p=np.array(usages)/sum(usages))

        # shot type
        is3=rand.random()<shooter.tendencies["three_pt_rate"]
        p_make=shooter.eff_fg()
        if fatigue_flag: p_make*=0.95            # back‑to‑back penalty
        p_make+=rand.uniform(-0.025,0.025)       # random noise
        made=rand.random()<p_make
        pts=3 if (made and is3) else 2 if made else 0

        shooter.shot(made,is3)
        shooter.misc()

        score[off.name]+=pts
        qsplit[off.name][quarter]+=pts

        # advance time
        poss=rand.integers(4,23)
        clock+=poss
        for p in lineup: p.minutes_so_far+=poss/60

        if clock//60>= (quarter+1)*12 and quarter<3: quarter+=1

    return {
        "Final Score":score,
        "Quarter Splits":qsplit,
        "Box Scores": {
            home.name:[p.g|{"Player":p.name} for p in home.players],
            away.name:[p.g|{"Player":p.name} for p in away.players]
        }
    }
