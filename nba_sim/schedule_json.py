"""
schedule_json.py  – Team schedule & back‑to‑backs via JSON

Primary: data.nba.com
No crash: returns empty DataFrame when nothing found.
"""
from __future__ import annotations
import datetime as dt, json, time, requests, re
from pathlib import Path
from functools import lru_cache
from typing import Dict, List

import pandas as pd
from bs4 import BeautifulSoup

from nba_sim.rosters_json import TEAM_NAME, _season_year

SCH_URL = "https://data.nba.com/data/10s/prod/v1/{season}/schedule.json"
CACHE   = Path(__file__).with_name("sched_json_cache.json")
TTL     = 12 * 60 * 60
HDRS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:115.0) "
        "Gecko/20100101 Firefox/115.0"
    ),
    "Referer": "https://www.nba.com/",
}

def _load() -> Dict[str, List[str]]:
    if CACHE.exists() and time.time() - CACHE.stat().st_mtime < TTL:
        return json.loads(CACHE.read_text())
    return {}

def _save(d): CACHE.write_text(json.dumps(d))

@lru_cache(maxsize=None)
def _season_sched(season: int) -> pd.DataFrame:
    try:
        js = requests.get(SCH_URL.format(season=season),
                          headers=HDRS, timeout=10).json()
        df = pd.json_normalize(js["league"]["standard"])
        df["startDate"] = pd.to_datetime(df["startDateEastern"])
        return df
    except Exception:
        return pd.DataFrame(columns=["startDate"])

def get_team_schedule(team: str, season: int | None = None) -> pd.DataFrame:
    season = season or _season_year()
    team_id = next(k for k, v in TEAM_NAME.items() if v == team)

    for off in range(6):  # season down to season‑5
        df = _season_sched(season - off)
        if df.empty:
            continue
        games = df[(df["homeTeam.teamId"] == str(team_id)) |
                   (df["awayTeam.teamId"] == str(team_id))]
        if not games.empty:
            return games
    return pd.DataFrame(columns=["startDate"])
