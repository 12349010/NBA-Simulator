############################################
# app.py  –  Streamlit GUI  (Engine v0.2)  #
############################################
import streamlit as st
import numpy as np
import pandas as pd
from datetime import date
from main import play_game            # ← uses the full engine in nba_sim

ENGINE_VERSION = "v0.2-core-package"

# ---------- Page setup ----------
st.set_page_config(page_title="NBA Game Sim", layout="wide")
st.title(f"🔮 48-Minute NBA Game Simulator | {ENGINE_VERSION}")

# ---------- Input form ----------
with st.form("sim_form", clear_on_submit=False):
    col1, col2 = st.columns(2)

    # HOME side
    with col1:
        home_team = st.text_input("Home team", "Golden State Warriors")
        home_start = st.text_area(
            "Home starters (one per line)",
            "Stephen Curry\nKlay Thompson\nAndrew Wiggins\nDraymond Green\nKevon Looney"
        )
        home_back = st.text_area("Home backups (one per line)", "")
        home_coach = st.text_input("Home coach", "Steve Kerr")

    # AWAY side
    with col2:
        away_team = st.text_input("Away team", "Boston Celtics")
        away_start = st.text_area(
            "Away starters (one per line)",
            "Jrue Holiday\nDerrick White\nJaylen Brown\nJayson Tatum\nKristaps Porzingis"
        )
        away_back = st.text_area("Away backups (one per line)", "")
        away_coach = st.text_input("Away coach", "Joe Mazzulla")

    game_date = st.date_input("Game date", value=date.today())
    runs = st.slider("Number of simulations", 1, 500, 50)

    submitted = st.form_submit_button("▶️  Simulate")

# ---------- Run simulations ----------
if submitted:
    st.info("Running simulations …")

    # clean input lists
    home_players = [p.strip() for p in home_start.strip().splitlines() if p.strip()]
    away_players = [p.strip() for p in away_start.strip().splitlines() if p.strip()]
    home_bench   = [p.strip() for p in home_back.strip().splitlines() if p.strip()]
    away_bench   = [p.strip() for p in away_back.strip().splitlines() if p.strip()]

    base_cfg = {
        "game_date": str(game_date),
        "home_team": home_team, "away_team": away_team,
        "home_starters": home_players, "away_starters": away_players,
        "home_backups": home_bench, "away_backups": away_bench,
        "home_coach": home_coach, "away_coach": away_coach
    }

    progress_bar = st.progress(0.0)
    results_home, results_away = [], []

    for i in range(runs):
        score = play_game(base_cfg)
        results_home.append(score[home_team])
        results_away.append(score[away_team])
        progress_bar.progress((i + 1) / runs)

    # ---------- Aggregate outputs ----------
    mean_home, mean_away = np.mean(results_home), np.mean(results_away)
    wins_home = sum(h > a for h, a in zip(results_home, results_away))
    win_prob_home = wins_home / runs
    win_prob_away = 1 - win_prob_home

    st.header("🏁 Average Final Score")
    st.markdown(f"**{home_team}: {mean_home:.1f} | {away_team}: {mean_away:.1f}**")

    st.subheader("📊 Win Probability")
    st.markdown(
        f"- **{home_team}: {win_prob_home:.1%}**\n"
        f"- **{away_team}: {win_prob_away:.1%}**"
    )

    # ---------- Histogram of score differential ----------
    st.subheader("📈 Score-Differential Distribution (Home − Away)")
    diffs = np.array(results_home) - np.array(results_away)
    hist_df = pd.DataFrame(diffs, columns=["Score Diff"])
    st.bar_chart(hist_df["Score Diff"].value_counts().sort_index())

    # ---------- Sample single-game box score ----------
    st.subheader("📝 Sample Single-Game Box Score")
    st.json(play_game(base_cfg))
