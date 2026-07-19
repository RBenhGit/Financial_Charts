import argparse
import sys

from financial_charts.sources.market import market_of
from financial_charts.sources.registry import get_source
from financial_charts.sources.verify import reconcile
from financial_charts.template.models import Market, Period


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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="financial_charts")
    subparsers = parser.add_subparsers(dest="command")
    _add_verify_source_parser(subparsers)

    args = parser.parse_args(argv)

    if args.command == "verify-source":
        return _run_verify_source(args)

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
