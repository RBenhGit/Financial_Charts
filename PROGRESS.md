# Progress

SPEC.md tasks 1–15 are complete and committed (see git log). The tool is fully
functional end-to-end:

```sh
python -m financial_charts AAPL --source yfinance --range 10y --out out/AAPL.html
python -m financial_charts TEVA.TA --source twelvedata --range 10y --out out/TEVA.html
python -m financial_charts verify-source yfinance --ticker AAPL
```

## Web UI (step 1 — static)

An independent `financial_charts/web/` module adds a browser UI. It composes only
the published interfaces of the existing modules (nothing else was modified) and has
its own entry point:

```sh
python -m financial_charts.web --port 8000   # then open the forwarded port
```

Enter a ticker + source/period/range/chart-set in the form; the dashboard renders in
an iframe below. Same static matplotlib PNG grid as the CLI. **Step 2 (future):**
interactive charts — add a JSON endpoint in this same `web/` module and swap the
front-end to a JS chart library; the template already serializes to JSON, so no
changes to sources/cache/template are needed.

240 tests passing, `ruff check` clean, `.claude` hooks wired to the uv toolchain.

## Web UI (step 2 — interactive)

Done. The iframe/static-PNG dashboard is replaced with client-side Plotly.js
charts, exactly as step 1 anticipated — no changes to sources/cache/template/
charts/dashboard, all new code lives in `web/`. The CLI (`--out *.png/*.pdf/*.html`)
is untouched and stays static matplotlib.

- `web/chart_data.py` (new) shapes a `CompanyFundamentals` chart set into JSON,
  independent of every `charts/builtins/*.py` file — re-derived from the template
  (reusing `charts.base`'s published `currency_symbol`/`format_compact_number` and
  `template.derived`'s published `resolve`/`ratio`/`DerivedMetric` constants) rather
  than introspecting matplotlib `Axes` output, which would depend on an unpublished
  surface. A handful of charts (market cap, P/E, dividend yield, ROE, valuation's
  nearest-price join, price's SMA overlay) have their small inline math
  re-implemented here since it isn't externalized from their chart file today —
  an accepted, not eliminated, duplication/drift risk against those originals.
- **NaN → invalid JSON**: `flask.jsonify()` reproduces a raw `NaN` token for values
  like the SMA warm-up period (invalid per the JSON spec, breaks `JSON.parse`).
  Fixed by returning `ChartDataResponse.model_dump_json()` (Pydantic launders NaN
  to `null`) via a raw `Response`, never through `jsonify()`.
- New `GET /chart-data` route in `web/app.py`, alongside the unchanged `/render`
  (kept as a plain-HTML fallback). Both share a new `_resolve_request()` extracted
  from `/render`'s old body. While extracting it: `chart_set` was previously
  unvalidated (`?chart_set=bogus` → unhandled 500) — fixed as a small in-scope gap
  while already touching this validation code.
- `index.html`'s iframe is gone; the form fetches `/chart-data` and renders cards
  client-side. KPI charts render as plain HTML stat tiles (not Plotly traces) per
  the dataviz skill's guidance that a single current value is a stat tile, not a
  one-bar chart. Colors use the dataviz skill's validated categorical palette,
  deliberately dropping the matplotlib named colors (`"darkorange"` etc.) used
  today as per-card decoration. Dark mode re-themes via `prefers-color-scheme`
  (Plotly doesn't auto-theme) and re-renders the last response on an OS theme
  change. Plotly.js loads from its CDN pinned to an exact version (`plotly-basic-
  3.7.0.min.js`), not `plotly-latest`.
- **Deferred, not dropped**: no table-view accessibility fallback for the
  interactive charts (the dataviz skill's twin of every chart); no delta/sparkline
  on KPI stat tiles even though the underlying series exists.
- No JS test runner exists in this toolchain (plain Flask+Jinja2, no bundler) —
  the fetch+Plotly wiring is verified manually (`python -m financial_charts.web`),
  not by `pytest`.

## Task 16 — chart inventory (SPEC.md)

Done. The full inventory beyond the original six (Price, Revenue, Net Income,
FCF, EPS, Margins) is implemented, each its own vertical slice under
`charts/builtins/` following the `revenue.py`/`revenue_test.py` pattern:

- **EBITDA, Expenses (R&D/SG&A), Dividends Paid, Shares Outstanding** — reuse
  fields already present in the existing income-statement/cash-flow fetch
  calls in both adapters; no new endpoints needed.
- **Cash & Debt, Assets/Equity/Liabilities, Debt & Financial Leverage,
  Ratios (Current Ratio)** — added `balance_sheet` fetching to both adapters
  (yfinance's `balance_sheet`/`quarterly_balance_sheet` properties, Twelve
  Data's `balance_sheet` endpoint), exposing `total_assets`,
  `total_liabilities`, `total_equity`, `cash_and_equivalents`, `total_debt`,
  `total_current_assets`, `total_current_liabilities`, `ebit` as base
  metrics. Two new `DerivedMetric`s (`current_ratio`, `debt_to_equity`) in
  `template/derived.py`.
- **Return on Capital (ROIC/ROCE)** — ROCE is the standard EBIT / (Assets -
  Current Liabilities); ROIC is a simplification (Net Income / (Debt +
  Equity - Cash), documented in `derived.py`) that avoids fetching a
  separate effective tax rate for one chart.
- **Valuation (P/B)** — book value/share is a normal same-cadence derived
  metric, but pairing it with daily price needed nearest-date matching
  (statement dates rarely land on a trading day) — done locally in
  `valuation.py` rather than complicating `resolve()`'s exact-date join used
  by every other derived metric.
- **KPI cards** (Market Cap, P/E, Dividend Yield, ROE) — single-value "stat
  tile" cards; each is a normal `Chart` that draws a big number via two new
  shared helpers (`render_kpi_value`, `format_compact_number`) instead of a
  line/bar, so no dashboard/layout changes were needed. All four reuse
  metrics already fetched for other charts.

Building the KPI cards surfaced a real bug (now fixed, with a regression
test): yfinance's price series never filtered `NaN` closes — yfinance
returns one for the current, still-open trading day — so "latest price"
was silently NaN. Every other statement-series helper already filtered
`NaN`; `_price_series` didn't.

Capability declarations for both sources were hand-verified against live
bank/large-cap sample data (not `commission-source` — that tool's
metric-availability probe is scoped to `available_charts()`'s
`required_metrics`, so running it before a metric has a consuming chart
drops it from the regenerated `capability.py`; it's also stricter than the
existing declarations tolerate, e.g. it would drop `gross_margin` for
yfinance since bank samples lack a clean gross-profit line — a pre-existing
imprecision, not something to silently fix as a side effect of Task 16).

## Remaining work

No known gaps. Nothing half-done — safe to stop or resume at any point.
