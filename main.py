from nba_sim.team_model import Team
from nba_sim.possession_engine import simulate_game
from nba_sim.rosters_http import roster as get_roster, team_list as get_team_list
from nba_sim.schedule_http import games as get_team_schedule

def _build(name, starters, bench, season, home):
    return Team(name, starters+bench, season, is_home=home)

def play_game(cfg:dict, seed:int|None=None):
    season=int(cfg["game_date"][:4])+(1 if int(cfg["game_date"][5:7])>=7 else 0)
    home=_build(cfg["home_team"], cfg["home_starters"], cfg["home_backups"], season, True)
    away=_build(cfg["away_team"], cfg["away_starters"], cfg["away_backups"], season, False)
    return simulate_game(home, away, cfg["game_date"], cfg.get("fatigue_on",True), seed)
