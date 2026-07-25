from matplotlib.axes import Axes

from financial_charts.charts.base import draw_no_data, render_kpi_value
from financial_charts.template.derived import ratio
from financial_charts.template.models import CompanyFundamentals


class PERatioChart:
    name = "pe_ratio"
    title = "P/E (Trailing)"
    required_metrics = ["price", "eps"]

    def render(self, ax: Axes, fundamentals: CompanyFundamentals) -> None:
        price = fundamentals.series["price"].points[-1].value
        eps = fundamentals.series["eps"].points[-1].value
        try:
            pe = ratio(price, eps)
        except (ZeroDivisionError, ValueError):
            # Zero trailing EPS, or a currency mismatch between the price and
            # financial statement currencies — not a crash, just no P/E to show.
            draw_no_data(ax)
            return
        render_kpi_value(ax, f"{pe:.1f}x")
