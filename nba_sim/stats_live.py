"""
Live player season stats with safe fallback.
"""
import pandas as pd
from functools import lru_cache
from datetime import datetime
from .utils.scraping import soup

_DEFAULT_ROW = pd.Series({
    "Age":27,"PTS":12,"AST":3,"TRB":4,"FG%":.46,"3PA":3,"FGA":10,"USG%":20
})

def _slug(full:str)->str:
    p=full.lower().replace(".","").split()
    return p[-1][:5]+p[0][:2]+"01"

def _season():
    t=datetime.now(); return t.year+ (1 if t.month>=7 else 0)

@lru_cache(maxsize=None)
def get_stats(full_name:str,year:int|None=None)->pd.Series:
    year=year or _season()
    url=f"https://www.basketball-reference.com/players/{full_name[0].lower()}/{_slug(full_name)}.html"
    html=soup(url)
    if not html:
        return _DEFAULT_ROW.copy()
    try:
        per=pd.read_html(str(html.select_one("#per_game")))[0]
        per=per[per["Season"].str.contains("-")]
        per["Season_start"]=per["Season"].str[:4].astype(int)
        row=per[per["Season_start"]==year-1]
        if row.empty: row=per.iloc[-1:]
        return row.squeeze()
    except Exception:
        return _DEFAULT_ROW.copy()

def get_tendencies(full_name:str,year:int|None=None)->dict:
    s=get_stats(full_name,year)
    fga=float(s.get("FGA",10)); tpa=float(s.get("3PA",3))
    three=max(0,min(1,tpa/fga)) if fga else 0.35
    iso=0.07+0.4*max(0,(float(s.get("USG%",20))-20)/15)
    drive=0.25-three*0.2
    return {"three_pt_rate":round(three,2),
            "iso_freq":round(iso,2),
            "drive_rate":round(drive,2)}
