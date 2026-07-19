import argparse
import sys
from datetime import date
from pathlib import Path

from financial_charts import config
from financial_charts.cache.store import TemplateCache
from financial_charts.charts.catalog import get_chart
from financial_charts.charts.registry import register_chart_set
from financial_charts.dashboard.render import write_output
from financial_charts.sources.base import (
    Capability,
    MissingCredentials,
    SourceUnavailable,
    TickerNotFound,
)
from financial_charts.sources.market import market_of
from financial_charts.sources.registry import (
    get_capability,
    get_source,
    registered_sources,
)
from financial_charts.sources.validation import check_request
from financial_charts.sources.verify import reconcile
from financial_charts.template.models import CompanyFundamentals, Market, Period


def _render_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="financial_charts")
    parser.add_argument("ticker", help="e.g. AAPL (US) or TEVA.TA (TASE)")
    parser.add_argument(
        "--source", default=None, help="overrides the DATA_SOURCE env var"
    )
    parser.add_argument(
        "--period", choices=[p.value for p in Period], default=config.DEFAULT_PERIOD
    )
    parser.add_argument("--range", default=config.DEFAULT_RANGE)
    parser.add_argument(
        "--chart-set", dest="chart_set", default=config.DEFAULT_CHART_SET
    )
    parser.add_argument(
        "--charts",
        default=None,
        help="comma-separated chart ids overriding --chart-set, e.g. price,eps,margins",
    )
    parser.add_argument(
        "--out", default=None, help="output path (.html, .png, or .pdf)"
    )
    return parser


def _dedup_chart_ids(raw_ids: list[str]) -> list[str]:
    """Strip, drop empties, and drop duplicates, keeping first-seen order.

    First-seen order is preserved so a user's `--charts eps,price` renders in
    the order they asked for; a registered set's name is still built from the
    sorted ids so equivalent selections (any order) share one registry entry
    instead of growing `_CHART_SETS` once per ordering.
    """
    seen: set[str] = set()
    ids: list[str] = []
    for raw in raw_ids:
        chart_id = raw.strip()
        if chart_id and chart_id not in seen:
            seen.add(chart_id)
            ids.append(chart_id)
    return ids


def _resolve_chart_set_name(args: argparse.Namespace) -> str | None:
    """Return the chart set name to render, or None with an error already printed.

    `--charts` builds and registers an ad-hoc set from catalog chart ids,
    overriding `--chart-set`; otherwise the named set is used as-is.
    """
    if not args.charts:
        return args.chart_set

    chart_ids = _dedup_chart_ids(args.charts.split(","))
    if not chart_ids:
        print("error: no charts specified", file=sys.stderr)
        return None

    try:
        charts = [get_chart(chart_id) for chart_id in chart_ids]
    except KeyError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return None

    # Registered permanently in the shared _CHART_SETS registry (never evicted)
    # keyed by the sorted id set, so repeat/reordered requests for the same
    # selection reuse one entry — bounded by the catalog's size (at most
    # 2^N - 1 distinct subsets for N registered charts), which only grows
    # through reviewed commits, not user input.
    chart_set_name = "custom:" + ",".join(sorted(chart_ids))
    register_chart_set(chart_set_name, charts)
    return chart_set_name


def _fetch_with_cache_fallback(
    adapter,
    cache: TemplateCache,
    ticker: str,
    source_name: str,
    market: Market,
    period: Period,
    range_: str,
) -> CompanyFundamentals:
    today = date.today()
    cached = cache.get(ticker, source_name, period, range_, today)
    if cached is not None:
        return cached

    try:
        fundamentals = adapter.fetch(ticker, market, period, range_)
    except SourceUnavailable:
        stale = cache.latest(ticker, source_name, period, range_)
        if stale is None:
            raise
        stale.source_limits.append(
            "network/API unavailable; showing a stale cached page"
        )
        return stale

    cache.put(ticker, source_name, period, range_, today, fundamentals)
    return fundamentals


def _run_render(args: argparse.Namespace) -> int:
    ticker = args.ticker
    market = market_of(ticker)
    period = Period(args.period)
    source_name = args.source or config.data_source_name()

    chart_set_name = _resolve_chart_set_name(args)
    if chart_set_name is None:
        return 1

    try:
        adapter = get_source(source_name)
    except (KeyError, MissingCredentials) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    cache = TemplateCache()
    try:
        fundamentals = _fetch_with_cache_fallback(
            adapter, cache, ticker, source_name, market, period, args.range
        )
    except TickerNotFound:
        print(f"error: ticker not found: {ticker}", file=sys.stderr)
        return 1
    except SourceUnavailable as exc:
        print(
            f"error: source unavailable and no cache to fall back to: {exc}",
            file=sys.stderr,
        )
        return 1

    fundamentals.source_limits.extend(
        limit
        for limit in check_request(adapter.capability(), market, period, args.range)
        if limit not in fundamentals.source_limits
    )

    out_path = Path(args.out) if args.out else Path("out") / f"{ticker}.html"
    write_output(fundamentals, out_path, chart_set_name)
    print(f"wrote {out_path}")
    return 0


