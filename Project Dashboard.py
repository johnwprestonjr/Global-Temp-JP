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
df_long = df.melt(
    id_vars=["Country", "ISO2", "ISO3", "Indicator", "Unit"],
    value_vars=year_cols,
    var_name="Year",
    value_name="TempChange"
)
df_long["Year"] = df_long["Year"].astype(int)

# ─── Development Status Mapping ────────────────────────────
developed_iso3 = ["USA", "CAN", "GBR", "DEU", "FRA", "JPN", "AUS",
                  "NZL", "NOR", "SWE", "CHE"]
df_long["DevStatus"] = df_long["ISO3"].apply(
    lambda x: "Developed" if x in developed_iso3 else "Developing"
)

# ─── Build lists once for filters ──────────────────────────
all_countries = ["All"] + sorted(df_long["Country"].unique())
all_years     = ["All"] + sorted(df_long["Year"].unique())
year_min, year_max = df_long["Year"].min(), df_long["Year"].max()

# ─── Sidebar (two separate filter areas) ───────────────────
with st.sidebar.expander("📊 Charts Filters", expanded=True):
    chart_country = st.selectbox("Country", all_countries, key="chart_country")
    chart_year    = st.selectbox("Year",    all_years,     key="chart_year")

with st.sidebar.expander("🌐 DevStatus Filters", expanded=False):
    dev_year_range = st.slider(
        "Year Range",
        min_value=year_min,
        max_value=year_max,
        value=(year_min, year_max),
        step=1,
        key="dev_year_range"
    )

# ── DataFrames after independent filters ───────────────────
filtered_chart = df_long.copy()
if chart_country != "All":
    filtered_chart = filtered_chart[filtered_chart["Country"] == chart_country]
if chart_year != "All":
    filtered_chart = filtered_chart[filtered_chart["Year"] == chart_year]

filtered_dev = df_long[
    (df_long["Year"] >= dev_year_range[0]) &
    (df_long["Year"] <= dev_year_range[1])
].copy()

# ─── Tabs layout ───────────────────────────────────────────
tab_charts, tab_dev, tab_data = st.tabs(
    ["📊 Charts", "🌐 Developed vs Developing", "📋 Data"]
)

# ─── Shared selection for interactivity ────────────────────
alt.data_transformers.disable_max_rows()
sel_country = alt.selection_point(fields=["Country"], empty="all")

