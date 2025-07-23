############################################
# app.py  –  NBA Simulator  (Engine v0.7)  #
############################################
import streamlit as st, numpy as np, pandas as pd
from datetime import date
from nba_sim import calibration as calib, weights as W
from nba_sim.rosters_live import get_team_list, get_roster
from nba_sim.utils.injury import get_status
from main import play_game

ENGINE_VERSION = "v0.7-coachless"

st.set_page_config(page_title="NBA Game Sim", layout="wide")
st.title(f"🔮 48‑Min NBA Simulator | {ENGINE_VERSION}")

TEAM_OPTIONS = ["— Select —"] + get_team_list()

# init state
for k in ["home_team","away_team","home_starters","away_starters","home_bench","away_bench"]:
    st.session_state.setdefault(k,"")

def refresh(side:str):
    team = st.session_state[f"{side}_team"]
    if team == "— Select —":
        st.session_state[f"{side}_starters"] = ""
        st.session_state[f"{side}_bench"] = ""
    else:
        r = get_roster(team)
        st.session_state[f"{side}_starters"] = "\n".join(r["starters"])
        st.session_state[f"{side}_bench"]    = "\n".join(r["bench"])

# sidebar calibration
with st.sidebar:
    st.header("🛠 Calibration")
    cal_mode = st.checkbox("Enable calibrator")

# main UI
c1,c2 = st.columns(2)

with c1:
    st.selectbox("Home team",TEAM_OPTIONS,key="home_team",on_change=refresh,args=("home",))
    st.text_area("Home starters",key="home_starters",height=120)
    st.text_area("Home bench",key="home_bench",height=120)

with c2:
    st.selectbox("Away team",TEAM_OPTIONS,key="away_team",on_change=refresh,args=("away",))
    st.text_area("Away starters",key="away_starters",height=120)
    st.text_area("Away bench",key="away_bench",height=120)

game_date = st.date_input("Game date",value=date.today())
runs      = st.slider("Number of simulations",1,500,100)

if cal_mode:
    ch,ca = st.columns(2)
    actual_home = ch.number_input("Actual home score",value=0)
    actual_away = ca.number_input("Actual away score",value=0)
    cal_trials  = st.slider("Calibration trials",5,50,25)

if st.button("▶️  Simulate"):
    if "— Select —" in (st.session_state.home_team, st.session_state.away_team):
        st.error("Pick both teams first"); st.stop()

    cfg = {
        "game_date": str(game_date),
        "home_team": st.session_state.home_team,
        "away_team": st.session_state.away_team,
        "home_starters":[p for p in st.session_state.home_starters.splitlines() if p],
        "away_starters":[p for p in st.session_state.away_starters.splitlines() if p],
        "home_backups":[p for p in st.session_state.home_bench.splitlines() if p],
        "away_backups":[p for p in st.session_state.away_bench.splitlines() if p]
    }

    with st.sidebar.expander("Injury report"):
        for pl in cfg["home_starters"]+cfg["away_starters"]:
            st.write(f"{pl}: **{get_status(pl)}**")

    if cal_mode and (actual_home or actual_away):
        with st.spinner("Calibrating…"):
            W.save(W.DEFAULT)
            new_w,best_err = calib.calibrate(cfg,actual_home,actual_away,cal_trials)
        st.sidebar.success(f"MAE ≈ {best_err:.2f}")
        st.sidebar.json(new_w)

    bar = st.progress(0.0)
    res_h,res_a,per_player = [],[],{}
    for i in range(runs):
        out = play_game(cfg)
        res_h.append(out["Final Score"][cfg["home_team"]])
        res_a.append(out["Final Score"][cfg["away_team"]])
        for pl,pts in out["Box"].items():
            per_player.setdefault(pl,[]).append(pts)
        bar.progress((i+1)/runs)

    st.subheader("Average Final Score")
    st.markdown(f"**{cfg['home_team']}: {np.mean(res_h):.1f} | {cfg['away_team']}: {np.mean(res_a):.1f}**")

    wp = sum(h>a for h,a in zip(res_h,res_a))/runs
    st.subheader("Win Probability")
    st.markdown(f"- **{cfg['home_team']}: {wp:.1%}**  - **{cfg['away_team']}: {1-wp:.1%}**")

    st.subheader("Score‑Diff Histogram")
    st.bar_chart(pd.Series(np.array(res_h)-np.array(res_a)).value_counts().sort_index())

    st.subheader("Top Performers (median PTS)")
    tops = sorted(((p,np.median(v)) for p,v in per_player.items()),key=lambda x:x[1],reverse=True)[:5]
    st.table(pd.DataFrame(tops,columns=["Player","Median PTS"]))

    st.expander("Sample single‑game JSON").json(play_game(cfg))
