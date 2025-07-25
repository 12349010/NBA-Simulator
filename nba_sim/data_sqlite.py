# nba_sim/data_sqlite.py

import sqlite3
import pandas as pd
from pathlib import Path

# Ensure this file is at the top, before any DB access
DATA_DIR = Path(__file__).parent.parent / "data"
DB_PATH  = DATA_DIR / "nba.sqlite"

def ensure_db():
    """
    Make sure nba.sqlite exists locally. If not, try to auto-download via gdown
    using the shared Drive ID; otherwise prompt for manual placement.
    """
    if not DB_PATH.exists() or DB_PATH.stat().st_size == 0:
        print("⚠️ nba.sqlite not found locally.")
        try:
            import gdown
            print("Attempting to download nba.sqlite via gdown...")
            # Extracted from your share link:
            url = "https://drive.google.com/uc?id=1vvpcwTK6s11d8i5Cpb_sAAKN86AFaKjx"
            DATA_DIR.mkdir(exist_ok=True)
            gdown.download(url, str(DB_PATH), quiet=False)
        except Exception as e:
            print(f"\n❗ Auto-download failed: {e}")
            print("Please manually download the file from:")
            print("  https://drive.google.com/file/d/1vvpcwTK6s11d8i5Cpb_sAAKN86AFaKjx/view?usp=sharing")
            print(f"and save it to: {DB_PATH}\n")
            raise SystemExit("nba.sqlite is required to run the simulator.")

# Run on import
  ensure_db()


# --- your existing DB helper functions below ---

def get_team_list() -> list[str]:
    """Return list of team full_names from `team` table."""
    con = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT full_name FROM team ORDER BY full_name", con)
    con.close()
    return df["full_name"].tolist()


def get_player_id(display_name: str, season: int) -> int:
    """
    Fetches the player_id from common_player_info for a given display name and season.
    """
    con = sqlite3.connect(DB_PATH)
    query = """
    SELECT player_id FROM common_player_info
     WHERE display_first_last = ?
       AND ? BETWEEN from_year AND to_year
     LIMIT 1
    """
    df = pd.read_sql(query, con, params=(display_name, season))
    con.close()
    if df.empty:
        raise ValueError(f"No player_id for {display_name} in season {season}")
    return int(df["player_id"].iloc[0])


def get_roster(team_name: str, season: int) -> dict:
    """
    Returns {'starters': [...names...], 'bench': [...names...]} for the given team and season.
    """
    # Your existing implementation here...
    pass


def get_team_schedule(team_name: str, season: int) -> pd.DataFrame:
    """
    Returns a DataFrame of scheduled games for a team in a season,
    with columns ['game_id','date', ...].
    """
    # Your existing implementation here...
    pass


def played_yesterday(team_name: str, game_date: str) -> bool:
    """
    Returns True if the given team played on the day before game_date.
    """
    sched = get_team_schedule(team_name, int(game_date[:4]) + (1 if int(game_date[5:7]) >= 7 else 0))
    if sched.empty:
        return False
    gd = pd.to_datetime(game_date).date()
    return (gd - pd.Timedelta(days=1)) in sched["date"].dt.date.values
