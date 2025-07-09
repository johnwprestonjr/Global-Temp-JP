# ───────────────────────────────────────────────────────────
#  🌍  GLOBAL TEMPERATURE STORY DASHBOARD  (Streamlit + Altair)
# ───────────────────────────────────────────────────────────
import streamlit as st
import pandas as pd
import altair as alt

# ─── Page set‑up ────────────────────────────────────────────
st.set_page_config(page_title="Global Temperature Dashboard",
                   page_icon="🌍",
                   layout="wide")
st.title("🌍 Global Temperature Story  🌡️")

# ─── Data load & reshape ───────────────────────────────────
df = pd.read_csv(
    "Indicator_3_1_Climate_Indicators_Annual_Mean_Global_Surface_Temperature_577579683071085080.csv"
)

year_cols = [c for c in df.columns if c.isdigit()]
df = df[df["Element"] == "Temperature change"]
    df = df.groupby("Area").mean(numeric_only=True).reset_index()
    df.columns = df.columns.str.replace("Y", "", regex=False)
    return df

df = load_data()

# Mapping dictionaries
continent_map = {
    'United States of America': 'North America', 'Canada': 'North America', 'Brazil': 'South America',
    'Argentina': 'South America', 'France': 'Europe', 'Germany': 'Europe', 'Nigeria': 'Africa',
    'South Africa': 'Africa', 'China': 'Asia', 'India': 'Asia', 'Australia': 'Oceania'
    # Extend this with your full mapping
}
development_map = {
    'United States of America': 'Developed', 'Canada': 'Developed', 'France': 'Developed',
    'Germany': 'Developed', 'Japan': 'Developed', 'Australia': 'Developed'
    # Extend this as needed
}

# Add region info
df["Continent"] = df["Area"].map(continent_map)
df["Development"] = df["Area"].map(development_map).fillna("Developing")

# Melt the dataframe to long format
df_long = pd.melt(df, id_vars=["Area", "Continent", "Development"],
                  value_vars=[str(y) for y in range(1961, 2025)],
                  var_name="Year", value_name="TempChange")
df_long["Year"] = df_long["Year"].astype(int)

# Filter options in sidebar
st.sidebar.title("🌍 Filters")
selected_continent = st.sidebar.selectbox("Select a continent:", sorted(df_long["Continent"].dropna().unique()))
selected_year_range = st.sidebar.slider("Select Year Range", 1961, 2024, (1980, 2024))

# Filter by continent and year
filtered_df = df_long[(df_long["Continent"] == selected_continent) &
                      (df_long["Year"].between(*selected_year_range))]

# Tabs for layout
tab1, tab2, tab3 = st.tabs(["📊 Charts", "🌐 Developed vs Developing", "📋 Data"])

# ------------------- 📊 Charts Tab -------------------
with tab1:
    st.subheader(f"Top 5 Fastest-Warming Countries in {selected_continent}")
    top5 = filtered_df.groupby("Area")["TempChange"].mean().nlargest(5).reset_index()

    bar_chart = alt.Chart(top5).mark_bar().encode(
        x=alt.X("TempChange:Q", title="Avg Temp Change (°C)"),
        y=alt.Y("Area:N", sort='-x'),
        tooltip=["Area", "TempChange"]
    ).properties(
        width=700, height=400,
        title="Top 5 Countries by Avg Temp Change"
    )

    st.altair_chart(bar_chart, use_container_width=True)

# ------------------- 🌐 Developed vs Developing Tab -------------------
with tab2:
    st.subheader("Avg Temp Change: Developed vs Developing")

    dev_filtered = df_long[df_long["Year"].between(*selected_year_range)]
    dev_avg = dev_filtered.groupby(["Year", "Development"])["TempChange"].mean().reset_index()

    line_chart = alt.Chart(dev_avg).mark_line(point=True).encode(
        x="Year:O",
        y=alt.Y("TempChange:Q", title="Avg Temp Change (°C)"),
        color="Development:N",
        tooltip=["Year", "Development", "TempChange"]
    ).properties(
        width=800, height=400,
        title="Temperature Change Over Time"
    )

    st.altair_chart(line_chart, use_container_width=True)

# ------------------- 📋 Data Tab -------------------
with tab3:
    st.subheader("Filtered Data Table")
    st.dataframe(filtered_df)
