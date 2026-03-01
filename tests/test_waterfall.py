"""Tests for src/waterfall.py — waterfall chart data generation."""

import pytest

from src.model import UnitEconInputs
from src.waterfall import build_waterfall_data, create_waterfall_figure


@pytest.fixture
def delivery_inputs():
    return UnitEconInputs(
        aov=34.0,
        orders_per_month=2.8,
        gross_margin_pct=0.30,
        variable_cost_per_order=4.20,
        monthly_churn_rate=0.08,
    )


@pytest.fixture
def negative_margin_inputs():
    return UnitEconInputs(
        aov=20.0,
        orders_per_month=1.0,
        gross_margin_pct=0.15,
        variable_cost_per_order=10.0,
        monthly_churn_rate=0.30,
    )


class TestBuildWaterfallData:
    def test_returns_required_keys(self, delivery_inputs):
        data = build_waterfall_data(delivery_inputs)
        assert "labels" in data
        assert "values" in data
        assert "measures" in data
        assert "text" in data

    def test_five_items(self, delivery_inputs):
        data = build_waterfall_data(delivery_inputs)
        assert len(data["labels"]) == 5
        assert len(data["values"]) == 5
        assert len(data["measures"]) == 5
        assert len(data["text"]) == 5

    def test_revenue_is_aov(self, delivery_inputs):
        data = build_waterfall_data(delivery_inputs)
        assert data["values"][0] == pytest.approx(34.0)

    def test_cogs_is_negative(self, delivery_inputs):
        data = build_waterfall_data(delivery_inputs)
        # COGS = AOV * (1 - GM%) = 34 * 0.70 = 23.80
        assert data["values"][1] == pytest.approx(-23.80)

    def test_variable_cost_is_negative(self, delivery_inputs):
        data = build_waterfall_data(delivery_inputs)
        assert data["values"][3] == pytest.approx(-4.20)

    def test_measures_correct(self, delivery_inputs):
        data = build_waterfall_data(delivery_inputs)
        assert data["measures"] == ["absolute", "relative", "total", "relative", "total"]

    def test_cm_in_text(self, delivery_inputs):
        data = build_waterfall_data(delivery_inputs)
        # CM = 34 * 0.30 - 4.20 = 6.00
        assert "$6.00" in data["text"][4]

    def test_negative_margin(self, negative_margin_inputs):
        data = build_waterfall_data(negative_margin_inputs)
        # CM = 20 * 0.15 - 10 = -7.00
        assert "$-7.00" in data["text"][4] or "$7.00" in data["text"][4]


class TestCreateWaterfallFigure:
    def test_returns_figure(self, delivery_inputs):
        data = build_waterfall_data(delivery_inputs)
        fig = create_waterfall_figure(data)
        assert fig is not None
        assert hasattr(fig, "data")
        assert len(fig.data) == 1  # single waterfall trace

    def test_custom_title(self, delivery_inputs):
        data = build_waterfall_data(delivery_inputs)
        fig = create_waterfall_figure(data, title="Test Title")
        assert fig.layout.title.text == "Test Title"

    def test_custom_height(self, delivery_inputs):
        data = build_waterfall_data(delivery_inputs)
        fig = create_waterfall_figure(data, height=500)
        assert fig.layout.height == 500
