from matplotlib.axes import Axes

from financial_charts.charts.base import draw_no_data, render_kpi_value
from financial_charts.template.models import CompanyFundamentals


class DividendYieldChart:
    name = "dividend_yield"
    title = "Dividend Yield"
    required_metrics = ["price", "dividends_paid", "shares_outstanding"]

    def render(self, ax: Axes, fundamentals: CompanyFundamentals) -> None:
        price = fundamentals.series["price"].points[-1].value
        dividends = fundamentals.series["dividends_paid"].points[-1].value
        shares = fundamentals.series["shares_outstanding"].points[-1].value
        try:
            dividend_per_share = dividends.as_base_units() / shares
            dividend_yield = dividend_per_share / price.as_base_units() * 100
        except ZeroDivisionError:
            draw_no_data(ax)
            return
        render_kpi_value(ax, f"{dividend_yield:.2f}%")
