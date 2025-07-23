"""
schedule_live.py  – detect back‑to‑backs for fatigue modelling
--------------------------------------------------------------
• played_yesterday(team, game_date) → bool
  Returns True if the given team had a game on the day before `game_date`.
"""

from __future__ import annotations
import json, time, datetime as dt
from pathlib import Path
from functools import lru_cache
from typing import Dict, List

import pandas as pd
from bs4 import BeautifulSoup

from .utils.scraping import soup
from nba_sim.rosters_live import TEAM_ABR, _season_year

CACHE_FILE = Path(__file__).with_name("sched_cache.json")
TTL_SEC    = 12 * 60 * 60   # 12 hours


# ---------- tiny JSON cache helpers ----------
def _load_cache() -> Dict[str, List[str]]:
    if CACHE_FILE.exists() and time.time() - CACHE_FILE.stat().st_mtime < TTL_SEC:
        return json.loads(CACHE_FILE.read_text())
    return {}


def _save_cache(d: Dict[str, List[str]]) -> None:
    CACHE_FILE.write_text(json.dumps(d))


@lru_cache(maxsize=None)
def _team_schedule(team: str, season: int) -> pd.DataFrame:
    """
    Return schedule DataFrame. Walks back up to 5 seasons until it finds a page
    with a #games table.
    """
    abr = TEAM_ABR[team]

    def _fetch(season_year: int) -> BeautifulSoup | None:
        url = f"https://www.basketball-reference.com/teams/{abr}/{season_year}_games.html"
        try:
            return soup(url, ttl_hours=TTL // 3600).select_one("#games")
        except Exception:
            return None

    for yr_offset in range(0, 6):            # season, season‑1, … season‑5
        tbl = _fetch(season - yr_offset)
        if tbl is not None:
            df = pd.read_html(str(tbl), flavor="lxml")[0]
            df = df[df["G"].astype(str).str.isnumeric()]
            df["Date"] = pd.to_datetime(df["Date"])
            return df

    raise ValueError(f"Could not fetch schedule for {team} "
                     f"(seasons {season}..{season-5})")


# ---------- public helper ----------
def played_yesterday(team: str, game_date: str) -> bool:
    """
    True if `team` played on the calendar day immediately before `game_date`.
    """
    gd   = dt.datetime.fromisoformat(game_date).date()
    season = _season_year(gd)
    cache = _load_cache()
    key   = f"{team}_{season}"
    if key not in cache:
        sched = _team_schedule(team, season)
        cache[key] = sched["Date"].dt.date.astype(str).tolist()
        _save_cache(cache)

    yesterday = (gd - dt.timedelta(days=1)).isoformat()
    return yesterday in cache[key]
