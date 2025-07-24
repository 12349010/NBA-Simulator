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

# ─── Google Drive file ID (keep this!) ─────────────────────────────────
GDRIVE_ID = "1vvpcwTK6s11d8i5Cpb_sAAKN86AFaKjx"

# ─── Ensure the data folder exists ─────────────────────────────────────
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

def _download_db():
    """Download the SQLite file from Google Drive via gdown."""
    import gdown
    url = f"https://drive.google.com/uc?id={GDRIVE_ID}"
    print("[Setup] nba.sqlite missing or invalid; downloading via gdown…", file=sys.stderr)
    gdown.download(url, str(DB_PATH), quiet=False)
    print(f"[Setup] Download complete: {DB_PATH}", file=sys.stderr)

# ─── Determine whether we need to fetch the DB ──────────────────────────
_need_download = False

if not DB_PATH.exists():
    _need_download = True
else:
    try:
        with open(DB_PATH, "rb") as f:
            header = f.read(15)
        if not header.startswith(b"SQLite format 3"):
            _need_download = True
    except Exception:
        _need_download = True

if _need_download:
    _download_db()

# ─── Context manager for SQLite connections ─────────────────────────────
@contextlib.contextmanager
def _connect():
    con = sqlite3.connect(DB_PATH)
    try:
        yield con
    finally:
        con.close()

# ─── Public helpers ─────────────────────────────────────────────────────

@functools.lru_cache(maxsize=None)
def get_team_list() -> list[str]:
    """Return all full team names."""
    with _connect() as con:
        df = pd.read_sql("SELECT DISTINCT full_name FROM team ORDER BY full_name", con)
    return df["full_name"].tolist()

@functools.lru_cache(maxsize=512)
def get_roster(team: str, season: int) -> dict[str, list[str]]:
    """Return starters (top 5 by games started) and bench for a team in a season."""
    with _connect() as con:
        team_id = pd.read_sql(
            "SELECT team_id FROM team WHERE full_name = ?", con,
            params=(team,)
        )["team_id"].iloc[0]

        query = f"""
          SELECT p.player_name,
                 SUM(CASE WHEN ls.line = 'starter' THEN 1 ELSE 0 END) AS starts
          FROM game g
          JOIN line_score ls ON ls.game_id = g.game_id AND ls.team_id = {team_id}
          JOIN player p     ON p.player_id = ls.player_id
          WHERE g.season = {season}
          GROUP BY p.player_id
          ORDER BY starts DESC
        """
        df = pd.read_sql(query, con)

    names = df["player_name"].tolist()
    return {"starters": names[:5], "bench": names[5:]}

@functools.lru_cache(maxsize=128)
def get_team_schedule(team: str, season: int) -> pd.DataFrame:
    """Return a DataFrame of all games for <team> in <season>."""
    with _connect() as con:
        team_id = pd.read_sql(
            "SELECT team_id FROM team WHERE full_name = ?", con,
            params=(team,)
        )["team_id"].iloc[0]

        df = pd.read_sql(
            f"SELECT game_id, date FROM game "
            f"WHERE season = {season} "
            f"  AND (home_team_id = {team_id} OR away_team_id = {team_id}) "
            f"ORDER BY date",
            con
        )
    df["date"] = pd.to_datetime(df["date"]).dt.date
    return df

def played_yesterday(team: str, game_date: str|dt.date) -> bool:
    """True if <team> had a game the day before <game_date>."""
    gd    = pd.to_datetime(game_date).date()
    sched = get_team_schedule(team, gd.year)
    return (gd - dt.timedelta(days=1)) in sched["date"].values

def play_by_play(game_id: int) -> pd.DataFrame:
    """Fetch the full play‑by‑play lines for a given game."""
    with _connect() as con:
        pbp = pd.read_sql(
            "SELECT * FROM play_by_play WHERE game_id = ? "
            "ORDER BY quarter, time_remaining",
            con, params=(game_id,)
        )
    return pbp
