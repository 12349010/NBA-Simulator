import streamlit as st
import pandas as pd
import numpy as np
from datetime import date

from nba_sim.data_csv import get_team_list, get_team_schedule, iter_play_by_play, _game_df
from nba_sim.utils.injury import get_status
from nba_sim import calibration as calib, weights as W
from nba_sim.possession_engine import simulate_game
from nba_sim.team_model import Team

# Page config & version
st.set_page_config(page_title="NBA 48‑Min Simulator", layout="wide")
ENGINE_VERSION = "v0.9.1"
st.sidebar.markdown(f"**Engine v{ENGINE_VERSION}**")

# Sidebar controls
# Team selection
t_teams = get_team_list()
teams = t_teams['full_name'].tolist()
home_team = st.sidebar.selectbox("Home Team", teams)
away_team = st.sidebar.selectbox("Away Team", [t for t in teams if t != home_team])

# Season selection
# Pull all raw season IDs
season_ids = sorted(_game_df['season_id'].astype(int).unique())

# Build human‐friendly labels
season_labels = [str(sid % 10000) for sid in season_ids]  # 12008 → “2008”, 22021 → “2021”

# Let user pick by label, then map back to the real ID
chosen_label = st.sidebar.selectbox("Season", season_labels)
season = season_ids[season_labels.index(chosen_label)]

# Game date selection
game_date = st.sidebar.date_input(
    "Game Date",
    value=date.today()
).strftime("%Y-%m-%d")

# Number of simulations
sim_runs = st.sidebar.number_input(
    "Number of simulations",
    min_value=1,
    value=100,
    step=1
)

# Fatigue toggle
fatigue_on = st.sidebar.checkbox(
    "Apply fatigue (back‑to‑back)",
    value=True
)

# Optional: injured players
if st.sidebar.checkbox("Show injured players"):
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
                    "fatigue_on": fatigue_on,
                    "season": season
                }
            )
            st.sidebar.write("**Calibration Results**", cal_results)
        except Exception as e:
            st.sidebar.error(f"Calibration error: {e}")

# Main simulation trigger
if st.sidebar.button("Run Simulations"):
    # Initialize Team objects
    home = Team(home_team, season, is_home=True)
    away = Team(away_team, season, is_home=False)

    results_home = []
    results_away = []
    boxes_home = []
    boxes_away = []
    bar = st.progress(0.0)

    for i in range(int(sim_runs)):
        sim_cfg = {"seed": i, "fatigue_on": fatigue_on}
        g = simulate_game(home, away, game_date, sim_cfg)

        results_home.append(g["Final Score"][home_team])
        results_away.append(g["Final Score"][away_team])
        boxes_home.append(pd.DataFrame(g["Box Scores"][home_team]))
        boxes_away.append(pd.DataFrame(g["Box Scores"][away_team]))

        bar.progress((i + 1) / sim_runs)

    # Summary stats
    home_avg = np.mean(results_home)
    away_avg = np.mean(results_away)
    home_wins = sum(1 for h, a in zip(results_home, results_away) if h > a)
    win_pct = 100 * home_wins / sim_runs

    st.subheader("Simulation Summary")
    st.write({
        f"{home_team} avg": round(home_avg, 1),
        f"{away_team} avg": round(away_avg, 1),
        f"{home_team} win %": f"{win_pct:.1f}%"
    })

    df_scores = pd.DataFrame({home_team: results_home, away_team: results_away})
    st.bar_chart(df_scores)

    # Show sample box scores
    st.subheader("Sample Box Scores (Last Simulation)")
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**{home_team} Box**")
        st.dataframe(boxes_home[-1], use_container_width=True)
    with col2:
        st.write(f"**{away_team} Box**")
        st.dataframe(boxes_away[-1], use_container_width=True)

    # Play-by-play log
    if "Play Log" in g:
        with st.expander("Play‑by‑Play Log", expanded=False):
            for e in g["Play Log"]:
                assist_part = f", AST by {e.get('assist')}" if e.get('assist') else ""
                st.write(
                    f"Q{e['quarter']} {e['time']} — {e['team']}: "
                    f"{e['player']} {e['action']} (+{e['points']} pts), "
                    f"REB {e['rebound']}{assist_part}"
                )
