# -*- coding: utf-8 -*-
"""
Dynamic NBA rosters & coach (UTF‑8 safe)
"""
import json, time, re
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Dict, List

import pandas as pd
from unidecode import unidecode   # already in requirements

from .utils.scraping import soup

# ---------------- Team map ----------------
TEAM_ABR: Dict[str, str] = { ... }   # (same dict as before – omitted for brevity)

CACHE_FILE = Path(__file__).with_name("roster_cache.json")
CACHE_TTL  = 12 * 60 * 60

def _season_year() -> int:
    today = datetime.now()
    return today.year + (1 if today.month >= 7 else 0)

def _load_cache():
    if CACHE_FILE.exists() and time.time() - CACHE_FILE.stat().st_mtime < CACHE_TTL:
        return json.loads(CACHE_FILE.read_text())
    return {}

def _save_cache(d):
    CACHE_FILE.write_text(json.dumps(d))

def get_team_list() -> List[str]:
    return sorted(TEAM_ABR.keys())

def _fix_mojibake(s: str) -> str:
    """
    Quick heuristic: if the string contains the 'Ã' / 'Å' mojibake markers,
    try latin‑1 → UTF‑8 round‑trip repair, else return as‑is.
    """
    if "Ã" in s or "Å" in s:
        try:
            return s.encode("latin1").decode("utf-8")
        except UnicodeDecodeError:
            pass
    return s

@lru_cache(maxsize=None)
def _team_html(team: str):
    abr = TEAM_ABR[team]
    url = f"https://www.basketball-reference.com/teams/{abr}/{_season_year()}.html"
    return soup(url, ttl_hours=CACHE_TTL // 3600)

@lru_cache(maxsize=None)
def get_roster(team: str) -> Dict[str, List[str]]:
    cache = _load_cache()
    if team in cache:
        return cache[team]

    html = _team_html(team)
    df = pd.read_html(str(html.select_one("#roster")))[0]

    name_col = "Player" if "Player" in df.columns else next(col for col in df.columns if "Player" in col)
    if "GS" in df.columns:
        df["GS"] = pd.to_numeric(df["GS"], errors="coerce").fillna(0)
        df = df.sort_values("GS", ascending=False)

    starters = [_fix_mojibake(p) for p in df.head(5)[name_col].tolist()]
    bench    = [_fix_mojibake(p) for p in df[name_col].tolist() if p not in starters]

    roster = {"starters": starters, "bench": bench}
    cache[team] = roster
    _save_cache(cache)
    return roster

@lru_cache(maxsize=None)
def get_coach(team: str) -> str:
    html = _team_html(team)
    tag = html.find(string=re.compile(r"Coach:", re.I))
    name = tag.parent.find_next("a").get_text(strip=True) if tag else "Unknown"
    return _fix_mojibake(name)
