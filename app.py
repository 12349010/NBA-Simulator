import streamlit as st
import pandas as pd

from nba_sim.data_csv import get_team_list, get_roster
from nba_sim.main import play_game

# Page configuration for wide layout
st.set_page_config(layout="wide")
st.title("NBA Game Simulator")

# Load teams and build options dict
teams_df = get_team_list()
team_options = {row.team_name: row.team_id for row in teams_df.itertuples()}

# Sidebar: Team & Season Selection
st.sidebar.header("Select Teams & Season")
home_name = st.sidebar.selectbox("Home Team", list(team_options.keys()))
away_name = st.sidebar.selectbox(
    "Away Team", list(team_options.keys()),
    index=min(1, len(team_options)-1)
)
season = st.sidebar.selectbox(
    "Season",
    [str(y) for y in range(2025, 1999, -1)]
)

# Fetch team IDs and season as int
home_id = team_options[home_name]
away_id = team_options[away_name]
season_int = int(season)

# Load rosters
home_roster_df = get_roster(home_id, season_int)
away_roster_df = get_roster(away_id, season_int)

# Roster selectors default to first five players
home_players = st.sidebar.multiselect(
    "Home Starters", home_roster_df.display_first_last.tolist(),
    default=home_roster_df.display_first_last.tolist()[:5]
)
away_players = st.sidebar.multiselect(
    "Away Starters", away_roster_df.display_first_last.tolist(),
    default=away_roster_df.display_first_last.tolist()[:5]
)

# Simulation speed control
speed = st.sidebar.slider(
    "Simulation Speed (seconds per event)",
    min_value=0.1, max_value=2.0, value=1.0, step=0.1
)

# Simulate button
simulate = st.sidebar.button("Simulate Game")

# Main layout: side-by-side team columns
col1, col2 = st.columns(2)

with col1:
    # Home team logo and starters
    home_logo_url = f"https://cdn.nba.com/logos/nba/{home_id}/primary/L/logo.svg"
    st.image(home_logo_url, width=120)
    st.subheader(f"{home_name} Starters")
    for player in home_players:
        st.write(f"• {player}")

with col2:
    # Away team logo and starters
    away_logo_url = f"https://cdn.nba.com/logos/nba/{away_id}/primary/L/logo.svg"
    st.image(away_logo_url, width=120)
    st.subheader(f"{away_name} Starters")
    for player in away_players:
        st.write(f"• {player}")

# Run simulation and display results
if simulate:
    box_score_df, pbp_df = play_game(
        home_name, away_name, season_int,
        home_players, away_players, speed=speed
    )
    st.subheader("Final Box Score")
    st.dataframe(box_score_df)
    # TODO: integrate play-by-play display when available
