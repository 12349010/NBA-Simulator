import json, pandas as pd
from pathlib import Path

DATA = Path(__file__).with_name("../data/players.json").resolve()

with open(DATA) as f:
    PLAYERS = json.load(f)["league"]["standard"]

TEAM_NAME = {int(p["teamId"]): p["teamSitesOnly"]["teamName"] + " " +
             p["teamSitesOnly"]["teamNickname"]
             for p in PLAYERS if p["teamId"]}

def get_team_list():
    return sorted(set(TEAM_NAME.values()))

def get_roster(team_name):
    tid = next(k for k,v in TEAM_NAME.items() if v==team_name)
    names=[f"{p['firstName']} {p['lastName']}".strip()
           for p in PLAYERS if p["teamId"]==str(tid)]
    return {"starters": names[:5], "bench": names[5:]}
