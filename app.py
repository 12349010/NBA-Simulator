# app.py (only the run_sim part shown)
def run_sim():
    # look up numeric IDs
    home_id = teams_df.loc[teams_df.team_name == home_team, "team_id"].iloc[0]
    away_id = teams_df.loc[teams_df.team_name == away_team, "team_id"].iloc[0]

    # instantiate your Team objects (just id + season for now)
    home_obj = Team(home_id, season)
    away_obj = Team(away_id, season)

    # TODO: once Team supports custom roster injection, wire home_start/home_bench here

    # run the sim
    events = simulate_game(home_obj, away_obj)

    # render the play‐by‐play & live score
    st.write(f"## Simulation: {home_team} vs. {away_team} ({season})")
    live = st.empty()
    score_display = st.empty()
    home_pts = away_pts = 0

    for ev in events:
        home_pts = ev.get("home_pts", home_pts)
        away_pts = ev.get("away_pts", away_pts)
        score_display.markdown(f"**Score: {home_team} {home_pts} – {away_team} {away_pts}**")
        live.write(f"{ev['time']} – {ev['desc']}")
        # st.sleep(0.2)  # if you want pacing

    st.success("🏁 End of Simulation")
