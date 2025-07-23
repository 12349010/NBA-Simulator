"""
Centralised weight dictionary so calibration can update it then persist.
"""
import json, os
from pathlib import Path

WEIGHTS_FILE = Path(__file__).resolve().parent / "weights.json"

# default startup weights
DEFAULT = {
    "player_base_stats": 0.25,
    "player_tendencies": 0.20,
    "recent_form":       0.15,
    "age_regression":    0.05,
    "home_away_bias":    0.10,
    "coach_impact":      0.10,
    "chemistry":         0.05,
    "random_variance":   0.10
}

def load():
    if WEIGHTS_FILE.exists():
        with open(WEIGHTS_FILE) as f:
            return json.load(f)
    return DEFAULT.copy()

def save(w: dict):
    with open(WEIGHTS_FILE, "w") as f:
        json.dump(w, f, indent=2)
