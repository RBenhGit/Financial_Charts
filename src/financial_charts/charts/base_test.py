import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from financial_charts.charts.base import render_or_no_data
from financial_charts.charts.builtins._test_helpers import (
    fundamentals_with,
    money_series,
    unavailable_series,
)
from financial_charts.charts.builtins.revenue import RevenueChart


def test_renders_chart_when_metric_available():
    fundamentals = fundamentals_with(
        {"revenue": money_series("revenue", [1.0, 2.0, 3.0])}
    )
    fig, ax = plt.subplots()

    render_or_no_data(RevenueChart(), ax, fundamentals)

    assert ax.get_title() == "Revenue"
    assert len(ax.patches) > 0  # bars were drawn
    plt.close(fig)


def test_falls_back_to_no_data_when_metric_unavailable():
    fundamentals = fundamentals_with({"revenue": unavailable_series("revenue")})
    fig, ax = plt.subplots()

    render_or_no_data(RevenueChart(), ax, fundamentals)

    assert ax.get_title() == "Revenue"
    assert len(ax.patches) == 0
    texts = [t.get_text() for t in ax.texts]
    assert "No Data" in texts
    plt.close(fig)


def test_falls_back_to_no_data_when_metric_missing_entirely():
    fundamentals = fundamentals_with({})
    fig, ax = plt.subplots()

    render_or_no_data(RevenueChart(), ax, fundamentals)

    texts = [t.get_text() for t in ax.texts]
    assert "No Data" in texts
    plt.close(fig)
