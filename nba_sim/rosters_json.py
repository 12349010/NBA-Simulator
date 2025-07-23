"""
Fetch active NBA rosters without HTML scraping.

Priority
1. nba_api PlayerIndex  (JSON, always includes TEAM_ID)  – with full headers
2. balldontlie REST     (rate‑limited fallback)
3. Return placeholders so UI never crashes
"""
from __future__ import annotations
import datetime as dt, json, time, logging, requests
from pathlib import Path
from typing import Dict, List

import pandas as pd
from nba_api.stats.endpoints import playerindex

# ------------------------------------------------------------------ #
# HTTP headers that NBA's CDN accepts
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:115.0) "
        "Gecko/20100101 Firefox/115.0"
    ),
    "Referer": "https://www.nba.com/",
    "Origin":  "https://www.nba.com",
    "x-nba-stats-origin": "stats",
    "x-nba-stats-token":  "true",
}

BL_URL = "https://www.balldontlie.io/api/v1/players"
CACHE  = Path(__file__).with_name("roster_json_cache.json")
TTL    = 12 * 60 * 60                     # 12 h

# -------- teamId → name --------
TEAM_NAME = {
    1610612737:"Atlanta Hawks", 1610612738:"Boston Celtics", 1610612751:"Brooklyn Nets",
    1610612766:"Charlotte Hornets", 1610612741:"Chicago Bulls", 1610612739:"Cleveland Cavaliers",
    1610612765:"Detroit Pistons", 1610612754:"Indiana Pacers", 1610612748:"Miami Heat",
    1610612749:"Milwaukee Bucks", 1610612752:"New York Knicks", 1610612753:"Orlando Magic",
    1610612755:"Philadelphia 76ers", 1610612761:"Toronto Raptors", 1610612764:"Washington Wizards",
    1610612742:"Dallas Mavericks", 1610612743:"Denver Nuggets", 1610612744:"Golden State Warriors",
    1610612745:"Houston Rockets", 1610612746:"LA Clippers", 1610612747:"Los Angeles Lakers",
    1610612763:"Memphis Grizzlies", 1610612750:"Minnesota Timberwolves", 1610612740:"New Orleans Pelicans",
    1610612760:"Oklahoma City Thunder", 1610612756:"Phoenix Suns", 1610612757:"Portland Trail Blazers",
    1610612758:"Sacramento Kings", 1610612759:"San Antonio Spurs", 1610612762:"Utah Jazz",
}

# ------------------------------------------------------------------ #
def _season_year(d: dt.date | None = None) -> int:
    today = d or dt.datetime.now().date()
    return today.year + (1 if today.month >= 7 else 0)

def _load() -> Dict[str, Dict]:
    if CACHE.exists() and time.time() - CACHE.stat().st_mtime < TTL:
        return json.loads(CACHE.read_text())
    return {}

def _save(d): CACHE.write_text(json.dumps(d))

# ------------------------------------------------------------------ #
def _player_dump() -> List[Dict]:
    """Return list of dicts with firstName / lastName / teamId."""

    # ---- 1) PlayerIndex (NBA official) ----
    try:
        df = playerindex.PlayerIndex(
            season="", league_id="00", timeout=10, headers=HEADERS
        ).get_data_frames()[0]
        if not df.empty:
            fn = next(c for c in df.columns if str(c).upper().startswith("FIRST"))
            ln = next(c for c in df.columns if str(c).upper().startswith("LAST"))
            tid = next(c for c in df.columns if str(c).upper().startswith("TEAM_ID"))
            return [
                {
                    "firstName": fn_, "lastName": ln_,
                    "teamId": int(tid_) if pd.notna(tid_) else None,
                }
                for fn_, ln_, tid_ in zip(df[fn], df[ln], df[tid])
            ]
    except Exception as e:
        logging.warning(f"PlayerIndex failed: {e}")

    # ---- 2) balldontlie fallback ----
    try:
        players, page = [], 1
        while True:
            r = requests.get(f"{BL_URL}?page={page}&per_page=100",
                             timeout=10, headers=HEADERS)
            r.raise_for_status()
            js = r.json()
            players.extend(js["data"])
            if js["meta"]["next_page"] is None:
                break
            page += 1
        return [
            {
                "firstName": p["first_name"],
                "lastName": p["last_name"],
                "teamId": p["team"]["id"] if p["team"] else None,
            }
            for p in players
        ]
    except Exception as e:
        logging.warning(f"balldontlie fallback failed: {e}")

    return []  # total failure

# ------------------------------------------------------------------ #
def get_team_list() -> List[str]:
    return sorted(set(TEAM_NAME.values()))

def get_roster(team: str) -> Dict[str, List[str]]:
    season = _season_year()
    cache  = _load()
    key    = f"{team}_{season}"
    if key in cache:
        return cache[key]

    team_id = next(k for k, v in TEAM_NAME.items() if v == team)
    players = [p for p in _player_dump() if p.get("teamId") == team_id]

    if not players:
        roster = {"starters": ["N/A"]*5, "bench": []}
        cache[key] = roster; _save(cache)
        return roster

    names   = [f"{p['firstName']} {p['lastName']}".strip() for p in players]
    roster  = {"starters": names[:5], "bench": names[5:]}
    cache[key] = roster; _save(cache)
    return roster
