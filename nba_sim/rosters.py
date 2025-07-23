"""
Loads team rosters from rosters_2025.csv and exposes:
    get_team_list()           -> ["Boston Celtics", ...]
    get_roster(team, starters=True) -> list[str]
"""
import csv
from pathlib import Path

CSV = Path(__file__).resolve().parent / "rosters_2025.csv"
_CACHE = {"teams": [], "starters": {}, "bench": {}}

def _load():
    if _CACHE["teams"]:
        return
    with open(CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            tm = row["Team"]
            ply = row["Player"]
            is_start = row["Starter"] == "1"
            if tm not in _CACHE["teams"]:
                _CACHE["teams"].append(tm)
                _CACHE["starters"][tm] = []
                _CACHE["bench"][tm] = []
            (_CACHE["starters" if is_start else "bench"][tm]).append(ply)

def get_team_list():
    _load()
    return sorted(_CACHE["teams"])

def get_roster(team: str, starters=True):
    _load()
    return _CACHE["starters" if starters else "bench"].get(team, [])
