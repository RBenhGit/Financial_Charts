import matplotlib

matplotlib.use("Agg")

from datetime import date
from unittest.mock import patch

import pytest

from financial_charts.sources.base import MissingCredentials, TickerNotFound
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
from financial_charts.web.app import create_app


def _fundamentals() -> CompanyFundamentals:
    return CompanyFundamentals(
        ticker="AAPL",
        market=Market.US,
        currency=Currency.USD,
        period=Period.ANNUAL,
        range="10y",
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


@pytest.fixture
def client():
    return create_app().test_client()


def test_index_shows_the_form(client):
    response = client.get("/")

    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert 'name="ticker"' in body
    assert "yfinance" in body
    assert "fundamentals" in body


def test_render_returns_dashboard_html(client):
    with patch(
        "financial_charts.web.app.load_fundamentals", return_value=_fundamentals()
    ):
        response = client.get("/render?ticker=AAPL&source=yfinance")

    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "AAPL" in body
    assert "<img" in body


def test_render_without_ticker_is_a_400(client):
    response = client.get("/render")
    assert response.status_code == 400
    assert "Enter a ticker" in response.get_data(as_text=True)


def test_render_unknown_ticker_shows_not_found(client):
    with patch(
        "financial_charts.web.app.load_fundamentals",
        side_effect=TickerNotFound("ZZZ"),
    ):
        response = client.get("/render?ticker=ZZZ")

    assert response.status_code == 404
    assert "not found" in response.get_data(as_text=True).lower()


def test_render_missing_credentials_names_env_var(client):
    with patch(
        "financial_charts.web.app.load_fundamentals",
        side_effect=MissingCredentials("TWELVEDATA_API_KEY is not set"),
    ):
        response = client.get("/render?ticker=AAPL&source=twelvedata")

    assert response.status_code == 400
    assert "TWELVEDATA_API_KEY" in response.get_data(as_text=True)


def test_render_unknown_source_shows_error(client):
    response = client.get("/render?ticker=AAPL&source=not-a-real-source")

    assert response.status_code == 400
    assert "unknown data source" in response.get_data(as_text=True)
