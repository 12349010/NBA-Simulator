import requests, pandas as pd, logging
from functools import lru_cache
from .rosters_http import team_list, FREE, BALL

@lru_cache(maxsize=None)
def games(team_name:str, season:int):
    tid = next(k for k,v in team_list().items() if v==team_name)
    url_base = f"{FREE}/games?per_page=100&team_ids[]={tid}&seasons[]={season}"
    try:
        pages = []
        page=1
        while True:
            js = requests.get(f"{url_base}&page={page}", timeout=10).json()
            pages.extend(js["data"])
            if js["meta"]["next_page"] is None:
                break
            page+=1
        return pd.json_normalize(pages)
    except Exception as e:
        logging.warning(f"free‑nba schedule failed: {e}")
        # fallback balldontlie
        js = requests.get(url_base.replace(FREE, BALL), timeout=10).json()["data"]
        return pd.json_normalize(js)
