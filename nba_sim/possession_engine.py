import numpy as np
import pandas as pd

from nba_sim.data_csv import get_roster, get_team_schedule, iter_play_by_play
from nba_sim.data_sqlite import played_yesterday  # if still needed for fatigue logic
from nba_sim.player_model import Player
from nba_sim.utils.roster_utils import assign_lineup

# Load full line_score table once
from nba_sim.data_csv import _line_score_df  # private import of module‑level DataFrame


def _get_line_score(game_id: int) -> dict[str, list[int]]:
    """
    Fetches quarter-by-quarter scoring for a given game_id using CSV data.
    """
    df = _line_score_df[_line_score_df['game_id'] == game_id]
    if df.empty:
        return {"home": [], "away": []}
    row = df.iloc[0]
    home_scores = [int(row[f"pts_qtr{i}_home"]) for i in range(1, 5)]
    away_scores = [int(row[f"pts_qtr{i}_away"]) for i in range(1, 5)]
    return {"home": home_scores, "away": away_scores}


def simulate_game(home, away, game_date: str, config: dict) -> dict:
    """
    Simulates a 48-minute NBA game between home and away on game_date.
    Returns final results and play log.
    """
    rng = np.random.default_rng(config.get("seed"))

    # Determine season from date
    year, month = map(int, game_date.split("-")[:2])
    season = year + (1 if month >= 7 else 0)

    # Fatigue/back-to-back flags
    fat_h = played_yesterday(home.name, game_date)
    fat_a = played_yesterday(away.name, game_date)

    # Load rosters via CSV
    raw_h = get_roster(home.name, season)
    home.players = [Player(name, season) for name in raw_h.get("players", [])]
    raw_a = get_roster(away.name, season)
    away.players = [Player(name, season) for name in raw_a.get("players", [])]

    # Assign starters vs. bench
    home.starters, home.bench = assign_lineup(home.players)
    away.starters, away.bench = assign_lineup(away.players)
    lineup_home = home.starters.copy()
    lineup_away = away.starters.copy()

    # Tracking
    score = {home.name: 0, away.name: 0}
    qsplit = {home.name: {i: 0 for i in range(4)}, away.name: {i: 0 for i in range(4)}}
    play_log = []
    clock = 0
    quarter = 0

    def choose_rebounder(lineup):
        rates = np.array([p.reb_rate for p in lineup], dtype=float)
        probs = rates / rates.sum() if rates.sum() > 0 else np.ones(len(lineup)) / len(lineup)
        idx = rng.choice(len(lineup), p=probs)
        return lineup[idx]

    # Main loop
    while quarter < 4:
        off = home if (clock // 24) % 2 == 0 else away
        def_lineup = lineup_away if off is home else lineup_home
        off_lineup = lineup_home if off is home else lineup_away

        shooter = rng.choice(off_lineup)
        is3 = rng.random() < shooter.three_prop
        pct = shooter.three_pct if is3 else shooter.fg_pct
        made = rng.random() < pct
        pts = 3 if (made and is3) else (2 if made else 0)

        shooter.shot(made, is3)
        if made:
            rebounder = choose_rebounder(def_lineup)
        else:
            if rng.random() < 0.3:
                rebounder = choose_rebounder(off_lineup)
            else:
                rebounder = choose_rebounder(def_lineup)
        rebounder.g["rebounds"] += 1

        rem = max(0, 48 * 60 - clock)
        m, s = divmod(rem, 60)
        action = f"{'made' if made else 'missed'} {'3-pt' if is3 else '2-pt'}"
        play_log.append({
            "quarter": quarter + 1,
            "time": f"{m}:{s:02d}",
            "team": off.name,
            "player": shooter.name,
            "action": action,
            "points": pts,
            "rebound": rebounder.name
        })

        score[off.name] += pts
        qsplit[off.name][quarter] += pts

        poss_time = int(rng.integers(4, 23))
        clock += poss_time
        for p in off_lineup:
            p.minutes_so_far += poss_time / 60

        if clock // 60 >= (quarter + 1) * 6:
            if off is home and home.bench:
                i = rng.integers(len(lineup_home))
                lineup_home[i], home.bench[0] = home.bench[0], lineup_home[i]
            if off is away and away.bench:
                i = rng.integers(len(lineup_away))
                lineup_away[i], away.bench[0] = away.bench[0], lineup_away[i]

        if clock // 60 >= (quarter + 1) * 12:
            quarter += 1

    # Actual quarter splits via CSV
    sched = get_team_schedule(home.name, season)
    row = sched[sched['game_date'] == pd.to_datetime(game_date)]
    if not row.empty:
        gid = int(row['game_id'].iloc[0])
        actual = _get_line_score(gid)
    else:
        actual = {"home": [], "away": []}

    # Box scores
    box_scores = {
        home.name: [{**p.g, "Player": p.name} for p in home.players],
        away.name: [{**p.g, "Player": p.name} for p in away.players]
    }

    return {
        "Final Score": score,
        "Simulated Quarter Splits": qsplit,
        "Actual Quarter Splits": actual,
        "Box Scores": box_scores,
        "Fatigue Flags": {home.name: fat_h, away.name: fat_a},
        "Play Log": play_log
    }
