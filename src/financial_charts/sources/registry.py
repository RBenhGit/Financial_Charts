from financial_charts.sources.base import DataSource
from financial_charts.sources.twelvedata.adapter import TwelveDataAdapter
from financial_charts.sources.yfinance.adapter import YFinanceAdapter

_ADAPTERS: dict[str, type[DataSource]] = {
    "yfinance": YFinanceAdapter,
    "twelvedata": TwelveDataAdapter,
}


def get_source(name: str) -> DataSource:
    """Resolve a `DATA_SOURCE` name to an adapter instance.

    Raises `KeyError` for an unregistered name; a paid adapter with no
    credentials raises `MissingCredentials` from its own constructor.
    """
    try:
        adapter_cls = _ADAPTERS[name]
    except KeyError:
        raise KeyError(
            f"unknown data source {name!r}; registered sources: {sorted(_ADAPTERS)}"
        ) from None
    return adapter_cls()
