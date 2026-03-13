from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

try:
    # When run as a module: python -m analysis.build_outputs
    from analysis.config import PATHS, SHEETS
except ModuleNotFoundError:
    # When run as a script: python analysis\build_outputs.py
    from config import PATHS, SHEETS


def _cagr(start: float, end: float, years: int) -> float:
    if start <= 0 or end <= 0 or years <= 0:
        return float("nan")
    return (end / start) ** (1 / years) - 1


def _linear_fit_year_to_value(df: pd.DataFrame, year_col: str, value_col: str) -> tuple[float, float]:
    """
    Fit value = a + b*year using least squares, returning (a, b).
    """
    d = df[[year_col, value_col]].dropna().copy()
    x = d[year_col].astype(float).to_numpy()
    y = d[value_col].astype(float).to_numpy()
    b, a = np.polyfit(x, y, 1)
    return float(a), float(b)


@dataclass(frozen=True)
class ScenarioParams:
    name: str
    omani_growth: float  # annual
    expat_growth: float  # annual (migration-heavy)


def load_inputs() -> dict[str, pd.DataFrame]:
    wb = PATHS.workbook
    out: dict[str, pd.DataFrame] = {}
    for k, sheet in SHEETS.items():
        out[k] = pd.read_excel(wb, sheet_name=sheet)
    return out


def build_population_projection(inputs: dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, dict]:
    pop = inputs["population"].rename(columns={"Muscat Population": "population"}).copy()
    pop["Year"] = pop["Year"].astype(int)
    pop = pop.sort_values("Year")

    # Baseline CAGR as requested (2002–2022)
    pop_2002 = float(pop.loc[pop["Year"] == 2002, "population"].iloc[0])
    pop_2022 = float(pop.loc[pop["Year"] == 2022, "population"].iloc[0])
    cagr_2002_2022 = _cagr(pop_2002, pop_2022, 2022 - 2002)

    shares = (
        inputs["omani_expat"]
        .rename(columns={"Expart": "expat_share", "Omani": "omani_share"})
        .copy()
    )
    shares["Year"] = shares["Year"].astype(int)

    # Use 2022–2024 shares to split totals into Omani/Expat counts (migration adjustment channel).
    pop_sh = pop.merge(shares, on="Year", how="left")
    for col in ["expat_share", "omani_share"]:
        pop_sh[col] = pop_sh[col].astype(float)
    pop_sh["expat_pop"] = pop_sh["population"] * pop_sh["expat_share"]
    pop_sh["omani_pop"] = pop_sh["population"] * pop_sh["omani_share"]

    # Recent component growth (2022→2024) to inform migration adjustment.
    o22 = float(pop_sh.loc[pop_sh["Year"] == 2022, "omani_pop"].iloc[0])
    o24 = float(pop_sh.loc[pop_sh["Year"] == 2024, "omani_pop"].iloc[0])
    e22 = float(pop_sh.loc[pop_sh["Year"] == 2022, "expat_pop"].iloc[0])
    e24 = float(pop_sh.loc[pop_sh["Year"] == 2024, "expat_pop"].iloc[0])
    omani_cagr_recent = _cagr(o22, o24, 2)
    expat_cagr_recent = _cagr(e22, e24, 2)

    # Blend long-run CAGR with recent component trends (keeps assumptions transparent & stable).
    blend_recent = 0.35
    omani_growth_base = (1 - blend_recent) * cagr_2002_2022 + blend_recent * omani_cagr_recent
    expat_growth_base = (1 - blend_recent) * cagr_2002_2022 + blend_recent * expat_cagr_recent

    scenarios = [
        ScenarioParams("Low", omani_growth=max(0.0, omani_growth_base - 0.0035), expat_growth=expat_growth_base - 0.0080),
        ScenarioParams("Base", omani_growth=omani_growth_base, expat_growth=expat_growth_base),
        ScenarioParams("High", omani_growth=omani_growth_base + 0.0035, expat_growth=expat_growth_base + 0.0100),
    ]

    # Anchor to observed totals for 2023–2025 (same across scenarios), then project 2026–2040 by components.
    anchor_years = [2022, 2023, 2024, 2025]
    anchor = pop[pop["Year"].isin(anchor_years)].set_index("Year")["population"].to_dict()

    # For component split anchor, use latest available shares (2024) and hold shares dynamic via linear trend.
    share_a_expat, share_b_expat = _linear_fit_year_to_value(shares, "Year", "expat_share")
    share_a_omani, share_b_omani = _linear_fit_year_to_value(shares, "Year", "omani_share")

    # Start components at 2025 using 2024 shares applied to 2025 total (closest available).
    expat_share_2025 = float(share_a_expat + share_b_expat * 2025)
    expat_share_2025 = float(np.clip(expat_share_2025, 0.0, 1.0))
    omani_share_2025 = 1.0 - expat_share_2025
    base_total_2025 = float(anchor[2025])
    base_expat_2025 = base_total_2025 * expat_share_2025
    base_omani_2025 = base_total_2025 * omani_share_2025

    years = list(range(2023, 2041))
    rows = []
    for sc in scenarios:
        exp = base_expat_2025
        om = base_omani_2025
        for y in years:
            if y <= 2025:
                total = float(anchor[y])
            else:
                exp *= 1 + sc.expat_growth
                om *= 1 + sc.omani_growth
                total = exp + om
            rows.append({"Year": y, "Scenario": sc.name, "Population": total})

    proj = pd.DataFrame(rows)

    assumptions = {
        "cagr_2002_2022": cagr_2002_2022,
        "omani_cagr_2022_2024": omani_cagr_recent,
        "expat_cagr_2022_2024": expat_cagr_recent,
        "blend_recent_weight": blend_recent,
        "omani_growth_base": omani_growth_base,
        "expat_growth_base": expat_growth_base,
        "scenario_params": {s.name: {"omani_growth": s.omani_growth, "expat_growth": s.expat_growth} for s in scenarios},
        "anchor_years_observed": anchor_years,
        "component_split_anchor": {"year": 2025, "expat_share_used": expat_share_2025},
    }
    return proj, assumptions


