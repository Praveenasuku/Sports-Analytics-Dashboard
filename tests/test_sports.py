import pytest

from sports.analysis import (
    biggest_upsets,
    calibration_table,
    forecast_scores,
    home_advantage_by_decade,
    peak_teams,
    recalibration_test,
    season_standings,
)
from sports.data import games, load_team_games


@pytest.fixture(scope="module")
def team_games():
    return load_team_games()


@pytest.fixture(scope="module")
def game_rows(team_games):
    return games(team_games)


def test_each_game_appears_twice(team_games, game_rows):
    assert len(team_games) == 2 * len(game_rows)
    assert game_rows["game_id"].is_unique


def test_both_sides_of_a_game_agree(team_games):
    one = team_games[team_games["game_id"] == team_games["game_id"].iloc[0]]
    assert one["win"].sum() == 1
    assert one["forecast"].sum() == pytest.approx(1.0, abs=1e-6)


def test_elo_beats_simple_baselines(game_rows):
    s = forecast_scores(game_rows)
    assert s["brier_elo"] < s["brier_home_rate"] < s["brier_coin_flip"]
    assert 0.6 < s["favourite_win_rate"] < 0.75


def test_calibration_is_close(game_rows):
    cal = calibration_table(game_rows)
    big = cal[cal["games"] > 1000]
    assert (abs(big["predicted"] - big["actual"]) < 0.03).all()


def test_recalibration_uses_time_split(game_rows):
    result = recalibration_test(game_rows, split_year=2000)
    assert result["test_games"] == (game_rows["season"] >= 2000).sum()


def test_home_teams_win_more_than_half(team_games):
    home = home_advantage_by_decade(team_games)
    assert (home["home_win_rate"] > 0.55).all()


def test_1996_bulls_have_highest_peak(team_games):
    top = peak_teams(team_games, 1).iloc[0]
    assert (top["season"], top["fran_id"]) == (1996, "Bulls")


def test_standings_for_1996(team_games):
    table = season_standings(team_games, 1996)
    bulls = table[table["fran_id"] == "Bulls"].iloc[0]
    assert (bulls["wins"], bulls["losses"]) == (72, 10)


def test_upsets_are_wins_with_low_forecast(team_games):
    ups = biggest_upsets(team_games, 10)
    assert (ups["forecast"] < 0.1).all()
