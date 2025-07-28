# app.py
import streamlit as st
import pandas as pd
from typing import Optional

from nba_sim.data_csv import (
    get_team_list,
    get_team_schedule,
    get_roster,
    get_player_id,
)
from nba_sim.utils.injury import get_status
from nba_sim.possession_engine import simulate_game

st.set_page_config(page_title="NBA Game Simulator", layout="wide")
st.title("NBA Game Simulator")

# Sidebar: Team & Season Selection
st.sidebar.header("Select Teams & Season")
teams_df = get_team_list()
team_names = teams_df["team_name"].tolist()

home_team = st.sidebar.selectbox("Home Team", team_names)
away_team = st.sidebar.selectbox(
    "Away Team", [t for t in team_names if t != home_team]
)

seasons = sorted(pd.read_csv("data/game.csv")["season_id"].unique())
season = st.sidebar.selectbox("Season", seasons)

# Sidebar: Roster Pickers
st.sidebar.header("Customize Rosters")
home_roster_df = get_roster(home_team, season)
away_roster_df = get_roster(away_team, season)

home_names = home_roster_df["display_first_last"].tolist()
away_names = away_roster_df["display_first_last"].tolist()

home_start = st.sidebar.multiselect(
    "Home Starting Five", home_names, default=home_names[:5]
)
home_bench = st.sidebar.multiselect(
    "Home Bench", [n for n in home_names if n not in home_start], default=home_names[5:8]
)

away_start = st.sidebar.multiselect(
    "Away Starting Five", away_names, default=away_names[:5]
)
away_bench = st.sidebar.multiselect(
    "Away Bench", [n for n in away_names if n not in away_start], default=away_names[5:8]
)

# Main area placeholders
scoreboard = st.empty()
boxscore = st.empty()
play_by_play = st.empty()

def run_sim():
    # resolve to IDs
    home_id = teams_df.loc[teams_df.team_name == home_team, "team_id"].iloc[0]
    away_id = teams_df.loc[teams_df.team_name == away_team, "team_id"].iloc[0]

    # 🚧 NOTE: simulate_game now only takes two args, so we pass just those.
    events = simulate_game(home_id, away_id)

    # render scoreboard, boxscore, and play log
    for ev in events:
        # simple example: update live score
        scoreboard.markdown(f"**{ev['time']}** | {ev['description']}  ")
        # build a quick boxscore
        boxscore.table(pd.DataFrame(ev["boxscore"]))
        play_by_play.write(ev["description"])
        # you can add st.sleep(...) here for speed control

if st.button("Run Simulation"):
    run_sim()
