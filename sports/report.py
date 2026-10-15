"""Produce the figures and summary used in the README.

Usage:
    python -m sports.report
"""

from __future__ import annotations

import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from .analysis import (  # noqa: E402
    biggest_upsets,
    calibration_table,
    forecast_scores,
    home_advantage_by_decade,
    peak_teams,
    recalibration_test,
    season_end_elo,
)
from .data import ROOT, games, load_team_games  # noqa: E402

FIG_DIR = ROOT / "reports" / "figures"
ICONIC = ["Celtics", "Lakers", "Bulls", "Warriors", "Spurs"]


def main() -> dict:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"figure.dpi": 140, "font.size": 10})
    tg = load_team_games()
    g = games(tg)

    cal = calibration_table(g)
    fig, ax = plt.subplots(figsize=(4.8, 4.4))
    ax.plot([0, 1], [0, 1], color="#8c959f", lw=1, ls="--", label="perfect calibration")
    ax.plot(cal["predicted"], cal["actual"], marker="o", color="#1f6feb", lw=2, label="Elo forecast")
    ax.set_xlabel("Predicted win probability")
    ax.set_ylabel("Actual win rate")
    ax.set_title("Elo says 70%, teams win about 70%")
    ax.legend(loc="upper left")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "calibration.png")
    plt.close(fig)

    home = home_advantage_by_decade(tg)
    fig, ax = plt.subplots(figsize=(5.4, 3.4))
    ax.plot(home.index.astype(str) + "s", home["home_win_rate"] * 100, marker="o", color="#d1242f", lw=2)
    ax.set_ylabel("Home teams' win rate (%)")
    ax.set_title("Home-court advantage by decade (NBA regular season)")
    ax.set_ylim(50, 70)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "home_advantage.png")
    plt.close(fig)

    end = season_end_elo(tg)
    fig, ax = plt.subplots(figsize=(7, 3.6))
    for team in ICONIC:
        t = end[end["fran_id"] == team]
        ax.plot(t["season"], t["end_elo"], lw=1.6, label=team)
    ax.axhline(1500, color="#8c959f", lw=1, ls="--")
    ax.set_ylabel("Elo at season end")
    ax.set_title("Dynasties in Elo (1500 = average team)")
    ax.legend(ncol=5, loc="upper center", bbox_to_anchor=(0.5, -0.12), frameon=False)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "dynasties.png")
    plt.close(fig)

    summary = {
        "forecast_scores": forecast_scores(g),
        "recalibration_test": recalibration_test(g),
        "home_advantage": home["home_win_rate"].to_dict(),
        "peak_teams": peak_teams(tg).round(1).to_dict(orient="records"),
        "biggest_upsets": biggest_upsets(tg, 5).assign(date=lambda d: d["date"].dt.date.astype(str))
        .round(3).to_dict(orient="records"),
    }
    (ROOT / "reports" / "summary.json").write_text(json.dumps(summary, indent=2, default=float))
    print(json.dumps(summary, indent=2, default=float))
    return summary


if __name__ == "__main__":
    main()
