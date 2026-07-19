from financial_charts.template.models import Market


def market_of(ticker: str) -> Market:
    """Route a ticker to its market by the `.TA` suffix (TASE); bare tickers are US."""
    if ticker.upper().endswith(".TA"):
        return Market.TASE
    return Market.US
