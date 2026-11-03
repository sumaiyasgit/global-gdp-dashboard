import streamlit as st

import data
from utils import BLUE, ORANGE, data_note, get_wide, hbar

st.set_page_config(page_title="Growth | Global GDP", page_icon="🚀", layout="wide")

wide = get_wide()
years = data.years_with_data(wide)

st.title("🚀 Growth")
st.write("Who grew fastest, who shrank, and who added the most output between two years.")

st.sidebar.header("Filters")
start_options = years[:-1]
start = st.sidebar.selectbox("From year", start_options, index=start_options.index(2015) if 2015 in start_options else 0)
end_options = [y for y in years if y > start]
end = st.sidebar.selectbox("To year", end_options, index=len(end_options) - 1)
min_gdp = st.sidebar.select_slider(
    "Ignore economies smaller than (in the first year)",
    options=[0, 1, 5, 10, 25, 50, 100],
    value=10,
    format_func=lambda v: "no limit" if v == 0 else f"${v}B",
    help="Very small economies can show huge percentage growth from a tiny base.",
)
top_n = st.sidebar.slider("Number of economies to show", 5, 20, 10)

growth = data.growth_table(wide, start, end, min_gdp)
if growth.empty:
    st.warning("No economies match these filters. Try a lower size limit or a different period.")
    st.stop()

if data.spans_break(start, end):
    st.warning(
        "This period crosses the 2014 to 2015 break in the source data, so some growth rates are inflated or "
        "deflated by the data itself. Try a period that starts in 2015 or later, or ends in 2014 or earlier."
    )

fastest = growth["CAGR"].idxmax()
biggest = growth["Change"].idxmax()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Economies compared", len(growth))
c2.metric("Median annual growth", f"{growth['CAGR'].median():.1%}")
c3.metric("Fastest growing", fastest, f"{growth.loc[fastest, 'CAGR']:+.1%} per year", delta_color="off")
c4.metric("Biggest absolute gain", biggest, f"+{data.fmt_gdp(growth.loc[biggest, 'Change'])}", delta_color="off")

st.caption(f"Annual growth is the compound annual growth rate (CAGR) from {start} to {end}.")

tab_fast, tab_slow, tab_abs = st.tabs(["Fastest growing", "Steepest declines", "Biggest absolute gains"])

with tab_fast:
    d = growth.nlargest(top_n, "CAGR")
    st.subheader(f"Fastest-growing economies, {start} to {end}")
    st.plotly_chart(
        hbar(d.index, d["CAGR"], [f"{v:+.1%}" for v in d["CAGR"]], BLUE, "%{y}: %{x:+.1%} per year", ".0%")
    )

with tab_slow:
    d = growth.nsmallest(top_n, "CAGR")
    st.subheader(f"Slowest-growing or shrinking economies, {start} to {end}")
    st.plotly_chart(
        hbar(d.index, d["CAGR"], [f"{v:+.1%}" for v in d["CAGR"]], ORANGE, "%{y}: %{x:+.1%} per year", ".0%")
    )
    shrinking = int((growth["CAGR"] < 0).sum())
    st.info(f"**Takeaway:** {shrinking} of {len(growth)} economies were smaller in {end} than in {start}.")

with tab_abs:
    d = growth.nlargest(top_n, "Change")
    st.subheader(f"Largest increases in GDP, {start} to {end}")
    st.plotly_chart(
        hbar(d.index, d["Change"], [f"+{data.fmt_gdp(v)}" for v in d["Change"]], BLUE, "%{y}: +$%{x:,.1f}B")
    )
    total_change = growth["Change"].sum()
    if total_change > 0:
        st.info(
            f"**Takeaway:** the {top_n} biggest gainers added {d['Change'].sum() / total_change:.0%} "
            f"of all new GDP across the {len(growth)} economies compared."
        )

with st.expander("Full growth table"):
    table = growth.sort_values("CAGR", ascending=False).copy()
    table["CAGR"] = (table["CAGR"] * 100).round(2)
    table = table.rename(
        columns={
            "Start": f"GDP {start} ({data.UNIT})",
            "End": f"GDP {end} ({data.UNIT})",
            "Change": f"Change ({data.UNIT})",
            "CAGR": "Annual growth (%)",
        }
    ).round(2)
    st.dataframe(table)
    st.download_button(
        "Download as CSV",
        table.to_csv().encode("utf-8"),
        file_name=f"gdp_growth_{start}_{end}.csv",
        mime="text/csv",
    )

data_note()
