from typing import Protocol

from pydantic import BaseModel

from financial_charts.template.models import CompanyFundamentals, Market, Period


class Capability(BaseModel):
    """Config-as-code declaration of what a data source can supply.

    Declared statically per source in its `capability.py`. Render-time validation
    trusts this declaration; it is never probed live except via `verify-source`.
    """

    markets: set[Market]
    periods: set[Period]
    max_history: dict[Period, int]
    metrics: set[str]


class DataSource(Protocol):
    def capability(self) -> Capability: ...

    def fetch(
        self, ticker: str, market: Market, period: Period, range: str
    ) -> CompanyFundamentals: ...


class TickerNotFound(Exception):
    pass


class SourceUnavailable(Exception):
    pass


class MissingCredentials(Exception):
    pass


class UnsupportedPeriod(Exception):
    pass