# ───────────────────────────────────────────────────────────
# 📊 CHARTS TAB — SCATTER + BAR
# ───────────────────────────────────────────────────────────
with tab_charts:

    # ── 1) SCATTER (top) ───────────────────────────────────
    if chart_country == "All":
        sample_countries = df_long["Country"].unique()[:10]
        scatter_data = df_long[df_long["Country"].isin(sample_countries)]
    else:
        scatter_data = filtered_chart

    scatter = (
        alt.Chart(scatter_data)
        .mark_circle(size=60)
        .encode(
            x=alt.X("Year:O", axis=alt.Axis(labelAngle=0)),
            y="TempChange:Q",
            color=alt.Color("TempChange:Q",
                            scale=alt.Scale(scheme="redblue",
                                            reverse=True,
                                            domainMid=0),
                            legend=alt.Legend(title="Temp Change (°C)")),
            opacity=alt.condition(sel_country, alt.value(1), alt.value(0.15)),
            tooltip=["Country", "Year", "TempChange"]
        )
        .transform_filter(sel_country)
        .properties(
            height=400,
            width=750,
            title=f"Temperature Change Over Time – "
                  f"{chart_country if chart_country!='All' else 'All Countries'}"
        )
    )

    # ── 2) BAR (bottom) ────────────────────────────────────
    #   Only country filter (not year filter) so stats don't vanish
    stats_base = df_long.copy()
    if chart_country != "All":
        stats_base = stats_base[stats_base["Country"] == chart_country]

    early = (
        stats_base[stats_base["Year"] <= 1992]
        .groupby("Country")["TempChange"].std()
        .reset_index(name="Std_Early")
    )
    late = (
        stats_base[stats_base["Year"] >= 1993]
        .groupby("Country")["TempChange"].std()
        .reset_index(name="Std_Late")
    )
    std_comp = early.merge(late, on="Country")
    std_comp["Delta_Std"] = std_comp["Std_Late"] - std_comp["Std_Early"]
    decreasing = std_comp[std_comp["Delta_Std"] < 0].sort_values("Delta_Std")
    if not decreasing.empty:
        xmin = float(decreasing["Delta_Std"].min())
    else:
        xmin = -0.1  # fallback domain

    bar = (
        alt.Chart(decreasing)
        .mark_bar()
        .encode(
            x=alt.X("Delta_Std:Q",
                    scale=alt.Scale(domain=[0, xmin]),
                    title="Δ Std Dev (1993–2024 – 1961–1992)"),
            y=alt.Y("Country:N", sort="-x"),
            color=alt.Color("Delta_Std:Q",
                            scale=alt.Scale(scheme="redblue",
                                            reverse=True,
                                            domainMid=0),
                            legend=alt.Legend(title="Δ Std Dev")),
            opacity=alt.condition(sel_country, alt.value(1), alt.value(0.4)),
            stroke=alt.condition(sel_country, alt.value("white"), alt.value(None)),
            tooltip=["Country", "Std_Early", "Std_Late", "Delta_Std"]
        )
        .add_params(sel_country)
        .properties(
            height=600,
            width=750,
            title="Countries with Decreasing Temperature Variability"
        )
    )

    st.altair_chart(
        alt.vconcat(scatter, bar).resolve_scale(color="independent"),
        use_container_width=True
    )

# ───────────────────────────────────────────────────────────
# 🌐 DEVELOPED vs DEVELOPING TAB
# ───────────────────────────────────────────────────────────
with tab_dev:
    st.subheader("Average Temperature Change: Developed vs Developing")

    # Line Graph (yearly average)
    dev_avg = (
        filtered_dev
        .groupby(["Year", "DevStatus"])["TempChange"]
        .mean()
        .reset_index()
    )

    line_chart = (
        alt.Chart(dev_avg)
        .mark_line(point=True)
        .encode(
            x=alt.X("Year:O", axis=alt.Axis(labelAngle=0)),
            y=alt.Y("TempChange:Q", title="Avg Temp Change (°C)"),
            color=alt.Color("DevStatus:N", legend=alt.Legend(title="Group")),
            tooltip=["Year", "DevStatus", "TempChange"]
        )
        .properties(
            title=f"Average Temp Change ({dev_year_range[0]}–{dev_year_range[1]})",
            width=750,
            height=400
        )
    )
    st.altair_chart(line_chart, use_container_width=True)

    # Bar Graph (5‑year groups)
    filtered_dev["YearGroup"] = (filtered_dev["Year"] // 5) * 5
    dev_bar = (
        filtered_dev
        .groupby(["YearGroup", "DevStatus"])["TempChange"]
        .mean()
        .reset_index()
    )

    bar_chart = (
        alt.Chart(dev_bar)
        .mark_bar()
        .encode(
            x=alt.X("YearGroup:O", title="5‑Year Group"),
            y=alt.Y("TempChange:Q", title="Avg Temp Change (°C)"),
            color=alt.Color("DevStatus:N", legend=alt.Legend(title="Group")),
            tooltip=["YearGroup", "DevStatus", "TempChange"]
        )
        .properties(
            title="5‑Year Average Temperature Change by Development Status",
            width=750,
            height=400
        )
    )
    st.altair_chart(bar_chart, use_container_width=True)

# ───────────────────────────────────────────────────────────
# 📋 DATA TAB — TABLE BASED ON CHART FILTERS
# ───────────────────────────────────────────────────────────
with tab_data:
    st.subheader("Filtered Data Table (Charts Filters)")
    st.dataframe(filtered_chart)
