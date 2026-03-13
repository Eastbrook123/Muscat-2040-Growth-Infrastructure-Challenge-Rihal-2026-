from __future__ import annotations

import io

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from pathlib import Path

import pandas as pd
import os

BASE_DIR = os.path.dirname(__file__)
WORKBOOK = os.path.join(BASE_DIR, "MOH_health_units_data.xlsx")

df = pd.read_excel(WORKBOOK)



def _cagr(start: float, end: float, years: int) -> float:
    if start <= 0 or end <= 0 or years <= 0:
        return float("nan")
    return (end / start) ** (1 / years) - 1


@st.cache_data
def load_inputs() -> dict[str, pd.DataFrame]:
    return {
        "population": pd.read_excel(WORKBOOK, sheet_name="Muscat Population"),
        "omani_expat": pd.read_excel(WORKBOOK, sheet_name="Muscat_omani_expart"),
        "hh_size": pd.read_excel(WORKBOOK, sheet_name="Average_Household_Size"),
        "moh_beds": pd.read_excel(WORKBOOK, sheet_name="muscat_moh_beds_manpower"),
        "male_female": pd.read_excel(WORKBOOK, sheet_name="Muscat_male_female"),
        "private_clinics": pd.read_excel(WORKBOOK, sheet_name="muscat_private_clinics"),
        "moh_units": pd.read_excel(WORKBOOK, sheet_name="MOH Health Units Data"),
        "electricity": pd.read_excel(WORKBOOK, sheet_name="Electricity consumption "),
        "gov_dist": pd.read_excel(WORKBOOK, sheet_name="Oman population distribution"),
    }


def build_projection(
    inputs: dict[str, pd.DataFrame],
    years: list[int],
    omani_growth: float,
    expat_growth: float,
    anchor_to_observed_through: int = 2025,
) -> pd.DataFrame:
    pop = inputs["population"].rename(columns={"Muscat Population": "population"}).copy()
    pop["Year"] = pop["Year"].astype(int)
    pop = pop.sort_values("Year")

    shares = inputs["omani_expat"].rename(columns={"Expart": "expat_share", "Omani": "omani_share"}).copy()
    shares["Year"] = shares["Year"].astype(int)
    shares["expat_share"] = shares["expat_share"].astype(float)

    # Anchor: use observed totals through anchor_to_observed_through
    anchor = pop.set_index("Year")["population"].to_dict()
    if anchor_to_observed_through not in anchor:
        anchor_to_observed_through = max([y for y in anchor.keys() if y <= anchor_to_observed_through])

    # Component split at anchor year using latest share trend (simple linear extrapolation).
    x = shares["Year"].to_numpy(dtype=float)
    y = shares["expat_share"].to_numpy(dtype=float)
    slope, intercept = np.polyfit(x, y, 1)
    exp_share_anchor = float(np.clip(intercept + slope * anchor_to_observed_through, 0.0, 1.0))
    total_anchor = float(anchor[anchor_to_observed_through])
    exp = total_anchor * exp_share_anchor
    om = total_anchor * (1.0 - exp_share_anchor)

    rows = []
    for yr in years:
        if yr <= anchor_to_observed_through and yr in anchor:
            total = float(anchor[yr])
        else:
            exp *= 1.0 + expat_growth
            om *= 1.0 + omani_growth
            total = exp + om
        rows.append({"Year": yr, "Population": total, "Omani_pop": om, "Expat_pop": exp})
    return pd.DataFrame(rows)


def hh_size_assumed(inputs: dict[str, pd.DataFrame], years: list[int]) -> pd.Series:
    hh = inputs["hh_size"].rename(columns={"Average Household Size": "hh_size"}).copy()
    hh["Year"] = hh["Year"].astype(int)
    d = hh.dropna()
    b, a = np.polyfit(d["Year"].to_numpy(dtype=float), d["hh_size"].to_numpy(dtype=float), 1)
    s = pd.Series(a + b * np.array(years, dtype=float), index=years)
    return s.clip(lower=3.5, upper=9.0)


