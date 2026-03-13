import pandas as pd


def main() -> None:
    base = r"c:\Users\musafa\OneDrive\Desktop\rihal\outputs\tables"
    proj = pd.read_csv(f"{base}\\population_projection_2023_2040.csv")
    health = pd.read_csv(f"{base}\\healthcare_beds_demand_gap.csv")
    housing = pd.read_csv(f"{base}\\housing_households_needed.csv")

    def val(df: pd.DataFrame, scenario: str, year: int, col: str) -> float:
        return float(df[(df["Scenario"] == scenario) & (df["Year"] == year)][col].iloc[0])

    cap = float(health["Current_capacity_moh_beds"].iloc[0])
    cap_year = int(health["Current_capacity_year"].iloc[0])
    print(f"MOH bed capacity (assumed constant): {cap:.0f} beds (capacity year {cap_year})")

    for sc in ["Low", "Base", "High"]:
        p2040 = val(proj, sc, 2040, "Population")
        bd2040 = val(health, sc, 2040, "Bed_demand_OECD_3_per_1000")
        gap2040 = val(health, sc, 2040, "Bed_gap")
        stress2040 = val(health, sc, 2040, "Stress_index")
        bp_s = health[health["Scenario"] == sc]["Breakpoint_year_demand_exceeds_capacity"].dropna()
        bp = int(bp_s.iloc[0]) if len(bp_s) else None
        hh2040 = val(housing, sc, 2040, "Households_needed")
        print(
            f"{sc}: Pop2040={p2040:,.0f} | Beds2040={bd2040:,.0f} | Gap2040={gap2040:,.0f} | "
            f"Stress2040={stress2040:.2f} | Breakpoint={bp} | HH2040={hh2040:,.0f}"
        )


if __name__ == "__main__":
    main()

