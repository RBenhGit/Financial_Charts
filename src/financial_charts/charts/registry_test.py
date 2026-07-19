import pytest

from financial_charts.charts.registry import get_chart_set, register_chart_set


def test_builtin_fundamentals_set_has_six_charts():
    charts = get_chart_set("fundamentals")
    assert len(charts) == 6
    assert {c.name for c in charts} == {
        "price",
        "revenue",
        "net_income",
        "free_cash_flow",
        "eps",
        "margins",
    }


def test_unknown_chart_set_raises_key_error():
    with pytest.raises(KeyError):
        get_chart_set("not-a-real-set")


def test_can_register_custom_chart_set():
    charts = get_chart_set("fundamentals")
    register_chart_set("price-only", charts[:1])

    assert [c.name for c in get_chart_set("price-only")] == ["price"]
