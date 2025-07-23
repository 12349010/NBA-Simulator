"""
calibration.py – weight‑tuner for NBA sim engine
------------------------------------------------
Usage:

    best_w, mae = calibrate(cfg, auto=True)                   # auto score lookup
    best_w, mae = calibrate(cfg, actual_home=101, actual_away=98, cal_trials=30)
"""
from __future__ import annotations
import random, copy, json, pathlib
from typing import Tuple
import numpy as np

from nba_sim import weights as W
from nba_sim.past_games_live import get_score
from main import play_game


DEFAULT_TRIALS = 25
RADIUS = 0.10                 # ±10 % per weight


def _sample_weights(base: dict[str, float]) -> dict[str, float]:
    """Return a dict with each weight adjusted ±RADIUS% randomly."""
    return {k: v * (1 + random.uniform(-RADIUS, RADIUS)) for k, v in base.items()}


def _mae(pred_home: float, pred_away: float, true_home: float, true_away: float) -> float:
    return abs(pred_home - true_home) + abs(pred_away - true_away) / 2


def calibrate(
    cfg: dict,
    *,
    auto: bool = False,
    actual_home: int | None = None,
    actual_away: int | None = None,
    cal_trials: int = DEFAULT_TRIALS,
) -> Tuple[dict[str, float], float]:
    """
    Returns (best_weight_dict, best_mae).
    cfg is the same dict passed to play_game().
    """

    # ---------- 1. determine target score ----------
    if auto:
        scr = get_score(cfg["home_team"], cfg["away_team"], cfg["game_date"])
        if scr is None:
            raise ValueError("Could not locate real score for that matchup/date.")
        target_home, target_away = scr["home"], scr["away"]
    else:
        if actual_home is None or actual_away is None:
            raise ValueError("Provide actual_home & actual_away or use auto=True.")
        target_home, target_away = actual_home, actual_away

    # ---------- 2. search weight space ----------
    best_err = float("inf")
    best_w = copy.deepcopy(W.DEFAULT)

    for _ in range(cal_trials):
        test_w = _sample_weights(W.DEFAULT)
        W.save(test_w)

        g = play_game(cfg, seed=random.randint(0, 999_999))
        pred_home = g["Final Score"][cfg["home_team"]]
        pred_away = g["Final Score"][cfg["away_team"]]

        err = _mae(pred_home, pred_away, target_home, target_away)
        if err < best_err:
            best_err = err
            best_w = test_w

    # ---------- 3. persist best weights ----------
    W.save(best_w)
    _persist(best_w, best_err, cfg, target_home, target_away)
    return best_w, best_err


# ---------- simple persistence ----------
CALIB_LOG = pathlib.Path(__file__).with_name("calib_history.json")


def _persist(w: dict[str, float], mae: float, cfg: dict, th: int, ta: int):
    rec = {
        "cfg": {
            "date": cfg["game_date"],
            "home": cfg["home_team"],
            "away": cfg["away_team"],
        },
        "target": {"home": th, "away": ta},
        "mae": round(mae, 3),
        "weights": w,
    }

    hist = []
    if CALIB_LOG.exists():
        hist = json.loads(CALIB_LOG.read_text())
    hist.append(rec)
    CALIB_LOG.write_text(json.dumps(hist, indent=2))