def _add_verify_source_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "verify-source",
        help="Reconcile a source's declared Capability against a live fetch",
    )
    parser.add_argument(
        "name", help="registered source name, e.g. yfinance or twelvedata"
    )
    parser.add_argument("--ticker", required=True)
    parser.add_argument("--market", choices=[m.value for m in Market], default=None)
    parser.add_argument(
        "--period", choices=[p.value for p in Period], default=Period.ANNUAL.value
    )
    parser.add_argument("--range", default="5y")


def _run_verify_source(args: argparse.Namespace) -> int:
    market = Market(args.market) if args.market else market_of(args.ticker)
    period = Period(args.period)

    adapter = get_source(args.name)
    report = reconcile(adapter, args.ticker, market, period, args.range)

    print(
        f"verify-source: {args.name} / {args.ticker} ({market.value}, {period.value}, {args.range})"
    )
    print(
        f"  declared-but-missing metrics (mismatch): {report.missing_metrics or 'none'}"
    )
    print(
        f"  undeclared extras (info):                {report.undeclared_extras or 'none'}"
    )
    print(
        f"  unit/currency warnings:                  {report.unit_warnings or 'none'}"
    )
    print(f"  history points per metric:                {report.history_points}")

    if report.has_mismatch:
        print("RESULT: mismatch found", file=sys.stderr)
        return 1
    print("RESULT: clean")
    return 0


def _add_capabilities_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "capabilities",
        help="Print a registered source's declared Capability (offline, no credentials)",
    )
    parser.add_argument(
        "name", nargs="?", default=None, help="registered source name; omit for all"
    )
    parser.add_argument(
        "--matrix",
        action="store_true",
        help="print a metric x source availability table instead",
    )


def _format_capability(name: str, capability: Capability) -> str:
    markets = ", ".join(sorted(m.value for m in capability.markets))
    periods = ", ".join(sorted(p.value for p in capability.periods))
    history = ", ".join(
        f"{period.value}={years}y"
        for period, years in sorted(
            capability.max_history.items(), key=lambda kv: kv[0].value
        )
    )
    metrics = ", ".join(sorted(capability.metrics))
    return (
        f"capabilities: {name}\n"
        f"  markets:      {markets}\n"
        f"  periods:      {periods}\n"
        f"  max_history:  {history}\n"
        f"  metrics:      {metrics}"
    )


def _format_matrix(names: list[str]) -> str:
    capabilities = {name: get_capability(name) for name in names}
    all_metrics = sorted(set().union(*(c.metrics for c in capabilities.values())))
    metric_col = max(len(m) for m in all_metrics) + 2
    source_col = max(len(n) for n in names) + 2

    lines = ["capability matrix (metric x source):"]
    lines.append(" " * metric_col + "".join(n.ljust(source_col) for n in names))
    for metric in all_metrics:
        row = metric.ljust(metric_col)
        for name in names:
            row += ("x" if metric in capabilities[name].metrics else "-").ljust(
                source_col
            )
        lines.append(row)
    return "\n".join(lines)


def _run_capabilities(args: argparse.Namespace) -> int:
    if args.name:
        try:
            get_capability(args.name)
        except KeyError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        names = [args.name]
    else:
        names = registered_sources()

    if args.matrix:
        print(_format_matrix(names))
    else:
        print(
            "\n\n".join(
                _format_capability(name, get_capability(name)) for name in names
            )
        )
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv

    if argv[:1] == ["verify-source"]:
        parser = argparse.ArgumentParser(prog="financial_charts")
        subparsers = parser.add_subparsers(dest="command")
        _add_verify_source_parser(subparsers)
        args = parser.parse_args(argv)
        return _run_verify_source(args)

    if argv[:1] == ["capabilities"]:
        parser = argparse.ArgumentParser(prog="financial_charts")
        subparsers = parser.add_subparsers(dest="command")
        _add_capabilities_parser(subparsers)
        args = parser.parse_args(argv)
        return _run_capabilities(args)

    args = _render_parser().parse_args(argv)
    return _run_render(args)


if __name__ == "__main__":
    raise SystemExit(main())
