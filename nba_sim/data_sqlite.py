# nba_sim/data_sqlite.py

import os
import sqlite3
import pandas as pd
from pathlib import Path

# === CONFIGURATION ===
# You MUST set this env var to the full path of your local nba.sqlite (the 2 GB file).
DB_PATH = Path(os.getenv("NBA_SQLITE_PATH", "")).expanduser()

if not DB_PATH or not DB_PATH.exists():
    raise FileNotFoundError(
        f"Cannot find nba.sqlite at {DB_PATH!r}.\n"
        "Please set the NBA_SQLITE_PATH environment variable to the absolute path\n"
        "of your existing nba.sqlite file (no downloading needed)."
    )


def get_team_list() -> list[str]:
    """Return sorted list of all team full_names."""
    con = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT full_name FROM team ORDER BY full_name", con)
    con.close()
    return df["full_name"].tolist()


def get_player_id(display_name: str, season: int) -> int:
    """Look up player_id by name & season."""
    con = sqlite3.connect(DB_PATH)
    df = pd.read_sql(
        """
        SELECT player_id
          FROM common_player_info
         WHERE display_first_last = ?
           AND ? BETWEEN from_year AND to_year
         LIMIT 1
        """,
        con, params=(display_name, season)
    )
    con.close()
    if df.empty:
        raise ValueError(f"No player_id for {display_name!r} in season {season}")
    return int(df["player_id"].iloc[0])


def get_roster(team_name: str, season: int) -> dict:
    """Fetch roster names for a team-season."""
    con = sqlite3.connect(DB_PATH)
    td = pd.read_sql(
        "SELECT id FROM team WHERE full_name = ?", con, params=(team_name,)
    )
    if td.empty:
        con.close()
        raise ValueError(f"No team record for {team_name!r}")
    team_id = int(td["id"].iloc[0])

    # Primary: common_player_info window
    df1 = pd.read_sql(
        """
        SELECT DISTINCT display_first_last AS name
          FROM common_player_info
         WHERE team_id = ?
           AND ? BETWEEN from_year AND to_year
        """,
        con, params=(team_id, season)
    )
    names = df1["name"].dropna().tolist()

    # Fallback: active rosterstatus
    if not names:
        df2 = pd.read_sql(
            """
            SELECT DISTINCT display_first_last AS name
              FROM common_player_info
             WHERE team_id = ?
               AND rosterstatus = 'Active'
            """,
            con, params=(team_id,)
        )
        names = df2["name"].dropna().tolist()

    # Final fallback: inactive_players
    if not names:
        df3 = pd.read_sql(
            "SELECT first_name, last_name FROM inactive_players WHERE team_id = ?",
            con, params=(team_id,)
        )
        names = [f"{r['first_name']} {r['last_name']}" for _, r in df3.iterrows()]

    con.close()
    return {"starters": names, "bench": []}


def get_team_schedule(team_name: str, season: int) -> pd.DataFrame:
    """Fetch a DataFrame of (game_id, date) for a team-season."""
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
        SELECT game_id, DATE(game_date) AS date
          FROM game
         WHERE season_id = ?
           AND (team_id_home = ? OR team_id_away = ?)
         ORDER BY date
        """,
        con, params=(season, team_id, team_id)
    )
    con.close()
    sched["date"] = pd.to_datetime(sched["date"]).dt.date
    return sched


def played_yesterday(team_name: str, game_date: str) -> bool:
    """Return True if team played the day before game_date."""
    year, month = map(int, game_date.split("-")[:2])
    season = year + (1 if month >= 7 else 0)
    sched = get_team_schedule(team_name, season)
    if sched.empty:
        return False
    gd = pd.to_datetime(game_date).date()
    return (gd - pd.Timedelta(days=1)) in sched["date"].values


def play_by_play(game_id: int) -> pd.DataFrame:
    """Return the raw play_by_play log for a game."""
    con = sqlite3.connect(DB_PATH)
    df = pd.read_sql(
        "SELECT * FROM play_by_play WHERE game_id = ? ORDER BY eventnum",
        con, params=(game_id,)
    )
    con.close()
    return df
