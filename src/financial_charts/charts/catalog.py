from financial_charts.charts.base import Chart
from financial_charts.charts.builtins.eps import EPSChart
from financial_charts.charts.builtins.fcf_margin import FCFMarginChart
from financial_charts.charts.builtins.free_cash_flow import FreeCashFlowChart
from financial_charts.charts.builtins.margins import MarginsChart
from financial_charts.charts.builtins.net_income import NetIncomeChart
from financial_charts.charts.builtins.price import PriceChart
from financial_charts.charts.builtins.revenue import RevenueChart

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
