from financial_charts.charts.base import Chart
from financial_charts.charts.builtins.eps import EPSChart
from financial_charts.charts.builtins.free_cash_flow import FreeCashFlowChart
from financial_charts.charts.builtins.margins import MarginsChart
from financial_charts.charts.builtins.net_income import NetIncomeChart
from financial_charts.charts.builtins.price import PriceChart
from financial_charts.charts.builtins.revenue import RevenueChart

_CHART_SETS: dict[str, list[Chart]] = {
    "fundamentals": [
        PriceChart(),
        RevenueChart(),
        NetIncomeChart(),
        FreeCashFlowChart(),
        EPSChart(),
        MarginsChart(),
    ]
}


def register_chart_set(name: str, charts: list[Chart]) -> None:
    """Register a custom named chart set for the dashboard to render."""
    _CHART_SETS[name] = charts


def get_chart_set(name: str) -> list[Chart]:
    try:
        return _CHART_SETS[name]
    except KeyError:
        raise KeyError(
            f"unknown chart set {name!r}; registered sets: {sorted(_CHART_SETS)}"
        ) from None
