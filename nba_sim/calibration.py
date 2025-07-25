import numpy as np
import pandas as pd
from pathlib import Path
import sqlite3

# Path to the SQLite DB
data_path = Path(__file__).parent.parent / "data" / "nba.sqlite"

# Weights module for calibration parameters
from nba_sim import weights as W


def _get_actual_score(game_id: int) -> tuple[int, int]:
    """
    Returns the actual final scores (home_pts, away_pts) from the game table for calibration.
    """
    con = sqlite3.connect(data_path)
    df = pd.read_sql(
        "SELECT pts_home, pts_away FROM game WHERE game_id = ?", con,
        params=(game_id,)
    )
    con.close()
    if df.empty:
        raise ValueError(f"No game entry for game_id={game_id}")
    row = df.iloc[0]
    return int(row["pts_home"]), int(row["pts_away"])


def calibrate(game_id: int, config: dict) -> dict:
    """
    Runs the simulator against a real game and computes calibration adjustments.
    Returns dict with 'sim_score', 'actual_score', and 'adjustments'.
    """
    # Run simulation (uses main.play_game underneath)
    sim = play_game({
        "home_team": config["home_team"],
        "away_team": config["away_team"],
        "game_date": config["game_date"],
        "fatigue_on": config.get("fatigue_on", True)
    }, seed=config.get("seed", None))

    sim_score = sim["Final Score"]
    actual_score = _get_actual_score(game_id)

    # Compute point differentials
    diff_sim = sim_score[config["home_team"]] - sim_score[config["away_team"]]
    diff_act = actual_score[0] - actual_score[1]

    # Simple linear adjustment factor
    factor = diff_act / diff_sim if diff_sim != 0 else 1.0

    # Return calibration results
    return {
        "sim_score": sim_score,
        "actual_score": actual_score,
        "adjustment_factor": factor,
        "weights_used": W.get_weights()
    }
