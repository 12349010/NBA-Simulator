import streamlit as st
import pandas as pd
from typing import Optional

from nba_sim.main import play_game
from nba_sim.data_csv import get_team_list, get_team_schedule, get_roster
from nba_sim.utils.injury import get_status

# Page configuration
st.set_page_config(page_title="NBA Simulator", layout="wide")
st.title("NBA Game Simulator")

# Sidebar: Team & Season Selection
st.sidebar.header("Select Teams & Season")
teams_df = get_team_list()
team_names = teams_df['team_name'].tolist()

# Home team selection
home_team = st.sidebar.selectbox("Home Team", team_names)
home_abbr = teams_df.loc[teams_df['team_name'] == home_team, 'team_abbreviation'].iloc[0]
st.sidebar.image(f"https://i.cdn.turner.com/nba/nba/.element/img/4.0/global/logos/512x512/bg.white/svg/{home_abbr}.svg", width=80)

# Seasons available for home team
schedule_all = get_team_schedule(home_team, season=None)
home_seasons = sorted(schedule_all['season'].dropna().unique().tolist()) if 'season' in schedule_all.columns else []
season = st.sidebar.selectbox("Season", home_seasons)

# Away team selection
away_team = st.sidebar.selectbox("Away Team", [t for t in team_names if t != home_team])
away_abbr = teams_df.loc[teams_df['team_name'] == away_team, 'team_abbreviation'].iloc[0]
st.sidebar.image(f"https://i.cdn.turner.com/nba/nba/.element/img/4.0/global/logos/512x512/bg.white/svg/{away_abbr}.svg", width=80)

# Roster & Injuries
st.sidebar.header("Rosters & Injury Status")
home_roster_df = get_roster(home_team, season)
home_players = home_roster_df['player_name'].tolist()
away_roster_df = get_roster(away_team, season)
away_players = away_roster_df['player_name'].tolist()

st.sidebar.subheader("Home Injury Status")
for p in home_players:
    status = get_status(p)
    if status.lower() not in ['healthy', 'active']:
        st.sidebar.write(f"{p}: {status}")

st.sidebar.subheader("Away Injury Status")
for p in away_players:
    status = get_status(p)
    if status.lower() not in ['healthy', 'active']:
        st.sidebar.write(f"{p}: {status}")

# Roster customization
default_home_starters = home_players[:5]
default_home_bench = home_players[5:]
default_away_starters = away_players[:5]
default_away_bench = away_players[5:]

home_starters = st.sidebar.multiselect("Home Starters", home_players, default=default_home_starters)
home_bench = st.sidebar.multiselect("Home Bench", [p for p in home_players if p not in home_starters], default=default_home_bench)
away_starters = st.sidebar.multiselect("Away Starters", away_players, default=default_away_starters)
away_bench = st.sidebar.multiselect("Away Bench", [p for p in away_players if p not in away_starters], default=default_away_bench)

# Simulation controls
st.sidebar.header("Simulation Controls")
speed = st.sidebar.slider("Speed (secs per play)", 0.1, 2.0, 1.0, 0.1)
run_to_end = st.sidebar.checkbox("Run to End", value=False)

# Run simulation
if st.sidebar.button("Simulate Game"):
    config = {
        'home_team': home_team,
        'away_team': away_team,
        'season': season,
        'home_roster': home_starters + home_bench,
        'away_roster': away_starters + away_bench
    }
    results = play_game(config)
    box_df = results['box_score'].copy()
    pbp_df = results['pbp']

    # Handle missing PBP
    if pbp_df.empty:
        st.warning("No play-by-play data available; displaying box score only.")
        st.subheader("Box Score")
        st.dataframe(box_df)
        st.stop()

    # Live update placeholders
    score_ph = st.empty()
    box_ph = st.empty()
    pbp_ph = st.empty()

    play_texts = []
    for _, ev in pbp_df.iterrows():
        desc = ev.get('description', str(ev.to_dict()))
        play_texts.append(desc)

        # Update box score
        pts = ev.get('points', 0)
        pid = ev.get('player1_id')
        team_id = ev.get('team_id')
        home_id = teams_df.loc[teams_df['team_name'] == home_team, 'team_id'].iloc[0]
        label = 'home' if team_id == home_id else 'away'
        if pts and pid:
            mask = (box_df['team'] == label) & (box_df['player_id'] == pid)
            box_df.loc[mask, 'points'] += pts

        # Current score
        h_score = box_df[box_df['team']=='home']['points'].sum()
        a_score = box_df[box_df['team']=='away']['points'].sum()

        score_ph.markdown(f"**Score: Home {h_score} - {a_score} Away**")
        box_ph.dataframe(box_df)
        pbp_ph.write("\n".join(play_texts[-10:]))

        if not run_to_end:
            st.sleep(speed)

    st.markdown("---")
    st.subheader("Final Box Score")
    st.dataframe(box_df)
    st.subheader("Full Play-by-Play Log")
    st.dataframe(pbp_df)
