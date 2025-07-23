# -*- coding: utf-8 -*-
"""
Dynamic NBA rosters (UTF‑8 safe) — coach scraping removed
---------------------------------------------------------
get_team_list()  ->  list[ str ]
get_roster(team) ->  {"starters":[...], "bench":[...]}
"""
import json, time, re
import datetime as dt
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Dict, List

import pandas as pd
from .utils.scraping import soup

TEAM_ABR: Dict[str, str] = {
    "Atlanta Hawks": "ATL", "Boston Celtics": "BOS", "Brooklyn Nets": "BRK",
    "Charlotte Hornets": "CHO", "Chicago Bulls": "CHI", "Cleveland Cavaliers": "CLE",
    "Dallas Mavericks": "DAL", "Denver Nuggets": "DEN", "Detroit Pistons": "DET",
    "Golden State Warriors": "GSW", "Houston Rockets": "HOU", "Indiana Pacers": "IND",
    "Los Angeles Clippers": "LAC", "Los Angeles Lakers": "LAL", "Memphis Grizzlies": "MEM",
    "Miami Heat": "MIA", "Milwaukee Bucks": "MIL", "Minnesota Timberwolves": "MIN",
    "New Orleans Pelicans": "NOP", "New York Knicks": "NYK", "Oklahoma City Thunder": "OKC",
    "Orlando Magic": "ORL", "Philadelphia 76ers": "PHI", "Phoenix Suns": "PHO",
    "Portland Trail Blazers": "POR", "Sacramento Kings": "SAC", "San Antonio Spurs": "SAS",
    "Toronto Raptors": "TOR", "Utah Jazz": "UTA", "Washington Wizards": "WAS",
}

CACHE_FILE = Path(__file__).with_name("roster_cache.json")
CACHE_TTL  = 12 * 60 * 60

def _season_year(d: dt.date | None = None) -> int:
    """
    Return NBA season year given a date (defaults to today).
    2025‑26 season ⇒ returns 2026.
    """
    today = d or dt.datetime.now().date()
    return today.year + (1 if today.month >= 7 else 0)

def _fix(text: str) -> str:            # repair mojibake
    if "Ã" in text or "Å" in text:
        try: return text.encode("latin1").decode("utf-8")
        except UnicodeDecodeError: pass
    return text

@lru_cache(maxsize=None)
def _team_html(team: str, season: int) -> BeautifulSoup:
    url = f"https://www.basketball-reference.com/teams/{TEAM_ABR[team]}/{season}.html"
    return soup(url, ttl_hours=CACHE_TTL // 3600)

def get_team_list() -> List[str]:
    return sorted(TEAM_ABR.keys())

@lru_cache(maxsize=None)
def get_roster(team: str) -> Dict[str, List[str]]:
    """
    Return {"starters": [...], "bench": [...]}.
    If upcoming‑season page isn't available yet, fall back to last season.
    """
    cache: Dict[str, Dict] = {}
    if CACHE_FILE.exists() and time.time() - CACHE_FILE.stat().st_mtime < CACHE_TTL:
        cache = json.loads(CACHE_FILE.read_text())

    def _scrape(season: int) -> Dict[str, List[str]] | None:
        table = _team_html(team, season).select_one("#roster")
        if table is None:
            return None
        df = pd.read_html(str(table), flavor="lxml")[0]

        name_col = "Player" if "Player" in df.columns else next(
            c for c in df.columns if "Player" in c
        )

        if "GS" in df.columns:
            df["GS"] = pd.to_numeric(df["GS"], errors="coerce").fillna(0)
            df = df.sort_values("GS", ascending=False)

        starters = [_fix(p) for p in df.head(5)[name_col].tolist()]
        bench = [_fix(p) for p in df[name_col].tolist() if p not in starters]
        return {"starters": starters, "bench": bench}

    season = _season_year()
    key = f"{team}_{season}"
    if key in cache:
        return cache[key]

    roster = _scrape(season) or _scrape(season - 1)  # fall back
    if roster is None:
        raise ValueError(f"Unable to locate roster table for {team} ({season})")

    cache[key] = roster
    CACHE_FILE.write_text(json.dumps(cache))
    return roster

