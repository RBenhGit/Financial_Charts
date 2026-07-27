"""Shape a `CompanyFundamentals` chart set into JSON for the interactive web dashboard.

Independent of matplotlib and of every `charts/builtins/*.py` file: each chart's
*data prep* (as opposed to its matplotlib drawing) is re-derived here from the
template, reusing only published functions (`charts.base.currency_symbol`/
`format_compact_number`, `template.derived.resolve`/`ratio`/the `DerivedMetric`
constants). A handful of charts (market cap, P/E, dividend yield, ROE, the
valuation nearest-price join, price's SMA overlay) have their small inline math
re-implemented here rather than imported, since it isn't externalized from its
chart file today — see PROGRESS.md for the accepted duplication/drift trade-off.

Values are laundered through Pydantic (`ChartDataResponse.model_dump_json()`),
never `flask.jsonify()`: `jsonify` reproduces raw `NaN` tokens (invalid JSON),
which pandas SMA warm-up periods and other computed ratios can produce.
"""

from __future__ import annotations

from datetime import date
from typing import Annotated, Callable, Literal

import pandas as pd
from pydantic import BaseModel, Field

from financial_charts.charts.base import currency_symbol, format_compact_number
from financial_charts.charts.registry import get_chart_set
from financial_charts.template.derived import (
    BOOK_VALUE_PER_SHARE,
    CURRENT_RATIO,
    DEBT_TO_EQUITY,
    FCF_MARGIN,
    ROCE,
    ROIC,
    DerivedMetric,
    ratio,
    resolve,
)
from financial_charts.template.models import CompanyFundamentals, Point


class SeriesSpec(BaseModel):
    label: str
    dates: list[date]
    values: list[float]


class _ChartSpecBase(BaseModel):
    name: str
    title: str


class BarChartSpec(_ChartSpecBase):
    kind: Literal["bar"] = "bar"
    y_label: str
    series: list[SeriesSpec]


class LineChartSpec(_ChartSpecBase):
    kind: Literal["line"] = "line"
    y_label: str
    series: list[SeriesSpec]


class KpiChartSpec(_ChartSpecBase):
    kind: Literal["kpi"] = "kpi"
    value_text: str


class NoDataChartSpec(_ChartSpecBase):
    kind: Literal["no_data"] = "no_data"


ChartSpec = Annotated[
    BarChartSpec | LineChartSpec | KpiChartSpec | NoDataChartSpec,
    Field(discriminator="kind"),
]


class ChartDataResponse(BaseModel):
    ticker: str
    market: str
    currency: str
    source_limits: list[str] = []
    charts: list[ChartSpec]


def build_chart_specs(
    fundamentals: CompanyFundamentals, chart_set_name: str
) -> list[dict]:
    """One JSON-serializable chart spec dict per chart in `chart_set_name`, in order.

    Mirrors `charts.base.render_or_no_data`'s required-metrics gate; a chart
    whose gate passes can still shape to `None` (e.g. a derived value with no
    overlapping dates across otherwise-available inputs), which also degrades
    to a `no_data` spec, same as the matplotlib path.
    """
    specs: list[dict] = []
    for chart in get_chart_set(chart_set_name):
        missing = [
            metric_id
            for metric_id in chart.required_metrics
            if (series := fundamentals.series.get(metric_id)) is None
            or not series.available
        ]
        body = None if missing else _SHAPERS[chart.name](fundamentals)
        if body is None:
            specs.append({"kind": "no_data", "name": chart.name, "title": chart.title})
        else:
            specs.append({"name": chart.name, "title": chart.title, **body})
    return specs


def _money_bar(metric_id: str) -> Callable[[CompanyFundamentals], dict]:
    """Single-series bar of a raw `Money.value` (not base units) — matches
    `render_money_bar`'s scale-relative plotting exactly."""

    def shaper(fundamentals: CompanyFundamentals) -> dict:
        points = fundamentals.series[metric_id].points
        label = metric_id.replace("_", " ").title()
        return {
            "kind": "bar",
            "y_label": f"{label} ({currency_symbol(fundamentals)})",
            "series": [
                {
                    "label": label,
                    "dates": [p.date for p in points],
                    "values": [p.value.value for p in points],
                }
            ],
        }

    return shaper


