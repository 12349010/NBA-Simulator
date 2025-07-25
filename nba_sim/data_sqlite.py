# nba_sim/data_sqlite.py

import os
import sqlite3
import pandas as pd
from pathlib import Path

# Local path for the SQLite file
DATA_DIR = Path(__file__).parent.parent / "data"
DB_PATH  = DATA_DIR / "nba.sqlite"

def ensure_db():
    if not DB_PATH.exists() or DB_PATH.stat().st_size == 0:
        print("⚠️  nba.sqlite not found locally.")
        try:
            import gdown
            print("Downloading nba.sqlite via Google Drive link…")
            DATA_DIR.mkdir(exist_ok=True)
            # ← correct link for gdown
            url = "https://drive.google.com/uc?id=1vvpcwTK6s11d8i5Cpb_sAAKN86AFaKjx"
            gdown.download(url, str(DB_PATH), quiet=False)
        except Exception as e:
            print(f"Download failed: {e}")
            print("Please manually download from:")
            print("  https://drive.google.com/file/d/1vvpcwTK6s11d8i5Cpb_sAAKN86AFaKjx/view?usp=sharing")
            print(f"and save to {DB_PATH}")
            raise SystemExit("nba.sqlite is required.")

# Run this at import time
ensure_db()


def get_team_list() -> list[str]:
    con = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT full_name FROM team ORDER BY full_name", con)
    con.close()
    return df["full_name"].tolist()


def get_player_id(display_name: str, season: int) -> int:
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
        raise ValueError(f"No player_id for {display_name!r} in season {season}")
    return int(df["player_id"].iloc[0])


def get_roster(team_name: str, season: int) -> dict:
    con = sqlite3.connect(DB_PATH)
    td = pd.read_sql(
        "SELECT id FROM team WHERE full_name = ?", con, params=(team_name,)
    )
    if td.empty:
        con.close()
        raise ValueError(f"No team record for {team_name!r}")
    team_id = int(td["id"].iloc[0])

    # Primary roster pull
    q1 = """
    SELECT DISTINCT display_first_last AS name
      FROM common_player_info
     WHERE team_id = ?
       AND ? BETWEEN from_year AND to_year
    """
    df1 = pd.read_sql(q1, con, params=(team_id, season))
    names = df1["name"].dropna().tolist()

    # Fallback to active rosterstatus
    if not names:
        q2 = """
        SELECT DISTINCT display_first_last AS name
          FROM common_player_info
         WHERE team_id = ?
           AND rosterstatus = 'Active'
        """
        df2 = pd.read_sql(q2, con, params=(team_id,))
        names = df2["name"].dropna().tolist()

    # Final fallback to inactive_players
    if not names:
        df3 = pd.read_sql(
            "SELECT first_name, last_name FROM inactive_players WHERE team_id = ?",
            con, params=(team_id,)
        )
        names = [f"{r['first_name']} {r['last_name']}" for _, r in df3.iterrows()]

    con.close()
    return {"starters": names, "bench": []}


def get_team_schedule(team_name: str, season: int) -> pd.DataFrame:
    con = sqlite3.connect(DB_PATH)
    td = pd.read_sql(
        "SELECT id FROM team WHERE full_name = ?", con, params=(team_name,)
    )
    if td.empty:
        con.close()
        raise ValueError(f"No team record for {team_name!r}")
    team_id = int(td["id"].iloc[0])

    sched = pd.read_sql(
        """
        SELECT
          game_id,
          DATE(game_date) AS date
        FROM game
        WHERE season_id = ?
          AND (team_id_home = ? OR team_id_away = ?)
        ORDER BY date
        """,
        con,
        params=(season, team_id, team_id),
    )
    con.close()

    sched["date"] = pd.to_datetime(sched["date"]).dt.date
    return sched


def played_yesterday(team_name: str, game_date: str) -> bool:
    year, month = map(int, game_date.split("-")[:2])
    season = year + (1 if month >= 7 else 0)
    sched = get_team_schedule(team_name, season)
    if sched.empty:
        return False
    gd = pd.to_datetime(game_date).date()
    return (gd - pd.Timedelta(days=1)) in sched["date"].values


def play_by_play(game_id: int) -> pd.DataFrame:
    con = sqlite3.connect(DB_PATH)
    df = pd.read_sql(
        "SELECT * FROM play_by_play WHERE game_id = ? ORDER BY eventnum",
        con,
        params=(game_id,)
    )
    con.close()
    return df
