from datetime import date

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from financial_charts.charts.base import (
    currency_symbol,
    format_compact_number,
    render_kpi_value,
    render_or_no_data,
    render_percentage_line,
)
from financial_charts.charts.builtins._test_helpers import (
    fundamentals_with,
    money_series,
    unavailable_series,
)
from financial_charts.charts.builtins.revenue import RevenueChart
from financial_charts.template.models import Currency


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


def test_currency_symbol_is_shekel_for_ils():
    fundamentals = fundamentals_with({}, currency=Currency.ILS)
    assert currency_symbol(fundamentals) == "₪"


def test_currency_symbol_is_dollar_for_usd():
    fundamentals = fundamentals_with({}, currency=Currency.USD)
    assert currency_symbol(fundamentals) == "$"


def test_render_percentage_line_scales_ratios_to_percent():
    fig, ax = plt.subplots()

    render_percentage_line(
        ax, [date(2020, 1, 1), date(2021, 1, 1)], [0.4, 0.45], "Gross Margin"
    )

    line = ax.get_lines()[0]
    assert line.get_label() == "Gross Margin"
    assert list(line.get_ydata()) == [40.0, 45.0]
    plt.close(fig)


def test_format_compact_number_picks_the_largest_fitting_suffix():
    assert format_compact_number(4_900_000_000_000) == "4.9T"
    assert format_compact_number(450_500_000_000) == "450.5B"
    assert format_compact_number(12_300_000) == "12.3M"
    assert format_compact_number(1_500) == "1.5K"
    assert format_compact_number(42) == "42.0"


def test_render_kpi_value_draws_the_text_with_no_axes():
    fig, ax = plt.subplots()

    render_kpi_value(ax, "34.6x")

    texts = [t.get_text() for t in ax.texts]
    assert "34.6x" in texts
    assert ax.get_xticks().size == 0
    plt.close(fig)
