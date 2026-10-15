"""NBA analytics dashboard on FiveThirtyEight's Elo ratings.

Run:
    streamlit run app/streamlit_app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sports.analysis import (  # noqa: E402
    accuracy_by_decade,
    biggest_upsets,
    calibration_table,
    forecast_scores,
    home_advantage_by_decade,
    peak_teams,
    season_end_elo,
    season_standings,
)
from sports.data import games, load_team_games  # noqa: E402

st.set_page_config(page_title="NBA Analytics Dashboard", page_icon="🏀", layout="wide")


@st.cache_data
def get_data():
    tg = load_team_games()
    return tg, games(tg), season_end_elo(tg)


team_games, game_rows, end_elo = get_data()

st.title("NBA Analytics Dashboard")
st.caption(
    f"{len(game_rows):,} games from 1946 to 2015, with FiveThirtyEight's Elo ratings. "
    "Teams are grouped by franchise under their current names (for example, the Seattle SuperSonics appear as the Thunder)."
)

history, season_tab, forecast_tab, home_tab, records = st.tabs(
    ["Franchise history", "Season explorer", "Forecast accuracy", "Home court", "Greatest teams and upsets"]
)

with history:
    franchises = sorted(end_elo["fran_id"].unique())
    picked = st.multiselect("Franchises", franchises, default=["Celtics", "Lakers", "Bulls", "Warriors"])
    years = st.slider("Seasons", 1947, 2015, (1960, 2015))
    view = end_elo[end_elo["fran_id"].isin(picked) & end_elo["season"].between(*years)]
    if view.empty:
        st.info("Pick at least one franchise to see its Elo history.")
    else:
        fig = px.line(view, x="season", y="end_elo", color="fran_id", markers=True, height=480,
                      labels={"end_elo": "Elo at season end", "season": "Season", "fran_id": "Franchise"})
        fig.add_hline(y=1500, line_dash="dash", line_color="gray", annotation_text="average team (1500)")
        st.plotly_chart(fig, use_container_width=True)
        best = view.loc[view.groupby("fran_id")["end_elo"].idxmax()].sort_values("end_elo", ascending=False)
        cols = st.columns(min(len(best), 4))
        for col, (_, row) in zip(cols, best.head(4).iterrows()):
            col.metric(f"{row['fran_id']} best season", int(row["season"]), f"Elo {row['end_elo']:.0f}")

with season_tab:
    season = st.selectbox("Season", sorted(team_games["season"].unique(), reverse=True), index=0)
    standings = season_standings(team_games, int(season))
    left, right = st.columns([2, 3])
    with left:
        st.subheader(f"{season} regular season")
        show = standings.rename(columns={
            "fran_id": "Franchise", "lg_id": "League", "wins": "W", "losses": "L", "win_pct": "Win %",
            "avg_margin": "Avg margin", "end_elo": "Elo",
        })
        st.dataframe(show, hide_index=True, use_container_width=True, height=520)
    with right:
        top = standings.head(6)["fran_id"].tolist()
        s = team_games[(team_games["season"] == season) & (team_games["fran_id"].isin(top))]
        fig = px.line(s, x="date", y="elo_n", color="fran_id", height=520, title="Elo through the season, top 6 teams",
                      labels={"elo_n": "Elo", "date": "", "fran_id": "Franchise"})
        st.plotly_chart(fig, use_container_width=True)

with forecast_tab:
    scores = forecast_scores(game_rows)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Favourite won", f"{scores['favourite_win_rate']:.1%}")
    c2.metric("Brier score (Elo)", f"{scores['brier_elo']:.3f}", help="Lower is better. A coin flip scores 0.250.")
    c3.metric("Brier, home team always wins at its usual rate", f"{scores['brier_home_rate']:.3f}")
    c4.metric("Skill over that baseline", f"{scores['brier_skill_vs_home_rate']:.1%}")

    left, right = st.columns(2)
    with left:
        cal = calibration_table(game_rows)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=[0, 1], y=[0, 1], mode="lines", name="perfect", line={"dash": "dash", "color": "gray"}))
        fig.add_trace(go.Scatter(x=cal["predicted"], y=cal["actual"], mode="lines+markers", name="Elo",
                                 text=cal["games"], hovertemplate="predicted %{x:.2f}<br>actual %{y:.2f}<br>%{text} games"))
        fig.update_layout(title="Calibration: predicted vs actual win rate", xaxis_title="Predicted",
                          yaxis_title="Actual", height=420)
        st.plotly_chart(fig, use_container_width=True)
    with right:
        dec = accuracy_by_decade(game_rows).reset_index()
        fig = px.bar(dec, x="decade", y="favourite_win_rate", height=420, title="How often the favourite won, by decade",
                     labels={"favourite_win_rate": "Favourite win rate", "decade": "Decade"})
        fig.update_yaxes(range=[0.5, 0.75], tickformat=".0%")
        st.plotly_chart(fig, use_container_width=True)
    st.caption("Elo's probabilities are well calibrated: games it rates at 70% are won about 70% of the time.")

with home_tab:
    home = home_advantage_by_decade(team_games).reset_index()
    home["decade"] = home["decade"].astype(str) + "s"
    left, right = st.columns(2)
    fig = px.line(home, x="decade", y="home_win_rate", markers=True, height=380, title="Home win rate",
                  labels={"home_win_rate": "Home teams' win rate", "decade": ""})
    fig.update_yaxes(tickformat=".0%", range=[0.5, 0.7])
    left.plotly_chart(fig, use_container_width=True)
    fig = px.bar(home, x="decade", y="avg_home_margin", height=380, title="Average home winning margin (points)",
                 labels={"avg_home_margin": "Points", "decade": ""})
    right.plotly_chart(fig, use_container_width=True)
    st.caption("NBA regular-season games only. Home advantage peaked in the 1950s and 1980s and has declined since.")

with records:
    left, right = st.columns(2)
    with left:
        st.subheader("Highest peak Elo in a season")
        st.dataframe(peak_teams(team_games, 15).rename(columns={"season": "Season", "fran_id": "Franchise",
                                                                  "peak_elo": "Peak Elo"}).round(1),
                     hide_index=True, use_container_width=True)
    with right:
        st.subheader("Biggest upsets")
        playoffs = st.toggle("Playoffs only", value=False)
        ups = biggest_upsets(team_games, 15, playoffs_only=playoffs)
        ups = ups.assign(date=ups["date"].dt.date, forecast=(ups["forecast"] * 100).round(1)).rename(columns={
            "date": "Date", "season": "Season", "fran_id": "Winner", "opp_fran": "Beat", "pts": "Pts",
            "opp_pts": "Opp pts", "forecast": "Win chance (%)", "is_playoffs": "Playoffs",
        })
        st.dataframe(ups, hide_index=True, use_container_width=True)
