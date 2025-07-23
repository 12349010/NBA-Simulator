############################################
# app.py  –  Streamlit GUI  (Engine v0.6.2) #
############################################
import streamlit as st, numpy as np, pandas as pd
from datetime import date
from nba_sim import calibration as calib, weights as W
from nba_sim.rosters_live import get_team_list, get_roster
from nba_sim.utils.injury import get_status
from main import play_game

ENGINE_VERSION = "v0.6.2-dyn-fix"

st.set_page_config(page_title="NBA Game Sim", layout="wide")
st.title(f"🔮 48‑Min NBA Simulator | {ENGINE_VERSION}")

all_teams = get_team_list()

# ---------- sidebar: calibration ----------
with st.sidebar:
    st.header("🛠 Calibration")
    cal_mode = st.checkbox("Enable calibrator")
    if cal_mode:
        st.caption("Enter actual scores below the main form.")

# ---------- main form ----------
with st.form("sim_form"):
    col1, col2 = st.columns(2)

    # HOME
    with col1:
        home_team = st.selectbox("Home team", all_teams, index=all_teams.index("Golden State Warriors"))
        h_roster  = get_roster(home_team)
        home_start = st.text_area("Home starters", "\n".join(h_roster["starters"]), height=120)
        home_bench = st.text_area("Home bench",    "\n".join(h_roster["bench"]),    height=120)
        home_coach = st.text_input("Home coach", "")

    # AWAY
