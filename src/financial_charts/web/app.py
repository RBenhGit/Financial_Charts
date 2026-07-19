from flask import Flask, render_template, request

from financial_charts import config
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
