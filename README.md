---
title: Unit Econ Builder
emoji: 📊
colorFrom: blue
colorTo: indigo
sdk: streamlit
sdk_version: "1.41.0"
app_file: app.py
pinned: false
license: mit
---

# unit-econ-builder

A Streamlit web app for interactive unit economics modeling. Calculate LTV, LTV:CAC, payback periods, and run sensitivity analysis across your key business levers.

## Quick Start

```bash
pip install -r requirements.txt
streamlit run app.py
```

## CLI Mode

Run the model from the command line with a JSON config:

```bash
python src/model.py --config data/example_dark_store.json
```

## Features

- **KPI Dashboard** — LTV, LTV:CAC, payback period, contribution margin, health score
- **Health Diagnostics** — Color-coded flags (critical / warning / watch) based on metric thresholds
- **Cohort LTV Curves** — Cumulative contribution vs CAC, survival curves, monthly revenue
- **Sensitivity Analysis** — Tornado chart ranking lever impact, single-lever sweep across ±40%
- **Export** — Download JSON summary and LTV curve CSV

## Project Structure

```
app.py                      Streamlit entry point
src/
  model.py                  Core calculations (pure Python, independently testable)
  sensitivity.py            Sensitivity analysis (tornado + sweep)
  cohorts.py                Cohort LTV curve generation
  health.py                 Diagnostic flag helpers
  export.py                 CSV/JSON export utilities
data/
  example_dark_store.json   Dark store delivery preset
  example_saas.json         B2B SaaS preset
tests/
  test_model.py             Unit tests for core calculations
docs/
  methodology.md            Formulas and scoring methodology
```

## Example Presets

| Preset | CAC | AOV | Orders/mo | Gross Margin | Var. Cost | Churn |
|--------|-----|-----|-----------|--------------|-----------|-------|
| Dark Store | $18 | $34 | 2.8 | 30% | $4.20 | 8% |
| B2B SaaS | $350 | $99 | 1.0 | 82% | $5.00 | 3% |

## Tests

```bash
python -m pytest tests/ -v
```

## Deploy to HuggingFace Spaces

This repo includes a HuggingFace Spaces config. Push to a Space repo and it will auto-deploy.

## Tech Stack

Streamlit, Plotly, Pandas, NumPy
