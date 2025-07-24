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
    Returns simulated results, actual splits, box scores, and fatigue flags.
    """
    # RNG init
    rng = np.random.default_rng(config.get("seed", None))

    # Season calculation: if month>=7 then next year-based season id
    year, month = map(int, game_date.split("-")[:2])
    season = year + (1 if month >= 7 else 0)

    # Fatigue/back-to-back flags
    fat_h = played_yesterday(home.name, game_date)
    fat_a = played_yesterday(away.name, game_date)

    # Load rosters and instantiate Player objects
    roster_h = get_roster(home.name, season)
    home.players = [Player(name, season) for name in roster_h["starters"] + roster_h["bench"]]
    roster_a = get_roster(away.name, season)
    away.players = [Player(name, season) for name in roster_a["starters"] + roster_a["bench"]]

    # Define lineups
    lineup_home = home.players[:5]
    lineup_away = away.players[:5]

    # Initialize simulation trackers
    score_sim = {home.name: 0, away.name: 0}
    qsplit_sim = {home.name: {i: 0 for i in range(4)}, away.name: {i: 0 for i in range(4)}}
    clock = 0  # seconds elapsed
    quarter = 0

    # Run possession-by-possession simulation
    while quarter < 4:
        # Offense team alternates roughly on clock/24 but can be improved
        off = home if (clock // 24) % 2 == 0 else away
        lineup = lineup_home if off is home else lineup_away

        # Determine shot outcome based on flat probabilities (placeholder)
        made = rng.random() < 0.45
        is3 = rng.random() < 0.35
        pts = 3 if (made and is3) else (2 if made else 0)

        # Choose shooter and update stats
        shooter = lineup[rng.integers(len(lineup))]
        shooter.shot(made, is3)
        shooter.misc()
        score_sim[off.name] += pts
        qsplit_sim[off.name][quarter] += pts

        # Advance clock by possession duration
        poss_time = int(rng.integers(4, 23))
        clock += poss_time
        for p in lineup:
            p.minutes_so_far += poss_time / 60

        # Move to next quarter when time threshold met
        if (clock // 60) >= (quarter + 1) * 12 and quarter < 3:
            quarter += 1

    # Retrieve actual quarter splits from DB
    sched = get_team_schedule(home.name, season)
    target_date = pd.to_datetime(game_date).date()
    matches = sched[sched["date"] == target_date]
    if matches.empty:
        actual_splits = {"home": [], "away": []}
    else:
        gid = int(matches["game_id"].iloc[0])
        actual_splits = _get_line_score(gid)

    # Build box scores from Player.g stats
    box_home = [{**p.g, "Player": p.name} for p in home.players]
    box_away = [{**p.g, "Player": p.name} for p in away.players]

    return {
        "Final Score (Simulated)": score_sim,
        "Simulated Quarter Splits": qsplit_sim,
        "Actual Quarter Splits": actual_splits,
        "Box Scores": {home.name: box_home, away.name: box_away},
        "Fatigue Flags": {home.name: fat_h, away.name: fat_a}
    }
