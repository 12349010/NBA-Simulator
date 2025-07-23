"""
rosters_json.py  – NBA rosters without HTML scraping

Order:
1. nba_api CommonAllPlayers (walk back 6 seasons, robust column detection)
2. nba_api.stats.static.players  (active list; no team → None)
3. balldontlie REST (rate‑limited)
4. return placeholders on total failure
"""
from __future__ import annotations
import datetime as dt, json, time, logging, requests
from pathlib import Path
from typing import Dict, List

import pandas as pd
from nba_api.stats.endpoints import commonallplayers
from nba_api.stats.static import players as static_players

HDRS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:115.0) "
        "Gecko/20100101 Firefox/115.0"
    ),
    "Referer": "https://www.nba.com/",
}
BL_URL = "https://www.balldontlie.io/api/v1/players"

CACHE = Path(__file__).with_name("roster_json_cache.json")
TTL   = 12 * 60 * 60  # 12 h

TEAM_NAME = {   # teamId → name  (unchanged map)
    1610612737:"Atlanta Hawks",1610612738:"Boston Celtics",1610612751:"Brooklyn Nets",
    1610612766:"Charlotte Hornets",1610612741:"Chicago Bulls",1610612739:"Cleveland Cavaliers",
    1610612765:"Detroit Pistons",1610612754:"Indiana Pacers",1610612748:"Miami Heat",
    1610612749:"Milwaukee Bucks",1610612752:"New York Knicks",1610612753:"Orlando Magic",
    1610612755:"Philadelphia 76ers",1610612761:"Toronto Raptors",1610612764:"Washington Wizards",
    1610612742:"Dallas Mavericks",1610612743:"Denver Nuggets",1610612744:"Golden State Warriors",
    1610612745:"Houston Rockets",1610612746:"LA Clippers",1610612747:"Los Angeles Lakers",
    1610612763:"Memphis Grizzlies",1610612750:"Minnesota Timberwolves",1610612740:"New Orleans Pelicans",
    1610612760:"Oklahoma City Thunder",1610612756:"Phoenix Suns",1610612757:"Portland Trail Blazers",
    1610612758:"Sacramento Kings",1610612759:"San Antonio Spurs",1610612762:"Utah Jazz",
}

# ---------- helpers ----------
def _season_year(d: dt.date | None = None) -> int:
    today = d or dt.datetime.now().date()
    return today.year + (1 if today.month >= 7 else 0)

def _load() -> Dict[str, Dict]:
    if CACHE.exists() and time.time() - CACHE.stat().st_mtime < TTL:
        return json.loads(CACHE.read_text())
    return {}

def _save(d): CACHE.write_text(json.dumps(d))

def _extract_cols(df: pd.DataFrame):
    fn = next(c for c in df.columns if str(c).upper().startswith("FIRST"))
    ln = next(c for c in df.columns if str(c).upper().startswith("LAST"))
    if "TEAM_ID" in df.columns:
        tid = "TEAM_ID"
    elif "TEAM_ID_CURRENT" in df.columns:
        tid = "TEAM_ID_CURRENT"
    else:
        tid = None
    return fn, ln, tid

def _player_dump(season: int) -> List[Dict]:
    # 1) CommonAllPlayers walk back 6 seasons
    for off in range(6):
        season_id = f"{season-off-1}-{str(season-off)[-2:]}"  # '2024-25'
        try:
            df = commonallplayers.CommonAllPlayers(
                season=season_id, is_only_current_season=0, league_id="00"
            ).get_data_frames()[0]
            if df.empty:
                continue
            fn_col, ln_col, tid_col = _extract_cols(df)
            return [
                {"firstName": fn, "lastName": ln,
                 "teamId": int(tid) if tid_col and pd.notna(tid) else None}
                for fn, ln, tid in zip(df[fn_col], df[ln_col],
                                       df[tid_col] if tid_col else [None]*len(df))
            ]
        except Exception as e:
            logging.warning(f"CommonAllPlayers {season_id} failed: {e}")

    # 2) static.players active list
    try:
        plist = static_players.get_players()
        return [
            {"firstName": p["first_name"], "lastName": p["last_name"],
             "teamId": p.get("team_id") or None}
            for p in plist
        ]
    except Exception as e:
        logging.warning(f"static_players fallback failed: {e}")

    # 3) balldontlie
    try:
        players, page = [], 1
        while True:
            r = requests.get(f"{BL_URL}?page={page}&per_page=100",
                             headers=HDRS, timeout=10)
            r.raise_for_status()
            js = r.json()
            players.extend(js["data"])
            if js["meta"]["next_page"] is None:
                break
            page += 1
        return [
            {"firstName": p["first_name"], "lastName": p["last_name"],
             "teamId": p["team"]["id"] if p["team"] else None}
            for p in players
        ]
    except Exception as e:
        logging.warning(f"balldontlie fallback failed: {e}")

    return []

# ---------- public ----------
def get_team_list() -> List[str]:
    return sorted(set(TEAM_NAME.values()))

def get_roster(team: str) -> Dict[str, List[str]]:
    season = _season_year()
    cache  = _load()
    key    = f"{team}_{season}"
    if key in cache:
        return cache[key]

    team_id = next(k for k, v in TEAM_NAME.items() if v == team)
    players = [p for p in _player_dump(season) if p.get("teamId") == team_id]

    if not players:
        roster = {"starters": ["N/A"] * 5, "bench": []}
        cache[key] = roster; _save(cache)
        return roster

    names   = [f"{p['firstName']} {p['lastName']}".strip() for p in players]
    roster  = {"starters": names[:5], "bench": names[5:]}
    cache[key] = roster; _save(cache)
    return roster
