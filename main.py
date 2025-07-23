import random, copy
import nba_sim.data_acquisition as da
from nba_sim.team_model      import Team
from nba_sim.player_model    import Player
from nba_sim.possession_engine import simulate_possession
from nba_sim import weights as W

SIM_WEIGHTS = W.load()

def _build_team(name, starters, backups, coach, season, is_home):
    roster = starters + backups
    ages = {n: 20 + len(da.get_player_season_avgs(da.slugify(n), season)) for n in roster}
    players = [Player(n, ages[n], season) for n in roster]
    players = [p for p in players if p.minutes_cap > 0]   # skip 'Out'
    return Team(name, players, da.get_coach_profile(coach), is_home)
    
def play_game(cfg: dict):
    random.seed()                 # new seed each call
    state = {"minute": 0}
    score = {cfg["home_team"]: 0, cfg["away_team"]: 0}
    box   = {}

    home = _build_team(cfg["home_team"], cfg["home_starters"], cfg["home_backups"],
                       cfg["home_coach"], int(cfg["game_date"][:4]), True)
    away = _build_team(cfg["away_team"], cfg["away_starters"], cfg["away_backups"],
                       cfg["away_coach"], int(cfg["game_date"][:4]), False)

    while state["minute"] < 48:
        for offense, defense in ((home, away), (away, home)):
            out = simulate_possession(offense, defense, state)
            pts = out["points"]
            score[offense.name] += pts
            if pts:
                box.setdefault(out["shooter"], 0)
                box[out["shooter"]] += pts
            state["minute"] += out["elapsed"] / 60
            if state["minute"] >= 48: break

    return {
        "Final Score": score,
        "Box": box,
        "Tendencies": {p.name: p.tendencies for p in home.players + away.players}
    }
