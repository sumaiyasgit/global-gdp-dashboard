"""Basic checks for the data layer. Run with:  python -m pytest"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import data  # noqa: E402


def wide():
    return data.load_wide()


def test_shape_and_years():
    w = wide()
    assert w.shape[1] == 24  # 1999..2022
    assert w.index.is_unique
    assert 2011 not in data.years_with_data(w)  # absent in the source file
    assert w[2011].isna().all()


def test_zero_means_missing():
    w = wide()
    assert not (w == 0).any().any()  # no zeros left
    assert math.isnan(w.loc["Afghanistan", 2015])  # was 0 in the CSV
    assert math.isnan(w.loc["Iran", 2022])


def test_thousands_separator_parsed():
    w = wide()
    assert w.loc["United States", 2022] == 24796.08
    assert w.loc["Australia", 2012] == 1039.69


def test_names_renamed():
    w = wide()
    assert "South Korea" in w.index and "Korea" not in w.index
    assert not any("," in c for c in w.index)


def test_cagr_and_growth_table():
    assert abs(data.cagr(100, 121, 2) - 0.10) < 1e-9
    assert math.isnan(data.cagr(0, 10, 3))
    g = data.growth_table(wide(), 2015, 2022, min_start_gdp=10)
    assert (g["Start"] >= 10).all()
    assert g.loc["United States", "Change"] > 0


def test_top_share_bounds():
    s = wide()[2022]
    assert 0 < data.top_share(s, 5) < 1
    assert abs(data.top_share(s, 1000) - 1.0) < 1e-9


def test_formatting():
    assert data.fmt_gdp(24796.08) == "$24.8T"
    assert data.fmt_gdp(51.5) == "$52B" or data.fmt_gdp(51.5) == "$51B"
    assert data.fmt_gdp(3.44) == "$3.4B"
    assert data.fmt_gdp(0.047) == "$47M"
    assert data.fmt_gdp(float("nan")) == "n/a"


def test_log_histogram_counts_everything():
    s = wide()[2022].dropna()
    _, counts, lows, highs = data.log_histogram(s)
    assert counts.sum() == len(s)
    assert (highs > lows).all()


def test_break_detection():
    assert data.spans_break(2012, 2016)
    assert not data.spans_break(2015, 2022)
    assert not data.spans_break(1999, 2014)
