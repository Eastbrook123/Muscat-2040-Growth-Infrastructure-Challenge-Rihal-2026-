# Muscat 2040: Growth & Infrastructure Challenge

> **Rihal 2026** — Full reproducible analysis and interactive model for Muscat Governorate population projections and infrastructure demand (healthcare, housing, electricity).

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-Interactive%20Dashboard-FF4B4B.svg)](https://streamlit.io/)

---

## Overview

This repository contains the complete analysis and interactive dashboard for the **Muscat 2040 Growth & Infrastructure Challenge**. It projects Muscat Governorate's population to 2040 under three scenarios (Low, Base, High) and translates growth into **healthcare** and **housing** infrastructure demand pressures.

### Objectives

- **Project** Muscat population to 2040 under Low, Base, and High growth scenarios
- **Translate** population growth into healthcare bed demand and housing household requirements
- **Identify** capacity gaps, stress indices, and breakpoint years when current infrastructure is exceeded
- **Provide** a policy-ready, interactive model for stakeholders to adjust assumptions dynamically

---

## Repository Structure

```
Muscat-2040-Rihal/
├── rihal/
│   ├── MOH_health_units_data.xlsx    # Source data (population, beds, household size, etc.)
│   ├── analysis/                     # Python analysis scripts
│   │   ├── build_outputs.py          # Generates CSV tables (population, healthcare, housing)
│   │   ├── make_figures.py           # Generates publication-ready figures
│   │   ├── build_pdfs.py             # Exports executive summary & technical appendix as PDF
│   │   └── config.py                # Paths and sheet mappings
│   ├── outputs/
│   │   ├── tables/                   # Exported scenario data (CSV)
│   │   ├── figures/                  # Charts (PNG)
│   │   ├── Muscat_2040_Executive_Summary.pdf
│   │   └── Muscat_2040_Technical_Appendix_and_Logic.pdf
│   ├── streamlit_app/
│   │   ├── app.py                    # Interactive dashboard
│   │   └── style.css                 # Custom theme and layout
│   ├── requirements.txt
│   └── README.md
└── README.md
```

---

## Data Sources

| Source | Description |
|--------|-------------|
| **MOH_health_units_data.xlsx** | Primary workbook: Muscat population (2002–2025), Omani/expat shares (2022–2024), household size (2006–2018), MOH beds & manpower (2002–2023), private clinics, electricity, governorate distribution |
| [OECD Hospital Beds](https://www.oecd.org/en/data/indicators/hospital-beds.html) | Benchmark definition (3 beds per 1,000 residents) |
| [OECD Health at a Glance](https://www.oecd.org/en/publications/health-at-a-glance-2023_7a7afb35-en/full-report/hospital-beds-and-occupancy_10add5df.html) | Cross-country context |
| [Oman NCSI](https://data.ncsi.gov.om/?q=dataset%2Ftotal-population) | Official population data portal |

---

## Methodology

### Population Projection

- **Historical CAGR** (2002–2022) computed from Muscat population series
- **Component split**: Omani vs. expatriate using 2022–2024 shares
- **Scenario blending**: Long-run CAGR + recent component trends → Low, Base, High growth rates
- **Anchoring**: 2022–2025 use observed totals; 2026–2040 use projected components

### Healthcare Demand

- **Benchmark**: 3 hospital beds per 1,000 residents (OECD planning standard)
- **Capacity**: MOH Muscat beds held constant at 2023 level (1,608 beds)
- **Outputs**: Bed demand, gap vs. capacity, stress index (demand/capacity), breakpoint year

### Housing Demand

- **Household size**: Oman-wide series as proxy; linear trend extrapolated to 2040 (bounded 3.5–9.0)
- **Outputs**: Households required by scenario (demand-side)

### Interactive Model

- **Built with Streamlit** — sliders for Omani/expat growth deltas, household size, beds per 1,000
- **Real-time updates**: Population, healthcare stress, housing demand, electricity proxy
- **Tabs**: Dashboard, Population, Healthcare, Housing, Electricity, Data export

---

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/Eastbrook123/Muscat-2040-Growth-Infrastructure-Challenge-Rihal-2026-.git
cd Muscat-2040-Growth-Infrastructure-Challenge-Rihal-2026-/rihal
```

### 2. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 3. Generate tables and figures (optional)

```bash
python analysis\build_outputs.py
python -m analysis.make_figures
python analysis\build_pdfs.py
```

### 4. Run the interactive dashboard

```bash
streamlit run streamlit_app\app.py
```

Then open **http://localhost:8501** in your browser.

---

## Key Features

| Feature | Description |
|---------|-------------|
| **Transparent workflow** | Raw data → assumptions → tables → charts → interactive model |
| **Policy-focused** | Highlights infrastructure bottlenecks and long-term planning implications |
| **Scenario analysis** | Low, Base, High population growth with adjustable deltas |
| **Dynamic interactivity** | Change assumptions and see immediate impact on healthcare and housing demand |
| **Methodology & formulas** | Expandable section with LaTeX formulas and data source links |
| **Export-ready** | CSV download, PDF executive summary, technical appendix |

---

## Outputs

- **Tables**: `outputs/tables/` — population projections, healthcare demand/gap, housing households
- **Figures**: `outputs/figures/` — population trajectories, bed demand vs. capacity, stress index, households
- **PDFs**: Executive summary (≤2 pages), technical appendix with assumptions and calculation logic
- **Interactive model**: Scenario comparison, sensitivity analysis, downloadable results

---

## Acknowledgments

- **Rihal 2026** for the challenge brief
- **Oman NCSI** and **OECD** for reference data and benchmarks
- **Streamlit** and **Plotly** for the interactive visualization stack
