import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from financial_charts.charts.builtins._test_helpers import (
    fundamentals_with,
    money_series,
)
from financial_charts.charts.builtins.return_on_equity import ReturnOnEquityChart


def test_declares_net_income_and_total_equity_as_required():
    assert ReturnOnEquityChart().required_metrics == ["net_income", "total_equity"]


def test_renders_latest_net_income_over_latest_equity_as_a_percentage():
    fundamentals = fundamentals_with(
        {
            "net_income": money_series("net_income", [15.0]),
            "total_equity": money_series("total_equity", [200.0]),
        }
    )
    fig, ax = plt.subplots()

    ReturnOnEquityChart().render(ax, fundamentals)

    # 15 / 200 = 7.5%
    texts = [t.get_text() for t in ax.texts]
    assert "7.5%" in texts
    plt.close(fig)


def test_falls_back_to_no_data_on_zero_equity():
    fundamentals = fundamentals_with(
        {
            "net_income": money_series("net_income", [15.0]),
            "total_equity": money_series("total_equity", [0.0]),
        }
    )
    fig, ax = plt.subplots()

    ReturnOnEquityChart().render(ax, fundamentals)

    texts = [t.get_text() for t in ax.texts]
    assert "No Data" in texts
    plt.close(fig)
