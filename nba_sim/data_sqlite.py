"""
data_sqlite.py  – helpers to query the local NBA SQLite dump at data/nba.sqlite
(auto‑downloads & validates via gdown on first run)
"""

from pathlib import Path
import sqlite3
import pandas as pd
import functools
import datetime as dt
import contextlib
import sys

# ─── Path to the DB under your repo’s data/ folder ───────────────────────
PKG_DIR = Path(__file__).parent           # .../nba_sim
DB_PATH = (PKG_DIR.parent / "data" / "nba.sqlite").resolve()

# ─── Google Drive file ID ───────────────────────────────────────────────
GDRIVE_ID = "1vvpcwTK6s11d8i5Cpb_sAAKN86AFaKjx"

# ─── Ensure the data folder exists ──────────────────────────────────────
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

def _download_db():
    import gdown
    url = f"https://drive.google.com/uc?id={GDRIVE_ID}"
    print("[Setup] nba.sqlite missing or invalid; downloading via gdown…", file=sys.stderr)
    gdown.download(url, str(DB_PATH), quiet=False)
    print(f"[Setup] Download complete: {DB_PATH}", file=sys.stderr)

# ─── Download if missing or corrupt ─────────────────────────────────────
_need = False
if not DB_PATH.exists():
    _need = True
else:
    try:
        with open(DB_PATH, "rb") as f:
            if not f.read(15).startswith(b"SQLite format 3"):
                _need = True
    except:
        _need = True

if _need:
    _download_db()

@contextlib.contextmanager
def _connect():
    con = sqlite3.connect(DB_PATH)
    try:
        yield con
    finally:
        con.close()

# ─── Team list from `team.full_name` ────────────────────────────────────
@functools.lru_cache(maxsize=None)
def get_team_list() -> list[str]:
    with _connect() as con:
        df = pd.read_sql(
            "SELECT full_name FROM team ORDER BY full_name", con
        )
    return df["full_name"].tolist()

# ─── Roster via `common_player_info` ────────────────────────────────────
@functools.lru_cache(maxsize=512)
def get_roster(team: str, season: int) -> dict[str, list[str]]:
    """
    Return starters (first 5) and bench (rest) for <team> in <season>.
    1) Try common_player_info.from_year/to_year filter.
    2) Fallback to rosterstatus='Active'.
    3) Final fallback to inactive_players for that season (last resort).
    """
    import sys
    from pprint import pprint

    with _connect() as con:
        # 1) Look up the team’s numeric ID
        tid = pd.read_sql(
            "SELECT id FROM team WHERE full_name = ?", con,
            params=(team,)
        )["id"].iloc[0]

        # --- Attempt #1: season-range from common_player_info ---
        sql1 = """
        SELECT display_first_last AS player_name
          FROM common_player_info
         WHERE team_id = ?
           AND from_year <= ?
           AND to_year   >= ?
         ORDER BY player_name
        """
        df1 = pd.read_sql(sql1, con, params=(tid, season, season))
        if not df1.empty:
            names = df1["player_name"].tolist()
            return {"starters": names[:5], "bench": names[5:]}

        # Log for debugging
        print(f"[get_roster] season‐range empty for {team} / {season}", file=sys.stderr)

        # --- Attempt #2: rosterstatus = 'Active' in common_player_info ---
        sql2 = """
        SELECT display_first_last AS player_name
          FROM common_player_info
         WHERE team_id = ?
           AND rosterstatus = 'Active'
         ORDER BY player_name
        """
        df2 = pd.read_sql(sql2, con, params=(tid,))
        if not df2.empty:
            print(f"[get_roster] using Active fallback for {team}", file=sys.stderr)
            names = df2["player_name"].tolist()
            return {"starters": names[:5], "bench": names[5:]}

        print(f"[get_roster] Active fallback empty for {team}", file=sys.stderr)

        # --- Attempt #3: use inactive_players table for any entries that season ---
        # Note: inactive_players game‐level, so grab unique names
        sql3 = """
        SELECT DISTINCT first_name || ' ' || last_name AS player_name
          FROM inactive_players
         WHERE team_id = ?
        """
        df3 = pd.read_sql(sql3, con, params=(tid,))
        if not df3.empty:
            print(f"[get_roster] using inactive_players fallback for {team}", file=sys.stderr)
            names = df3["player_name"].tolist()
            return {"starters": names[:5], "bench": names[5:]}

        # Nothing found at all
        print(f"[get_roster] no roster data for {team}", file=sys.stderr)
        return {"starters": [], "bench": []}


# ─── Schedule from `game` table ─────────────────────────────────────────
@functools.lru_cache(maxsize=128)
def get_team_schedule(team: str, season: int) -> pd.DataFrame:
    """
    Return DataFrame with game_id & date for all games where <team> is home or away.
    """
    with _connect() as con:
        tid = pd.read_sql(
            "SELECT id FROM team WHERE full_name = ?", con,
            params=(team,)
        )["id"].iloc[0]

        sql = """
        SELECT game_id, game_date
          FROM game
         WHERE season_id = ?
           AND (team_id_home = ? OR team_id_away = ?)
         ORDER BY game_date
        """
        df = pd.read_sql(sql, con, params=(season, tid, tid))

    df["date"] = pd.to_datetime(df["game_date"]).dt.date
    return df[["game_id", "date"]]

# ─── Back‑to‑back check ──────────────────────────────────────────────────
def played_yesterday(team: str, game_date: str | dt.date) -> bool:
    """True if <team> had a game the day before <game_date>."""
    gd = pd.to_datetime(game_date).date()
    sched = get_team_schedule(team, gd.year)
    return (gd - dt.timedelta(days=1)) in sched["date"].values

# ─── Play‑by‑play loader ─────────────────────────────────────────────────
def play_by_play(game_id: int) -> pd.DataFrame:
    """
    Return the full play‑by‑play lines for <game_id>.
    Columns include eventnum, period, player1_name, score, etc.
    """
    with _connect() as con:
        df = pd.read_sql(
            "SELECT * FROM play_by_play WHERE game_id = ? "
            "ORDER BY period, eventnum",
            con,
            params=(game_id,)
        )
    return df
