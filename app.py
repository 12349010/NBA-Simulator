############################################
# app.py  –  Streamlit GUI  (Engine v0.6.2) #
############################################
import streamlit as st, numpy as np, pandas as pd
from datetime import date
from nba_sim import calibration as calib, weights as W
from nba_sim.rosters_live import get_team_list, get_roster
from nba_sim.utils.injury import get_status
from main import play_game

ENGINE_VERSION = "v0.6.2-dyn-fix"

st.set_page_config(page_title="NBA Game Sim", layout="wide")
st.title(f"🔮 48‑Min NBA Simulator | {ENGINE_VERSION}")

all_teams = get_team_list()

# ---------- sidebar: calibration ----------
with st.sidebar:
    st.header("🛠 Calibration")
    cal_mode = st.checkbox("Enable calibrator")
    if cal_mode:
        st.caption("Enter actual scores below the main form.")

# ---------- main form ----------
with st.form("sim_form"):
    col1, col2 = st.columns(2)

    # HOME
    with col1:
        home_team = st.selectbox("Home team", all_teams, index=all_teams.index("Golden State Warriors"))
        h_roster  = get_roster(home_team)
        home_start = st.text_area("Home starters", "\n".join(h_roster["starters"]), height=120)
        home_bench = st.text_area("Home bench",    "\n".join(h_roster["bench"]),    height=120)
        home_coach = st.text_input("Home coach", "")

    # AWAY
    with col2:
        away_team = st.selectbox("Away team", all_teams, index=all_teams.index("Boston Celtics"))
        a_roster  = get_roster(away_team)
        away_start = st.text_area("Away starters", "\n".join(a_roster["starters"]), height=120)
        away_bench = st.text_area("Away bench",    "\n".join(a_roster["bench"]),    height=120)
        away_coach = st.text_input("Away coach", "")

    game_date = st.date_input("Game date", value=date.today())
    runs      = st.slider("Number of simulations", 1, 500, 100)

    if cal_mode:
        colh, cola = st.columns(2)
        actual_home = colh.number_input(f"Actual {home_team} score", value=0)
        actual_away = cola.number_input(f"Actual {away_team} score", value=0)
        cal_trials  = st.slider("Calibration trials", 5, 50, 25)

    submitted = st.form_submit_button("▶️  Simulate")   # <-- inside form ✅

# ---------- execution ----------
if submitted:
    cfg = {
        "game_date": str(game_date),
        "home_team": home_team, "away_team": away_team,
        "home_starters": [p.strip() for p in home_start.splitlines() if p.strip()],
        "away_starters": [p.strip() for p in away_start.splitlines() if p.strip()],
        "home_backups":  [p.strip() for p in home_bench.splitlines() if p.strip()],
        "away_backups":  [p.strip() for p in away_bench.splitlines() if p.strip()],
        "home_coach": home_coach or "—",
        "away_coach": away_coach or "—"
    }

    # injuries
    with st.sidebar.expander("Injury report"):
        for pl in cfg["home_starters"] + cfg["away_starters"]:
            st.write(f"{pl}: **{get_status(pl)}**")

    # calibration
    if cal_mode and (actual_home or actual_away):
        with st.spinner("Calibrating…"):
            W.save(W.DEFAULT)
            new_w, best_err = calib.calibrate(cfg, actual_home, actual_away, cal_trials)
        st.sidebar.success(f"MAE ≈ {best_err:.2f}")
        st.sidebar.json(new_w)

    # simulations
    bar = st.progress(0.0)
    res_h, res_a, per_player = [], [], {}
    for i in range(runs):
        out = play_game(cfg)
        res_h.append(out["Final Score"][home_team])
        res_a.append(out["Final Score"][away_team])
        for pl, pts in out["Box"].items():
            per_player.setdefault(pl, []).append(pts)
        bar.progress((i + 1)/runs)

    st.subheader("Average Final Score")
    st.markdown(f"**{home_team}: {np.mean(res_h):.1f} | {away_team}: {np.mean(res_a):.1f}**")

    st.subheader("Win Probability")
    wp = sum(h>a for h,a in zip(res_h, res_a)) / runs
    st.markdown(f"- **{home_team}: {wp:.1%}**  - **{away_team}: {1-wp:.1%}**")

    st.subheader("Score‑Diff Histogram (Home − Away)")
    st.bar_chart(pd.Series(np.array(res_h) - np.array(res_a)).value_counts().sort_index())

    st.subheader("Top Performers (median PTS)")
    tops = sorted([(p, np.median(v)) for p,v in per_player.items()],
                  key=lambda x: x[1], reverse=True)[:5]
    st.table(pd.DataFrame(tops, columns=["Player","Median PTS"]))

    st.expander("Sample single‑game JSON").json(play_game(cfg))
