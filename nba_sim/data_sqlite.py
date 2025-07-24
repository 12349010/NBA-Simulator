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
    Uses common_player_info.from_year/to_year to pick that season's roster.
    """
    with _connect() as con:
        # look up the team’s numeric ID
        tid = pd.read_sql(
            "SELECT id FROM team WHERE full_name = ?", con,
            params=(team,)
        )["id"].iloc[0]

        # grab everyone whose from_year ≤ season ≤ to_year
        sql = """
        SELECT display_first_last AS player_name
          FROM common_player_info
         WHERE team_id = ?
           AND from_year <= ?
           AND to_year   >= ?
         ORDER BY player_name
        """
        df = pd.read_sql(sql, con, params=(tid, season, season))

    names = df["player_name"].tolist()
    return {
        "starters": names[:5],
        "bench":    names[5:]
    }

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
