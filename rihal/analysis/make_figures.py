from __future__ import annotations

import os

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from analysis.config import PATHS


def _ensure_dirs() -> None:
    os.makedirs(PATHS.figures_dir, exist_ok=True)


def plot_population_scenarios() -> str:
    df = pd.read_csv(f"{PATHS.tables_dir}\\population_projection_2023_2040.csv")
    sns.set_theme(style="whitegrid")
    plt.figure(figsize=(10, 5.5))
    sns.lineplot(data=df, x="Year", y="Population", hue="Scenario", linewidth=2.5)
    plt.title("Muscat population projection (2023–2040): Low / Base / High")
    plt.ylabel("Population")
    plt.xlabel("Year")
    plt.tight_layout()
    out = f"{PATHS.figures_dir}\\fig_population_projection.png"
    plt.savefig(out, dpi=200)
    plt.close()
    return out


def plot_bed_demand_gap() -> tuple[str, str]:
    df = pd.read_csv(f"{PATHS.tables_dir}\\healthcare_beds_demand_gap.csv")
    df["Bed_demand_OECD_3_per_1000"] = pd.to_numeric(df["Bed_demand_OECD_3_per_1000"])
    df["MOH_bed_capacity_assumed_constant"] = pd.to_numeric(df["MOH_bed_capacity_assumed_constant"])
    sns.set_theme(style="whitegrid")

    # Demand vs capacity
    plt.figure(figsize=(10, 5.5))
    sns.lineplot(data=df, x="Year", y="Bed_demand_OECD_3_per_1000", hue="Scenario", linewidth=2.5)
    cap = float(df["MOH_bed_capacity_assumed_constant"].iloc[0])
    plt.axhline(cap, color="black", linestyle="--", linewidth=1.5, label="Current MOH capacity (constant)")
    plt.title("Healthcare: hospital bed demand (3 per 1,000) vs current MOH bed capacity")
    plt.ylabel("Beds (demand)")
    plt.xlabel("Year")
    plt.tight_layout()
    out1 = f"{PATHS.figures_dir}\\fig_beds_demand_vs_capacity.png"
    plt.savefig(out1, dpi=200)
    plt.close()

    # Stress index
    plt.figure(figsize=(10, 5.5))
    sns.lineplot(data=df, x="Year", y="Stress_index", hue="Scenario", linewidth=2.5)
    plt.axhline(1.0, color="black", linestyle="--", linewidth=1.5)
    plt.title("Healthcare stress index = Demand / Capacity (breakpoint at 1.0)")
    plt.ylabel("Stress index")
    plt.xlabel("Year")
    plt.tight_layout()
    out2 = f"{PATHS.figures_dir}\\fig_beds_stress_index.png"
    plt.savefig(out2, dpi=200)
    plt.close()

    return out1, out2


def plot_households_needed() -> str:
    df = pd.read_csv(f"{PATHS.tables_dir}\\housing_households_needed.csv")
    sns.set_theme(style="whitegrid")
    plt.figure(figsize=(10, 5.5))
    sns.lineplot(data=df, x="Year", y="Households_needed", hue="Scenario", linewidth=2.5)
    plt.title("Housing: households required (population / assumed household size)")
    plt.ylabel("Households needed")
    plt.xlabel("Year")
    plt.tight_layout()
    out = f"{PATHS.figures_dir}\\fig_households_needed.png"
    plt.savefig(out, dpi=200)
    plt.close()
    return out


def main() -> None:
    _ensure_dirs()
    paths = [
        plot_population_scenarios(),
        *plot_bed_demand_gap(),
        plot_households_needed(),
    ]
    print("Saved figures:")
    for p in paths:
        print(" -", p)


if __name__ == "__main__":
    main()

