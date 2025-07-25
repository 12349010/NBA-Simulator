import random
import numpy as np
import pandas as pd
import datetime as dt
from nba_sim.data_sqlite import (
    get_team_list,
    get_roster,
    get_team_schedule,
    played_yesterday,
    play_by_play
)
from nba_sim.player_model import Player
from nba_sim.utils.roster_utils import assign_lineup
from pathlib import Path
import sqlite3

# Path to the SQLite DB
DB_PATH = Path(__file__).parent.parent / "data" / "nba.sqlite"


def _get_line_score(game_id: int) -> dict[str, list[int]]:
    """
    Fetches quarter-by-quarter scoring for a given game_id from line_score.
    Returns a dict with 'home' and 'away' lists of points per quarter.
    """
    con = sqlite3.connect(DB_PATH)
    cols = [f"pts_qtr{i}_home" for i in range(1,5)] + [f"pts_qtr{i}_away" for i in range(1,5)]
    df = pd.read_sql(
        f"SELECT {', '.join(cols)} FROM line_score WHERE game_id = ?", con,
        params=(game_id,)
    )
    con.close()
    if df.empty:
        raise ValueError(f"No line_score entry for game_id={game_id}")
    row = df.iloc[0]
    return {
        "home": [int(row[f"pts_qtr{i}_home"]) for i in range(1,5)],
        "away": [int(row[f"pts_qtr{i}_away"]) for i in range(1,5)]
    }


def simulate_game(home, away, game_date: str, config: dict) -> dict:
    """
    Simulates a 48-minute NBA game between home and away on game_date.
    Automatically assigns starters vs bench, rotates bench into play, and returns stats.

    Returns dict with:
      - "Final Score"
      - "Simulated Quarter Splits"
      - "Actual Quarter Splits"
      - "Box Scores"
      - "Fatigue Flags"
    """
    # RNG init
    rng = np.random.default_rng(config.get("seed", None))

    # Season calculation
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

    # Assign smart starters vs bench
    home.starters, home.bench = assign_lineup(home.players)
    away.starters, away.bench = assign_lineup(away.players)

    # Working lineups (modifiable for rotation)
    lineup_home = home.starters.copy()
    lineup_away = away.starters.copy()

    # Simulation trackers
    score_sim = {home.name: 0, away.name: 0}
    qsplit_sim = {home.name: {i: 0 for i in range(4)}, away.name: {i: 0 for i in range(4)}}
    clock = 0  # seconds elapsed
    quarter = 0

    # Bench rotation every 6 minutes of game time
    SUB_FREQ = 6 * 60
    next_sub_time_h = SUB_FREQ
    next_sub_time_a = SUB_FREQ

    # Possession-by-possession simulation
    while quarter < 4:
        # Choose offense team
        off = home if (clock // 24) % 2 == 0 else away
        lineup = lineup_home if off is home else lineup_away

        # Random shot outcome (placeholder probabilities)
        made = rng.random() < 0.45
        is3 = rng.random() < 0.35
        pts = 3 if (made and is3) else (2 if made else 0)

        # Update shooter stats
        shooter = lineup[rng.integers(len(lineup))]
        shooter.shot(made, is3)
        shooter.misc()
        score_sim[off.name] += pts
        qsplit_sim[off.name][quarter] += pts

        # Advance clock
        poss_time = int(rng.integers(4, 23))
        clock += poss_time
        for p in lineup:
            p.minutes_so_far += poss_time / 60

        # Handle bench substitutions
        # Home substitutions
        if clock >= next_sub_time_h and home.bench:
            out = rng.choice(lineup_home)
            inp = rng.choice(home.bench)
            idx = lineup_home.index(out)
            lineup_home[idx] = inp
            home.bench[home.bench.index(inp)] = out
            next_sub_time_h += SUB_FREQ
        # Away substitutions (use same clock)
        if clock >= next_sub_time_a and away.bench:
            out = rng.choice(lineup_away)
            inp = rng.choice(away.bench)
            idx = lineup_away.index(out)
            lineup_away[idx] = inp
            away.bench[away.bench.index(inp)] = out
            next_sub_time_a += SUB_FREQ

        # Advance quarter
        if clock // 60 >= (quarter + 1) * 12:
            quarter += 1

    # Retrieve actual quarter splits
    sched = get_team_schedule(home.name, season)
    target_date = pd.to_datetime(game_date).date()
    matches = sched[sched["date"] == target_date]
    if matches.empty:
        actual_splits = {"home": [], "away": []}
    else:
        gid = int(matches["game_id"].iloc[0])
        actual_splits = _get_line_score(gid)

    # Build box scores
    box_home = [{**p.g, "Player": p.name} for p in home.players]
    box_away = [{**p.g, "Player": p.name} for p in away.players]

    return {
        "Final Score": score_sim,
        "Simulated Quarter Splits": qsplit_sim,
        "Actual Quarter Splits": actual_splits,
        "Box Scores": {home.name: box_home, away.name: box_away},
        "Fatigue Flags": {home.name: fat_h, away.name: fat_a}
    }
