import streamlit as st
import pandas as pd
import altair as alt

# Set Streamlit page config
st.set_page_config(
    page_title="Global Temperature Dashboard",
    page_icon="🌍",
    layout="wide"
)

st.title("🌍 Global Temperature Story 🌡️")

# Load temperature dataset
df = pd.read_csv("Indicator_3_1_Climate_Indicators_Annual_Mean_Global_Surface_Temperature_577579683071085080.csv")
year_cols = [col for col in df.columns if col.isdigit()]
df_long = df.melt(
    id_vars=["Country", "ISO2", "ISO3", "Indicator", "Unit"],
    value_vars=year_cols,
    var_name="Year",
    value_name="TempChange"
)

# Convert Year to int for comparison
df_long["Year"] = df_long["Year"].astype(int)

# Sidebar filters
st.sidebar.header("🔍 Filters")
countries = ["All"] + sorted(df_long["Country"].dropna().unique().tolist())
selected_country = st.sidebar.selectbox("Country", countries)
years = ["All"] + sorted(df_long["Year"].unique().tolist())
selected_year = st.sidebar.selectbox("Year", years)

# Filter data for display
filtered_data = df_long.copy()
if selected_country != "All":
    filtered_data = filtered_data[filtered_data["Country"] == selected_country]
if selected_year != "All":
    filtered_data = filtered_data[filtered_data["Year"] == selected_year]

# Layout Tabs
tab1, tab2 = st.tabs(["📊 Charts", "📋 Data"])

# ───────────────────────────────────────────
# TAB 1: Charts
# ───────────────────────────────────────────
with tab1:
    alt.data_transformers.disable_max_rows()
    st.subheader(f"Temperature Change Over Time – {selected_country if selected_country != 'All' else 'Sample of Countries'}")

    chart_data = filtered_data if selected_country != "All" else df_long[df_long["Country"].isin(df_long["Country"].unique()[:10])]
    circle_chart = alt.Chart(chart_data).mark_circle(size=60).encode(
        x=alt.X("Year:O", axis=alt.Axis(labelAngle=0)),
        y="TempChange:Q",
        color=alt.Color("TempChange:Q", scale=alt.Scale(scheme="redblue")),
        tooltip=["Country", "Year", "TempChange"]
    ).properties(height=400, width=700)
    st.altair_chart(circle_chart, use_container_width=True)

    st.subheader("Countries with Decreasing Temperature Variability")
    early = df_long[df_long["Year"] <= 1992].groupby("Country")["TempChange"].std().reset_index(name="Std_Early")
    late = df_long[df_long["Year"] >= 1993].groupby("Country")["TempChange"].std().reset_index(name="Std_Late")
    std_comp = early.merge(late, on="Country")
    std_comp["Delta_Std"] = std_comp["Std_Late"] - std_comp["Std_Early"]
    decreasing_std = std_comp[std_comp["Delta_Std"] < 0].sort_values("Delta_Std")

    bar_chart = alt.Chart(decreasing_std).mark_bar().encode(
        x=alt.X("Delta_Std:Q", title="Δ Std Dev (1993–2024 minus 1961–1992)"),
        y=alt.Y("Country:N", sort="-x"),
        color=alt.Color("Delta_Std:Q", scale=alt.Scale(scheme="redblue")),
        tooltip=["Country", "Std_Early", "Std_Late", "Delta_Std"]
    ).properties(height=600, width=750)
    st.altair_chart(bar_chart, use_container_width=True)

# ───────────────────────────────────────────
# TAB 2: Data Table
# ───────────────────────────────────────────
with tab2:
    st.subheader("Filtered Data Table")
    st.dataframe(filtered_data)
