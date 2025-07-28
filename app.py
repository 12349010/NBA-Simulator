# app.py

import streamlit as st
import pandas as pd

from nba_sim.data_csv import get_team_list, get_roster
from nba_sim.possession_engine import simulate_game
from nba_sim.team_model import Team

st.set_page_config(page_title="NBA Game Simulator")
st.title("🏀 NBA Game Simulator")

# — Sidebar: Team & Season Selection —
st.sidebar.header("Select Teams & Season")
teams_df = get_team_list()
team_names = teams_df["team_name"].tolist()

home_team = st.sidebar.selectbox("Home Team", team_names)
away_team = st.sidebar.selectbox(
    "Away Team", 
    [t for t in team_names if t != home_team]
)
season = st.sidebar.number_input(
    "Season (e.g. 1996)", min_value=1946, max_value=2025, value=2021, step=1
)

st.sidebar.markdown("---")
st.sidebar.header("Select Rosters (future use)")
# we load full roster now, even though Team doesn't yet accept custom lineups
home_roster = get_roster(home_team, season)
away_roster = get_roster(away_team, season)
player_names_home = home_roster["display_first_last"].tolist()
player_names_away = away_roster["display_first_last"].tolist()

# just show selectors for later wiring
home_start = st.sidebar.multiselect("Home Starters (5)", player_names_home, default=player_names_home[:5])
home_bench = st.sidebar.multiselect("Home Bench", player_names_home, default=player_names_home[5:12])

away_start = st.sidebar.multiselect("Away Starters (5)", player_names_away, default=player_names_away[:5])
away_bench = st.sidebar.multiselect("Away Bench", player_names_away, default=player_names_away[5:12])

st.sidebar.markdown("*(Roster injection coming soon)*")


def run_sim():
    # look up numeric IDs
    home_id = teams_df.loc[teams_df.team_name == home_team, "team_id"].iloc[0]
    away_id = teams_df.loc[teams_df.team_name == away_team, "team_id"].iloc[0]

    # instantiate Team objects (just id + season for now)
    home_obj = Team(home_id, season)
    away_obj = Team(away_id, season)

    # run the simulation
    events = simulate_game(home_obj, away_obj)

    # display header
    st.write(f"## Simulation: {home_team} vs. {away_team} ({season})")

    live = st.empty()
    score_display = st.empty()
    home_pts = away_pts = 0

    # render play-by-play & live score
    for ev in events:
        home_pts = ev.get("home_pts", home_pts)
        away_pts = ev.get("away_pts", away_pts)
        score_display.markdown(
            f"**Score: {home_team} {home_pts} – {away_team} {away_pts}**"
        )
        live.write(f"{ev.get('time','')} — {ev.get('desc','')}")
        # st.sleep(0.1)  # uncomment to throttle pacing

    st.success("🏁 End of Simulation")


if st.button("Run Simulation"):
    run_sim()
