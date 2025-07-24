from nba_sim.team_model import Team
from nba_sim.possession_engine import simulate_game

def _build(name, starters, bench, season, home):
    return Team(name, starters + bench, season, is_home=home)

def play_game(cfg: dict, seed: int | None = None):
    # Determine NBA season based on game_date
    year, month = map(int, cfg["game_date"].split("-")[:2])
    season = year + (1 if month >= 7 else 0)

    # Build Team objects for home and away
    home = _build(
        cfg["home_team"],
        cfg.get("home_starters", []),
        cfg.get("home_backups", []),
        season,
        True,
    )
    away = _build(
        cfg["away_team"],
        cfg.get("away_starters", []),
        cfg.get("away_backups", []),
        season,
        False,
    )

    # Consolidate simulation config
    config = {
        "fatigue_on": cfg.get("fatigue_on", True),
        "seed": seed,
    }

    # Run simulation and return results
    return simulate_game(home, away, cfg["game_date"], config)
