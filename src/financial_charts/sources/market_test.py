from financial_charts.sources.market import market_of
from financial_charts.template.models import Market


def test_ta_suffix_routes_to_tase():
    assert market_of("TEVA.TA") == Market.TASE


def test_bare_ticker_routes_to_us():
    assert market_of("AAPL") == Market.US


def test_ta_suffix_is_case_insensitive():
    assert market_of("teva.ta") == Market.TASE
