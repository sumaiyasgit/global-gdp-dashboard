import streamlit as st

import data
from utils import data_note, get_wide

st.set_page_config(page_title="Global GDP Dashboard", page_icon="🌍", layout="wide")

wide = get_wide()
years = data.years_with_data(wide)
first, last = years[0], years[-1]

st.title("🌍 Global GDP Dashboard")
st.markdown(
    f"Explore how the size of **{wide[last].notna().sum()} economies** changed between "
    f"**{first} and {last}**. Rank countries, compare their paths, and see who grew fastest."
)

# ---- headline numbers for the latest year ----------------------------------
snap = wide[last].dropna().sort_values(ascending=False)
total = snap.sum()
leader = snap.index[0]

c1, c2, c3, c4 = st.columns(4)
c1.metric(f"Economies with data ({last})", f"{len(snap)}")
c2.metric("Combined GDP", data.fmt_gdp(total))
c3.metric("Largest economy", leader, f"{snap.iloc[0] / total:.0%} of combined GDP", delta_color="off")
c4.metric("Median economy", data.fmt_gdp(snap.median()))

# ---- findings computed from the data (so they can never go out of date) -----
st.subheader("What the data shows")

both = wide[[first, last]].dropna()  # like-for-like: countries present in both years
share_first = data.top_share(both[first], 5)
share_last = data.top_share(both[last], 5)
direction = "fell" if share_last < share_first else "rose"
st.markdown(
    f"- **The top 5 economies still dominate.** Among the {len(both)} economies reported in both years, "
    f"the five largest held {share_first:.0%} of combined GDP in {first} and {share_last:.0%} in {last} "
    f"(their share {direction} by {abs(share_last - share_first) * 100:.1f} percentage points)."
)

if {"China", "United States"} <= set(wide.index):
    r_first = wide.loc["China", first] / wide.loc["United States", first]
    r_last = wide.loc["China", last] / wide.loc["United States", last]
    st.markdown(
        f"- **China closed most of the gap with the United States.** Its GDP was {r_first:.0%} of the US figure "
        f"in {first} and {r_last:.0%} in {last} "
        f"({data.fmt_gdp(wide.loc['China', first])} to {data.fmt_gdp(wide.loc['China', last])})."
    )

small = int((snap < 10).sum())
st.markdown(
    f"- **Most economies are small.** The median economy produced {data.fmt_gdp(snap.median())} in {last}, "
    f"while {leader} produced {data.fmt_gdp(snap.iloc[0])}, about {snap.iloc[0] / snap.median():,.0f} times more. "
    f"{small} of {len(snap)} economies are below $10B."
)

# ---- navigation --------------------------------------------------------------
st.subheader("Explore")
n1, n2, n3 = st.columns(3)
with n1:
    st.page_link("pages/1_Rankings.py", label="Rankings", icon="🏆")
    st.caption("Largest and smallest economies in any year, and how sizes are distributed.")
with n2:
    st.page_link("pages/2_Country_Trends.py", label="Country trends", icon="📈")
    st.caption("Compare up to five countries over time, in dollars or indexed to 100.")
with n3:
    st.page_link("pages/3_Growth.py", label="Growth", icon="🚀")
    st.caption("Fastest growers, steepest declines and biggest absolute gains between two years.")

with st.expander("Data notes and limitations"):
    st.markdown(
        f"""
- **Unit:** nominal GDP in {data.UNIT}.
- **Missing values:** the source file stores *not reported* as `0`. Those cells are treated as missing,
  so countries such as Afghanistan, Iran or Yemen do not appear to have zero GDP.
- **No 2011:** that year is absent from the source file, so charts show a gap there.
- **Series break 2014 → 2015:** many countries jump or drop by 30–100% in this one step, which does not happen
  in other years. It likely reflects a change in the underlying data release, so be careful with growth
  rates that cross it (charts mark the break).
- **Latest years** may be estimates rather than final figures.
"""
    )
data_note()
