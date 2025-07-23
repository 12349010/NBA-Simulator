"""
rosters_live.py  – reliable NBA roster scraper with fallbacks

Public
------
get_team_list()  ->  list[str]
get_roster(team) ->  {"starters":[...], "bench":[...]}

Key features
------------
✓ Works even when Basketball‑Reference hides the roster table in HTML comments
✓ Falls back up to 5 seasons, tries alternate abbreviations (BKN↔BRK, etc.)
✓ 12‑hour JSON cache to minimise network calls
"""
from __future__ import annotations
import json, time, datetime as dt, re
from pathlib import Path
from functools import lru_cache
from typing import Dict, List, Optional

import pandas as pd
from bs4 import BeautifulSoup

from .utils.scraping import soup

# ------------------------------------------------------------------ #
# 1) Team abbreviations                                              #
# ------------------------------------------------------------------ #
TEAM_ABR: Dict[str, str] = {
    # East
    "Atlanta Hawks": "ATL", "Boston Celtics": "BOS", "Brooklyn Nets": "BKN",
    "Charlotte Hornets": "CHA", "Chicago Bulls": "CHI", "Cleveland Cavaliers": "CLE",
    "Detroit Pistons": "DET", "Indiana Pacers": "IND", "Miami Heat": "MIA",
    "Milwaukee Bucks": "MIL", "New York Knicks": "NYK", "Orlando Magic": "ORL",
    "Philadelphia 76ers": "PHI", "Toronto Raptors": "TOR", "Washington Wizards": "WAS",
    # West
    "Dallas Mavericks": "DAL", "Denver Nuggets": "DEN", "Golden State Warriors": "GSW",
    "Houston Rockets": "HOU", "Los Angeles Clippers": "LAC", "Los Angeles Lakers": "LAL",
    "Memphis Grizzlies": "MEM", "Minnesota Timberwolves": "MIN", "New Orleans Pelicans": "NOP",
    "Oklahoma City Thunder": "OKC", "Phoenix Suns": "PHO", "Portland Trail Blazers": "POR",
    "Sacramento Kings": "SAC", "San Antonio Spurs": "SAS", "Utah Jazz": "UTA",
}

ALT_ABR: Dict[str, List[str]] = {
    "BKN": ["BRK", "NJN"], "BRK": ["BKN", "NJN"],
    "CHA": ["CHO", "CHH"], "CHO": ["CHA", "CHH"],
    "NOP": ["NOH"],        "NOH": ["NOP"],
}

# ------------------------------------------------------------------ #
# 2) Cache helpers                                                   #
# ------------------------------------------------------------------ #
CACHE_FILE = Path(__file__).with_name("roster_cache.json")
CACHE_TTL  = 12 * 60 * 60  # 12 h

def _load() -> Dict[str, Dict]:
    if CACHE_FILE.exists() and time.time() - CACHE_FILE.stat().st_mtime < CACHE_TTL:
        return json.loads(CACHE_FILE.read_text())
    return {}

def _save(d: Dict[str, Dict]) -> None:
    CACHE_FILE.write_text(json.dumps(d))

# ------------------------------------------------------------------ #
# 3) Utilities                                                       #
# ------------------------------------------------------------------ #
def _season_year(d: dt.date | None = None) -> int:
    today = d or dt.datetime.now().date()
    return today.year + (1 if today.month >= 7 else 0)

@lru_cache(maxsize=None)
def _team_html_abbr(abr: str, season: int) -> BeautifulSoup:
    url = f"https://www.basketball-reference.com/teams/{abr}/{season}.html"
    return soup(url, ttl_hours=CACHE_TTL // 3600)

def _fix(txt: str) -> str:
    if "Ã" in txt or "Å" in txt:
        try:  # garbled utf‑8 fix
            return txt.encode("latin1").decode("utf-8")
        except UnicodeDecodeError:
            pass
    return txt

# ------------------------------------------------------------------ #
# 4) Core fetch attempt                                              #
# ------------------------------------------------------------------ #
def _extract_roster_table(page: BeautifulSoup) -> Optional[BeautifulSoup]:
    # First try direct <table id="roster">
    tbl = page.select_one("#roster")
    if tbl:
        return tbl

    # If not present, search inside HTML comments
    comments = re.findall(r"<!--([\s\S]*?)-->", str(page))
    for c in comments:
        if 'id="roster"' in c:
            return BeautifulSoup(c, "lxml").select_one("#roster")
    return None

def _attempt(abr: str, year: int, cache: dict) -> Optional[Dict[str, List[str]]]:
    key = f"{abr}_{year}"
    if key in cache:
        return cache[key]

    try:
        page = _team_html_abbr(abr, year)
        tbl  = _extract_roster_table(page)
        if tbl is None:
            return None
        df = pd.read_html(str(tbl), flavor="lxml")[0]
    except Exception:
        return None

    name_col = "Player" if "Player" in df.columns else next(
        c for c in df.columns if "Player" in c
    )
    if "GS" in df.columns:
        df["GS"] = pd.to_numeric(df["GS"], errors="coerce").fillna(0)
        df = df.sort_values("GS", ascending=False)

    starters = [_fix(p) for p in df.head(5)[name_col].tolist()]
    bench    = [_fix(p) for p in df[name_col].tolist() if p not in starters]
    roster   = {"starters": starters, "bench": bench}
    cache[key] = roster
    _save(cache)
    return roster

# ------------------------------------------------------------------ #
# 5) Public helpers                                                  #
# ------------------------------------------------------------------ #
def get_team_list() -> List[str]:
    return sorted(TEAM_ABR.keys())

@lru_cache(maxsize=None)
def get_roster(team: str) -> Dict[str, List[str]]:
    season   = _season_year()
    primary  = TEAM_ABR[team]
    cache    = _load()

    # Pass 1: try primary abbreviation, seasons [season..season‑5]
    for yr_offset in range(6):
        roster = _attempt(primary, season - yr_offset, cache)
        if roster:
            return roster

    # Pass 2: try alternate abbreviations
    for alt in ALT_ABR.get(primary, []):
        for yr_offset in range(6):
            roster = _attempt(alt, season - yr_offset, cache)
            if roster:
                return roster

    raise ValueError(
        f"Unable to locate roster table for {team} "
        f"(tried {primary} plus alternates over 6 seasons)"
    )
