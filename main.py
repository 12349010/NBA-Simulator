"""
CLI helper so we can call `python main.py` (or import play_game elsewhere).
"""
import random, json
import nba_sim.data_acquisition as da
from nba_sim.team_model      import Team
from nba_sim.player_model    import Player
from nba_sim.possession_engine import simulate_possession

def _build_team(name, starters, backups, coach, season, is_home):
    roster = starters + backups
    # crude age estimate: rookie (age 20) + seasons played
    ages = {n: 20 + len(da.get_player_season_avgs(da.slugify(n), season)) for n in roster}
    players = [Player(n, ages[n], season) for n in roster]
    return Team(name, players, da.get_coach_profile(coach), is_home)

def play_game(cfg: dict):
    random.seed(42)                          # reproducibility
    state = {"minute": 0}
    score = {cfg["home_team"]: 0, cfg["away_team"]: 0}

    home = _build_team(cfg["home_team"], cfg["home_starters"], cfg["home_backups"],
                       cfg["home_coach"], int(cfg["game_date"][:4]), True)
    away = _build_team(cfg["away_team"], cfg["away_starters"], cfg["away_backups"],
                       cfg["away_coach"], int(cfg["game_date"][:4]), False)

    # 48-minute regulation
    while state["minute"] < 48:
        for offense, defense in ((home, away), (away, home)):
            out = simulate_possession(offense, defense, state)
            score[offense.name] += out["points"]
            state["minute"] += out["elapsed"] / 60
            if state["minute"] >= 48:
                break
    return score

# ---------- CLI entry ----------
if __name__ == "__main__":
    # expects cfg.json in the same folder OR falls back to tiny example
    try:
        cfg = json.load(open("cfg.json"))
    except FileNotFoundError:
        cfg = {
            "game_date": "2025-07-22",
            "home_team": "Golden State Warriors",
            "away_team": "Boston Celtics",
            "home_starters":  ["Stephen Curry","Klay Thompson","Andrew Wiggins","Draymond Green","Kevon Looney"],
            "away_starters":  ["Jrue Holiday","Derrick White","Jaylen Brown","Jayson Tatum","Kristaps Porzingis"],
            "home_backups":   [],
            "away_backups":   [],
            "home_coach": "Steve Kerr",
            "away_coach": "Joe Mazzulla"
        }
    print(play_game(cfg))
