"""Analyses behind the dashboard: forecast accuracy, home court, team strength, upsets."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, log_loss


# ---------- How good are Elo's win probabilities? ----------

def forecast_scores(games: pd.DataFrame) -> dict:
    """Brier score, log loss and favourite accuracy of Elo's pre-game forecasts.

    Two baselines: a coin flip (0.5) and "the home team wins at its historical
    rate", which is the simplest forecast that uses any information at all.
    """
    y, p = games["win"].to_numpy(), games["forecast"].to_numpy()
    home_rate = np.full(len(y), y.mean())
    brier = brier_score_loss(y, p)
    return {
        "games": int(len(y)),
        "brier_elo": round(float(brier), 4),
        "brier_coin_flip": 0.25,
        "brier_home_rate": round(float(brier_score_loss(y, home_rate)), 4),
        "brier_skill_vs_home_rate": round(float(1 - brier / brier_score_loss(y, home_rate)), 4),
        "log_loss_elo": round(float(log_loss(y, p)), 4),
        "favourite_win_rate": round(float(((p > 0.5) == y).mean()), 4),
    }


def calibration_table(games: pd.DataFrame, bins: int = 10) -> pd.DataFrame:
    """Predicted vs actual win rate in probability bins."""
    cut = pd.cut(games["forecast"], np.linspace(0, 1, bins + 1))
    return (
        games.groupby(cut, observed=True)
        .agg(predicted=("forecast", "mean"), actual=("win", "mean"), games=("win", "size"))
        .reset_index(drop=True)
    )


def recalibration_test(games: pd.DataFrame, split_year: int = 2000) -> dict:
    """Can a model trained on older games beat Elo's forecasts on newer games?

    Fits a logistic regression on rating difference and home court using games
    before ``split_year``, then compares it with Elo on games from that year on.
    """
    X_cols = ["elo_diff", "is_home"]
    data = games.assign(is_home=(games["game_location"] == "H").astype(int))
    train, test = data[data["season"] < split_year], data[data["season"] >= split_year]
    model = LogisticRegression().fit(train[X_cols], train["win"])
    p = model.predict_proba(test[X_cols])[:, 1]
    return {
        "test_games": int(len(test)),
        "brier_elo": round(float(brier_score_loss(test["win"], test["forecast"])), 4),
        "brier_recalibrated": round(float(brier_score_loss(test["win"], p)), 4),
        "home_advantage_elo_points": round(float(model.coef_[0][1] / model.coef_[0][0]), 1),
    }


def accuracy_by_decade(games: pd.DataFrame) -> pd.DataFrame:
    g = games.assign(decade=(games["season"] // 10) * 10, correct=((games["forecast"] > 0.5) == games["win"]))
    return g.groupby("decade").agg(
        games=("win", "size"),
        favourite_win_rate=("correct", "mean"),
        brier=("forecast", lambda s: brier_score_loss(g.loc[s.index, "win"], s)),
    ).round(4)


# ---------- Home court ----------

def home_advantage_by_decade(team_games: pd.DataFrame) -> pd.DataFrame:
    """Home win rate and average home margin, NBA regular season only."""
    home = team_games[
        (team_games["game_location"] == "H") & (team_games["is_playoffs"] == 0) & (team_games["lg_id"] == "NBA")
    ]
    home = home.assign(decade=(home["season"] // 10) * 10)
    return home.groupby("decade").agg(
        games=("win", "size"), home_win_rate=("win", "mean"), avg_home_margin=("margin", "mean")
    ).round(3)


# ---------- Team strength ----------

def season_end_elo(team_games: pd.DataFrame) -> pd.DataFrame:
    """Each franchise's Elo after its last game of each season."""
    last = team_games.sort_values("date").groupby(["season", "fran_id"]).tail(1)
    return last[["season", "fran_id", "lg_id", "elo_n"]].rename(columns={"elo_n": "end_elo"}).reset_index(drop=True)


def peak_teams(team_games: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """Highest Elo ever reached by a team in a single season."""
    peaks = team_games.loc[team_games.groupby(["season", "fran_id"])["elo_n"].idxmax()]
    return peaks.nlargest(n, "elo_n")[["season", "fran_id", "elo_n"]].rename(columns={"elo_n": "peak_elo"}).reset_index(drop=True)


def season_standings(team_games: pd.DataFrame, season: int) -> pd.DataFrame:
    s = team_games[(team_games["season"] == season) & (team_games["is_playoffs"] == 0)]
    table = s.groupby(["fran_id", "lg_id"]).agg(
        wins=("win", "sum"), games=("win", "size"), avg_margin=("margin", "mean"), end_elo=("elo_n", "last")
    )
    table["losses"] = table["games"] - table["wins"]
    table["win_pct"] = table["wins"] / table["games"]
    return table.sort_values("win_pct", ascending=False).reset_index()[
        ["fran_id", "lg_id", "wins", "losses", "win_pct", "avg_margin", "end_elo"]
    ].round(3)


# ---------- Upsets ----------

def biggest_upsets(team_games: pd.DataFrame, n: int = 15, playoffs_only: bool = False) -> pd.DataFrame:
    """Wins by the team Elo gave the smallest chance."""
    wins = team_games[team_games["win"] == 1]
    if playoffs_only:
        wins = wins[wins["is_playoffs"] == 1]
    cols = ["date", "season", "fran_id", "opp_fran", "pts", "opp_pts", "forecast", "is_playoffs"]
    return wins.nsmallest(n, "forecast")[cols].reset_index(drop=True)
