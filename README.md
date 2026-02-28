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

<div align="center">

# Unit Econ Builder

**Model. Measure. Decide.**

A decision-grade unit economics engine for operators and investors who need
answers — not spreadsheets.

[![Python](https://img.shields.io/badge/python-3.7+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/streamlit-1.41+-FF4B4B?style=flat&logo=streamlit&logoColor=white)](https://streamlit.io)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg?style=flat)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen?style=flat)](#testing)

</div>

---

## The Problem

Every growth-stage company asks the same question: **"Is our customer acquisition profitable?"**

The answer lives in unit economics — but building reliable models is tedious. Teams default to fragile spreadsheets, inconsistent assumptions, and metrics that don't travel well across stakeholders.

Unit Econ Builder replaces that workflow with a structured, interactive modeling environment that produces investor-ready outputs in minutes.

---

## What It Does

Unit Econ Builder takes six core inputs and produces a complete profitability picture:

| Input | What It Captures |
|-------|-----------------|
| **Customer Acquisition Cost (CAC)** | Blended cost to acquire one customer |
| **Average Order Value (AOV)** | Revenue per transaction |
| **Orders per Month** | Purchase frequency |
| **Gross Margin %** | Revenue retained after COGS |
| **Variable Cost per Order** | Fulfillment, packaging, delivery |
| **Monthly Churn Rate** | Percentage of customers lost per period |

From these inputs, the engine computes:

| Output | Why It Matters |
|--------|---------------|
| **LTV** | Total expected revenue per customer over their lifetime |
| **Discounted LTV** | Time-value-adjusted LTV using configurable discount rate |
| **LTV:CAC Ratio** | Capital efficiency of acquisition spend (benchmark: 3:1) |
| **Payback Period** | Months to recover CAC — drives cash flow planning |
| **Contribution Margin** | Per-order profit after variable costs |
| **Health Score (0–100)** | Composite index across four weighted dimensions |
| **Expansion Revenue (Skok)** | ARPU growth from upsell/cross-sell, modeled via `a/c + m/c²` |

---

## Quick Start

### Web UI

```bash
pip install -r requirements.txt
streamlit run app.py
```

### CLI (Headless)

Run against any JSON config for scripted pipelines or CI integration:

```bash
python src/model.py --config data/example_dark_store.json
```

```
──────────────────────────────────────────
 Unit Economics Summary
──────────────────────────────────────────
 Contribution Margin / Order:    $5.80
 Monthly Contribution:          $16.24
 LTV (simple):                $203.00
 LTV:CAC:                      11.28x
 Payback Period:              1.1 months
 Health Score:                    93/100
──────────────────────────────────────────
```

---

## Core Capabilities

### 1. KPI Dashboard

Real-time calculation of LTV, LTV:CAC, payback period, contribution margin, and health score — updated instantly as inputs change.

### 2. Health Diagnostics

Automated flags surface risks before they compound:

| Severity | Trigger | Signal |
|----------|---------|--------|
| **Critical** | LTV:CAC < 1.0 | Negative unit economics — every customer acquired destroys value |
| **Warning** | Payback > 18 months | Capital recovery too slow for most funding cycles |
| **Warning** | Contribution margin < 10% of AOV | Margin structure cannot absorb cost volatility |
| **Watch** | Monthly churn > 10% | Retention risk — investigate activation and engagement |
| **Positive** | Negative net churn | Expansion revenue exceeds losses — rare and valuable |

### 3. Cohort LTV Curves

36-month forward projection of a 1,000-customer cohort:
- **Survival curve** — geometric decay at the modeled churn rate
- **Cumulative contribution vs. CAC** — visualizes the payback crossover
- **Monthly revenue trend** — with optional ARPU expansion

### 4. Sensitivity Analysis

- **Tornado chart** — ranks lever impact from a 10% improvement in each variable
- **Single-lever sweep** — charts LTV:CAC across a ±40% range for any selected parameter

### 5. Export

Download investor-ready artifacts:
- JSON summary (inputs + computed outputs)
- LTV cohort curve as CSV

---

## Analytical Framework

### Contribution Margin

```
CM/order = (AOV × Gross Margin %) − Variable Cost/Order
```

### Customer Lifetime Value

**Simple model** (constant churn, no expansion):

```
LTV = Monthly Contribution / Monthly Churn Rate
```

**Skok model** (with expansion revenue):

```
LTV = a/c + m/c²
```

Where `a` = base monthly contribution, `m` = monthly ARPU growth in dollars, `c` = monthly churn rate. This formulation captures the compounding effect of upsell and cross-sell within retained cohorts.

### Discounted LTV

Applies a monthly discount rate derived from an annual rate to sum present-value cash flows over the expected customer lifetime:

```
DLTV = Σ (Survivorsₜ × MC) / (1 + r)ᵗ    for t ∈ [1, lifetime_months]
```

### Health Score

Composite of four equally-weighted dimensions (25 points each):

| Dimension | Full Score (25) | Proportional | Zero |
|-----------|:-:|:-:|:-:|
| LTV:CAC ratio | ≥ 3.0 | 1.0 – 3.0 | < 1.0 |
| Payback period | ≤ 6 months | 6 – 18 months | > 18 |
| Contribution margin | ≥ $5.00 | $0 – $5.00 | ≤ $0 |
| Monthly contribution | ≥ $15.00 | $0 – $15.00 | ≤ $0 |

Full methodology: [`docs/methodology.md`](docs/methodology.md)

---

## Example Scenarios

Two presets are included to demonstrate the model across business types:

| Metric | Dark Store Delivery | B2B SaaS |
|--------|:--:|:--:|
| CAC | $18 | $350 |
| AOV | $34 | $99 |
| Orders / Month | 2.8 | 1.0 |
| Gross Margin | 30% | 82% |
| Variable Cost / Order | $4.20 | $5.00 |
| Monthly Churn | 8% | 3% |
| | | |
| **LTV** | **~$203** | **~$2,527** |
| **LTV:CAC** | **~11.3x** | **~7.2x** |
| **Payback** | **~1.1 mo** | **~4.6 mo** |
| **Health Score** | **93** | **100** |

The dark store model wins on payback speed. The SaaS model wins on absolute LTV. Both clear the 3:1 benchmark comfortably — but for different structural reasons.

---

## Architecture

```
unit-econ-builder/
│
├── app.py                        Streamlit UI — sidebar inputs, KPI cards, tabbed views
│
├── src/
│   ├── model.py                  Pure-Python calculation engine (no framework deps)
│   ├── cohorts.py                36-month cohort simulation & payback detection
│   ├── sensitivity.py            Tornado + single-lever sweep analysis
│   ├── health.py                 Diagnostic flag rendering & severity sorting
│   └── export.py                 JSON/CSV serialization utilities
│
├── data/
│   ├── example_dark_store.json   Quick-commerce preset
│   └── example_saas.json         B2B SaaS preset
│
├── tests/
│   └── test_model.py             13 test classes, 3 fixture scenarios
│
└── docs/
    └── methodology.md            Formulas, scoring, and model assumptions
```

**Design decisions:**

- **Separation of calculation from presentation.** `src/model.py` has zero Streamlit imports — it runs standalone via CLI and is independently testable.
- **Dataclass contracts.** `UnitEconInputs` and `UnitEconOutputs` provide typed, self-documenting interfaces between layers.
- **Modular analysis.** Cohort simulation, sensitivity analysis, and health diagnostics are isolated modules — swap or extend without touching the core engine.

---

## Testing

```bash
python -m pytest tests/ -v
```

Coverage spans all core calculations across three fixture scenarios:

| Fixture | Purpose |
|---------|---------|
| `dark_store_inputs` | Healthy quick-commerce economics |
| `bad_economics_inputs` | Intentionally unprofitable — validates critical flags |
| `high_churn_inputs` | 15% monthly churn — validates retention warnings |

Tests validate contribution margins, LTV calculations (simple and Skok), payback periods, health scores, diagnostic flags, expansion revenue, and full `compute()` integration.

---

## Deployment

This repo includes HuggingFace Spaces configuration. Push to a Space repo and it auto-deploys — no Docker, no infra.

For local development, the Streamlit server runs headless on port 7860 by default (configurable in `.streamlit/config.toml`).

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Web framework | Streamlit |
| Visualization | Plotly |
| Data manipulation | Pandas |
| Numerical engine | NumPy |
| Testing | pytest |

---

## Known Limitations

- Churn is modeled as constant (no cohort-vintage curves or improving retention)
- Fixed costs are captured as an input but excluded from per-customer LTV
- Single-geography, single-segment model — no multi-cohort blending
- No Monte Carlo or probabilistic scenario modeling (deterministic only)

These are intentional scope boundaries, not oversights. The goal is a sharp, reliable tool — not a general-purpose financial model.

---

<div align="center">

**Built for operators who measure what matters.**

</div>
