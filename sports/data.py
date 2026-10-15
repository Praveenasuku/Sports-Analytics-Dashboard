"""Download, compact and load FiveThirtyEight's NBA Elo dataset.

Each game appears twice in the source file, once from each team's side.
`_iscopy == 0` marks the first copy, which is the home team's view for all
but a handful of neutral-site games.
"""

from __future__ import annotations

import urllib.request
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
SOURCE_URL = "https://raw.githubusercontent.com/fivethirtyeight/data/master/nba-elo/nbaallelo.csv"
DATA_PATH = ROOT / "data" / "nba_elo.csv.gz"

KEEP = [
    "game_id", "lg_id", "_iscopy", "year_id", "date_game", "seasongame", "is_playoffs",
    "fran_id", "pts", "elo_i", "elo_n", "opp_fran", "opp_pts", "opp_elo_i",
    "game_location", "game_result", "forecast",
]


def download(path: Path = DATA_PATH) -> Path:
    """Fetch the source CSV and save only the columns we use, gzipped."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(SOURCE_URL, timeout=120) as response:
        raw = pd.read_csv(response)
    raw[KEEP].to_csv(path, index=False, compression="gzip")
    return path


def load_team_games(path: Path = DATA_PATH) -> pd.DataFrame:
    """One row per team per game (both sides of every game)."""
    if not path.exists():
        download(path)
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date_game"], format="%m/%d/%Y")
    df["win"] = (df["game_result"] == "W").astype(int)
    df["margin"] = df["pts"] - df["opp_pts"]
    df["season"] = df["year_id"]
    return df.drop(columns=["date_game"])


def games(team_games: pd.DataFrame) -> pd.DataFrame:
    """One row per game, from the first-listed (usually home) team's side."""
    g = team_games[team_games["_iscopy"] == 0].copy()
    g["elo_diff"] = g["elo_i"] - g["opp_elo_i"]
    return g
