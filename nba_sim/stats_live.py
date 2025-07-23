"""
Live player season‑level stats & derived tendencies
---------------------------------------------------
get_stats(full_name, season_year) -> pd.Series (per‑game row)
get_tendencies(full_name, season_year) -> dict
"""
import pandas as pd
from functools import lru_cache
from datetime import datetime
from .utils.scraping import soup

def _slug(full: str) -> str:
    p = full.lower().replace(".", "").split()
    return p[-1][:5] + p[0][:2] + "01"

def _season_year(date_obj=None):
    today = date_obj or datetime.now()
    return today.year + (1 if today.month >= 7 else 0)

@lru_cache(maxsize=None)
def get_stats(full_name: str, season_year: int | None = None) -> pd.Series:
    season_year = season_year or _season_year()
    url = f"https://www.basketball-reference.com/players/{full_name[0].lower()}/{_slug(full_name)}.html"
    html = soup(url)
    per = pd.read_html(str(html.select_one("#per_game")))[0]
    per = per[per["Season"].str.contains("-")]          # drop 'Career'
    per["Season_start"] = per["Season"].str[:4].astype(int)
    row = per[per["Season_start"] == season_year - 1]
    if row.empty:
        row = per.iloc[-1:]                             # fallback latest
    return row.squeeze()                                # Series

def get_tendencies(full_name: str, season_year=None) -> dict:
    s = get_stats(full_name, season_year)
    try:
        three_rate = float(s["3PA"]) / float(s["FGA"]) if float(s["FGA"]) else 0.35
    except (KeyError, ZeroDivisionError):
        three_rate = 0.35
    # very rough proxies
    iso_freq  = 0.07 + 0.4 * max(0, (float(s.get("USG%", 20)) - 20) / 15)
    drive_rate = 0.25 - three_rate * 0.2
    return {"three_pt_rate": round(three_rate, 2),
            "iso_freq": round(iso_freq, 2),
            "drive_rate": round(drive_rate, 2)}
