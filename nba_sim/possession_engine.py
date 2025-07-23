import random

def simulate_possession(off_team, def_team, game_state):
    """
    Returns a dict with 'points', 'shooter', and 'elapsed' (seconds).
    Very lightweight—for now ignores defense quality & fouls.
    """
    lineup = off_team.pick_lineup(int(game_state["minute"]))
    usages = [p.base_stats.get("USG%", 20) for p in lineup]
    shooter = random.choices(lineup, weights=usages, k=1)[0]

    # shot selection
    shot_type = random.choices(
        ["2pt", "3pt"],
        weights=[1 - shooter.tendencies["three_pt_rate"],
                 shooter.tendencies["three_pt_rate"]]
    )[0]
    made   = random.random() < shooter.effective_fg()
    points = (3 if shot_type == "3pt" else 2) if made else 0

    elapsed = random.randint(4, 24)
    shooter.minutes_so_far += elapsed / 60
    return {"points": points, "shooter": shooter.name, "elapsed": elapsed}
