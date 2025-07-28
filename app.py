import streamlit as st
import pandas as pd

from nba_sim.data_csv import get_team_list, get_roster
from nba_sim.team_model import Team
from nba_sim.possession_engine import simulate_game

st.title("NBA Simulator")

# --- Sidebar: pick teams & season ---
teams_df = get_team_list()
team_names = teams_df['team_name'].tolist()

season = st.sidebar.number_input("Season (year)", min_value=1947, max_value=2100, value=2023)
home_team = st.sidebar.selectbox("Home team", team_names)
away_team = st.sidebar.selectbox("Away team", team_names, index=1)

# Fetch the rosters for the selected season
home_id = teams_df.loc[teams_df.team_name == home_team, "team_id"].iloc[0]
away_id = teams_df.loc[teams_df.team_name == away_team, "team_id"].iloc[0]

home_roster_df = get_roster(home_id, season)
away_roster_df = get_roster(away_id, season)

home_names = home_roster_df['display_first_last'].tolist()
away_names = away_roster_df['display_first_last'].tolist()

# Pick your starters & bench
home_start = st.sidebar.multiselect("Home starters (5)", home_names, default=home_names[:5])
home_bench = st.sidebar.multiselect("Home bench", [n for n in home_names if n not in home_start])

away_start = st.sidebar.multiselect("Away starters (5)", away_names, default=away_names[:5])
away_bench = st.sidebar.multiselect("Away bench", [n for n in away_names if n not in away_start])

# Run simulation
def run_sim():
    home = Team(home_id, season, starters=home_start, bench=home_bench)
    away = Team(away_id, season, starters=away_start, bench=away_bench)
    events = simulate_game(home, away)

    st.subheader("Play-by-Play")
    for ev in events:
        st.write(ev)

if st.button("Run Simulation"):
    run_sim()
