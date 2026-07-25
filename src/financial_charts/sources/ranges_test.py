import pytest

from financial_charts.sources.ranges import RANGES, approx_years, range_years
from financial_charts.template.models import Period


def test_range_years_covers_every_declared_range():
    assert all(range_years(r) is not None for r in RANGES)


def test_range_years_is_case_insensitive():
    assert range_years("5Y") == range_years("5y")


def test_range_years_unrecognized_range_returns_none():
    assert range_years("8y") is None


def test_approx_years_annual_is_one_year_per_point():
    assert approx_years(Period.ANNUAL, 4) == 4


def test_approx_years_quarterly_is_four_points_per_year():
    assert approx_years(Period.QUARTERLY, 9) == 2  # 9 // 4, rounded down


def test_approx_years_raises_for_an_unhandled_period():
    # TTM has no real adapter support yet; an unhandled Period member must
    # raise rather than silently fall through to the annual approximation.
    with pytest.raises(ValueError, match="ttm"):
        approx_years(Period.TTM, 8)
