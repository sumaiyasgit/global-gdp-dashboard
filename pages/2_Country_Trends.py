import numpy as np
import plotly.graph_objects as go
import streamlit as st

import data
from utils import SERIES, data_note, get_wide, style

st.set_page_config(page_title="Country trends | Global GDP", page_icon="📈", layout="wide")

wide = get_wide()
years = data.years_with_data(wide)

st.title("📈 Country trends")

st.sidebar.header("Filters")
selected = st.sidebar.multiselect(
    "Countries (up to 5)",
    list(wide.index),
    default=[c for c in ["United States", "China", "India"] if c in wide.index],
    max_selections=5,
)
lo, hi = st.sidebar.select_slider("Years", options=years, value=(years[0], years[-1]))
mode = st.sidebar.radio(
    "Show",
    ["Actual GDP", "Indexed (first year = 100)"],
    help="Indexed view makes growth comparable between large and small economies.",
)
log_scale = st.sidebar.checkbox("Log scale", help="Useful when comparing very large and very small economies.")

if not selected:
    st.info("Choose at least one country in the sidebar.")
    st.stop()
if lo == hi:
    st.info("Choose a range that covers at least two different years.")
    st.stop()

indexed = mode.startswith("Indexed")

# ---- summary cards -------------------------------------------------------------
cols = st.columns(len(selected))
for col, country in zip(cols, selected):
    s = wide.loc[country, lo:hi].dropna()
    if s.empty:
        col.metric(country, "no data")
        continue
    growth = data.cagr(s.iloc[0], s.iloc[-1], int(s.index[-1] - s.index[0]))
    delta = f"{growth:+.1%} per year since {s.index[0]}" if np.isfinite(growth) else None
    col.metric(f"{country} ({s.index[-1]})", data.fmt_gdp(s.iloc[-1]), delta)

# ---- chart ---------------------------------------------------------------------
fig = go.Figure()
for i, country in enumerate(selected):
    s = wide.loc[country, lo:hi]
    if s.notna().sum() == 0:
        continue
    if indexed:
        s = s / s.dropna().iloc[0] * 100
    fig.add_trace(
        go.Scatter(
            x=s.index,
            y=s.values,
            name=country,
            mode="lines+markers",
            line=dict(color=SERIES[i], width=2),
            marker=dict(size=6),
            connectgaps=False,  # leave a visible gap for missing years (2011)
            hovertemplate=country + " %{x}: " + ("%{y:,.0f}" if indexed else "$%{y:,.1f}B") + "<extra></extra>",
        )
    )

if lo <= data.BREAK_AFTER < hi:
    fig.add_vline(
        x=data.BREAK_AFTER + 0.5,
        line_dash="dot",
        line_color="gray",
        annotation_text="Source data break",
        annotation_position="top left",
    )

fig.update_xaxes(tickformat="d", dtick=2)
fig.update_yaxes(title="Index (first year = 100)" if indexed else f"GDP ({data.UNIT})")
if log_scale:
    fig.update_yaxes(type="log")
st.plotly_chart(style(fig, height=480))

if data.spans_break(lo, hi):
    st.warning(
        "This range crosses the 2014 to 2015 break in the source data. Some jumps there come from the data, "
        "not from the economy."
    )

# ---- automatic takeaway ----------------------------------------------------------
rates = {}
for country in selected:
    s = wide.loc[country, lo:hi].dropna()
    if len(s) >= 2:
        g = data.cagr(s.iloc[0], s.iloc[-1], int(s.index[-1] - s.index[0]))
        if np.isfinite(g):
            rates[country] = g
if len(rates) >= 2:
    fastest = max(rates, key=rates.get)
    slowest = min(rates, key=rates.get)
    st.info(
        f"**Takeaway:** between {lo} and {hi}, {fastest} grew fastest ({rates[fastest]:+.1%} per year) "
        f"and {slowest} slowest ({rates[slowest]:+.1%} per year)."
    )

with st.expander("Data table"):
    table = wide.loc[selected, lo:hi].T.round(2)
    st.dataframe(table)
    st.download_button(
        "Download as CSV",
        table.to_csv().encode("utf-8"),
        file_name="gdp_trends.csv",
        mime="text/csv",
    )

data_note()
