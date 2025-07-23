"""
Return DataFrame with team schedule using data.nba.com
"""
import datetime as dt, json, requests, pandas as pd, functools
from pathlib import Path
from nba_sim.rosters_json import TEAM_NAME, _season_year

SCH_URL="https://data.nba.com/data/10s/prod/v1/{season}/schedule.json"
CACHE=Path(__file__).with_name("sched_json_cache.json"); TTL=12*60*60

def _load()->dict:
    if CACHE.exists() and (dt.datetime.now().timestamp()-CACHE.stat().st_mtime)<TTL:
        return json.loads(CACHE.read_text())
    return {}

def _save(d): CACHE.write_text(json.dumps(d))

@functools.lru_cache(maxsize=None)
def _season_sched(season:int)->pd.DataFrame:
    js=requests.get(SCH_URL.format(season=season),timeout=10).json()
    df=pd.json_normalize(js["league"]["standard"])
    df["startDate"]=pd.to_datetime(df["startDateEastern"])
    return df

def get_team_schedule(team:str,season:int|None=None)->pd.DataFrame:
    season=season or _season_year()
    team_id=[k for k,v in TEAM_NAME.items() if v==team][0]
    for yr_off in range(6):
        df=_season_sched(season-yr_off)
        games=df[(df["homeTeam.teamId"]==str(team_id))|(df["awayTeam.teamId"]==str(team_id))]
        if not games.empty:
            return games
    return pd.DataFrame(columns=["startDate"])
