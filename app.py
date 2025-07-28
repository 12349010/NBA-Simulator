# app.py

import streamlit as st
import pandas as pd

from nba_sim.data_csv import get_team_list, get_common_roster
from nba_sim.team_model import Team
from nba_sim.possession_engine import simulate_game

# Page layout
st.set_page_config(page_title="NBA Game Simulator", layout="wide")
st.title("🏀 NBA Game Simulator")

# Sidebar controls
st.sidebar.header("Select Teams & Season")
teams_df = get_team_list()
team_names = teams_df.team_name.tolist()

home_team = st.sidebar.selectbox("Home Team", team_names)
away_team = st.sidebar.selectbox(
    "Away Team",
    [t for t in team_names if t != home_team]
)

season = st.sidebar.number_input(
    "Season (e.g. 2015)",
    min_value=1946,
    max_value=2100,
    value=2023,
    step=1
)

def season_filtered_roster(team_name: str, season: int):
    """
    Return just the common-roster names for that franchise in that season.
    Uses only from_year/to_year in common_player_info.csv.
    """
    tid = teams_df.loc[teams_df.team_name == team_name, "team_id"].iat[0]
    df = get_common_roster(tid, season)
    return df.display_first_last.tolist()

# Populate the per-season lists
home_players = season_filtered_roster(home_team, season)
away_players = season_filtered_roster(away_team, season)

# Pick starters & bench
st.sidebar.markdown("### Home Roster")
home_start = st.sidebar.multiselect(
    "Home Starters (up to 5)",
    options=home_players,
    default=home_players[:5],
    help="Only picks from this season's roster."
)
home_bench = st.sidebar.multiselect(
    "Home Bench",
    options=[p for p in home_players if p not in home_start],
    default=[],
    help="Pick your bench squad."
)

st.sidebar.markdown("### Away Roster")
away_start = st.sidebar.multiselect(
    "Away Starters (up to 5)",
    options=away_players,
    default=away_players[:5],
    help="Only picks from this season's roster."
)
away_bench = st.sidebar.multiselect(
    "Away Bench",
    options=[p for p in away_players if p not in away_start],
    default=[],
    help="Pick your bench squad."
)

# Simulation
def run_sim():
    home_id = teams_df.loc[teams_df.team_name == home_team, "team_id"].iat[0]
    away_id = teams_df.loc[teams_df.team_name == away_team, "team_id"].iat[0]

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

    events = simulate_game(home_obj, away_obj)

    st.header(f"{home_team} vs. {away_team} — {season} Season")
    st.subheader("Play‑by‑Play")
    for ev in events:
        st.write(ev)

if st.button("Run Simulation"):
    run_sim()