def _shares_outstanding(fundamentals: CompanyFundamentals) -> dict:
    points = fundamentals.series["shares_outstanding"].points
    return {
        "kind": "bar",
        "y_label": "Shares",
        "series": [
            {
                "label": "Shares",
                "dates": [p.date for p in points],
                "values": [p.value for p in points],
            }
        ],
    }


def _money_line(
    pairs: list[tuple[str, str]],
) -> Callable[[CompanyFundamentals], dict]:
    """Multi-series line of `Money.as_base_units()` — matches `render_money_line`."""

    def shaper(fundamentals: CompanyFundamentals) -> dict:
        series = []
        for metric_id, label in pairs:
            points = fundamentals.series[metric_id].points
            series.append(
                {
                    "label": label,
                    "dates": [p.date for p in points],
                    "values": [p.value.as_base_units() for p in points],
                }
            )
        return {
            "kind": "line",
            "y_label": f"({currency_symbol(fundamentals)})",
            "series": series,
        }

    return shaper


def _margins(fundamentals: CompanyFundamentals) -> dict:
    series = []
    for metric_id, label in [
        ("gross_margin", "Gross Margin"),
        ("net_margin", "Net Margin"),
    ]:
        points = fundamentals.series[metric_id].points
        series.append(
            {
                "label": label,
                "dates": [p.date for p in points],
                "values": [p.value * 100 for p in points],
            }
        )
    return {"kind": "line", "y_label": "Margin (%)", "series": series}


def _percentage_line_derived(
    derived: DerivedMetric, label: str, y_label: str
) -> Callable[[CompanyFundamentals], dict | None]:
    def shaper(fundamentals: CompanyFundamentals) -> dict | None:
        series = resolve(fundamentals, derived)
        if not series.available:
            return None
        return {
            "kind": "line",
            "y_label": y_label,
            "series": [
                {
                    "label": label,
                    "dates": [p.date for p in series.points],
                    "values": [p.value * 100 for p in series.points],
                }
            ],
        }

    return shaper


def _ratio_line_derived(
    derived: DerivedMetric, label: str, y_label: str
) -> Callable[[CompanyFundamentals], dict | None]:
    def shaper(fundamentals: CompanyFundamentals) -> dict | None:
        series = resolve(fundamentals, derived)
        if not series.available:
            return None
        return {
            "kind": "line",
            "y_label": y_label,
            "series": [
                {
                    "label": label,
                    "dates": [p.date for p in series.points],
                    "values": [p.value for p in series.points],
                }
            ],
        }

    return shaper


def _return_on_capital(fundamentals: CompanyFundamentals) -> dict | None:
    roce = resolve(fundamentals, ROCE)
    roic = resolve(fundamentals, ROIC)
    if not roce.available or not roic.available:
        return None
    return {
        "kind": "line",
        "y_label": "Return (%)",
        "series": [
            {
                "label": "ROCE",
                "dates": [p.date for p in roce.points],
                "values": [p.value * 100 for p in roce.points],
            },
            {
                "label": "ROIC",
                "dates": [p.date for p in roic.points],
                "values": [p.value * 100 for p in roic.points],
            },
        ],
    }


def _nearest_price(price_points: list[Point], target: date) -> float:
    closest = min(price_points, key=lambda p: abs((p.date - target).days))
    return closest.value.value


def _valuation(fundamentals: CompanyFundamentals) -> dict | None:
    book_value = resolve(fundamentals, BOOK_VALUE_PER_SHARE)
    price_points = fundamentals.series["price"].points
    equity_points = fundamentals.series["total_equity"].points
    if not book_value.available or not price_points or not equity_points:
        return None
    if price_points[0].value.currency != equity_points[0].value.currency:
        return None

    dates = []
    values = []
    for point in book_value.points:
        if point.value == 0:
            continue
        dates.append(point.date)
        values.append(_nearest_price(price_points, point.date) / point.value)

    if not values:
        return None
    return {
        "kind": "line",
        "y_label": "Price / Book (x)",
        "series": [{"label": "P/B", "dates": dates, "values": values}],
    }


