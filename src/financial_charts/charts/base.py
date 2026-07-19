from typing import Protocol

from matplotlib.axes import Axes

from financial_charts.template.models import CompanyFundamentals


class Chart(Protocol):
    name: str
    title: str
    required_metrics: list[str]

    def render(self, ax: Axes, fundamentals: CompanyFundamentals) -> None: ...


def draw_no_data(ax: Axes) -> None:
    """Draw the shared "No Data" placeholder on `ax`.

    Public so a chart whose data is unavailable only after computation (e.g. a
    derived quantity whose inputs don't share any overlapping date) can fall
    back to the same card as a chart with a missing required metric.
    """
    ax.text(
        0.5,
        0.5,
        "No Data",
        ha="center",
        va="center",
        transform=ax.transAxes,
        fontsize=14,
        color="gray",
    )
    ax.set_xticks([])
    ax.set_yticks([])


def render_or_no_data(
    chart: Chart, ax: Axes, fundamentals: CompanyFundamentals
) -> None:
    """Render `chart`, falling back to a "No Data" card if a required metric is unavailable.

    A source's declared gaps are never a crash — the dashboard grid always renders
    the full layout, with unavailable metrics shown as an explicit "No Data" card.
    """
    missing = [
        metric_id
        for metric_id in chart.required_metrics
        if not fundamentals.series.get(metric_id, _UNAVAILABLE).available
    ]
    ax.set_title(chart.title)
    if missing:
        draw_no_data(ax)
        return
    chart.render(ax, fundamentals)


class _Unavailable:
    available = False


_UNAVAILABLE = _Unavailable()


def render_money_bar(
    ax: Axes, fundamentals: CompanyFundamentals, metric_id: str
) -> None:
    """Shared bar-chart rendering for Money-valued metrics (revenue, net income, FCF, EPS)."""
    points = fundamentals.series[metric_id].points
    dates = [p.date for p in points]
    values = [p.value.value for p in points]

    ax.bar(dates, values, width=60, color="steelblue")
    currency_symbol = "₪" if fundamentals.currency.value == "ILS" else "$"
    ax.set_ylabel(f"{metric_id.replace('_', ' ').title()} ({currency_symbol})")
