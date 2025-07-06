import streamlit as st
import pandas as pd
import altair as alt
import pydeck as pdk

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
df_long["Year"] = df_long["Year"].astype(int)

# Load country coordinates (ISO3 + lat/lon)
coords_url = "https://raw.githubusercontent.com/plotly/datasets/master/2014_world_gdp_with_codes.csv"
coords_df = pd.read_csv(coords_url)[["COUNTRY", "CODE", "Latitude", "Longitude"]]
coords_df.columns = ["Country", "ISO3", "Latitude", "Longitude"]

# Merge temperature data with coordinates
df_geo = df_long.merge(coords_df, on="ISO3", how="left")

# Sidebar filters
st.sidebar.header("🔍 Filters")
countries = ["All"] + sorted(df_geo["Country"].dropna().unique().tolist())
selected_country = st.sidebar.selectbox("Country", countries)
years = ["All"] + sorted(df_geo["Year"].unique().tolist())
selected_year = st.sidebar.selectbox("Year", years)

# Filter data for display
filtered_data = df_geo.copy()
if selected_country != "All":
    filtered_data = filtered_data[filtered_data["Country"] == selected_country]
if selected_year != "All":
    filtered_data = filtered_data[filtered_data["Year"] == selected_year]

# Layout Tabs
tab1, tab2, tab3 = st.tabs(["📊 Charts", "🗺️ Map", "📋 Data"])

# ───────────────────────────────────────────
# TAB 1: Charts
# ───────────────────────────────────────────
with tab1:
    alt.data_transformers.disable_max_rows()
    st.subheader(f"Temperature Change Over Time – {selected_country if selected_country != 'All' else 'Sample of Countries'}")

    chart_data = filtered_data if selected_country != "All" else df_geo[df_geo["Country"].isin(df_geo["Country"].unique()[:10])]
    circle_chart = alt.Chart(chart_data).mark_circle(size=60).encode(
        x=alt.X("Year:O", axis=alt.Axis(labelAngle=0)),
        y="TempChange:Q",
        color=alt.Color("TempChange:Q", scale=alt.Scale(scheme="redblue")),
        tooltip=["Country", "Year", "TempChange"]
    ).properties(height=400, width=700)
    st.altair_chart(circle_chart, use_container_width=True)

    st.subheader("Countries with Decreasing Temperature Variability")
    early = df_geo[df_geo["Year"] <= 1992].groupby("Country")["TempChange"].std().reset_index(name="Std_Early")
    late = df_geo[df_geo["Year"] >= 1993].groupby("Country")["TempChange"].std().reset_index(name="Std_Late")
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
# TAB 2: Map
# ───────────────────────────────────────────
with tab2:
    st.subheader(f"🌐 Map of Global Temperature Change {f'for {selected_year}' if selected_year != 'All' else ''}")
    if selected_year == "All":
        map_year = df_geo["Year"].max()
    else:
        map_year = int(selected_year)

    map_df = df_geo[df_geo["Year"] == map_year].dropna(subset=["Latitude", "Longitude", "TempChange"])

    st.pydeck_chart(pdk.Deck(
        map_style="mapbox://styles/mapbox/light-v9",
        initial_view_state=pdk.ViewState(
            latitude=0,
            longitude=0,
            zoom=1,
            pitch=0,
        ),
        layers=[
            pdk.Layer(
                "ScatterplotLayer",
                data=map_df,
                get_position="[Longitude, Latitude]",
                get_radius=40000,
                get_fill_color="[255, (1 - TempChange / 2) * 100, TempChange * 150, 160]",
                pickable=True,
            )
        ],
        tooltip={"text": "Country: {Country}\nYear: " + str(map_year) + "\nTemp Change: {TempChange}°C"}
    ))

# ───────────────────────────────────────────
# TAB 3: Data Table
# ───────────────────────────────────────────
with tab3:
    st.subheader("Filtered Data Table")
    st.dataframe(filtered_data)
