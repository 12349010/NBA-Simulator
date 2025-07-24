"""
data_sqlite.py  – helpers to query the local NBA SQLite dump at data/nba.sqlite
(auto‑downloads from Google Drive on first run)
"""

from pathlib import Path
import sqlite3, pandas as pd, functools, datetime as dt, contextlib, requests, sys

# ─── point at the SQLite file in your repo's data/ folder ────────────────
PKG_DIR = Path(__file__).parent             # .../nba_sim
DB_PATH = (PKG_DIR.parent / "data" / "nba.sqlite").resolve()

# ─── your public Google Drive direct‑download link ──────────────────────
DOWNLOAD_URL = (
    "https://drive.google.com/uc?export=download"
    "&id=1vvpcwTK6s11d8i5Cpb_sAAKN86AFaKjx"
)

# ─── ensure the data folder exists ──────────────────────────────────────
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

# ─── if the DB isn’t there, grab it from Google Drive ───────────────────
if not DB_PATH.exists():
    print(f"[Setup] nba.sqlite not found; downloading from Google Drive…", file=sys.stderr)
    resp = requests.get(DOWNLOAD_URL, stream=True, timeout=120)
    resp.raise_for_status()
    with open(DB_PATH, "wb") as f:
        for chunk in resp.iter_content(chunk_size=2_000_000):
            f.write(chunk)
    print(f"[Setup] Download complete: {DB_PATH}", file=sys.stderr)


@contextlib.contextmanager
def _connect():
    con = sqlite3.connect(DB_PATH)
    try:
        yield con
    finally:
        con.close()


@functools.lru_cache(maxsize=None)
def get_team_list() -> list[str]:
    """Return all full team names."""
    with _connect() as con:
        df = pd.read_sql(
            "SELECT DISTINCT full_name FROM team ORDER BY full_name", con
        )
    return df["full_name"].tolist()


@functools.lru_cache(maxsize=512)
def get_roster(team: str, season: int) -> dict[str, list[str]]:
    """
    Return starters (top 5 by games started) and bench for <team> in <season>.
    """
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
