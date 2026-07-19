from financial_charts.sources.base import Capability, DataSource
from financial_charts.sources.twelvedata.adapter import TwelveDataAdapter
from financial_charts.sources.twelvedata.capability import (
    CAPABILITY as _TWELVEDATA_CAPABILITY,
)
from financial_charts.sources.yfinance.adapter import YFinanceAdapter
from financial_charts.sources.yfinance.capability import (
    CAPABILITY as _YFINANCE_CAPABILITY,
)

_ADAPTERS: dict[str, type[DataSource]] = {
    "yfinance": YFinanceAdapter,
    "twelvedata": TwelveDataAdapter,
}

_CAPABILITIES: dict[str, Capability] = {
    "yfinance": _YFINANCE_CAPABILITY,
    "twelvedata": _TWELVEDATA_CAPABILITY,
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


def get_capability(name: str) -> Capability:
    """Look up a registered source's declared `Capability`.

    Reads the static `capability.py` declaration directly — no adapter is
    constructed, so this needs no credentials and makes no network call.
    """
    try:
        return _CAPABILITIES[name]
    except KeyError:
        raise KeyError(
            f"unknown data source {name!r}; registered sources: {sorted(_CAPABILITIES)}"
        ) from None


def registered_sources() -> list[str]:
    return sorted(_ADAPTERS)