def build_healthcare_demand(inputs: dict[str, pd.DataFrame], proj: pd.DataFrame, beds_per_1000: float = 3.0) -> pd.DataFrame:
    beds = inputs["moh_beds_manpower"].rename(
        columns={"Muscat number of beds in MOH Hospitals": "moh_beds", "Oman health manpower": "oman_health_manpower"}
    ).copy()
    beds["Year"] = beds["Year"].astype(int)
    current_year = int(beds["Year"].max())
    current_capacity = float(beds.loc[beds["Year"] == current_year, "moh_beds"].iloc[0])

    df = proj.copy()
    df["Bed_demand_OECD_3_per_1000"] = df["Population"] * (beds_per_1000 / 1000.0)
    df["MOH_bed_capacity_assumed_constant"] = current_capacity
    df["Bed_gap"] = df["Bed_demand_OECD_3_per_1000"] - df["MOH_bed_capacity_assumed_constant"]
    df["Stress_index"] = df["Bed_demand_OECD_3_per_1000"] / df["MOH_bed_capacity_assumed_constant"]

    # Breakpoint year: first year demand exceeds capacity.
    breakpoints = (
        df[df["Bed_gap"] > 0]
        .groupby("Scenario")["Year"]
        .min()
        .reset_index()
        .rename(columns={"Year": "Breakpoint_year_demand_exceeds_capacity"})
    )
    df = df.merge(breakpoints, on="Scenario", how="left")
    df["Current_capacity_year"] = current_year
    df["Current_capacity_moh_beds"] = current_capacity
    return df


def build_housing_demand(inputs: dict[str, pd.DataFrame], proj: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    hh = inputs["hh_size"].rename(columns={"Average Household Size": "hh_size"}).copy()
    hh["Year"] = hh["Year"].astype(int)

    # Household-size model: linear fit on available years (Oman-wide), used as proxy for Muscat.
    a, b = _linear_fit_year_to_value(hh, "Year", "hh_size")
    df = proj.copy()
    df["hh_size_assumed"] = (a + b * df["Year"]).clip(lower=3.5, upper=9.0)
    df["Households_needed"] = df["Population"] / df["hh_size_assumed"]

    assumptions = {
        "hh_size_source_years": hh["Year"].tolist(),
        "hh_size_linear_fit": {"intercept_a": a, "slope_b_per_year": b},
        "hh_size_clamp": {"min": 3.5, "max": 9.0},
        "note": "Average household size is Oman-wide (not Muscat-specific) and used as proxy due to data availability in workbook.",
    }
    return df, assumptions


def main() -> None:
    inputs = load_inputs()

    proj, pop_assumptions = build_population_projection(inputs)
    proj_out = proj.copy()
    proj_out["Population"] = proj_out["Population"].round(0).astype("int64")
    proj_out.to_csv(f"{PATHS.tables_dir}\\population_projection_2023_2040.csv", index=False)

    health = build_healthcare_demand(inputs, proj, beds_per_1000=3.0)
    health_out = health.copy()
    for c in ["Bed_demand_OECD_3_per_1000", "MOH_bed_capacity_assumed_constant", "Bed_gap", "Stress_index"]:
        health_out[c] = health_out[c].astype(float)
    health_out.to_csv(f"{PATHS.tables_dir}\\healthcare_beds_demand_gap.csv", index=False)

    housing, housing_assumptions = build_housing_demand(inputs, proj)
    housing_out = housing.copy()
    housing_out["Households_needed"] = housing_out["Households_needed"].round(0).astype("int64")
    housing_out["hh_size_assumed"] = housing_out["hh_size_assumed"].round(2)
    housing_out.to_csv(f"{PATHS.tables_dir}\\housing_households_needed.csv", index=False)

    # Save assumptions as a single JSON-like table (CSV) for transparency.
    assumptions_rows = []
    for k, v in pop_assumptions.items():
        assumptions_rows.append({"section": "population_projection", "assumption": k, "value": str(v)})
    for k, v in housing_assumptions.items():
        assumptions_rows.append({"section": "housing", "assumption": k, "value": str(v)})
    pd.DataFrame(assumptions_rows).to_csv(f"{PATHS.tables_dir}\\assumptions_register.csv", index=False)

    print("Wrote tables to:", PATHS.tables_dir)


if __name__ == "__main__":
    main()

