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

# ─── Sidebar filters ───────────────────────────────────────
st.sidebar.header("🔍 Filters")
countries = ["All"] + sorted(df_long["Country"].unique())
years     = ["All"] + sorted(df_long["Year"].unique())

selected_country = st.sidebar.selectbox("Country", countries)
selected_year    = st.sidebar.selectbox("Year", years)

filtered = df_long.copy()
if selected_country != "All":
    filtered = filtered[filtered["Country"] == selected_country]
if selected_year != "All":
    filtered = filtered[filtered["Year"] == selected_year]

# ─── Tabs layout ───────────────────────────────────────────
tab_charts, tab_data = st.tabs(["📊 Charts", "📋 Data"])

with tab_charts:
    alt.data_transformers.disable_max_rows()

    # Shared selection
    sel_country = alt.selection_point(fields=["Country"], empty="all")

    # ── 1) SCATTER (top) ───────────────────────────────────
    if selected_country == "All":
        sample_countries = df_long["Country"].unique()[:10]
        scatter_data = df_long[df_long["Country"].isin(sample_countries)]
    else:
        scatter_data = filtered

    scatter = (
        alt.Chart(scatter_data)
        .mark_circle(size=60)
        .encode(
            x=alt.X("Year:O", axis=alt.Axis(labelAngle=0)),
            y="TempChange:Q",
            color=alt.Color(
                "TempChange:Q",
                scale=alt.Scale(scheme="redblue",
                                reverse=True,  # 🔵 ➜ ⚪ ➜ 🔴
                                domainMid=0),
                legend=alt.Legend(title="Temp Change (°C)")
            ),
            opacity=alt.condition(sel_country, alt.value(1), alt.value(0.15)),
            tooltip=["Country", "Year", "TempChange"]
        )
        .transform_filter(sel_country)
        .properties(
            height=400,
            width=750,
            title=f"Temperature Change Over Time – "
                  f"{selected_country if selected_country!='All' else 'All Countries'}"
        )
    )

    # ── 2) BAR (bottom) ────────────────────────────────────
    early = (
        df_long[df_long["Year"] <= 1992]
        .groupby("Country")["TempChange"].std()
        .reset_index(name="Std_Early")
    )
    late = (
        df_long[df_long["Year"] >= 1993]
        .groupby("Country")["TempChange"].std()
        .reset_index(name="Std_Late")
    )
    std_comp = early.merge(late, on="Country")
    std_comp["Delta_Std"] = std_comp["Std_Late"] - std_comp["Std_Early"]
    decreasing = std_comp[std_comp["Delta_Std"] < 0].sort_values("Delta_Std")

    bar = (
        alt.Chart(decreasing)
        .mark_bar()
        .encode(
            x=alt.X("Delta_Std:Q",
                    title="Δ Std Dev (1993–2024 – 1961–1992)"),
            y=alt.Y("Country:N", sort="-x"),
            color=alt.Color(
                "Delta_Std:Q",
                scale=alt.Scale(scheme="redblue",
                                reverse=True,
                                domainMid=0),
                legend=alt.Legend(title="Δ Std Dev")
            ),
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

    # Display: scatter on top, bar below
    st.altair_chart(
        alt.vconcat(scatter, bar).resolve_scale(color="independent"),
        use_container_width=True
    )

with tab_data:
    st.subheader("Filtered Data Table")
    st.dataframe(filtered)
