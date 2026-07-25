import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from financial_charts.charts.builtins._test_helpers import (
    fundamentals_with,
    money_series,
)
from financial_charts.charts.builtins.pe_ratio import PERatioChart


def test_declares_price_and_eps_as_required():
    assert PERatioChart().required_metrics == ["price", "eps"]


def test_renders_latest_price_over_latest_eps():
    fundamentals = fundamentals_with(
        {
            "price": money_series("price", [100.0, 200.0]),
            "eps": money_series("eps", [4.0, 5.0]),
        }
    )
    fig, ax = plt.subplots()

    PERatioChart().render(ax, fundamentals)

    texts = [t.get_text() for t in ax.texts]
    assert "40.0x" in texts
    plt.close(fig)


def test_falls_back_to_no_data_on_zero_eps():
    fundamentals = fundamentals_with(
        {
            "price": money_series("price", [100.0]),
            "eps": money_series("eps", [0.0]),
        }
    )
    fig, ax = plt.subplots()

    PERatioChart().render(ax, fundamentals)

    texts = [t.get_text() for t in ax.texts]
    assert "No Data" in texts
    plt.close(fig)
