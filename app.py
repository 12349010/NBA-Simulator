############################################
# app.py  –  NBA Simulator  (Engine v0.8.1) #
############################################
import streamlit as st, numpy as np, pandas as pd
from datetime import date
from nba_sim import calibration as calib, weights as W
from nba_sim.rosters_live import get_team_list, get_roster
from nba_sim.utils.injury import get_status
from main import play_game

ENGINE = "v0.8.1"

st.set_page_config(page_title="NBA Game Sim", layout="wide")
st.title(f"🔮 48‑Min NBA Simulator  |  {ENGINE}")

teams = ["— Select —"]+get_team_list()
for k in ["home_team","away_team","home_starters","away_starters","home_bench","away_bench"]:
    st.session_state.setdefault(k,"")

def _refresh(side):
    tm=st.session_state[f"{side}_team"]
    if tm!="— Select —":
        r=get_roster(tm)
        st.session_state[f"{side}_starters"]="\n".join(r["starters"])
        st.session_state[f"{side}_bench"]="\n".join(r["bench"])
    else:
        st.session_state[f"{side}_starters"]=st.session_state[f"{side}_bench"]=""

c1,c2=st.columns(2)
with c1:
    st.selectbox("Home team",teams,key="home_team",on_change=_refresh,args=("home",))
    st.text_area("Home starters",key="home_starters",height=120)
    st.text_area("Home bench",key="home_bench",height=120)
with c2:
    st.selectbox("Away team",teams,key="away_team",on_change=_refresh,args=("away",))
    st.text_area("Away starters",key="away_starters",height=120)
    st.text_area("Away bench",key="away_bench",height=120)

game_date=st.date_input("Game date",value=date.today())
runs=st.slider("Simulations",10,500,100)

if st.button("▶️ Simulate"):
    if "— Select —" in (st.session_state.home_team,st.session_state.away_team):
        st.error("Pick both teams first"); st.stop()

    cfg={
        "game_date":str(game_date),
        "home_team":st.session_state.home_team,
        "away_team":st.session_state.away_team,
        "home_starters":[p for p in st.session_state.home_starters.splitlines() if p],
        "away_starters":[p for p in st.session_state.away_starters.splitlines() if p],
        "home_backups":[p for p in st.session_state.home_bench.splitlines() if p],
        "away_backups":[p for p in st.session_state.away_bench.splitlines() if p]
    }

    res_home,res_away,boxes_home,boxes_away=[],[],[],[]
    bar=st.progress(0.0)
    for i in range(runs):
        g=play_game(cfg,i)
        res_home.append(g["Final Score"][cfg["home_team"]])
        res_away.append(g["Final Score"][cfg["away_team"]])
        boxes_home.append(pd.DataFrame(g["Box Scores"][cfg["home_team"]]))
        boxes_away.append(pd.DataFrame(g["Box Scores"][cfg["away_team"]]))
        bar.progress((i+1)/runs)

    # aggregate box scores
    box_h=pd.concat(boxes_home).groupby("Player").mean().round(1).reset_index()
    box_a=pd.concat(boxes_away).groupby("Player").mean().round(1).reset_index()

    # big centred score banner
    avg_h,avg_a=np.mean(res_home),np.mean(res_away)
    st.markdown(
        f"<h2 style='text-align:center;margin-top:0'>"
        f"{cfg['home_team']} {avg_h:=.0f} – {avg_a:=.0f} {cfg['away_team']}"
        f"</h2>",
        unsafe_allow_html=True)

    colh,cola=st.columns(2)
    with colh:
        st.subheader(f"{cfg['home_team']} Box (avg)")
        st.dataframe(box_h.round(0).astype(int),use_container_width=True)
    with cola:
        st.subheader(f"{cfg['away_team']} Box (avg)")
        st.dataframe(box_a.round(0).astype(int),use_container_width=True)
