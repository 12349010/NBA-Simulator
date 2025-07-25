# nba_sim/data_sqlite.py

import os
import sqlite3
import pandas as pd
from pathlib import Path

# Allow overriding via env var, else default to data/nba.sqlite
_DB_PATH_ENV = os.getenv("NBA_SQLITE_PATH")
if _DB_PATH_ENV:
    DB_PATH = Path(_DB_PATH_ENV)
else:
    DB_PATH = Path(__file__).parent.parent / "data" / "nba.sqlite"


def _ensure_db_exists():
    """
    Fail early if the SQLite file isn't present.
    """
    if not DB_PATH.exists() or DB_PATH.stat().st_size == 0:
        raise FileNotFoundError(
            f"Cannot find nba.sqlite at {DB_PATH!r}. "
            "Please set NBA_SQLITE_PATH to your sqlite file location."
        )


# Check on import
_ensure_db_exists()


def get_team_list() -> list[str]:
    """
    Returns a sorted list of all franchise full names.
    """
    _ensure_db_exists()
    con = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT full_name FROM team ORDER BY full_name", con)
    con.close()
    return df["full_name"].tolist()


def get_player_id(display_name: str, season: int) -> int:
    """
    Looks up the unique player_id for a given display_first_last in a season.
    """
    _ensure_db_exists()
    con = sqlite3.connect(DB_PATH)
    query = """
    SELECT player_id
      FROM common_player_info
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
    """
    Returns the roster for a team in a season.
    Output format:
      { "starters": [<names>...], "bench": [] }
    We defer starter/bench splits to your lineup logic.
    """
    _ensure_db_exists()
    con = sqlite3.connect(DB_PATH)
    # Find team_id
    team_df = pd.read_sql(
        "SELECT id FROM team WHERE full_name = ?", con, params=(team_name,)
    )
    if team_df.empty:
        con.close()
        raise ValueError(f"No team record for {team_name!r}")
    team_id = int(team_df["id"].iloc[0])

    # 1) Primary: players on roster in that season
    query1 = """
    SELECT DISTINCT display_first_last AS name
      FROM common_player_info
     WHERE team_id = ?
       AND ? BETWEEN from_year AND to_year
    """
    df1 = pd.read_sql(query1, con, params=(team_id, season))
    names = df1["name"].dropna().tolist()

    # 2) Fallback: active players ever on team
    if not names:
        query2 = """
        SELECT DISTINCT display_first_last AS name
          FROM common_player_info
         WHERE team_id = ?
           AND rosterstatus = 'Active'
        """
        df2 = pd.read_sql(query2, con, params=(team_id,))
        names = df2["name"].dropna().tolist()

    # 3) Final fallback: inactive_players table
    if not names:
        df3 = pd.read_sql(
            "SELECT first_name, last_name FROM inactive_players WHERE team_id = ?",
            con, params=(team_id,)
        )
        names = [f"{r['first_name']} {r['last_name']}" for _, r in df3.iterrows()]

    con.close()
    return {"starters": names, "bench": []}


def get_team_schedule(team_name: str, season: int) -> pd.DataFrame:
    """
    Returns a DataFrame of that team's games in the given season:
      [game_id (int), date (datetime.date), ...]
    """
    _ensure_db_exists()
    con = sqlite3.connect(DB_PATH)
    # Resolve team_id
    team_df = pd.read_sql(
        "SELECT id FROM team WHERE full_name = ?", con, params=(team_name,)
    )
    if team_df.empty:
        con.close()
        raise ValueError(f"No team record for {team_name!r}")
    team_id = int(team_df["id"].iloc[0])

    # Query games where they were home or away
    schedule = pd.read_sql(
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

    schedule["date"] = pd.to_datetime(schedule["date"]).dt.date
    return schedule


def played_yesterday(team_name: str, game_date: str) -> bool:
    """
    Checks if `team_name` played on the day before `game_date`.
    """
    # Convert date and compute season
    year, month = map(int, game_date.split("-")[:2])
    season = year + (1 if month >= 7 else 0)

    sched = get_team_schedule(team_name, season)
    if sched.empty:
        return False

    gd = pd.to_datetime(game_date).date()
    prev_day = gd - pd.Timedelta(days=1)
    return prev_day in sched["date"].values


def play_by_play(game_id: int) -> pd.DataFrame:
    """
    Returns the raw play_by_play log for a given game_id.
    """
    _ensure_db_exists()
    con = sqlite3.connect(DB_PATH)
    df = pd.read_sql(
        "SELECT * FROM play_by_play WHERE game_id = ? ORDER BY eventnum",
        con,
        params=(game_id,)
    )
    con.close()
    return df
