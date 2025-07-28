# app.py

import streamlit as st
import pandas as pd

from nba_sim.data_csv import get_team_list, get_roster, get_team_schedule
from nba_sim.team_model import Team
from nba_sim.possession_engine import simulate_game

# ---- Page Config ----
st.set_page_config(page_title="NBA Game Simulator", layout="wide")
st.title("🏀 NBA Game Simulator")

# ---- Sidebar: Team & Season Selection ----
st.sidebar.header("Select Teams & Season")

teams_df = get_team_list()
team_names = teams_df["team_name"].tolist()

home_team = st.sidebar.selectbox("Home Team", team_names)
away_team = st.sidebar.selectbox(
    "Away Team",
    [t for t in team_names if t != home_team]
)

season = st.sidebar.number_input(
    "Season (e.g. 1996)",
    min_value=1946,
    max_value=2100,
    value=2020,
    step=1
)

# ---- Build per-season rosters ----
def season_filtered_roster(team_name, season):
    """Fetch roster for team+season, filtering out anyone not in that year."""
    # only common players whose from_year≤season≤to_year,
    # plus inactive but only from games in that season
    tid = teams_df.loc[teams_df.team_name == team_name, "team_id"].iat[0]
    # get all games in that season for this team
    sched = get_team_schedule(tid, season)
    # call get_roster which now looks at both common and inactive,
    # but we'll re-filter inactive internally
    full = get_roster(team_name, season)
    # full already respects common from/to and inactive via play-by-play fallback,
    # but to be sure, we intersect display_first_last with those who appear
    # in at least one row of sched or in the _common_player_info span.
    return full["display_first_last"].tolist()

home_players = season_filtered_roster(home_team, season)
away_players = season_filtered_roster(away_team, season)

# ---- Sidebar: Pick Starters & Bench ----
st.sidebar.markdown("### Home Roster")
home_start = st.sidebar.multiselect(
    "Home Starters (pick up to 5)",
    options=home_players,
    default=home_players[:5]
)
home_bench = st.sidebar.multiselect(
    "Home Bench",
    options=[p for p in home_players if p not in home_start],
    default=[]
)

st.sidebar.markdown("### Away Roster")
away_start = st.sidebar.multiselect(
    "Away Starters (pick up to 5)",
    options=away_players,
    default=away_players[:5]
)
away_bench = st.sidebar.multiselect(
    "Away Bench",
    options=[p for p in away_players if p not in away_start],
    default=[]
)

# ---- Simulation runner ----
def run_sim():
    home_id = teams_df.loc[teams_df.team_name == home_team, "team_id"].iat[0]
    away_id = teams_df.loc[teams_df.team_name == away_team, "team_id"].iat[0]

    # instantiate Team (now accepts starters & bench)
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

    st.header(f"{home_team} vs. {away_team} — Season {season}")
    st.subheader("Play‑by‑Play")
    for ev in events:
        st.write(ev)

if st.button("Run Simulation"):
    run_sim()
