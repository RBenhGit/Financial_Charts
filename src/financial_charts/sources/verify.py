from pydantic import BaseModel

from financial_charts.sources.base import DataSource
from financial_charts.template.models import CompanyFundamentals, Market, Period

# A TASE price above this looks like raw agorot that was never divided into shekels.
_AGOROT_NOT_CONVERTED_THRESHOLD = 100_000


class ReconciliationReport(BaseModel):
    missing_metrics: list[str]
    undeclared_extras: list[str]
    unit_warnings: list[str]
    history_points: dict[str, int]

    @property
    def has_mismatch(self) -> bool:
        return bool(self.missing_metrics)


def reconcile(
    adapter: DataSource, ticker: str, market: Market, period: Period, range: str
) -> ReconciliationReport:
    """Live-fetch `ticker` and compare the response against the adapter's declared `Capability`.

    Dev-time only — invoked by the `verify-source` CLI, never by a normal render.
    """
    capability = adapter.capability()
    fundamentals = adapter.fetch(ticker, market, period, range)

    declared = capability.metrics
    returned_available = {
        metric_id
        for metric_id, series in fundamentals.series.items()
        if series.available
    }
    returned_all = set(fundamentals.series.keys())

    missing_metrics = sorted(declared - returned_available)
    undeclared_extras = sorted(returned_all - declared)
    unit_warnings = _unit_warnings(market, fundamentals)
    history_points = {
        metric_id: len(series.points)
        for metric_id, series in fundamentals.series.items()
    }

    return ReconciliationReport(
        missing_metrics=missing_metrics,
        undeclared_extras=undeclared_extras,
        unit_warnings=unit_warnings,
        history_points=history_points,
    )


def _unit_warnings(market: Market, fundamentals: CompanyFundamentals) -> list[str]:
    warnings: list[str] = []
    price = fundamentals.series.get("price")
    if market == Market.TASE and price and price.available and price.points:
        last_price = price.points[-1].value
        if last_price.value > _AGOROT_NOT_CONVERTED_THRESHOLD:
            warnings.append(
                f"TASE price {last_price.value} looks like unconverted agorot "
                "(expected shekels after /100 conversion)"
            )
    return warnings
