import os

import requests
from dotenv import load_dotenv

from financial_charts.sources.base import (
    Capability,
    MissingCredentials,
    SourceUnavailable,
    TickerNotFound,
)
from financial_charts.sources.twelvedata.capability import CAPABILITY
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

_BASE_URL = "https://api.twelvedata.com"

# Coarser intervals for longer ranges keep the point count sane for a static chart.
_PRICE_INTERVAL_BY_RANGE = {
    "6m": ("1day", 130),
    "1y": ("1day", 260),
    "3y": ("1week", 160),
    "5y": ("1week", 260),
    "10y": ("1month", 120),
    "max": ("1month", 240),
}

_CURRENCY_BY_CODE = {"USD": Currency.USD, "ILS": Currency.ILS}


def _map_currency(code: str | None) -> Currency | None:
    if code == "ILA":
        return Currency.ILS  # agorot; converted to shekels at the value level
    return _CURRENCY_BY_CODE.get(code or "")


class TwelveDataAdapter:
    def __init__(self, api_key: str | None = None):
        load_dotenv()
        self._api_key = api_key or os.environ.get("TWELVEDATA_API_KEY")
        if not self._api_key:
            raise MissingCredentials("TWELVEDATA_API_KEY is not set")

    def capability(self) -> Capability:
        return CAPABILITY

    def fetch(
        self, ticker: str, market: Market, period: Period, range: str
    ) -> CompanyFundamentals:
        symbol = ticker.removesuffix(".TA") if market == Market.TASE else ticker
        mic_code = "XTAE" if market == Market.TASE else None

        price_json = self._get(
            "time_series", symbol=symbol, mic_code=mic_code, **_price_params(range)
        )
        income_json = self._get(
            "income_statement", symbol=symbol, mic_code=mic_code, period=period.value
        )
        cashflow_json = self._get(
            "cash_flow", symbol=symbol, mic_code=mic_code, period=period.value
        )

        display_currency = Currency.ILS if market == Market.TASE else Currency.USD
        source_limits: list[str] = []

        series: dict[str, MetricSeries] = {
            "price": _price_series(price_json, source_limits),
        }
        income_statement = income_json.get("income_statement", [])
        cashflow_statement = cashflow_json.get("cash_flow", [])
        financial_currency = _map_currency(income_json.get("meta", {}).get("currency"))

        series["revenue"] = _income_series(
            income_statement, "sales", financial_currency, "revenue", source_limits
        )
        series["net_income"] = _income_series(
            income_statement,
            "net_income",
            financial_currency,
            "net_income",
            source_limits,
        )
        series["eps"] = _income_series(
            income_statement, "eps_diluted", financial_currency, "eps", source_limits
        )
        series["free_cash_flow"] = _cashflow_series(
            cashflow_statement, financial_currency, source_limits
        )
        series["gross_margin"] = _margin_series(
            income_statement, "gross_profit", "sales", "gross_margin", source_limits
        )
        series["net_margin"] = _margin_series(
            income_statement, "net_income", "sales", "net_margin", source_limits
        )

        return CompanyFundamentals(
            ticker=ticker,
            market=market,
            currency=display_currency,
            period=period,
            range=range,
            series=series,
            source_limits=source_limits,
        )

    def _get(self, endpoint: str, **params) -> dict:
        query = {k: v for k, v in params.items() if v is not None}
        query["apikey"] = self._api_key
        response = requests.get(f"{_BASE_URL}/{endpoint}", params=query, timeout=30)
        try:
            payload = response.json()
        except ValueError as exc:
            raise SourceUnavailable(
                f"twelvedata returned a non-JSON response: {response.text[:200]}"
            ) from exc

        if isinstance(payload, dict) and payload.get("status") == "error":
            if payload.get("code") == 404:
                raise TickerNotFound(params.get("symbol", ""))
            raise SourceUnavailable(payload.get("message", "twelvedata request failed"))
        return payload


def _price_params(range: str) -> dict:
    interval, outputsize = _PRICE_INTERVAL_BY_RANGE.get(range.lower(), ("1month", 240))
    return {"interval": interval, "outputsize": outputsize}


def _price_series(price_json: dict, source_limits: list[str]) -> MetricSeries:
    meta = price_json.get("meta", {})
    values = price_json.get("values", [])
    currency = _map_currency(meta.get("currency"))
    if not values or currency is None:
        source_limits.append("price: no data available for this ticker")
        return MetricSeries(metric_id="price", points=[], available=False)

    is_agorot = meta.get("currency") == "ILA"
    points = [
        Point(
            date=row["datetime"],
            value=Money(
                value=(float(row["close"]) / 100 if is_agorot else float(row["close"])),
                currency=currency,
                scale=Unit.ONES,
            ),
        )
        for row in reversed(values)
    ]
    return MetricSeries(metric_id="price", points=points, available=True)


def _income_series(
    income_statement: list[dict],
    field: str,
    currency: Currency | None,
    metric_id: str,
    source_limits: list[str],
) -> MetricSeries:
    if currency is None:
        source_limits.append(f"{metric_id}: no data available for this ticker")
        return MetricSeries(metric_id=metric_id, points=[], available=False)

    points = [
        Point(
            date=row["fiscal_date"],
            value=Money(value=float(row[field]), currency=currency, scale=Unit.ONES),
        )
        for row in reversed(income_statement)
        if row.get(field) is not None
    ]
    if not points:
        source_limits.append(f"{metric_id}: no data available for this ticker")
        return MetricSeries(metric_id=metric_id, points=[], available=False)
    return MetricSeries(metric_id=metric_id, points=points, available=True)


def _cashflow_series(
    cashflow_statement: list[dict], currency: Currency | None, source_limits: list[str]
) -> MetricSeries:
    if currency is None:
        source_limits.append("free_cash_flow: no data available for this ticker")
        return MetricSeries(metric_id="free_cash_flow", points=[], available=False)

    points = []
    for row in reversed(cashflow_statement):
        fcf = row.get("free_cash_flow")
        if fcf is None:
            operating = row.get("operating_activities", {}).get("operating_cash_flow")
            capex = row.get("investing_activities", {}).get("capital_expenditures")
            fcf = (
                operating + capex
                if operating is not None and capex is not None
                else None
            )
        if fcf is not None:
            points.append(
                Point(
                    date=row["fiscal_date"],
                    value=Money(value=float(fcf), currency=currency, scale=Unit.ONES),
                )
            )
    if not points:
        source_limits.append("free_cash_flow: no data available for this ticker")
        return MetricSeries(metric_id="free_cash_flow", points=[], available=False)
    return MetricSeries(metric_id="free_cash_flow", points=points, available=True)


def _margin_series(
    income_statement: list[dict],
    numerator_field: str,
    denominator_field: str,
    metric_id: str,
    source_limits: list[str],
) -> MetricSeries:
    points = []
    for row in reversed(income_statement):
        num, den = row.get(numerator_field), row.get(denominator_field)
        if num is not None and den:
            points.append(Point(date=row["fiscal_date"], value=float(num) / float(den)))
    if not points:
        source_limits.append(f"{metric_id}: no data available for this ticker")
        return MetricSeries(metric_id=metric_id, points=[], available=False)
    return MetricSeries(metric_id=metric_id, points=points, available=True)
