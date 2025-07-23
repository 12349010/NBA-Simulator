"""
team_stats_live.py – live DRtg and opponent eFG% for each team/season
"""
import json, time
from pathlib import Path
from functools import lru_cache
import pandas as pd
from .utils.scraping import soup
from nba_sim.rosters_live import TEAM_ABR, _season_year

CACHE = Path(__file__).with_name("team_def_cache.json")
TTL   = 12*60*60  # 12 h

def _load():
    if CACHE.exists() and time.time()-CACHE.stat().st_mtime < TTL:
        return json.loads(CACHE.read_text())
    return {}

def _save(d): CACHE.write_text(json.dumps(d))

@lru_cache(maxsize=None)
def get_team_defense(team:str, season:int|None=None)->dict:
    season = season or _season_year()
    cache=_load(); key=f"{team}_{season}"
    if key in cache: return cache[key]

    abr=TEAM_ABR[team]
    url=f"https://www.basketball-reference.com/teams/{abr}/{season}.html"
    html=soup(url, ttl_hours=TTL//3600)
    misc = pd.read_html(str(html.select_one("#team_misc")), flavor="lxml")[0]
    row  = misc.iloc[0]
    drtg = float(row["DRtg"])
    oppefg = float(row["Opp eFG%"])
    out={"DRtg":drtg, "Opp_eFG":oppefg}
    cache[key]=out; _save(cache)
    return out
