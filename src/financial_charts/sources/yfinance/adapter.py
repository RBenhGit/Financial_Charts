import pandas as pd
import yfinance as yf

from financial_charts.sources.base import Capability, TickerNotFound
from financial_charts.sources.yfinance.capability import CAPABILITY
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

# yfinance `history(period=...)` accepts each of these directly.
_YFINANCE_PERIODS = {
    "6m": "6mo",
    "1y": "1y",
    "3y": "3y",
    "5y": "5y",
    "10y": "10y",
    "max": "max",
}

_CURRENCY_BY_CODE = {"USD": Currency.USD, "ILS": Currency.ILS}


def _map_currency(code: str | None) -> Currency | None:
    if code == "ILA":
        return Currency.ILS  # agorot; converted to shekels at the value level
    return _CURRENCY_BY_CODE.get(code or "")


class YFinanceAdapter:
    def capability(self) -> Capability:
        return CAPABILITY

    def fetch(
        self, ticker: str, market: Market, period: Period, range: str
    ) -> CompanyFundamentals:
        yf_ticker = yf.Ticker(ticker)
        info = yf_ticker.info
        history = yf_ticker.history(period=_range_to_yfinance_period(range))
        if history.empty and len(info) <= 1:
            raise TickerNotFound(ticker)

        price_currency = _map_currency(info.get("currency"))
        financial_currency = _map_currency(info.get("financialCurrency"))
        display_currency = Currency.ILS if market == Market.TASE else Currency.USD

        series: dict[str, MetricSeries] = {}
        source_limits: list[str] = []

        series["price"] = _price_series(
            history, info.get("currency"), price_currency, source_limits
        )

        statements = (
            (yf_ticker.financials, yf_ticker.cashflow)
            if period == Period.ANNUAL
            else (yf_ticker.quarterly_financials, yf_ticker.quarterly_cashflow)
        )
        financials, cashflow = statements

        series["revenue"] = _statement_series(
            financials,
            "Total Revenue",
            financial_currency,
            Unit.ONES,
            "revenue",
            source_limits,
        )
        series["net_income"] = _statement_series(
            financials,
            "Net Income",
            financial_currency,
            Unit.ONES,
            "net_income",
            source_limits,
        )
        series["eps"] = _statement_series(
            financials,
            "Diluted EPS",
            financial_currency,
            Unit.ONES,
            "eps",
            source_limits,
        )
        series["free_cash_flow"] = _statement_series(
            cashflow,
            "Free Cash Flow",
            financial_currency,
            Unit.ONES,
            "free_cash_flow",
            source_limits,
        )
        series["gross_margin"] = _margin_series(
            financials, "Gross Profit", "Total Revenue", "gross_margin", source_limits
        )
        series["net_margin"] = _margin_series(
            financials, "Net Income", "Total Revenue", "net_margin", source_limits
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


def _range_to_yfinance_period(range: str) -> str:
    return _YFINANCE_PERIODS.get(range.lower(), "max")


def _price_series(
    history: pd.DataFrame,
    raw_currency_code: str | None,
    currency: Currency | None,
    source_limits: list[str],
) -> MetricSeries:
    if history.empty or currency is None:
        source_limits.append("price: no data available for this ticker")
        return MetricSeries(metric_id="price", points=[], available=False)

    is_agorot = raw_currency_code == "ILA"
    points = [
        Point(
            date=idx.date(),
            value=Money(
                value=(row["Close"] / 100 if is_agorot else row["Close"]),
                currency=currency,
                scale=Unit.ONES,
            ),
        )
        for idx, row in history.iterrows()
    ]
    return MetricSeries(metric_id="price", points=points, available=True)


def _statement_series(
    statement: pd.DataFrame,
    row_name: str,
    currency: Currency | None,
    scale: Unit,
    metric_id: str,
    source_limits: list[str],
) -> MetricSeries:
    if statement.empty or row_name not in statement.index or currency is None:
        source_limits.append(f"{metric_id}: no data available for this ticker")
        return MetricSeries(metric_id=metric_id, points=[], available=False)

    row = statement.loc[row_name]
    points = [
        Point(
            date=col.date(),
            value=Money(value=float(val), currency=currency, scale=scale),
        )
        for col, val in row.items()
        if pd.notna(val)
    ]
    if not points:
        source_limits.append(f"{metric_id}: no data available for this ticker")
        return MetricSeries(metric_id=metric_id, points=[], available=False)
    return MetricSeries(metric_id=metric_id, points=points, available=True)


def _margin_series(
    financials: pd.DataFrame,
    numerator_row: str,
    denominator_row: str,
    metric_id: str,
    source_limits: list[str],
) -> MetricSeries:
    if (
        financials.empty
        or numerator_row not in financials.index
        or denominator_row not in financials.index
    ):
        source_limits.append(f"{metric_id}: no data available for this ticker")
        return MetricSeries(metric_id=metric_id, points=[], available=False)

    numerator = financials.loc[numerator_row]
    denominator = financials.loc[denominator_row]
    points = []
    for col in financials.columns:
        num, den = numerator.get(col), denominator.get(col)
        if pd.notna(num) and pd.notna(den) and den != 0:
            points.append(Point(date=col.date(), value=float(num) / float(den)))
    if not points:
        source_limits.append(f"{metric_id}: no data available for this ticker")
        return MetricSeries(metric_id=metric_id, points=[], available=False)
    return MetricSeries(metric_id=metric_id, points=points, available=True)
