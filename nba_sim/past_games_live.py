# nba_sim/past_games_live.py
import datetime as dt, pandas as pd, re
from functools import lru_cache
from .utils.scraping import soup
from .rosters_live import TEAM_ABR

@lru_cache(maxsize=None)
def _season_schedule(team:str, season:int) -> pd.DataFrame:
    abr = TEAM_ABR[team]
    url = f"https://www.basketball-reference.com/teams/{abr}/{season}_games.html"
    tbl = soup(url, ttl_hours=12).select_one("#games")
    df = pd.read_html(str(tbl))[0]
    df = df[df["G"].astype(str).str.isnumeric()]            # drop headers
    df["Date"] = pd.to_datetime(df["Date"])
    return df

def get_score(home:str, away:str, game_date:str) -> dict|None:
    """Return {'home':pts,'away':pts} or None if not found."""
    gd = dt.datetime.fromisoformat(game_date).date()
    season = gd.year + (1 if gd.month >= 7 else 0)
    sched = _season_schedule(home, season)
    row = sched[sched["Date"].dt.date == gd]
    if row.empty:                                           # maybe team order flipped?
        sched = _season_schedule(away, season)
        row = sched[sched["Date"].dt.date == gd]
    if row.empty: return None
    r = row.iloc[0]
    # identify whether 'home' was actually home in bb-ref table
    home_is_home = r["Unnamed: 5"].strip() != "@"           # '@' indicates away
    if home_is_home:
        return {"home": int(r["PTS"]), "away": int(r["Opp PTS"])}
    else:
        return {"home": int(r["Opp PTS"]), "away": int(r["PTS"])}
