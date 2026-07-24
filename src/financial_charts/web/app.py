from flask import Flask, render_template, request

from financial_charts import chart_support, config
from financial_charts.charts.catalog import available_charts, get_chart
from financial_charts.charts.registry import get_chart_set, register_chart_set
from financial_charts.dashboard.render import render_html
from financial_charts.sources.base import (
    MissingCredentials,
    SourceUnavailable,
    TickerNotFound,
    UnsupportedPeriod,
)
from financial_charts.sources.market import is_valid_ticker
from financial_charts.sources.ranges import RANGES
from financial_charts.sources.registry import get_source
from financial_charts.sources.validation import require_supported_period
from financial_charts.template.models import Period
from financial_charts.web.service import load_fundamentals

# Form option lists owned by this module, keeping it independent of the registries'
# internals. Submitted values are still validated by the real get_source/get_chart_set
# inside the render path, so an unsupported value produces a proper error, not a blank.
SOURCES = ["yfinance", "twelvedata"]
CHART_SETS = ["fundamentals"]
PERIODS = [p.value for p in Period]


def _dedup_chart_ids(raw_ids: list[str]) -> list[str]:
    """Strip, drop empties, and drop duplicates, keeping first-seen order.

    Mirrors __main__._dedup_chart_ids (this module and the CLI compose the
    same published functions independently rather than sharing private code,
    matching web/service.py's existing convention). Preventing duplicate ids
    from reaching register_chart_set keeps the generated set name — and the
    permanent, never-evicted _CHART_SETS entry it creates — bounded by the
    catalog's size rather than growing once per repeated/reordered request.
    """
    seen: set[str] = set()
    ids: list[str] = []
    for raw in raw_ids:
        chart_id = raw.strip()
        if chart_id and chart_id not in seen:
            seen.add(chart_id)
            ids.append(chart_id)
    return ids


def create_app() -> Flask:
    app = Flask(__name__)

    @app.get("/")
    def index() -> str:
        return render_template(
            "index.html",
            sources=SOURCES,
            periods=PERIODS,
            ranges=RANGES,
            chart_sets=CHART_SETS,
            # Read live from the catalog (unlike the literals above) so a new
            # registered chart appears in the picker without a template change.
            charts=available_charts(),
            chart_support={
                name: sorted(sources)
                for name, sources in chart_support.chart_support().items()
            },
            defaults={
                "source": config.data_source_name(),
                "period": config.DEFAULT_PERIOD,
                "range": config.DEFAULT_RANGE,
                "chart_set": config.DEFAULT_CHART_SET,
            },
        )

    @app.get("/render")
    def render():
        ticker = (request.args.get("ticker") or "").strip()
        if not ticker:
            return render_template(
                "error.html", message="Enter a ticker to render."
            ), 400
        if not is_valid_ticker(ticker):
            return render_template(
                "error.html", message=f"Invalid ticker: {ticker}"
            ), 400

        source_name = request.args.get("source") or config.data_source_name()
        period_value = request.args.get("period") or config.DEFAULT_PERIOD
        if period_value not in PERIODS:
            return render_template(
                "error.html", message=f"Unsupported period: {period_value}"
            ), 400
        range_ = (request.args.get("range") or config.DEFAULT_RANGE).lower()
        if range_ not in RANGES:
            return render_template(
                "error.html", message=f"Unsupported range: {range_}"
            ), 400

        chart_ids = _dedup_chart_ids(request.args.getlist("charts"))
        if chart_ids:
            try:
                charts = [get_chart(chart_id) for chart_id in chart_ids]
            except KeyError as exc:
                return render_template("error.html", message=str(exc).strip('"')), 400
            # Registering here depends on the dev server's threaded=False
            # (web/__main__.py) so no two requests interleave a register and
            # a read of a different selection — see the memory note on this
            # pattern if that assumption ever changes (e.g. threaded=True or
            # a multi-worker WSGI deployment).
            chart_set = "custom:" + ",".join(sorted(chart_ids))
            register_chart_set(chart_set, charts)
        else:
            chart_set = request.args.get("chart_set") or config.DEFAULT_CHART_SET

        # Resolved here (not inside load_fundamentals) so an unsupported period
        # is rejected before any fetch is attempted — same pre-flight gate the
        # CLI uses, kept independent rather than threaded through service.py.
        try:
            adapter = get_source(source_name)
        except KeyError as exc:
            return render_template("error.html", message=str(exc).strip('"')), 400
        except MissingCredentials as exc:
            return render_template("error.html", message=str(exc)), 400

        period = Period(period_value)
        try:
            require_supported_period(adapter.capability(), period)
        except UnsupportedPeriod as exc:
            return render_template("error.html", message=str(exc)), 400

        try:
            fundamentals = load_fundamentals(ticker, source_name, period, range_)
            fundamentals.source_limits.extend(
                limit
                for limit in chart_support.capability_limits(
                    get_chart_set(chart_set), adapter.capability()
                )
                if limit not in fundamentals.source_limits
            )
            return render_html(fundamentals, chart_set)
        except TickerNotFound:
            return render_template(
                "error.html", message=f"Ticker not found: {ticker}"
            ), 404
        except SourceUnavailable as exc:
            return render_template(
                "error.html",
                message=f"Source unavailable and no cache to fall back to: {exc}",
            ), 502

    return app
