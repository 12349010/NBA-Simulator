"""
rosters_local.py  – read active rosters from data/players.json committed
with the repo (refreshed nightly by GitHub Action).

Public helpers
--------------
get_team_list()           -> list[str]
get_roster(team_name:str) -> dict{starters, bench}
"""

from __future__ import annotations
import json, logging
from pathlib import Path
from typing import Dict, List

# ------- locate the data file -------
PKG_DIR = Path(__file__).parent
DATA    = (PKG_DIR.parent / "data" / "players.json").resolve()

if DATA.exists() and DATA.stat().st_size > 0:          # ← check size
    with open(DATA, "r") as f:
        try:
            PLAYERS_RAW = json.load(f)\
                           .get("league", {})\
                           .get("standard", [])
        except json.JSONDecodeError as e:
            logging.warning(f"Malformed players.json ({e}); using stub.")
            PLAYERS_RAW = []
else:
    logging.warning("players.json missing or empty; using stub roster.")
    PLAYERS_RAW = []

# teamId -> full team name (single source of truth)
TEAM_NAME: Dict[int, str] = {
    int(p["teamId"]): p["teamSitesOnly"]["teamName"] + " " +
                     p["teamSitesOnly"]["teamNickname"]
    for p in PLAYERS_RAW if p.get("teamId")
}

def get_team_list() -> List[str]:
    return sorted(set(TEAM_NAME.values()))

def get_roster(team: str) -> Dict[str, List[str]]:
    if not PLAYERS_RAW:
        return {"starters": ["N/A"] * 5, "bench": []}

    tid = next(k for k, v in TEAM_NAME.items() if v == team)
    players = [
        f"{p['firstName']} {p['lastName']}".strip()
        for p in PLAYERS_RAW
        if int(p.get("teamId", 0)) == tid
    ]
    return {"starters": players[:5], "bench": players[5:]}
