# Muscat 2040: Growth & Infrastructure Challenge (Rihal 2026)

This folder contains a fully reproducible analysis and an interactive model built from the provided workbook:

- `MOH_health_units_data.xlsx`

## What’s included

- **Reproducible tables**: `outputs/tables/*.csv`
- **Publication-ready charts**: `outputs/figures/*.png`
- **Interactive model**: `streamlit_app/app.py`

## How to run (Windows / PowerShell)

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Generate tables + charts:

```bash
python analysis\build_outputs.py
python -m analysis.make_figures
```

Run the interactive model:

```bash
streamlit run streamlit_app\app.py
```

