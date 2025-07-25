import random
import numpy as np
import pandas as pd
import datetime as dt
from nba_sim.data_sqlite import (
    get_roster,
    get_team_schedule,
    played_yesterday
)
from nba_sim.player_model import Player
from nba_sim.utils.roster_utils import assign_lineup
from pathlib import Path
import sqlite3

# Path to SQLite DB
data_path = Path(__file__).parent.parent / "data" / "nba.sqlite"


def _get_line_score(game_id: int) -> dict[str, list[int]]:
    """
    Fetches quarter-by-quarter scoring for a given game_id.
    """
    con = sqlite3.connect(data_path)
    cols = [f"pts_qtr{i}_home" for i in range(1,5)] + [f"pts_qtr{i}_away" for i in range(1,5)]
    df = pd.read_sql(
        f"SELECT {', '.join(cols)} FROM line_score WHERE game_id = ?", con,
        params=(game_id,)
    )
    con.close()
    if df.empty:
        raise ValueError(f"No line_score for game_id={game_id}")
    row = df.iloc[0]
    return {"home": [row[f"pts_qtr{i}_home"] for i in range(1,5)],
            "away": [row[f"pts_qtr{i}_away"] for i in range(1,5)]}


def simulate_game(home, away, game_date: str, config: dict) -> dict:
    """
    Runs a 48-min NBA game sim with play-by-play logging.
    Returns final score, splits, box scores, fatigue flags, and "Play Log".
    """
    rng = np.random.default_rng(config.get("seed"))

    # Season
    year, month = map(int, game_date.split("-")[:2])
    season = year + (1 if month >= 7 else 0)

    # Fatigue flags
    fat_h = played_yesterday(home.name, game_date)
    fat_a = played_yesterday(away.name, game_date)

    # Rosters -> Player objects
    raw_h = get_roster(home.name, season)
    home.players = [Player(n, season) for n in raw_h["starters"] + raw_h["bench"]]
    raw_a = get_roster(away.name, season)
    away.players = [Player(n, season) for n in raw_a["starters"] + raw_a["bench"]]

    # Assign starters/bench
    home.starters, home.bench = assign_lineup(home.players)
    away.starters, away.bench = assign_lineup(away.players)
    lineup_home = home.starters.copy()
    lineup_away = away.starters.copy()

    # Trackers
    score = {home.name: 0, away.name: 0}
    qsplit = {home.name: {i: 0 for i in range(4)}, away.name: {i: 0 for i in range(4)}}
    play_log: list[dict] = []
    clock = 0
    quarter = 0

    # Sub rotation every 6 minutes
    SUB = 6*60
    next_sub = SUB

    # Simulate
    while quarter < 4:
        off = home if (clock // 24) % 2 == 0 else away
        lineup = lineup_home if off is home else lineup_away

        # Shot outcome
        made = rng.random() < 0.45
        is3 = rng.random() < 0.35
        pts = 3 if made and is3 else 2 if made else 0

        # Choose shooter
        shooter = lineup[rng.integers(len(lineup))]
        shooter.shot(made, is3)
        shooter.misc()

        # Log event
        rem = max(0, 48*60 - clock)
        m, s = divmod(rem, 60)
        action = (
            f"made {'3-pt' if is3 else '2-pt'}"
            if made else f"missed {'3-pt' if is3 else '2-pt'}"
        )
        play_log.append({
            "quarter": quarter+1,
            "time": f"{m}:{s:02d}",
            "team": off.name,
            "player": shooter.name,
            "action": action,
            "points": pts
        })

        # Update score
        score[off.name] += pts
        qsplit[off.name][quarter] += pts

        # Advance clock
        dt = int(rng.integers(4,23))
        clock += dt
        for p in lineup:
            p.minutes_so_far += dt/60

        # Subs
        if clock >= next_sub and home.bench:
            i = rng.integers(len(lineup_home))
            lineup_home[i], home.bench[0] = home.bench[0], lineup_home[i]
            next_sub += SUB
        if clock >= next_sub and away.bench:
            i = rng.integers(len(lineup_away))
            lineup_away[i], away.bench[0] = away.bench[0], lineup_away[i]

        # Advance quarter
        if clock//60 >= (quarter+1)*12:
            quarter += 1

    # Actual splits
    sched = get_team_schedule(home.name, season)
    tgt = pd.to_datetime(game_date).date()
    row = sched[sched['date']==tgt]
    actual = _get_line_score(int(row['game_id'].iloc[0])) if not row.empty else {"home":[],"away":[]}

    # Box scores
    box = {
        home.name: [{**p.g, 'Player': p.name} for p in home.players],
        away.name: [{**p.g, 'Player': p.name} for p in away.players]
    }

    return {
        "Final Score": score,
        "Simulated Quarter Splits": qsplit,
        "Actual Quarter Splits": actual,
        "Box Scores": box,
        "Fatigue Flags": {home.name: fat_h, away.name: fat_a},
        "Play Log": play_log
    }
