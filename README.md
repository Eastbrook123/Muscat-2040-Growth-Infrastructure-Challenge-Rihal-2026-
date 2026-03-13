This repository contains the full reproducible analysis and an interactive model for the Muscat 2040 Growth & Infrastructure Challenge. The analysis projects population growth to 2040 and estimates healthcare and housing infrastructure demand pressures under three scenarios: Low, Base, and High growth. 📁 Repository Structure Muscat_2040/ │ ├─ MOH_health_units_data.xlsx # Source data used for all calculations ├─ analysis/ # Python scripts for analysis │ ├─ build_outputs.py # Generates CSV tables for population, healthcare, housing │ └─ make_figures.py # Generates publication-ready figures ├─ outputs/ │ ├─ tables/ # Exported scenario data (population, beds, households) │ └─ figures/ # Charts used in reports and executive summary ├─ streamlit_app/ │ └─ app.py # Interactive model for scenario exploration ├─ requirements.txt # Python dependencies for reproducibility └─ README.md # Project documentation 🔎 Project Overview Objective

Project Muscat Governorate’s population to 2040 under three growth scenarios: Low, Base, High.

Translate population growth into healthcare and housing infrastructure demand.

Identify capacity gaps, stress points, and breakpoint years when current infrastructure will be exceeded.

Provide a policy-ready, interactive model that allows stakeholders to adjust assumptions dynamically.

Data

Primary data: MOH_health_units_data.xlsx

Muscat population (2002–2025)

Omani vs. expatriate population shares (2022–2024)

Oman household size trends (2006–2018)

MOH beds and manpower (2002–2023)

Optional context: private clinics, electricity consumption, Oman population distribution

External references: OECD health benchmarks, Oman National Center for Statistics and Information (NCSI)

🛠 Methodology

Population Projection
Historical CAGR (2002–2022) calculated using Muscat population series.

Component split: Population decomposed into Omani and expatriate groups using recent shares (2022–2024).

Scenario blending: Long-term CAGR and recent component trends combined to produce Low, Base, High growth rates.

Projection period: 2026–2040, with 2022–2025 anchored to observed data.

Healthcare Demand
Benchmark: 3 hospital beds per 1,000 residents (OECD standard).

MOH capacity assumption: Constant at 2023 observed level (1,608 beds).

Outputs: Bed demand, gap vs capacity, stress index (demand/capacity), and breakpoint year when demand exceeds capacity.

Housing Demand
Household size: Oman-wide series used as a proxy for Muscat.

Method: Linear trend extrapolated to 2040, bounded between 3.5–9.0 persons per household.

Outputs: Number of households required by scenario (demand-side).

Interactive Model
Built with Streamlit to allow dynamic scenario exploration.

Adjustable assumptions include:

Population growth rate

Migration rate

Average household size

Model updates population projections, healthcare stress, and housing demand in real time.

📌 Reproducibility

Install dependencies

python -m pip install -r requirements.txt

Generate outputs

python analysis\build_outputs.py python -m analysis.make_figures

Run interactive model

streamlit run streamlit_app\app.py

All outputs are automatically linked to source data and assumptions table (outputs/tables/assumptions_register.csv).

Updating assumptions triggers automatic recalculation of tables, charts, and the interactive model.

🎯 Key Features

Transparent and reproducible workflow from raw data → assumptions → tables → charts → interactive model.

Policy-focused: Highlights infrastructure bottlenecks and long-term planning implications.

Scenario analysis: Low, Base, High population growth scenarios.

Dynamic interactivity: Change assumptions to immediately see the impact on healthcare and housing demand.

📄 Outputs

Tables: Population projections, healthcare demand, housing demand, gaps, and stress indices.

Figures: Population trajectories, healthcare stress index, housing requirements.

Technical appendix: Assumptions, methodology, and calculation logic.

Interactive model: Scenario comparison and sensitivity analysis. Ensures full transparency and reproducibility.
