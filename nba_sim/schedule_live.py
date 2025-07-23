"""
schedule_live.py – flag back‑to‑backs
"""
import json, time, datetime as dt
from pathlib import Path
from functools import lru_cache
import pandas as pd
from .utils.scraping import soup
from nba_sim.rosters_live import TEAM_ABR, _season_year

CACHE = Path(__file__).with_name("sched_cache.json")
TTL   = 12*60*60

def _load(): return json.loads(CACHE.read_text()) if CACHE.exists() else {}
def _save(d): CACHE.write_text(json.dumps(d))

@lru_cache(maxsize=None)
def _team_schedule(team:str, season:int):
    abr=TEAM_ABR[team]
    url=f"https://www.basketball-reference.com/teams/{abr}/{season}_games.html"
    tbl = soup(url, ttl_hours=TTL//3600).select_one("#games")
    df  = pd.read_html(str(tbl), flavor="lxml")[0]    # ← force lxml parser
    df  = df[df["G"].apply(lambda x:str(x).isdigit())]
    df["Date"] = pd.to_datetime(df["Date"])
    return df

def played_yesterday(team:str, game_date:str)->bool:
    gd = dt.datetime.fromisoformat(game_date).date()
    season=_season_year(gd)
    # cache
    cache=_load(); key=f"{team}_{season}"
    if key not in cache:
        cache[key]=_team_schedule(team,season)["Date"].dt.date.astype(str).tolist()
        _save(cache)
    return (gd - dt.timedelta(days=1)).isoformat() in cache[key]
