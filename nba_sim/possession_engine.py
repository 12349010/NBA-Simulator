import numpy as np
import pandas as pd
import sqlite3
from pathlib import Path

from nba_sim.data_sqlite import get_roster, get_team_schedule, played_yesterday
from nba_sim.player_model import Player
from nba_sim.utils.roster_utils import assign_lineup

# Path to the SQLite DB
DB_PATH = Path(__file__).parent.parent / "data" / "nba.sqlite"


def _get_line_score(game_id: int) -> dict[str, list[int]]:
    """
    Fetches quarter-by-quarter scoring for a given game_id.
    """
    con = sqlite3.connect(DB_PATH)
    cols = [f"pts_qtr{i}_home" for i in range(1, 5)] + [f"pts_qtr{i}_away" for i in range(1, 5)]
    df = pd.read_sql(
        f"SELECT {', '.join(cols)} FROM line_score WHERE game_id = ?",
        con, params=(game_id,)
    )
    con.close()
    if df.empty:
        return {"home": [], "away": []}
    row = df.iloc[0]
    return {
        "home": [int(row[f"pts_qtr{i}_home"]) for i in range(1, 5)],
        "away": [int(row[f"pts_qtr{i}_away"]) for i in range(1, 5)]
    }


def simulate_game(home, away, game_date: str, config: dict) -> dict:
    """
    Simulates a 48-minute NBA game between home and away on game_date.
    Uses player-specific probabilities for shots and rebounds.
    Returns:
      - Final Score
      - Simulated Quarter Splits
      - Actual Quarter Splits
      - Box Scores
      - Fatigue Flags
      - Play Log (possession-level events)
    """
    rng = np.random.default_rng(config.get("seed"))

    # Determine season
    year, month = map(int, game_date.split("-")[:2])
    season = year + (1 if month >= 7 else 0)

    # Fatigue/back-to-back flags
    fat_h = played_yesterday(home.name, game_date)
    fat_a = played_yesterday(away.name, game_date)

    # Load rosters and instantiate Player objects
    raw_h = get_roster(home.name, season)
    home.players = [Player(name, season) for name in raw_h["starters"] + raw_h["bench"]]
    raw_a = get_roster(away.name, season)
    away.players = [Player(name, season) for name in raw_a["starters"] + raw_a["bench"]]

    # Smartly assign starters vs. bench
    home.starters, home.bench = assign_lineup(home.players)
    away.starters, away.bench = assign_lineup(away.players)
    lineup_home = home.starters.copy()
    lineup_away = away.starters.copy()

    # Tracking structures
    score = {home.name: 0, away.name: 0}
    qsplit = {
        home.name: {i: 0 for i in range(4)},
        away.name: {i: 0 for i in range(4)},
    }
    play_log = []
    clock = 0  # seconds elapsed
    quarter = 0

    def choose_rebounder(lineup):
        rates = np.array([p.reb_rate for p in lineup], dtype=float)
        if rates.sum() > 0:
            probs = rates / rates.sum()
        else:
            probs = np.ones(len(lineup)) / len(lineup)
        idx = rng.choice(len(lineup), p=probs)
        return lineup[idx]

    # Main simulation loop
    while quarter < 4:
        # Determine possession
        off = home if (clock // 24) % 2 == 0 else away
        lineup_off = lineup_home if off is home else lineup_away
        lineup_def = lineup_away if off is home else lineup_home

        # 1) Pick the shooter
        shooter = rng.choice(lineup_off)

        # 2) Decide shot type
        is3 = rng.random() < shooter.three_prop

        # 3) Determine make/miss
        pct = shooter.three_pct if is3 else shooter.fg_pct
        made = rng.random() < pct
        pts = 3 if (made and is3) else (2 if made else 0)

        # 4) Update shooter stats
        shooter.shot(made, is3)

        # 5) Assign rebound
        if made:
            rebounder = choose_rebounder(lineup_def)
        else:
            # 30% of misses are rebounded by offense
            if rng.random() < 0.3:
                rebounder = choose_rebounder(lineup_off)
            else:
                rebounder = choose_rebounder(lineup_def)
        rebounder.g["rebounds"] += 1

        # 6) Log event
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

        # 7) Update score
        score[off.name] += pts
        qsplit[off.name][quarter] += pts

        # 8) Advance clock and allocate minutes
        poss_time = int(rng.integers(4, 23))
        clock += poss_time
        for p in lineup_off:
            p.minutes_so_far += poss_time / 60

        # 9) Substitutions every 6 minutes
        if clock // 60 >= (quarter + 1) * 6:
            if off is home and home.bench:
                i = rng.integers(len(lineup_home))
                lineup_home[i], home.bench[0] = home.bench[0], lineup_home[i]
            if off is away and away.bench:
                i = rng.integers(len(lineup_away))
                lineup_away[i], away.bench[0] = away.bench[0], lineup_away[i]

        # 10) Next quarter check
        if clock // 60 >= (quarter + 1) * 12:
            quarter += 1

    # Actual splits from DB
    sched = get_team_schedule(home.name, season)
    target = pd.to_datetime(game_date).date()
    row = sched[sched["date"] == target]
    if not row.empty:
        gid = int(row["game_id"].iloc[0])
        actual = _get_line_score(gid)
    else:
        actual = {"home": [], "away": []}

    # Build final box scores
    box_scores = {
        home.name: [{**p.g, "Player": p.name} for p in home.players],
        away.name: [{**p.g, "Player": p.name} for p in away.players],
    }

    return {
        "Final Score": score,
        "Simulated Quarter Splits": qsplit,
        "Actual Quarter Splits": actual,
        "Box Scores": box_scores,
        "Fatigue Flags": {home.name: fat_h, away.name: fat_a},
        "Play Log": play_log
    }
