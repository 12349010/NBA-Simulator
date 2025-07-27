# app.py
import streamlit as st
import pandas as pd
from nba_sim.calibration import play_game  # Adjust import if play_game moved
from nba_sim.data_csv import get_team_list, get_team_schedule, get_roster

# Page configuration
st.set_page_config(page_title="NBA Simulator", layout="wide")

# Title
st.title("NBA Game Simulator")

# Sidebar - Team and Season Selection
st.sidebar.header("Select Teams & Season")

# Get list of teams
teams_df = get_team_list()
team_names = teams_df['team_name'].tolist()

# Home team selection
home_team = st.sidebar.selectbox("Home Team", team_names, key='home_team')
# Seasons available for home
home_id = teams_df[teams_df['team_name'] == home_team]['team_id'].iloc[0]
home_schedule = get_team_schedule(home_team, None) if False else get_team_schedule(home_team, 0)
# Actually fetch unique seasons from full schedule
home_schedule_all = get_team_schedule(home_team, season=None)
home_seasons = sorted(home_schedule_all['season'].unique().tolist()) if 'season' in home_schedule_all.columns else []
season = st.sidebar.selectbox("Season", home_seasons, key='season')

# Away team selection
away_team = st.sidebar.selectbox("Away Team", [t for t in team_names if t != home_team], key='away_team')

# Roster selection for home and away
st.sidebar.header("Customize Rosters")
# Fetch rosters
home_roster_df = get_roster(home_team, season)
home_players = home_roster_df['player_name'].tolist()
away_roster_df = get_roster(away_team, season)
away_players = away_roster_df['player_name'].tolist()

# Default starters and bench
default_home_starters = home_players[:5]
default_home_bench = home_players[5:]
default_away_starters = away_players[:5]
default_away_bench = away_players[5:]

home_starters = st.sidebar.multiselect("Home Starters", home_players, default=default_home_starters)
home_bench = st.sidebar.multiselect("Home Bench", [p for p in home_players if p not in home_starters], default=default_home_bench)
away_starters = st.sidebar.multiselect("Away Starters", away_players, default=default_away_starters)
away_bench = st.sidebar.multiselect("Away Bench", [p for p in away_players if p not in away_starters], default=default_away_bench)

# Simulation control
if st.sidebar.button("Simulate Game"):
    # Prepare configuration
    config = {
        'home_team': home_team,
        'away_team': away_team,
        'season': season,
        'home_roster': home_starters + home_bench,
        'away_roster': away_starters + away_bench
    }
    # Run simulation
    results = play_game(config)
    box = results['box_score']
    pbp = results['pbp']

    # Layout - Two Columns: Scoreboard and Play-by-Play
    col1, col2 = st.columns(2)

    # Scoreboard & Box Score
    with col1:
        st.subheader("Box Score")
        st.dataframe(box)

    # Play-by-Play Log
    with col2:
        st.subheader("Play-by-Play")
        st.dataframe(pbp)

    # Optionally show raw data
    st.write("---")
    st.write("Detailed Results:")
    st.write(results)
