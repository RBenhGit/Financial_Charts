from datetime import date

from financial_charts.cache.store import TemplateCache
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


def _fundamentals() -> CompanyFundamentals:
    return CompanyFundamentals(
        ticker="AAPL",
        market=Market.US,
        currency=Currency.USD,
        period=Period.ANNUAL,
        range="5y",
        series={
            "revenue": MetricSeries(
                metric_id="revenue",
                points=[
                    Point(
                        date=date(2025, 9, 30),
                        value=Money(
                            value=416_161_000_000,
                            currency=Currency.USD,
                            scale=Unit.ONES,
                        ),
                    )
                ],
                available=True,
            )
        },
        source_limits=["eps: no data available for this ticker"],
    )


def test_cache_miss_returns_none(tmp_path):
    cache = TemplateCache(cache_dir=tmp_path)
    assert cache.get("AAPL", "yfinance", Period.ANNUAL, "5y", date(2026, 7, 19)) is None


def test_put_then_get_round_trips(tmp_path):
    cache = TemplateCache(cache_dir=tmp_path)
    fundamentals = _fundamentals()
    as_of = date(2026, 7, 19)

    cache.put("AAPL", "yfinance", Period.ANNUAL, "5y", as_of, fundamentals)
    loaded = cache.get("AAPL", "yfinance", Period.ANNUAL, "5y", as_of)

    assert loaded == fundamentals


def test_key_distinguishes_source_period_range_and_date(tmp_path):
    cache = TemplateCache(cache_dir=tmp_path)
    fundamentals = _fundamentals()
    as_of = date(2026, 7, 19)
    cache.put("AAPL", "yfinance", Period.ANNUAL, "5y", as_of, fundamentals)

    assert cache.get("AAPL", "twelvedata", Period.ANNUAL, "5y", as_of) is None
    assert cache.get("AAPL", "yfinance", Period.QUARTERLY, "5y", as_of) is None
    assert cache.get("AAPL", "yfinance", Period.ANNUAL, "10y", as_of) is None
    assert cache.get("AAPL", "yfinance", Period.ANNUAL, "5y", date(2026, 7, 20)) is None


def test_latest_returns_none_when_nothing_cached(tmp_path):
    cache = TemplateCache(cache_dir=tmp_path)
    assert cache.latest("AAPL", "yfinance", Period.ANNUAL, "5y") is None


def test_latest_returns_most_recent_dated_entry(tmp_path):
    cache = TemplateCache(cache_dir=tmp_path)
    fundamentals = _fundamentals()

    cache.put("AAPL", "yfinance", Period.ANNUAL, "5y", date(2026, 7, 1), fundamentals)
    cache.put("AAPL", "yfinance", Period.ANNUAL, "5y", date(2026, 7, 19), fundamentals)

    latest = cache.latest("AAPL", "yfinance", Period.ANNUAL, "5y")
    assert latest == fundamentals
