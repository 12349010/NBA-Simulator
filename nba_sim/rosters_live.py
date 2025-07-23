"""
Live roster grabber — Basketball‑Reference teams pages
------------------------------------------------------
get_team_list()  ->  ["Atlanta Hawks", ..., "Washington Wizards"]

get_roster(team) ->  {"starters": [5 names], "bench": [rest]}
"""
import pandas as pd, json, time
from functools import lru_cache
from pathlib import Path
from .utils.scraping import soup

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

CACHE_F   = Path(__file__).resolve().parent / "roster_cache.json"
CACHE_TTL = 12 * 3600  # 12 h

def _l_
