from financial_charts.sources.base import Capability
from financial_charts.template.models import Market, Period

# Range strings, ordered shortest to longest, mapped to the number of years they span.
_RANGE_YEARS: dict[str, int] = {
    "6m": 1,
    "1y": 1,
    "3y": 3,
    "5y": 5,
    "10y": 10,
    "max": 10_000,
}


def check_request(
    capability: Capability, market: Market, period: Period, range: str
) -> list[str]:
    """Compare a declared `Capability` against a requested (market, period, range).

    Pure, offline, deterministic. Returns human-readable limits to surface as
    `source_limits` on the rendered page; an empty list means the request is
    fully covered by the declared capability.
    """
    limits: list[str] = []

    if market not in capability.markets:
        limits.append(f"source does not support market {market.value}")

    if period not in capability.periods:
        limits.append(f"source does not support period {period.value}")
        return limits

    requested_years = _RANGE_YEARS.get(range.lower())
    max_years = capability.max_history.get(period)
    if requested_years is not None and max_years is not None and requested_years > max_years:
        limits.append(
            f"requested range {range} exceeds source's {max_years}y history for {period.value}"
        )

    return limits
