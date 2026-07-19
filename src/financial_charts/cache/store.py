from datetime import date
from pathlib import Path

from financial_charts.template.models import CompanyFundamentals, Period

_DEFAULT_CACHE_DIR = Path(".cache") / "financial_charts"


def _key(ticker: str, source: str, period: Period, range: str, as_of: date) -> str:
    return (
        f"{ticker.upper()}_{source}_{period.value}_{range.lower()}_{as_of.isoformat()}"
    )


class TemplateCache:
    """Disk cache for fetched `CompanyFundamentals`, keyed by (ticker, source, period, range, date).

    Paid sources are metered, so the display reads cache-first before ever calling an adapter.
    """

    def __init__(self, cache_dir: Path | str = _DEFAULT_CACHE_DIR):
        self._dir = Path(cache_dir)

    def _path(
        self, ticker: str, source: str, period: Period, range: str, as_of: date
    ) -> Path:
        return self._dir / f"{_key(ticker, source, period, range, as_of)}.json"

    def get(
        self, ticker: str, source: str, period: Period, range: str, as_of: date
    ) -> CompanyFundamentals | None:
        path = self._path(ticker, source, period, range, as_of)
        if not path.exists():
            return None
        return CompanyFundamentals.model_validate_json(path.read_text())

    def latest(
        self, ticker: str, source: str, period: Period, range: str
    ) -> CompanyFundamentals | None:
        """Most recent cached entry for (ticker, source, period, range), any date.

        Used to serve a stale-but-usable page when a live fetch fails.
        """
        prefix = f"{ticker.upper()}_{source}_{period.value}_{range.lower()}_"
        matches = (
            sorted(self._dir.glob(f"{prefix}*.json")) if self._dir.exists() else []
        )
        if not matches:
            return None
        return CompanyFundamentals.model_validate_json(matches[-1].read_text())

    def put(
        self,
        ticker: str,
        source: str,
        period: Period,
        range: str,
        as_of: date,
        fundamentals: CompanyFundamentals,
    ) -> None:
        self._dir.mkdir(parents=True, exist_ok=True)
        path = self._path(ticker, source, period, range, as_of)
        path.write_text(fundamentals.model_dump_json())
