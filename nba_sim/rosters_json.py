"""
Pull active rosters from data.nba.com. Fallback: balldontlie
Usage: get_roster("Boston Celtics") ➞ {"starters":[…], "bench":[…]}
"""
from __future__ import annotations
import datetime as dt, json, requests, functools, time
from pathlib import Path
from typing import Dict, List

DATA_URL   = "https://data.nba.com/data/10s/prod/v1/{season}/players.json"
BL_URL     = "https://www.balldontlie.io/api/v1/players"
CACHE      = Path(__file__).with_name("roster_json_cache.json")
TTL        = 12 * 60 * 60  # 12 h

TEAM_NAME  = {1610612738:"Boston Celtics", 1610612751:"Brooklyn Nets", 1610612766:"Charlotte Hornets",
              1610612741:"Chicago Bulls", 1610612739:"Cleveland Cavaliers", 1610612765:"Detroit Pistons",
              1610612754:"Indiana Pacers", 1610612748:"Miami Heat", 1610612749:"Milwaukee Bucks",
              1610612752:"New York Knicks", 1610612753:"Orlando Magic", 1610612755:"Philadelphia 76ers",
              1610612761:"Toronto Raptors", 1610612764:"Washington Wizards",
              1610612742:"Dallas Mavericks", 1610612743:"Denver Nuggets", 1610612744:"Golden State Warriors",
              1610612745:"Houston Rockets", 1610612746:"LA Clippers", 1610612747:"Los Angeles Lakers",
              1610612763:"Memphis Grizzlies", 1610612750:"Minnesota Timberwolves", 1610612740:"New Orleans Pelicans",
              1610612760:"Oklahoma City Thunder", 1610612756:"Phoenix Suns", 1610612757:"Portland Trail Blazers",
              1610612758:"Sacramento Kings", 1610612759:"San Antonio Spurs", 1610612762:"Utah Jazz"}

def _season_year(d: dt.date | None = None) -> int:
    today = d or dt.datetime.now().date()
    return today.year + (1 if today.month >= 7 else 0)

def _load_cache() -> Dict[str, Dict]:
    if CACHE.exists() and time.time() - CACHE.stat().st_mtime < TTL:
        return json.loads(CACHE.read_text())
    return {}

def _save_cache(d: Dict[str, Dict]):
    CACHE.write_text(json.dumps(d))

@functools.lru_cache(maxsize=None)
def _player_dump(season:int) -> List[Dict]:
    url = DATA_URL.format(season=season)
    try:
        return requests.get(url, timeout=10).json()["league"]["standard"]
    except Exception:
        # fallback balldontlie current season (returns 25/page; loop)
        players=[]
        page=1
        while True:
            js=requests.get(f"{BL_URL}?per_page=100&page={page}",timeout=10).json()
            players+=js["data"]
            if js["meta"]["next_page"] is None: break
            page+=1
        return [{"firstName":p["first_name"],"lastName":p["last_name"],
                 "teamId":p["team"]["id"]} for p in players]

def get_team_list()->List[str]:
    return sorted(set(TEAM_NAME.values()))

def get_roster(team:str)->Dict[str,List[str]]:
    season=_season_year()
    cache=_load_cache()
    key=f"{team}_{season}"
    if key in cache: return cache[key]

    # map team→id
    team_id=[k for k,v in TEAM_NAME.items() if v==team][0]

    players=[p for p in _player_dump(season) if int(p["teamId"])==team_id]
    names=[f"{p['firstName']} {p['lastName']}".strip() for p in players]

    starters=names[:5]
    bench=names[5:]
    roster={"starters":starters,"bench":bench}
    cache[key]=roster; _save_cache(cache)
    return roster
