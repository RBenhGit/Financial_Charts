from datetime import date

from financial_charts.sources.base import Capability
from financial_charts.sources.verify import reconcile
from financial_charts.template.models import (
    CompanyFundamentals,
    Currency,
    Market,
    MetricSeries,
    Money,
    Period,
    Point,
    Unit,
)


class _StubAdapter:
    def __init__(self, capability: Capability, fundamentals: CompanyFundamentals):
        self._capability = capability
        self._fundamentals = fundamentals

    def capability(self) -> Capability:
        return self._capability

    def fetch(self, ticker, market, period, range) -> CompanyFundamentals:
        return self._fundamentals


def _money(value: float, currency: Currency = Currency.USD) -> Money:
    return Money(value=value, currency=currency, scale=Unit.ONES)


def test_clean_reconciliation_has_no_mismatch():
    capability = Capability(
        markets={Market.US},
        periods={Period.ANNUAL},
        max_history={Period.ANNUAL: 4},
        metrics={"price", "revenue"},
    )
    fundamentals = CompanyFundamentals(
        ticker="AAPL",
        market=Market.US,
        currency=Currency.USD,
        period=Period.ANNUAL,
        range="4y",
        series={
            "price": MetricSeries(
                metric_id="price",
                points=[Point(date=date(2026, 1, 1), value=_money(200))],
                available=True,
            ),
            "revenue": MetricSeries(
                metric_id="revenue",
                points=[Point(date=date(2026, 1, 1), value=_money(1_000_000))],
                available=True,
            ),
        },
    )

    report = reconcile(
        _StubAdapter(capability, fundamentals), "AAPL", Market.US, Period.ANNUAL, "4y"
    )

    assert report.missing_metrics == []
    assert report.undeclared_extras == []
    assert report.unit_warnings == []
    assert not report.has_mismatch


def test_declared_but_missing_metric_is_a_mismatch():
    capability = Capability(
        markets={Market.US},
        periods={Period.ANNUAL},
        max_history={Period.ANNUAL: 4},
        metrics={"price", "eps"},
    )
    fundamentals = CompanyFundamentals(
        ticker="AAPL",
        market=Market.US,
        currency=Currency.USD,
        period=Period.ANNUAL,
        range="4y",
        series={
            "price": MetricSeries(
                metric_id="price",
                points=[Point(date=date(2026, 1, 1), value=_money(200))],
                available=True,
            ),
            "eps": MetricSeries(metric_id="eps", points=[], available=False),
        },
    )

    report = reconcile(
        _StubAdapter(capability, fundamentals), "AAPL", Market.US, Period.ANNUAL, "4y"
    )

    assert report.missing_metrics == ["eps"]
    assert report.has_mismatch


def test_undeclared_extra_metric_is_reported_but_not_a_mismatch():
    capability = Capability(
        markets={Market.US},
        periods={Period.ANNUAL},
        max_history={Period.ANNUAL: 4},
        metrics={"price"},
    )
    fundamentals = CompanyFundamentals(
        ticker="AAPL",
        market=Market.US,
        currency=Currency.USD,
        period=Period.ANNUAL,
        range="4y",
        series={
            "price": MetricSeries(
                metric_id="price",
                points=[Point(date=date(2026, 1, 1), value=_money(200))],
                available=True,
            ),
            "eps": MetricSeries(
                metric_id="eps",
                points=[Point(date=date(2026, 1, 1), value=_money(6))],
                available=True,
            ),
        },
    )

    report = reconcile(
        _StubAdapter(capability, fundamentals), "AAPL", Market.US, Period.ANNUAL, "4y"
    )

    assert report.undeclared_extras == ["eps"]
    assert not report.has_mismatch


def test_unconverted_agorot_price_triggers_unit_warning():
    capability = Capability(
        markets={Market.TASE},
        periods={Period.ANNUAL},
        max_history={Period.ANNUAL: 4},
        metrics={"price"},
    )
    fundamentals = CompanyFundamentals(
        ticker="TEVA.TA",
        market=Market.TASE,
        currency=Currency.ILS,
        period=Period.ANNUAL,
        range="4y",
        series={
            "price": MetricSeries(
                metric_id="price",
                # A raw agorot quote left unconverted (should have been /100).
                points=[
                    Point(date=date(2026, 1, 1), value=_money(973_500, Currency.ILS))
                ],
                available=True,
            ),
        },
    )

    report = reconcile(
        _StubAdapter(capability, fundamentals),
        "TEVA.TA",
        Market.TASE,
        Period.ANNUAL,
        "4y",
    )

    assert len(report.unit_warnings) == 1
    assert "agorot" in report.unit_warnings[0]
