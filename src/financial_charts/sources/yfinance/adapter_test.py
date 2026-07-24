import json
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

from financial_charts.sources.base import SourceUnavailable, TickerNotFound
from financial_charts.sources.yfinance.adapter import YFinanceAdapter
from financial_charts.template.models import Currency, Market, Period

_FIXTURES = Path(__file__).parent / "fixtures"

_DATAFRAME_KEYS = [
    "history",
    "financials",
    "quarterly_financials",
    "cashflow",
    "quarterly_cashflow",
]


class _FakeTicker:
    """Stands in for `yfinance.Ticker`, serving a recorded fixture instead of the network."""

    def __init__(self, fixture_name: str):
        raw = json.loads((_FIXTURES / f"{fixture_name}.json").read_text())
        self.info = raw["info"]
        self._frames = {
            key: pd.read_json(StringIO(raw[key]), orient="split")
            for key in _DATAFRAME_KEYS
        }

    def history(self, period: str) -> pd.DataFrame:
        return self._frames["history"]

    @property
    def financials(self) -> pd.DataFrame:
        return self._frames["financials"]

    @property
    def quarterly_financials(self) -> pd.DataFrame:
        return self._frames["quarterly_financials"]

    @property
    def cashflow(self) -> pd.DataFrame:
        return self._frames["cashflow"]

    @property
    def quarterly_cashflow(self) -> pd.DataFrame:
        return self._frames["quarterly_cashflow"]


def _fetch_with_fixture(
    fixture_name: str, ticker: str, market: Market, period: Period, range: str
):
    with patch(
        "financial_charts.sources.yfinance.adapter.yf.Ticker",
        lambda _ticker: _FakeTicker(fixture_name),
    ):
        return YFinanceAdapter().fetch(ticker, market, period, range)


def test_us_ticker_maps_price_and_fundamentals_in_usd():
    fundamentals = _fetch_with_fixture("aapl", "AAPL", Market.US, Period.ANNUAL, "5y")

    assert fundamentals.currency == Currency.USD
    assert fundamentals.series["price"].available
    assert fundamentals.series["price"].points[0].value.currency == Currency.USD

    revenue = fundamentals.series["revenue"]
    assert revenue.available
    assert revenue.points[0].value.currency == Currency.USD
    assert revenue.points[0].value.value > 0

    assert fundamentals.series["eps"].available
    assert fundamentals.series["net_margin"].available


def test_tase_ticker_converts_agorot_price_and_reports_ils_financials():
    fundamentals = _fetch_with_fixture(
        "lumi_ta", "LUMI.TA", Market.TASE, Period.ANNUAL, "5y"
    )

    assert fundamentals.currency == Currency.ILS

    price = fundamentals.series["price"]
    assert price.available
    assert price.points[0].value.currency == Currency.ILS
    # Fixture's raw quote is in agorot; the adapter must divide by 100 to reach shekels.
    raw_agorot_close = json.loads((_FIXTURES / "lumi_ta.json").read_text())
    raw_history = pd.read_json(StringIO(raw_agorot_close["history"]), orient="split")
    expected_shekels = raw_history.iloc[0]["Close"] / 100
    assert price.points[0].value.value == pytest.approx(expected_shekels)

    revenue = fundamentals.series["revenue"]
    assert revenue.available
    assert revenue.points[0].value.currency == Currency.ILS


def test_unknown_ticker_raises_ticker_not_found():
    class _EmptyTicker:
        info = {"trailingPegRatio": None}

        def history(self, period: str) -> pd.DataFrame:
            return pd.DataFrame()

    with patch(
        "financial_charts.sources.yfinance.adapter.yf.Ticker",
        lambda _ticker: _EmptyTicker(),
    ):
        with pytest.raises(TickerNotFound):
            YFinanceAdapter().fetch("ZZZZZZINVALID", Market.US, Period.ANNUAL, "1y")


def test_declares_capability():
    capability = YFinanceAdapter().capability()
    assert Market.US in capability.markets
    assert Market.TASE in capability.markets
    assert "price" in capability.metrics


def test_network_failure_raises_source_unavailable():
    class _BrokenTicker:
        @property
        def info(self):
            raise ConnectionError("network is down")

    with patch(
        "financial_charts.sources.yfinance.adapter.yf.Ticker",
        lambda _ticker: _BrokenTicker(),
    ):
        with pytest.raises(SourceUnavailable):
            YFinanceAdapter().fetch("AAPL", Market.US, Period.ANNUAL, "1y")


def test_statement_series_points_are_ascending_by_date():
    # yfinance's statement columns come back newest-first; the adapter must
    # sort them ascending so every series in one fetch runs the same
    # chronological direction as price.
    fundamentals = _fetch_with_fixture("aapl", "AAPL", Market.US, Period.ANNUAL, "5y")

    revenue_dates = [p.date for p in fundamentals.series["revenue"].points]
    assert revenue_dates == sorted(revenue_dates)
