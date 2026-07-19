from financial_charts.sources.base import Capability
from financial_charts.sources.validation import check_request
from financial_charts.template.models import Market, Period


def _capability(**overrides) -> Capability:
    defaults = dict(
        markets={Market.US},
        periods={Period.ANNUAL},
        max_history={Period.ANNUAL: 4},
        metrics={"revenue"},
    )
    defaults.update(overrides)
    return Capability(**defaults)


def test_request_within_capability_has_no_limits():
    cap = _capability(max_history={Period.ANNUAL: 10})
    assert check_request(cap, Market.US, Period.ANNUAL, "10y") == []


def test_free_tier_4y_history_flags_10y_request():
    cap = _capability(max_history={Period.ANNUAL: 4})
    limits = check_request(cap, Market.US, Period.ANNUAL, "10y")
    assert len(limits) == 1
    assert "4y" in limits[0]
    assert "10y" in limits[0]


def test_unsupported_market_is_flagged():
    cap = _capability(markets={Market.US})
    limits = check_request(cap, Market.TASE, Period.ANNUAL, "1y")
    assert any("TASE" in limit for limit in limits)


def test_unsupported_period_is_flagged_and_skips_history_check():
    cap = _capability(periods={Period.ANNUAL}, max_history={Period.ANNUAL: 4})
    limits = check_request(cap, Market.US, Period.QUARTERLY, "1y")
    assert len(limits) == 1
    assert "quarterly" in limits[0]