def current_bed_capacity(inputs: dict[str, pd.DataFrame]) -> tuple[int, float]:
    beds = inputs["moh_beds"].rename(columns={"Muscat number of beds in MOH Hospitals": "moh_beds"}).copy()
    beds["Year"] = beds["Year"].astype(int)
    y = int(beds["Year"].max())
    cap = float(beds.loc[beds["Year"] == y, "moh_beds"].iloc[0])
    return y, cap


def compute_base_component_rates(inputs: dict[str, pd.DataFrame]) -> tuple[float, float, float]:
    """
    Returns:
      - cagr_2002_2022 (total)
      - omani_growth_base
      - expat_growth_base
    """
    pop = inputs["population"].rename(columns={"Muscat Population": "population"}).copy()
    pop["Year"] = pop["Year"].astype(int)
    pop_2002 = float(pop.loc[pop["Year"] == 2002, "population"].iloc[0])
    pop_2022 = float(pop.loc[pop["Year"] == 2022, "population"].iloc[0])
    cagr_2002_2022 = _cagr(pop_2002, pop_2022, 20)

    shares = inputs["omani_expat"].rename(columns={"Expart": "expat_share", "Omani": "omani_share"}).copy()
    shares["Year"] = shares["Year"].astype(int)
    shares["expat_share"] = shares["expat_share"].astype(float)
    shares["omani_share"] = shares["omani_share"].astype(float)

    pop_sh = pop.merge(shares, on="Year", how="left")
    pop_sh["expat_pop"] = pop_sh["population"] * pop_sh["expat_share"]
    pop_sh["omani_pop"] = pop_sh["population"] * pop_sh["omani_share"]

    o22 = float(pop_sh.loc[pop_sh["Year"] == 2022, "omani_pop"].iloc[0])
    o24 = float(pop_sh.loc[pop_sh["Year"] == 2024, "omani_pop"].iloc[0])
    e22 = float(pop_sh.loc[pop_sh["Year"] == 2022, "expat_pop"].iloc[0])
    e24 = float(pop_sh.loc[pop_sh["Year"] == 2024, "expat_pop"].iloc[0])
    omani_recent = _cagr(o22, o24, 2)
    expat_recent = _cagr(e22, e24, 2)

    blend_recent = 0.35
    omani_growth_base = (1 - blend_recent) * cagr_2002_2022 + blend_recent * omani_recent
    expat_growth_base = (1 - blend_recent) * cagr_2002_2022 + blend_recent * expat_recent
    return cagr_2002_2022, omani_growth_base, expat_growth_base


def add_infrastructure_metrics(df: pd.DataFrame, cap_beds: float, beds_per_1000: float, hh_size: float) -> pd.DataFrame:
    out = df.copy()
    out["Bed_demand"] = out["Population"] * (beds_per_1000 / 1000.0)
    out["Bed_gap"] = out["Bed_demand"] - cap_beds
    out["Stress_index"] = out["Bed_demand"] / cap_beds
    out["HH_size_used"] = hh_size
    out["Households_needed"] = out["Population"] / out["HH_size_used"]
    return out


def _load_css() -> None:
    css_path = Path(__file__).with_name("style.css")
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


def stress_bucket(s: pd.Series) -> pd.Series:
    bins = [-np.inf, 1.0, 1.25, 1.5, 2.0, np.inf]
    labels = ["≤1.00 (OK)", "1.00–1.25", "1.25–1.50", "1.50–2.00", ">2.00 (Severe)"]
    return pd.cut(s, bins=bins, labels=labels)


def fig_capacity_gap_bars(df: pd.DataFrame, value_col: str, title: str, y_title: str) -> go.Figure:
    d = df[df["Year"].isin([2025, 2030, 2035, 2040])].copy()
    d[value_col] = pd.to_numeric(d[value_col])
    fig = px.bar(
        d,
        x="Year",
        y=value_col,
        color="Scenario",
        barmode="group",
        title=title,
    )
    fig.update_layout(yaxis_title=y_title, legend_title_text="")
    return fig


