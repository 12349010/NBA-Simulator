# nba_sim/data_sqlite.py

import sqlite3
import pandas as pd
from pathlib import Path

# Path to the local SQLite file; we expect it at data/nba.sqlite
DB_PATH = Path(__file__).parent.parent / "data" / "nba.sqlite"

if not DB_PATH.exists() or DB_PATH.stat().st_size == 0:
    raise FileNotFoundError(
        f"Cannot find nba.sqlite at {DB_PATH!r}.\n"
        "Make sure you have placed the file there (see README)."
    )


def get_team_list() -> list[str]:
    """Return sorted list of all team full_names."""
    con = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT full_name FROM team ORDER BY full_name", con)
    con.close()
    return df["full_name"].tolist()


def get_player_id(display_name: str, season: int) -> int:
    """Look up player_id by display name & season."""
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
    """
    Returns {'starters': [...names...], 'bench': [...]} for the given team and season.
    We'll defer true starter/bench splits to your lineup logic.
    """
    con = sqlite3.connect(DB_PATH)
    # find team_id
    td = pd.read_sql(
        "SELECT id FROM team WHERE full_name = ?", con, params=(team_name,)
    )
    if td.empty:
        con.close()
        raise ValueError(f"No team record for {team_name!r}")
    team_id = int(td["id"].iloc[0])

    # primary roster window
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

    # fallback: active rosterstatus
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

    # final fallback: inactive_players
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
    Returns a DataFrame of this team’s games in that season:
    columns ['game_id', 'date'].
    """
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
    """
    Returns True if `team_name` played on the day before `game_date`.
    """
    year, month = map(int, game_date.split("-", 2)[:2])
    season = year + (1 if month >= 7 else 0)
    sched = get_team_schedule(team_name, season)
    if sched.empty:
        return False
    gd = pd.to_datetime(game_date).date()
    return (gd - pd.Timedelta(days=1)) in sched["date"].values


def play_by_play(game_id: int) -> pd.DataFrame:
    """Returns the raw play_by_play log for a given game_id."""
    con = sqlite3.connect(DB_PATH)
    df = pd.read_sql(
        "SELECT * FROM play_by_play WHERE game_id = ? ORDER BY eventnum",
        con, params=(game_id,)
    )
    con.close()
    return df
