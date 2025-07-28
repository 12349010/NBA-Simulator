# app.py
import streamlit as st
import pandas as pd
import time

from nba_sim.data_csv import get_team_list, get_team_schedule, get_roster
from nba_sim.possession_engine import simulate_game
from nba_sim.utils.injury import get_status

st.set_page_config(page_title="NBA Game Simulator", layout="wide")

# --- Sidebar: Configuration ---
st.sidebar.header("Select Teams & Season")
teams_df = get_team_list()
team_map = teams_df.set_index('team_name')['team_id'].to_dict()
team_names = list(team_map.keys())

home_team_name = st.sidebar.selectbox("Home Team", team_names, index=0)
away_team_name = st.sidebar.selectbox("Away Team", team_names, index=1)
season = st.sidebar.number_input("Season (year)", min_value=1946, max_value=2025, value=2021, step=1)

speed = st.sidebar.slider("Simulation Speed (events/sec)", min_value=0.5, max_value=10.0, value=1.0, step=0.5)
sim_to_end = st.sidebar.checkbox("Simulate to End Instantly", value=False)

# --- Load rosters once team & season chosen ---
home_team_id = team_map[home_team_name]
away_team_id = team_map[away_team_name]

with st.sidebar.expander("Home Roster Selection"):
    home_roster_df = get_roster(home_team_id, season)
    home_names = home_roster_df['display_first_last'].tolist()
    home_start = st.multiselect("Home Starting 5", home_names, default=home_names[:5])
    home_bench = st.multiselect("Home Bench", [n for n in home_names if n not in home_start])

with st.sidebar.expander("Away Roster Selection"):
    away_roster_df = get_roster(away_team_id, season)
    away_names = away_roster_df['display_first_last'].tolist()
    away_start = st.multiselect("Away Starting 5", away_names, default=away_names[:5])
    away_bench = st.multiselect("Away Bench", [n for n in away_names if n not in away_start])

# --- Main UI ---
st.title("NBA Game Simulator")
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader(f"Home: {home_team_name}")
    home_logo = f"https://a.espncdn.com/combiner/i?img=/i/teamlogos/nba/500/{teams_df.set_index('team_id').loc[home_team_id,'team_abbreviation']}.png"
    st.image(home_logo, width=150)
with col2:
    st.subheader(f"Away: {away_team_name}")
    away_logo = f"https://a.espncdn.com/combiner/i?img=/i/teamlogos/nba/500/{teams_df.set_index('team_id').loc[away_team_id,'team_abbreviation']}.png"
    st.image(away_logo, width=150)

# Placeholders for live updates
scoreboard_ph = st.empty()
boxscore_ph = st.empty()
log_ph = st.empty()

# Run Simulation
def run_sim():
    # call your simulate_game engine
    events = simulate_game(
        home_team_id, away_team_id,
        season,
        home_start + home_bench,
        away_start + away_bench
    )
    home_score = away_score = 0
    box = pd.DataFrame(columns=["Player","PTS","REB","AST","STL","BLK"])

    for ev in events:
        # update scores if present
        if 'home_score' in ev and 'away_score' in ev:
            home_score, away_score = ev['home_score'], ev['away_score']
        # update scoreboard
        scoreboard_ph.markdown(f"**{home_team_name} {home_score} - {away_score} {away_team_name}**")
        # update boxscore if provided
        if 'boxscore' in ev:
            box = pd.DataFrame(ev['boxscore'])
            boxscore_ph.dataframe(box)
        # log play-by-play
        timestamp = ev.get('time', '')
        description = ev.get('description', '')
        log_ph.write(f"{timestamp}  {description}")
        # control speed
        if not sim_to_end:
            time.sleep(1.0 / speed)

# Button
if st.button("Run Simulation"):
    run_sim()
