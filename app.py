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
# Display home team logo
home_abbr = teams_df.loc[teams_df['team_name']==home_team, 'team_abbreviation'].iloc[0]
logo_url = f"https://i.cdn.turner.com/nba/nba/.element/img/4.0/global/logos/512x512/bg.white/svg/{home_abbr}.svg"
st.sidebar.image(logo_url, width=100)

# Seasons available for home team (dynamic)
schedule_all = get_team_schedule(home_team)
home_seasons = sorted(schedule_all['season'].unique().tolist()) if 'season' in schedule_all.columns else []
season = st.sidebar.selectbox("Season", home_seasons, key='season')

# Away team selection
away_team = st.sidebar.selectbox("Away Team", [t for t in team_names if t != home_team], key='away_team')
# Display away team logo
away_abbr = teams_df.loc[teams_df['team_name']==away_team, 'team_abbreviation'].iloc[0]
st.sidebar.image(f"https://i.cdn.turner.com/nba/nba/.element/img/4.0/global/logos/512x512/bg.white/svg/{away_abbr}.svg", width=100)
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
# Speed control for live simulation (1x default)
speed = st.sidebar.slider("Simulation Speed (seconds per play)", min_value=0.1, max_value=2.0, value=1.0, step=0.1)
# Run to end toggle
run_to_end = st.sidebar.checkbox("Run to End", value=False)

if st.sidebar.button("Simulate Game"):("Simulate Game"):
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
