# app.py – NBA Simulator (Engine v0.8.2)
import streamlit as st
import numpy as np
import pandas as pd
from datetime import date
from nba_sim.rosters_live import get_team_list, get_roster
from nba_sim.utils.injury import get_status
from nba_sim import calibration as calib, weights as W
from main import play_game

ENGINE_VERSION = "v0.8.2"

# ---------- page ----------
st.set_page_config(page_title="NBA Game Sim", layout="wide")
st.title(f"🔮 48‑Min NBA Simulator  |  {ENGINE_VERSION}")

TEAM_OPTIONS = ["— Select —"] + get_team_list()

# ---------- session defaults ----------
for k in ["home_team","away_team",
          "home_starters","home_bench",
          "away_starters","away_bench"]:
    st.session_state.setdefault(k,"")

def refresh(side:str):
    team = st.session_state[f"{side}_team"]
    if team != "— Select —":
        r = get_roster(team)
        st.session_state[f"{side}_starters"] = "\n".join(r["starters"])
        st.session_state[f"{side}_bench"]    = "\n".join(r["bench"])
    else:
        st.session_state[f"{side}_starters"] = ""
        st.session_state[f"{side}_bench"]    = ""

# ---------- pickers ----------
col1,col2 = st.columns(2)
with col1:
    st.selectbox("Home team", TEAM_OPTIONS,
                 key="home_team", on_change=refresh, args=("home",))
    st.text_area("Home starters", key="home_starters", height=120)
    st.text_area("Home bench",    key="home_bench",   height=120)
with col2:
    st.selectbox("Away team", TEAM_OPTIONS,
                 key="away_team", on_change=refresh, args=("away",))
    st.text_area("Away starters", key="away_starters", height=120)
    st.text_area("Away bench",    key="away_bench",   height=120)

game_date = st.date_input("Game date", value=date.today())
runs      = st.slider("Simulations", 10, 500, 50)

# ---------- calibration sidebar ----------
with st.sidebar:
    st.header("🛠 Calibration")
    cal_mode = st.checkbox("Enable calibrator")
    if cal_mode:
        actual_home = st.number_input("Actual home score", value=0)
        actual_away = st.number_input("Actual away score", value=0)
        cal_trials  = st.slider("Calibration trials", 5, 50, 25)

# ---------- simulate ----------
if st.button("▶️ Simulate"):
    if "— Select —" in (st.session_state.home_team, st.session_state.away_team):
        st.error("Pick both teams before simulating.")
        st.stop()

    cfg = {
        "game_date": str(game_date),
        "home_team": st.session_state.home_team,
        "away_team": st.session_state.away_team,
        "home_starters": [p for p in st.session_state.home_starters.splitlines() if p],
        "away_starters": [p for p in st.session_state.away_starters.splitlines() if p],
        "home_backups":  [p for p in st.session_state.home_bench.splitlines() if p],
        "away_backups":  [p for p in st.session_state.away_bench.splitlines() if p],
    }

    # injury sidebar
    with st.sidebar.expander("Injury report"):
        for pl in cfg["home_starters"] + cfg["away_starters"]:
            st.write(f"{pl}: **{get_status(pl)}**")

    # calibration
    if cal_mode and (actual_home or actual_away):
        with st.spinner("Calibrating…"):
            W.save(W.DEFAULT)
            new_w, best_err = calib.calibrate(cfg, actual_home, actual_away, cal_trials)
        st.sidebar.success(f"MAE ≈ {best_err:.2f}")
        st.sidebar.json(new_w, expanded=False)

    # ---------- run sims ----------
    res_h, res_a, boxes_h, boxes_a = [], [], [], []
    bar = st.progress(0.0)
    for i in range(runs):
        g = play_game(cfg, seed=i)
        res_h.append(g["Final Score"][cfg["home_team"]])
        res_a.append(g["Final Score"][cfg["away_team"]])
        boxes_h.append(pd.DataFrame(g["Box Scores"][cfg["home_team"]]))
        boxes_a.append(pd.DataFrame(g["Box Scores"][cfg["away_team"]]))
        bar.progress((i + 1) / runs)

    # aggregate box scores
    box_h = pd.concat(boxes_h).groupby("Player").mean().round(0)
    box_a = pd.concat(boxes_a).groupby("Player").mean().round(0)

    avg_h, avg_a = np.mean(res_h), np.mean(res_a)
    st.markdown(
        f"<h2 style='text-align:center;margin-top:0;'>"
        f"{cfg['home_team']} {avg_h:.0f} – {avg_a:.0f} {cfg['away_team']}"
        f"</h2>",
        unsafe_allow_html=True
    )

    def as_int(df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()
        num_cols = out.select_dtypes("number").columns
        out[num_cols] = out[num_cols].astype(int)
        return out

    ch, ca = st.columns(2)
    with ch:
        st.subheader(f"{cfg['home_team']} Box (avg)")
        st.dataframe(as_int(box_h), use_container_width=True)
    with ca:
        st.subheader(f"{cfg['away_team']} Box (avg)")
        st.dataframe(as_int(box_a), use_container_width=True)
