import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from financial_charts.charts.builtins._test_helpers import (
    fundamentals_with,
    money_series,
    ratio_series,
)
from financial_charts.charts.builtins.dividend_yield import DividendYieldChart
from financial_charts.template.models import Currency


def test_declares_price_dividends_and_shares_as_required():
    assert DividendYieldChart().required_metrics == [
        "price",
        "dividends_paid",
        "shares_outstanding",
    ]


def test_renders_dividend_per_share_over_price_as_a_percentage():
    fundamentals = fundamentals_with(
        {
            "price": money_series("price", [100.0]),
            "dividends_paid": money_series("dividends_paid", [200_000.0]),
            "shares_outstanding": ratio_series("shares_outstanding", [100_000.0]),
        }
    )
    fig, ax = plt.subplots()

    DividendYieldChart().render(ax, fundamentals)

    # dividend/share = $2; yield = 2/100 = 2.00%
    texts = [t.get_text() for t in ax.texts]
    assert "2.00%" in texts
    plt.close(fig)


def test_falls_back_to_no_data_on_currency_mismatch():
    # A dual-listed company can report financials in a different currency
    # than the one its shares trade in — must degrade, never silently
    # combine mismatched currencies into a nonsensical yield.
    fundamentals = fundamentals_with(
        {
            "price": money_series("price", [100.0], currency=Currency.ILS),
            "dividends_paid": money_series(
                "dividends_paid", [200_000.0], currency=Currency.USD
            ),
            "shares_outstanding": ratio_series("shares_outstanding", [100_000.0]),
        }
    )
    fig, ax = plt.subplots()

    DividendYieldChart().render(ax, fundamentals)

    texts = [t.get_text() for t in ax.texts]
    assert "No Data" in texts
    plt.close(fig)


def test_falls_back_to_no_data_on_zero_price():
    fundamentals = fundamentals_with(
        {
            "price": money_series("price", [0.0]),
            "dividends_paid": money_series("dividends_paid", [200_000.0]),
            "shares_outstanding": ratio_series("shares_outstanding", [100_000.0]),
        }
    )
    fig, ax = plt.subplots()

    DividendYieldChart().render(ax, fundamentals)

    texts = [t.get_text() for t in ax.texts]
    assert "No Data" in texts
    plt.close(fig)
