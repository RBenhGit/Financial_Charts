# Financial Charts

A Python tool that fetches a company's fundamentals — for **US and Tel Aviv Stock Exchange
(TASE)** listings — and renders a fixed, pre-determined grid of charts *all at once*, so an
investor can evaluate the company at a glance (in the spirit of a Qualtrim-style dashboard).

Use it two ways: a **CLI** that writes a static dashboard page, or a **local web UI** where you
type a ticker into a form and see the dashboard in your browser.

## Quick start

Requires **Python 3.12+** and [uv](https://docs.astral.sh/uv/).

```sh
uv sync                                              # install dependencies
uv run python -m financial_charts AAPL --out out/AAPL.html    # CLI → static page
uv run python -m financial_charts.web --port 8000    # web UI → open the (forwarded) port
```

Paid-source credentials go in a local `.env` (never committed):

```sh
TWELVEDATA_API_KEY=your_key_here
DATA_SOURCE=yfinance        # or twelvedata; overridable per render with --source
```

## Usage

### CLI — render a static dashboard

```sh
# US via the free source
uv run python -m financial_charts AAPL --source yfinance --period annual --range 10y --out out/AAPL.html
# TASE via the paid source (native ₪, agorot/millions handled)
uv run python -m financial_charts TEVA.TA --source twelvedata --range 10y --out out/TEVA.html
```

`TICKER [--source] [--period quarterly|ttm|annual] [--range 6m|1y|3y|5y|10y|max]
[--chart-set] [--out PATH]`. `--out` accepts `.html`, `.png`, or `.pdf`; it defaults to
`out/<TICKER>.html`. Unavailable metrics render a "No Data" card and are listed under the
page's source-limits panel. **`--period ttm` is accepted by the parser but not yet declared
by any registered source** — it fails fast with a clear "source does not support period ttm"
error rather than a blank or mislabeled chart.

### Web UI — a browser front-end (static charts)

```sh
uv run python -m financial_charts.web --host 0.0.0.0 --port 8000
```

Open the (port-forwarded) address, enter a ticker plus source/period/range/chart-set, and the
dashboard renders below the form. It serves the same static chart grid as the CLI. This is a
self-contained module (`financial_charts/web/`) with its own entry point — a local dev server,
not for production.

### `verify-source` — reconcile a source against its live API

A developer command run when a source is added or changed; it live-fetches a sample ticker and
diffs the response against the source's declared capability (missing metrics, undeclared
extras, TASE agorot-vs-shekel unit checks), exiting non-zero on any mismatch. It is **never**
run during a normal render.

```sh
uv run python -m financial_charts verify-source yfinance   --ticker AAPL
uv run python -m financial_charts verify-source twelvedata --ticker TEVA.TA --market TASE
```

## Architecture

Data flows one way — **env-configured data source → per-source adapter → canonical template →
display** — and the display layer reads *only* the template, never a data source directly.

- **Pluggable data sources, chosen by environment config.** `yfinance` is the free tier;
  `twelvedata` is the paid tier. Credentials come from env / `.env`, never committed.
- **One adapter ("converter") per source** maps that source's endpoints onto the canonical
  template. Each source also declares a **capability set** (which metrics, how much history —
  paid = 10y, free = 4y — supported markets/periods) as config-as-code. Adding a source =
  an `adapter.py` + a declared `capability.py` + a `registry` entry, then confirmed with the
  explicit `verify-source` command. Renders never probe live — declared limits are surfaced to
  the user instead.
- **Canonical template = the single display data model** (Pydantic). Every monetary series is
  a `Money`-style `(value, currency, scale)` value tagged with its currency and unit.
- **Markets: US + TASE, native currency only** (₪ / $, no FX conversion). TASE has a unit
  trap — prices are in agorot (1/100 ₪) while reports are in millions of shekels — reconciled
  at the adapter boundary.
- **Caching:** adapters cache the template to disk (keyed by ticker + source + period + range +
  date); the display reads cache-first, so metered paid APIs aren't hit needlessly.

The charts themselves are **static** (matplotlib PNGs); the web UI is a front-end that drives
static renders, not an interactive charting app. The full design — chart inventory, per-source
capability matrix, tasks, edge cases — is in [SPEC.md](SPEC.md). Free source **yfinance** +
paid source **Twelve Data**, US-vs-TASE routing by **`.TA` suffix**, period/range **configurable
per render**.

## Status

Core spec (SPEC.md tasks 1–15) is complete, plus a browser UI. See [PROGRESS.md](PROGRESS.md)
for what's done and what's next (task 16: expanding the chart inventory; step 2: interactive
web charts).

- [x] Project conventions & architecture ([CLAUDE.md](CLAUDE.md)) and full spec ([SPEC.md](SPEC.md))
- [x] Toolchain & scaffold (`pyproject.toml`, package layout, `.claude` hooks wired to uv)
- [x] Canonical template + `Money` model
- [x] Data-source adapters (`yfinance` + `twelvedata`) + capability validation + `verify-source`
- [x] Disk cache, source registry, env config
- [x] Charts + dashboard assembly (static grid) + CLI
- [x] Browser web UI (static charts) — `python -m financial_charts.web`
- [ ] Remaining inventory charts (SPEC task 16: EBITDA, dividends, ratios, KPI cards, …)
- [ ] Interactive web charts (web step 2)

## Development

```sh
uv sync            # install/lock dependencies
uv run pytest -q   # run tests (offline — adapters use recorded fixtures, no live network)
uv run ruff check  # lint
uv run ruff format # format
```

Conventions (simplicity, modularity, verification policy, workflow) live in
[CLAUDE.md](CLAUDE.md). The `.claude/` hooks auto-format/lint edited files and gate turns on a
green test suite. This repo is built on the **CodeFundation starter kit**.
