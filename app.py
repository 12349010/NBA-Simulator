############################################
# app.py  –  Streamlit GUI  (Engine v0.6.1) #
############################################
import streamlit as st, numpy as np, pandas as pd
from datetime import date
from nba_sim import calibration as calib, weights as W
from nba_sim.rosters_live import get_team_list, get_roster
from nba_sim.utils.injury import get_status
from main import play_game

ENGINE_VERSION = "v0.6.1-dynamic-rosters"

st.set_page_config(page_title="NBA Game Sim", layout="wide")
st.title(f"🔮 48‑Min NBA Simulator | {ENGINE_VERSION}")

ALL_TEAMS = get_team_list()

# ---------- sidebar: calibration ----------
with st.sidebar:
    st.header("🛠 Calibration")
    cal_mode = st.checkbox("Enable calibrator")
    if cal_mode:
        st.caption("Enter actual scores in main form after selecting teams.")

# ---------- main form ----------
with st.form("sim_form", clear_on_submit=False):
    col1, col2 = st.columns(2)

    # ---- HOME COLUMN ----
    with col1:
        home_team = st.selectbox("Home team", ALL_TEAMS, index=ALL_TEAM_
