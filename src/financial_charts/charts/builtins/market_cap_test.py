import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from financial_charts.charts.builtins._test_helpers import (
    fundamentals_with,
    money_series,
    ratio_series,
)
from financial_charts.charts.builtins.market_cap import MarketCapChart


def test_declares_price_and_shares_outstanding_as_required():
    assert MarketCapChart().required_metrics == ["price", "shares_outstanding"]


def test_renders_latest_price_times_latest_shares_outstanding():
    fundamentals = fundamentals_with(
        {
            "price": money_series("price", [10.0, 20.0]),
            "shares_outstanding": ratio_series(
                "shares_outstanding", [1_000_000.0, 2_000_000.0]
            ),
        }
    )
    fig, ax = plt.subplots()

    MarketCapChart().render(ax, fundamentals)

    # latest price ($20) * latest shares (2,000,000) = $40,000,000 -> "40.0M"
    texts = [t.get_text() for t in ax.texts]
    assert "$40.0M" in texts
    plt.close(fig)
