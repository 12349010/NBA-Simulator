"""
Live roster grabber (Basketball‑Reference).
-------------------------------------------------
Functions exposed to the rest of the app:

    get_team_list()  ->  ["Atlanta Hawks", ..., "Washington Wizards"]

    get_roster(team_name)  ->  dict with keys:
        "starters": [list of 5 based on Games Started]
        "bench":    [everyone else on the current roster]
Cache is refreshed every 12 hours to avoid hammering the site.
"""
import pandas as pd, re, time, json
from functools import lru_cache
from pathlib import Path
from .utils.scraping import soup

# Map full team names to BB‑Ref 3‑letter codes
TEAM_ABR = {
    "Atlanta Hawks": "ATL", "Boston Celtics": "BOS", "Brooklyn Nets": "BRK",
    "Charlotte Hornets": "CHO", "Chicago Bulls": "CHI", "Cleveland Cavaliers": "CLE",
    "Dallas Mavericks": "DAL", "Denver Nuggets": "DEN", "Detroit Pistons": "DET",
    "Golden State Warriors": "GSW", "Houston Rockets": "HOU", "Indiana Pacers": "IND",
    "Los Angeles Clippers": "LAC", "Los Angeles Lakers": "LAL", "Memphis Grizzlies": "MEM",
    "Miami Heat": "MIA", "Milwaukee Bucks": "MIL", "Minnesota Timberwolves": "MIN",
    "New Orleans Pelicans": "NOP", "New York Knicks": "NYK", "Oklahoma City Thunder": "OKC",
    "Orlando Magic": "ORL", "Philadelphia 76ers": "PHI", "Phoenix Suns": "PHO",
    "Portland Trail Blazers": "POR", "Sacramento Kings": "SAC", "San Antonio Spurs": "SAS",
    "Toronto Raptors": "TOR", "Utah Jazz": "UTA", "Washington Wizards": "WAS"
}

CACHE_F = Path(__file__).resolve().parent / "roster_cache.json"
CACHE_TTL = 12 * 3600      # 12 hours

def _load_cache():
    if CACHE_F.exists():
        mtime = CACHE_F.stat().st_mtime
        if time.time() - mtime < CACHE_TTL:
            return json.loads(CACHE_F.read_text())
    return {}

def _save_cache(d):
    CACHE_F.write_text(json.dumps(d))

def get_team_list():
    return sorted(TEAM_ABR.keys())

@lru_cache(maxsize=None)
def get_roster(team_name: str) -> dict:
    cache = _load_cache()
    if team_name in cache:
        return cache[team_name]

    abr = TEAM_ABR[team_name]
    # use current season (similar URL pattern each year: /teams/GSW/2025.html)
    from datetime import datetime
    yr = datetime.now().year + (1 if datetime.now().month >= 7 else 0)
    url = f"https://www.basketball-reference.com/teams/{abr}/{yr}.html"
    html = soup(url, ttl_hours=CACHE_TTL/3600)
    roster_tbl = html.select_one("#roster")
    df = pd.read_html(str(roster_tbl))[0]

    # sort by Games Started (GS) desc to pick top 5
    df["GS"] = pd.to_numeric(df["GS"], errors="coerce").fillna(0)
    df = df.sort_values("GS", ascending=False)
    starters = df.head(5)["No. Player"].tolist() if "No. Player" in df.columns else df.head(5)["Player"].tolist()
    bench = d
