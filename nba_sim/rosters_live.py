# -*- coding: utf-8 -*-
"""
Dynamic NBA rosters (UTF‑8 safe) — coach scraping removed
---------------------------------------------------------
get_team_list()  ->  list[ str ]
get_roster(team) ->  {"starters":[...], "bench":[...]}
"""
import json, time, re
import datetime as dt
from functools import lru_cache
from pathlib import Path
from typing import Dict, List
from bs4 import BeautifulSoup
import pandas as pd
from .utils.scraping import soup

TEAM_ABR: dict[str, str] = {
    # Eastern Conference
    "Atlanta Hawks":             "ATL",
    "Boston Celtics":            "BOS",
    "Brooklyn Nets":             "BKN",
    "Charlotte Hornets":         "CHA",
    "Chicago Bulls":             "CHI",
    "Cleveland Cavaliers":       "CLE",
    "Detroit Pistons":           "DET",
    "Indiana Pacers":            "IND",
    "Miami Heat":                "MIA",
    "Milwaukee Bucks":           "MIL",
    "New York Knicks":           "NYK",
    "Orlando Magic":             "ORL",
    "Philadelphia 76ers":        "PHI",
    "Toronto Raptors":           "TOR",
    "Washington Wizards":        "WAS",

    # Western Conference
    "Dallas Mavericks":          "DAL",
    "Denver Nuggets":            "DEN",
    "Golden State Warriors":     "GSW",
    "Houston Rockets":           "HOU",
    "Los Angeles Clippers":      "LAC",
    "Los Angeles Lakers":        "LAL",
    "Memphis Grizzlies":         "MEM",
    "Minnesota Timberwolves":    "MIN",
    "New Orleans Pelicans":      "NOP",
    "Oklahoma City Thunder":     "OKC",
    "Phoenix Suns":              "PHO",
    "Portland Trail Blazers":    "POR",
    "Sacramento Kings":          "SAC",
    "San Antonio Spurs":         "SAS",
    "Utah Jazz":                 "UTA",
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
    Robust roster fetch:
      • tries up to 5 seasons back
      • automatically switches to known alternate abbreviations
    """
    ALT = {
        "BKN": ["BRK", "NJN"],
        "BRK": ["BKN", "NJN"],
        "CHA": ["CHO", "CHH"],
        "CHO": ["CHA", "CHH"],
        "NOP": ["NOH"],
        "NOH": ["NOP"],
    }
    base_abr = TEAM_ABR[team]
    season   = _season_year()
    tried: set[str] = set()

    def _attempt(abr: str, yr: int) -> Dict[str, List[str]] | None:
        key = f"{team}_{yr}_{abr}"
        cache = _load()              # small helper that opens JSON or {}
        if key in cache:
            return cache[key]

        url = f"https://www.basketball-reference.com/teams/{abr}/{yr}.html"
        try:
            tbl = soup(url, ttl_hours=CACHE_TTL // 3600).select_one("#roster")
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

        cache[key] = roster; _save(cache)
        return roster

    # 1) primary loop: current season → season‑5
    for yr_offset in range(0, 6):
        yr = season - yr_offset
        roster = _attempt(base_abr, yr)
        if roster:
            return roster
        tried.add(f"{base_abr}_{yr}")

    # 2) secondary loop: alternate abbreviations
    for alt in ALT.get(base_abr, []):
        for yr_offset in range(0, 6):
            yr = season - yr_offset
            if f"{alt}_{yr}" in tried:
                continue
            roster = _attempt(alt, yr)
            if roster:
                return roster

    raise ValueError(f"Unable to locate roster table for {team} "
                     f"(tried {base_abr} plus alternates over 6 seasons)")
