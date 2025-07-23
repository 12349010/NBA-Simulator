import random, numpy as np

def simulate_game(home, away, seed=None):
    """
    home / away : nba_sim.team_model.Team objects (contain Player objs)
    Returns dict with Final Score, box scores, quarter splits.
    """
    if seed is not None:
        random.seed(seed)

    clock = 0          # seconds
    quarter = 0
    score = {home.name:0, away.name:0}
    splits = [ [0,0,0,0] , [0,0,0,0] ]   # q1‑q4 pts for home/away

    offense_toggle = 0  # 0 = home start

    while clock < 48*60:
        off  = home if offense_toggle==0 else away
        deff = away if offense_toggle==0 else home

        # pick lineup & shooter
        lineup = off.pick_lineup(int(clock/60))
        if not lineup:
            lineup = off.players[:5]            # safety
        usages  = [ float(p.base_stats.get("USG%",20)) for p in lineup ]
        shooter = random.choices(lineup, weights=usages, k=1)[0]

        # decide shot type
        three_prob = shooter.tendencies["three_pt_rate"]
        shot_is_three = random.random() < three_prob

        # shot success prob
        p_make = shooter.effective_fg()
        # noise: mild home‑court + defensive randomness
        p_make *= 1.03 if off.is_home else 0.97
        p_make += random.uniform(-0.03,0.03)

        made = random.random() < p_make
        pts  = 3 if (made and shot_is_three) else (2 if made else 0)

        # update stats
        shooter.record_shot(made, shot_is_three)
        score[off.name] += pts
        splits[0 if off is home else 1][quarter] += pts

        # advance time
        poss_time = random.randint(4,23)
        clock += poss_time
        shooter.minutes_so_far += poss_time/60

        # quarter increment
        if clock//60 >= (quarter+1)*12 and quarter < 3:
            quarter += 1

        offense_toggle ^= 1   # switch sides

    # overtime not implemented yet (rare; v0.8 keeps regulation)
    box = {
        home.name: [p.game | {"Player":p.name} for p in home.players],
        away.name: [p.game | {"Player":p.name} for p in away.players]
    }
    return {
        "Final Score": score,
        "Quarter Splits": {
            "Home": splits[0],
            "Away": splits[1]
        },
        "Box Scores": box
    }

