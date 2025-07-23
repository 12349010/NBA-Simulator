"""
schedule_local.py  – Team schedule & back‑to‑back helper
--------------------------------------------------------

Reads the local file `data/schedule.json` committed in the repo
( refreshed nightly by GitHub Action ).

Public API
----------
get_team_schedule(team_name:str, season:int|None) -> pandas.DataFrame
played_yesterday(team_name:str, game_date:str|datetime) -> bool
"""

from __future__ import annotations
import datetime as dt, json
from pathlib import Path
from functools import lru_cache
from typing import List

import pandas as pd

# --------------------------------------------------------------------- #
# Location of the committed JSON (relative to this file)
PKG_DIR = Path(__file__).parent
DATA_PATH = (PKG_DIR.parent / "data" / "schedule.json").resolve()

# Import the team‑id map from the roster module
from nba_sim.rosters_http import TEAM_NAME   # id→name dict

# --------------------------------------------------------------------- #
def _season_year(d: dt.date | None = None) -> int:
    today = d or dt.datetime.now().date()
    return today.year + (1 if today.month >= 7 else 0)

@lru_cache(maxsize=None)
def _schedule_df() -> pd.DataFrame:
    """Load entire schedule.json into a DataFrame once."""
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"{DATA_PATH} missing – make sure GitHub Action committed it."
        )
    games = json.loads(DATA_PATH.read_text())["league"]["standard"]
    df = pd.json_normalize(games)
    df["startDate"] = pd.to_datetime(df["startDateEastern"])
    df["season"]    = df["seasonStageId"].map(
        lambda s: df["startDate"].dt.year.max() if s == 2 else df["startDate"].dt.year
    )
    return df

# --------------------------------------------------------------------- #
def get_team_schedule(team: str, season: int | None = None) -> pd.DataFrame:
    """
    Return DataFrame of all games for <team> in <season>.
    If season is None, uses the season corresponding to today's date.
    Columns include startDate, home/away ids, gameId, etc.
    """
    season = season or _season_year()
    df     = _schedule_df()
    tid    = next(k for k, v in TEAM_NAME.items() if v == team)

    games = df[
        ((df["homeTeam.teamId"] == str(tid)) | (df["awayTeam.teamId"] == str(tid)))
        & (df["startDate"].dt.year.between(season - 1, season))
    ].copy()

    games.sort_values("startDate", inplace=True)
    games.reset_index(drop=True, inplace=True)
    return games

# --------------------------------------------------------------------- #
def played_yesterday(team: str, game_date: str | dt.date) -> bool:
    """
    True if <team> had a game on the day before <game_date>.
    <game_date> may be 'YYYY-MM-DD' or datetime/date.
    """
    gd = pd.to_datetime(game_date).date()
    sched = get_team_schedule(team, gd.year)
    if sched.empty:
        return False
    return (gd - dt.timedelta(days=1)) in sched["startDate"].dt.date.values

# --------------------------------------------------------------------- #
# Simple CLI quick‑test:  python -m nba_sim.schedule_local "Boston Celtics"
if __name__ == "__main__":  # pragma: no cover
    import sys, pprint
    team = sys.argv[1] if len(sys.argv) > 1 else "Boston Celtics"
    print(f"Showing next 5 games for {team}")
    print(get_team_schedule(team).head()[["startDate","gameId"]])
