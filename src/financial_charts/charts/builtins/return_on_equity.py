from matplotlib.axes import Axes

from financial_charts.charts.base import draw_no_data, render_kpi_value
from financial_charts.template.derived import ratio
from financial_charts.template.models import CompanyFundamentals


class ReturnOnEquityChart:
    name = "return_on_equity"
    title = "ROE"
    required_metrics = ["net_income", "total_equity"]

    def render(self, ax: Axes, fundamentals: CompanyFundamentals) -> None:
        net_income = fundamentals.series["net_income"].points[-1].value
        equity = fundamentals.series["total_equity"].points[-1].value
        try:
            roe = ratio(net_income, equity) * 100
        except (ZeroDivisionError, ValueError):
            draw_no_data(ax)
            return
        render_kpi_value(ax, f"{roe:.1f}%")
