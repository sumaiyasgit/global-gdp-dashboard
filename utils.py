"""Shared Streamlit helpers: cached data loading and consistent chart styling."""
import plotly.graph_objects as go
import streamlit as st

import data

# Colours: one blue for single series, a fixed order for multi-country charts,
# orange for "decline" so it stands apart from blue.
BLUE = "#2a78d6"
ORANGE = "#eb6834"
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]
GRID = "rgba(128,128,128,0.25)"


@st.cache_data
def get_wide():
    """Load and clean the data once; Streamlit caches the result."""
    return data.load_wide()


def style(fig: go.Figure, height: int = 420) -> go.Figure:
    """Apply the same clean look to every chart."""
    fig.update_layout(
        height=height,
        margin=dict(l=10, r=10, t=30, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend_title_text="",
        hovermode="closest",
    )
    fig.update_xaxes(gridcolor=GRID, zeroline=False)
    fig.update_yaxes(gridcolor=GRID, zeroline=False)
    return fig


def hbar(labels, values, texts, color=BLUE, hover="%{y}: %{x:,.1f}", tickformat=None) -> go.Figure:
    """Horizontal bar chart with the value written at the end of each bar."""
    fig = go.Figure(
        go.Bar(
            x=list(values),
            y=list(labels),
            orientation="h",
            marker_color=color,
            text=list(texts),
            textposition="outside",
            cliponaxis=False,
            hovertemplate=hover + "<extra></extra>",
        )
    )
    fig.update_yaxes(autorange="reversed", showgrid=False)  # first item on top
    if tickformat:
        fig.update_xaxes(tickformat=tickformat)
    return style(fig, height=70 + 30 * len(list(labels)))


def data_note():
    """Small footer shown on every page."""
    st.caption(
        f"Values are nominal GDP in {data.UNIT}. Economies with no reported value are left out "
        "rather than shown as zero. See the README for data notes."
    )
