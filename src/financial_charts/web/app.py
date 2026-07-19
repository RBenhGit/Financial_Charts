from flask import Flask, render_template, request

from financial_charts import config
from financial_charts.charts.catalog import available_charts, get_chart
from financial_charts.charts.registry import register_chart_set
from financial_charts.dashboard.render import render_html
from financial_charts.sources.base import (
    MissingCredentials,
    SourceUnavailable,
    TickerNotFound,
)
from financial_charts.template.models import Period
from financial_charts.web.service import load_fundamentals

# Form option lists owned by this module, keeping it independent of the registries'
# internals. Submitted values are still validated by the real get_source/get_chart_set
# inside the render path, so an unsupported value produces a proper error, not a blank.
SOURCES = ["yfinance", "twelvedata"]
RANGES = ["6m", "1y", "3y", "5y", "10y", "max"]
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

        source_name = request.args.get("source") or config.data_source_name()
        period_value = request.args.get("period") or config.DEFAULT_PERIOD
        range_ = request.args.get("range") or config.DEFAULT_RANGE

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

        try:
            fundamentals = load_fundamentals(
                ticker, source_name, Period(period_value), range_
            )
            return render_html(fundamentals, chart_set)
        except TickerNotFound:
            return render_template(
                "error.html", message=f"Ticker not found: {ticker}"
            ), 404
        except MissingCredentials as exc:
            return render_template("error.html", message=str(exc)), 400
        except KeyError as exc:
            return render_template("error.html", message=str(exc).strip('"')), 400
        except SourceUnavailable as exc:
            return render_template(
                "error.html",
                message=f"Source unavailable and no cache to fall back to: {exc}",
            ), 502

    return app
