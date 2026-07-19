import pytest

from financial_charts.charts.catalog import (
    available_charts,
    chart_support,
    get_chart,
    supported_by,
)


def test_available_charts_includes_all_builtins_and_fcf_margin():
    names = {chart.name for chart in available_charts()}
    assert names == {
        "price",
        "revenue",
        "net_income",
        "free_cash_flow",
        "eps",
        "margins",
        "fcf_margin",
    }


def test_get_chart_resolves_by_id():
    assert get_chart("price").name == "price"


def test_get_chart_unknown_id_raises_key_error():
    with pytest.raises(KeyError):
        get_chart("not-a-real-chart")


class _StubChart:
    name = "stub"
    title = "Stub"
    required_metrics = ["ebitda"]

    def render(self, ax, fundamentals):
        pass


class _PriceOnlyChart:
    name = "price-only"
    title = "Price Only"
    required_metrics = ["price"]

    def render(self, ax, fundamentals):
        pass


def test_supported_by_is_empty_when_no_source_declares_the_metric():
    assert supported_by(_StubChart()) == frozenset()


def test_supported_by_lists_sources_that_declare_all_required_metrics():
    assert supported_by(_PriceOnlyChart()) == {"yfinance", "twelvedata"}


def test_chart_support_covers_every_catalog_chart():
    support = chart_support()

    assert set(support) == {chart.name for chart in available_charts()}
    assert support["fcf_margin"] == {"yfinance", "twelvedata"}
