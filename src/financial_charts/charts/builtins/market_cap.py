from matplotlib.axes import Axes

from financial_charts.charts.base import (
    currency_symbol,
    format_compact_number,
    render_kpi_value,
)
from financial_charts.template.models import CompanyFundamentals


class MarketCapChart:
    name = "market_cap"
    title = "Market Cap"
    required_metrics = ["price", "shares_outstanding"]

    def render(self, ax: Axes, fundamentals: CompanyFundamentals) -> None:
        price = fundamentals.series["price"].points[-1].value
        shares = fundamentals.series["shares_outstanding"].points[-1].value
        market_cap = price.as_base_units() * shares
        render_kpi_value(
            ax, f"{currency_symbol(fundamentals)}{format_compact_number(market_cap)}"
        )
