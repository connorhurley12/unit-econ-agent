"""Tests for src/model.py core calculations."""

import math

import pytest

from src.model import (
    UnitEconInputs,
    compute,
    compute_channel_ltv_cac_ratios,
    compute_contribution_margin_per_order,
    compute_health_flags,
    compute_ltv,
    compute_ltv_cac_ratio,
    compute_monthly_contribution,
    compute_payback_months,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _single_channel(cac: float) -> list:
    """Create a single-channel list for backward-compatible test setups."""
    return [{"name": "Blended", "cac": cac, "pct_of_new_customers": 1.0}]


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def dark_store_inputs():
    """Dark store example with multi-channel CAC.

    Blended CAC = 25×0.60 + 8×0.30 + 4×0.10 = 17.80
    """
    return UnitEconInputs(
        channels=[
            {"name": "Paid", "cac": 25.0, "pct_of_new_customers": 0.60},
            {"name": "Organic", "cac": 8.0, "pct_of_new_customers": 0.30},
            {"name": "Referral", "cac": 4.0, "pct_of_new_customers": 0.10},
        ],
        aov=34.0,
        orders_per_month=2.8,
        gross_margin_pct=0.30,
        variable_cost_per_order=4.20,
        monthly_churn_rate=0.08,
        monthly_fixed_costs=12000.0,
    )


@pytest.fixture
def bad_economics_inputs():
    """Inputs where CAC >> LTV (very high CAC, thin margins, high churn)."""
    return UnitEconInputs(
        channels=_single_channel(500.0),
        aov=20.0,
        orders_per_month=1.0,
        gross_margin_pct=0.15,
        variable_cost_per_order=2.50,
        monthly_churn_rate=0.30,
        monthly_fixed_costs=5000.0,
    )


@pytest.fixture
def high_churn_inputs():
    """Inputs with very high monthly churn (> 10%)."""
    return UnitEconInputs(
        channels=_single_channel(50.0),
        aov=40.0,
        orders_per_month=2.0,
        gross_margin_pct=0.40,
        variable_cost_per_order=3.00,
        monthly_churn_rate=0.15,
        monthly_fixed_costs=8000.0,
    )


# ── Blended CAC ──────────────────────────────────────────────────────────────

class TestBlendedCAC:
    def test_blended_cac_weighted_average(self, dark_store_inputs):
        # 25×0.60 + 8×0.30 + 4×0.10 = 15 + 2.4 + 0.4 = 17.80
        assert dark_store_inputs.blended_cac == pytest.approx(17.80, abs=0.01)

    def test_single_channel_blended_equals_cac(self):
        inputs = UnitEconInputs(channels=_single_channel(42.0))
        assert inputs.blended_cac == pytest.approx(42.0, abs=0.01)


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
            channels=_single_channel(18.0),
            aov=34.0, orders_per_month=2.8,
            gross_margin_pct=0.30, variable_cost_per_order=4.20,
            monthly_churn_rate=0.0,
        )
        assert compute_ltv(inputs) == float("inf")


# ── LTV:CAC ratio ────────────────────────────────────────────────────────────

class TestLTVCACRatio:
    def test_ratio_is_positive(self, dark_store_inputs):
        ratio = compute_ltv_cac_ratio(dark_store_inputs)
        assert ratio > 0

    def test_dark_store_ratio(self, dark_store_inputs):
        ratio = compute_ltv_cac_ratio(dark_store_inputs)
        # 210 / 17.80 ≈ 11.7978
        assert ratio == pytest.approx(11.798, abs=0.01)

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
        # 17.80 / 16.80 ≈ 1.06
        assert pb == pytest.approx(1.06, abs=0.01)


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


# ── Channel LTV:CAC ratios ───────────────────────────────────────────────────

class TestChannelLTVCAC:
    def test_channel_ratios_all_positive(self, dark_store_inputs):
        ratios = compute_channel_ltv_cac_ratios(dark_store_inputs)
        for r in ratios:
            assert r["ltv_cac_ratio"] > 0

    def test_channel_count_matches(self, dark_store_inputs):
        ratios = compute_channel_ltv_cac_ratios(dark_store_inputs)
        assert len(ratios) == len(dark_store_inputs.channels)

    def test_cheaper_channel_has_higher_ratio(self, dark_store_inputs):
        ratios = compute_channel_ltv_cac_ratios(dark_store_inputs)
        by_name = {r["name"]: r["ltv_cac_ratio"] for r in ratios}
        # Referral ($4) should have higher ratio than Paid ($25)
        assert by_name["Referral"] > by_name["Paid"]


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
