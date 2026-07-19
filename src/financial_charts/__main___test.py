from datetime import date
from unittest.mock import patch

from financial_charts.__main__ import main
from financial_charts.sources.base import Capability, MissingCredentials, TickerNotFound
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


def _fundamentals(ticker: str = "AAPL") -> CompanyFundamentals:
    return CompanyFundamentals(
        ticker=ticker,
        market=Market.US,
        currency=Currency.USD,
        period=Period.ANNUAL,
        range="5y",
        series={
            "price": MetricSeries(
                metric_id="price",
                points=[
                    Point(
                        date=date(2026, 1, 1),
                        value=Money(value=100, currency=Currency.USD, scale=Unit.ONES),
                    )
                ],
                available=True,
            )
        },
    )


def _capability() -> Capability:
    return Capability(
        markets={Market.US, Market.TASE},
        periods={Period.ANNUAL},
        max_history={Period.ANNUAL: 5},
        metrics={"price"},
    )


class _StubAdapter:
    def __init__(self, fundamentals=None, fetch_error=None):
        self._fundamentals = fundamentals or _fundamentals()
        self._fetch_error = fetch_error

    def capability(self) -> Capability:
        return _capability()

    def fetch(self, ticker, market, period, range) -> CompanyFundamentals:
        if self._fetch_error:
            raise self._fetch_error
        return self._fundamentals


def test_render_writes_html_output(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    out = tmp_path / "out.html"

    with patch("financial_charts.__main__.get_source", return_value=_StubAdapter()):
        code = main(["AAPL", "--out", str(out)])

    assert code == 0
    assert out.exists()
    assert "AAPL" in out.read_text()


def test_render_unknown_ticker_returns_error(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)

    with patch(
        "financial_charts.__main__.get_source",
        return_value=_StubAdapter(fetch_error=TickerNotFound("ZZZ")),
    ):
        code = main(["ZZZ", "--out", str(tmp_path / "out.html")])

    assert code == 1
    assert "not found" in capsys.readouterr().err


def test_render_missing_credentials_returns_error(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)

    with patch(
        "financial_charts.__main__.get_source",
        side_effect=MissingCredentials("TWELVEDATA_API_KEY is not set"),
    ):
        code = main(
            ["AAPL", "--source", "twelvedata", "--out", str(tmp_path / "out.html")]
        )

    assert code == 1
    assert "TWELVEDATA_API_KEY" in capsys.readouterr().err


def test_render_unknown_source_returns_error(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)

    code = main(
        ["AAPL", "--source", "not-a-real-source", "--out", str(tmp_path / "out.html")]
    )

    assert code == 1
    assert "unknown data source" in capsys.readouterr().err


def test_render_uses_cache_before_fetching(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    fetch_calls = []

    class _CountingAdapter(_StubAdapter):
        def fetch(self, ticker, market, period, range):
            fetch_calls.append(ticker)
            return super().fetch(ticker, market, period, range)

    with patch("financial_charts.__main__.get_source", return_value=_CountingAdapter()):
        main(["AAPL", "--out", str(tmp_path / "a.html")])
        main(["AAPL", "--out", str(tmp_path / "b.html")])

    assert len(fetch_calls) == 1


def test_verify_source_subcommand_dispatches(monkeypatch, capsys):
    with patch("financial_charts.__main__.get_source", return_value=_StubAdapter()):
        code = main(["verify-source", "yfinance", "--ticker", "AAPL"])

    assert code == 0
    assert "RESULT: clean" in capsys.readouterr().out
