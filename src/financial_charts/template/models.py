from __future__ import annotations

from datetime import date
from enum import Enum

from pydantic import BaseModel, ConfigDict


class Currency(str, Enum):
    USD = "USD"
    ILS = "ILS"


class Unit(str, Enum):
    ONES = "ones"
    THOUSANDS = "thousands"
    MILLIONS = "millions"


_UNIT_SCALE: dict[Unit, int] = {
    Unit.ONES: 1,
    Unit.THOUSANDS: 1_000,
    Unit.MILLIONS: 1_000_000,
}


class Period(str, Enum):
    QUARTERLY = "quarterly"
    TTM = "ttm"
    ANNUAL = "annual"


class Market(str, Enum):
    US = "US"
    TASE = "TASE"


class Money(BaseModel):
    """A monetary value tagged with its currency and unit scale.

    Two `Money` values in different currencies or scales must never be combined
    silently (e.g. TASE prices in agorot vs. statements in millions of shekels).
    """

    model_config = ConfigDict(frozen=True)

    value: float
    currency: Currency
    scale: Unit

    def to(self, scale: Unit) -> Money:
        """Rescale to a different unit, preserving the represented amount."""
        base = self.value * _UNIT_SCALE[self.scale]
        return Money(
            value=base / _UNIT_SCALE[scale], currency=self.currency, scale=scale
        )

    def _check_comparable(self, other: Money) -> None:
        if self.currency != other.currency:
            raise ValueError(
                f"cannot combine Money of different currencies: {self.currency} vs {other.currency}"
            )

    def __add__(self, other: Money) -> Money:
        self._check_comparable(other)
        other_rescaled = other.to(self.scale)
        return Money(
            value=self.value + other_rescaled.value,
            currency=self.currency,
            scale=self.scale,
        )

    def __sub__(self, other: Money) -> Money:
        self._check_comparable(other)
        other_rescaled = other.to(self.scale)
        return Money(
            value=self.value - other_rescaled.value,
            currency=self.currency,
            scale=self.scale,
        )

    def as_base_units(self) -> float:
        """The represented amount in the currency's smallest common unit (ones)."""
        return self.value * _UNIT_SCALE[self.scale]


class Point(BaseModel):
    date: date
    value: Money | float | None = None


class MetricSeries(BaseModel):
    metric_id: str
    points: list[Point] = []
    available: bool = True


class CompanyFundamentals(BaseModel):
    ticker: str
    market: Market
    currency: Currency
    period: Period
    range: str
    series: dict[str, MetricSeries] = {}
    source_limits: list[str] = []
