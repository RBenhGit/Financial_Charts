from financial_charts.charts.base import Chart
from financial_charts.charts.builtins.eps import EPSChart
from financial_charts.charts.builtins.fcf_margin import FCFMarginChart
from financial_charts.charts.builtins.free_cash_flow import FreeCashFlowChart
from financial_charts.charts.builtins.margins import MarginsChart
from financial_charts.charts.builtins.net_income import NetIncomeChart
from financial_charts.charts.builtins.price import PriceChart
from financial_charts.charts.builtins.revenue import RevenueChart
from financial_charts.sources.registry import get_capability, registered_sources

_CHARTS: list[Chart] = [
    PriceChart(),
    RevenueChart(),
    NetIncomeChart(),
    FreeCashFlowChart(),
    EPSChart(),
    MarginsChart(),
    FCFMarginChart(),
]


def available_charts() -> list[Chart]:
    """Every chart registered in the catalog — what a user's picker chooses from."""
    return list(_CHARTS)


def get_chart(chart_id: str) -> Chart:
    for chart in _CHARTS:
        if chart.name == chart_id:
            return chart
    raise KeyError(
        f"unknown chart {chart_id!r}; available charts: "
        f"{sorted(c.name for c in _CHARTS)}"
    )


def supported_by(chart: Chart) -> frozenset[str]:
    """Registered source names whose declared `Capability` supplies every metric
    `chart` requires.

    Reads only the static `capability.py` declarations (offline, no adapter
    instantiated) — lets a chart developer see, at design time, which sources
    can actually render a chart before shipping it.
    """
    return frozenset(
        name
        for name in registered_sources()
        if set(chart.required_metrics) <= get_capability(name).metrics
    )


def chart_support() -> dict[str, frozenset[str]]:
    """Chart id -> the sources that can supply it, for every catalog chart."""
    return {chart.name: supported_by(chart) for chart in _CHARTS}
