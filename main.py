"""
Thin wrapper: build Team objects, run possession engine, expose play_game()
"""
from nba_sim.possession_engine import simulate_game
from nba_sim.team_model import Team
from nba_sim.rosters_live import get_roster

def build_team(name:str, starters:list[str], bench:list[str], season:int, home:bool):
    roster = starters + bench
    return Team(name, roster, season=season, is_home=home)

def play_game(cfg:dict, seed:int|None=None):
    season = int(cfg["game_date"][:4]) + (1 if int(cfg["game_date"][5:7])>=7 else 0)

    home = build_team(cfg["home_team"],
                      cfg["home_starters"],
                      cfg["home_backups"],
                      season, True)
    away = build_team(cfg["away_team"],
                      cfg["away_starters"],
                      cfg["away_backups"],
                      season, False)

    return simulate_game(home, away, seed=seed)