def _price(fundamentals: CompanyFundamentals) -> dict:
    points = fundamentals.series["price"].points
    dates = [p.date for p in points]
    closes = pd.Series([p.value.value for p in points], index=dates)

    series = [{"label": "Close", "dates": dates, "values": closes.tolist()}]
    for window in (50, 150, 200):
        if len(closes) >= window:
            sma = closes.rolling(window=window).mean()
            series.append(
                {"label": f"SMA {window}", "dates": dates, "values": sma.tolist()}
            )

    return {
        "kind": "line",
        "y_label": f"Price ({currency_symbol(fundamentals)})",
        "series": series,
    }


def _market_cap(fundamentals: CompanyFundamentals) -> dict:
    price = fundamentals.series["price"].points[-1].value
    shares = fundamentals.series["shares_outstanding"].points[-1].value
    market_cap = price.as_base_units() * shares
    return {
        "kind": "kpi",
        "value_text": f"{currency_symbol(fundamentals)}{format_compact_number(market_cap)}",
    }


def _pe_ratio(fundamentals: CompanyFundamentals) -> dict | None:
    price = fundamentals.series["price"].points[-1].value
    eps = fundamentals.series["eps"].points[-1].value
    try:
        pe = ratio(price, eps)
    except (ZeroDivisionError, ValueError):
        return None
    return {"kind": "kpi", "value_text": f"{pe:.1f}x"}


def _dividend_yield(fundamentals: CompanyFundamentals) -> dict | None:
    price = fundamentals.series["price"].points[-1].value
    dividends = fundamentals.series["dividends_paid"].points[-1].value
    shares = fundamentals.series["shares_outstanding"].points[-1].value
    try:
        price.require_same_currency(dividends)
        dividend_per_share = dividends.as_base_units() / shares
        dividend_yield = dividend_per_share / price.as_base_units() * 100
    except (ZeroDivisionError, ValueError):
        return None
    return {"kind": "kpi", "value_text": f"{dividend_yield:.2f}%"}


def _return_on_equity(fundamentals: CompanyFundamentals) -> dict | None:
    net_income = fundamentals.series["net_income"].points[-1].value
    equity = fundamentals.series["total_equity"].points[-1].value
    try:
        roe = ratio(net_income, equity) * 100
    except (ZeroDivisionError, ValueError):
        return None
    return {"kind": "kpi", "value_text": f"{roe:.1f}%"}


_SHAPERS: dict[str, Callable[[CompanyFundamentals], dict | None]] = {
    "price": _price,
    "revenue": _money_bar("revenue"),
    "net_income": _money_bar("net_income"),
    "free_cash_flow": _money_bar("free_cash_flow"),
    "eps": _money_bar("eps"),
    "margins": _margins,
    "fcf_margin": _percentage_line_derived(FCF_MARGIN, "FCF Margin", "FCF Margin (%)"),
    "ebitda": _money_bar("ebitda"),
    "expenses": _money_line(
        [
            ("research_and_development", "R&D"),
            ("selling_general_administrative", "SG&A"),
        ]
    ),
    "dividends": _money_bar("dividends_paid"),
    "shares_outstanding": _shares_outstanding,
    "cash_and_debt": _money_line(
        [("cash_and_equivalents", "Cash"), ("total_debt", "Total Debt")]
    ),
    "assets_equity_liabilities": _money_line(
        [
            ("total_assets", "Assets"),
            ("total_equity", "Equity"),
            ("total_liabilities", "Liabilities"),
        ]
    ),
    "debt_leverage": _ratio_line_derived(
        DEBT_TO_EQUITY, "Debt / Equity", "Debt / Equity (x)"
    ),
    "ratios": _ratio_line_derived(CURRENT_RATIO, "Current Ratio", "Current Ratio (x)"),
    "return_on_capital": _return_on_capital,
    "valuation": _valuation,
    "market_cap": _market_cap,
    "pe_ratio": _pe_ratio,
    "dividend_yield": _dividend_yield,
    "return_on_equity": _return_on_equity,
}
