from financial_charts.sources.ranges import RANGES, range_years


def test_range_years_covers_every_declared_range():
    assert all(range_years(r) is not None for r in RANGES)


def test_range_years_is_case_insensitive():
    assert range_years("5Y") == range_years("5y")


def test_range_years_unrecognized_range_returns_none():
    assert range_years("8y") is None
