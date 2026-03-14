# Muscat 2040 — Rihal Project (rihal/)

This folder contains the core analysis and interactive model. See the [root README](../README.md) for full documentation.

## Quick run

```bash
# From this folder (rihal/)
python -m pip install -r requirements.txt
streamlit run streamlit_app\app.py
```

## Contents

| Path | Description |
|------|-------------|
| `MOH_health_units_data.xlsx` | Source workbook |
| `analysis/` | Scripts: `build_outputs.py`, `make_figures.py`, `build_pdfs.py` |
| `outputs/tables/` | CSV exports |
| `outputs/figures/` | PNG charts |
| `streamlit_app/` | Interactive dashboard |
