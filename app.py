############################################
# app.py – one-file NBA game simulator GUI #
############################################
import streamlit as st, requests, random, time, math
import pandas as pd, numpy as np
from bs4 import BeautifulSoup

# ---------- tiny helpers ----------
USER_AGENT = {"User-Agent": "nba-sim/0.1 (streamlit)"}

@st.cache_data(ttl=24*3600, show_spinner=False)
def fetch_table(url, selector, numeric_cols=()):
    html = requests.get(url, headers=USER_AGENT, timeout=30).text
    soup  = BeautifulSoup(html, "lxml")
    table = soup.select_one(selector)
    df    = pd.read_html(str(table))[0]
    df = df.loc[:,~df.columns.str.contains("Unnamed")]
    for c in numeric_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df

def slug(full_name):
    parts = full_name.lower().replace(".","").split()
    return parts[-1][:5] + parts[0][:2] + "01"

@st.cache_data(ttl=24*3600, show_spinner=False)
def get_latest_season_row(player):
    try:
        df = fetch_table(
            f"https://www.basketball-reference.com/players/{player[0].lower()}/{slug(player)}.html",
            "#per_game",
            numeric_cols=("G","PTS","AST","TRB","FG%","3P%","FT%")
        )
        df = df[df["Season"].str.contains("-")]
        return df.iloc[-1]
    except Exception:
        # fallback to league-average line
        return pd.Series({"PTS":12,"AST":3,"TRB":4,"FG%":.46,"3P%":.35,"FT%":.76})

def age_factor(age):
    peak = 28
    return max(.65, 1 - 0.035*max(0, age-peak))

def sim_player_line(row, age, minutes):
    mult = age_factor(age) * (1 - 0.005*max(0, minutes-30))
    pts = np.random.poisson(row["PTS"]*mult*minutes/36)
    ast = np.random.poisson(row["AST"]*mult*minutes/36)
    reb = np.random.poisson(row["TRB"]*mult*minutes/36)
    return pts, ast, reb

# ---------- Streamlit UI ----------
st.set_page_config("NBA Game Sim", layout="wide")
st.title("🔮 48-Minute NBA Game Simulator")

with st.form("inputs"):
    col1, col2 = st.columns(2)
    with col1:
        home_team  = st.text_input("Home team",  "Golden State Warriors")
        home_start = st.text_area("Home starters (one per line)",
            "Stephen Curry\nKlay Thompson\nAndrew Wiggins\nDraymond Green\nKevon Looney")
        home_coach = st.text_input("Home coach", "Steve Kerr")
    with col2:
        away_team  = st.text_input("Away team",  "Boston Celtics")
        away_start = st.text_area("Away starters (one per line)",
            "Jrue Holiday\nDerrick White\nJaylen Brown\nJayson Tatum\nKristaps Porzingis")
        away_coach = st.text_input("Away coach", "Joe Mazzulla")
    game_date = st.date_input("Game date")
    runs = st.slider("Number of simulations", 1, 500, 50)
    submitted = st.form_submit_button("▶️  Simulate")

if submitted:
    progress = st.progress(0)
    results = {home_team:[], away_team:[]}

    home_players = home_start.strip().splitlines()
    away_players = away_start.strip().splitlines()
    all_players  = home_players + away_players

    # quick ages: assume rookie season age 20, add seasons played
    ages = {}
    for p in all_players:
        row = get_latest_season_row(p)
        seasons = len(fetch_table(
            f"https://www.basketball-reference.com/players/{p[0].lower()}/{slug(p)}.html",
            "#per_game"
        ))
        ages[p] = 20 + seasons

    for i in range(runs):
        score_home = score_away = 0
        for p in home_players:
            pts,_,_ = sim_player_line(get_latest_season_row(p), ages[p], 34)
            score_home += pts
        for p in away_players:
            pts,_,_ = sim_player_line(get_latest_season_row(p), ages[p], 34)
            score_away += pts
        results[home_team].append(score_home)
        results[away_team].append(score_away)
        progress.progress((i+1)/runs)

    st.subheader("🏁 Results")
    home_m = np.mean(results[home_team]); away_m = np.mean(results[away_team])
    st.write(f"**{home_team} avg:** {home_m:.1f}  |  **{away_team} avg:** {away_m:.1f}")

    wins_home = sum(1 for h,a in zip(results[home_team], results[away_team]) if h>a)
    st.write(f"**Win probability** – {home_team}: {wins_home/runs:.1%} | {away_team}: {(runs-wins_home)/runs:.1%}")

    st.line_chart(pd.DataFrame({
        home_team: results[home_team],
        away_team: results[away_team]
    }))
