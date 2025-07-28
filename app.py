# app.py
import streamlit as st
import pandas as pd
from typing import Optional

from nba_sim.data_csv import (
    get_team_list,
    get_team_schedule,
    get_roster,
)
from nba_sim.utils.injury import get_status
from nba_sim import calibration as calib, weights as W
from nba_sim.possession_engine import simulate_game
from nba_sim.team_model import Team


st.set_page_config(page_title="NBA Game Simulator", layout="wide")
st.title("🏀 NBA Game Simulator")

# Sidebar: Team & Season Selection
st.sidebar.header("Select Teams & Season")
teams_df = get_team_list()
team_names = teams_df["team_name"].tolist()

home_team = st.sidebar.selectbox("Home Team", team_names)
away_team = st.sidebar.selectbox("Away Team", [t for t in team_names if t != home_team])
season = st.sidebar.selectbox("Season", list(range(1950, pd.Timestamp.now().year + 1)))

# Sidebar: Roster Selection
st.sidebar.header("Build Rosters")
home_full_roster = get_roster(home_team, season)
away_full_roster = get_roster(away_team, season)

home_start = st.sidebar.multiselect(
    f"{home_team} Starters", home_full_roster["display_first_last"].tolist(), max_selections=5
)
home_bench = st.sidebar.multiselect(
    f"{home_team} Bench", [n for n in home_full_roster["display_first_last"] if n not in home_start]
)

away_start = st.sidebar.multiselect(
    f"{away_team} Starters", away_full_roster["display_first_last"].tolist(), max_selections=5
)
away_bench = st.sidebar.multiselect(
    f"{away_team} Bench", [n for n in away_full_roster["display_first_last"] if n not in away_start]
)

# Simulation runner
def run_sim():
    # Look up team IDs
    home_id = teams_df.loc[teams_df.team_name == home_team, "team_id"].iloc[0]
    away_id = teams_df.loc[teams_df.team_name == away_team, "team_id"].iloc[0]

    # Instantiate Team objects (pull in rosters, season, etc.)
    home_obj = Team(home_id, season, starters=home_start, bench=home_bench)
    away_obj = Team(away_id, season, starters=away_start, bench=away_bench)

    # Run the simulation
    events = simulate_game(home_obj, away_obj)

    # Display a live-updating play-by-play & box score
    box = {}
    st.write(f"## Simulation: {home_team} vs. {away_team} ({season})")
    live = st.empty()
    score_display = st.empty()

    home_pts = away_pts = 0
    for ev in events:
        # suppose each ev is {'time':..., 'desc':..., 'home_pts':..., 'away_pts':...}
        home_pts = ev.get("home_pts", home_pts)
        away_pts = ev.get("away_pts", away_pts)
        score_display.text(f"**Score:** {home_team} {home_pts} – {away_team} {away_pts}")
        live.write(f"{ev['time']} – {ev['desc']}")
        # optional sleep for pacing
        # st.sleep(0.5)

    st.success("🏁 End of Simulation")

# Button
if st.button("Run Simulation"):
    run_sim()
