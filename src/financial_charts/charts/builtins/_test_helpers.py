from datetime import date

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


def money_series(
    metric_id: str, values: list[float], currency=Currency.USD
) -> MetricSeries:
    points = [
        Point(
            date=date(2020 + i, 1, 1),
            value=Money(value=v, currency=currency, scale=Unit.ONES),
        )
        for i, v in enumerate(values)
    ]
    return MetricSeries(metric_id=metric_id, points=points, available=True)


def ratio_series(metric_id: str, values: list[float]) -> MetricSeries:
    points = [Point(date=date(2020 + i, 1, 1), value=v) for i, v in enumerate(values)]
    return MetricSeries(metric_id=metric_id, points=points, available=True)


def unavailable_series(metric_id: str) -> MetricSeries:
    return MetricSeries(metric_id=metric_id, points=[], available=False)


def fundamentals_with(
    series: dict[str, MetricSeries], currency=Currency.USD
) -> CompanyFundamentals:
    return CompanyFundamentals(
        ticker="TEST",
        market=Market.US,
        currency=currency,
        period=Period.ANNUAL,
        range="5y",
        series=series,
    )
