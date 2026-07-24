"""The canonical `--range`/`range=` vocabulary, shared by validation, the web
picker, and both adapters (each of which also keeps its own range -> API-token
mapping — a different concern from this shared vocabulary/years table).
"""

RANGES: tuple[str, ...] = ("6m", "1y", "3y", "5y", "10y", "max")

_RANGE_YEARS: dict[str, int] = {
    "6m": 1,
    "1y": 1,
    "3y": 3,
    "5y": 5,
    "10y": 10,
    "max": 10_000,
}


def range_years(range_: str) -> int | None:
    """Years spanned by a range string, or `None` if it's not in `RANGES`."""
    return _RANGE_YEARS.get(range_.lower())
