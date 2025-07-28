# app.py

import streamlit as st
import pandas as pd

from nba_sim.data_csv import get_team_list, get_roster
from nba_sim.team_model import Team
from nba_sim.possession_engine import simulate_game

# ---- Page Config ----
st.set_page_config(page_title="NBA Game Simulator", layout="wide")
st.title("🏀 NBA Game Simulator")

# ---- Sidebar: Team & Season Selection ----
st.sidebar.header("Select Teams & Season")

# Fetch list of all teams
teams_df = get_team_list()
team_names = teams_df["team_name"].tolist()

# Home/Away selectors
home_team = st.sidebar.selectbox("Home Team", team_names, index=0)
# Remove home choice from away options
away_team = st.sidebar.selectbox(
    "Away Team",
    [t for t in team_names if t != home_team],
    index=0
)

# Season selector
season = st.sidebar.number_input(
    "Season (e.g. 1996)",
    min_value=1946,
    max_value=2100,
    value=2020,
    step=1
)

# ---- Sidebar: Roster Selection ----
# Pull full roster for each side
home_roster_df = get_roster(home_team, season)
away_roster_df = get_roster(away_team, season)

home_players = home_roster_df["display_first_last"].tolist()
away_players = away_roster_df["display_first_last"].tolist()

st.sidebar.markdown("### Home Roster")
home_start = st.sidebar.multiselect(
    "Home Starters (choose 5)",
    options=home_players,
    default=home_players[:5]
)
home_bench = st.sidebar.multiselect(
    "Home Bench",
    options=[p for p in home_players if p not in home_start],
    default=home_players[5:]
)

st.sidebar.markdown("### Away Roster")
away_start = st.sidebar.multiselect(
    "Away Starters (choose 5)",
    options=away_players,
    default=away_players[:5]
)
away_bench = st.sidebar.multiselect(
    "Away Bench",
    options=[p for p in away_players if p not in away_start],
    default=away_players[5:]
)

# ---- Simulation Function ----
def run_sim():
    # Resolve numeric IDs
    home_id = teams_df.loc[teams_df.team_name == home_team, "team_id"].iat[0]
    away_id = teams_df.loc[teams_df.team_name == away_team, "team_id"].iat[0]

    # Build Team objects
    home_obj = Team(
        home_id,
        season,
        starters=home_start,
        bench=home_bench
    )
    away_obj = Team(
        away_id,
        season,
        starters=away_start,
        bench=away_bench
    )

    # Run simulation (one 48‑min play‑by‑play)
    events = simulate_game(home_obj, away_obj)

    # ---- Display Outputs ----
    st.header(f"{home_team} vs. {away_team} — Season {season}")
    st.subheader("Play‑by‑Play")
    for ev in events:
        st.write(ev)

# ---- Run Button ----
if st.button("Run Simulation"):
    run_sim()
