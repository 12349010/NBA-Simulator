# -*- coding: utf-8 -*-
"""
Dynamic NBA rosters pulled from Basketball‑Reference
====================================================

Public helpers
    get_team_list()  ->  list of 30 full team names
    get_roster(team) ->  {"starters": [...5 names...], "bench": [...rest...]}

Data are cached to roster_cache.json for 12 h.
"""
import json
import time
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Dict, List

import pandas as pd

from .utils.scraping import soup

# ---------------- Team → Abbreviation map -----------------
TEAM_ABR: Dict[str, str] = {
    "Atlanta Hawks": "ATL",
    "Boston Celtics": "BOS",
    "Brooklyn Nets": "BRK",
    "Charlotte Hornets": "CHO",
    "Chicago Bulls": "CHI",
    "Cleveland Cavaliers": "CLE",
    "Dallas Mavericks": "DAL",
    "Denver Nuggets": "DEN",
    "Detroit Pistons": "DET",
    "Golden State Warriors": "GSW",
    "Houston Rockets": "HOU",
    "Indiana Pacers": "IND",
    "Los Angeles Clippers": "LAC",
    "Los Angeles Lakers": "LAL",
    "Memphis Grizzlies": "MEM",
    "Miami Heat": "MIA",
    "Milwaukee Bucks": "MIL",
    "Minnesota Timberwolves": "MIN",
    "New Orleans Pelicans": "NOP",
    "New York Knicks": "NYK",
    "Oklahoma City Thunder": "OKC",
    "Orlando Magic": "ORL",
    "Philadelphia 76ers": "PHI",
    "Phoenix Suns": "PHO",
    "Portland Trail Blazers": "POR",
    "Sacramento Kings": "SAC",
    "San Antonio Spurs": "SAS",
    "Toronto Raptors": "TOR",
    "Utah Jazz": "UTA",
    "Washington Wizards": "WAS",
}

# ---------------- Caching -----------------
CACHE_FILE = Path(__file__).with_name("roster_cache.json")
CACHE_TTL = 12 * 60 * 60  # 12 hours in seconds


def _load_cache() -> Dict[str, Dict]:
    if CACHE_FILE.exists() and time.time() - CACHE_FILE.stat().st_mtime < CACHE_TTL:
        return json.loads(CACHE_FILE.read_text())
    return {}


def _save_cache(cache: Dict[str, Dict]) -> None:
    CACHE_FILE.write_text(json.dumps(cache))


# ---------------- Public API -----------------
def get_team_list() -> List[str]:
    return sorted(TEAM_ABR.keys())


@lru_cache(maxsize=None)
def get_roster(team_name: str) -> Dict[str, List[str]]:
    """Return starters & bench for the requested team."""
    cache = _load_cache()
    if team_name in cache:
        return cache[team_name]

    abr = TEAM_ABR[team_name]
    season_year = datetime.now().year + (1 if datetime.now().month >= 7 else 0)
    url = f"https://www.basketball-reference.com/teams/{abr}/{season_year}.html"
    html = soup(url, ttl_hours=CACHE_TTL // 3600)
    table = html.select_one("#roster")

    df = pd.read_html(str(table))[0]
    # column that holds player names (depends on b‑ref HTML)
    name_col = "Player"
    if name_col not in df.columns:
        # fallback: first column that contains 'Player'
        name_col = next(col for col in df.columns if "Player" in col)

    if "GS" in df.columns:
        df["GS"] = pd.to_numeric(df["GS"], errors="coerce").fillna(0)
        df = df.sort_values("GS", ascending=False)

    starters = df.head(5)[name_col].tolist()
    bench = [p for p in df[name_col].tolist() if p not in starters]

    roster = {"starters": starters, "bench": bench}
    cache[team_name] = roster
    _save_cache(cache)
    return roster
