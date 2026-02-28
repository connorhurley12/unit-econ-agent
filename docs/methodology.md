# Unit Economics Methodology

## Core Formulas

### Contribution Margin per Order

```
Contribution Margin = (AOV × Gross Margin %) − Variable Cost per Order
```

This is the profit per order after deducting COGS and variable fulfillment costs.

### Monthly Contribution per Customer

```
Monthly Contribution = Contribution Margin × Orders per Month
```

The net dollars each active customer contributes per month before fixed costs.

### Customer Lifetime Value (LTV)

```
LTV = Monthly Contribution × (1 / Monthly Churn Rate)
```

Uses the simple geometric model where `1 / churn` is the expected customer lifetime in months. This assumes constant churn over time (exponential decay).

### LTV : CAC Ratio

```
LTV:CAC = LTV / CAC
```

Industry benchmark: a ratio of **3:1** is considered healthy. Below 1:1 means you lose money on every customer acquired.

### Payback Period

```
Payback Months = CAC / Monthly Contribution
```

How many months of customer activity it takes to recoup the acquisition cost. Shorter is better; under 12 months is generally considered good.

## Health Score (0–100)

The health score is a composite of four equally-weighted components (25 points each):

| Component | Full Score (25) | Proportional | Zero |
|-----------|----------------|--------------|------|
| LTV:CAC ratio | ≥ 3.0 | 1.0 – 3.0 | < 1.0 |
| Payback period | ≤ 6 months | 6 – 18 months | > 18 months |
| Contribution margin/order | ≥ $5.00 | $0 – $5.00 | ≤ $0 |
| Monthly contribution | ≥ $15.00 | $0 – $15.00 | ≤ $0 |

## Diagnostic Flags

| Severity | Condition | Meaning |
|----------|-----------|---------|
| **Critical** | LTV:CAC < 1.0 | You lose money on every customer |
| **Warning** | Payback > 18 months | Slow capital recovery |
| **Warning** | Contribution margin < 10% of AOV | Dangerously thin margins |
| **Watch** | Monthly churn > 10% | Retention risk |

## Sensitivity Analysis

The tornado chart measures the impact of a **10% improvement** in each lever on LTV:CAC. For cost levers (CAC, variable cost, churn), "improvement" means a 10% *reduction*.

The single-lever sweep charts LTV:CAC across a **±40%** range for the selected parameter.

## Cohort Model

The cohort simulation starts with 1,000 customers and applies geometric churn month over month:

```
Survivors(month) = Initial × (1 − Churn Rate)^month
```

Monthly revenue and contribution are computed for each month, and cumulative contribution is compared against total CAC to find the payback crossover point.

## Limitations

- Assumes constant churn (no improving/worsening retention curves)
- Does not account for expansion revenue or upsell
- Fixed costs are tracked as an input but not factored into per-customer LTV
- Simple single-period model (no discounting / NPV)
