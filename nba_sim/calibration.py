"""
Calibrate the sim so its mean final scores match an actual game.
We adjust two knobs:
    - random_variance weight
    - home_away_bias weight
"""
import optuna, numpy as np
from . import weights as W
from main import play_game

def _objective(trial, cfg, actual_home, actual_away, runs=150):
    # propose new weights
    w = W.load()
    w["random_variance"] = trial.suggest_float("rand", 0.05, 0.25)
    w["home_away_bias"]  = trial.suggest_float("homebias", 0.05, 0.20)

    # monkey‑patch global weights in memory
    W.save(w)          # save, so play_game sees new values

    res_home, res_away = [], []
    for _ in range(runs):
        out = play_game(cfg)
        res_home.append(out["Final Score"][cfg["home_team"]])
        res_away.append(out["Final Score"][cfg["away_team"]])
    err = abs(np.mean(res_home) - actual_home) + abs(np.mean(res_away) - actual_away)
    return err

def calibrate(cfg, actual_home, actual_away, n_trials=25):
    study = optuna.create_study(direction="minimize")
    study.optimize(lambda tr: _objective(tr, cfg, actual_home, actual_away), n_trials=n_trials)
    best_w = W.load()
    return best_w, study.best_value
