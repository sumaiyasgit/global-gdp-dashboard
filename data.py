"""Data loading and calculations for the GDP dashboard.

Everything in this file is plain pandas (no Streamlit), so it is easy to test.
"""
from pathlib import Path

import numpy as np
import pandas as pd

DATA_PATH = Path(__file__).parent / "data" / "GDP.csv"

FIRST_YEAR, LAST_YEAR = 1999, 2022
UNIT = "US$ billions"  # CHECK against your data source and edit if different

# The source file changes abruptly between 2014 and 2015 (many countries jump
# or fall by 30-100% in that one step, which never happens in other years).
# It looks like two different data releases were joined there, so we flag it.
BREAK_AFTER = 2014

# Shorter, friendlier country names (the source uses IMF-style names).
RENAME = {
    "Afghanistan, Rep. of.": "Afghanistan",
    "Bahamas, The": "Bahamas",
    "Brunei Darussalam": "Brunei",
    "Cape Verde": "Cabo Verde",
    "Congo, Democratic Republic of": "DR Congo",
    "Congo, Republic of": "Republic of the Congo",
    "Gambia, The": "Gambia",
    "Hong Kong SAR": "Hong Kong",
    "Iran, Islamic Republic of": "Iran",
    "Korea": "South Korea",
    "Kyrgyz Republic": "Kyrgyzstan",
    "Lao People's Democratic Republic": "Laos",
    "Macedonia, Former Yugoslav Republic of": "North Macedonia",
    "Slovak Republic": "Slovakia",
    "Swaziland": "Eswatini",
    "Syrian Arab Republic": "Syria",
    "Taiwan Province of China": "Taiwan",
    "Timor-Leste, Dem. Rep. of": "Timor-Leste",
    "Yemen, Republic of": "Yemen",
}


def load_wide(path=DATA_PATH) -> pd.DataFrame:
    """Return GDP as a table: one row per country, one column per year (1999-2022).

    Cleaning steps:
    * numbers such as "1,039.69" are read as 1039.69
    * a value of 0 means "not reported" in this file, so it becomes NaN
      (otherwise Afghanistan, Iran, Yemen... would look like they have zero GDP)
    * the year 2011 is absent from the file, so it is added as an empty column
      (charts then show a gap instead of a misleading straight line)
    """
    df = pd.read_csv(path, thousands=",")
    df["Country"] = df["Country"].str.strip().replace(RENAME)
    df = df.set_index("Country")
    df.columns = df.columns.astype(int)
    df = df.apply(pd.to_numeric, errors="coerce")
    df = df.mask(df <= 0)
    df = df.reindex(columns=range(FIRST_YEAR, LAST_YEAR + 1))
    df.columns.name = "Year"
    return df.sort_index()


def years_with_data(wide: pd.DataFrame) -> list:
    """Years that actually contain data (2011 is excluded)."""
    return [int(y) for y in wide.columns if wide[y].notna().any()]


def top_share(series: pd.Series, n: int) -> float:
    """Share (0-1) of the total held by the n largest values."""
    s = series.dropna()
    return float(s.nlargest(n).sum() / s.sum())


def cagr(start_value: float, end_value: float, years: int) -> float:
    """Compound annual growth rate between two values."""
    if years <= 0 or not (start_value > 0 and end_value > 0):
        return float("nan")
    return float((end_value / start_value) ** (1 / years) - 1)


def growth_table(wide: pd.DataFrame, start: int, end: int, min_start_gdp: float = 0.0) -> pd.DataFrame:
    """Growth of every country between two years.

    Columns: Start, End, Change (absolute), CAGR (compound annual growth rate).
    Only countries with a value in both years are included.
    """
    sub = wide[[start, end]].dropna()
    sub = sub[sub[start] >= min_start_gdp]
    out = pd.DataFrame(
        {
            "Start": sub[start],
            "End": sub[end],
            "Change": sub[end] - sub[start],
            "CAGR": (sub[end] / sub[start]) ** (1 / (end - start)) - 1,
        }
    )
    return out


def spans_break(start: int, end: int) -> bool:
    """True if the period start..end crosses the 2014 -> 2015 data break."""
    return start <= BREAK_AFTER < end


def fmt_gdp(value: float) -> str:
    """Format a value in US$ billions as $24.8T, $51B, $3.4B or $120M."""
    if value is None or pd.isna(value):
        return "n/a"
    if abs(value) >= 1000:
        return f"${value / 1000:,.1f}T"
    if abs(value) >= 10:
        return f"${value:,.0f}B"
    if abs(value) >= 1:
        return f"${value:,.1f}B"
    return f"${value * 1000:,.0f}M"


def to_long(wide: pd.DataFrame, countries=None) -> pd.DataFrame:
    """Country / Year / GDP rows (handy for plotting and CSV export)."""
    w = wide if countries is None else wide.loc[list(countries)]
    return w.reset_index().melt(id_vars="Country", var_name="Year", value_name="GDP")


def log_histogram(values: pd.Series, step: float = 0.25):
    """Histogram in log10 space. Returns (bin_centres, counts, low_edges, high_edges)."""
    logs = np.log10(values.dropna().to_numpy())
    lo = np.floor(logs.min())
    hi = np.ceil(logs.max())
    edges = np.arange(lo, hi + step, step)
    counts, edges = np.histogram(logs, bins=edges)
    centres = (edges[:-1] + edges[1:]) / 2
    return centres, counts, 10 ** edges[:-1], 10 ** edges[1:]
