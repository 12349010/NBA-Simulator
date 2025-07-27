# nba_sim/weights.py
import json
from pathlib import Path

# Path to the weights file
BASE_DIR = Path(__file__).parent.parent
WEIGHTS_FILE = BASE_DIR / 'factors.json'


def load() -> dict:
    """
    Load saved weight factors from the factors.json file.
    """
    if WEIGHTS_FILE.exists():
        with open(WEIGHTS_FILE, 'r') as f:
            return json.load(f)
    return {}


def get_weights() -> dict:
    """
    Alias for load(), return the current weight factors.
    """
    return load()


def save(factors: dict):
    """
    Save weight factors to the factors.json file.
    """
    with open(WEIGHTS_FILE, 'w') as f:
        json.dump(factors, f, indent=2)
