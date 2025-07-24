from nba_sim.team_model import Team
from nba_sim.possession_engine import simulate_game
from nba_sim.data_sqlite import (
    get_team_list,      # for populating your team dropdown
    get_roster,         # to fetch starters & bench
    get_team_schedule,  # for fatigue / schedule lookups
    played_yesterday,   # to check back‑to‑back games
    play_by_play        # (if/when you need play‑by‑play data)
)

def _build(name, starters, bench, season, home):
    return Team(name, starters+bench, season, is_home=home)

def play_game(cfg:dict, seed:int|None=None):
    season=int(cfg["game_date"][:4])+(1 if int(cfg["game_date"][5:7])>=7 else 0)
    home=_build(cfg["home_team"], cfg["home_starters"], cfg["home_backups"], season, True)
    away=_build(cfg["away_team"], cfg["away_starters"], cfg["away_backups"], season, False)
    return simulate_game(home, away, cfg["game_date"], cfg.get("fatigue_on",True), seed)
