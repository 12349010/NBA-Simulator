import streamlit as st
from nba_sim.data_csv import get_team_list, get_team_schedule, get_roster
from nba_sim.possession_engine import simulate_game

# Page configuration
st.set_page_config(page_title="NBA Game Simulator", layout="wide")

# Title
st.title("NBA Game Simulator")

# Sidebar: Team & Season Selection
st.sidebar.header("Select Teams & Season")
teams_df = get_team_list()
team_names = teams_df['team_name'].tolist()

# Home team
home_team_name = st.sidebar.selectbox("Home Team", team_names)
home_team_id = teams_df.loc[teams_df['team_name'] == home_team_name, 'team_id'].iloc[0]

# Home season
home_seasons = get_team_schedule(home_team_id, season=None)['season_id'].unique().tolist()
home_seasons = sorted(set(int(s) for s in home_seasons), reverse=True)
home_season = st.sidebar.selectbox("Home Season", home_seasons)

# Home roster selection
home_roster_df = get_roster(home_team_id, home_season)
home_player_names = home_roster_df['display_first_last'].tolist()
home_default_start = home_player_names[:5]
starting_five = st.sidebar.multiselect("Starting Five", home_player_names, default=home_default_start)
bench_players = [p for p in home_player_names if p not in starting_five]
bench_selection = st.sidebar.multiselect("Bench Players", bench_players, default=bench_players[:5])

# Opponent selection
st.sidebar.markdown("---")
st.sidebar.header("Select Opponent & Season")
away_team_name = st.sidebar.selectbox("Away Team", [t for t in team_names if t != home_team_name])
away_team_id = teams_df.loc[teams_df['team_name'] == away_team_name, 'team_id'].iloc[0]

away_seasons = get_team_schedule(away_team_id, season=None)['season_id'].unique().tolist()
away_seasons = sorted(set(int(s) for s in away_seasons), reverse=True)
away_season = st.sidebar.selectbox("Away Season", away_seasons)

away_roster_df = get_roster(away_team_id, away_season)
away_player_names = away_roster_df['display_first_last'].tolist()
away_default_start = away_player_names[:5]
away_starting_five = st.sidebar.multiselect("Away Starting Five", away_player_names, default=away_default_start)
away_bench = [p for p in away_player_names if p not in away_starting_five]
away_bench_selection = st.sidebar.multiselect("Away Bench Players", away_bench, default=away_bench[:5])

# Display team logos and headers
col1, col2 = st.columns(2)
with col1:
    st.image(f"https://cdn.nba.com/logos/nba/{home_team_id}/primary/L/logo.svg", width=150)
    st.header(home_team_name)
with col2:
    st.image(f"https://cdn.nba.com/logos/nba/{away_team_id}/primary/L/logo.svg", width=150)
    st.header(away_team_name)

# Simulation controls
st.sidebar.markdown("---")
st.sidebar.header("Simulation Controls")
speed = st.sidebar.slider("Simulation Speed", min_value=0.1, max_value=5.0, value=1.0, step=0.1)
simulate_to_end = st.sidebar.checkbox("Simulate to End", value=True)

# Run simulation button
if st.sidebar.button("Run Simulation"):
    # Placeholder: call simulate_game (implementation TBD)
    sim_result = simulate_game(
        home_team_id,
        away_team_id,
        home_season,
        starting_five,
        bench_selection,
        away_starting_five,
        away_bench_selection,
        speed,
        simulate_to_end
    )
    st.success("Simulation complete! (Results processing coming soon)")
