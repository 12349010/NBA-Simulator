"""
main.py – thin wrapper around the simulation engine.
Builds Team objects, then calls simulate_game().
"""
from nba_sim.team_model import Team
from nba_sim.possession_engine import simulate_game

# ------------- helpers -------------
def _build_team(team_name: str, starters: list[str], bench: list[str],
                season: int, is_home: bool) -> Team:
    roster = starters + bench
    return Team(team_name, roster, season, is_home=is_home)

# ------------- public API -------------
def play_game(cfg: dict, seed: int | None = None):
    """
    cfg expects:
      game_date: 'YYYY-MM-DD'
      home_team, away_team
      home_starters, away_starters  (list[str])
      home_backups,  away_backups   (list[str])
    """
    season = int(cfg["game_date"][:4])
    if int(cfg["game_date"][5:7]) >= 7:       # after July = next NBA season
        season += 1

    home = _build_team(cfg["home_team"],
                       cfg["home_starters"],
                       cfg["home_backups"],
                       season,
                       is_home=True)

    away = _build_team(cfg["away_team"],
                       cfg["away_starters"],
                       cfg["away_backups"],
                       season,
                       is_home=False)

    return simulate_game(home, away, seed=seed)
