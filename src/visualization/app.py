import matplotlib.pyplot as plt
import streamlit as st

from charts import (
    available_categories,
    available_years,
    constructor_points_chart,
    load_season,
    retirements_chart,
    top_riders_chart,
)

st.set_page_config(page_title="MotoGP Performance Analyzer", layout="wide")


@st.cache_data
def load_data(year):
    return load_season(year)


def show(fig):
    st.pyplot(fig)
    plt.close(fig)


st.title("MotoGP Performance Analyzer")

years = available_years()
if not years:
    st.error("No processed data found in data/processed/. Run load_data.py first.")
    st.stop()

year = st.sidebar.selectbox("Season", years, index=len(years) - 1)
df = load_data(year)
category = st.sidebar.selectbox("Category", available_categories(df))

tab_riders, tab_constructors, tab_reliability = st.tabs(
    ["Riders", "Constructors", "Reliability"]
)

with tab_riders:
    show(top_riders_chart(df, category, year))
    st.caption("Points from Grands Prix and Sprints, summed over the season.")

with tab_constructors:
    show(constructor_points_chart(df, category, year))
    st.caption(
        "Sum of the points scored by all riders of each constructor. "
        "Not the official constructors' standings."
    )

with tab_reliability:
    show(retirements_chart(df, category, year))
    st.caption(
        "Grand Prix only. Counts retirements, disqualifications and did-not-starts. "
        "Teams with more riders on track have more chances to appear here."
    )