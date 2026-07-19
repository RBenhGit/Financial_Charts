from matplotlib.axes import Axes

from financial_charts.template.models import CompanyFundamentals


class MarginsChart:
    name = "margins"
    title = "Margins"
    required_metrics = ["gross_margin", "net_margin"]

    def render(self, ax: Axes, fundamentals: CompanyFundamentals) -> None:
        for metric_id, label in [
            ("gross_margin", "Gross Margin"),
            ("net_margin", "Net Margin"),
        ]:
            points = fundamentals.series[metric_id].points
            dates = [p.date for p in points]
            percentages = [p.value * 100 for p in points]
            ax.plot(dates, percentages, marker="o", label=label)

        ax.set_ylabel("Margin (%)")
        ax.legend(fontsize=7, loc="upper left")
