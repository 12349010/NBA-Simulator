############################################
# app.py  –  Streamlit GUI  (Engine v0.5)  #
############################################
import streamlit as st, numpy as np, pandas as pd
from datetime import date
from nba_sim import calibration as calib
from nba_sim import weights as W
from nba_sim.utils.injury import get_status
from main import play_game

ENGINE_VERSION = "v0.5-injury"

st.set_page_config(page_title="NBA Game Sim", layout="wide")
st.title(f"🔮 48‑Min NBA Simulator | {ENGINE_VERSION}")

# ---------- sidebar: calibration ----------
with st.sidebar:
    st.header("🛠 Calibration")
    cal_mode = st.checkbox("Enable calibrator")
    if cal_mode:
        st.caption("Enter actual scores in main form")

# ---------- main form ----------
with st.form("sim_form", clear_on_submit=False):
    col1, col2 = st.columns(2)
    with col1:
        home_team = st.text_input("Home team", "Golden State Warriors")
        home_start = st.text_area("Home starters", "Stephen Curry\nKlay Thompson\nAndrew Wiggins\nDraymond Green\nKevon Looney")
        home_back  = st.text_area("Home backups", "")
        home_coach = st.text_input("Home coach", "Steve Kerr")
    with col2:
        away_team = st.text_input("Away team", "Boston Celtics")
        away_start = st.text_area("Away starters", "Jrue Holiday\nDerrick White\nJaylen Brown\nJayson Tatum\nKristaps Porzingis")
        away_back  = st.text_area("Away backups", "")
        away_coach = st.text_input("Away coach", "Joe Mazzulla")

    game_date = st.date_input("Game date", value=date.today())
    runs = st.slider("Number of simulations", 1, 500, 100)

    if cal_mode:
        colh, cola = st.columns(2)
        actual_home = colh.number_input(f"Actual {home_team} score", value=0, step=1)
        actual_away = cola.number_input(f"Actual {away_team} score", value=0, step=1)
        cal_trials  = st.slider("Calibration trials", 5, 50, 25)

    submitted = st.form_submit_button("▶️ Simulate")

# ---------- run ----------
if submitted:
    starters_h = [p.strip() for p in home_start.strip().splitlines() if p.strip()]
    starters_a = [p.strip() for p in away_start.strip().splitlines() if p.strip()]
    cfg_base = {
        "game_date": str(game_date),
        "home_team": home_team, "away_team": away_team,
        "home_starters": starters_h, "away_starters": starters_a,
        "home_backups":  [p.strip() for p in home_back.strip().splitlines() if p.strip()],
        "away_backups":  [p.strip() for p in away_back.strip().splitlines() if p.strip()],
        "home_coach": home_coach, "away_coach": away_coach
    }

    # injury sidebar read‑out
    with st.sidebar.expander("Injury report", expanded=False):
        for pl in starters_h + starters_a:
            st.write(f"{pl}: **{get_status(pl)}**")

    # calibration
    if cal_mode and (actual_home > 0 or actual_away > 0):
        with st.spinner("Calibrating…"):
            W.save(W.DEFAULT)                   # reset to defaults first
            new_w, best_err = calib.calibrate(cfg_base, actual_home, actual_away, cal_trials)
        st.sidebar.success(f"MAE ≈ {best_err:.2f}")
        st.sidebar.json(new_w, expanded=False)

    # simulations
    prog = st.progress(0.0)
    res_home, res_away, per_player = [], [], {}
    for i in range(runs):
        out = play_game(cfg_base)
        res_home.append(out["Final Score"][home_team])
        res_away.append(out["Final Score"][away_team])
        for pl, pts in out["Box"].items():
            per_player.setdefault(pl, []).append(pts)
        prog.progress((i + 1) / runs)

    st.subheader("Average Final Score")
    st.markdown(f"**{home_team}: {np.mean(res_home):.1f} | {away_team}: {np.mean(res_away):.1f}**")

    wp_home = sum(h > a for h, a in zip(res_home, res_away)) / runs
    st.subheader("Win Probability")
    st.markdown(f"- **{home_team}: {wp_home:.1%}**  |  **{away_team}: {1-wp_home:.1%}**")

    st.subheader("Score‑Diff Histogram (Home − Away)")
    st.bar_chart(pd.Series(np.array(res_home) - np.array(res_away)).value_counts().sort_index())

    st.subheader("Top Performers (median PTS)")
    tops = sorted([(pl, np.median(pts)) for pl, pts in per_player.items()],
                  key=lambda x: x[1], reverse=True)[:5]
    st.table(pd.DataFrame(tops, columns=["Player", "Median PTS"]))

    st.expander("Sample single‑game JSON").json(play_game(cfg_base))
