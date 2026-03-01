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

A guided unit economics simulator for operators and investors who need
answers — not spreadsheets. Think TurboTax for unit economics: one decision
at a time, instant impact, full control.

[![Python](https://img.shields.io/badge/python-3.7+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/streamlit-1.41+-FF4B4B?style=flat&logo=streamlit&logoColor=white)](https://streamlit.io)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg?style=flat)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen?style=flat)](#testing)

</div>

---

## The Problem

Every growth-stage company asks the same question: **"Is our customer acquisition profitable?"**

The answer lives in unit economics — but building reliable models is tedious. Teams default to fragile spreadsheets, inconsistent assumptions, and metrics that don't travel well across stakeholders.

Unit economics is inherently sequential — every number feeds the next — but if you dump all the levers on screen at once, even an MBA freezes. The fix isn't removing complexity, it's **revealing it progressively**.

Unit Econ Builder walks you through a 5-stage guided simulation that produces investor-ready outputs in minutes.

---

## How It Works — The 5-Stage Journey

### Stage 1 — "What's your business?"

Pick a template archetype — **Delivery Marketplace**, **SaaS Marketplace**, **Services Marketplace**, or **Custom** — and start with sensible defaults and a labeled P&L structure. Nobody starts from a blank screen.

### Stage 2 — "Set your assumptions"

Walk through each layer of the unit economics stack, one card at a time:

| Layer | What You Set | Example Context |
|-------|-------------|-----------------|
| **Demand** | AOV, orders/month | "DoorDash averages $30–45 per order" |
| **Revenue & Margins** | Gross margin % (take rate) | "Delivery: 25–35%. SaaS: 70–85%." |
| **Variable Costs** | Fulfillment cost per order | "Quick commerce: $3–6/order" |
| **Retention** | Monthly churn, ARPU growth | "Best-in-class delivery: 5–8% churn" |
| **Fixed Costs & Acquisition** | Overhead, channel-level CAC | "Blend across paid, organic, referral" |

Each slider shows a **typical range indicator** and a one-sentence explainer. The education is embedded in the input, not in a separate tutorial.

### Stage 3 — "Your unit economics snapshot"

One clean **waterfall chart** showing revenue flowing down to contribution margin per order. Green for revenue, red for costs, bold for margin. Below the waterfall: **CM/order**, **CM%**, and **orders to breakeven** at current fixed costs.

### Stage 4 — "What if?"

Pull one lever at a time and watch the waterfall change. Pre-built scenarios:

- "What if AOV increases 15%?"
- "What if delivery cost drops $1.50 per order?"
- "What if you batch 2 orders per delivery run?"
- "What if spoilage doubles?"
- "What if churn drops to 5%?"

Each scenario shows a **side-by-side waterfall** (before/after) and a **plain-English summary**: *"Batching 2 orders per run improves contribution margin from $6.00 to $8.10 per order, reaching breakeven at 1,481 orders/month instead of 2,000."*

### Stage 5 — "Your playbook"

Auto-generated executive summary: your model, your most sensitive levers (**tornado chart**), and the 2–3 moves that get you to profitability fastest. **Exportable as PDF, JSON, or CSV.** This is the thing people screenshot and share.

---

## What It Computes

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

## Health Diagnostics

Automated flags surface risks at every stage:

| Severity | Trigger | Signal |
|----------|---------|--------|
| **Critical** | LTV:CAC < 1.0 | Negative unit economics — every customer acquired destroys value |
| **Warning** | Payback > 18 months | Capital recovery too slow for most funding cycles |
| **Warning** | Contribution margin < 10% of AOV | Margin structure cannot absorb cost volatility |
| **Watch** | Monthly churn > 10% | Retention risk — investigate activation and engagement |
| **Positive** | Negative net churn | Expansion revenue exceeds losses — rare and valuable |

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

## Archetype Templates

Four templates are included, each with pre-loaded defaults, typical ranges, and contextual help:

| Template | AOV | GM% | Var Cost | Churn | Example |
|----------|:---:|:---:|:--------:|:-----:|---------|
| **Delivery Marketplace** | $34 | 30% | $4.20 | 8% | DoorDash, Gopuff |
| **SaaS Marketplace** | $99 | 82% | $5.00 | 3% | B2B subscriptions |
| **Services Marketplace** | $150 | 45% | $12.00 | 6% | Thumbtack, TaskRabbit |
| **Custom** | $50 | 40% | $5.00 | 7% | Start from balanced defaults |

Select an archetype in Stage 1 to load sensible defaults. Every value is adjustable in Stage 2.

---

## Architecture

```
unit-econ-builder/
│
├── app.py                        Orchestrator — session state, progress bar, stage dispatch
│
├── stages/                       Journey UI (one module per stage)
│   ├── __init__.py               Navigation helpers, progress bar renderer
│   ├── stage1_archetype.py       "What's your business?" — template selection
│   ├── stage2_assumptions.py     "Set your assumptions" — layer-by-layer input cards
│   ├── stage3_snapshot.py        "Your snapshot" — waterfall chart + KPIs
│   ├── stage4_whatif.py          "What if?" — scenario comparison
│   └── stage5_playbook.py        "Your playbook" — recommendations + export
│
├── src/                          Calculation engine (zero Streamlit imports)
│   ├── model.py                  Core engine: UnitEconInputs → UnitEconOutputs
│   ├── waterfall.py              Waterfall chart data builder (Plotly go.Waterfall)
│   ├── scenarios.py              Pre-built what-if scenarios + impact summaries
│   ├── playbook.py               Recommendation engine + PDF export (fpdf2)
│   ├── cohorts.py                36-month cohort simulation & payback detection
│   ├── sensitivity.py            Tornado + single-lever sweep analysis
│   ├── health.py                 Diagnostic flag rendering & severity sorting
│   └── export.py                 JSON/CSV serialization utilities
│
├── data/
│   ├── archetypes/               Template configs (model inputs + UI metadata)
│   │   ├── delivery_marketplace.json
│   │   ├── saas_marketplace.json
│   │   ├── services_marketplace.json
│   │   └── custom.json
│   ├── example_dark_store.json   Legacy preset (CLI-compatible)
│   └── example_saas.json         Legacy preset (CLI-compatible)
│
├── tests/
│   ├── test_model.py             Core calculation tests (25 tests)
│   ├── test_waterfall.py         Waterfall chart tests (11 tests)
│   └── test_scenarios.py         Scenario engine tests (11 tests)
│
└── docs/
    └── methodology.md            Formulas, scoring, and model assumptions
```

**Design decisions:**

- **Guided journey, not a dashboard.** `app.py` is a ~55-line orchestrator that routes to stage modules based on `st.session_state.stage`. Users progress linearly but can navigate back at any time.
- **Separation of calculation from presentation.** `src/model.py` has zero Streamlit imports — it runs standalone via CLI and is independently testable.
- **Dataclass contracts.** `UnitEconInputs` and `UnitEconOutputs` provide typed, self-documenting interfaces between layers.
- **Modular analysis.** Waterfall charts, scenarios, sensitivity analysis, and health diagnostics are isolated modules — swap or extend without touching the core engine.

---

## Testing

```bash
python -m pytest tests/ -v
```

47 tests across three test modules:

| Module | Tests | Coverage |
|--------|:-----:|---------|
| `test_model.py` | 25 | Core calculations: CM, LTV (simple + Skok), payback, health score, flags, expansion revenue |
| `test_waterfall.py` | 11 | Waterfall data structure, value correctness, figure generation |
| `test_scenarios.py` | 11 | Scenario application, impact summaries, all pre-built scenarios |

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
| PDF export | fpdf2 |
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

**Built for operators who measure what matters. One stage at a time.**

</div>
