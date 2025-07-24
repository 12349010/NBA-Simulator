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

# Path to the SQLite DB for direct queries if needed
from pathlib import Path
import sqlite3
DB_PATH = Path(__file__).parent.parent / "data" / "nba.sqlite"


def _get_line_score(game_id: int) -> dict[str, list[int]]:
    """
    Fetches quarter-by-quarter scoring for a given game_id from the line_score table.
    Returns a dict with keys 'home' and 'away', each mapping to a list of 4 quarterly point totals.
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
    Simulates a 48-minute NBA game between home and away teams on game_date.
    Returns a dict containing final score, quarter splits (simulated), box scores, and fatigue flags.
    """
    # RNG setup
    rng = np.random.default_rng(config.get("seed", None))

    # Season calculation for schedule lookup
    season = int(game_date[:4]) + (1 if int(game_date[5:7]) >= 7 else 0)

    # Fatigue/back-to-back check
    fat_h = played_yesterday(home.name, game_date)
    fat_a = played_yesterday(away.name, game_date)

    # Load rosters (starters + bench)
    rost_h = get_roster(home.name, season)
    rost_a = get_roster(away.name, season)
    home.players = rost_h["starters"] + rost_h["bench"]
    away.players = rost_a["starters"] + rost_a["bench"]

    # Ensure we have Player objects
    home.players = home.players
    away.players = away.players

    # Setup lineups
    lineup_home = home.players[:5]
    lineup_away = away.players[:5]

    # Initialize tracking
    score = {home.name: 0, away.name: 0}
    qsplit = {home.name: {i: 0 for i in range(4)}, away.name: {i: 0 for i in range(4)}}
    clock = 0  # seconds elapsed
    quarter = 0

    # Core possession loop
    while quarter < 4:
        # Determine which team has the ball
        off = home if (clock // 24) % 2 == 0 else away
        lineup = lineup_home if off is home else lineup_away

        # Random shot outcome parameters (placeholder)
        made = rng.random() < 0.45
        is3 = rng.random() < 0.35
        pts = 3 if (made and is3) else (2 if made else 0)

        # Assign points and update player stats
        shooter = lineup[rng.integers(len(lineup))]
        shooter.shot(made, is3)
        shooter.misc()
        score[off.name] += pts
        qsplit[off.name][quarter] += pts

        # Advance clock by possession length
        poss = int(rng.integers(4, 23))
        clock += poss
        for p in lineup:
            p.minutes_so_far += poss / 60

        # Move to next quarter if time threshold reached
        if (clock // 60) >= (quarter + 1) * 12 and quarter < 3:
            quarter += 1

    # Fetch actual line_score for calibration/testing if needed
    # schedule_df = get_team_schedule(home.name, season)
    # gid = schedule_df.loc[schedule_df['date'] == pd.to_datetime(game_date).date(), 'game_id'].iloc[0]
    # actual_q = _get_line_score(gid)

    # Return simulation results
    return {
        "Final Score": score,
        "Quarter Splits": qsplit,
        "Box Scores": {
            home.name: [{**p.g, "Player": p.name} for p in home.players],
            away.name: [{**p.g, "Player": p.name} for p in away.players]
        },
        "Fatigue Flags": {home.name: fat_h, away.name: fat_a}
    }
