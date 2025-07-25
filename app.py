# app.py

import streamlit as st
import pandas as pd
import numpy as np
from datetime import date

from nba_sim.data_sqlite import get_team_list
from nba_sim.utils.injury import get_status
from nba_sim import calibration as calib, weights as W
from main import play_game

# --------------------------------------------
# Page config & version
# --------------------------------------------
st.set_page_config(page_title="NBA 48‑Min Simulator", layout="wide")
ENGINE_VERSION = "v0.9.1"
st.sidebar.markdown(f"**Engine v{ENGINE_VERSION}**")

# --------------------------------------------
# Sidebar controls
# --------------------------------------------
teams = get_team_list()
home_team = st.sidebar.selectbox("Home Team", teams)
away_team = st.sidebar.selectbox("Away Team", [t for t in teams if t != home_team])

game_date = st.sidebar.date_input(
    "Game Date",
    value=date.today()
).strftime("%Y-%m-%d")

sim_runs = st.sidebar.number_input(
    "Number of simulations",
    min_value=1,
    value=100,
    step=1
)

fatigue_on = st.sidebar.checkbox(
    "Apply fatigue (back‑to‑back)",
    value=True
)

# Optional: show current injury status
if st.sidebar.checkbox("Show injuried players"):
    st.sidebar.write(f"**{home_team} Injuries:**", get_status(home_team))
    st.sidebar.write(f"**{away_team} Injuries:**", get_status(away_team))

# Calibration controls
calibrate = st.sidebar.checkbox("Calibrate to actual", value=False)
if calibrate:
    game_id_input = st.sidebar.text_input("Game ID for calibration", "")
    if st.sidebar.button("Run Calibration"):
        try:
            cal_results = calib.calibrate(
                int(game_id_input),
                {
                    "home_team": home_team,
                    "away_team": away_team,
                    "game_date": game_date,
                    "fatigue_on": fatigue_on
                }
            )
            st.sidebar.write("**Calibration Results**", cal_results)
        except Exception as e:
            st.sidebar.error(f"Calibration error: {e}")

# --------------------------------------------
# Main simulation trigger
# --------------------------------------------
if st.sidebar.button("Run Simulations"):
    cfg = {
        "home_team": home_team,
        "away_team": away_team,
        "game_date": game_date,
        "fatigue_on": fatigue_on
    }

    res_h, res_a = [], []
    boxes_h, boxes_a = [], []
    bar = st.progress(0.0)

    # Monte‑Carlo runs
    for i in range(sim_runs):
        g = play_game(cfg, seed=i)
        res_h.append(g["Final Score"][home_team])
        res_a.append(g["Final Score"][away_team])
        boxes_h.append(pd.DataFrame(g["Box Scores"][home_team]))
        boxes_a.append(pd.DataFrame(g["Box Scores"][away_team]))
        bar.progress((i + 1) / sim_runs)

    # --------------------------------------------
    # Summary stats
    # --------------------------------------------
    home_avg = np.mean(res_h)
    away_avg = np.mean(res_a)
    home_wins = sum(1 for h, a in zip(res_h, res_a) if h > a)
    win_pct = 100 * home_wins / sim_runs

    st.subheader("Simulation Summary")
    st.write({
        f"{home_team} avg": round(home_avg, 1),
        f"{away_team} avg": round(away_avg, 1),
        f"{home_team} win %": f"{win_pct:.1f}%"
    })

    # Score distribution chart
    df_scores = pd.DataFrame({home_team: res_h, away_team: res_a})
    st.bar_chart(df_scores)

    # --------------------------------------------
    # Sample Box Scores
    # --------------------------------------------
    st.subheader("Sample Box Scores (Last Simulation)")
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**{home_team} Box**")
        st.dataframe(boxes_h[-1], use_container_width=True)
    with col2:
        st.write(f"**{away_team} Box**")
        st.dataframe(boxes_a[-1], use_container_width=True)

    # --------------------------------------------
    # Play‑by‑Play Log
    # --------------------------------------------
    if "Play Log" in g:
        with st.expander("Play‑by‑Play Log", expanded=False):
            for e in g["Play Log"]:
                assist_part = f", AST by {e.get('assist')}" if e.get('assist') else ""
                st.write(
                    f"Q{e['quarter']} {e['time']} — {e['team']}: "
                    f"{e['player']} {e['action']} (+{e['points']} pts), "
                    f"REB {e['rebound']}{assist_part}"
                )
