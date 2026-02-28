"""Tests for src/model.py core calculations."""

import math

import pytest

from src.model import (
    UnitEconInputs,
    compute,
    compute_contribution_margin_per_order,
    compute_health_flags,
    compute_ltv,
    compute_ltv_cac_ratio,
    compute_monthly_contribution,
    compute_payback_months,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def dark_store_inputs():
    """Dark store example: blended CAC $18, AOV $34, 2.8 orders/mo, 30% GM, $4.20 VC, 8% churn."""
    return UnitEconInputs(
        aov=34.0,
        orders_per_month=2.8,
        gross_margin_pct=0.30,
        variable_cost_per_order=4.20,
        monthly_churn_rate=0.08,
        monthly_fixed_costs=12000.0,
        channels=[{"name": "Blended", "cac": 18.0, "pct_of_new_customers": 1.0}],
    )


@pytest.fixture
def bad_economics_inputs():
    """Inputs where CAC >> LTV (very high CAC, thin margins, high churn)."""
    return UnitEconInputs(
        aov=20.0,
        orders_per_month=1.0,
        gross_margin_pct=0.15,
        variable_cost_per_order=2.50,
        monthly_churn_rate=0.30,
        monthly_fixed_costs=5000.0,
        channels=[{"name": "Blended", "cac": 500.0, "pct_of_new_customers": 1.0}],
    )


@pytest.fixture
def high_churn_inputs():
    """Inputs with very high monthly churn (> 10%)."""
    return UnitEconInputs(
        aov=40.0,
        orders_per_month=2.0,
        gross_margin_pct=0.40,
        variable_cost_per_order=3.00,
        monthly_churn_rate=0.15,
        monthly_fixed_costs=8000.0,
        channels=[{"name": "Blended", "cac": 50.0, "pct_of_new_customers": 1.0}],
    )


# ── Contribution margin ──────────────────────────────────────────────────────

class TestContributionMargin:
    def test_dark_store_cm(self, dark_store_inputs):
        cm = compute_contribution_margin_per_order(dark_store_inputs)
        # (34 × 0.30) - 4.20 = 10.20 - 4.20 = 6.00
        assert cm == pytest.approx(6.00, abs=0.01)

    def test_cm_is_positive_healthy_business(self, dark_store_inputs):
        cm = compute_contribution_margin_per_order(dark_store_inputs)
        assert cm > 0


# ── Monthly contribution ─────────────────────────────────────────────────────

class TestMonthlyContribution:
    def test_dark_store_mc(self, dark_store_inputs):
        mc = compute_monthly_contribution(dark_store_inputs)
        # 6.00 × 2.8 = 16.80
        assert mc == pytest.approx(16.80, abs=0.01)


# ── LTV ───────────────────────────────────────────────────────────────────────

class TestLTV:
    def test_ltv_is_positive(self, dark_store_inputs):
        ltv = compute_ltv(dark_store_inputs)
        assert ltv > 0

    def test_dark_store_ltv(self, dark_store_inputs):
        ltv = compute_ltv(dark_store_inputs)
        # 16.80 × (1/0.08) = 16.80 × 12.5 = 210.00
        assert ltv == pytest.approx(210.00, abs=0.01)

    def test_zero_churn_gives_infinite_ltv(self):
        inputs = UnitEconInputs(
            aov=34.0, orders_per_month=2.8,
            gross_margin_pct=0.30, variable_cost_per_order=4.20,
            monthly_churn_rate=0.0,
            channels=[{"name": "Blended", "cac": 18.0, "pct_of_new_customers": 1.0}],
        )
        assert compute_ltv(inputs) == float("inf")


# ── LTV:CAC ratio ────────────────────────────────────────────────────────────

class TestLTVCACRatio:
    def test_ratio_is_positive(self, dark_store_inputs):
        ratio = compute_ltv_cac_ratio(dark_store_inputs)
        assert ratio > 0

    def test_dark_store_ratio(self, dark_store_inputs):
        ratio = compute_ltv_cac_ratio(dark_store_inputs)
        # 210 / 18 = 11.6667
        assert ratio == pytest.approx(11.667, abs=0.01)

    def test_bad_economics_ratio_below_one(self, bad_economics_inputs):
        ratio = compute_ltv_cac_ratio(bad_economics_inputs)
        assert ratio < 1.0


# ── Payback period ────────────────────────────────────────────────────────────

class TestPayback:
    def test_payback_is_positive(self, dark_store_inputs):
        pb = compute_payback_months(dark_store_inputs)
        assert pb > 0

    def test_dark_store_payback(self, dark_store_inputs):
        pb = compute_payback_months(dark_store_inputs)
        # 18 / 16.80 ≈ 1.07
        assert pb == pytest.approx(1.07, abs=0.01)


# ── Health score ──────────────────────────────────────────────────────────────

class TestHealthScore:
    def test_score_in_range(self, dark_store_inputs):
        outputs = compute(dark_store_inputs)
        assert 0 <= outputs.health_score <= 100

    def test_bad_economics_low_score(self, bad_economics_inputs):
        outputs = compute(bad_economics_inputs)
        assert outputs.health_score < 50

    def test_good_economics_high_score(self, dark_store_inputs):
        outputs = compute(dark_store_inputs)
        assert outputs.health_score >= 70


# ── Health flags ──────────────────────────────────────────────────────────────

class TestHealthFlags:
    def test_critical_flag_when_cac_exceeds_ltv(self, bad_economics_inputs):
        outputs = compute(bad_economics_inputs)
        severities = [f.severity for f in outputs.health_flags]
        assert "critical" in severities

    def test_no_critical_on_healthy_business(self, dark_store_inputs):
        outputs = compute(dark_store_inputs)
        severities = [f.severity for f in outputs.health_flags]
        assert "critical" not in severities

    def test_high_churn_triggers_watch(self, high_churn_inputs):
        outputs = compute(high_churn_inputs)
        severities = [f.severity for f in outputs.health_flags]
        assert "watch" in severities

    def test_bad_economics_has_flags(self, bad_economics_inputs):
        outputs = compute(bad_economics_inputs)
        assert len(outputs.health_flags) > 0


# ── Expansion revenue (Skok formula) ─────────────────────────────────────────

class TestExpansionRevenue:
    def test_zero_growth_uses_simple_formula(self, dark_store_inputs):
        """With growth=0, LTV should match the simple a/c formula."""
        ltv = compute_ltv(dark_store_inputs)
        assert dark_store_inputs.monthly_arpu_growth_rate == 0.0
        assert ltv == pytest.approx(210.00, abs=0.01)

    def test_expansion_increases_ltv(self, dark_store_inputs):
        """With ARPU growth > 0, LTV should be higher than the base case."""
        from dataclasses import replace
        base_ltv = compute_ltv(dark_store_inputs)
        expanded = replace(dark_store_inputs, monthly_arpu_growth_rate=0.02)
        expanded_ltv = compute_ltv(expanded)
        assert expanded_ltv > base_ltv

    def test_skok_formula_values(self):
        """Verify the Skok formula: LTV = a/c + m/c^2."""
        inputs = UnitEconInputs(
            aov=50.0, orders_per_month=1.0,
            gross_margin_pct=0.80, variable_cost_per_order=0.0,
            monthly_churn_rate=0.10, monthly_arpu_growth_rate=0.03,
            channels=[{"name": "Blended", "cac": 100.0, "pct_of_new_customers": 1.0}],
        )
        # a = 50 * 0.80 * 1.0 = 40.0
        # m = 40.0 * 0.03 = 1.2
        # c = 0.10
        # LTV = 40/0.10 + 1.2/0.01 = 400 + 120 = 520
        assert compute_ltv(inputs) == pytest.approx(520.0, abs=0.01)

    def test_negative_churn_flag_when_growth_exceeds_churn(self):
        """When ARPU growth > churn, a positive 'negative churn' flag appears."""
        inputs = UnitEconInputs(
            aov=50.0, orders_per_month=1.0,
            gross_margin_pct=0.80, variable_cost_per_order=0.0,
            monthly_churn_rate=0.05, monthly_arpu_growth_rate=0.08,
            channels=[{"name": "Blended", "cac": 100.0, "pct_of_new_customers": 1.0}],
        )
        outputs = compute(inputs)
        severities = [f.severity for f in outputs.health_flags]
        assert "positive" in severities
        messages = " ".join(f.message for f in outputs.health_flags)
        assert "Negative churn achieved" in messages

    def test_no_negative_churn_flag_when_growth_below_churn(self, dark_store_inputs):
        """No positive flag when ARPU growth < churn."""
        from dataclasses import replace
        inputs = replace(dark_store_inputs, monthly_arpu_growth_rate=0.01)
        outputs = compute(inputs)
        severities = [f.severity for f in outputs.health_flags]
        assert "positive" not in severities

    def test_default_arpu_growth_is_zero(self):
        """Default monthly_arpu_growth_rate should be 0."""
        inputs = UnitEconInputs(
            aov=34.0, orders_per_month=2.8,
            gross_margin_pct=0.30, variable_cost_per_order=4.20,
            monthly_churn_rate=0.08,
            channels=[{"name": "Blended", "cac": 18.0, "pct_of_new_customers": 1.0}],
        )
        assert inputs.monthly_arpu_growth_rate == 0.0


# ── Full compute integration ─────────────────────────────────────────────────

class TestCompute:
    def test_compute_returns_all_fields(self, dark_store_inputs):
        outputs = compute(dark_store_inputs)
        assert outputs.contribution_margin_per_order is not None
        assert outputs.monthly_contribution is not None
        assert outputs.ltv is not None
        assert outputs.ltv_cac_ratio is not None
        assert outputs.payback_months is not None
        assert outputs.health_score is not None
        assert outputs.health_flags is not None
