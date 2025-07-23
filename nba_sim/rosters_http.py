import requests, itertools, logging
from functools import lru_cache

FREE  = "https://www.free-nba.com/api"
BALL  = "https://balldontlie.io/api/v1"

def _pages(base:str):
    page = 1
    while True:
        r = requests.get(f"{base}&page={page}", timeout=10)
        r.raise_for_status()
        js = r.json()
        yield from js["data"]
        if js.get("meta", {}).get("next_page") is None:
            break
        page += 1

@lru_cache(maxsize=None)
def player_dump():
    try:
        return list(_pages(f"{FREE}/players?per_page=100"))
    except Exception as e:
        logging.warning(f"free‑nba players failed: {e}")
        return list(_pages(f"{BALL}/players?per_page=100"))

@lru_cache(maxsize=None)
def team_list():
    js = requests.get(f"{FREE}/teams", timeout=10).json()["data"]
    return {t["id"]: t["full_name"] for t in js}

def roster(team_name:str):
    tid = next(k for k,v in team_list().items() if v==team_name)
    players = [p for p in player_dump() if p["team"]["id"]==tid]
    names   = [f"{p['first_name']} {p['last_name']}".strip() for p in players]
    return {"starters": names[:5], "bench": names[5:]}
