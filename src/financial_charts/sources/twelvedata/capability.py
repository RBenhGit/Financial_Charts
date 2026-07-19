from financial_charts.sources.base import Capability
from financial_charts.template.models import Market, Period

# Twelve Data (paid tier): full US + TASE coverage with 10y history, metered by API credits.
CAPABILITY = Capability(
    markets={Market.US, Market.TASE},
    periods={Period.ANNUAL, Period.QUARTERLY},
    max_history={Period.ANNUAL: 10, Period.QUARTERLY: 10},
    metrics={
        "price",
        "revenue",
        "net_income",
        "free_cash_flow",
        "eps",
        "gross_margin",
        "net_margin",
    },
)
