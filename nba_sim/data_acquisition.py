import pandas as pd, csv, pkg_resources
from functools import lru_cache
from .utils.scraping import soup
from pathlib import Path

# ---------- 2K25 tendencies CSV ----------
CSV_FILE = Path(__file__).resolve().parent / "2k25_tendencies.csv"

def _load_tendencies_csv() -> dict:
    """
    Expect a CSV with columns: Name,ThreePtRate,IsoFreq,DriveRate
    """
    if not CSV_FILE.exists():
        return {}
    out = {}
    with open(CSV_FILE, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            out[row["Name"].strip().lower()] = {
                "three_pt_rate": float(row["ThreePtRate"]),
                "iso_freq":      float(row["IsoFreq"]),
                "drive_rate":    float(row["DriveRate"])
            }
    return out

_TENDENCY_TABLE = _load_tendencies_csv()

# ---------- helper slugs ----------
def slugify(full_name: str) -> str:
    parts = full_name.lower().replace(".", "").split()
    return parts[-1][:5] + parts[0][:2] + "01"

# ---------- averages ----------
@lru_cache
def get_player_season_avgs(player_slug: str, thru_season: int) -> pd.DataFrame:
    url = f"https://www.basketball-reference.com/players/{player_slug[0]}/{player_slug}.html"
    html = soup(url)
    table = html.select_one("#per_game")
    df = pd.read_html(str(table))[0]
    df = df[df["Season"].str.contains("-")]
    df["Season_start"] = df["Season"].str[:4].astype(int)
    return df[df["Season_start"] <= thru_season]

# ---------- tendencies ----------
def get_player_tendencies(full_name: str) -> dict:
    key = full_name.lower()
    if key in _TENDENCY_TABLE:
        return _TENDENCY_TABLE[key]
    # fallback league-avg
    return {"three_pt_rate": 0.35, "iso_freq": 0.08, "drive_rate": 0.20}

# ---------- coach profile ----------
def get_coach_profile(name: str) -> dict:
    return {
        "pace": 99, "off_rating": 115, "def_rating": 112,
        "rotation_tightness": 7, "clutch_bias": 1.05
    }
