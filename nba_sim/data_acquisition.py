"""
Light-weight wrappers around Basketball-Reference.
(Calls are cached in utils.scraping.)
"""
import pandas as pd
from functools import lru_cache
from .utils.scraping import soup

# ---------- helpers ----------
def slugify(full_name: str) -> str:
    """
    Convert 'Stephen Curry' → 'curryst01' style slug used by b-ref.
    Works for >90 % of names; edge-cases can be patched later.
    """
    parts = full_name.lower().replace(".", "").split()
    return parts[-1][:5] + parts[0][:2] + "01"

# ---------- player season averages ----------
@lru_cache
def get_player_season_avgs(player_slug: str, thru_season: int) -> pd.DataFrame:
    url = f"https://www.basketball-reference.com/players/{player_slug[0]}/{player_slug}.html"
    html = soup(url)
    table = html.select_one("#per_game")
    df = pd.read_html(str(table))[0]
    df = df[df["Season"].str.contains("-")]        # drop 'Career' row
    df["Season_start"] = df["Season"].str[:4].astype(int)
    return df[df["Season_start"] <= thru_season]

# ---------- placeholder tendency & coach profiles ----------
def get_player_tendencies(full_name: str) -> dict:
    """
    TODO: replace with real NBA 2K25 CSV.  Defaults are reasonable league avg.
    """
    return {
        "three_pt_rate": 0.35,   # % of FGA that are 3-pointers
        "iso_freq": 0.08,
        "drive_rate": 0.20
    }

def get_coach_profile(name: str) -> dict:
    """Mini knowledge-base; extend or load from YAML later."""
    return {
        "pace": 99,
        "off_rating": 115,
        "def_rating": 112,
        "rotation_tightness": 7,   # 7-man vs 10-man rotation
        "clutch_bias": 1.05        # 5 % boost to stars in clutch
    }
