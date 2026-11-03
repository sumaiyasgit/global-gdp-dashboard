import plotly.graph_objects as go
import streamlit as st

import data
from utils import BLUE, data_note, get_wide, hbar, style

st.set_page_config(page_title="Rankings | Global GDP", page_icon="🏆", layout="wide")

wide = get_wide()
years = data.years_with_data(wide)

st.title("🏆 Rankings")

st.sidebar.header("Filters")
year = st.sidebar.selectbox("Year", years, index=len(years) - 1)
top_n = st.sidebar.slider("Number of economies to show", 5, 20, 10)

snap = wide[year].dropna().sort_values(ascending=False)
total = snap.sum()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Economies with data", len(snap))
c2.metric("Largest economy", snap.index[0], data.fmt_gdp(snap.iloc[0]), delta_color="off")
c3.metric(f"Top {top_n} share of combined GDP", f"{snap.head(top_n).sum() / total:.0%}")
c4.metric("Median economy", data.fmt_gdp(snap.median()))

tab_top, tab_dist, tab_small = st.tabs(["Largest economies", "Distribution", "Smallest economies"])

with tab_top:
    top = snap.head(top_n)
    st.subheader(f"Top {top_n} economies by GDP, {year}")
    fig = hbar(
        top.index,
        top.values,
        [data.fmt_gdp(v) for v in top.values],
        hover="%{y}: $%{x:,.1f}B",
    )
    fig.update_xaxes(title=f"GDP ({data.UNIT})")
    st.plotly_chart(fig)
    st.info(
        f"**Takeaway:** the {top_n} largest economies produce {top.sum() / total:.0%} of the combined GDP of all "
        f"{len(snap)} economies. {snap.index[0]} alone accounts for {snap.iloc[0] / total:.0%}."
    )

with tab_dist:
    st.subheader(f"How sizes are distributed, {year}")
    centres, counts, lows, highs = data.log_histogram(snap)
    fig = go.Figure(
        go.Bar(
            x=centres,
            y=counts,
            width=0.22,
            marker_color=BLUE,
            customdata=list(zip(lows, highs)),
            hovertemplate="%{customdata[0]:,.1f} to %{customdata[1]:,.1f} US$B<br>%{y} economies<extra></extra>",
        )
    )
    ticks = list(range(int(min(centres) // 1), int(max(centres) // 1) + 2))
    fig.update_xaxes(
        tickvals=ticks,
        ticktext=[data.fmt_gdp(10.0**t).replace(".0", "") for t in ticks],
        title="GDP (each step is 10x larger)",
    )
    fig.update_yaxes(title="Number of economies")
    st.plotly_chart(style(fig))
    st.info(
        f"**Takeaway:** the typical economy is small ({data.fmt_gdp(snap.median())}), but sizes span "
        f"{snap.iloc[0] / snap.iloc[-1]:,.0f}x from smallest to largest, so the axis uses a log scale; "
        "on a normal scale almost every country would fall into the first bar."
    )

with tab_small:
    bottom = snap.tail(top_n).sort_values()
    st.subheader(f"{top_n} smallest economies, {year}")
    fig = hbar(
        bottom.index,
        bottom.values,
        [data.fmt_gdp(v) for v in bottom.values],
        hover="%{y}: $%{x:,.2f}B",
    )
    fig.update_xaxes(title=f"GDP ({data.UNIT})")
    st.plotly_chart(fig)
    st.caption("Economies with no reported value are excluded rather than shown as zero.")

with st.expander(f"Full table for {year}"):
    table = snap.rename(f"GDP ({data.UNIT})").to_frame()
    table.insert(0, "Rank", range(1, len(table) + 1))
    table["Share of combined GDP"] = (snap / total * 100).round(2)
    st.dataframe(table.round(2))
    st.download_button(
        "Download as CSV",
        table.to_csv().encode("utf-8"),
        file_name=f"gdp_{year}.csv",
        mime="text/csv",
    )

data_note()
