"""Tests for src/scenarios.py — scenario engine and impact summaries."""

import pytest

from src.model import UnitEconInputs, compute
from src.scenarios import (
    apply_scenario,
    generate_impact_summary,
    get_default_scenarios,
)


@pytest.fixture
def delivery_inputs():
    return UnitEconInputs(
        aov=34.0,
        orders_per_month=2.8,
        gross_margin_pct=0.30,
        variable_cost_per_order=4.20,
        monthly_churn_rate=0.08,
        monthly_fixed_costs=12000.0,
        channels=[
            {"name": "Paid Social", "cac": 25.0, "pct_of_new_customers": 0.60},
            {"name": "Organic", "cac": 8.0, "pct_of_new_customers": 0.30},
            {"name": "Referral", "cac": 6.0, "pct_of_new_customers": 0.10},
        ],
    )


class TestGetDefaultScenarios:
    def test_returns_list(self):
        scenarios = get_default_scenarios()
        assert isinstance(scenarios, list)
        assert len(scenarios) >= 4

    def test_scenarios_have_names(self):
        for s in get_default_scenarios():
            assert s.name
            assert s.description
            assert callable(s.apply)


class TestApplyScenario:
    def test_aov_increase(self, delivery_inputs):
        scenarios = get_default_scenarios()
        aov_scenario = [s for s in scenarios if "AOV" in s.name][0]
        new_inputs, new_outputs = apply_scenario(delivery_inputs, aov_scenario)
        assert new_inputs.aov > delivery_inputs.aov
        assert new_outputs.contribution_margin_per_order > compute(delivery_inputs).contribution_margin_per_order

    def test_delivery_cost_drop(self, delivery_inputs):
        scenarios = get_default_scenarios()
        cost_scenario = [s for s in scenarios if "Delivery" in s.name or "cost" in s.name.lower()][0]
        new_inputs, new_outputs = apply_scenario(delivery_inputs, cost_scenario)
        assert new_inputs.variable_cost_per_order < delivery_inputs.variable_cost_per_order

    def test_batch_orders(self, delivery_inputs):
        scenarios = get_default_scenarios()
        batch_scenario = [s for s in scenarios if "Batch" in s.name or "batch" in s.name][0]
        new_inputs, new_outputs = apply_scenario(delivery_inputs, batch_scenario)
        assert new_inputs.variable_cost_per_order == pytest.approx(delivery_inputs.variable_cost_per_order * 0.5)

    def test_spoilage_doubles(self, delivery_inputs):
        scenarios = get_default_scenarios()
        spoilage_scenario = [s for s in scenarios if "Spoilage" in s.name or "spoilage" in s.name][0]
        new_inputs, new_outputs = apply_scenario(delivery_inputs, spoilage_scenario)
        assert new_inputs.gross_margin_pct < delivery_inputs.gross_margin_pct

    def test_churn_drops(self, delivery_inputs):
        scenarios = get_default_scenarios()
        churn_scenario = [s for s in scenarios if "Churn drops to 5%" == s.name][0]
        new_inputs, new_outputs = apply_scenario(delivery_inputs, churn_scenario)
        assert new_inputs.monthly_churn_rate == pytest.approx(0.05)


class TestGenerateImpactSummary:
    def test_returns_string(self, delivery_inputs):
        outputs_before = compute(delivery_inputs)
        scenarios = get_default_scenarios()
        new_inputs, new_outputs = apply_scenario(delivery_inputs, scenarios[0])
        summary = generate_impact_summary(delivery_inputs, outputs_before, new_inputs, new_outputs)
        assert isinstance(summary, str)
        assert len(summary) > 10

    def test_includes_cm_change(self, delivery_inputs):
        outputs_before = compute(delivery_inputs)
        scenarios = get_default_scenarios()
        new_inputs, new_outputs = apply_scenario(delivery_inputs, scenarios[0])
        summary = generate_impact_summary(delivery_inputs, outputs_before, new_inputs, new_outputs)
        assert "Contribution margin" in summary or "contribution margin" in summary

    def test_includes_breakeven(self, delivery_inputs):
        outputs_before = compute(delivery_inputs)
        scenarios = get_default_scenarios()
        new_inputs, new_outputs = apply_scenario(delivery_inputs, scenarios[0])
        summary = generate_impact_summary(delivery_inputs, outputs_before, new_inputs, new_outputs)
        assert "breakeven" in summary.lower() or "orders" in summary.lower()

    def test_negative_margin_scenario(self, delivery_inputs):
        outputs_before = compute(delivery_inputs)
        scenarios = get_default_scenarios()
        # Spoilage doubles
        spoilage_scenario = [s for s in scenarios if "Spoilage" in s.name][0]
        new_inputs, new_outputs = apply_scenario(delivery_inputs, spoilage_scenario)
        summary = generate_impact_summary(delivery_inputs, outputs_before, new_inputs, new_outputs)
        assert isinstance(summary, str)