def parse_electricity(inputs: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """
    Sheet provides Oman totals by sector in GWh. We convert to long format and keep years columns.
    """
    el = inputs["electricity"].copy()
    # First row is total Oman Electricity Uses; next rows are sectors with 'Energy Uses' labels.
    year_cols = [c for c in el.columns if isinstance(c, (int, float)) or str(c).strip().isdigit()]
    year_cols = [int(c) for c in year_cols]
    el_year = el[["Energy Uses"] + year_cols].copy()
    el_year = el_year.rename(columns={"Energy Uses": "sector_raw"})
    el_long = el_year.melt(id_vars=["sector_raw"], var_name="Year", value_name="GWh")
    el_long["Year"] = el_long["Year"].astype(int)
    el_long["GWh"] = pd.to_numeric(el_long["GWh"], errors="coerce")
    # Clean sector names
    el_long["Sector"] = (
        el_long["sector_raw"]
        .astype(str)
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
    )
    return el_long.dropna(subset=["GWh"])


st.set_page_config(page_title="Muscat 2040: Growth & Infrastructure Challenge", layout="wide")

_load_css()

# Global chart styling (consistent + premium)
SCENARIO_COLORS = {"Low": "#60A5FA", "Base": "#A78BFA", "High": "#F472B6"}
px.defaults.template = "plotly_dark"
px.defaults.color_discrete_map = SCENARIO_COLORS

inputs = load_inputs()

hero = f"""
<div class="hero">
  <div class="hero-title">Muscat 2040 — Growth & Infrastructure Dashboard</div>
  <div class="hero-sub">Scenario planning engine for population, healthcare capacity, housing demand, and optional electricity proxies — fully driven by your workbook.</div>
  <div class="hero-badges">
    <span class="badge"><span class="dot low"></span> Low scenario</span>
    <span class="badge"><span class="dot base"></span> Base scenario</span>
    <span class="badge"><span class="dot high"></span> High scenario</span>
    <span class="badge"><span class="dot"></span> Sliders update everything</span>
  </div>
</div>
"""
st.markdown(hero, unsafe_allow_html=True)

cagr_2002_2022, omani_growth_base, expat_growth_base = compute_base_component_rates(inputs)

with st.expander("Methodology, formulas, and data sources (click to expand)", expanded=False):
    st.markdown("### Mathematical formulas (used in this dashboard)")

    st.markdown("#### Population (CAGR, baseline)")
    st.markdown("Historical growth rate (2002–2022):")
    st.latex(r"\mathrm{CAGR}_{2002\to 2022}=\left(\frac{P_{2022}}{P_{2002}}\right)^{\frac{1}{20}}-1")

    st.markdown("#### Population projection (Omani + Expat components)")
    st.markdown("Anchoring uses observed totals through 2025 (from the workbook). From 2026 onward:")
    st.latex(r"P^{O}_{t+1}=P^{O}_t(1+g_O)\qquad P^{E}_{t+1}=P^{E}_t(1+g_E)")
    st.latex(r"P^{Total}_t=P^{O}_t+P^{E}_t")
    st.markdown("Expat share is estimated via a simple linear trend from 2022–2024 shares:")
    st.latex(r"Share^{E}_t \approx a+b\cdot t")

    st.markdown("#### Healthcare beds demand (planning benchmark)")
    st.latex(r"BedsDemand_t=P^{Total}_t\times\frac{BedsPer1000}{1000}")
    st.markdown("Capacity is held at the latest MOH bed count in the workbook (currently 2023):")
    st.latex(r"Gap_t=BedsDemand_t-BedsCapacity")
    st.latex(r"Stress_t=\frac{BedsDemand_t}{BedsCapacity}")
    st.markdown(r"Breakpoint year = first year where \(Gap_t>0\).")

    st.markdown("#### Housing demand (households required)")
    st.latex(r"Households_t=\frac{P^{Total}_t}{HHSize}")
    st.markdown("This dashboard uses the **Household size** slider as the operational planning assumption.")

    st.markdown("#### Electricity module (optional; proxy method)")
    st.markdown("The workbook provides **Oman** electricity by sector (GWh). We scale to Muscat using Muscat’s share of Oman population (2024) as a proxy:")
    st.latex(r"GWh^{Muscat}_{sector,2023}\approx Share^{Muscat}_{2024}\times GWh^{Oman}_{sector,2023}")
    st.markdown("Per-capita kWh proxy:")
    st.latex(r"kWhPerCapita_{sector,2023}=\frac{GWh^{Muscat}_{sector,2023}\times 10^6}{P^{Muscat}_{2023}}")
    st.markdown("Then per-capita changes linearly to 2040 based on the sidebar % assumption and multiplies by scenario population.")

    st.divider()

    st.markdown("### Data sources (links)")
    st.markdown("#### Provided workbook (primary data)")
    st.markdown(
        "- `MOH_health_units_data.xlsx` tabs used: `Muscat Population`, `Muscat_omani_expart`, `Average_Household_Size`, "
        "`muscat_moh_beds_manpower`, `Muscat_male_female`, `muscat_private_clinics`, `MOH Health Units Data`, "
        "`Electricity consumption `, `Oman population distribution`"
    )
    st.markdown("#### External reference links (for benchmark definitions / official portals)")
    st.markdown("- OECD indicator (hospital bed definition): https://www.oecd.org/en/data/indicators/hospital-beds.html")
    st.markdown("- OECD Health at a Glance (bed context/ranges): https://www.oecd.org/en/publications/health-at-a-glance-2023_7a7afb35-en/full-report/hospital-beds-and-occupancy_10add5df.html")
    st.markdown("- Oman NCSI data portal (official population datasets): https://data.ncsi.gov.om/?q=dataset%2Ftotal-population")

st.sidebar.header("Scenario inputs")
st.sidebar.caption("Baseline CAGR (2002–2022) computed from the workbook is shown below. Sliders adjust Low/Base/High scenarios.")
st.sidebar.metric("CAGR 2002–2022", f"{cagr_2002_2022*100:.2f}%")

st.sidebar.subheader("Population scenarios (adjustable)")
st.sidebar.caption("Defaults match the submission run; you can override using the deltas below.")

omani_delta_low = st.sidebar.slider("Low: Omani growth delta (pp)", -2.0, 2.0, -0.35, 0.05) / 100.0
expat_delta_low = st.sidebar.slider("Low: Expat growth delta (pp)", -3.0, 3.0, -0.80, 0.05) / 100.0
omani_delta_high = st.sidebar.slider("High: Omani growth delta (pp)", -2.0, 2.0, 0.35, 0.05) / 100.0
expat_delta_high = st.sidebar.slider("High: Expat growth delta (pp)", -3.0, 3.0, 1.00, 0.05) / 100.0

st.sidebar.subheader("Infrastructure planning parameters")
hh_override = st.sidebar.slider("Household size", 3.5, 9.0, 6.27, 0.1)
beds_per_1000 = st.sidebar.slider("Beds per 1,000 population benchmark", 1.0, 8.0, 3.0, 0.1)

st.sidebar.subheader("Electricity (optional)")
use_electricity = st.sidebar.toggle("Enable electricity module", value=True)
per_capita_elasticity = st.sidebar.slider(
    "Per-capita electricity change to 2040 (total, %)", -30, 60, 0, 5
) / 100.0

years = list(range(2023, 2041))

cap_year, cap_beds = current_bed_capacity(inputs)

scenario_params = {
    "Low": {"omani": omani_growth_base + omani_delta_low, "expat": expat_growth_base + expat_delta_low},
    "Base": {"omani": omani_growth_base, "expat": expat_growth_base},
    "High": {"omani": omani_growth_base + omani_delta_high, "expat": expat_growth_base + expat_delta_high},
}

frames = []
for sc, p in scenario_params.items():
    df = build_projection(inputs, years, omani_growth=p["omani"], expat_growth=p["expat"], anchor_to_observed_through=2025)
    df = add_infrastructure_metrics(df, cap_beds=cap_beds, beds_per_1000=beds_per_1000, hh_size=hh_override)
    df["Scenario"] = sc
    frames.append(df)
all_df = pd.concat(frames, ignore_index=True)

base_2040 = all_df[(all_df["Scenario"] == "Base") & (all_df["Year"] == 2040)].iloc[0]
low_2040 = all_df[(all_df["Scenario"] == "Low") & (all_df["Year"] == 2040)].iloc[0]
high_2040 = all_df[(all_df["Scenario"] == "High") & (all_df["Year"] == 2040)].iloc[0]

st.markdown(
    f"""
<div class="kpi-grid">
  <div class="kpi">
    <div class="label">2040 population range (Low → High)</div>
    <div class="value">{low_2040['Population']:,.0f} – {high_2040['Population']:,.0f}</div>
    <div class="delta">Planning envelope for total service demand</div>
  </div>
  <div class="kpi">
    <div class="label">2040 bed gap range (Low → High)</div>
    <div class="value">{low_2040['Bed_gap']:,.0f} – {high_2040['Bed_gap']:,.0f}</div>
    <div class="delta">BedsDemand − current MOH bed capacity (benchmark: {beds_per_1000:.1f}/1,000)</div>
  </div>
  <div class="kpi">
    <div class="label">MOH bed capacity (latest in workbook)</div>
    <div class="value">{cap_beds:,.0f}</div>
    <div class="delta">Capacity year: {cap_year}</div>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

bp = all_df[(all_df["Scenario"] == "Base") & (all_df["Bed_gap"] > 0)]["Year"]
bp_year = int(bp.min()) if len(bp) else None
with st.container(border=True):
    st.markdown("**System alert**")
    st.write(
        f"Breakpoint year (first year demand exceeds current MOH capacity of {cap_beds:,.0f} beds, capacity year {cap_year}): "
        + (str(bp_year) if bp_year else "No breakpoint through 2040 under these inputs.")
    )

tabs = st.tabs(
    [
        "Dashboard",
        "Population",
        "Healthcare",
        "Housing",
        "Electricity",
        "Data export",
    ]
)

with tabs[0]:
    c1, c2 = st.columns([1.4, 1.0])
    with c1:
        st.plotly_chart(
            px.area(
                all_df,
                x="Year",
                y="Population",
                color="Scenario",
                title="Population scenarios (area)",
            ),
            use_container_width=True,
        )
    with c2:
        pie_df = inputs["gov_dist"].copy()
        pie_df.columns = ["City", "Share"]
        st.plotly_chart(
            px.pie(pie_df, names="City", values="Share", title="Oman population distribution (2024)"),
            use_container_width=True,
        )

    st.plotly_chart(
        fig_capacity_gap_bars(
            all_df,
            "Bed_gap",
            "Healthcare capacity gap snapshots (Beds)",
            "Gap (beds)",
        ),
        use_container_width=True,
    )

    st.plotly_chart(
        fig_capacity_gap_bars(
            all_df,
            "Households_needed",
            "Housing demand snapshots (Households needed)",
            "Households",
        ),
        use_container_width=True,
    )

with tabs[1]:
    st.subheader("Population")
    left, right = st.columns([1.2, 0.8])
    with left:
        st.plotly_chart(
            px.line(all_df, x="Year", y="Population", color="Scenario", title="Population (Low / Base / High)"),
            use_container_width=True,
        )
    with right:
        mf = inputs["male_female"].copy()
        mf["Year"] = mf["Year"].astype(int)
        mf_long = mf.melt(id_vars=["Year"], var_name="Gender", value_name="Share")
        st.plotly_chart(
            px.bar(mf_long, x="Year", y="Share", color="Gender", barmode="group", title="Gender shares (2022–2024)"),
            use_container_width=True,
        )

    st.subheader("Population structure (Omani vs Expat)")
    stacked = all_df[all_df["Scenario"] == "Base"].copy()
    stacked_long = stacked.melt(
        id_vars=["Year"],
        value_vars=["Omani_pop", "Expat_pop"],
        var_name="Group",
        value_name="Population_component",
    )
    st.plotly_chart(
        px.area(
            stacked_long,
            x="Year",
            y="Population_component",
            color="Group",
            title="Base scenario: Omani vs Expat (stacked area)",
        ),
        use_container_width=True,
    )

with tabs[2]:
    st.subheader("Healthcare")
    df_beds = all_df.copy()
    df_beds["Capacity"] = cap_beds
    c1, c2 = st.columns([1.2, 0.8])
    with c1:
        st.plotly_chart(
            px.line(df_beds, x="Year", y="Bed_demand", color="Scenario", title=f"Bed demand (benchmark = {beds_per_1000:.1f} per 1,000)"),
            use_container_width=True,
        )
    with c2:
        st.plotly_chart(
            px.line(df_beds, x="Year", y="Stress_index", color="Scenario", title="Stress index (Demand/Capacity)"),
            use_container_width=True,
        )

    st.plotly_chart(
        fig_capacity_gap_bars(df_beds, "Bed_gap", "Bed gap snapshots", "Gap (beds)"),
        use_container_width=True,
    )

    st.subheader("Stress frequency table (how many years fall into each stress band)")
    freq = (
        df_beds.assign(Stress_band=lambda d: stress_bucket(d["Stress_index"]))
        .groupby(["Scenario", "Stress_band"], observed=False)["Year"]
        .count()
        .reset_index()
        .rename(columns={"Year": "Years_count"})
    )
    st.dataframe(freq, use_container_width=True)

    st.subheader("Private sector context (from workbook)")
    clinics = inputs["private_clinics"].copy()
    clinics["Year"] = clinics["Year"].astype(int)
    clinics_long = clinics.melt(id_vars=["Year"], var_name="Clinic type", value_name="Count")
    st.plotly_chart(
        px.line(clinics_long, x="Year", y="Count", color="Clinic type", title="Muscat private clinics (trend)"),
        use_container_width=True,
    )

    units = inputs["moh_units"].copy()
    units["Year"] = units["Year"].astype(int)
    units_long = units.melt(id_vars=["Year"], var_name="Unit type", value_name="Count")
    st.plotly_chart(
        px.bar(units_long, x="Year", y="Count", color="Unit type", barmode="group", title="MOH health units (historical)"),
        use_container_width=True,
    )

with tabs[3]:
    st.subheader("Housing")
    st.plotly_chart(
        px.line(all_df, x="Year", y="Households_needed", color="Scenario", title=f"Households needed (household size = {hh_override:.2f})"),
        use_container_width=True,
    )

    annual_add = (
        all_df.sort_values(["Scenario", "Year"])
        .assign(Annual_households_added=lambda d: d.groupby("Scenario")["Households_needed"].diff())
        .dropna()
    )
    st.plotly_chart(
        px.histogram(
            annual_add,
            x="Annual_households_added",
            color="Scenario",
            nbins=25,
            barmode="overlay",
            opacity=0.6,
            title="Distribution (histogram): annual additional households required",
        ),
        use_container_width=True,
    )

    st.subheader("Household size proxy (from workbook, Oman-wide)")
    hh = inputs["hh_size"].copy()
    hh["Year"] = hh["Year"].astype(int)
    hh_y = pd.to_numeric(hh["Average Household Size"], errors="coerce")
    hh_x = pd.to_numeric(hh["Year"], errors="coerce")
    mask = (~hh_x.isna()) & (~hh_y.isna())
    x = hh_x[mask].to_numpy(dtype=float)
    y = hh_y[mask].to_numpy(dtype=float)
    if len(x) >= 2:
        m, b = np.polyfit(x, y, 1)
        hh_fit = pd.DataFrame({"Year": sorted(hh["Year"].unique())})
        hh_fit["Fitted"] = m * hh_fit["Year"] + b
        fig_hh = go.Figure()
        fig_hh.add_trace(go.Scatter(x=hh["Year"], y=hh["Average Household Size"], mode="markers", name="Observed"))
        fig_hh.add_trace(go.Scatter(x=hh_fit["Year"], y=hh_fit["Fitted"], mode="lines", name="Linear fit"))
        fig_hh.update_layout(title="Average household size series (workbook) + fitted trend", xaxis_title="Year", yaxis_title="Average household size")
        st.plotly_chart(fig_hh, use_container_width=True)
    else:
        st.plotly_chart(
            px.scatter(hh, x="Year", y="Average Household Size", title="Average household size series (workbook)"),
            use_container_width=True,
        )

with tabs[4]:
    st.subheader("Electricity (optional, Oman sector data scaled to Muscat share)")
    if not use_electricity:
        st.warning("Electricity module disabled in the sidebar.")
    else:
        el_long = parse_electricity(inputs)
        # Use Muscat share of Oman pop (2024) as a scaling proxy for Muscat electricity.
        dist = inputs["gov_dist"].copy()
        dist.columns = ["City", "Share"]
        muscat_share = float(dist.loc[dist["City"].astype(str).str.lower() == "muscat", "Share"].iloc[0])

        # Build Muscat baseline electricity (proxy) for 2023 from Oman sector totals * share.
        el_muscat = el_long.copy()
        el_muscat["Muscat_GWh_proxy"] = el_muscat["GWh"] * muscat_share

        # Convert to per-capita using observed Muscat population for 2023 if available in projection anchor.
        base_pop_2023 = float(all_df[(all_df["Scenario"] == "Base") & (all_df["Year"] == 2023)]["Population"].iloc[0])
        el_muscat["kWh_per_capita_proxy"] = (el_muscat["Muscat_GWh_proxy"] * 1e6) / base_pop_2023

        # Project to 2040 for each scenario assuming per-capita changes linearly to elasticity and population varies by scenario.
        years_el = list(range(2023, 2041))
        out_rows = []
        for sc in ["Low", "Base", "High"]:
            pop_sc = all_df[all_df["Scenario"] == sc][["Year", "Population"]].set_index("Year")["Population"].to_dict()
            for _, r in el_muscat[el_muscat["Year"] == 2023].iterrows():
                sector = str(r["Sector"])
                kwh0 = float(r["kWh_per_capita_proxy"])
                for y in years_el:
                    t = (y - 2023) / (2040 - 2023)
                    kwh = kwh0 * (1 + per_capita_elasticity * t)
                    gwh = (kwh * float(pop_sc[y])) / 1e6
                    out_rows.append({"Scenario": sc, "Year": y, "Sector": sector, "Muscat_GWh_projected": gwh})
        el_proj = pd.DataFrame(out_rows)
        total = el_proj.groupby(["Scenario", "Year"], as_index=False)["Muscat_GWh_projected"].sum()

        c1, c2 = st.columns([1.2, 0.8])
        with c1:
            st.plotly_chart(
                px.line(total, x="Year", y="Muscat_GWh_projected", color="Scenario", title="Projected Muscat electricity (proxy total, GWh)"),
                use_container_width=True,
            )
        with c2:
            pie_2040 = el_proj[(el_proj["Scenario"] == "Base") & (el_proj["Year"] == 2040)].copy()
            st.plotly_chart(
                px.pie(pie_2040, names="Sector", values="Muscat_GWh_projected", title="Base 2040: sector mix (proxy)"),
                use_container_width=True,
            )

        st.plotly_chart(
            px.area(el_proj[el_proj["Scenario"] == "Base"], x="Year", y="Muscat_GWh_projected", color="Sector", title="Base scenario: sector breakdown over time (proxy)"),
            use_container_width=True,
        )

with tabs[5]:
    st.subheader("Data export (all scenarios)")
    export_df = all_df.assign(
        Population=lambda d: d["Population"].round(0).astype(int),
        Bed_demand=lambda d: d["Bed_demand"].round(1),
        Bed_gap=lambda d: d["Bed_gap"].round(1),
        Stress_index=lambda d: d["Stress_index"].round(3),
        Households_needed=lambda d: d["Households_needed"].round(0).astype(int),
    )

    st.dataframe(export_df, use_container_width=True)

    csv_bytes = export_df.to_csv(index=False).encode("utf-8")
    st.download_button("Download results as CSV", data=csv_bytes, file_name="muscat_2040_scenarios_results.csv", mime="text/csv")

st.caption("All inputs are sourced from the provided Excel workbook except the bed benchmark slider (user-defined planning parameter).")

