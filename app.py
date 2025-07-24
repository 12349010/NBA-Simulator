# app.py – NBA Simulator (Engine v0.9.1 – polished UI)
import streamlit as st, numpy as np, pandas as pd, subprocess, shlex
from datetime import date
from nba_sim.data_sqlite import roster as get_roster
from nba_sim.data_sqlite import get_team_list, team_schedule as get_team_schedule
from nba_sim.data_sqlite import played_yesterday
from nba_sim.data_sqlite import play_by_play
from nba_sim.utils.injury import get_status
from nba_sim import calibration as calib, weights as W
from main import play_game

ENGINE_VERSION = "v0.9.1"

st.set_page_config(page_title="NBA Game Sim", layout="wide")
st.markdown(f"## 🏀 48‑Minute NBA Simulator &nbsp;|&nbsp; *{ENGINE_VERSION}*")

TEAM_OPTS = ["— Select —"] + get_team_list()
SIM_RUNS  = [1, 10, 25, 50, 100]

# ---------- Session ----------
for k in ["home_team","away_team","home_starters","away_starters","home_bench","away_bench"]:
    st.session_state.setdefault(k,"")

def _fill(side:str):
    tm = st.session_state[f"{side}_team"]
    if tm != "— Select —":
        r = get_roster(tm)
        st.session_state[f"{side}_starters"] = "\n".join(r["starters"])
        st.session_state[f"{side}_bench"] = "\n".join(r["bench"])
    else:
        st.session_state[f"{side}_starters"] = st.session_state[f"{side}_bench"] = ""

# ---------- Team inputs ----------
c1,c2 = st.columns(2)
with c1:
    st.selectbox("Home team", TEAM_OPTS, key="home_team", on_change=_fill, args=("home",))
    st.text_area("Starters", key="home_starters", height=120)
    st.text_area("Bench",    key="home_bench",    height=120)
with c2:
    st.selectbox("Away team", TEAM_OPTS, key="away_team", on_change=_fill, args=("away",))
    st.text_area("Starters", key="away_starters", height=120)
    st.text_area("Bench",    key="away_bench",    height=120)

# ---------- OPTIONS PANEL ----------
with st.expander("🎛️  Simulation Options", expanded=True):

    # -- basic options -----------------------
    sim_runs   = st.selectbox("Simulations to run",
                              options=[1, 10, 25, 50, 100], index=3)
    fatigue_on = st.checkbox("Apply travel‑fatigue (auto back‑to‑back)",
                             value=True)

    # -- advanced calibration ---------------
    with st.expander("Advanced settings · Calibrator", expanded=False):
        st.markdown(
            "📐 **Calibrator** lets the engine tune its internal weight matrix "
            "so that simulated final scores match a *real* past game as closely "
            "as possible.\n\n"
            "* **Auto** – uses Basketball‑Reference data for the chosen matchup & date*\n"
            "* **Manual** – you type the actual score\n"
            "* **No** – skip calibration entirely"
        )

        cal_mode = st.radio("Calibrate?", ["No", "Auto", "Manual"],
                            horizontal=True)

        if cal_mode == "Manual":
            act_home   = st.number_input("Actual home score", value=0)
            act_away   = st.number_input("Actual away score", value=0)
            cal_trials = st.slider("Calibration trials", 5, 50, 25)

game_date = st.date_input("Game date", value=date.today())

# ---------- Simulate ----------
if st.button("▶️  Simulate"):
    if "— Select —" in (st.session_state.home_team, st.session_state.away_team):
        st.error("Pick both teams first."); st.stop()

    cfg = {
        "game_date": str(game_date),
        "home_team": st.session_state.home_team,
        "away_team": st.session_state.away_team,
        "home_starters":[p for p in st.session_state.home_starters.splitlines() if p],
        "away_starters":[p for p in st.session_state.away_starters.splitlines() if p],
        "home_backups":[p for p in st.session_state.home_bench.splitlines() if p],
        "away_backups":[p for p in st.session_state.away_bench.splitlines() if p],
        "fatigue_on": fatigue_on,
    }

    # run sims
    res_h,res_a,boxes_h,boxes_a=[],[],[],[]
    bar = st.progress(0.0)
    for i in range(sim_runs):
        g = play_game(cfg, seed=i)
        res_h.append(g["Final Score"][cfg["home_team"]])
        res_a.append(g["Final Score"][cfg["away_team"]])
        boxes_h.append(pd.DataFrame(g["Box Scores"][cfg["home_team"]]))
        boxes_a.append(pd.DataFrame(g["Box Scores"][cfg["away_team"]]))
        bar.progress((i+1)/sim_runs)

    # optional calibration
    if 'enable_cal' in locals() and enable_cal and (act_home or act_away):
        W.save(W.DEFAULT)
        new_w,best_err = calib.calibrate(cfg, act_home, act_away, cal_trials)
        st.sidebar.success(f"Calibrator MAE ≈ {best_err:.2f}")
        st.sidebar.json(new_w,expanded=False)

    # ---------- Sidebar: injuries + fatigue + defense ----------
    with st.sidebar:
        st.subheader("Game context")
        for pl in cfg["home_starters"]+cfg["away_starters"]:
            st.write(f"{pl}: **{get_status(pl)}**")
        if g["Fatigue Flags"][cfg["home_team"]]:
            st.write(f"💤 {cfg['home_team']} on back‑to‑back")
        if g["Fatigue Flags"][cfg["away_team"]]:
            st.write(f"💤 {cfg['away_team']} on back‑to‑back")

    # ---------- Display ----------
    avg_h,avg_a = np.mean(res_h), np.mean(res_a)
    st.markdown(
        f"<h2 style='text-align:center;margin-top:0;'>"
        f"{cfg['home_team']} {avg_h:.0f} – {avg_a:.0f} {cfg['away_team']}"
        f"</h2>",
        unsafe_allow_html=True)

    def _as_int(df):
        out=df.copy(); nums=out.select_dtypes("number").columns
        out[nums]=out[nums].astype(int); return out

    ch,ca=st.columns(2)
    with ch:
        st.subheader(f"{cfg['home_team']} Box (avg)")
        st.dataframe(_as_int(pd.concat(boxes_h).groupby("Player").mean().round(0)),use_container_width=True)
    with ca:
        st.subheader(f"{cfg['away_team']} Box (avg)")
        st.dataframe(_as_int(pd.concat(boxes_a).groupby("Player").mean().round(0)),use_container_width=True)

# ---------- footer ----------
st.markdown(
    "<div style='text-align:center;color:gray;margin-top:2rem;font-size:0.8em;'>"
    f"Engine {ENGINE_VERSION} – Git { subprocess.check_output(shlex.split('git rev-parse --short HEAD')).decode().strip() }"
    "</div>",
    unsafe_allow_html=True
)
